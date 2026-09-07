from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from PIL import Image, ImageOps
import requests


MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_SIDE = 1600


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
    content = response.content
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds configured size limit.")
    return content


def process_apod_image(image_url: str, target_directory: str | Path, output_name: str) -> tuple[Path, tuple[int, int]]:
    target_path = Path(target_directory)
    target_path.mkdir(parents=True, exist_ok=True)
    image_bytes = _download_bytes(image_url)

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
            original.save(webp_path, format="WEBP", quality=85)
            size = original.size
    except OSError as exc:
        raise ValueError("Image file format is not recognized or not supported.") from exc

    return webp_path.resolve(), size
