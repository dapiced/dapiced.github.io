from __future__ import annotations

import pytest

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


def test_fetch_apod_network_error_raises(monkeypatch):
    def fake_get(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(RuntimeError):
        fetch_apod("2024-01-01", api_key="DEMO_KEY")


PAYLOAD = {
    "date": "2026-10-16",
    "title": "Example title",
    "media_type": "image",
    "url": "https://example.com/image.jpg",
    "explanation": "Example explanation",
    "apod_url": "https://apod.nasa.gov/apod/ap20261016.html",
}


@pytest.fixture
def no_sleep(monkeypatch):
    waits = []
    monkeypatch.setattr("cosmic_daily.nasa_client.time.sleep", waits.append)
    return waits


def test_transient_5xx_is_retried_with_growing_pauses(monkeypatch, no_sleep):
    answers = [DummyResponse(status_code=503), DummyResponse(status_code=502), DummyResponse(PAYLOAD)]
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: answers.pop(0))

    record = fetch_apod("2026-10-16", api_key="key")

    assert record.title == "Example title"
    assert no_sleep == [10, 20]


def test_persistent_503_fails_after_the_last_attempt(monkeypatch, no_sleep):
    calls = []
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: calls.append(1) or DummyResponse(status_code=503))

    with pytest.raises(RuntimeError, match="HTTP 503"):
        fetch_apod("2026-10-16", api_key="key")
    assert len(calls) == 4 and no_sleep == [10, 20, 30]


def test_client_errors_are_not_retried(monkeypatch, no_sleep):
    calls = []
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: calls.append(1) or DummyResponse(status_code=403))

    with pytest.raises(RuntimeError, match="HTTP 403"):
        fetch_apod("2026-10-16", api_key="key")
    assert len(calls) == 1 and no_sleep == []


def test_network_error_then_success(monkeypatch, no_sleep):
    import requests

    answers = [requests.ConnectionError("reset"), DummyResponse(PAYLOAD)]

    def fake_get(*args, **kwargs):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr("requests.get", fake_get)
    assert fetch_apod("2026-10-16", api_key="key").date == "2026-10-16"
    assert no_sleep == [10]
