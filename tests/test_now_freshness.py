from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "site-checks" / "check_now_freshness.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_now_freshness", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def page_with_updated(value: str, *, duplicate: str | None = None) -> str:
    duplicate_line = f"updated: {duplicate}\n" if duplicate else ""
    return f"---\nlayout: default\nupdated: {value}\n{duplicate_line}---\n<section></section>\n"


def test_parse_updated_date_requires_one_exact_front_matter_field():
    checker = load_checker()

    assert checker.parse_updated_date(page_with_updated("2026-10-01")) == date(2026, 10, 1)

    with pytest.raises(checker.FreshnessError, match="missing"):
        checker.parse_updated_date("---\nlayout: default\n---\n")

    with pytest.raises(checker.FreshnessError, match="exactly one"):
        checker.parse_updated_date(
            page_with_updated("2026-10-01", duplicate="2026-09-30")
        )

    with pytest.raises(checker.FreshnessError, match="valid"):
        checker.parse_updated_date(page_with_updated("2026-1-1"))

    with pytest.raises(checker.FreshnessError, match="front matter"):
        checker.parse_updated_date("body\n---\nupdated: 2026-10-01\n---\n")


def test_assess_freshness_marks_only_the_90_day_boundary_stale():
    checker = load_checker()
    today = date(2026, 10, 1)

    fresh = checker.assess_freshness(date(2026, 7, 4), today)
    stale = checker.assess_freshness(date(2026, 7, 3), today)

    assert fresh.age_days == 89
    assert fresh.stale is False
    assert stale.age_days == 90
    assert stale.stale is True

    with pytest.raises(checker.FreshnessError, match="future"):
        checker.assess_freshness(date(2026, 10, 2), today)

    with pytest.raises(checker.FreshnessError, match="threshold"):
        checker.assess_freshness(date(2026, 9, 1), today, threshold_days=-1)


def run_checker(page: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER_PATH), str(page), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_distinguishes_fresh_stale_and_invalid_results(tmp_path: Path):
    fresh_page = tmp_path / "fresh.html"
    fresh_page.write_text(page_with_updated("2026-09-30"), encoding="utf-8")
    stale_page = tmp_path / "stale.html"
    stale_page.write_text(page_with_updated("2026-06-01"), encoding="utf-8")
    future_page = tmp_path / "future.html"
    future_page.write_text(page_with_updated("2026-10-02"), encoding="utf-8")

    fresh = run_checker(fresh_page, "--today", "2026-10-01")
    stale = run_checker(stale_page, "--today", "2026-10-01")
    future = run_checker(future_page, "--today", "2026-10-01")

    assert fresh.returncode == 0
    assert "updated=2026-09-30" in fresh.stdout
    assert "age_days=1" in fresh.stdout
    assert "threshold_days=90" in fresh.stdout
    assert "stale=false" in fresh.stdout
    assert stale.returncode == 2
    assert "stale=true" in stale.stdout
    assert future.returncode == 1
    assert "future" in future.stderr

    invalid_args = run_checker(fresh_page, "--threshold-days", "not-a-number")
    assert invalid_args.returncode == 1


def test_cli_json_supports_injected_today_and_threshold(tmp_path: Path):
    page = tmp_path / "page.html"
    page.write_text(page_with_updated("2026-09-25"), encoding="utf-8")

    result = run_checker(
        page,
        "--today",
        "2026-10-01",
        "--threshold-days",
        "5",
        "--format",
        "json",
    )

    assert result.returncode == 2
    assert json.loads(result.stdout) == {
        "age_days": 6,
        "stale": True,
        "threshold_days": 5,
        "today": "2026-10-01",
        "updated": "2026-09-25",
    }
