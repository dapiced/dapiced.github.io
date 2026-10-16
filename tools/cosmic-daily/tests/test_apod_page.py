from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

import cosmic_daily.apod_page as apod_page
from cosmic_daily.apod_page import ApodUnavailableError, parse_apod_page
from cosmic_daily.nasa_client import fetch_apod


FIXTURE = Path(__file__).parent / "fixtures" / "apod_page_2026-10-10.html"
DAY = date(2026, 10, 10)
ORIGINAL = "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/2026/october/farside_lro1600.jpg"
RESIZED = (
    "https://assets.science.nasa.gov/dynamicimage/assets/science/cds/apod/apod/2026/october/"
    "farside_lro1600.jpg?w=1600&h=1600&fit=clip&crop=faces%2Cfocalpoint"
)
# What api.nasa.gov answers since APOD moved to science.nasa.gov.
DEGRADED_PAYLOAD = {
    "date": "2026-10-10",
    "title": "NASA Science",
    "media_type": "image",
    "url": "https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/nasa-logo@2x.png",
    "hdurl": "https://science.nasa.gov/wp-content/themes/nasa-child/assets/images/nasa-logo@2x.png",
    "explanation": "Tidally locked in synchronous rotation.Tomorrow's picture: Sunday's Childe",
    "service_version": "v1",
}


def _html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, *, payload=None, text="", url="", status_code=200):
        self.payload = payload
        self.text = text
        self.url = url
        self.status_code = status_code
        self.headers = {}

    def json(self):
        return self.payload


def test_parse_reads_title_credit_explanation_and_image():
    page = parse_apod_page(_html(), DAY)

    assert page.date == "2026-10-10"
    assert page.title == "Lunar Farside"
    assert page.credit == "NASA / GSFC / Arizona State Univ. / Lunar Reconnaissance Orbiter"
    assert page.explanation.startswith("Tidally locked in synchronous rotation, the Moon")
    assert page.explanation.endswith("form dark, smooth maria.")
    assert "Tomorrow" not in page.explanation
    assert "Explanation:" not in page.explanation
    # Original file first, resized hero second; the site logo is never a candidate.
    assert page.image_urls == (ORIGINAL, RESIZED)


@pytest.mark.parametrize("label", ["Credit &amp; Copyright", "Credit &amp; License"])
def test_parse_accepts_credit_label_variants(label):
    page = parse_apod_page(_html().replace(">Credit:<", f">{label}<"), DAY)
    assert page.credit.startswith("NASA / GSFC")


@pytest.mark.parametrize(
    "mutate, reason",
    [
        (lambda html: html.replace("October 10, 2026", "October 9, 2026"), "not 2026-10-10"),
        (lambda html: html.replace("October 10, 2026", "soon"), "no readable date"),
        (lambda html: html.replace(">Lunar Farside</h1>", "></h1>"), "no title"),
        (lambda html: html.replace("hds-media-inner", "hds-other"), "no still image"),
        (lambda html: html.replace("/science/cds/apod/", "/science/other/"), "no still image"),
        (lambda html: html.replace(">Credit:<", ">Source:<"), "no credit"),
    ],
)
def test_parse_fails_closed(mutate, reason):
    with pytest.raises(ApodUnavailableError, match=reason):
        parse_apod_page(mutate(_html()), DAY)


def test_fetch_apod_page_rejects_unexpected_host(monkeypatch):
    monkeypatch.setattr("requests.get",
        lambda *args, **kwargs: FakeResponse(text=_html(), url="https://example.com/apod/"),
    )
    with pytest.raises(ApodUnavailableError, match="example.com"):
        apod_page.fetch_apod_page(DAY)


def test_fetch_apod_falls_back_to_page_when_api_is_degraded(monkeypatch):
    calls = []

    def fake_get(url, *args, **kwargs):
        calls.append((url, kwargs.get("params")))
        if url.startswith("https://api.nasa.gov/"):
            return FakeResponse(payload=DEGRADED_PAYLOAD)
        return FakeResponse(
            text=_html(),
            url="https://science.nasa.gov/image-article/apod-2026-october-10-lunar-farside/",
        )

    monkeypatch.setattr("requests.get", fake_get)
    record = fetch_apod("2026-10-10", api_key="DEMO_KEY")

    assert calls[1] == ("https://science.nasa.gov/apod/", {"date": "261010"})
    assert record.title == "Lunar Farside"
    assert record.media_type == "image"
    assert record.hdurl == ORIGINAL
    assert record.url == RESIZED
    assert record.copyright.startswith("NASA / GSFC")
    assert "Tomorrow" not in record.explanation
    assert record.apod_url == "https://apod.nasa.gov/apod/ap20261010.html"


