from __future__ import annotations

import io

import pytest

from PIL import Image

import cosmic_daily.image_processor as image_processor
from cosmic_daily.image_processor import process_apod_image


def _checkerboard_payload(width: int, height: int, block: int = 8) -> bytes:
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            parity = ((x // block) + (y // block)) % 2
            pixels[x, y] = (255, 20, 20) if parity == 0 else (20, 20, 255)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class DummyResponse:
    def __init__(self, payload: bytes, *, content_type: str = "image/png", content_length: int | None = None):
        self.status_code = 200
        self.headers = {"Content-Type": content_type}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
        self._payload = payload

    def iter_content(self, chunk_size: int = 1):
        for start in range(0, len(self._payload), chunk_size):
            yield self._payload[start : start + chunk_size]


def test_process_apod_image_converts_to_webp(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    image = Image.new("RGB", (2200, 1200), color="blue")
    image.save(buffer, format="PNG")
    payload = buffer.getvalue()

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse(payload))
    target, size = process_apod_image("https://example.com/image.png", tmp_path, "2024-03-15-demo")

    assert target.suffix == ".webp"
    assert target.exists()
    assert size[0] <= 1600
    assert size[1] <= 1600


def test_process_apod_image_under_limit_stays_single_pass(monkeypatch, tmp_path, capsys):
    payload = _checkerboard_payload(400, 300)

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse(payload))
    target, _ = process_apod_image("https://example.com/image.png", tmp_path, "small")

    output = capsys.readouterr().out
    assert target.exists()
    assert target.stat().st_size <= image_processor.MAX_IMAGE_BYTES
    assert "Optimization pass 1" in output
    assert "Optimization pass 2" not in output


def test_process_apod_image_oversized_is_optimized(monkeypatch, tmp_path, capsys):
    payload = _checkerboard_payload(1600, 1600)

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse(payload))
    monkeypatch.setattr(image_processor, "MAX_IMAGE_BYTES", 20_000)
    target, size = process_apod_image("https://example.com/image.png", tmp_path, "optimized")

    output = capsys.readouterr().out
    assert target.exists()
    assert "Optimization pass 2" in output
    assert target.stat().st_size <= image_processor.MAX_IMAGE_BYTES
    assert size[0] <= 1600
    assert size[1] <= 1600


def test_process_apod_image_fails_when_optimization_cannot_fit(monkeypatch, tmp_path):
    payload = _checkerboard_payload(1600, 1600)

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse(payload))
    monkeypatch.setattr(image_processor, "MAX_IMAGE_BYTES", 50)
    monkeypatch.setattr(image_processor, "MIN_IMAGE_SIDE", 1400)
    with pytest.raises(ValueError, match="Image optimization could not satisfy configured size limit"):
        process_apod_image("https://example.com/image.png", tmp_path, "cannot-fit")


def test_process_apod_image_rejects_oversized_download(monkeypatch, tmp_path):
    payload = _checkerboard_payload(400, 300)

    monkeypatch.setattr(
        "requests.get",
        lambda *args, **kwargs: DummyResponse(payload, content_length=image_processor.MAX_DOWNLOAD_BYTES + 1),
    )

    with pytest.raises(ValueError, match="Downloaded image exceeds configured input size limit"):
        process_apod_image("https://example.com/image.png", tmp_path, "too-large")


def test_process_apod_image_rejects_streamed_oversized_download(monkeypatch, tmp_path):
    payload = _checkerboard_payload(400, 300)

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse(payload))
    monkeypatch.setattr(image_processor, "MAX_DOWNLOAD_BYTES", len(payload) - 1)

    with pytest.raises(ValueError, match="Downloaded image exceeds configured input size limit"):
        process_apod_image("https://example.com/image.png", tmp_path, "stream-too-large")
