#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


SCHEMAS = {
    "navigation": {
        "required": {"label": str, "href": str},
        "optional": {"class": str, "target": str, "rel": str},
    },
    "skills": {
        "required": {"domain": str, "tags": list},
        "optional": {},
    },
    "timeline": {
        "required": {"year": str, "role": str, "description": str},
        "optional": {},
    },
    "resources": {
        "required": {
            "icon": str,
            "title": str,
            "description": str,
            "href": str,
            "more": str,
        },
        "optional": {},
    },
}

APPROVED_SITE_DATA = {
    "navigation": [
        {"label": "About", "href": "/#about"},
        {"label": "Projects", "href": "/#projects"},
        {"label": "Portfolios", "href": "/portfolio/"},
        {"label": "Timeline", "href": "/#timeline"},
        {"label": "Resume", "href": "/resume/"},
        {"label": "Blogs", "href": "/blog/"},
        {"label": "Now", "href": "/now/"},
        {
            "label": "My LabML",
            "href": "https://app.dominicdapice.com/",
            "class": "nav-labml",
            "target": "_blank",
            "rel": "noopener",
        },
        {"label": "Resources", "href": "/resources/"},
        {
            "label": "Contact",
            "href": "https://www.linkedin.com/in/dapiced/",
            "target": "_blank",
            "rel": "noopener",
        },
        {
            "label": "GitHub ↗",
            "href": "https://github.com/dapiced",
            "class": "nav-gh",
            "target": "_blank",
            "rel": "noopener",
        },
    ],
    "skills": [
        {
            "domain": "Cloud & Data",
            "tags": ["Azure", "Databricks", "VMware", "Azure DevOps"],
        },
        {
            "domain": "IaC & Automation",
            "tags": [
                "Ansible",
                "Terraform",
                "Packer",
                "GitHub Actions",
                "PowerShell",
                "Bash",
            ],
        },
        {"domain": "Languages", "tags": ["Python", "R", "JavaScript", "Perl"]},
        {
            "domain": "Systems",
            "tags": ["Red Hat", "SUSE", "Windows", "IBM AIX", "Red Hat Satellite"],
        },
        {
            "domain": "Databases",
            "tags": ["PostgreSQL", "MSSQL", "MySQL", "Oracle"],
        },
        {
            "domain": "ML & Data",
            "tags": ["MLOps", "DataOps", "Machine Learning", "Kaggle"],
        },
    ],
    "timeline": [
        {
            "year": "2026 - NOW",
            "role": "Developer - Azure Infrastructure AI",
            "description": (
                "Azure for AI · Databricks platform · MLOps / DataOps · IaC · CI/CD"
            ),
        },
        {
            "year": "2018 - 2025",
            "role": "Cloud / Linux Administrator & IaC Developer",
            "description": (
                "Self-service cloud for business clients · "
                "IaC in NERC-regulated environments"
            ),
        },
        {
            "year": "2015 - 2018",
            "role": "IT Standardization Linux System Administrator",
            "description": (
                "Fleet of 1000+ servers · patching and standardization at scale"
            ),
        },
        {
            "year": "2011 - 2015",
            "role": "IT Linux System Administrator",
            "description": (
                "Physical & virtual server deployments · Linux appliances"
            ),
        },
        {
            "year": "2001 - 2011",
            "role": "IT Linux System Administrator",
            "description": (
                "Installation and configuration of servers and Linux appliances"
            ),
        },
        {
            "year": "1998 - 2001",
            "role": "IT Technician & System Administrator",
            "description": (
                "Internal IT and client support - where it all started"
            ),
        },
    ],
    "resources": [
        {
            "icon": "🌌",
            "title": "Astronomy",
            "description": (
                "Exploring celestial objects and following the latest discoveries - "
                "from JWST deep fields to backyard skies."
            ),
            "href": "/blog/astronomy/",
            "more": "Read articles →",
        },
        {
            "icon": "🧠",
            "title": "Artificial Intelligence",
            "description": (
                "Studying ML advances and how they translate into real-world impact - "
                "then testing myself on Kaggle."
            ),
            "href": "/blog/ai/",
            "more": "Read articles →",
        },
        {
            "icon": "⚛️",
            "title": "Physics",
            "description": (
                "Fascinated by the fundamental laws that describe our universe - "
                "the original distributed system."
            ),
            "href": "/blog/physics/",
            "more": "Read articles →",
        },
    ],
}


class SiteDataError(ValueError):
    pass


def _validate_string(value: Any, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SiteDataError(f"{location} must be a non-empty string")


def _validate_item(name: str, index: int, item: Any) -> None:
    location = f"{name}[{index}]"
    if not isinstance(item, dict):
        raise SiteDataError(f"{location} must be a mapping")

    schema = SCHEMAS[name]
    allowed = set(schema["required"]) | set(schema["optional"])
    unexpected = set(item) - allowed
    if unexpected:
        raise SiteDataError(
            f"{location} contains unexpected fields: {', '.join(sorted(unexpected))}"
        )

    for field, expected_type in schema["required"].items():
        if field not in item:
            raise SiteDataError(f"{location} is missing required field '{field}'")
        value = item[field]
        if not isinstance(value, expected_type):
            raise SiteDataError(
                f"{location}.{field} must be {expected_type.__name__}"
            )
        if expected_type is str:
            _validate_string(value, f"{location}.{field}")

    for field, expected_type in schema["optional"].items():
        if field in item:
            if not isinstance(item[field], expected_type):
                raise SiteDataError(
                    f"{location}.{field} must be {expected_type.__name__}"
                )
            _validate_string(item[field], f"{location}.{field}")

    if name == "skills":
        tags = item["tags"]
        if not tags:
            raise SiteDataError(f"{location}.tags must not be empty")
        for tag_index, tag in enumerate(tags):
            _validate_string(tag, f"{location}.tags[{tag_index}]")

    if name == "navigation":
        target_present = "target" in item
        rel_present = "rel" in item
        if target_present != rel_present:
            raise SiteDataError(f"{location} must define target and rel together")
        if target_present and (
            item["target"] != "_blank"
            or item["rel"] != "noopener"
            or not item["href"].startswith("https://")
        ):
            raise SiteDataError(
                f"{location} external links require https, target '_blank', and rel 'noopener'"
            )


def load_site_data(root: Path | str) -> dict[str, list[dict[str, Any]]]:
    data_dir = Path(root) / "_data"
    loaded: dict[str, list[dict[str, Any]]] = {}

    for name in SCHEMAS:
        path = data_dir / f"{name}.yml"
        if not path.is_file():
            raise SiteDataError(f"required data file is missing: {path}")
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise SiteDataError(f"{path} contains invalid YAML: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise SiteDataError(f"{path} must contain a non-empty list")
        for index, item in enumerate(data):
            _validate_item(name, index, item)
        if data != APPROVED_SITE_DATA[name]:
            raise SiteDataError(
                f"{name} does not match the approved content and order"
            )
        loaded[name] = data

    return loaded


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        data = load_site_data(root)
    except SiteDataError as exc:
        print(f"Site data validation failed: {exc}", file=sys.stderr)
        return 1

    counts = ", ".join(f"{name}={len(items)}" for name, items in data.items())
    print(f"Site data validation passed: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
