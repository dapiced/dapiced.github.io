"""Share cards (tools/og-cards): every post and portfolio entry that needs one
has a current card, and the cards stay light enough for LinkedIn previews."""
import importlib.util
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "assets" / "img" / "og"

spec = importlib.util.spec_from_file_location("og_cards", ROOT / "tools" / "og-cards" / "og_cards.py")
og_cards = importlib.util.module_from_spec(spec)
sys.modules["og_cards"] = og_cards  # dataclasses resolve types through sys.modules
spec.loader.exec_module(og_cards)


def test_cards_are_current():
    # Same check as `python tools/og-cards/og_cards.py --check`, with a readable failure.
    entries = og_cards.discover()
    stale = og_cards.stale(entries, og_cards.load_manifest())
    orphans = og_cards.orphans(entries)
    assert not stale and not orphans, (
        "Share cards out of date (run `python tools/og-cards/og_cards.py`): "
        + ", ".join([e.slug for e in stale] + [p.name for p in orphans])
    )


def test_cards_are_1200_by_630_and_light():
    cards = sorted(CARDS.glob("*.jpg"))
    assert cards, "no share cards generated"
    for card in cards:
        with Image.open(card) as image:
            assert image.size == (1200, 630), card.name
        assert card.stat().st_size < 200_000, f"{card.name} is over 200 KB"


def test_existing_share_cards_are_kept():
    # Hand-made 1200x630 cards (Prophet, Long Dash, Tree) are not replaced.
    slugs = {e.slug for e in og_cards.discover()}
    assert "what-i-learned-about-facebook-prophet" not in slugs
    assert "the-long-dash-was-a-deprecation-notice" not in slugs


def test_gold_accent_is_only_for_vincenzo():
    accented = [e.slug for e in og_cards.discover() if e.accent]
    assert accented == ["a-star-for-my-father"]


def test_render_fits_long_titles(tmp_path):
    entry = og_cards.Entry(
        slug="test",
        source=ROOT / "_posts" / "x.md",
        kind="post",
        title="Un titre très long " * 8,
        date="2026-10-13",
        lang="fr",
        photo=None,
        focus=0.5,
        accent=None,
    )
    image = og_cards.render(entry)
    assert image.size == (1200, 630)


def test_plugin_points_seo_at_the_card():
    plugin = (ROOT / "_plugins" / "og_cards.rb").read_text(encoding="utf-8")
    assert "assets/img/og" in plugin and '"width" => 1200' in plugin
