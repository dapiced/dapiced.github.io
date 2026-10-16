"""Frame extraction with the bundled ffmpeg (imageio-ffmpeg), on a generated clip."""
from __future__ import annotations

import io
import subprocess

import imageio_ffmpeg
import pytest
from PIL import Image

import cosmic_daily.video_frame as video_frame


@pytest.fixture(scope="module")
def clip(tmp_path_factory):
    path = tmp_path_factory.mktemp("video") / "clip.mp4"
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "lavfi",
         "-i", "testsrc=duration=4:size=320x240:rate=10", "-pix_fmt", "yuv420p", str(path)],
        check=True, timeout=60,
    )
    return path


def test_duration_and_middle_frame(clip):
    assert video_frame.video_duration(clip) == pytest.approx(4, abs=0.2)
    with Image.open(io.BytesIO(video_frame.extract_frame(clip, 2.0))) as frame:
        assert frame.format == "PNG" and frame.size == (320, 240)


def test_only_apod_library_videos_are_downloaded(tmp_path):
    with pytest.raises(ValueError, match="APOD media library"):
        video_frame.download_video("https://www.youtube.com/watch?v=abc", tmp_path / "v")
