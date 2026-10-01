#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class HtmlDataError(ValueError):
    pass


def _load_validator(root: Path):
    path = root / "tools" / "site-checks" / "validate_site_data.py"
    spec = importlib.util.spec_from_file_location("validate_site_data", path)
    if not spec or not spec.loader:
        raise HtmlDataError(f"cannot load site data validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HomepageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.navigation: list[dict[str, str]] = []
        self.skills: list[dict[str, Any]] = []
        self.timeline: list[dict[str, str]] = []
        self.resources: list[dict[str, str]] = []
        self._in_navigation = False
        self._navigation_link: dict[str, str] | None = None
        self._skill: dict[str, Any] | None = None
        self._timeline_item: dict[str, str] | None = None
        self._resource: dict[str, str] | None = None
        self._capture: tuple[dict[str, Any], str, bool] | None = None

    @staticmethod
    def _classes(attrs: dict[str, str | None]) -> set[str]:
        return set((attrs.get("class") or "").split())

    def handle_starttag(
        self,
        tag: str,
        raw_attrs: list[tuple[str, str | None]],
    ) -> None:
        attrs = dict(raw_attrs)
        classes = self._classes(attrs)

        if tag == "ul" and attrs.get("id") == "nav-links":
            self._in_navigation = True
        elif tag == "a" and self._in_navigation:
            self._navigation_link = {
                key: value
                for key in ("href", "class", "target", "rel")
                if (value := attrs.get(key)) is not None
            }
            self._navigation_link["label"] = ""
            self._capture = (self._navigation_link, "label", False)

        if tag == "div" and "skill-row" in classes:
            self._skill = {"domain": "", "tags": []}
        elif tag == "span" and self._skill is not None:
            if "skill-domain" in classes:
                self._capture = (self._skill, "domain", False)
            elif "tag" in classes:
                self._capture = (self._skill, "tags", True)

        if tag == "div" and "tl-item" in classes:
            self._timeline_item = {"year": "", "role": "", "description": ""}
        elif self._timeline_item is not None:
            timeline_fields = {
                "tl-year": "year",
                "tl-role": "role",
                "tl-desc": "description",
            }
            for class_name, field in timeline_fields.items():
                if class_name in classes:
                    self._capture = (self._timeline_item, field, False)
                    break

        if tag == "a" and "beyond-card" in classes:
            self._resource = {
                "href": attrs.get("href") or "",
                "icon": "",
                "title": "",
                "description": "",
                "more": "",
            }
        elif self._resource is not None:
            if tag == "span" and "icon" in classes:
                self._capture = (self._resource, "icon", False)
            elif tag == "h3":
                self._capture = (self._resource, "title", False)
            elif tag == "p":
                self._capture = (self._resource, "description", False)
            elif tag == "span" and "beyond-more" in classes:
                self._capture = (self._resource, "more", False)

    def handle_data(self, data: str) -> None:
        if self._capture is None:
            return
        target, field, is_list = self._capture
        text = data.strip()
        if not text:
            return
        if is_list:
            target[field].append(text)
        else:
            target[field] += text

    def handle_endtag(self, tag: str) -> None:
        if tag in {"a", "span", "p", "h3"}:
            self._capture = None

        if tag == "a" and self._navigation_link is not None:
            self.navigation.append(self._navigation_link)
            self._navigation_link = None
        elif tag == "ul" and self._in_navigation:
            self._in_navigation = False

        if tag == "div" and self._skill is not None:
            self.skills.append(self._skill)
            self._skill = None

        if tag == "div" and self._timeline_item is not None:
            self.timeline.append(self._timeline_item)
            self._timeline_item = None

        if tag == "a" and self._resource is not None:
            self.resources.append(self._resource)
            self._resource = None


def parse_rendered_homepage(html: str) -> dict[str, list[dict[str, Any]]]:
    parser = HomepageParser()
    parser.feed(html)
    return {
        "navigation": parser.navigation,
        "skills": parser.skills,
        "timeline": parser.timeline,
        "resources": parser.resources,
    }


def validate_rendered_homepage(root: Path | str) -> dict[str, int]:
    root_path = Path(root)
    homepage = root_path / "_site" / "index.html"
    if not homepage.is_file():
        raise HtmlDataError(f"generated homepage is missing: {homepage}")

    validator = _load_validator(root_path)
    expected = validator.load_site_data(root_path)
    rendered = parse_rendered_homepage(homepage.read_text(encoding="utf-8"))
    for name, expected_items in expected.items():
        if rendered[name] != expected_items:
            raise HtmlDataError(
                f"generated {name} does not match _data/{name}.yml: "
                f"expected {expected_items!r}, got {rendered[name]!r}"
            )

    return {name: len(items) for name, items in rendered.items()}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        summary = validate_rendered_homepage(root)
    except (HtmlDataError, ValueError) as exc:
        print(f"Generated homepage validation failed: {exc}", file=sys.stderr)
        return 1

    counts = ", ".join(f"{name}={count}" for name, count in summary.items())
    print(f"Generated homepage validation passed: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
