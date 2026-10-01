"""Tests for the build-time GitHub project-card generator.

The homepage used to call api.github.com from the visitor's browser. The data
now comes from `_data/repos.json`, refreshed by
`tools/repo_cards/generate_repo_data.py`. These tests pin the behaviour that
used to live in assets/js/main.js: filtering, pinned repos, sort order,
description cleanup, language colours and the Ansible topic fallback.

Fixtures are real GitHub REST payload shapes, trimmed to the fields the
generator reads.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "tools" / "repo_cards" / "generate_repo_data.py"
DATA_FILE = REPO_ROOT / "_data" / "repos.json"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_repo_data", GENERATOR_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    if not GENERATOR_PATH.exists():
        pytest.fail(f"missing generator: {GENERATOR_PATH}")
    return _load_generator()


def repo(
    name,
    *,
    fork=False,
    description="An automation role",
    language="Python",
    stars=0,
    forks=0,
    topics=(),
    updated_at="2026-01-01T00:00:00Z",
):
    """A trimmed but real-shaped GET /users/:user/repos item."""
    return {
        "name": name,
        "full_name": f"dapiced/{name}",
        "html_url": f"https://github.com/dapiced/{name}",
        "fork": fork,
        "description": description,
        "language": language,
        "stargazers_count": stars,
        "forks_count": forks,
        "topics": list(topics),
        "updated_at": updated_at,
        "private": False,
    }


@pytest.fixture
def payload():
    return [
        repo("dapiced", description="profile readme", language="Markdown", stars=9),
        repo("dapiced.github.io", description="this site", language="HTML", stars=7),
        repo("some-fork", fork=True, stars=50),
        repo("titanic", description="Kaggle Titanic", language="Jupyter Notebook", stars=0),
        repo("rhel_vmware_disk_manager", stars=3, forks=1),
        repo(
            "patch_update_yum",
            description="An Ansible role that upgrade yum packages",
            language=None,
            stars=2,
            forks=2,
            topics=("ansible", "yum"),
        ),
        repo("newer", stars=1, updated_at="2026-05-02T00:00:00Z"),
        repo("older", stars=1, updated_at="2026-05-01T00:00:00Z"),
    ]


# --- selection --------------------------------------------------------------


def test_forks_and_profile_repos_are_excluded(gen, payload):
    names = [card["name"] for card in gen.build_cards(payload)]
    assert "some-fork" not in names
    assert "dapiced" not in names
    assert "dapiced.github.io" not in names


def test_pinned_repo_comes_first_despite_zero_stars(gen, payload):
    cards = gen.build_cards(payload)
    assert cards[0]["name"] == "titanic"
    assert cards[0]["stars"] == 0


def test_remaining_repos_are_sorted_by_stars_then_recency(gen, payload):
    names = [card["name"] for card in gen.build_cards(payload)]
    assert names[1:] == [
        "rhel_vmware_disk_manager",
        "patch_update_yum",
        "newer",
        "older",
    ]


def test_at_most_nine_cards_are_kept(gen):
    payload = [repo(f"repo-{i:02d}", stars=100 - i) for i in range(20)]
    assert len(gen.build_cards(payload)) == 9


def test_selection_is_deterministic(gen, payload):
    assert gen.build_cards(payload) == gen.build_cards(list(reversed(payload)))


# --- card contents ----------------------------------------------------------


def test_card_exposes_the_fields_the_template_renders(gen, payload):
    card = next(c for c in gen.build_cards(payload) if c["name"] == "rhel_vmware_disk_manager")
    assert card == {
        "name": "rhel_vmware_disk_manager",
        "url": "https://github.com/dapiced/rhel_vmware_disk_manager",
        "description": "An automation role",
        "language": "Python",
        "language_color": "#3572A5",
        "stars": 3,
        "forks": 1,
    }


def test_missing_description_falls_back_to_a_neutral_label(gen):
    card = gen.build_cards([repo("quiet", description=None)])[0]
    assert card["description"] == "Automation project"


def test_markdown_bold_markers_are_stripped_from_descriptions(gen):
    card = gen.build_cards([repo("bolded", description="An **Ansible** role")])[0]
    assert card["description"] == "An Ansible role"


def test_long_descriptions_are_truncated_with_an_ellipsis(gen):
    card = gen.build_cards([repo("verbose", description="x" * 200)])[0]
    assert card["description"] == "x" * 129 + "\u2026"
    assert len(card["description"]) == 130


def test_descriptions_of_exactly_the_limit_are_kept_intact(gen):
    card = gen.build_cards([repo("borderline", description="y" * 130)])[0]
    assert card["description"] == "y" * 130


def test_ansible_topic_is_used_when_github_reports_no_language(gen, payload):
    card = next(c for c in gen.build_cards(payload) if c["name"] == "patch_update_yum")
    assert card["language"] == "Ansible"
    assert card["language_color"] == "#EE0000"


def test_language_less_repo_without_the_ansible_topic_has_no_language(gen):
    card = gen.build_cards([repo("plain", language=None, topics=("docs",))])[0]
    assert card["language"] is None
    assert card["language_color"] is None


def test_unknown_languages_get_the_default_accent_colour(gen):
    card = gen.build_cards([repo("exotic", language="Brainfuck")])[0]
    assert card["language_color"] == "#bc8cff"


# --- document and file ------------------------------------------------------


def test_document_wraps_cards_under_a_repositories_key(gen, payload):
    document = gen.build_document(payload)
    assert list(document) == ["repositories"]
    assert document["repositories"] == gen.build_cards(payload)


def test_rendered_json_is_stable_and_newline_terminated(gen, payload):
    text = gen.render_json(gen.build_document(payload))
    assert text.endswith("\n")
    assert text == gen.render_json(gen.build_document(payload))
    assert json.loads(text) == gen.build_document(payload)


def test_refresh_writes_the_document_and_reports_a_change(gen, tmp_path, payload):
    out = tmp_path / "repos.json"
    changed = gen.refresh(out, fetch_pages=lambda: payload)
    assert changed is True
    assert json.loads(out.read_text(encoding="utf-8")) == gen.build_document(payload)


def test_refresh_is_idempotent(gen, tmp_path, payload):
    out = tmp_path / "repos.json"
    gen.refresh(out, fetch_pages=lambda: payload)
    assert gen.refresh(out, fetch_pages=lambda: payload) is False


def test_api_failure_propagates_and_keeps_the_committed_data(gen, tmp_path):
    out = tmp_path / "repos.json"
    out.write_text('{"repositories": [{"name": "kept"}]}\n', encoding="utf-8")

    def boom():
        raise RuntimeError("GitHub API returned HTTP 503")

    with pytest.raises(RuntimeError):
        gen.refresh(out, fetch_pages=boom)

    assert json.loads(out.read_text(encoding="utf-8"))["repositories"][0]["name"] == "kept"


def test_an_empty_api_response_is_rejected_instead_of_emptying_the_file(gen, tmp_path):
    out = tmp_path / "repos.json"
    out.write_text('{"repositories": [{"name": "kept"}]}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        gen.refresh(out, fetch_pages=lambda: [])
    assert "kept" in out.read_text(encoding="utf-8")


# --- HTTP transport ---------------------------------------------------------


class _FakeResponse:
    """Minimal stand-in for the context manager returned by urlopen."""

    def __init__(self, payload):
        self.status = 200
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(gen, monkeypatch, pages):
    """Serve `pages` in order and record every Request object sent."""
    sent = []
    queue = list(pages)

    def fake_urlopen(request, timeout=None):
        sent.append(request)
        return _FakeResponse(queue.pop(0) if queue else [])

    monkeypatch.setattr(gen.urllib.request, "urlopen", fake_urlopen)
    return sent


def test_fetch_sends_a_usable_bearer_token(gen, monkeypatch):
    sent = _capture_urlopen(gen, monkeypatch, [[repo("titanic")]])
    gen.fetch_pages(token="ghp_example")
    assert sent[0].get_header("Authorization") == "Bearer ghp_example"


def test_fetch_stays_anonymous_without_a_token(gen, monkeypatch):
    sent = _capture_urlopen(gen, monkeypatch, [[repo("titanic")]])
    gen.fetch_pages()
    assert sent[0].get_header("Authorization") is None


def test_fetch_stops_once_a_page_is_not_full(gen, monkeypatch):
    sent = _capture_urlopen(gen, monkeypatch, [[repo(f"r{i}") for i in range(3)]])
    assert len(gen.fetch_pages()) == 3
    assert len(sent) == 1


def test_a_truncated_listing_fails_instead_of_committing_partial_data(gen, monkeypatch):
    full_page = [repo(f"r{i}") for i in range(gen.PAGE_SIZE)]
    _capture_urlopen(gen, monkeypatch, [full_page] * gen.MAX_PAGES)
    with pytest.raises(gen.RefreshError):
        gen.fetch_pages()


# --- committed data ---------------------------------------------------------


def test_committed_repo_data_exists_and_matches_the_card_schema(gen):
    assert DATA_FILE.exists(), "_data/repos.json must be committed for the build"
    document = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    cards = document["repositories"]
    assert 1 <= len(cards) <= 9
    for card in cards:
        assert set(card) == {
            "name",
            "url",
            "description",
            "language",
            "language_color",
            "stars",
            "forks",
        }
        assert card["url"].startswith("https://github.com/dapiced/")
        assert isinstance(card["stars"], int)
        assert isinstance(card["forks"], int)
        assert card["description"]
        assert len(card["description"]) <= 130


def test_committed_repo_data_is_rendered_by_the_generator(gen):
    text = DATA_FILE.read_text(encoding="utf-8")
    assert text == gen.render_json(json.loads(text))
