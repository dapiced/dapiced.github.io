from __future__ import annotations

from cosmic_daily.repository import RepositoryContext

FRONT = "---\nlayout: {layout}\napod_date: 2024-03-15\napod_url: \"https://apod.nasa.gov/apod/ap20240315.html\"\n---\n"


def _write(directory, name, layout="apod"):
    directory.mkdir(exist_ok=True)
    path = directory / name
    path.write_text(FRONT.format(layout=layout), encoding="utf-8")
    return path


def test_repository_writes_entries_to_apod_collection(tmp_path):
    repo = RepositoryContext(repo_root=tmp_path)
    assert repo.apod_dir == tmp_path.resolve() / "_apod"


def test_repository_detects_duplicates_in_apod_collection(tmp_path):
    entry = _write(tmp_path / "_apod", "2024-03-15-duplicate.md")
    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates("2024-03-15", "https://apod.nasa.gov/apod/ap20240315.html")
    assert duplicates == [entry]


def test_repository_detects_duplicates_in_legacy_posts(tmp_path):
    post = _write(tmp_path / "_posts", "2024-03-15-apod-duplicate.md", layout="post")
    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates("2024-03-15", "https://apod.nasa.gov/apod/ap20240315.html")
    assert duplicates == [post]


def test_repository_detects_duplicate_by_url_only(tmp_path):
    entry = _write(tmp_path / "_apod", "2024-03-14-other-name.md")
    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates("2099-01-01", "https://apod.nasa.gov/apod/ap20240315.html")
    assert duplicates == [entry]


def test_repository_ignores_current_entry_when_checking_duplicates(tmp_path):
    entry = _write(tmp_path / "_apod", "2024-03-15-duplicate.md")
    repo = RepositoryContext(repo_root=tmp_path)
    duplicates = repo.find_duplicates(
        "2024-03-15",
        "https://apod.nasa.gov/apod/ap20240315.html",
        exclude_path=entry,
    )
    assert duplicates == []


def test_repository_lists_apod_entries(tmp_path):
    entry = _write(tmp_path / "_apod", "2024-03-15-one.md")
    repo = RepositoryContext(repo_root=tmp_path)
    assert list(repo.list_apod_files()) == [entry]