def test_fetch_apod_raises_unavailable_when_page_cannot_be_read(monkeypatch):
    def fake_get(url, *args, **kwargs):
        if url.startswith("https://api.nasa.gov/"):
            return FakeResponse(payload=DEGRADED_PAYLOAD)
        return FakeResponse(text="<html></html>", url="https://science.nasa.gov/apod/", status_code=200)

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(ApodUnavailableError):
        fetch_apod("2026-10-10", api_key="DEMO_KEY")


def test_fetch_apod_keeps_healthy_api_payload_without_reading_the_page(monkeypatch):
    payload = dict(
        DEGRADED_PAYLOAD,
        title="Lunar Farside",
        url="https://apod.nasa.gov/apod/image/2610/farside.jpg",
        hdurl=None,
        explanation="A healthy explanation.",
    )
    calls = []

    def fake_get(url, *args, **kwargs):
        calls.append(url)
        return FakeResponse(payload=payload)

    monkeypatch.setattr("requests.get", fake_get)
    record = fetch_apod("2026-10-10", api_key="DEMO_KEY")

    assert calls == ["https://api.nasa.gov/planetary/apod"]
    assert record.title == "Lunar Farside"


ROLLOVER = Path(__file__).parent / "fixtures" / "apod_page_2026-10-13_rollover.html"
VIDEO = Path(__file__).parent / "fixtures" / "apod_page_2026-10-16_video.html"


def test_rollover_page_uses_the_original_not_the_annotated_image():
    # 13 October 2026: an "original / annotated" rollover instead of a <figure>.
    page = parse_apod_page(ROLLOVER.read_text(encoding="utf-8"), date(2026, 10, 13))
    assert page.media_type == "image" and page.title == "Desert Stairway to Heaven"
    assert page.credit == "Julien Looten"
    assert page.image_urls[0] == (
        "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/2026/october/Stairway2Heaven_Looten_6750.jpg"
    )
    assert not any("annotated" in url for url in page.image_urls)


def test_video_page_yields_the_library_video_and_its_credit():
    url = "https://science.nasa.gov/image-article/apod-2026-october-16-chasing-the-international-space-station/"
    page = parse_apod_page(VIDEO.read_text(encoding="utf-8"), date(2026, 10, 16), page_url=url)
    assert page.media_type == "video" and page.image_urls == ()
    assert page.video_url == (
        "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/2026/october/CRS35-Holland30s1080p.mp4"
    )
    assert page.credit == "Eric Holland"  # from "Video Credit:"
    assert page.page_url == url
    assert page.explanation.startswith("Blasting into the predawn sky")


def test_library_video_check():
    assert apod_page.is_library_video(
        "https://assets.science.nasa.gov/content/dam/science/cds/apod/apod/2026/october/x.mp4")
    assert not apod_page.is_library_video("https://www.youtube.com/embed/abc")
    assert not apod_page.is_library_video("https://assets.science.nasa.gov/content/dam/other/x.mp4")



def test_page_errors_fail_loudly_instead_of_skipping(monkeypatch):
    # A skip (ApodUnavailableError) ends the run green and loses the day; a
    # transport failure must fail the run so that an issue is opened.
    from cosmic_daily import http

    monkeypatch.setattr("requests.get", lambda *a, **k: FakeResponse(url="https://science.nasa.gov/apod/", status_code=503))
    with pytest.raises(http.TransientError):
        apod_page.fetch_apod_page(DAY)
    monkeypatch.setattr("requests.get", lambda *a, **k: FakeResponse(url="https://science.nasa.gov/apod/", status_code=403))
    with pytest.raises(RuntimeError, match="HTTP 403") as caught:
        apod_page.fetch_apod_page(DAY)
    assert not isinstance(caught.value, ApodUnavailableError)
