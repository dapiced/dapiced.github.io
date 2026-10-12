"""The site must never name the author's current employer.

This is a deliberate editorial rule, not a style preference: the employer is
not mentioned anywhere in the published site or in the repository, and this
test blocks any change that would introduce it (posts, portfolio, data files,
layouts, generated APOD entries, documentation).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EMPLOYER = re.compile(r"\bhydro" + r"[\s_\-]*" + r"qu[eé]bec", re.IGNORECASE)
TEXT_SUFFIXES = {
    ".html", ".md", ".markdown", ".yml", ".yaml", ".json", ".xml", ".txt",
    ".js", ".css", ".scss", ".py", ".rb", ".toml", ".svg", ".webmanifest",
}
# Third-party code copied verbatim is not authored content.
SKIPPED_PREFIXES = ("assets/vendor/",)


def tracked_text_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    files = []
    for name in filter(None, output.split("\0")):
        if name.startswith(SKIPPED_PREFIXES):
            continue
        path = ROOT / name
        # This file spells the name on purpose, to test the pattern itself.
        if path == Path(__file__).resolve():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES and path.is_file():
            files.append(path)
    return files


def test_pattern_catches_the_usual_spellings():
    for spelling in ("Hydro-Québec", "hydro quebec", "HYDRO_QUEBEC", "HydroQuébec"):
        assert EMPLOYER.search(spelling), spelling
    for harmless in ("hydrogen", "hydrogène", "hydrostatic", "Québec City"):
        assert not EMPLOYER.search(harmless), harmless


def test_repository_never_names_the_employer():
    offenders = []
    for path in tracked_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if EMPLOYER.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}")
    assert not offenders, "Employer name found in: " + ", ".join(offenders)
