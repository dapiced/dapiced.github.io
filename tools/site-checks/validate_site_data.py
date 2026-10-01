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
