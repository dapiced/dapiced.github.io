from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from .nasa_client import APODRecord
from .rights_policy import evaluate_media_rights


SEO_TEXT_MIN = 120
SEO_TEXT_MAX = 160


def slugify_title(title: str) -> str:
    normalized = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized)
    slug = slug.strip("-")
    return slug or "apod"


def _local_timezone_offset_for(date_value: str) -> str:
    tz = ZoneInfo("America/Toronto")
    local_dt = datetime.fromisoformat(f"{date_value}T00:00:00").replace(tzinfo=tz)
    offset = local_dt.utcoffset()
    if offset is None:
        return "-0500"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}{minutes:02d}"


def build_seo_description(title: str, explanation: str) -> str:
    base = f"{title}: {explanation.strip()}"
    cleaned = re.sub(r"\s+", " ", base).strip()
    if len(cleaned) <= SEO_TEXT_MAX:
        return cleaned[:SEO_TEXT_MAX]
    trimmed = cleaned[:SEO_TEXT_MAX].rsplit(" ", 1)[0]
    return trimmed if len(trimmed) >= SEO_TEXT_MIN else cleaned[:SEO_TEXT_MAX]


def _yaml_string(value: str) -> str:
    return json.dumps(re.sub(r"\s+", " ", value).strip(), ensure_ascii=False)


def generate_article_markdown(apod: APODRecord) -> str:
    return apod.explanation.strip() + "\n"


def generate_article(apod: APODRecord, image_path: str, width: int, height: int) -> tuple[str, str]:
    """Build a factual APOD collection entry. The optional `note` field is left for a human to add."""
    date_value = apod.date
    offset = _local_timezone_offset_for(date_value)
    seo = build_seo_description(apod.title, apod.explanation)
    decision = evaluate_media_rights(apod.media_type, apod.copyright)
    credit = apod.copyright.strip() if apod.copyright and apod.copyright.strip() else "Rights metadata unavailable"
    front_matter = (
        "---\n"
        "layout: apod\n"
        f"title: {_yaml_string(apod.title)}\n"
        f"date: {date_value} 08:00:00 {offset}\n"
        "tags: [astronomy, nasa, apod]\n"
        f"description: {_yaml_string(seo)}\n"
        f"image: {image_path}\n"
        f"image_width: {width}\n"
        f"image_height: {height}\n"
        f"credit: {_yaml_string(credit)}\n"
        f"rights_status: {decision.status}\n"
        f"apod_date: {date_value}\n"
        f'apod_url: "{apod.apod_url}"\n'
        "generated_by: cosmic-daily\n"
        "---\n\n"
    )
    return front_matter, front_matter + generate_article_markdown(apod)
