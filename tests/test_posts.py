"""Blog posts (_posts/) and the generator that creates them (tools/new-post):
translations point at each other, no post hides in the future, no placeholder
goes live."""
import argparse
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"

spec = importlib.util.spec_from_file_location("new_post", ROOT / "tools" / "new-post" / "new_post.py")
new_post = importlib.util.module_from_spec(spec)
sys.modules["new_post"] = new_post
spec.loader.exec_module(new_post)


def parse(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1]) or {}


def when(value) -> datetime:
    # "2026-09-26 20:00:00 -0400" is a string for YAML (space before the offset).
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S %z")


def url_of(path: Path) -> str:
    # _config.yml: permalink: /blog/:year/:month/:title/
    year, month, _day, slug = path.stem.split("-", 3)
    return f"/blog/{year}/{month}/{slug}/"


ALL = {url_of(p): (p, parse(p)) for p in sorted(POSTS.glob("*.md"))}
PUBLISHED = [(p, data) for p, data in ALL.values() if data.get("published") is not False]


@pytest.mark.parametrize("path, data", [(p, d) for p, d in ALL.values() if d.get("translation_url")],
                         ids=lambda v: v.name if isinstance(v, Path) else "")
def test_translations_point_at_each_other(path, data):
    target = ALL.get(data["translation_url"])
    assert target, f"{path.name}: translation_url {data['translation_url']} matches no post"
    other_path, other = target
    assert other.get("translation_url") == url_of(path), f"{other_path.name} does not link back to {path.name}"
    assert {data.get("lang", "en"), other.get("lang", "en")} == {"en", "fr"}
    assert data.get("translation_label"), f"{path.name} has no translation_label"


def test_no_published_post_is_dated_in_the_future():
    # Jekyll skips future posts without a word (the Prophet posts, September 2026).
    now = datetime.now(timezone.utc)
    future = [p.name for p, data in PUBLISHED if when(data["date"]) > now]
    assert not future, f"dated in the future, Jekyll would not publish: {future}"


def test_no_placeholder_is_published():
    leftovers = [p.name for p, _ in PUBLISHED if new_post.PLACEHOLDER in p.read_text(encoding="utf-8")]
    assert not leftovers, f"published with '{new_post.PLACEHOLDER}' still in it: {leftovers}"


# --- Generator ---------------------------------------------------------------

@pytest.mark.parametrize("title, slug", [
    ("Ce que j'ai appris sur Facebook Prophet", "ce-que-jai-appris-sur-facebook-prophet"),
    ("What I Learned About Facebook Prophet", "what-i-learned-about-facebook-prophet"),
    ("Été à Montréal : 45°N, ça caille !", "ete-a-montreal-45-n-ca-caille"),
])
def test_slugify_matches_the_existing_posts(title, slug):
    assert new_post.slugify(title) == slug


def test_long_slugs_are_cut_on_a_word():
    slug = new_post.slugify("word " * 30)
    assert len(slug) <= new_post.MAX_SLUG and not slug.endswith("-")


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.setattr(new_post, "POSTS", tmp_path)
    monkeypatch.setattr(new_post, "existing_tags", lambda: {"machine-learning", "kaggle", "meta"})
    return new_post.build(argparse.Namespace(**{
        "title_en": None, "title_fr": None, "tags": "", "description_en": None,
        "description_fr": None, "slug_en": None, "slug_fr": None, "image": None,
        "date": None, "new_tag": False, "ready": False, "dry_run": False, **dict(argv),
    }))


def test_a_pair_is_linked_both_ways_and_starts_unpublished(tmp_path, monkeypatch):
    files = run(tmp_path, monkeypatch, ("title_en", "What I learned about XGBoost"),
                ("title_fr", "Ce que j'ai appris sur XGBoost"), ("tags", "machine-learning,kaggle"))
    (en_path, en_text), (fr_path, fr_text) = files
    en = yaml.safe_load(en_text.split("---", 2)[1])
    fr = yaml.safe_load(fr_text.split("---", 2)[1])
    assert en["translation_url"] == url_of(fr_path) and fr["translation_url"] == url_of(en_path)
    assert (en["lang"], fr["lang"]) == ("en", "fr")
    assert fr["translation_label"].startswith("🇬🇧") and en["translation_label"].startswith("🇫🇷")
    assert en["published"] is False and fr["published"] is False
    assert en["date"] == fr["date"] and when(en["date"]) <= datetime.now(timezone.utc)
    assert "{: .in-brief }" in en_text and "**En bref**" in fr_text


def test_unknown_tags_are_refused_unless_asked(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="Unknown tags: xgboost"):
        run(tmp_path, monkeypatch, ("title_en", "X"), ("tags", "kaggle,xgboost"))
    assert run(tmp_path, monkeypatch, ("title_en", "X"), ("tags", "kaggle,xgboost"), ("new_tag", True))


def test_a_taken_slug_is_refused(tmp_path, monkeypatch):
    (tmp_path / "2026-01-01-hello-universe.md").write_text("---\n---\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="already uses the slug"):
        run(tmp_path, monkeypatch, ("title_en", "Hello, Universe"), ("tags", "meta"))


def test_a_future_date_is_refused():
    with pytest.raises(SystemExit, match="in the future"):
        new_post.parse_date("2999-01-01 12:00")


def test_ready_posts_have_no_published_flag(tmp_path, monkeypatch):
    [(_, text)] = run(tmp_path, monkeypatch, ("title_fr", "Notes"), ("tags", "meta"), ("ready", True))
    assert "published:" not in text
