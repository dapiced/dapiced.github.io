from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import yaml

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
    image_dir = repo.ensure_directory(repo.assets_apod_dir)
    try:
        image_path, image_size = process_apod_image_with_fallback(_image_candidates(apod), image_dir, f"{apod.date}-{slug}")
    except Exception as exc:
        print(f"Image processing failed: {exc}")
        return EXIT_ERROR

    article_front, article_text = generate_article(apod, f"/assets/img/apod/{apod.date}-{slug}.webp", image_size[0], image_size[1])
    post_path = repo.ensure_directory(repo.apod_dir) / f"{apod.date}-{slug}.md"
    if post_path.exists():
        print(f"Destination already exists: {post_path}")
        return EXIT_ERROR

    post_path.write_text(article_text, encoding="utf-8")
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

    content = chosen.read_text(encoding="utf-8")
    try:
        metadata, body = _parse_and_validate_post(content)
    except ValueError as exc:
        print(f"Validation failed: {exc}")
        return EXIT_ERROR

    image_reference = metadata["image"]
    resolved_image = repo.root / image_reference.lstrip("/")
    if not resolved_image.exists():
        print(f"Image file missing: {resolved_image}")
        return EXIT_ERROR

    duplicates = repo.find_duplicates(
        metadata["apod_date"],
        metadata["apod_url"],
        exclude_path=chosen,
    )
    if duplicates:
        print(f"Duplicate APOD article already exists: {[str(p) for p in duplicates]}")
        return EXIT_ERROR

    print(f"Validation passed for {chosen}")
    return EXIT_SUCCESS


def _parse_and_validate_post(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n"):
        raise ValueError("missing YAML front matter")
    header, separator, body = content[4:].partition("\n---\n")
    if not separator:
        raise ValueError("front matter is not closed")
    metadata = yaml.safe_load(header)
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
    if not isinstance(metadata.get("apod_date"), (str, date)):
        raise ValueError("missing apod_date")
    metadata["apod_date"] = metadata["apod_date"].isoformat() if isinstance(metadata["apod_date"], date) else metadata["apod_date"].strip()
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
