from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

import cosmic_daily.cli as cli
from cosmic_daily.apod_page import ApodUnavailableError
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


def _unavailable(target):
    raise ApodUnavailableError("APOD page has no still image from the APOD media library")


@pytest.mark.parametrize("command", ["generate", "preview"])
def test_unavailable_apod_entry_is_skipped_without_failing(monkeypatch, repo, capsys, command):
    monkeypatch.setattr(cli, "fetch_apod", _unavailable)

    exit_code = getattr(cli, command)("2026-10-10")

    output = capsys.readouterr().out
    assert exit_code == cli.EXIT_SUCCESS
    # The workflow keys its run summary on lines starting with "Skipped:".
    assert any(line.startswith("Skipped: APOD entry unavailable") for line in output.splitlines())
    assert not (repo.root / "_apod").exists()
    assert not (repo.root / "assets").exists()


@pytest.mark.parametrize("copyright", [None, "   "])
def test_preview_manual_review_is_successful_and_persists_nothing(monkeypatch, repo, capsys, copyright):
    record = _record()
    record = APODRecord(**{**record.__dict__, "copyright": copyright})
    monkeypatch.setattr(cli, "fetch_apod", lambda target: record)
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    exit_code = cli.preview("2026-09-13")

    output = capsys.readouterr().out.lower()
    assert exit_code == cli.EXIT_SUCCESS
    assert "manual review" in output
    assert "preview article:" in output
    assert not (repo.root / "_apod").exists()
    assert not (repo.root / "assets").exists()


def test_preview_manual_review_ignores_existing_published_duplicate(monkeypatch, repo, capsys):
    existing = repo.root / "_apod"
    existing.mkdir()
    (existing / "2026-09-13-existing.md").write_text(
        '---\napod_date: 2026-09-13\napod_url: "https://apod.nasa.gov/apod/ap20260913.html"\n---\n',
        encoding="utf-8",
    )
    uncredited = APODRecord(**{**_record().__dict__, "copyright": None})
    monkeypatch.setattr(cli, "fetch_apod", lambda target: uncredited)
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.preview("2026-09-13") == cli.EXIT_SUCCESS
    assert "manual review" in capsys.readouterr().out.lower()
    assert list(existing.glob("*.md")) == [existing / "2026-09-13-existing.md"]
    assert not (repo.root / "assets").exists()


def test_preview_invalid_candidate_fails_without_persisting(monkeypatch, repo, capsys):
    record = _record()
    malformed = APODRecord(**{
        **record.__dict__,
        "title": "NASA Science",
        "copyright": "NASA",
    })
    monkeypatch.setattr(cli, "fetch_apod", lambda target: malformed)
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.preview("2026-09-13") == cli.EXIT_ERROR
    assert "Preview validation failed" in capsys.readouterr().out
    assert not (repo.root / "_apod").exists()
    assert not (repo.root / "assets").exists()


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


def test_generate_publishes_third_party_credit_without_manual_review(monkeypatch, repo, capsys):
    # Owner's choice: third-party images are republished with their credit.
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    output = capsys.readouterr().out
    assert "manual review" not in output.lower()
    content = (repo.root / "_apod" / "2026-09-13-example-title.md").read_text(encoding="utf-8")
    assert 'credit: "Jane Photographer"' in content
    assert "rights_status: allowed" in content


@pytest.mark.parametrize("copyright", [None, "   "])
def test_generate_missing_rights_keeps_explicit_manual_review_credit(monkeypatch, repo, capsys, copyright):
    record = _record()
    record = APODRecord(**{**record.__dict__, "copyright": copyright})
    monkeypatch.setattr(cli, "fetch_apod", lambda target: record)
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    output = capsys.readouterr().out.lower()
    content = (repo.root / "_apod" / "2026-09-13-example-title.md").read_text(encoding="utf-8")
    assert "manual review" in output
    assert 'credit: "Rights metadata unavailable"' in content
    assert "rights_status: manual_review" in content
    assert 'credit: "NASA"' not in content


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


@pytest.mark.parametrize(
    "content",
    [
        lambda text: text.replace("rights_status: allowed", "rights_status: manual_review"),
        lambda text: text.replace('credit: "NASA"', 'credit: "Rights metadata unavailable"'),
    ],
)
def test_parse_rejects_inconsistent_rights_status_and_credit(content):
    with pytest.raises(ValueError, match="rights status"):
        cli._parse_and_validate_post(content(_valid_generated_content()))


