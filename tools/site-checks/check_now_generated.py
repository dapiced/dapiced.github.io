#!/usr/bin/env python3
"""Verify that the generated /now/ page exposes its source update date."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATE_IN_TIME = re.compile(
    r'<time\b[^>]*\bdatetime="(?P<date>\d{4}-\d{2}-\d{2})"[^>]*>'
)
REMOVED_MIGRATION_CLAIM = ("~200", "1,500 repositories")


def _load_freshness_checker():
    path = Path(__file__).with_name("check_now_freshness.py")
    spec = importlib.util.spec_from_file_location("check_now_freshness", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load freshness checker: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    checker = _load_freshness_checker()
    source = ROOT / "now" / "index.html"
    generated = ROOT / "_site" / "now" / "index.html"
    try:
        expected = checker.parse_updated_date(source.read_text(encoding="utf-8"))
        html = generated.read_text(encoding="utf-8")
    except (OSError, checker.FreshnessError) as error:
        print(f"Generated /now/ validation failed: {error}", file=sys.stderr)
        return 1

    match = DATE_IN_TIME.search(html)
    if match is None:
        print("Generated /now/ validation failed: update date is missing", file=sys.stderr)
        return 1
    if match.group("date") != expected.isoformat():
        print(
            "Generated /now/ validation failed: "
            f"expected {expected.isoformat()}, got {match.group('date')}",
            file=sys.stderr,
        )
        return 1
    if any(fragment in html for fragment in REMOVED_MIGRATION_CLAIM):
        print(
            "Generated /now/ validation failed: removed migration claim is present",
            file=sys.stderr,
        )
        return 1

    print(f"Generated /now/ validation passed: updated={expected.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
