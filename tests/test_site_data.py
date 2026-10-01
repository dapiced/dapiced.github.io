from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "tools" / "site-checks" / "validate_site_data.py"
HTML_CHECKER_PATH = ROOT / "tools" / "site-checks" / "check_site_data_html.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    return load_module("validate_site_data", VALIDATOR_PATH)


def test_site_data_files_match_required_schema():
    validator = load_validator()

    data = validator.load_site_data(ROOT)

    assert data["navigation"] == [
        {"label": "About", "href": "/#about"},
        {"label": "Projects", "href": "/#projects"},
        {"label": "Portfolios", "href": "/portfolio/"},
        {"label": "Timeline", "href": "/#timeline"},
        {"label": "Resume", "href": "/resume/"},
        {"label": "Blogs", "href": "/blog/"},
        {"label": "Now", "href": "/now/"},
        {
            "label": "My LabML",
            "href": "https://app.dominicdapice.com/",
            "class": "nav-labml",
            "target": "_blank",
            "rel": "noopener",
        },
        {"label": "Resources", "href": "/resources/"},
        {
            "label": "Contact",
            "href": "https://www.linkedin.com/in/dapiced/",
            "target": "_blank",
            "rel": "noopener",
        },
        {
            "label": "GitHub ↗",
            "href": "https://github.com/dapiced",
            "class": "nav-gh",
            "target": "_blank",
            "rel": "noopener",
        },
    ]
    assert data["skills"][0] == {
        "domain": "Cloud & Data",
        "tags": ["Azure", "Databricks", "VMware", "Azure DevOps"],
    }
    assert data["timeline"][0] == {
        "year": "2026 - NOW",
        "role": "Developer - Azure Infrastructure AI",
        "description": "Azure for AI · Databricks platform · MLOps / DataOps · IaC · CI/CD",
    }
    assert data["resources"][0] == {
        "icon": "🌌",
        "title": "Astronomy",
        "description": (
            "Exploring celestial objects and following the latest discoveries - "
            "from JWST deep fields to backyard skies."
        ),
        "href": "/blog/astronomy/",
        "more": "Read articles →",
    }


