"""Shared fixtures for the Cosmic Daily tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def pauses(monkeypatch):
    """No test really waits between retries (cosmic_daily/http.py); the pauses are recorded."""
    waits: list[float] = []
    monkeypatch.setattr("cosmic_daily.http.time.sleep", waits.append)
    return waits
