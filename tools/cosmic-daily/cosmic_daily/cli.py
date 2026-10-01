from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

import yaml
from PIL import Image, UnidentifiedImageError

from .article_generator import generate_article, slugify_title
from .image_processor import process_apod_image_with_fallback
from .nasa_client import APODRecord, fetch_apod
from .repository import RepositoryContext
from .rights_policy import evaluate_media_rights


EXIT_SUCCESS = 0
EXIT_ERROR = 1
MIN_IMAGE_DIMENSION = 320
BOILERPLATE_MARKERS = (
    "apod's main nasa site has moved",
    "apod's email for image submissions has changed",
    "tomorrow's picture:",
    "apod submissions",
)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate front matter key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _emit_github_output(**values: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _image_candidates(apod: APODRecord) -> list[str | None]:
    return [apod.hdurl, apod.url]


def _write_preview_files(apod, repo: RepositoryContext, output_dir: Path) -> tuple[Path, Path | None]:
    slug = slugify_title(apod.title)
    image_target_dir = output_dir / "assets" / "img" / "apod"
    image_target_dir.mkdir(parents=True, exist_ok=True)
    if apod.media_type == "image":
        decision = evaluate_media_rights(apod.media_type, apod.copyright)
        if decision.status != "allowed":
            raise ValueError(decision.reason)
        image_path, size = process_apod_image_with_fallback(_image_candidates(apod), image_target_dir, f"{apod.date}-{slug}")
        article_front, article_text = generate_article(apod, f"/assets/img/apod/{apod.date}-{slug}.webp", size[0], size[1])
        post_path = output_dir / "_apod" / f"{apod.date}-{slug}.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(article_text, encoding="utf-8")
        return post_path, image_path
    raise ValueError("Unsupported media type for preview generation.")


def preview(date_value: str | None = None) -> int:
    target = date_value or date.today().isoformat()
    try:
        apod = fetch_apod(target)
    except Exception as exc:
        print(f"Preview failed: {exc}")
        return EXIT_ERROR

    print(json.dumps({
        "date": apod.date,
        "title": apod.title,
        "media_type": apod.media_type,
        "url": apod.url,
        "copyright": apod.copyright,
        "apod_url": apod.apod_url,
    }, indent=2))

    decision = evaluate_media_rights(apod.media_type, apod.copyright)
    if decision.status == "unsupported_media":
        # A video day is a normal outcome, not a failure: nothing to publish.
        print(f"Skipped: {decision.reason}")
        return EXIT_SUCCESS

    try:
        with tempfile.TemporaryDirectory(prefix="cosmic-daily-") as temp_dir:
            repo = RepositoryContext(repo_root=Path.cwd())
            post_path, image_path = _write_preview_files(apod, repo, Path(temp_dir))
            print(f"Preview article: {post_path}")
            if image_path:
                print(f"Preview image: {image_path}")
        return EXIT_SUCCESS
    except Exception as exc:
        print(f"Preview generation failed: {exc}")
        return EXIT_ERROR


def generate(date_value: str | None = None) -> int:
    target = date_value or date.today().isoformat()
    repo = RepositoryContext()
    try:
        apod = fetch_apod(target)
    except Exception as exc:
        print(f"Generation failed: {exc}")
        return EXIT_ERROR

    decision = evaluate_media_rights(apod.media_type, apod.copyright)
    if decision.status == "unsupported_media":
        # A video day is a normal outcome, not a failure: nothing to publish.
        _emit_github_output(apod_date=apod.date, result="unsupported_media", post_path="", image_path="")
        print(f"Skipped: {decision.reason}")
        return EXIT_SUCCESS
    duplicates = repo.find_duplicates(apod.date, apod.apod_url)
    if duplicates:
        _emit_github_output(apod_date=apod.date, result="duplicate", post_path="", image_path="")
        print("Duplicate APOD detected; no file was generated.")
        return EXIT_SUCCESS

    slug = slugify_title(apod.title)
    filename = f"{apod.date}-{slug}"
    post_path = repo.apod_dir / f"{filename}.md"
    image_path = repo.assets_apod_dir / f"{filename}.webp"
    if post_path.exists() or image_path.exists():
        print(f"Destination already exists: {post_path if post_path.exists() else image_path}")
        return EXIT_ERROR

    with tempfile.TemporaryDirectory(prefix="cosmic-daily-") as temp_dir:
        staging_root = Path(temp_dir)
        staging_image_dir = staging_root / "assets" / "img" / "apod"
        staging_image_dir.mkdir(parents=True)
        try:
            staged_image, image_size = process_apod_image_with_fallback(
                _image_candidates(apod),
                staging_image_dir,
                filename,
            )
        except Exception as exc:
            print(f"Image processing failed: {exc}")
            return EXIT_ERROR

        _, article_text = generate_article(
            apod,
            f"/assets/img/apod/{filename}.webp",
            image_size[0],
            image_size[1],
        )
        staged_post = staging_root / "_apod" / f"{filename}.md"
        staged_post.parent.mkdir(parents=True)
        staged_post.write_text(article_text, encoding="utf-8")
        try:
            _validate_post_file(staged_post, repo, image_path=staged_image)
        except ValueError as exc:
            print(f"Validation failed: {exc}")
            return EXIT_ERROR

        repo.ensure_directory(repo.assets_apod_dir)
        repo.ensure_directory(repo.apod_dir)
        shutil.move(str(staged_image), image_path)
        shutil.move(str(staged_post), post_path)

    _emit_github_output(
        apod_date=apod.date,
        result=decision.status,
        post_path=str(post_path),
        image_path=str(image_path),
    )
    if decision.status == "manual_review":
        print(f"Generated post requires manual review: {decision.reason}")
    print(f"Generated post: {post_path}")
    print(f"Generated image: {image_path}")
    return EXIT_SUCCESS


def check(post_path: str | None = None) -> int:
    repo = RepositoryContext()
    candidates = sorted(repo.list_apod_files())
    chosen = candidates[-1] if candidates else None
    if post_path:
        chosen = Path(post_path)
    if chosen is None:
        print("No APOD article was found to validate.")
        return EXIT_ERROR

    if not chosen.exists():
        print(f"Article does not exist: {chosen}")
        return EXIT_ERROR

    try:
        _validate_post_file(chosen, repo)
    except ValueError as exc:
        print(f"Validation failed: {exc}")
        return EXIT_ERROR

    print(f"Validation passed for {chosen}")
    return EXIT_SUCCESS


def _validate_post_file(chosen: Path, repo: RepositoryContext, image_path: Path | None = None) -> None:
    content = chosen.read_text(encoding="utf-8")
    metadata, _ = _parse_and_validate_post(content)
    resolved_image = image_path or repo.root / metadata["image"].lstrip("/")
    if not resolved_image.exists():
        raise ValueError(f"Image file missing: {resolved_image}")
    try:
        with Image.open(resolved_image) as image:
            actual_width, actual_height = image.size
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Image file is not a readable raster image: {exc}") from exc
    if (actual_width, actual_height) != (metadata["image_width"], metadata["image_height"]):
        raise ValueError(
            "Image dimensions do not match front matter: "
            f"declared {metadata['image_width']}x{metadata['image_height']}, "
            f"actual {actual_width}x{actual_height}"
        )
    if actual_width < MIN_IMAGE_DIMENSION or actual_height < MIN_IMAGE_DIMENSION:
        raise ValueError(f"Image dimensions are too small: {actual_width}x{actual_height}")

    duplicates = repo.find_duplicates(
        metadata["apod_date"],
        metadata["apod_url"],
        exclude_path=chosen,
    )
    if duplicates:
        raise ValueError(f"Duplicate APOD article already exists: {[str(p) for p in duplicates]}")


def _parse_and_validate_post(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n"):
        raise ValueError("missing YAML front matter")
    header, separator, body = content[4:].partition("\n---\n")
    if not separator:
        raise ValueError("front matter is not closed")
    metadata = yaml.load(header, Loader=_UniqueKeyLoader)
    if not isinstance(metadata, dict):
        raise ValueError("front matter must be a mapping")
    required = {
        "layout": "apod",
        "generated_by": "cosmic-daily",
        "tags": ["astronomy", "nasa", "apod"],
    }
    for key, expected in required.items():
        if metadata.get(key) != expected:
            raise ValueError(f"invalid {key}")
    title = metadata.get("title")
    if not isinstance(title, str) or len(title.strip()) < 8 or title.strip().lower() in {"nasa science", "untitled", "apod"}:
        raise ValueError("generic or malformed title")
    for key in ("description", "image", "credit", "apod_url"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"missing {key}")
    publication_date = metadata.get("date")
    if publication_date is None:
        raise ValueError("missing date")
    try:
        parsed_publication_date = (
            publication_date.date()
            if isinstance(publication_date, datetime)
            else datetime.strptime(publication_date.strip(), "%Y-%m-%d %H:%M:%S %z").date()
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("invalid date") from exc
    apod_date_value = metadata.get("apod_date")
    if apod_date_value is None:
        raise ValueError("missing apod_date")
    try:
        parsed_apod_date = apod_date_value if isinstance(apod_date_value, date) else date.fromisoformat(apod_date_value.strip())
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("invalid apod_date") from exc
    if parsed_publication_date != parsed_apod_date:
        raise ValueError("date does not match apod_date")
    metadata["apod_date"] = parsed_apod_date.isoformat()
    expected_apod_url = f"https://apod.nasa.gov/apod/ap{parsed_apod_date:%Y%m%d}.html"
    if metadata["apod_url"] != expected_apod_url:
        raise ValueError("invalid apod_url")
    if not metadata["image"].startswith("/assets/img/apod/"):
        raise ValueError("image must be an APOD asset")
    if not isinstance(metadata.get("image_width"), int) or metadata["image_width"] < MIN_IMAGE_DIMENSION:
        raise ValueError("image width is too small")
    if not isinstance(metadata.get("image_height"), int) or metadata["image_height"] < MIN_IMAGE_DIMENSION:
        raise ValueError("image height is too small")
    lowered_body = body.lower()
    if any(marker in lowered_body for marker in BOILERPLATE_MARKERS):
        raise ValueError("known APOD navigation/footer boilerplate is present")
    if len(body.strip()) < 40:
        raise ValueError("article explanation is too short")
    return metadata, body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate APOD entries for the Jekyll /sky/ collection.")
    parser.add_argument("command", nargs="?", choices=["preview", "generate", "check"], default="preview")
    parser.add_argument("--date", help="APOD date in ISO format (YYYY-MM-DD)")
    parser.add_argument("--post-path", help="Path to post to validate")
    args = parser.parse_args(argv)

    if args.command == "preview":
        return preview(args.date)
    if args.command == "generate":
        return generate(args.date)
    return check(args.post_path)
