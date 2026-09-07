from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

from .article_generator import generate_article, slugify_title
from .image_processor import process_apod_image
from .nasa_client import fetch_apod
from .repository import RepositoryContext
from .rights_policy import evaluate_media_rights


EXIT_SUCCESS = 0
EXIT_ERROR = 1


def _emit_github_output(**values: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _write_preview_files(apod, repo: RepositoryContext, output_dir: Path) -> tuple[Path, Path | None]:
    slug = slugify_title(apod.title)
    image_target_dir = output_dir / "assets" / "img" / "apod"
    image_target_dir.mkdir(parents=True, exist_ok=True)
    if apod.media_type == "image":
        decision = evaluate_media_rights(apod.media_type, apod.copyright)
        if decision.status != "allowed":
            raise ValueError(decision.reason)
        image_path, size = process_apod_image(apod.hdurl or apod.url, image_target_dir, f"{apod.date}-{slug}")
        article_front, article_text = generate_article(apod, f"/assets/img/apod/{apod.date}-{slug}.webp", size[0], size[1])
        post_path = output_dir / "_posts" / f"{apod.date}-apod-{slug}.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(article_front + article_text.split("---\n\n", 1)[1], encoding="utf-8")
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
        _emit_github_output(apod_date=apod.date, result="unsupported_media", post_path="", image_path="")
        print(decision.reason)
        return EXIT_ERROR
    if decision.status == "review_required":
        _emit_github_output(apod_date=apod.date, result="review_required", post_path="", image_path="")
        print(decision.reason)
        return EXIT_ERROR

    duplicates = repo.find_duplicates(apod.date, apod.apod_url)
    if duplicates:
        _emit_github_output(apod_date=apod.date, result="duplicate", post_path="", image_path="")
        print("Duplicate APOD detected; no file was generated.")
        return EXIT_SUCCESS

    slug = slugify_title(apod.title)
    image_dir = repo.ensure_directory(repo.assets_apod_dir)
    try:
        image_path, image_size = process_apod_image(apod.hdurl or apod.url, image_dir, f"{apod.date}-{slug}")
    except Exception as exc:
        print(f"Image processing failed: {exc}")
        return EXIT_ERROR

    article_front, article_text = generate_article(apod, f"/assets/img/apod/{apod.date}-{slug}.webp", image_size[0], image_size[1])
    post_path = repo.ensure_directory(repo.posts_dir) / f"{apod.date}-apod-{slug}.md"
    if post_path.exists():
        print(f"Destination already exists: {post_path}")
        return EXIT_ERROR

    post_path.write_text(article_text, encoding="utf-8")
    _emit_github_output(
        apod_date=apod.date,
        result="generated",
        post_path=str(post_path),
        image_path=str(image_path),
    )
    print(f"Generated post: {post_path}")
    print(f"Generated image: {image_path}")
    return EXIT_SUCCESS


def check(post_path: str | None = None) -> int:
    repo = RepositoryContext()
    candidates = sorted(repo.list_post_files())
    chosen = next((item for item in candidates if "apod" in item.name.lower()), None)
    if post_path:
        chosen = Path(post_path)
    if chosen is None:
        print("No APOD article was found to validate.")
        return EXIT_ERROR

    if not chosen.exists():
        print(f"Article does not exist: {chosen}")
        return EXIT_ERROR

    content = chosen.read_text(encoding="utf-8")
    if not content.startswith("---"):
        print("Missing YAML front matter.")
        return EXIT_ERROR
    if "generated_by: cosmic-daily" not in content:
        print("Missing generated_by metadata.")
        return EXIT_ERROR
    if "tags: [astronomy, nasa, apod]" not in content:
        print("Missing astronomy tag.")
        return EXIT_ERROR

    image_match = next((line for line in content.splitlines() if "![" in line and "/assets/img/apod/" in line), None)
    if not image_match:
        print("Missing article image reference.")
        return EXIT_ERROR

    image_reference = image_match.split("(", 1)[1].split(")", 1)[0]
    resolved_image = repo.root / image_reference.lstrip("/")
    if not resolved_image.exists():
        print(f"Image file missing: {resolved_image}")
        return EXIT_ERROR

    duplicates = repo.find_duplicates(
        (content.split("apod_date: ", 1)[1].splitlines()[0].strip()) if "apod_date: " in content else "",
        (content.split('apod_url: "', 1)[1].split('"', 1)[0]) if 'apod_url: "' in content else "",
        exclude_path=chosen,
    )
    if duplicates:
        print(f"Duplicate APOD article already exists: {[str(p) for p in duplicates]}")
        return EXIT_ERROR

    print(f"Validation passed for {chosen}")
    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate APOD posts for the Jekyll site.")
    parser.add_argument("command", nargs="?", choices=["preview", "generate", "check"], default="preview")
    parser.add_argument("--date", help="APOD date in ISO format (YYYY-MM-DD)")
    parser.add_argument("--post-path", help="Path to post to validate")
    args = parser.parse_args(argv)

    if args.command == "preview":
        return preview(args.date)
    if args.command == "generate":
        return generate(args.date)
    return check(args.post_path)
