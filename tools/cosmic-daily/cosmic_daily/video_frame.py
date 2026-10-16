"""One frame of an APOD video, used as the entry's picture.

Since APOD moved to science.nasa.gov, a video entry is an MP4 file from the
APOD media library, played by NASA's own player. The site never hosts or embeds
the video: it shows one frame of it, and the picture links to NASA's page.

The frame is taken from the middle of the video: the first frame is often black
or a title card. ffmpeg comes from the imageio-ffmpeg wheel, so the same static
binary runs on the GitHub runner and on a laptop, without apt.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

from . import http
from .apod_page import is_library_video


MAX_VIDEO_BYTES = 300 * 1024 * 1024
REQUEST_TIMEOUT = (10, 120)
CHUNK_BYTES = 1024 * 1024


def download_video(video_url: str, target: Path) -> Path:
    """Stream the video to ``target``; only APOD media library files are accepted."""
    if not is_library_video(video_url):
        raise ValueError(f"Not a video from the APOD media library: {video_url}")
    # Only opening the stream is retried; a reset mid-download fails the run.
    with http.get(video_url, label="Video download", timeout=REQUEST_TIMEOUT,
                  allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise RuntimeError(f"Video download returned HTTP {response.status_code} for {video_url}")
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("video/"):
            raise ValueError(f"Unexpected video content type: {content_type}")
        written = 0
        with open(target, "wb") as handle:
            for chunk in response.iter_content(CHUNK_BYTES):
                written += len(chunk)
                if written > MAX_VIDEO_BYTES:
                    raise ValueError(f"Video is larger than {MAX_VIDEO_BYTES} bytes")
                handle.write(chunk)
    print(f"Downloaded video: {written} bytes")
    return target


def video_duration(path: Path) -> float:
    _frames, seconds = imageio_ffmpeg.count_frames_and_secs(str(path))
    return float(seconds or 0)


def extract_frame(path: Path, at_seconds: float) -> bytes:
    """PNG bytes of the frame at ``at_seconds``."""
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-ss", f"{max(at_seconds, 0):.3f}",
        "-i", str(path), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
    ]
    result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    if result.returncode != 0 or not result.stdout:
        raise ValueError(f"Could not extract a frame: {result.stderr.decode(errors='replace').strip()[:300]}")
    return result.stdout


def poster_frame(video_url: str) -> bytes:
    """Download the video, then return the PNG frame from its middle."""
    with tempfile.TemporaryDirectory(prefix="cosmic-daily-video-") as temp_dir:
        video = download_video(video_url, Path(temp_dir) / "video")
        duration = video_duration(video)
        at = duration / 2 if duration > 0 else 1.0
        print(f"Video duration: {duration:.1f} s; frame taken at {at:.1f} s")
        return extract_frame(video, at)
