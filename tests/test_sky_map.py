"""The "Montréal tonight" sky map: a small committed catalogue (built by
tools/sky-map/build_catalog.py), its licence, and both sky pages using it."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "data" / "sky-catalog.json"


def test_catalog_is_small_and_naked_eye_only():
    assert CATALOG.stat().st_size < 70_000
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert 1500 < len(data["stars"]) < 1800
    assert all(star[2] <= data["max_magnitude"] for star in data["stars"])
    assert len(data["lines"]) >= 88


def test_vincenzo_points_at_nu_andromedae():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    ra, dec, mag, _ = data["stars"][data["vincenzo"]]
    assert abs(ra - 12.45) < 0.05 and abs(dec - 41.08) < 0.05 and mag == 4.53


def test_source_licence_is_shipped():
    licence = (ROOT / "assets" / "data" / "LICENSE-d3-celestial.txt").read_text(encoding="utf-8")
    assert "Olaf Frohn" in licence
    assert "BSD-3-Clause" in json.loads(CATALOG.read_text(encoding="utf-8"))["source"]


def test_both_sky_pages_show_the_map():
    for page in ("sky/index.html", "fr/ciel/index.html"):
        assert "{% include sky-map.html %}" in (ROOT / page).read_text(encoding="utf-8"), page
