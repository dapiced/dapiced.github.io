#!/usr/bin/env python3
"""Refresh `_data/repos.json` from dapiced's public GitHub repositories.

The homepage used to call api.github.com from the visitor's browser, so the
project cards were invisible to crawlers and to anyone with JavaScript
disabled. The cards are now rendered by Jekyll from the JSON file this script
produces.

Failure is deliberate: if the GitHub API misbehaves, the script raises and
writes nothing, so the committed data stays as it is.

Usage:
    python tools/repo_cards/generate_repo_data.py

Set `GITHUB_TOKEN` to raise the API rate limit; it is not required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "_data" / "repos.json"

USER = "dapiced"
API_URL = "https://api.github.com/users/{user}/repos?per_page=100&page={page}&sort=updated"
PAGE_SIZE = 100
MAX_PAGES = 10

#: Repositories pinned to the front of the grid, in display order.
PINNED = ("titanic",)
#: Not projects: the profile readme and this site.
EXCLUDED = {"dapiced", "dapiced.github.io"}
#: The grid shows three rows of three cards.
MAX_CARDS = 9

DEFAULT_DESCRIPTION = "Automation project"
MAX_DESCRIPTION = 130

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "R": "#198CE7",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "JavaScript": "#f1e05a",
    "PowerShell": "#012456",
    "Jinja": "#a52a22",
    "Dockerfile": "#384d54",
    "Perl": "#0298c3",
    "Jupyter Notebook": "#DA5B0B",
    "Markdown": "#083fa1",
    "YAML": "#cb171e",
    "Text": "#6e7681",
    "Ansible": "#EE0000",
}
DEFAULT_LANGUAGE_COLOR = "#bc8cff"


class RefreshError(RuntimeError):
    """The GitHub data could not be fetched or is unusable."""


def fetch_pages(user: str = USER, token: str | None = None) -> list[dict]:
    """Return every public repository of `user`.

    Transport and HTTP errors are turned into `RefreshError`: a partial
    listing would silently drop cards from the homepage.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "dapiced-repo-cards",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repositories: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        request = urllib.request.Request(API_URL.format(user=user, page=page), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise RefreshError(f"GitHub API returned HTTP {response.status}")
                batch = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise RefreshError(f"GitHub API returned HTTP {error.code} on page {page}") from error
        except urllib.error.URLError as error:
            raise RefreshError(f"GitHub API unreachable: {error.reason}") from error

        if not isinstance(batch, list):
            raise RefreshError("Unexpected GitHub API payload: expected a list")
        repositories.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    else:
        raise RefreshError(
            f"More than {MAX_PAGES * PAGE_SIZE} repositories returned: the listing "
            "would be truncated, refusing to write a partial card set"
        )

    return repositories


def _clean_description(raw: str | None) -> str:
    text = (raw or "").replace("**", "").strip() or DEFAULT_DESCRIPTION
    if len(text) > MAX_DESCRIPTION:
        text = text[: MAX_DESCRIPTION - 1] + "\u2026"
    return text


def _language(repository: dict) -> str | None:
    language = repository.get("language")
    if language:
        return language
    if "ansible" in (repository.get("topics") or []):
        return "Ansible"
    return None


def _descending(value: str) -> tuple[int, ...]:
    """Sort a string descending inside an otherwise ascending sort key."""
    return tuple(-ord(char) for char in value)


def _sort_key(repository: dict):
    name = repository.get("name", "")
    pinned_rank = PINNED.index(name) if name in PINNED else len(PINNED)
    return (
        pinned_rank,
        -int(repository.get("stargazers_count") or 0),
        _descending(str(repository.get("updated_at") or "")),
        name,
    )


def select_repositories(payload: list[dict]) -> list[dict]:
    kept = [
        repository
        for repository in payload
        if not repository.get("fork") and repository.get("name") not in EXCLUDED
    ]
    kept.sort(key=_sort_key)
    return kept[:MAX_CARDS]


def to_card(repository: dict) -> dict:
    language = _language(repository)
    return {
        "name": repository["name"],
        "url": repository["html_url"],
        "description": _clean_description(repository.get("description")),
        "language": language,
        "language_color": (
            LANGUAGE_COLORS.get(language, DEFAULT_LANGUAGE_COLOR) if language else None
        ),
        "stars": int(repository.get("stargazers_count") or 0),
        "forks": int(repository.get("forks_count") or 0),
    }


def build_cards(payload: list[dict]) -> list[dict]:
    return [to_card(repository) for repository in select_repositories(payload)]


def build_document(payload: list[dict]) -> dict:
    return {"repositories": build_cards(payload)}


def render_json(document: dict) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def refresh(output_path, fetch_pages=fetch_pages) -> bool:
    """Rewrite `output_path` from the GitHub API. Returns True if it changed.

    The file is only touched once a usable payload is in hand, so a failed
    refresh leaves the committed data untouched.
    """
    document = build_document(fetch_pages())
    if not document["repositories"]:
        raise ValueError("GitHub returned no usable repository: keeping the committed data")

    text = render_json(document)
    output_path = Path(output_path)
    if output_path.exists() and output_path.read_text(encoding="utf-8") == text:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh _data/repos.json from GitHub.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    try:
        changed = refresh(args.output, fetch_pages=lambda: fetch_pages(token=token))
    except (RefreshError, ValueError, OSError) as error:
        print(f"Refresh failed: {error}", file=sys.stderr)
        return 1

    print("changed" if changed else "unchanged")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if changed else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
