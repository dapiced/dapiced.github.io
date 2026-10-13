"""Build assets/data/sky-catalog.json, the data behind the "Montréal tonight"
sky map (assets/js/sky-map.js).

Source: d3-celestial by Olaf Frohn (BSD-3-Clause), a pinned release fetched
from jsDelivr and checked against known SHA-256 digests, so a rebuild either
reproduces the committed file or fails loudly. Only naked-eye stars
(magnitude 5.0 or brighter) and the constellation stick figures are kept,
rounded to what a 600 px chart can show: about 55 KB instead of 680 KB.

Usage (from the repository root):
    python tools/sky-map/build_catalog.py
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "data" / "sky-catalog.json"
LICENSE_OUT = ROOT / "assets" / "data" / "LICENSE-d3-celestial.txt"

VERSION = "0.7.35"
BASE = f"https://cdn.jsdelivr.net/npm/d3-celestial@{VERSION}"
SOURCES = {
    "data/stars.6.json": "0297b8fa3adfbce1dc26566f61c4abcc1df4f29c6a28729ca06b56d1c6d25602",
    "data/constellations.lines.json": "294f66bef5d5cf50b1e17f16d2efa1d97a15131612c68dd935adef6e7373e13c",
    "LICENSE": "95e8d6c281db702112e3f990c9c2958a4b412e2cfc09d419ec33f1227aa8dce4",
}
MAX_MAGNITUDE = 5.0
VINCENZO_HIP = 3881  # ν Andromedae


def fetch(name: str) -> bytes:
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=60) as response:
        body = response.read()
    digest = hashlib.sha256(body).hexdigest()
    if digest != SOURCES[name]:
        raise SystemExit(f"{name}: unexpected SHA-256 {digest}")
    return body


def build(stars_raw: bytes, lines_raw: bytes) -> dict:
    stars = []
    vincenzo = None
    for feature in json.loads(stars_raw)["features"]:
        mag = feature["properties"]["mag"]
        if mag > MAX_MAGNITUDE:
            continue
        ra, dec = feature["geometry"]["coordinates"]
        bv = float(feature["properties"].get("bv") or 0)
        if feature["id"] == VINCENZO_HIP:
            vincenzo = len(stars)
        # [right ascension (degrees, 0-360), declination, magnitude, colour index B-V]
        stars.append([round(ra % 360, 2), round(dec, 2), round(mag, 2), round(bv, 2)])
    if vincenzo is None:
        raise SystemExit("ν Andromedae (HIP 3881) is missing from the catalogue")

    lines = {}
    for feature in json.loads(lines_raw)["features"]:
        lines[feature["id"]] = [
            [[round(ra % 360, 2), round(dec, 2)] for ra, dec in segment]
            for segment in feature["geometry"]["coordinates"]
        ]
    return {
        "source": f"d3-celestial {VERSION} by Olaf Frohn, BSD-3-Clause (see LICENSE-d3-celestial.txt)",
        "max_magnitude": MAX_MAGNITUDE,
        "vincenzo": vincenzo,
        "stars": stars,
        "lines": lines,
    }


def main() -> int:
    catalog = build(fetch("data/stars.6.json"), fetch("data/constellations.lines.json"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, separators=(",", ":")) + "\n", encoding="utf-8")
    LICENSE_OUT.write_bytes(fetch("LICENSE"))
    print(f"{OUT.relative_to(ROOT)}: {len(catalog['stars'])} stars, "
          f"{len(catalog['lines'])} constellations, {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
