"""The French section (/fr/): each pillar page has its English counterpart and
the other way around, the navigation leads to them, and the homepage and
resume are one template per page type rather than two copies."""
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]

PAIRS = [
    ("index.html", "fr/index.html"),
    ("about/index.html", "fr/a-propos/index.html"),
    ("resume/index.html", "fr/cv/index.html"),
    ("portfolio/index.html", "fr/realisations/index.html"),
    ("blog/index.html", "fr/blogue/index.html"),
    ("sky/index.html", "fr/ciel/index.html"),
]


def front_matter(relative: str) -> dict:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8").split("---", 2)[1])


def url_of(relative: str) -> str:
    folder = Path(relative).parent.as_posix()
    return "/" if folder == "." else f"/{folder}/"


@pytest.mark.parametrize("english, french", PAIRS)
def test_pillar_pages_are_reciprocal_translations(english, french):
    en, fr = front_matter(english), front_matter(french)
    assert en["lang"] == "en" and fr["lang"] == "fr"
    assert en["translation_url"] == url_of(french)
    assert fr["translation_url"] == url_of(english)


def test_french_navigation_targets_exist():
    for item in yaml.safe_load((ROOT / "_data" / "navigation.yml").read_text(encoding="utf-8")):
        if "href_fr" in item:
            assert (ROOT / item["href_fr"].strip("/") / "index.html").is_file(), item["href_fr"]


def test_homepage_and_resume_share_one_template_each():
    assert "{% include home.html %}" in (ROOT / "index.html").read_text(encoding="utf-8")
    assert "{% include home.html %}" in (ROOT / "fr" / "index.html").read_text(encoding="utf-8")
    assert "{% include resume.html %}" in (ROOT / "resume" / "index.html").read_text(encoding="utf-8")
    assert "{% include resume.html %}" in (ROOT / "fr" / "cv" / "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["home", "resume"])
def test_page_strings_exist_in_both_languages(name):
    strings = yaml.safe_load((ROOT / "_data" / f"{name}.yml").read_text(encoding="utf-8"))
    assert set(strings["en"]) == set(strings["fr"])


def test_every_timeline_and_skill_entry_is_translated():
    for item in yaml.safe_load((ROOT / "_data" / "timeline.yml").read_text(encoding="utf-8")):
        assert item.get("role_fr") and item.get("description_fr"), item["role"]
    for group in yaml.safe_load((ROOT / "_data" / "skills.yml").read_text(encoding="utf-8")):
        assert group.get("domain_fr"), group["domain"]


def test_language_switch_is_always_rendered():
    layout = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
    assert 'class="lang-switch lang-switch-home"' in layout
