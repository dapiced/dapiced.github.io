from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from .nasa_client import APODRecord


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


def generate_article_markdown(apod: APODRecord, image_url: str, image_width: int, image_height: int) -> str:
    intro = (
        f"Each day, the NASA APOD archive turns a different corner of the cosmos into a brief, human-sized window on the universe. "
        f"Today’s image, \"{apod.title}\", is a reminder that even a single observation can carry a surprisingly long story."
    )
    summary = apod.explanation.strip()
    if len(summary) > 700:
        summary = summary[:697].rsplit(" ", 1)[0] + "..."

    credit_line = apod.copyright.strip() if apod.copyright else "Credit: NASA APOD"
    body = f"""{intro}

![{apod.title}]({image_url}){{: width=\"{image_width}\" height=\"{image_height}\" loading=\"eager\" }}

*{credit_line}*

{summary}

## Why it caught my attention

This image stands out because it gives a compact view of a process or object that is easy to overlook when the sky is treated as a background. The science is not a dramatic narrative invented after the fact; it is the reason the observation matters in the first place: a structure, an event, or a field captured with enough clarity to reward a second look.

[Original APOD publication]({apod.apod_url})

*Source data: NASA APOD.*
"""
    return body.strip() + "\n"


def generate_article(apod: APODRecord, image_path: str, width: int, height: int) -> tuple[str, str]:
    slug = slugify_title(apod.title)
    date_value = apod.date
    offset = _local_timezone_offset_for(date_value)
    seo = build_seo_description(apod.title, apod.explanation)
    front_matter = (
        "---\n"
        f"layout: post\n"
        f'title: "APOD: {apod.title}"\n'
        f"date: {date_value} 08:00:00 {offset}\n"
        "tags: [astronomy, nasa, apod]\n"
        f'description: "{seo}"\n'
        f"image: /assets/img/apod/{date_value}-{slug}.webp\n"
        f"apod_date: {date_value}\n"
        f'apod_url: "{apod.apod_url}"\n'
        "generated_by: cosmic-daily\n"
        "---\n\n"
    )
    article_body = generate_article_markdown(apod, image_path, width, height)
    return front_matter, front_matter + article_body
