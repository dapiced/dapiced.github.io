"""Social share cards (Open Graph, 1200x630) for blog posts and portfolio entries.

LinkedIn, Bluesky and Slack crop whatever image a page declares into a 1.91:1
frame. A portrait photo or a screenshot loses its subject; a page with no image
falls back to the generic site card. This tool draws one branded card per entry
(series and date, title, the entry's own photo on the right when it has one)
and commits it under assets/img/og/. The Jekyll plugin _plugins/og_cards.rb then
points the page's og:image at it.

Only JPEG and WebP images become the photo panel: PNGs on this site are
screenshots and diagrams, unreadable once cropped to a narrow strip. The
front matter key `og_photo_focus` (0 = left edge, 1 = right edge, default 0.5)
picks which part of a wide photo stays in the panel.

Entries are skipped when their declared image is already a share card (about
1.91:1, at least 1200 px wide) or when their front matter says `og_card: false`.

Rendering only happens locally: `manifest.json` records a hash of every input
(text, photo bytes, generator version), so CI can prove the committed cards are
current without depending on the exact Pillow build.

Usage (from the repository root):
    python tools/og-cards/og_cards.py           # render missing or stale cards
    python tools/og-cards/og_cards.py --check   # exit 1 if any card is missing or stale
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

# Bump when the drawing changes: every card becomes stale and is re-rendered.
GENERATOR_VERSION = 2

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "assets" / "img" / "og"
MANIFEST = OUT_DIR / "manifest.json"
SOURCES = {"post": ROOT / "_posts", "portfolio": ROOT / "_portfolio"}

WIDTH, HEIGHT = 1200, 630
MARGIN = 72
PHOTO_WIDTH = 440
CARD_RATIO = WIDTH / HEIGHT

# Night theme tokens (assets/css/style.css). Gold is reserved for Vincenzo.
BG_TOP = (5, 7, 15)
BG_BOTTOM = (12, 18, 34)
TEXT = (219, 226, 238)
MUTED = (154, 167, 189)
SIGNAL = (108, 182, 255)
LINE = (31, 42, 68)
VINCENZO = (232, 184, 74)

FONTS = ROOT / "assets" / "fonts"
FONT_TITLE = FONTS / "archivo-expanded-latin.woff2"
FONT_SANS = FONTS / "ibm-plex-sans-latin-600.woff2"
FONT_MONO = FONTS / "ibm-plex-mono-latin-400.woff2"

SERIES = {
    ("post", "en"): "MISSION LOG",
    ("post", "fr"): "JOURNAL DE MISSION",
    ("portfolio", "en"): "PORTFOLIO",
    ("portfolio", "fr"): "PORTFOLIO",
}
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}


@dataclass(frozen=True)
class Entry:
    slug: str
    source: Path
    kind: str
    title: str
    date: str  # YYYY-MM-DD
    lang: str
    photo: Path | None
    focus: float
    accent: str | None

    @property
    def output(self) -> Path:
        return OUT_DIR / f"{self.slug}.jpg"

    def input_hash(self) -> str:
        payload = {
            "version": GENERATOR_VERSION,
            "kind": self.kind,
            "title": self.title,
            "date": self.date,
            "lang": self.lang,
            "accent": self.accent,
            "photo": self.photo.relative_to(ROOT).as_posix() if self.photo else None,
            "photo_sha256": hashlib.sha256(self.photo.read_bytes()).hexdigest() if self.photo else None,
            "focus": self.focus,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    return yaml.safe_load(block) or {}


def declared_image(data: dict) -> Path | None:
    image = data.get("image")
    if isinstance(image, dict):
        image = image.get("path")
    if not image or not isinstance(image, str) or not image.startswith("/"):
        return None
    path = ROOT / image.lstrip("/")
    return path if path.is_file() else None


def is_share_card(path: Path) -> bool:
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        return False
    with Image.open(path) as image:
        return image.width >= 1200 and abs(image.width / image.height - CARD_RATIO) < 0.05


def discover() -> list[Entry]:
    entries = []
    for kind, folder in SOURCES.items():
        for source in sorted(folder.glob("*.md")):
            data = front_matter(source)
            if data.get("og_card") is False or data.get("published") is False:
                continue
            image = declared_image(data)
            if image and is_share_card(image):
                continue
            photo = image if image and image.suffix.lower() in {".jpg", ".jpeg", ".webp"} else None
            # Posts are named YYYY-MM-DD-slug.md; Jekyll's URL drops the date.
            slug = source.stem[11:] if kind == "post" else source.stem
            entries.append(
                Entry(
                    slug=slug,
                    source=source,
                    kind=kind,
                    title=str(data.get("title", slug)).strip(),
                    date=str(data.get("date", source.stem[:10]))[:10],
                    lang=str(data.get("lang", "en"))[:2],
                    photo=photo,
                    focus=float(data.get("og_photo_focus", 0.5)),
                    accent=data.get("og_accent"),
                )
            )
    return entries


def format_date(iso: str, lang: str) -> str:
    year, month, day = (int(part) for part in iso.split("-"))
    name = MONTHS[lang][month - 1]
    return f"{day} {name} {year}" if lang == "fr" else f"{name} {day}, {year}"


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw: ImageDraw.ImageDraw, title: str, width: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest size that keeps the title within four lines; ellipsis as a last resort."""
    for size in range(64, 35, -2):
        font = ImageFont.truetype(str(FONT_TITLE), size)
        lines = wrap(draw, title, font, width)
        # A single long word can still overflow its line: shrink until it fits.
        if len(lines) <= 4 and all(draw.textlength(line, font=font) <= width for line in lines):
            return font, lines
    lines = lines[:4]
    while draw.textlength(lines[-1] + "…", font=font) > width and " " in lines[-1]:
        lines[-1] = lines[-1].rsplit(" ", 1)[0]
    lines[-1] += "…"
    return font, lines


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, colour: tuple) -> None:
    """Four-pointed star, drawn as a polygon so it never depends on a font glyph."""
    inner = radius * 0.28
    points = []
    for i in range(8):
        r = radius if i % 2 == 0 else inner
        dx, dy = [(0, -1), (0.7, -0.7), (1, 0), (0.7, 0.7), (0, 1), (-0.7, 0.7), (-1, 0), (-0.7, -0.7)][i]
        points.append((cx + dx * r, cy + dy * r))
    draw.polygon(points, fill=colour)


