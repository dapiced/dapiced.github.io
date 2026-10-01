from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable


class RepositoryContext:
    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.root = self._resolve_root(repo_root)
        self.apod_dir = self.root / "_apod"
        # Legacy location: APOD entries lived in _posts before the /sky/ collection.
        self.posts_dir = self.root / "_posts"
        self.assets_apod_dir = self.root / "assets" / "img" / "apod"

    @staticmethod
    def _resolve_root(repo_root: str | Path | None = None) -> Path:
        if repo_root is not None:
            return Path(repo_root).resolve()

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(Path.cwd()),
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return Path.cwd().resolve()
        return Path(result.stdout.strip()).resolve()

    def ensure_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def safe_relative_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        resolved = (self.root / candidate).resolve()
        if self.root not in resolved.parents and resolved != self.root:
            raise ValueError(f"Refusing to write outside repository: {path}")
        return resolved

    def find_duplicates(self, apod_date: str, apod_url: str, exclude_path: str | Path | None = None) -> list[Path]:
        excluded = Path(exclude_path).resolve() if exclude_path is not None else None
        duplicates: list[Path] = []
        for directory, needs_apod_marker in ((self.apod_dir, False), (self.posts_dir, True)):
            if not directory.exists():
                continue
            for entry_path in sorted(directory.glob("*.md")):
                if excluded is not None and entry_path.resolve() == excluded:
                    continue
                name_matches = bool(apod_date) and entry_path.name.startswith(f"{apod_date}-")
                if name_matches and (not needs_apod_marker or "apod" in entry_path.name.lower()):
                    duplicates.append(entry_path)
                elif apod_date and self._front_matter_has(entry_path, "apod_date", apod_date):
                    duplicates.append(entry_path)
                elif apod_url and self._front_matter_has(entry_path, "apod_url", apod_url):
                    duplicates.append(entry_path)
        return duplicates

    @staticmethod
    def _front_matter_has(post_path: Path, field: str, expected: str) -> bool:
        try:
            content = post_path.read_text(encoding="utf-8")
        except OSError:
            return False
        if not content.startswith("---"):
            return False
        header, _, _ = content.partition("\n---\n")
        if not header:
            return False
        for line in header.splitlines()[1:]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            if key.strip() == field and value.strip().strip('"\'') == expected:
                return True
        return False

    def list_post_files(self) -> Iterable[Path]:
        if not self.posts_dir.exists():
            return []
        return sorted(self.posts_dir.glob("*.md"))

    def list_apod_files(self) -> Iterable[Path]:
        if not self.apod_dir.exists():
            return []
        return sorted(self.apod_dir.glob("*.md"))
