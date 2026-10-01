#!/usr/bin/env python3
"""Validate generated blog discovery pages without third-party dependencies."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
EXPECTED_MACHINE_LEARNING = {
    "/blog/2026/09/what-i-learned-about-facebook-prophet/",
    "/blog/2026/08/autonomous-ai-agents-2026/",
    "/blog/2026/08/forty-years-of-losing-to-a-tree/",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tag_classes: list[tuple[str, str, str | None]] = []
        self.post_links: list[str] = []
        self.meta_description: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta" and values.get("name") == "description":
            self.meta_description = values.get("content")
        classes = (values.get("class") or "").split()
        href = values.get("href")
        if "tag" in classes:
            self.tag_classes.append((tag, " ".join(classes), href))
        if tag == "a" and "post-link" in classes and href:
            self.post_links.append(href)


def authored_tags() -> set[str]:
    tags: set[str] = set()
    for post in (ROOT / "_posts").glob("*.md"):
        text = post.read_text(encoding="utf-8")
        match = re.search(r"^tags:\s*\[([^\]]*)\]\s*$", text, re.MULTILINE)
        if match:
            tags.update(value.strip().strip("'\"") for value in match.group(1).split(","))
    return tags


def parse(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def output_path_for_url(url: str) -> Path:
    return SITE / url.lstrip("/") / "index.html"


def check() -> list[str]:
    errors: list[str] = []
    if not (SITE / "blog" / "index.html").is_file():
        return ["_site/blog/index.html is missing; build the site before running this check"]

    tags = authored_tags()
    for tag in sorted(tags):
        archive = SITE / "blog" / "tag" / tag / "index.html"
        if not archive.is_file():
            errors.append(f"missing authored tag archive: {archive.relative_to(SITE)}")
        else:
            description = parse(archive).meta_description or ""
            if f"#{tag}" not in description:
                errors.append(f"{archive.relative_to(SITE)}: SEO description is not tag-specific")

    machine_learning = SITE / "blog" / "tag" / "machine-learning" / "index.html"
    if machine_learning.is_file():
        actual = set(parse(machine_learning).post_links)
        if actual != EXPECTED_MACHINE_LEARNING:
            errors.append(
                "machine-learning archive should list exactly the three English posts; "
                f"found {sorted(actual)}"
            )

    for apod_tag in ("apod", "nasa"):
        if apod_tag not in tags and (SITE / "blog" / "tag" / apod_tag).exists():
            errors.append(f"APOD-only archive must not exist: /blog/tag/{apod_tag}/")

    blog_pages = [
        path
        for path in (SITE / "blog").rglob("*.html")
        if "search" not in path.relative_to(SITE / "blog").parts
    ]
    for path in blog_pages:
        page = parse(path)
        relative = path.relative_to(SITE)
        for tag, classes, href in page.tag_classes:
            if tag != "a" or not href:
                errors.append(f"{relative}: .tag must be a link, found <{tag} class='{classes}'>")
                continue
            if not href.startswith("/blog/tag/") or not output_path_for_url(href).is_file():
                errors.append(f"{relative}: broken tag archive link {href!r}")
        if relative.parts[:2] != ("blog", "tag"):
            continue
        for linked_post in re.findall(r'href="(/sky/[^"]*)"', path.read_text(encoding="utf-8")):
            errors.append(f"{relative}: archive links to excluded APOD content {linked_post}")

    for path in (SITE / "portfolio").rglob("*.html"):
        for tag, _, _ in parse(path).tag_classes:
            if tag != "span":
                errors.append(
                    f"{path.relative_to(SITE)}: portfolio .tag must remain a span, found <{tag}>"
                )
    return errors


def main() -> int:
    errors = check()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Blog discovery tag archives and links: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
