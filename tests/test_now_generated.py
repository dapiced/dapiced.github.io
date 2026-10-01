from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "site-checks" / "check_now_generated.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_now_generated", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prepare_site(tmp_path: Path, generated: str) -> None:
    (tmp_path / "now").mkdir(exist_ok=True)
    (tmp_path / "_site" / "now").mkdir(parents=True, exist_ok=True)
    (tmp_path / "now" / "index.html").write_text(
        "---\nupdated: 2026-10-01\n---\n", encoding="utf-8"
    )
    (tmp_path / "_site" / "now" / "index.html").write_text(
        generated, encoding="utf-8"
    )


def test_generated_now_check_requires_matching_rendered_date(tmp_path: Path):
    checker = load_checker()
    checker.ROOT = tmp_path

    prepare_site(tmp_path, '<time datetime="2026-10-01">October 1, 2026</time>')
    assert checker.main() == 0

    prepare_site(tmp_path, '<time datetime="2026-09-30">September 30, 2026</time>')
    assert checker.main() == 1


def test_generated_now_check_rejects_missing_output(tmp_path: Path):
    checker = load_checker()
    checker.ROOT = tmp_path
    (tmp_path / "now").mkdir()
    (tmp_path / "now" / "index.html").write_text(
        "---\nupdated: 2026-10-01\n---\n", encoding="utf-8"
    )

    assert checker.main() == 1