def test_validate_site_data_rejects_missing_required_field(tmp_path: Path):
    validator = load_validator()
    data_dir = tmp_path / "_data"
    data_dir.mkdir()

    for name in validator.SCHEMAS:
        source = ROOT / "_data" / f"{name}.yml"
        (data_dir / f"{name}.yml").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    navigation = yaml.safe_load((data_dir / "navigation.yml").read_text(encoding="utf-8"))
    del navigation[0]["href"]
    (data_dir / "navigation.yml").write_text(
        yaml.safe_dump(navigation, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(validator.SiteDataError, match=r"navigation\[0\].*href"):
        validator.load_site_data(tmp_path)


def test_validate_site_data_rejects_unpaired_external_link_attributes(tmp_path: Path):
    validator = load_validator()
    data_dir = tmp_path / "_data"
    data_dir.mkdir()

    for name in validator.SCHEMAS:
        source = ROOT / "_data" / f"{name}.yml"
        (data_dir / f"{name}.yml").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    navigation = yaml.safe_load((data_dir / "navigation.yml").read_text(encoding="utf-8"))
    del navigation[-1]["rel"]
    (data_dir / "navigation.yml").write_text(
        yaml.safe_dump(navigation, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(
        validator.SiteDataError,
        match=r"navigation\[10\].*target and rel",
    ):
        validator.load_site_data(tmp_path)


def test_templates_render_the_four_data_contracts_with_liquid_loops():
    layout = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "{% for item in site.data.navigation %}" in layout
    assert "{{ item.label | escape }}" in layout
    assert "{{ item.href | escape }}" in layout

    for data_name, variable in (
        ("skills", "group"),
        ("timeline", "item"),
        ("resources", "resource"),
    ):
        assert f"{{% for {variable} in site.data.{data_name} %}}" in homepage


def test_html_parser_extracts_the_four_rendered_contracts():
    checker = load_module("check_site_data_html", HTML_CHECKER_PATH)

    rendered = checker.parse_rendered_homepage(
        """
        <ul id="nav-links">
          <li><a class="nav-gh" href="https://example.com" target="_blank" rel="noopener">Example ↗</a></li>
        </ul>
        <div class="skill-row">
          <span class="skill-domain">Cloud &amp; Data</span>
          <span class="skill-tags"><span class="tag">Azure</span><span class="tag">Databricks</span></span>
        </div>
        <div class="tl-item">
          <span class="tl-year">2026 - NOW</span>
          <p class="tl-role">Developer</p>
          <p class="tl-desc">Infrastructure · Data</p>
        </div>
        <a class="beyond-card reveal" href="/blog/astronomy/">
          <span class="icon">🌌</span>
          <h3>Astronomy</h3>
          <p>Backyard skies.</p>
          <span class="beyond-more">Read articles →</span>
        </a>
        """
    )

    assert rendered == {
        "navigation": [
            {
                "href": "https://example.com",
                "class": "nav-gh",
                "target": "_blank",
                "rel": "noopener",
                "label": "Example ↗",
            }
        ],
        "skills": [{"domain": "Cloud & Data", "tags": ["Azure", "Databricks"]}],
        "timeline": [
            {
                "year": "2026 - NOW",
                "role": "Developer",
                "description": "Infrastructure · Data",
            }
        ],
        "resources": [
            {
                "href": "/blog/astronomy/",
                "icon": "🌌",
                "title": "Astronomy",
                "description": "Backyard skies.",
                "more": "Read articles →",
            }
        ],
    }


def test_html_parser_extracts_rendered_resume_contract():
    checker = load_module("check_site_data_html_resume", HTML_CHECKER_PATH)

    rendered = checker.parse_rendered_resume(
        """
        <article class="resume-page">
          <h1>Dominic D'Apice</h1>
          <section><h2>Experience</h2>
            <ol class="resume-experience-list">
              <li class="resume-experience-item">
                <p class="resume-experience-year">2026 - NOW</p>
                <div><h3>Developer</h3><p>Infrastructure · Data</p></div>
              </li>
            </ol>
          </section>
          <section><h2>Technical capabilities</h2>
            <ul class="resume-skill-groups">
              <li class="resume-skill-group">
                <h3>Cloud &amp; Data</h3>
                <ul><li class="tag">Azure</li><li class="tag">Databricks</li></ul>
              </li>
            </ul>
          </section>
          <section><h2>Profiles and contact</h2>
            <a class="resume-contact-link" href="https://www.linkedin.com/in/dapiced/" target="_blank" rel="noopener">Contact on LinkedIn</a>
            <a class="resume-profile-link" href="https://github.com/dapiced" target="_blank" rel="noopener">GitHub</a>
          </section>
          <button type="button" data-print-resume>Print / save as PDF</button>
        </article>
        """
    )

    assert rendered == {
        "timeline": [
            {
                "year": "2026 - NOW",
                "role": "Developer",
                "description": "Infrastructure · Data",
            }
        ],
        "skills": [{"domain": "Cloud & Data", "tags": ["Azure", "Databricks"]}],
        "headings": [
            "Dominic D'Apice",
            "Experience",
            "Technical capabilities",
            "Profiles and contact",
        ],
        "contact_links": [
            {
                "href": "https://www.linkedin.com/in/dapiced/",
                "target": "_blank",
                "rel": "noopener",
                "label": "Contact on LinkedIn",
            }
        ],
        "profile_links": [
            {
                "href": "https://github.com/dapiced",
                "target": "_blank",
                "rel": "noopener",
                "label": "GitHub",
            }
        ],
        "all_links": [
            {
                "href": "https://www.linkedin.com/in/dapiced/",
                "target": "_blank",
                "rel": "noopener",
                "label": "Contact on LinkedIn",
            },
            {
                "href": "https://github.com/dapiced",
                "target": "_blank",
                "rel": "noopener",
                "label": "GitHub",
            },
        ],
        "has_print_control": True,
        "has_form": False,
        "has_mailto": False,
    }


def write_generated_resume(
    root: Path,
    *,
    reverse_timeline: bool = False,
    contact_target: str = "_blank",
    include_form: bool = False,
    include_mailto: bool = False,
    extra_link: str = "",
) -> None:
    validator = load_validator()
    tools_dir = root / "tools" / "site-checks"
    tools_dir.mkdir(parents=True)
    (tools_dir / "validate_site_data.py").write_text(
        VALIDATOR_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    data_dir = root / "_data"
    data_dir.mkdir(parents=True)
    for name in validator.SCHEMAS:
        source = ROOT / "_data" / f"{name}.yml"
        (data_dir / f"{name}.yml").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    timeline = yaml.safe_load((data_dir / "timeline.yml").read_text(encoding="utf-8"))
    skills = yaml.safe_load((data_dir / "skills.yml").read_text(encoding="utf-8"))
    if reverse_timeline:
        timeline.reverse()

    timeline_html = "".join(
        (
            '<li class="resume-experience-item">'
            f'<p class="resume-experience-year">{item["year"]}</p>'
            f'<div><h3>{item["role"]}</h3><p>{item["description"]}</p></div>'
            "</li>"
        )
        for item in timeline
    )
    skills_html = "".join(
        (
            '<li class="resume-skill-group">'
            f'<h3>{group["domain"]}</h3><ul>'
            + "".join(f'<li class="tag">{tag}</li>' for tag in group["tags"])
            + "</ul></li>"
        )
        for group in skills
    )
    form_html = "<form></form>" if include_form else ""
    mailto_html = '<a href="mailto:private@example.com">Email</a>' if include_mailto else ""

    output = root / "_site" / "resume"
    output.mkdir(parents=True)
    (output / "index.html").write_text(
        f"""
        <article class="resume-page">
          <h1>Dominic D'Apice</h1>
          <h2>Experience</h2><ol>{timeline_html}</ol>
          <h2>Technical capabilities</h2><ul>{skills_html}</ul>
          <h2>Profiles and contact</h2>
          <a class="resume-contact-link" href="https://www.linkedin.com/in/dapiced/" target="{contact_target}" rel="noopener">Contact on LinkedIn</a>
          <a class="resume-profile-link" href="https://www.linkedin.com/in/dapiced/" target="_blank" rel="noopener">LinkedIn</a>
          <a class="resume-profile-link" href="https://github.com/dapiced" target="_blank" rel="noopener">GitHub</a>
          <a class="resume-profile-link" href="https://www.kaggle.com/dominicdapice" target="_blank" rel="noopener">Kaggle</a>
          <a class="resume-profile-link" href="https://huggingface.co/dapiced" target="_blank" rel="noopener">Hugging Face</a>
          <button data-print-resume>Print</button>
          {form_html}{mailto_html}{extra_link}
        </article>
        """,
        encoding="utf-8",
    )


def test_validate_rendered_resume_rejects_missing_output(tmp_path: Path):
    checker = load_module("check_site_data_html_missing_resume", HTML_CHECKER_PATH)

    with pytest.raises(checker.HtmlDataError, match="generated resume is missing"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_reordered_timeline(tmp_path: Path):
    checker = load_module("check_site_data_html_reordered_resume", HTML_CHECKER_PATH)
    write_generated_resume(tmp_path, reverse_timeline=True)

    with pytest.raises(checker.HtmlDataError, match="timeline does not match"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_unsafe_external_link(tmp_path: Path):
    checker = load_module("check_site_data_html_unsafe_resume", HTML_CHECKER_PATH)
    write_generated_resume(tmp_path, contact_target="_self")

    with pytest.raises(checker.HtmlDataError, match="safe external-link attributes"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_form(tmp_path: Path):
    checker = load_module("check_site_data_html_form_resume", HTML_CHECKER_PATH)
    write_generated_resume(tmp_path, include_form=True)

    with pytest.raises(checker.HtmlDataError, match="must not contain a form"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_mailto(tmp_path: Path):
    checker = load_module("check_site_data_html_mailto_resume", HTML_CHECKER_PATH)
    write_generated_resume(tmp_path, include_mailto=True)

    with pytest.raises(checker.HtmlDataError, match="approved public links"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_phone_link(tmp_path: Path):
    checker = load_module("check_site_data_html_phone_resume", HTML_CHECKER_PATH)
    write_generated_resume(
        tmp_path,
        extra_link='<a href="tel:+15551234567">Call</a>',
    )

    with pytest.raises(checker.HtmlDataError, match="approved public links"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_rendered_resume_rejects_unapproved_contact_service(tmp_path: Path):
    checker = load_module("check_site_data_html_service_resume", HTML_CHECKER_PATH)
    write_generated_resume(
        tmp_path,
        extra_link=(
            '<a href="https://contact.example/dapiced" target="_blank" '
            'rel="noopener">Contact service</a>'
        ),
    )

    with pytest.raises(checker.HtmlDataError, match="approved public links"):
        checker.validate_rendered_resume(tmp_path)


def test_validate_site_data_rejects_reordered_content(tmp_path: Path):
    validator = load_validator()
    data_dir = tmp_path / "_data"
    data_dir.mkdir()

    for name in validator.SCHEMAS:
        source = ROOT / "_data" / f"{name}.yml"
        (data_dir / f"{name}.yml").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    skills = yaml.safe_load((data_dir / "skills.yml").read_text(encoding="utf-8"))
    skills[0], skills[1] = skills[1], skills[0]
    (data_dir / "skills.yml").write_text(
        yaml.safe_dump(skills, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(validator.SiteDataError, match=r"skills.*approved content"):
        validator.load_site_data(tmp_path)
