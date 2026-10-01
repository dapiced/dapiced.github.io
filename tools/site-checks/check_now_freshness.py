from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


DEFAULT_THRESHOLD_DAYS = 90
UPDATED_FIELD = re.compile(r"^updated:\s*(\d{4}-\d{2}-\d{2})\s*$")


class FreshnessError(ValueError):
    """Raised when the page date cannot be assessed safely."""


@dataclass(frozen=True)
class FreshnessResult:
    updated: date
    today: date
    age_days: int
    threshold_days: int
    stale: bool

    def as_json(self) -> dict[str, object]:
        result = asdict(self)
        result["updated"] = self.updated.isoformat()
        result["today"] = self.today.isoformat()
        return result


def parse_updated_date(text: str) -> date:
    """Parse exactly one valid updated field from the page front matter."""
    delimiters = [index for index, line in enumerate(text.splitlines()) if line == "---"]
    if len(delimiters) < 2:
        raise FreshnessError("front matter is missing")

    front_matter = text.splitlines()[delimiters[0] + 1 : delimiters[1]]
    candidates = [line for line in front_matter if line.startswith("updated:")]
    if len(candidates) != 1:
        if len(candidates) > 1:
            raise FreshnessError("updated field must appear exactly one time")
        raise FreshnessError("updated field is missing or not a valid YYYY-MM-DD date")

    match = UPDATED_FIELD.fullmatch(candidates[0])
    if match is None:
        raise FreshnessError("updated field is missing or not a valid YYYY-MM-DD date")

    value = match.group(1)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise FreshnessError("updated field is not a valid calendar date") from error


def assess_freshness(
    updated: date,
    today: date,
    threshold_days: int = DEFAULT_THRESHOLD_DAYS,
) -> FreshnessResult:
    if threshold_days < 0:
        raise FreshnessError("threshold must be zero or greater")
    if updated > today:
        raise FreshnessError("updated date is in the future")

    age_days = (today - updated).days
    return FreshnessResult(
        updated=updated,
        today=today,
        age_days=age_days,
        threshold_days=threshold_days,
        stale=age_days >= threshold_days,
    )


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise FreshnessError(f"{label} must be a valid YYYY-MM-DD date") from error


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check /now/ page freshness.")
    parser.add_argument("page", nargs="?", type=Path, default=Path("now/index.html"))
    parser.add_argument("--today", help="Override today's date for deterministic checks.")
    parser.add_argument(
        "--threshold-days",
        type=int,
        default=DEFAULT_THRESHOLD_DAYS,
        help=f"Stale after this many days (default: {DEFAULT_THRESHOLD_DAYS}).",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        content = args.page.read_text(encoding="utf-8")
        updated = parse_updated_date(content)
        today = _parse_date(args.today, "today") if args.today else date.today()
        result = assess_freshness(updated, today, args.threshold_days)
    except (OSError, FreshnessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(result.as_json(), sort_keys=True))
    else:
        print(
            f"updated={result.updated.isoformat()} "
            f"today={result.today.isoformat()} "
            f"age_days={result.age_days} "
            f"threshold_days={result.threshold_days} "
            f"stale={str(result.stale).lower()}"
        )
    return 2 if result.stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
