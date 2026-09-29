from __future__ import annotations

from pathlib import Path

import pytest

import cosmic_daily.cli as cli
from cosmic_daily.nasa_client import APODRecord
from cosmic_daily.repository import RepositoryContext


def _record(media_type: str = "image", hdurl: str | None = "https://apod.nasa.gov/apod/image/hd.jpg") -> APODRecord:
    return APODRecord(
        date="2026-09-13",
        title="Example Title",
        media_type=media_type,
        url="https://apod.nasa.gov/apod/image/std.jpg",
        hdurl=hdurl,
        explanation="An explanation long enough to be useful for the description of the post.",
        copyright="Jane Photographer",
        apod_url="https://apod.nasa.gov/apod/ap20260913.html",
    )


@pytest.fixture
def repo(monkeypatch, tmp_path) -> RepositoryContext:
    context = RepositoryContext(repo_root=tmp_path)
    monkeypatch.setattr(cli, "RepositoryContext", lambda *args, **kwargs: context)
    monkeypatch.chdir(tmp_path)
    return context


def test_generate_skips_video_entries_without_failing(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record(media_type="video", hdurl=None))

    exit_code = cli.generate("2026-09-13")

    output = capsys.readouterr().out
    assert exit_code == cli.EXIT_SUCCESS
    assert "Skipped" in output
    assert not (repo.root / "_posts").exists()
    assert not (repo.root / "assets").exists()


def test_preview_skips_video_entries_without_failing(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record(media_type="video", hdurl=None))

    exit_code = cli.preview("2026-09-13")

    output = capsys.readouterr().out
    assert exit_code == cli.EXIT_SUCCESS
    assert '"media_type": "video"' in output
    assert "Skipped" in output


def test_generate_tries_hd_then_standard_url(monkeypatch, repo):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    seen: dict[str, object] = {}

    def fake_process(urls, target_dir, output_name):
        seen["urls"] = list(urls)
        target = Path(target_dir) / f"{output_name}.webp"
        target.write_bytes(b"webp")
        return target, (1200, 800)

    monkeypatch.setattr(cli, "process_apod_image_with_fallback", fake_process)

    exit_code = cli.generate("2026-09-13")

    assert exit_code == cli.EXIT_SUCCESS
    assert seen["urls"] == ["https://apod.nasa.gov/apod/image/hd.jpg", "https://apod.nasa.gov/apod/image/std.jpg"]
    post = repo.root / "_posts" / "2026-09-13-apod-example-title.md"
    assert post.exists()
    assert "generated_by: cosmic-daily" in post.read_text(encoding="utf-8")


def test_generate_reports_failure_when_no_image_url_works(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())

    def fake_process(urls, target_dir, output_name):
        raise RuntimeError("Image download returned HTTP 404 for https://apod.nasa.gov/apod/image/std.jpg")

    monkeypatch.setattr(cli, "process_apod_image_with_fallback", fake_process)

    exit_code = cli.generate("2026-09-13")

    assert exit_code == cli.EXIT_ERROR
    assert "Image processing failed" in capsys.readouterr().out
    assert not (repo.root / "_posts").exists()
