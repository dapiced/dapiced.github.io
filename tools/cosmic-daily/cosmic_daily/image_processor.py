from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from PIL import Image, ImageOps
import requests


MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_SIDE = 1600
WEBP_QUALITY_START = 85
WEBP_QUALITY_MIN = 40
WEBP_QUALITY_STEP = 5
RESIZE_SCALE_FACTOR = 0.9
MIN_IMAGE_SIDE = 320


def _validate_download_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"Unsupported image URL: {raw_url}")
    return raw_url


def _download_bytes(image_url: str) -> bytes:
    _validate_download_url(image_url)
    response = requests.get(image_url, timeout=20, allow_redirects=False, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Image download returned HTTP {response.status_code} for {image_url}")
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"Unexpected image content type: {content_type}")
    return response.content


def _encode_webp_bytes(image: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=quality)
    return buffer.getvalue()


def process_apod_image(image_url: str, target_directory: str | Path, output_name: str) -> tuple[Path, tuple[int, int]]:
    target_path = Path(target_directory)
    target_path.mkdir(parents=True, exist_ok=True)
    image_bytes = _download_bytes(image_url)
    print(f"Original downloaded image size: {len(image_bytes)} bytes (limit: {MAX_IMAGE_BYTES} bytes)")

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Downloaded image could not be decoded as valid image data.") from exc

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            original = ImageOps.exif_transpose(image).convert("RGB")
            width, height = original.size
            if width <= 0 or height <= 0:
                raise ValueError("Image dimensions are invalid.")
            max_side = max(width, height)
            if max_side > MAX_IMAGE_SIDE:
                scale = MAX_IMAGE_SIDE / max_side
                new_width = max(1, int(round(width * scale)))
                new_height = max(1, int(round(height * scale)))
                original = original.resize((new_width, new_height), Image.Resampling.LANCZOS)
            webp_path = target_path / f"{output_name}.webp"
            if webp_path.exists():
                raise FileExistsError(f"Refusing to overwrite existing image: {webp_path}")
            quality = WEBP_QUALITY_START
            pass_number = 1
            while True:
                encoded = _encode_webp_bytes(original, quality)
                encoded_size = len(encoded)
                print(
                    "Optimization pass "
                    f"{pass_number}: dimensions={original.size[0]}x{original.size[1]}, "
                    f"quality={quality}, output_size={encoded_size} bytes"
                )
                if encoded_size <= MAX_IMAGE_BYTES:
                    webp_path.write_bytes(encoded)
                    size = original.size
                    print(f"Final optimized image size: {encoded_size} bytes")
                    break

                if quality > WEBP_QUALITY_MIN:
                    quality = max(WEBP_QUALITY_MIN, quality - WEBP_QUALITY_STEP)
                    pass_number += 1
                    continue

                next_width = max(1, int(round(original.size[0] * RESIZE_SCALE_FACTOR)))
                next_height = max(1, int(round(original.size[1] * RESIZE_SCALE_FACTOR)))
                if min(next_width, next_height) < MIN_IMAGE_SIDE:
                    if min(original.size) <= MIN_IMAGE_SIDE:
                        raise ValueError(
                            "Image optimization could not satisfy configured size limit "
                            f"(limit={MAX_IMAGE_BYTES} bytes, min_quality={WEBP_QUALITY_MIN}, "
                            f"min_side={MIN_IMAGE_SIDE}px)."
                        )
                    if original.size[0] <= original.size[1]:
                        scale_ratio = MIN_IMAGE_SIDE / original.size[0]
                        next_width = MIN_IMAGE_SIDE
                        next_height = max(1, int(round(original.size[1] * scale_ratio)))
                    else:
                        scale_ratio = MIN_IMAGE_SIDE / original.size[1]
                        next_height = MIN_IMAGE_SIDE
                        next_width = max(1, int(round(original.size[0] * scale_ratio)))
                    next_width = min(next_width, original.size[0], MAX_IMAGE_SIDE)
                    next_height = min(next_height, original.size[1], MAX_IMAGE_SIDE)
                if next_width == original.size[0] and next_height == original.size[1]:
                    raise ValueError(
                        "Image optimization could not satisfy configured size limit "
                        "after exhausting quality and resize attempts."
                    )
                original = original.resize((next_width, next_height), Image.Resampling.LANCZOS)
                quality = WEBP_QUALITY_MIN
                pass_number += 1
    except OSError as exc:
        raise ValueError("Image file format is not recognized or not supported.") from exc

    return webp_path.resolve(), size
