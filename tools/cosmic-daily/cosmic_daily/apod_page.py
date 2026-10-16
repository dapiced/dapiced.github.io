"""Fallback reader for the APOD entry page on science.nasa.gov.

APOD moved from apod.nasa.gov to science.nasa.gov in autumn 2026. Since then the
api.nasa.gov endpoint keeps answering 200 but scrapes the old (redirected) page:
the title comes back as "NASA Science" and the image as the NASA logo, while the
explanation still carries the "Tomorrow's picture" footer. This module reads the
same entry from its new page instead.

The hero media comes in three shapes: a photo (<figure class="hds-media-inner">),
an "original / annotated" image rollover (only the original is used), or a video
file from the APOD media library (an MP4 played by NASA's own player). A video
entry is published with a frame of the video as its picture, linking to the
NASA page (cosmic_daily/video_frame.py).

The parser fails closed: when the title, the media or the credit cannot be found,
or the page is for another date, it raises ApodUnavailableError and the CLI skips
the day instead of publishing something wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests


APOD_PAGE_ENDPOINT = "https://science.nasa.gov/apod/"
PAGE_HOST = "science.nasa.gov"
IMAGE_HOST = "assets.science.nasa.gov"
# The APOD media library lives under this path, served either as the original
# file (content/dam/...) or through the resizing service (dynamicimage/assets/...).
ORIGINAL_IMAGE_PREFIX = "/content/dam/science/cds/apod/"
RESIZED_IMAGE_PREFIX = "/dynamicimage/assets/science/cds/apod/"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff")
VIDEO_EXTENSIONS = (".mp4", ".m4v", ".webm", ".mov")
# The annotated half of an image rollover: same picture with labels drawn on it.
ROLLOVER_SECONDARY = "smd-image-rollover__image--secondary"
REQUEST_TIMEOUT = (10, 45)
TOMORROW_MARKER = re.compile(r"tomorrow'?s picture\s*:", re.IGNORECASE)


class ApodUnavailableError(Exception):
    """The APOD entry cannot be read reliably; the day is skipped, not failed."""


@dataclass(frozen=True)
class ApodPage:
    date: str
    title: str
    explanation: str
    credit: str
    image_urls: tuple[str, ...]
    media_type: str = "image"
    video_url: str | None = None
    page_url: str | None = None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class _ApodPageParser(HTMLParser):
    """Collects the hero image, the <h1> title, the explanation and the meta table."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] | None = None
        self.title: str | None = None
        # Hero media: the first <div class="media-detail-hero__media">, or on
        # older pages the first <figure class="hds-media-inner ...">.
        self._hero_tag: str | None = None
        self._hero_depth = 0
        self._hero_done = False
        self.hero_links: list[str] = []
        self.hero_videos: list[str] = []
        # Explanation paragraph, stopped at the "Tomorrow's picture" footer.
        self._in_description = False
        self._description_stopped = False
        self._strong_parts: list[str] | None = None
        self.description_parts: list[str] = []
        # Meta table rows: <th scope="row">Label</th><td>Value</td>.
        self._cell: str | None = None
        self._cell_parts: list[str] = []
        self._row_label: str | None = None
        self.meta: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        classes = attributes.get("class", "").split()

        if self._hero_depth and tag == self._hero_tag:
            self._hero_depth += 1
        elif not self._hero_done and not self._hero_depth and (
            (tag == "div" and "media-detail-hero__media" in classes)
            or (tag == "figure" and "hds-media-inner" in classes)
        ):
            self._hero_tag, self._hero_depth = tag, 1
        if self._hero_depth:
            if tag == "a" and attributes.get("href"):
                self.hero_links.append(attributes["href"])
            elif tag == "img" and attributes.get("src") and ROLLOVER_SECONDARY not in classes:
                self.hero_links.append(attributes["src"])
            elif tag in ("video", "source") and attributes.get("src"):
                self.hero_videos.append(attributes["src"])

        if tag == "h1" and self.title is None:
            self.title_parts = []
        if tag == "p" and "media-detail-hero__description" in classes:
            self._in_description = True
        if self._in_description and tag == "strong":
            self._strong_parts = []
        if self._in_description and tag == "br":
            self.description_parts.append(" ")

        if tag == "th" and attributes.get("scope") == "row":
            self._cell, self._cell_parts = "th", []
        elif tag == "td" and self._row_label is not None:
            self._cell, self._cell_parts = "td", []

    def handle_endtag(self, tag: str) -> None:
        if self._hero_depth and tag == self._hero_tag:
            self._hero_depth -= 1
            if not self._hero_depth:
                self._hero_done = True
        if tag == "h1" and self.title_parts is not None:
            self.title = _clean("".join(self.title_parts))
            self.title_parts = None
        if tag == "strong" and self._strong_parts is not None:
            strong_text = _clean("".join(self._strong_parts))
            self._strong_parts = None
            if TOMORROW_MARKER.match(strong_text):
                self._description_stopped = True
            elif strong_text.lower() != "explanation:" and not self._description_stopped:
                self.description_parts.append(strong_text)
        if tag == "p" and self._in_description:
            self._in_description = False
            self._description_stopped = True
        if tag == "th" and self._cell == "th":
            self._row_label = _clean("".join(self._cell_parts))
            self._cell = None
        elif tag == "td" and self._cell == "td":
            self.meta.append((self._row_label or "", _clean("".join(self._cell_parts))))
            self._row_label, self._cell = None, None

    def handle_data(self, data: str) -> None:
        if self.title_parts is not None:
            self.title_parts.append(data)
        if self._cell:
            self._cell_parts.append(data)
        if self._in_description and not self._description_stopped:
            if self._strong_parts is not None:
                self._strong_parts.append(data)
            else:
                self.description_parts.append(data)