def background(slug: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        draw.line([(0, y), (WIDTH, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))
    # Same slug, same sky: the starfield is seeded so a re-render is identical.
    rng = random.Random(slug)
    for _ in range(160):
        x, y = rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT)
        level = rng.uniform(0.15, 0.6)
        radius = rng.choice([0.6, 0.8, 1.0, 1.4])
        colour = tuple(round(c * level + b * (1 - level)) for c, b in zip(TEXT, BG_BOTTOM))
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=colour)
    return image


def paste_photo(card: Image.Image, photo: Path, focus: float) -> None:
    """Cover-crop the photo into the right panel and fade its left edge into the sky."""
    with Image.open(photo) as source:
        source = source.convert("RGB")
        scale = max(PHOTO_WIDTH / source.width, HEIGHT / source.height)
        resized = source.resize((round(source.width * scale), round(source.height * scale)), Image.LANCZOS)
    left = round((resized.width - PHOTO_WIDTH) * min(max(focus, 0.0), 1.0))
    top = (resized.height - HEIGHT) // 2
    panel = resized.crop((left, top, left + PHOTO_WIDTH, top + HEIGHT))
    mask = Image.new("L", (PHOTO_WIDTH, HEIGHT), 255)
    fade = 160
    mask_draw = ImageDraw.Draw(mask)
    for x in range(fade):
        mask_draw.line([(x, 0), (x, HEIGHT)], fill=round(255 * (x / fade) ** 1.5))
    card.paste(panel, (WIDTH - PHOTO_WIDTH, 0), mask)


def render(entry: Entry) -> Image.Image:
    card = background(entry.slug)
    if entry.photo:
        paste_photo(card, entry.photo, entry.focus)
    draw = ImageDraw.Draw(card)
    text_width = WIDTH - 2 * MARGIN - (PHOTO_WIDTH - 40 if entry.photo else 0)

    mono = ImageFont.truetype(str(FONT_MONO), 24)
    sans = ImageFont.truetype(str(FONT_SANS), 28)
    accent = VINCENZO if entry.accent == "vincenzo" else SIGNAL

    eyebrow = f"{SERIES[(entry.kind, entry.lang)]}  ·  {format_date(entry.date, entry.lang).upper()}"
    draw.text((MARGIN, MARGIN), eyebrow, font=mono, fill=accent)
    draw.line([(MARGIN, MARGIN + 46), (MARGIN + 64, MARGIN + 46)], fill=accent, width=3)

    font, lines = fit_title(draw, entry.title, text_width)
    line_height = round(font.size * 1.22)
    block = line_height * len(lines)
    top = MARGIN + 80 + max(0, (HEIGHT - 2 * MARGIN - 80 - 60 - block) // 2)
    for i, line in enumerate(lines):
        draw.text((MARGIN, top + i * line_height), line, font=font, fill=TEXT)

    footer_y = HEIGHT - MARGIN - 28
    draw.line([(MARGIN, footer_y - 24), (MARGIN + text_width, footer_y - 24)], fill=LINE, width=1)
    star(draw, MARGIN + 10, footer_y + 15, 10, accent)
    draw.text((MARGIN + 32, footer_y), "Dominic D'Apice", font=sans, fill=TEXT)
    name_end = MARGIN + 32 + draw.textlength("Dominic D'Apice", font=sans)
    draw.text((name_end + 20, footer_y + 4), "dominicdapice.com", font=mono, fill=MUTED)
    return card


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}


def stale(entries: list[Entry], manifest: dict) -> list[Entry]:
    return [
        e for e in entries
        if not e.output.is_file() or manifest.get(e.slug, {}).get("inputs") != e.input_hash()
    ]


def orphans(entries: list[Entry]) -> list[Path]:
    wanted = {e.output.name for e in entries}
    return [p for p in sorted(OUT_DIR.glob("*.jpg")) if p.name not in wanted]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="fail if a card is missing, stale or orphaned")
    args = parser.parse_args(argv)

    entries = discover()
    manifest = load_manifest()
    todo = stale(entries, manifest)
    extra = orphans(entries)

    if args.check:
        for e in todo:
            print(f"stale or missing: {e.output.relative_to(ROOT)} ({e.source.relative_to(ROOT)})")
        for p in extra:
            print(f"orphan card: {p.relative_to(ROOT)}")
        if todo or extra:
            print("Run: python tools/og-cards/og_cards.py")
            return 1
        print(f"{len(entries)} share cards are current.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for e in todo:
        render(e).save(e.output, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"rendered {e.output.relative_to(ROOT)}")
    for p in extra:
        p.unlink()
        print(f"removed {p.relative_to(ROOT)}")
    manifest = {
        e.slug: {"source": e.source.relative_to(ROOT).as_posix(), "inputs": e.input_hash()}
        for e in entries
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
