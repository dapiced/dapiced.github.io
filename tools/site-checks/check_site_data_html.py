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


class ResumeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.timeline: list[dict[str, str]] = []
        self.skills: list[dict[str, Any]] = []
        self.headings: list[str] = []
        self.contact_links: list[dict[str, str]] = []
        self.profile_links: list[dict[str, str]] = []
        self.all_links: list[dict[str, str]] = []
        self.has_print_control = False
        self.has_form = False
        self.has_mailto = False
        self._in_resume = False
        self._experience_item: dict[str, str] | None = None
        self._skill: dict[str, Any] | None = None
        self._in_skill_tag = False
        self._heading: dict[str, str] | None = None
        self._link: dict[str, str] | None = None
        self._link_collection: list[dict[str, str]] | None = None
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

        if tag == "article" and "resume-page" in classes:
            self._in_resume = True
        if not self._in_resume:
            return

        if tag == "form":
            self.has_form = True
        if "data-print-resume" in attrs:
            self.has_print_control = True

        if tag in {"h1", "h2"}:
            self._heading = {"text": ""}
            self._capture = (self._heading, "text", False)

        if tag == "li" and "resume-experience-item" in classes:
            self._experience_item = {"year": "", "role": "", "description": ""}
        elif self._experience_item is not None:
            if tag == "p" and "resume-experience-year" in classes:
                self._capture = (self._experience_item, "year", False)
            elif tag == "h3":
                self._capture = (self._experience_item, "role", False)
            elif tag == "p":
                self._capture = (self._experience_item, "description", False)

        if tag == "li" and "resume-skill-group" in classes:
            self._skill = {"domain": "", "tags": []}
        elif self._skill is not None:
            if tag == "h3":
                self._capture = (self._skill, "domain", False)
            elif tag == "li" and "tag" in classes:
                self._in_skill_tag = True
                self._capture = (self._skill, "tags", True)

        if tag == "a":
            href = attrs.get("href") or ""
            if href.lower().startswith("mailto:"):
                self.has_mailto = True
            if "resume-contact-link" in classes:
                self._link_collection = self.contact_links
            elif "resume-profile-link" in classes:
                self._link_collection = self.profile_links
            else:
                self._link_collection = None
            self._link = {
                key: value
                for key in ("href", "target", "rel")
                if (value := attrs.get(key)) is not None
            }
            self._link["label"] = ""
            self._capture = (self._link, "label", False)

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
        if not self._in_resume:
            return

        if tag in {"h1", "h2"} and self._heading is not None:
            self.headings.append(self._heading["text"])
            self._heading = None
            self._capture = None
        elif tag in {"h3", "p"}:
            self._capture = None

        if tag == "a" and self._link is not None:
            self.all_links.append(self._link)
            if self._link_collection is not None:
                self._link_collection.append(self._link)
            self._link = None
            self._link_collection = None
            self._capture = None

        if tag == "li":
            if self._in_skill_tag:
                self._in_skill_tag = False
                self._capture = None
            elif self._skill is not None:
                self.skills.append(self._skill)
                self._skill = None
            elif self._experience_item is not None:
                self.timeline.append(self._experience_item)
                self._experience_item = None

        if tag == "article":
            self._in_resume = False


def parse_rendered_resume(html: str) -> dict[str, Any]:
    parser = ResumeParser()
    parser.feed(html)
    return {
        "timeline": parser.timeline,
        "skills": parser.skills,
        "headings": parser.headings,
        "contact_links": parser.contact_links,
        "profile_links": parser.profile_links,
        "all_links": parser.all_links,
        "has_print_control": parser.has_print_control,
        "has_form": parser.has_form,
        "has_mailto": parser.has_mailto,
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


def validate_rendered_resume(root: Path | str) -> dict[str, int]:
    root_path = Path(root)
    resume = root_path / "_site" / "resume" / "index.html"
    if not resume.is_file():
        raise HtmlDataError(f"generated resume is missing: {resume}")

    validator = _load_validator(root_path)
    expected = validator.load_site_data(root_path)
    rendered = parse_rendered_resume(resume.read_text(encoding="utf-8"))

    for name in ("timeline", "skills"):
        if rendered[name] != expected[name]:
            raise HtmlDataError(
                f"generated resume {name} does not match _data/{name}.yml: "
                f"expected {expected[name]!r}, got {rendered[name]!r}"
            )

    expected_headings = [
        "Dominic D'Apice",
        "Experience",
        "Technical capabilities",
        "Profiles and contact",
    ]
    if rendered["headings"] != expected_headings:
        raise HtmlDataError(
            "generated resume heading structure is incorrect: "
            f"expected {expected_headings!r}, got {rendered['headings']!r}"
        )

    expected_contact = [
        {
            "href": "https://www.linkedin.com/in/dapiced/",
            "target": "_blank",
            "rel": "noopener",
            "label": "Contact on LinkedIn",
        }
    ]
    if rendered["contact_links"] != expected_contact:
        raise HtmlDataError(
            "generated resume must use LinkedIn as its only contact link "
            f"with safe external-link attributes: got {rendered['contact_links']!r}"
        )

    expected_profiles = [
        ("https://www.linkedin.com/in/dapiced/", "LinkedIn"),
        ("https://github.com/dapiced", "GitHub"),
        ("https://www.kaggle.com/dominicdapice", "Kaggle"),
        ("https://huggingface.co/dapiced", "Hugging Face"),
    ]
    profiles = [
        (link.get("href"), link.get("label")) for link in rendered["profile_links"]
    ]
    if profiles != expected_profiles:
        raise HtmlDataError(
            "generated resume public profiles are incorrect: "
            f"expected {expected_profiles!r}, got {profiles!r}"
        )

    expected_all_links = expected_contact + [
        {
            "href": href,
            "target": "_blank",
            "rel": "noopener",
            "label": label,
        }
        for href, label in expected_profiles
    ]
    if rendered["all_links"] != expected_all_links:
        raise HtmlDataError(
            "generated resume must contain only its approved public links: "
            f"expected {expected_all_links!r}, got {rendered['all_links']!r}"
        )

    for link in rendered["contact_links"] + rendered["profile_links"]:
        if (
            not link.get("href", "").startswith("https://")
            or link.get("target") != "_blank"
            or link.get("rel") != "noopener"
        ):
            raise HtmlDataError(
                "generated resume profile links require safe external-link attributes"
            )

    if not rendered["has_print_control"]:
        raise HtmlDataError("generated resume is missing its print control")
    if rendered["has_form"]:
        raise HtmlDataError("generated resume must not contain a form")
    if rendered["has_mailto"]:
        raise HtmlDataError("generated resume must not contain mailto links")

    return {
        "timeline": len(rendered["timeline"]),
        "skills": len(rendered["skills"]),
        "profiles": len(rendered["profile_links"]),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        homepage_summary = validate_rendered_homepage(root)
        resume_summary = validate_rendered_resume(root)
    except (HtmlDataError, ValueError) as exc:
        print(f"Generated site data validation failed: {exc}", file=sys.stderr)
        return 1

    homepage_counts = ", ".join(
        f"{name}={count}" for name, count in homepage_summary.items()
    )
    resume_counts = ", ".join(
        f"{name}={count}" for name, count in resume_summary.items()
    )
    print(
        "Generated site data validation passed: "
        f"homepage({homepage_counts}); resume({resume_counts})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
