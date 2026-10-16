from __future__ import annotations

import pytest
import requests

from cosmic_daily import http, nasa_client
from cosmic_daily.nasa_client import APODRecord, fetch_apod


class DummyResponse:
    def __init__(self, payload=None, status_code=200, headers=None):
        self.payload = payload if payload is not None else {}
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self.payload


def test_fetch_apod_success(monkeypatch):
    payload = {
        "date": "2024-01-01",
        "title": "Example title",
        "media_type": "image",
        "url": "https://example.com/image.jpg",
        "hdurl": "https://example.com/image-hd.jpg",
        "explanation": "Example explanation",
        "copyright": "NASA",
        "apod_url": "https://apod.nasa.gov/apod/ap20240101.html",
    }

    def fake_get(*args, **kwargs):
        return DummyResponse(payload)

    monkeypatch.setattr("requests.get", fake_get)
    record = fetch_apod("2024-01-01", api_key="DEMO_KEY")

    assert isinstance(record, APODRecord)
    assert record.date == "2024-01-01"
    assert record.media_type == "image"
    assert record.apod_url.endswith("ap20240101.html")


def test_fetch_apod_missing_field_raises(monkeypatch):
    def fake_get(*args, **kwargs):
        return DummyResponse({"date": "2024-01-01", "title": "Example"})

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(ValueError):
        fetch_apod("2024-01-01", api_key="DEMO_KEY")


def test_api_and_page_both_down_fails_loudly(monkeypatch):
    # Network errors on every request: the API retries, the page fallback
    # retries too, then the run fails (an issue), it is never a silent skip.
    def fake_get(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(http.TransientError, match="APOD page failed after 3 attempts"):
        fetch_apod("2024-01-01", api_key="DEMO_KEY")



# --- Retries and fallback (cosmic_daily/http.py) -------------------------------

PAYLOAD = {
    "date": "2026-10-16",
    "title": "Example title",
    "media_type": "image",
    "url": "https://example.com/image.jpg",
    "explanation": "Example explanation",
    "apod_url": "https://apod.nasa.gov/apod/ap20261016.html",
}


def _answers(monkeypatch, *answers):
    """requests.get serves these in order (an exception is raised); returns the URLs asked."""
    queue, asked = list(answers), []

    def fake_get(url, *args, **kwargs):
        asked.append((url, kwargs))
        answer = queue.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr("requests.get", fake_get)
    return asked


def test_api_key_is_sent_in_a_header_never_in_the_url(monkeypatch):
    asked = _answers(monkeypatch, DummyResponse(PAYLOAD))
    fetch_apod("2026-10-16", api_key="secret-key")
    url, kwargs = asked[0]
    assert kwargs["headers"] == {"X-Api-Key": "secret-key"}
    assert "secret-key" not in url and "api_key" not in kwargs["params"]


def test_transient_5xx_is_retried(monkeypatch, pauses):
    _answers(monkeypatch, DummyResponse(status_code=503), DummyResponse(status_code=502), DummyResponse(PAYLOAD))
    assert fetch_apod("2026-10-16", api_key="k").title == "Example title"
    assert pauses == [5, 15]


@pytest.mark.parametrize("status", [400, 403, 404, 429, 500])
def test_other_statuses_fail_at_once(monkeypatch, pauses, status):
    # 429 is the hourly quota and 500 a deterministic API error: a retry cannot help.
    asked = _answers(monkeypatch, DummyResponse(status_code=status))
    with pytest.raises(RuntimeError, match=f"HTTP {status}"):
        fetch_apod("2026-10-16", api_key="k")
    assert len(asked) == 1 and pauses == []


def test_api_outage_falls_back_to_the_page(monkeypatch, pauses):
    # 16 October 2026: api.nasa.gov down for hours while the page was fine.
    _answers(monkeypatch, DummyResponse(status_code=503), requests.ConnectionError("x"), requests.ReadTimeout("x"))
    seen = []
    monkeypatch.setattr(nasa_client, "fetch_apod_page", lambda day: seen.append(day) or _page(day))
    record = fetch_apod("2026-10-16", api_key="k")
    assert [d.isoformat() for d in seen] == ["2026-10-16"]
    assert record.title == "From the page" and record.apod_url.endswith("ap20261016.html")
    assert pauses == [5, 15]


def test_transient_error_message_never_contains_the_url(monkeypatch):
    leaky = requests.ConnectionError("Max retries exceeded with url: /planetary/apod?api_key=SECRET")
    _answers(monkeypatch, leaky, leaky, leaky)
    with pytest.raises(http.TransientError) as caught:
        http.get("https://api.nasa.gov/planetary/apod?api_key=SECRET", label="NASA API")
    assert "SECRET" not in str(caught.value) and "ConnectionError" in str(caught.value)


def test_network_error_then_success(monkeypatch, pauses):
    _answers(monkeypatch, requests.ConnectionError("reset"), DummyResponse(PAYLOAD))
    assert fetch_apod("2026-10-16", api_key="k").date == "2026-10-16"
    assert pauses == [5]


def _page(day):
    from cosmic_daily.apod_page import ApodPage

    return ApodPage(
        date=day.isoformat(), title="From the page", explanation="An explanation.", credit="NASA",
        image_urls=("https://assets.science.nasa.gov/content/dam/science/cds/apod/x.jpg",),
    )
