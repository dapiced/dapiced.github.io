from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOW_PATH = ROOT / "now" / "index.html"


def read_now_template() -> str:
    assert NOW_PATH.is_file(), "now/index.html must define the /now/ page"
    return NOW_PATH.read_text(encoding="utf-8")


def test_now_page_uses_the_approved_date_and_durable_themes():
    template = read_now_template()

    assert re.search(r"^updated:\s*2026-10-01\s*$", template, re.MULTILINE)
    assert template.count('class="beyond-card reveal"') == 4
    assert "University Certificate in Data Science" in template
    assert "Kaggle" in template
    assert "Azure" in template and "Databricks" in template
    assert "MLOps / DataOps" in template and 'href="/blog/"' in template
    assert "~200" not in template
    assert "1,500" not in template
    assert "Azure DevOps Pipelines to GitHub Actions" not in template
    assert "Montréal, Canada" in template
    assert "https://nownownow.com/about" in template
    assert "https://nownownow.com/p/1Fe6" in template


def test_now_page_preserves_semantic_structure_and_safe_external_links():
    template = read_now_template()

    assert template.count("<h1") == 1
    assert template.count("<h2>") == 4
    assert "{{ page.updated }}" in template
    assert template.count('target="_blank"') >= 2
    assert template.count('rel="noopener"') >= 2
    assert "Finishing a" in template
    assert "certificate" in template.lower()
    assert "certificate in data science</strong> is complete" not in template.lower()
