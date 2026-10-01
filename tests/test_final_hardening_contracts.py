from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]


def test_default_layout_declares_dark_theme_and_manifest():
    layout = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
    assert '<meta name="theme-color" content="#04060f">' in layout
    assert '<link rel="manifest" href="/manifest.webmanifest">' in layout


def test_manifest_is_minimal_and_uses_branded_icon():
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "Dominic D'Apice"
    assert manifest["display"] == "browser"
    assert manifest["start_url"] == "/"
    assert manifest["theme_color"] == "#04060f"
    assert manifest["background_color"] == "#04060f"
    assert manifest["icons"] == [{"src": "/assets/favicon.svg", "sizes": "64x64", "type": "image/svg+xml"}]
    assert "service_worker" not in manifest


def test_license_and_readme_define_split_scope():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "authored articles" in license_text
    assert "refreshed by workflow" in readme
    assert "One-time step after this is merged" not in readme
    assert "GoatCounter" in readme


def test_completed_hardening_docs_match_the_implemented_contracts():
    plan = (ROOT / "docs" / "superpowers" / "plans" / "2026-10-01-final-site-hardening-implementation.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "tools" / "cosmic-daily" / "README.md").read_text(encoding="utf-8")
    for nonexistent_reference in (
        "tests/test_generated_site.py",
        "tests/test_documentation_contract.py",
        "tests/test_content_validator.py",
        "tests/test_editorial_images.py",
        "ValidationResult",
        "validate_generated_article",
        "rights_category",
        "site.webmanifest",
    ):
        assert nonexistent_reference not in plan
    assert "tests/test_final_hardening_contracts.py" in plan
    assert "tools/cosmic-daily/tests/test_cli.py" in plan
    assert "only explicit NASA/public-domain rights metadata" in readme
    assert "manual-review candidates remain open" in readme
    assert "Preview-only runs do not open failure issues" in readme


def test_repo_card_auth_uses_bearer_token_without_literal_placeholder():
    source = (ROOT / "tools" / "repo_cards" / "generate_repo_data.py").read_text(encoding="utf-8")
    assert 'headers["Authorization"] = f"Bearer {token}"' in source
    assert "******" not in source


def test_indexnow_manual_dispatch_is_explicitly_intentional():
    source = (ROOT / ".github" / "workflows" / "indexnow.yml").read_text(encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch'" in source
    assert "github.event.workflow_run.event == 'push'" in source
    assert "github.event.workflow_run.event == 'workflow_dispatch'" not in source


def test_heading_order_and_editorial_intrinsic_dimensions():
    now = (ROOT / "now" / "index.html").read_text(encoding="utf-8")
    blog = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")
    assert "<h2>Studying</h2>" in now
    assert "<h2>IT Infrastructure</h2>" in blog
    star = (ROOT / "_posts" / "2026-07-02-a-star-for-my-father.md").read_text(encoding="utf-8")
    nothing = (ROOT / "_posts" / "2026-07-02-nothingness-has-no-address.md").read_text(encoding="utf-8")
    assert re.search(r'etoile-vincenzo\.svg"[^>]*\bwidth="900"[^>]*\bheight="480"', star)
    assert re.search(r'nothingness-has-no-address\.svg"[^>]*\bwidth="1200"[^>]*\bheight="1772"', nothing)
