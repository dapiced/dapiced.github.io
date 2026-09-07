from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from cosmic_daily.image_processor import process_apod_image


def test_process_apod_image_converts_to_webp(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    image = Image.new("RGB", (2200, 1200), color="blue")
    image.save(buffer, format="PNG")
    payload = buffer.getvalue()

    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = payload

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse())
    target, size = process_apod_image("https://example.com/image.png", tmp_path, "2024-03-15-demo")

    assert target.suffix == ".webp"
    assert target.exists()
    assert size[0] <= 1600
    assert size[1] <= 1600
