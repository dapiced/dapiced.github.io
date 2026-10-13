"""The About page exists in both languages, as a translation pair, and the
homepage leads to it (navigation, 60-second profile, reader paths)."""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "about" / "index.html"
FR = ROOT / "fr" / "a-propos" / "index.html"


def front_matter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


def test_about_pages_are_a_translation_pair():
    en, fr = front_matter(EN), front_matter(FR)
    assert en["lang"] == "en" and en["translation_url"] == "/fr/a-propos/"
    assert fr["lang"] == "fr" and fr["translation_url"] == "/about/"


def test_both_versions_keep_the_same_sections():
    # Same anchors order: path, values, learning, sky, vincenzo, contact.
    en, fr = EN.read_text(encoding="utf-8"), FR.read_text(encoding="utf-8")
    assert en.count("<h2 ") == fr.count("<h2 ") == 6
    assert en.count('class="beyond-card"') == fr.count('class="beyond-card"') == 4


def test_french_pillar_page_addresses_the_reader_with_vous():
    text = FR.read_text(encoding="utf-8")
    assert "Vous " in text
    for informal in (" tu ", " ton ", " ta ", " tes "):
        assert informal not in text, informal


def test_contact_is_linkedin_only():
    for page in (EN, FR):
        text = page.read_text(encoding="utf-8")
        assert "https://www.linkedin.com/in/dapiced/" in text
        assert "mailto:" not in text


def test_homepage_leads_to_about_and_profile():
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'href="/about/"' in home
    assert 'id="profile"' in home and 'href="#profile"' in home
    assert home.count('class="path-card"') == 4
    nav = yaml.safe_load((ROOT / "_data" / "navigation.yml").read_text(encoding="utf-8"))
    assert nav[0]["href"] == "/about/" and nav[0]["href_fr"] == "/fr/a-propos/"
