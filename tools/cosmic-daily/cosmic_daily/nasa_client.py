from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests


APOD_ENDPOINT = "https://api.nasa.gov/planetary/apod"
# DEMO_KEY is a shared, rate-limited key; requests can be slow under load, so
# use a generous read timeout and retry a couple of times before giving up.
REQUEST_TIMEOUT = (10, 45)
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5


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

    response = None
    last_error: requests.RequestException | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                APOD_ENDPOINT,
                params={"api_key": configured_key, "date": target_day},
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    if response is None:
        raise RuntimeError(
            f"Failed to fetch APOD for {target_day} after {MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error

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
