from __future__ import annotations

from pathlib import Path

from cosmic_daily.repository import RepositoryContext


def test_repository_detects_duplicates(tmp_path):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    post_path = posts_dir / "2024-03-15-apod-duplicate.md"
    post_path.write_text(
        "---\nlayout: post\napod_date: 2024-03-15\napod_url: \"https://apod.nasa.gov/apod/ap20240315.html\"\n---\n",
        encoding="utf-8",
    )

    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates("2024-03-15", "https://apod.nasa.gov/apod/ap20240315.html")
    assert duplicates == [post_path]


def test_repository_ignores_current_post_when_checking_duplicates(tmp_path):
    posts_dir = tmp_path / "_posts"
    posts_dir.mkdir()
    post_path = posts_dir / "2024-03-15-apod-duplicate.md"
    post_path.write_text(
        "---\nlayout: post\napod_date: 2024-03-15\napod_url: \"https://apod.nasa.gov/apod/ap20240315.html\"\n---\n",
        encoding="utf-8",
    )

    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates(
        "2024-03-15",
        "https://apod.nasa.gov/apod/ap20240315.html",
        exclude_path=post_path,
    )
    assert duplicates == []
