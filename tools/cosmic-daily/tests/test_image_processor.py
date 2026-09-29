from __future__ import annotations

import io

import pytest
import requests

from PIL import Image

import cosmic_daily.image_processor as image_processor
from cosmic_daily.image_processor import process_apod_image, process_apod_image_with_fallback


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


def test_process_apod_image_under_limit_stays_single_pass(monkeypatch, tmp_path, capsys):
    payload = _checkerboard_payload(400, 300)

    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = payload

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse())
    target, _ = process_apod_image("https://example.com/image.png", tmp_path, "small")

    output = capsys.readouterr().out
    assert target.exists()
    assert target.stat().st_size <= image_processor.MAX_IMAGE_BYTES
    assert "Optimization pass 1" in output
    assert "Optimization pass 2" not in output


def test_process_apod_image_oversized_is_optimized(monkeypatch, tmp_path, capsys):
    payload = _checkerboard_payload(1600, 1600)

    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = payload

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse())
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

    class DummyResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = payload

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResponse())
    monkeypatch.setattr(image_processor, "MAX_IMAGE_BYTES", 50)
    monkeypatch.setattr(image_processor, "MIN_IMAGE_SIDE", 1400)
    with pytest.raises(ValueError, match="Image optimization could not satisfy configured size limit"):
        process_apod_image("https://example.com/image.png", tmp_path, "cannot-fit")


def _response_for(url_to_status: dict[str, int], payload: bytes):
    def fake_get(url, *args, **kwargs):
        class DummyResponse:
            status_code = url_to_status[url]
            headers = {"Content-Type": "image/png"}
            content = payload

        return DummyResponse()

    return fake_get


def test_fallback_uses_next_url_when_hd_download_fails(monkeypatch, tmp_path, capsys):
    payload = _checkerboard_payload(400, 300)
    monkeypatch.setattr(
        "requests.get",
        _response_for({"https://example.com/hd.png": 404, "https://example.com/std.png": 200}, payload),
    )

    target, size = process_apod_image_with_fallback(
        ["https://example.com/hd.png", "https://example.com/std.png"], tmp_path, "fallback"
    )

    output = capsys.readouterr().out
    assert target.exists()
    assert size == (400, 300)
    assert "HTTP 404" in output
    assert "https://example.com/std.png" in output


def test_fallback_skips_duplicate_and_empty_candidates(monkeypatch, tmp_path):
    payload = _checkerboard_payload(400, 300)
    calls: list[str] = []

    def fake_get(url, *args, **kwargs):
        calls.append(url)

        class DummyResponse:
            status_code = 200
            headers = {"Content-Type": "image/png"}
            content = payload

        return DummyResponse()

    monkeypatch.setattr("requests.get", fake_get)
    process_apod_image_with_fallback(
        [None, "https://example.com/same.png", "https://example.com/same.png"], tmp_path, "dedup"
    )

    assert calls == ["https://example.com/same.png"]


def test_fallback_uses_next_url_when_hd_download_times_out(monkeypatch, tmp_path):
    payload = _checkerboard_payload(400, 300)
    calls: list[str] = []

    def fake_get(url, *args, **kwargs):
        calls.append(url)
        if url.endswith("hd.png"):
            raise requests.exceptions.ReadTimeout("read timed out")

        class DummyResponse:
            status_code = 200
            headers = {"Content-Type": "image/png"}
            content = payload

        return DummyResponse()

    monkeypatch.setattr("requests.get", fake_get)
    target, size = process_apod_image_with_fallback(
        ["https://example.com/hd.png", "https://example.com/std.png"], tmp_path, "timeout"
    )

    assert target.exists()
    assert size == (400, 300)
    assert calls == ["https://example.com/hd.png", "https://example.com/std.png"]


def test_fallback_raises_last_error_when_every_url_fails(monkeypatch, tmp_path):
    payload = _checkerboard_payload(400, 300)
    monkeypatch.setattr(
        "requests.get",
        _response_for({"https://example.com/hd.png": 403, "https://example.com/std.png": 404}, payload),
    )

    with pytest.raises(RuntimeError, match="HTTP 404"):
        process_apod_image_with_fallback(
            ["https://example.com/hd.png", "https://example.com/std.png"], tmp_path, "all-fail"
        )


def test_fallback_rejects_empty_candidate_list(tmp_path):
    with pytest.raises(ValueError, match="No image URL"):
        process_apod_image_with_fallback([None, ""], tmp_path, "empty")
