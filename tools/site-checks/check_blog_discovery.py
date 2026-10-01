#!/usr/bin/env python3
"""Validate generated blog discovery pages without third-party dependencies."""

from __future__ import annotations

import re
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
EXPECTED_MACHINE_LEARNING = {
    "/blog/2026/09/what-i-learned-about-facebook-prophet/",
    "/blog/2026/08/autonomous-ai-agents-2026/",
    "/blog/2026/08/forty-years-of-losing-to-a-tree/",
}


@dataclass
class RelatedItem:
    url: str | None = None
    date: str | None = None
    tags: list[str] = field(default_factory=list)
    title_parts: list[str] = field(default_factory=list)


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
        self.html_lang: str | None = None
        self.forms: list[dict[str, str | None]] = []
        self.inputs: list[dict[str, str | None]] = []
        self.scripts: list[str] = []
        self.live_regions: list[str | None] = []
        self.label_targets: set[str] = set()
        self.post_content_div_depth = 0
        self.content_headings: list[tuple[str, str | None, str]] = []
        self.current_heading: tuple[str, str | None, list[str]] | None = None
        self.in_post_toc = False
        self.post_toc_count = 0
        self.toc_list_depth = 0
        self.toc_li_depth = 0
        self.toc_invalid_structure = False
        self.toc_entries: list[tuple[int, str, str]] = []
        self.current_toc_link: tuple[int, str, list[str]] | None = None
        self.toc_title_parts: list[str] | None = None
        self.toc_title_text: str | None = None
        self.related_section_count = 0
        self.related_labelledby: str | None = None
        self.in_related_section = False
        self.related_title_parts: list[str] | None = None
        self.related_title_text: str | None = None
        self.current_related_item: RelatedItem | None = None
        self.related_items: list[RelatedItem] = []
        self.in_related_post_link = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.html_lang = values.get("lang")
        if values.get("id"):
            element_id = values["id"] or ""
            self.ids.add(element_id)
        classes = (values.get("class") or "").split()
        if tag == "div":
            if self.post_content_div_depth:
                self.post_content_div_depth += 1
            elif "post-content" in classes:
                self.post_content_div_depth = 1
        if tag in ("h2", "h3") and self.post_content_div_depth:
            self.current_heading = (tag, values.get("id"), [])
        if tag == "nav" and "post-toc" in classes:
            self.post_toc_count += 1
            self.in_post_toc = True
            self.toc_list_depth = 0
            self.toc_li_depth = 0
            self.toc_invalid_structure = False
        if tag == "section" and "related-posts" in classes:
            self.related_section_count += 1
            self.related_labelledby = values.get("aria-labelledby")
            self.in_related_section = True
        if self.in_related_section and tag == "h2" and values.get("id") == "related-title":
            self.related_title_parts = []
        if (
            self.in_related_section
            and tag == "li"
            and "related-post-item" in classes
        ):
            self.current_related_item = RelatedItem()
        if self.in_post_toc and tag == "ol":
            if self.toc_li_depth != self.toc_list_depth:
                self.toc_invalid_structure = True
            self.toc_list_depth += 1
        if self.in_post_toc and tag == "a" and (values.get("href") or "").startswith("#"):
            self.current_toc_link = (
                self.toc_list_depth,
                (values["href"] or "")[1:],
                [],
            )
        if self.in_post_toc and tag == "li":
            if self.toc_list_depth == 0 or self.toc_li_depth < self.toc_list_depth - 1:
                self.toc_invalid_structure = True
            self.toc_li_depth += 1
        if self.current_related_item is not None and tag == "a":
            href = values.get("href")
            if "related-post-link" in classes and href:
                self.current_related_item.url = href
                self.in_related_post_link = True
            elif "tag" in classes and href:
                self.current_related_item.tags.append(href)
        if self.current_related_item is not None and tag == "time":
            self.current_related_item.date = values.get("datetime")
        if self.in_post_toc and tag == "h2" and values.get("id") == "post-toc-title":
            self.toc_title_parts = []
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

    def handle_data(self, data: str) -> None:
        if self.current_heading is not None:
            self.current_heading[2].append(data)
        if self.current_toc_link is not None:
            self.current_toc_link[2].append(data)
        if self.in_post_toc and self.toc_title_parts is not None:
            self.toc_title_parts.append(data)
        if self.in_related_section and self.related_title_parts is not None:
            self.related_title_parts.append(data)
        if self.current_related_item is not None and self.in_related_post_link:
            self.current_related_item.title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current_heading is not None and tag == self.current_heading[0]:
            level, heading_id, parts = self.current_heading
            heading_text = " ".join(" ".join(parts).split())
            self.content_headings.append((level, heading_id, heading_text))
            self.current_heading = None
        if self.in_post_toc and tag == "a" and self.current_toc_link is not None:
            depth, heading_id, parts = self.current_toc_link
            link_text = " ".join(" ".join(parts).split())
            self.toc_entries.append((depth, heading_id, link_text))
            self.current_toc_link = None
        if self.in_post_toc and tag == "h2" and self.toc_title_parts is not None:
            self.toc_title_text = " ".join(" ".join(self.toc_title_parts).split())
            self.toc_title_parts = None
        if self.in_post_toc and tag == "ol":
            if self.toc_list_depth == 0:
                self.toc_invalid_structure = True
            else:
                self.toc_list_depth -= 1
            if self.toc_li_depth != self.toc_list_depth:
                self.toc_invalid_structure = True
        if self.in_post_toc and tag == "li":
            if self.toc_li_depth == 0:
                self.toc_invalid_structure = True
            else:
                self.toc_li_depth -= 1
        if tag == "nav" and self.in_post_toc:
            if self.toc_list_depth or self.toc_li_depth:
                self.toc_invalid_structure = True
            self.in_post_toc = False
        if self.in_related_section and tag == "h2" and self.related_title_parts is not None:
            self.related_title_text = " ".join(" ".join(self.related_title_parts).split())
            self.related_title_parts = None
        if tag == "a" and self.in_related_post_link:
            self.in_related_post_link = False
        if tag == "li" and self.current_related_item is not None:
            self.related_items.append(self.current_related_item)
            self.current_related_item = None
        if tag == "section" and self.in_related_section:
            self.in_related_section = False
        if tag == "div" and self.post_content_div_depth:
            self.post_content_div_depth -= 1


