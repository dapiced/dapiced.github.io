#!/usr/bin/env python3
"""Validate generated blog discovery pages without third-party dependencies."""

from __future__ import annotations

import re
import json
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
        self.links: list[str] = []
        self.post_item_ids: list[str | None] = []
        self.unordered_lists: list[dict[str, str | None]] = []
        self.meta_description: str | None = None
        self.ids: set[str] = set()
        self.forms: list[dict[str, str | None]] = []
        self.inputs: list[dict[str, str | None]] = []
        self.scripts: list[str] = []
        self.live_regions: list[str | None] = []
        self.label_targets: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "form":
            self.forms.append(values)
        if tag == "input":
            self.inputs.append(values)
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")
        if tag == "label" and values.get("for"):
            self.label_targets.add(values["for"] or "")
        if values.get("aria-live"):
            self.live_regions.append(values.get("aria-live"))
        if tag == "meta" and values.get("name") == "description":
            self.meta_description = values.get("content")
        classes = (values.get("class") or "").split()
        href = values.get("href")
        if tag == "a" and href:
            self.links.append(href)
        if "tag" in classes:
            self.tag_classes.append((tag, " ".join(classes), href))
        if tag == "a" and "post-link" in classes and href:
            self.post_links.append(href)
        if tag == "li" and "post-item" in classes:
            self.post_item_ids.append(values.get("id"))
        if tag == "ul":
            self.unordered_lists.append(values)


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
    blog_index_path = SITE / "blog" / "index.html"
    if blog_index_path.is_file():
        blog_index = parse(blog_index_path)
        if len(blog_index.post_links) != 10:
            errors.append(
                f"blog index must retain all 10 listed post links in HTML; found {len(blog_index.post_links)}"
            )
        if not any(
            listing.get("id") == "all-posts" and listing.get("data-initial") == "8"
            for listing in blog_index.unordered_lists
        ):
            errors.append("blog index must contain ul#all-posts[data-initial='8']")
        if not any(src == "/assets/js/blog-index.js" for src in blog_index.scripts):
            errors.append("blog index must load the deferred blog-index.js enhancement")
        post_list = next(
            (listing for listing in blog_index.unordered_lists if listing.get("id") == "all-posts"),
            {},
        )
        template = post_list.get("data-show-more-template") or ""
        if "{n}" not in template:
            errors.append("blog index must provide a translated show-more label template")
        if post_list.get("data-hidden-count") != str(max(len(blog_index.post_links) - 8, 0)):
            errors.append("blog index must provide the number of initially hidden posts")
        expected_item_ids = {
            f"post-{href.rstrip('/').rsplit('/', 1)[-1]}" for href in blog_index.post_links
        }
        if len(blog_index.post_item_ids) != 10 or set(blog_index.post_item_ids) != expected_item_ids:
            errors.append("blog index item IDs must be post-<slug> values matching the listed post URLs")

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

    search_json = SITE / "blog" / "search.json"
    search_page = SITE / "blog" / "search" / "index.html"
    if not search_json.is_file():
        errors.append("missing generated search index: blog/search.json")
    else:
        try:
            records = json.loads(search_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"blog/search.json is invalid JSON: {error}")
        else:
            if not isinstance(records, list) or len(records) != 11:
                errors.append("blog/search.json must contain all 11 authored posts")
            else:
                required = {"title", "url", "date", "lang", "tags", "excerpt"}
                for record in records:
                    if not isinstance(record, dict) or not required.issubset(record):
                        errors.append("every search record must include title, url, date, lang, tags, excerpt")
                        continue
                    if not all(isinstance(record[field], str) and record[field] for field in ("title", "url", "date", "lang")):
                        errors.append("search title, url, date, and lang values must be non-empty strings")
                    if isinstance(record.get("url"), str) and not record["url"].startswith("/blog/"):
                        errors.append(f"search URL must be a relative authored blog path: {record['url']}")
                    if isinstance(record.get("date"), str) and not re.fullmatch(
                        r"\d{4}-\d{2}-\d{2}", record["date"]
                    ):
                        errors.append(f"search date must use YYYY-MM-DD: {record['date']}")
                    if not isinstance(record["tags"], list) or not all(
                        isinstance(tag, str) for tag in record["tags"]
                    ):
                        errors.append("search tags must be an array of strings")
                    if not isinstance(record["excerpt"], str):
                        errors.append("search excerpt must be plain text")
                    if isinstance(record.get("url"), str):
                        if "/sky/" in record["url"]:
                            errors.append(f"search index must exclude APOD URL {record['url']}")
                        elif not output_path_for_url(record["url"]).is_file():
                            errors.append(f"search URL has no generated post page: {record['url']}")

    if not search_page.is_file():
        errors.append("missing generated search page: blog/search/index.html")
    else:
        page = parse(search_page)
        if not any(
            form.get("role") == "search" and form.get("method", "").lower() == "get"
            for form in page.forms
        ):
            errors.append("blog search page must contain a role=search GET form")
        if not any(input_.get("id") == "blog-search-query" for input_ in page.inputs):
            errors.append("blog search page must contain the labelled #blog-search-query input")
        if "blog-search-query" not in page.label_targets:
            errors.append("blog search input must have an associated label")
        if "search-results" not in page.ids:
            errors.append("blog search page must contain #search-results")
        if "search-status" not in page.ids:
            errors.append("blog search page must contain #search-status")
        if "polite" not in page.live_regions:
            errors.append("blog search page must contain an aria-live=polite status region")
        if "search-fallback" not in page.ids or "tag-archives" not in page.ids:
            errors.append("blog search page must include a server-rendered fallback and tag archive list")
        source = search_page.read_text(encoding="utf-8").lower()
        if "search needs javascript" not in source or "/blog/" not in page.links:
            errors.append("blog search fallback must explain its JavaScript requirement and link to /blog/")
        fallback_start = source.find('id="search-fallback"')
        fallback_end = source.find("</div>", fallback_start)
        if fallback_start < 0 or fallback_end < 0 or "<noscript>" in source[fallback_start:fallback_end]:
            errors.append("blog search fallback must be server-rendered and visible without JavaScript")
        linked_archives = {href for _, _, href in page.tag_classes if href}
        for tag in authored_tags():
            expected = f"/blog/tag/{tag}/"
            if expected not in linked_archives:
                errors.append(f"blog search fallback is missing tag archive link {expected}")
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