def test_generate_writes_grid_thumbnail(monkeypatch, repo):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _record())
    monkeypatch.setattr(cli, "process_apod_image_with_fallback", _fake_process)

    assert cli.generate("2026-09-13") == cli.EXIT_SUCCESS
    thumbnail = repo.root / "assets" / "img" / "apod" / "thumbs" / "2026-09-13-example-title.webp"
    with Image.open(thumbnail) as image:
        assert image.size == (640, 427)


def test_thumbnails_backfills_only_missing_files(repo, capsys):
    images = repo.root / "assets" / "img" / "apod"
    images.mkdir(parents=True)
    for name in ("a", "b"):
        Image.new("RGB", (1600, 900), "navy").save(images / f"{name}.webp", format="WEBP")
    (images / "thumbs").mkdir()
    Image.new("RGB", (10, 10), "red").save(images / "thumbs" / "a.webp", format="WEBP")

    assert cli.thumbnails() == cli.EXIT_SUCCESS
    assert "Thumbnails created: 1" in capsys.readouterr().out
    with Image.open(images / "thumbs" / "a.webp") as kept:
        assert kept.size == (10, 10)
    with Image.open(images / "thumbs" / "b.webp") as created:
        assert created.size == (640, 360)


# --- Video entries (phase 5) ---------------------------------------------------

LIBRARY_VIDEO = "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/2026/october/CRS35-Holland30s1080p.mp4"
VIDEO_PAGE = "https://science.nasa.gov/image-article/apod-2026-october-16-chasing-the-international-space-station/"


def _video_record(url: str = LIBRARY_VIDEO, page_url: str | None = VIDEO_PAGE) -> APODRecord:
    return APODRecord(
        date="2026-10-16",
        title="Chasing the International Space Station",
        media_type="video",
        url=url,
        hdurl=None,
        explanation="A timelapse of a Falcon 9 launch chasing the International Space Station at dawn.",
        copyright="Eric Holland",
        apod_url="https://apod.nasa.gov/apod/ap20261016.html",
        page_url=page_url,
    )


def _png_frame(video_url):
    import io
    assert video_url == LIBRARY_VIDEO
    buffer = io.BytesIO()
    Image.new("RGB", (1620, 1080), "midnightblue").save(buffer, format="PNG")
    return buffer.getvalue()


def test_generate_publishes_a_video_as_a_frame_linking_to_nasa(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _video_record())
    monkeypatch.setattr(cli, "poster_frame", _png_frame)

    assert cli.generate("2026-10-16") == cli.EXIT_SUCCESS
    entry = repo.root / "_apod" / "2026-10-16-chasing-the-international-space-station.md"
    text = entry.read_text(encoding="utf-8")
    assert "media_type: video" in text and f'video_url: "{VIDEO_PAGE}"' in text
    assert "rights_status: allowed" in text and 'credit: "Eric Holland"' in text
    with Image.open(repo.root / "assets" / "img" / "apod" / f"{entry.stem}.webp") as image:
        assert image.size == (1600, 1067)
    assert (repo.root / "assets" / "img" / "apod" / "thumbs" / f"{entry.stem}.webp").exists()
    capsys.readouterr()
    assert cli.check(str(entry)) == cli.EXIT_SUCCESS


def test_video_without_page_url_links_to_the_dated_apod_page(monkeypatch, repo):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _video_record(page_url=None))
    monkeypatch.setattr(cli, "poster_frame", _png_frame)

    assert cli.generate("2026-10-16") == cli.EXIT_SUCCESS
    text = next((repo.root / "_apod").glob("*.md")).read_text(encoding="utf-8")
    assert 'video_url: "https://science.nasa.gov/apod/?date=261016"' in text


def test_embedded_video_is_still_skipped(monkeypatch, repo, capsys):
    monkeypatch.setattr(cli, "fetch_apod", lambda target: _video_record(url="https://www.youtube.com/embed/abc"))

    assert cli.generate("2026-10-16") == cli.EXIT_SUCCESS
    assert "Skipped: The video is not a file from the APOD media library" in capsys.readouterr().out
    assert not (repo.root / "_apod").exists()


def test_parse_rejects_video_entry_without_nasa_link():
    content = _valid_generated_content().replace("generated_by:", "media_type: video\ngenerated_by:")
    with pytest.raises(ValueError, match="video_url"):
        cli._parse_and_validate_post(content)
    content = _valid_generated_content().replace("generated_by:", 'video_url: "https://science.nasa.gov/x/"\ngenerated_by:')
    with pytest.raises(ValueError, match="video_url on an image entry"):
        cli._parse_and_validate_post(content)
