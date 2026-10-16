"""One GET for every request Cosmic Daily makes to NASA, retried on transient failures.

NASA's servers had a bad afternoon on 16 October 2026: api.nasa.gov answered
HTTP 503 and then timed out for hours, science.nasa.gov briefly served a bot
check. A short retry rides out a blip; it cannot outlast an outage, so the
callers decide what happens next (fall back to the page, or fail loudly).

What is retried: network errors and 502/503/504. Not retried: 429 (the
api.data.gov hourly quota, which only lifts after up to an hour) and 500 (on
api.nasa.gov usually a deterministic error for that date).

Error messages never include the request URL or the exception text, which
for connection errors repeats the full URL with its query string.
"""
from __future__ import annotations

import time

import requests

RETRYABLE_STATUS = frozenset({502, 503, 504})
ATTEMPTS = 3
PAUSES = (5, 15)  # seconds before attempts 2 and 3


class TransientError(RuntimeError):
    """Every attempt failed on the network or with a retryable status."""


def get(url: str, *, label: str, **kwargs) -> requests.Response:
    """requests.get with retries. Returns the first non-retryable response."""
    problem = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = requests.get(url, **kwargs)
        except requests.RequestException as exc:
            problem = type(exc).__name__  # str(exc) can contain the URL and its api_key
        else:
            if response.status_code not in RETRYABLE_STATUS:
                return response
            problem = f"HTTP {response.status_code}"
        print(f"{label}: {problem} (attempt {attempt}/{ATTEMPTS}).", flush=True)
        if attempt < ATTEMPTS:
            time.sleep(PAUSES[attempt - 1])
    raise TransientError(f"{label} failed after {ATTEMPTS} attempts ({problem})")
