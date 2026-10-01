from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RESUME_PATH = ROOT / "resume" / "index.html"
LINKEDIN_URL = "https://www.linkedin.com/in/dapiced/"


def read_resume_template() -> str:
    assert RESUME_PATH.is_file(), "resume/index.html must define the /resume/ page"
    return RESUME_PATH.read_text(encoding="utf-8")


def load_yaml(name: str):
    return yaml.safe_load((ROOT / "_data" / f"{name}.yml").read_text(encoding="utf-8"))


def test_resume_template_renders_shared_timeline_and_skills():
    template = read_resume_template()

    assert "{% for item in site.data.timeline %}" in template
    assert "{{ item.year | escape }}" in template
    assert "{{ item.role | escape }}" in template
    assert "{{ item.description | escape }}" in template
    assert "{% for group in site.data.skills %}" in template
    assert "{{ group.domain | escape }}" in template
    assert "{% for tag in group.tags %}" in template
    assert "{{ tag | escape }}" in template

    shared_content = template.split(
        '<section class="resume-section resume-profiles"',
        maxsplit=1,
    )[0]
    for item in load_yaml("timeline"):
        for value in item.values():
            assert value not in shared_content

    for group in load_yaml("skills"):
        assert group["domain"] not in shared_content
        for tag in group["tags"]:
            static_value = rf"(?<![\w]){re.escape(tag)}(?![\w])"
            assert re.search(static_value, shared_content) is None


def test_site_ci_runs_resume_source_contracts_before_building():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "python -m pytest \\" in workflow
    assert "tests/test_resume_page.py \\" in workflow
    assert "tests/test_site_data.py -q" in workflow
    assert workflow.index("tests/test_site_data.py -q") < workflow.index(
        "bundle exec jekyll build"
    )


def test_resume_template_has_accessible_structure_and_actions():
    template = read_resume_template()

    assert template.count("<h1") == 1
    assert "<h2" in template
    assert "Experience" in template
    assert "Technical capabilities" in template
    assert "Profiles and contact" in template
    assert "Montréal, Canada" in template
    assert '<ol class="resume-experience-list">' in template
    assert '<ul class="resume-skill-groups">' in template
    assert '<button type="button"' in template
    assert "data-print-resume" in template
    assert "Print / save as PDF" in template


def test_resume_uses_linkedin_as_its_only_contact_channel():
    template = read_resume_template()

    assert f'href="{LINKEDIN_URL}"' in template
    assert "Contact on LinkedIn" in template
    assert 'target="_blank"' in template
    assert 'rel="noopener"' in template
    assert "mailto:" not in template.lower()
    assert "<form" not in template.lower()


def test_resume_links_to_existing_public_profiles_safely():
    template = read_resume_template()

    for url in (
        LINKEDIN_URL,
        "https://github.com/dapiced",
        "https://www.kaggle.com/dominicdapice",
        "https://huggingface.co/dapiced",
    ):
        assert f'href="{url}"' in template

    assert template.count('target="_blank"') >= 4
    assert template.count('rel="noopener"') >= 4


def test_resume_assets_support_responsive_layout_and_printing():
    stylesheet = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    javascript = (ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8")

    assert ".resume-page" in stylesheet
    assert ".resume-experience-item" in stylesheet
    assert ".resume-skill-group" in stylesheet
    assert "@media (max-width: 700px)" in stylesheet
    assert "@media print" in stylesheet
    for selector in (".nav", ".footer", "#starfield", ".resume-actions"):
        assert selector in stylesheet.split("@media print", maxsplit=1)[1]

    assert 'querySelector("[data-print-resume]")' in javascript
    assert "window.print()" in javascript


def test_resume_print_styles_do_not_change_other_pages():
    template = read_resume_template()
    layout = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
    stylesheet = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    print_styles = stylesheet.split("@media print", maxsplit=1)[1].split(
        "/* ---------- beyond ---------- */",
        maxsplit=1,
    )[0]

    assert "body_class: resume-document" in template
    assert (
        '<body{% if page.body_class %} class="{{ page.body_class | escape }}"{% endif %}>'
        in layout
    )
    assert "@page resume" in print_styles
    assert "body.resume-document" in print_styles
    assert re.search(r"(?m)^\s*body\s*\{", print_styles) is None
    for selector in (".nav", ".footer", "#starfield", ".skip-link", ".gold-tip"):
        assert f"body.resume-document {selector}" in print_styles
