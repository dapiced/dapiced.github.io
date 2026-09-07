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
