"""Invariants for the homepage project cards.

The cards must be rendered by Jekyll from `_data/repos.json` so they are
indexable and still visible without JavaScript. The browser must not call the
GitHub API anymore, but the rest of the homepage script has to stay untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX = REPO_ROOT / "index.html"
MAIN_JS = REPO_ROOT / "assets" / "js" / "main.js"
DATA_FILE = REPO_ROOT / "_data" / "repos.json"


def index_html() -> str:
    return INDEX.read_text(encoding="utf-8")


def main_js() -> str:
    return MAIN_JS.read_text(encoding="utf-8")


def test_homepage_loops_over_the_committed_repo_data():
    html = index_html()
    assert re.search(r"{%-?\s*for\s+\w+\s+in\s+site\.data\.repos\.repositories", html), (
        "index.html must render the cards from _data/repos.json"
    )


def test_homepage_no_longer_hardcodes_project_cards():
    html = index_html()
    grid = html.split('id="projects-grid"', 1)[1].split("</div>", 1)[0]
    assert "https://github.com/dapiced/" not in grid, (
        "project URLs must come from the data file, not from hardcoded anchors"
    )


def test_homepage_renders_every_committed_card_field():
    html = index_html()
    for fragment in (".url", ".name", ".description", ".stars"):
        assert fragment in html, f"template does not use repo{fragment}"
    assert "language_color" in html
    assert "forks" in html


def test_homepage_does_not_promise_a_per_visit_api_refresh():
    html = index_html()
    assert "refreshed from the GitHub API every time you visit" not in html


def test_api_derived_values_are_escaped_in_the_template():
    """Liquid does not escape by default; the old renderer used textContent."""
    html = index_html()
    grid = html.split('id="projects-grid"', 1)[1].split("</section>", 1)[0]
    for field in ("url", "description", "name"):
        assert re.search(rf"{{{{\s*repo\.{field}\s*\|\s*escape\s*}}}}", grid), (
            f"repo.{field} must be rendered through the escape filter"
        )


def test_browser_script_no_longer_calls_the_github_api():
    assert "api.github.com" not in main_js()


def test_browser_script_no_longer_builds_project_cards():
    script = main_js()
    assert "projects-grid" not in script
    assert "LANG_COLORS" not in script
    assert "stargazers_count" not in script


def test_unrelated_homepage_behaviour_is_kept():
    script = main_js()
    for marker in (
        "starfield",
        "IntersectionObserver",
        "goatcounter",
        "nav-toggle",
        "typed",
    ):
        assert marker in script, f"unrelated feature '{marker}' disappeared from main.js"


def test_data_file_is_valid_json_for_jekyll():
    document = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    assert isinstance(document["repositories"], list)
    assert document["repositories"]
