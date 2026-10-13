"""tools/site-checks/check_production.py against canned responses: a healthy
site passes, a missing edge header or a broken share image fails."""
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_production", ROOT / "tools" / "site-checks" / "check_production.py")
prod = importlib.util.module_from_spec(spec)
sys.modules["check_production"] = prod
spec.loader.exec_module(prod)

HEADERS = {
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), microphone=()",
    "cross-origin-opener-policy": "same-origin",
}
OG = b'<meta property="og:image" content="https://example.test/card.jpg">'


def healthy(url, follow=True):
    R = prod.Response
    if url.startswith("http://"):
        return R(301, {}, b"", "https://example.test/")
    if url.endswith("/card.jpg"):
        return R(200, {"content-type": "image/jpeg"})
    bodies = {
        "/fr/": b'<html lang="fr">' + OG,
        "/sw.js": b"const SHELL_URLS = []",
        "/offline/": b"You are offline",
        "/manifest.webmanifest": b'{"start_url": "/"}',
        "/sitemap.xml": b"<loc>https://example.test/fr/</loc>",
        "/search-index.json": b"[" + b",".join([b"{}"] * 40) + b"]",
        "/assets/data/sky-catalog.json": b'{"stars": [[0, 0, 1, 0]]}',
    }
    path = url.replace("https://example.test", "")
    return R(200, dict(HEADERS), bodies.get(path, OG))


def test_healthy_site_passes():
    report = prod.run("https://example.test", get=healthy)
    assert report.failed == [], report.failed


def test_missing_csp_and_broken_share_image_fail():
    def broken(url, follow=True):
        response = healthy(url, follow)
        response.headers.pop("content-security-policy", None)
        if url.endswith("/card.jpg"):
            return prod.Response(404, {})
        return response

    failed = prod.run("https://example.test", get=broken).failed
    assert any("Content-Security-Policy" in item for item in failed)
    assert any("Share image" in item for item in failed)


def test_workflow_runs_weekly_and_opens_a_single_issue():
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "production-health.yml").read_text(encoding="utf-8"))
    assert workflow["permissions"] == {}
    assert workflow["jobs"]["notify"]["permissions"] == {"issues": "write"}
    text = (ROOT / ".github" / "workflows" / "production-health.yml").read_text(encoding="utf-8")
    assert 'grep -Fx "$title"' in text