def _image_candidates(links: list[str]) -> tuple[str, ...]:
    """Original file first, then the resized hero, both restricted to the APOD library."""
    candidates: list[str] = []
    for link in links:
        parsed = urlparse(link)
        if parsed.scheme != "https" or parsed.netloc != IMAGE_HOST:
            continue
        if not parsed.path.lower().endswith(IMAGE_EXTENSIONS):
            continue
        if parsed.path.startswith(RESIZED_IMAGE_PREFIX):
            original = f"https://{IMAGE_HOST}{ORIGINAL_IMAGE_PREFIX}{parsed.path[len(RESIZED_IMAGE_PREFIX):]}"
            for url in (original, link):
                if url not in candidates:
                    candidates.append(url)
        elif parsed.path.startswith(ORIGINAL_IMAGE_PREFIX) and link not in candidates:
            candidates.append(link)
    return tuple(candidates)


def is_library_video(url: str) -> bool:
    """A video file served from the APOD media library on assets.science.nasa.gov."""
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == IMAGE_HOST
        and parsed.path.startswith(ORIGINAL_IMAGE_PREFIX)
        and parsed.path.lower().endswith(VIDEO_EXTENSIONS)
    )


def _video_candidates(links: list[str]) -> tuple[str, ...]:
    candidates: list[str] = []
    for link in links:
        if is_library_video(link) and link not in candidates:
            candidates.append(link)
    return tuple(candidates)


def _meta_value(meta: list[tuple[str, str]], label_prefix: str) -> str | None:
    for label, value in meta:
        if label.lower().startswith(label_prefix):
            return value
    return None


def _credit_value(meta: list[tuple[str, str]]) -> str | None:
    # "Credit:", "Credit & Copyright", "Image Credit:", "Video Credit:"...
    for label, value in meta:
        if "credit" in label.lower():
            return value
    return None


def parse_apod_page(html: str, expected_day: date, page_url: str | None = None) -> ApodPage:
    parser = _ApodPageParser()
    parser.feed(html)
    parser.close()

    page_date_text = _meta_value(parser.meta, "date")
    try:
        page_day = datetime.strptime(page_date_text or "", "%B %d, %Y").date()
    except ValueError as exc:
        raise ApodUnavailableError(f"APOD page has no readable date ({page_date_text!r})") from exc
    if page_day != expected_day:
        raise ApodUnavailableError(
            f"APOD page is for {page_day.isoformat()}, not {expected_day.isoformat()}"
        )

    title = parser.title or ""
    if not title:
        raise ApodUnavailableError("APOD page has no title")

    image_urls = _image_candidates(parser.hero_links)
    video_urls = () if image_urls else _video_candidates(parser.hero_videos)
    if not image_urls and not video_urls:
        # An embedded third-party player, or a layout this parser does not recognize.
        raise ApodUnavailableError("APOD page has no still image or video from the APOD media library")

    credit = _credit_value(parser.meta)
    if not credit:
        raise ApodUnavailableError("APOD page has no credit line")

    explanation = _clean("".join(parser.description_parts))
    explanation = TOMORROW_MARKER.split(explanation, maxsplit=1)[0].strip()
    if not explanation:
        raise ApodUnavailableError("APOD page has no explanation")

    return ApodPage(
        date=expected_day.isoformat(),
        title=title,
        explanation=explanation,
        credit=credit,
        image_urls=image_urls,
        media_type="image" if image_urls else "video",
        video_url=video_urls[0] if video_urls else None,
        page_url=page_url,
    )


def fetch_apod_page(day: date) -> ApodPage:
    try:
        response = requests.get(
            APOD_PAGE_ENDPOINT,
            params={"date": f"{day:%y%m%d}"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ApodUnavailableError(f"APOD page could not be fetched: {exc}") from exc
    final_url = urlparse(response.url or "")
    if response.status_code != 200 or final_url.scheme != "https" or final_url.netloc != PAGE_HOST:
        raise ApodUnavailableError(
            f"APOD page returned HTTP {response.status_code} from {response.url}"
        )
    return parse_apod_page(response.text, day, page_url=response.url)