def authored_tags() -> set[str]:
    tags: set[str] = set()
    for post in (ROOT / "_posts").glob("*.md"):
        text = post.read_text(encoding="utf-8")
        match = re.search(r"^tags:\s*\[([^\]]*)\]\s*$", text, re.MULTILINE)
        if match:
            tags.update(value.strip().strip("'\"") for value in match.group(1).split(","))
    return tags


def authored_post_metadata() -> dict[str, dict[str, object]]:
    posts: dict[str, dict[str, object]] = {}
    for post in (ROOT / "_posts").glob("*.md"):
        match = re.match(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$", post.name)
        if not match:
            continue
        year, month, day, slug = match.groups()
        text = post.read_text(encoding="utf-8")
        tags_match = re.search(r"^tags:\s*\[([^\]]*)\]\s*$", text, re.MULTILINE)
        tags = {
            value.strip().strip("'\"")
            for value in tags_match.group(1).split(",")
            if value.strip()
        } if tags_match else set()
        date_match = re.search(r"^date:\s*(.+?)\s*$", text, re.MULTILINE)
        date_value = (
            date_match.group(1).strip().strip("'\"")
            if date_match
            else f"{year}-{month}-{day} 00:00:00+00:00"
        )
        parsed_date = datetime.fromisoformat(date_value)
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        lang_match = re.search(r"^lang:\s*[\"']?([^\"'\s#]+)", text, re.MULTILINE)
        translation_match = re.search(
            r"^translation_url:\s*[\"']?([^\"'\s#]+)",
            text,
            re.MULTILINE,
        )
        url = f"/blog/{year}/{month}/{slug}/"
        posts[url] = {
            "date": f"{year}-{month}-{day}",
            "sort_date": parsed_date.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "lang": lang_match.group(1) if lang_match else "en",
            "tags": tags,
            "translation_url": translation_match.group(1) if translation_match else None,
        }
    return posts


def parse(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def output_path_for_url(url: str) -> Path:
    return SITE / url.lstrip("/") / "index.html"


def related_urls_for_post(
    current_url: str,
    posts: dict[str, dict[str, object]],
) -> list[str]:
    current = posts.get(current_url)
    if current is None:
        return []
    translation_url = current["translation_url"]
    candidates: list[tuple[int, str, str, str]] = []
    for url, post in posts.items():
        if (
            url == current_url
            or url == translation_url
            or post["translation_url"] == current_url
        ):
            continue
        score = len(current["tags"] & post["tags"])
        if score:
            candidates.append((score, str(post["sort_date"]), url, str(post["lang"])))

    language = str(current["lang"])
    preferred = sorted(
        (candidate for candidate in candidates if candidate[3] == language),
        reverse=True,
    )
    selected = preferred[:3]
    if len(selected) < 3:
        english = sorted(
            (candidate for candidate in candidates if candidate[3] == "en"),
            reverse=True,
        )
        selected.extend(
            candidate for candidate in english if candidate not in selected
        )
    return [candidate[2] for candidate in selected[:3]]


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

    post_pages = [
        path
        for path in (SITE / "blog").rglob("index.html")
        if len(path.relative_to(SITE / "blog").parts) == 4
        and path.relative_to(SITE / "blog").parts[0].isdigit()
        and path.relative_to(SITE / "blog").parts[1].isdigit()
    ]
    authored_posts = authored_post_metadata()
    for url in authored_posts:
        if not output_path_for_url(url).is_file():
            errors.append(f"authored post has no generated page: {url}")
    for path in post_pages:
        page = parse(path)
        relative = path.relative_to(SITE)
        usable_headings = [
            (level, heading_id, heading_text)
            for level, heading_id, heading_text in page.content_headings
            if heading_id
        ]
        expected_entries: list[tuple[int, str, str]] = []
        seen_h2 = False
        for level, heading_id, heading_text in usable_headings:
            if level == "h2":
                seen_h2 = True
                depth = 1
            else:
                depth = 2 if seen_h2 else 1
            expected_entries.append((depth, heading_id or "", heading_text))

        needs_toc = len(usable_headings) >= 3
        if needs_toc and page.post_toc_count != 1:
            errors.append(f"{relative}: expected one TOC for {len(usable_headings)} usable h2/h3 headings")
        elif not needs_toc and page.post_toc_count:
            errors.append(f"{relative}: TOC must be omitted with fewer than 3 usable h2/h3 headings")
        if "post-toc-title" in {
            heading_id for _, heading_id, _ in usable_headings
        }:
            errors.append(f"{relative}: post heading ID collides with post-toc-title")
        if page.post_toc_count:
            actual_ids = [heading_id for _, heading_id, _ in page.toc_entries]
            if len(actual_ids) != len(set(actual_ids)):
                errors.append(f"{relative}: TOC contains duplicate fragment IDs")
            for heading_id in actual_ids:
                if heading_id not in page.ids:
                    errors.append(f"{relative}: TOC fragment #{heading_id} has no target ID")
            if page.toc_invalid_structure:
                errors.append(f"{relative}: TOC lists must be properly nested within list items")
            if page.toc_entries != expected_entries:
                errors.append(f"{relative}: TOC text, heading order or h3 nesting does not match post content")
            expected_title = "Sur cette page" if (page.html_lang or "").startswith("fr") else "On this page"
            if page.toc_title_text != expected_title:
                errors.append(f"{relative}: TOC title must use the page language")
    nothingness_path = SITE / "blog" / "2026" / "07" / "nothingness-has-no-address" / "index.html"
    if nothingness_path.is_file() and parse(nothingness_path).post_toc_count:
        errors.append("nothingness must not contain a TOC")

    for current_url in authored_posts:
        path = output_path_for_url(current_url)
        if not path.is_file():
            continue
        page = parse(path)
        relative = path.relative_to(SITE)
        expected_urls = related_urls_for_post(current_url, authored_posts)
        if expected_urls and page.related_section_count != 1:
            errors.append(f"{relative}: expected one related-posts section")
        elif not expected_urls and page.related_section_count:
            errors.append(f"{relative}: related section must be omitted without candidates")
        if page.related_section_count > 1:
            errors.append(f"{relative}: expected at most one related-posts section")
        if page.related_section_count and page.related_labelledby != "related-title":
            errors.append(f"{relative}: related section must label its heading")
        if page.related_section_count:
            expected_title = "Articles connexes" if (page.html_lang or "").startswith("fr") else "Related posts"
            if page.related_title_text != expected_title:
                errors.append(f"{relative}: related-posts title must use the page language")
        if len(page.related_items) > 3:
            errors.append(f"{relative}: related section must contain at most 3 posts")
        actual_urls = [item.url for item in page.related_items]
        if actual_urls != expected_urls:
            errors.append(
                f"{relative}: related links must follow shared-tag score/date order and language preference; "
                f"expected {expected_urls}, found {actual_urls}"
            )
        current = authored_posts.get(current_url)
        for item in page.related_items:
            if not item.url or item.url not in authored_posts:
                errors.append(f"{relative}: related links must target authored blog posts, found {item.url!r}")
                continue
            if item.url == current_url:
                errors.append(f"{relative}: related section links to the current post")
            if current and (
                item.url == current["translation_url"]
                or authored_posts[item.url]["translation_url"] == current_url
            ):
                errors.append(f"{relative}: related section links to the current post's translation")
            related_post = authored_posts[item.url]
            if current and not (current["tags"] & related_post["tags"]):
                errors.append(f"{relative}: related post {item.url} shares no tags")
            if not item.title_parts or not "".join(item.title_parts).strip():
                errors.append(f"{relative}: related link has no post title")
            if not item.date or not item.date.startswith(str(related_post["date"])):
                errors.append(f"{relative}: related post {item.url} has no matching date")
            if not item.tags:
                errors.append(f"{relative}: related post {item.url} has no linked tags")

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
