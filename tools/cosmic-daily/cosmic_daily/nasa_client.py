from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional
from urllib.parse import urlparse


from . import http
from .apod_page import fetch_apod_page


APOD_ENDPOINT = "https://api.nasa.gov/planetary/apod"
# DEMO_KEY is a shared, rate-limited key; requests can be slow under load, so
# use a generous read timeout. Retries are in cosmic_daily/http.py.
REQUEST_TIMEOUT = (10, 45)
# Since APOD moved to science.nasa.gov, the API scrapes the redirected old page
# and answers with the site name as title and the site logo as image.
DEGRADED_TITLES = {"nasa science", "apod - nasa science"}
DEGRADED_MEDIA_PATH = "/wp-content/"


@dataclass
class APODRecord:
    date: str
    title: str
    media_type: str
    url: str
    hdurl: Optional[str]
    explanation: str
    copyright: Optional[str]
    apod_url: str
    service_version: Optional[str] = None
    # science.nasa.gov page of the entry; a video entry links its picture there.
    page_url: Optional[str] = None


def _validate_https_url(raw_url: str, field_name: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field_name} must be an https URL")
    return raw_url


def build_apod_url(day: date) -> str:
    return f"https://apod.nasa.gov/apod/ap{day:%Y%m%d}.html"


def _coerce_date(value: Any) -> str:
    if not value:
        raise ValueError("APOD date is missing")
    text = str(value)
    try:
        valid = date.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid APOD date: {text}") from exc
    return valid.isoformat()


def fetch_apod(day: str | date | None = None, api_key: str | None = None) -> APODRecord:
    target_day = day.isoformat() if isinstance(day, date) else (str(day) if day else date.today().isoformat())
    configured_key = api_key or os.getenv("NASA_API_KEY") or "DEMO_KEY"

    try:
        # The key goes in a header (api.data.gov accepts X-Api-Key), never in the
        # URL: a connection error's text repeats the full URL, and that text can
        # reach the log tail that the workflow copies into a public issue.
        response = http.get(
            APOD_ENDPOINT,
            label="NASA API",
            params={"date": target_day},
            headers={"X-Api-Key": configured_key},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except http.TransientError as exc:
        # The entry is built from the science.nasa.gov page on most days anyway
        # (see _is_degraded); an API outage should not block it (16 October 2026).
        print(f"{exc}; reading the science.nasa.gov page instead.", flush=True)
        day_value = date.fromisoformat(target_day)
        return _record_from_page(day_value, build_apod_url(day_value), {})

    if response.status_code != 200:
        raise RuntimeError(f"NASA API returned HTTP {response.status_code} for {target_day}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError(f"NASA API returned invalid JSON for {target_day}") from exc

    if not isinstance(payload, dict):
        raise ValueError("NASA API response is not a JSON object")

    required_fields = ["date", "title", "media_type", "url", "explanation"]
    missing = [name for name in required_fields if name not in payload or payload.get(name) in (None, "")]
    if missing:
        raise ValueError(f"APOD payload missing required fields: {', '.join(missing)}")

    chosen_day = _coerce_date(payload["date"])
    apod_url = payload.get("apod_url") or build_apod_url(date.fromisoformat(chosen_day))
    _validate_https_url(apod_url, "apod_url")
    media_url = payload.get("url")
    if not media_url:
        raise ValueError("APOD media URL is required")
    _validate_https_url(media_url, "url")

    hdurl = payload.get("hdurl")
    if hdurl:
        _validate_https_url(hdurl, "hdurl")

    if _is_degraded(payload):
        return _record_from_page(date.fromisoformat(chosen_day), apod_url, payload)

    return APODRecord(
        date=chosen_day,
        title=str(payload["title"]).strip(),
        media_type=str(payload["media_type"]).strip().lower(),
        url=str(media_url),
        hdurl=str(hdurl) if hdurl else None,
        explanation=str(payload["explanation"]).strip(),
        copyright=str(payload["copyright"]).strip() if payload.get("copyright") else None,
        apod_url=str(apod_url),
        service_version=str(payload.get("service_version")) if payload.get("service_version") else None,
    )


def _is_degraded(payload: Dict[str, Any]) -> bool:
    if str(payload.get("title", "")).strip().lower() in DEGRADED_TITLES:
        return True
    for field_name in ("url", "hdurl"):
        parsed = urlparse(str(payload.get(field_name) or ""))
        if parsed.netloc.endswith("science.nasa.gov") and parsed.path.startswith(DEGRADED_MEDIA_PATH):
            return True
    return False


def _record_from_page(day: date, apod_url: str, payload: Dict[str, Any]) -> APODRecord:
    """Rebuild the record from the science.nasa.gov page; raises ApodUnavailableError."""
    print("NASA API returned placeholder APOD metadata; reading the science.nasa.gov page instead.")
    page = fetch_apod_page(day)
    if page.media_type == "video":
        url, hdurl = page.video_url or "", None
    else:
        url = page.image_urls[-1]
        hdurl = page.image_urls[0] if len(page.image_urls) > 1 else None
    return APODRecord(
        date=page.date,
        title=page.title,
        media_type=page.media_type,
        url=url,
        hdurl=hdurl,
        explanation=page.explanation,
        copyright=page.credit,
        apod_url=apod_url,
        service_version=str(payload.get("service_version")) if payload.get("service_version") else None,
        page_url=page.page_url,
    )

