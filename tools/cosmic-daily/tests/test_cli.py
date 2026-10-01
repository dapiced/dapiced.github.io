from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

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
    assert not (repo.root / "_apod").exists()
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
        Image.new("RGB", (1200, 800), "black").save(target, format="WEBP")
        return target, (1200, 800)

    monkeypatch.setattr(cli, "process_apod_image_with_fallback", fake_process)

    exit_code = cli.generate("2026-09-13")

    assert exit_code == cli.EXIT_SUCCESS
    assert seen["urls"] == ["https://apod.nasa.gov/apod/image/hd.jpg", "https://apod.nasa.gov/apod/image/std.jpg"]
    entry = repo.root / "_apod" / "2026-09-13-example-title.md"
    assert entry.exists()
    assert "generated_by: cosmic-daily" in entry.read_text(encoding="utf-8")
    assert not (repo.root / "_posts").exists()


def test_generate_reports_failure_when_no_image_url_works(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())

    def fake_process(urls, target_dir, output_name):
        raise RuntimeError("Image download returned HTTP 404 for https://apod.nasa.gov/apod/image/std.jpg")

    monkeypatch.setattr(cli, "process_apod_image_with_fallback", fake_process)

    exit_code = cli.generate("2026-09-13")

    assert exit_code == cli.EXIT_ERROR
    assert "Image processing failed" in capsys.readouterr().out
    assert not (repo.root / "_apod").exists()


def _fake_process(urls, target_dir, output_name):
    target = Path(target_dir) / f"{output_name}.webp"
    Image.new("RGB", (1200, 800), "black").save(target, format="WEBP")
    return target, (1200, 800)


def test_generate_then_check_validates_apod_entry(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    output = capsys.readouterr().out
    entry = repo.root / "_apod" / "2026-09-13-example-title.md"
    assert f"Generated post: {entry}" in output

    assert cli.check(str(entry)) == cli.EXIT_SUCCESS
    assert "Validation passed" in capsys.readouterr().out


def test_generate_skips_date_already_published_as_legacy_post(monkeypatch, repo, capsys):
    legacy = repo.root / "_posts"
    legacy.mkdir()
    (legacy / "2026-09-13-apod-example-title.md").write_text(
        '---\napod_date: 2026-09-13\napod_url: "https://apod.nasa.gov/apod/ap20260913.html"\n---\n', encoding="utf-8"
    )
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    assert "Duplicate APOD detected" in capsys.readouterr().out
    assert not (repo.root / "_apod").exists()


def test_check_rejects_entry_with_missing_image(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)
    cli.generate("2026-09-13")
    for image in (repo.root / "assets" / "img" / "apod").glob("*.webp"):
        image.unlink()
    capsys.readouterr()

    assert cli.check(str(repo.root / "_apod" / "2026-09-13-example-title.md")) == cli.EXIT_ERROR
    assert "Image file missing" in capsys.readouterr().out


def test_check_rejects_malformed_apod_payload(monkeypatch, repo, capsys):
    entry = repo.root / "_apod" / "2026-10-01-nasa-science.md"
    image = repo.root / "assets" / "img" / "apod" / "2026-10-01-nasa-science.webp"
    image.parent.mkdir(parents=True)
    Image.new("RGB", (121, 102), "black").save(image, format="WEBP")
    entry.parent.mkdir()
    entry.write_text(
        """---
layout: apod
title: "NASA Science"
date: 2026-10-01 08:00:00 -0400
tags: [astronomy, nasa, apod]
description: "NASA Science: Have you ever seen the full moon rise?"
image: /assets/img/apod/2026-10-01-nasa-science.webp
image_width: 320
image_height: 320
credit: "NASA"
apod_date: 2026-10-01
apod_url: "https://apod.nasa.gov/apod/ap20261001.html"
generated_by: cosmic-daily
---

The actual explanation. APOD's main NASA site has moved. Tomorrow's picture: sharpless
""",
        encoding="utf-8",
    )

    assert cli.check(str(entry)) == cli.EXIT_ERROR
    assert "Validation failed" in capsys.readouterr().out


def test_generate_marks_third_party_rights_for_manual_review(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    output = capsys.readouterr().out
    assert "manual review" in output.lower()
    assert (repo.root / "_apod" / "2026-09-13-example-title.md").exists()


def test_generate_rejects_malformed_output_before_persisting(monkeypatch, repo, capsys):
    malformed = _record()
    malformed = APODRecord(
        date=malformed.date,
        title="NASA Science",
        media_type=malformed.media_type,
        url=malformed.url,
        hdurl=malformed.hdurl,
        explanation="APOD's main NASA site has moved. Tomorrow's picture: sharpless",
        copyright="NASA",
        apod_url=malformed.apod_url,
    )
    monkeypatch.setattr(cli, "fetch_apod", lambda target: malformed)
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_ERROR
    assert "Validation failed" in capsys.readouterr().out
    assert not list((repo.root / "_apod").glob("*.md"))
    assert not list((repo.root / "assets" / "img" / "apod").glob("*.webp"))


def _valid_generated_content() -> str:
    _, content = cli.generate_article(
        APODRecord(
            date="2026-09-13",
            title="Example Title",
            media_type="image",
            url="https://apod.nasa.gov/apod/image/std.jpg",
            hdurl=None,
            explanation="An explanation long enough to satisfy the generated article validation contract.",
            copyright="NASA",
            apod_url="https://apod.nasa.gov/apod/ap20260913.html",
        ),
        "/assets/img/apod/2026-09-13-example-title.webp",
        1200,
        800,
    )
    return content


@pytest.mark.parametrize(
    ("mutate", "expected_error"),
    [
        (lambda content: content.replace('title: "Example Title"\n', 'title: "First Title"\ntitle: "Example Title"\n'), "duplicate front matter key"),
        (lambda content: content.replace("date: 2026-09-13 08:00:00 -0400\n", ""), "missing date"),
        (lambda content: content.replace("apod_date: 2026-09-13", "apod_date: not-a-date"), "invalid apod_date"),
        (lambda content: content.replace(
            'apod_url: "https://apod.nasa.gov/apod/ap20260913.html"',
            'apod_url: "https://example.com/not-apod"',
        ), "invalid apod_url"),
    ],
)
def test_parse_rejects_incomplete_or_ambiguous_front_matter(mutate, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        cli._parse_and_validate_post(mutate(_valid_generated_content()))
