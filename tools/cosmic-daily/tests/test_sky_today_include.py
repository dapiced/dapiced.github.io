from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

INCLUDE = Path(__file__).resolve().parents[3] / "_includes" / "sky-today.html"


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.nested = False
        self.anchors: list[dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            if self.depth:
                self.nested = True
            self.depth += 1
            self.anchors.append({"href": dict(attrs).get("href", ""), "text": ""})

    def handle_endtag(self, tag):
        if tag == "a":
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.anchors[-1]["text"] += data


def _parse() -> AnchorCollector:
    parser = AnchorCollector()
    parser.feed(INCLUDE.read_text(encoding="utf-8"))
    return parser


def test_sky_today_has_no_nested_links():
    assert not _parse().nested


def test_archive_cta_links_to_sky_index():
    anchors = _parse().anchors
    archive = [a for a in anchors if "Browse the sky archive" in a["text"]]
    assert len(archive) == 1
    assert archive[0]["href"] == "/sky/"


def test_latest_entry_link_is_separate_from_archive_cta():
    anchors = _parse().anchors
    entry = [a for a in anchors if a["href"] == "{{ sky_latest.url }}"]
    assert entry
    assert all("Browse the sky archive" not in a["text"] for a in entry)
