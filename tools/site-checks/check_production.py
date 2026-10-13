#!/usr/bin/env python3
"""Checks the live site, as visitors get it through Cloudflare.

Pull requests test the build; this tests what is actually served: the
security headers set at the edge (docs/infra/cloudflare-phase0.md), the
HTTPS redirect, the pages and files the features depend on, and the share
images LinkedIn fetches. Run weekly by .github/workflows/production-health.yml.

Usage: python tools/site-checks/check_production.py [--base https://dominicdapice.com]
Exit code 1 when a check fails; the report is printed as Markdown.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

USER_AGENT = "dominicdapice-production-health (+https://github.com/dapiced/dapiced.github.io)"


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes = b""
    location: str = ""


@dataclass
class Report:
    passed: list = field(default_factory=list)
    failed: list = field(default_factory=list)

    def check(self, condition: bool, label: str, detail: str = "") -> None:
        (self.passed if condition else self.failed).append(label + (f": {detail}" if detail and not condition else ""))

    def markdown(self) -> str:
        lines = [f"**{len(self.passed)} passed, {len(self.failed)} failed**", ""]
        lines += [f"- ❌ {item}" for item in self.failed]
        lines += [f"- ✅ {item}" for item in self.passed]
        return "\n".join(lines)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # keep 3xx visible to the checks
        return None


def fetch(url: str, follow: bool = True) -> Response:
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=30) as response:
            return Response(response.status, {k.lower(): v for k, v in response.headers.items()}, response.read())
    except urllib.error.HTTPError as error:
        headers = {k.lower(): v for k, v in error.headers.items()}
        return Response(error.code, headers, b"", headers.get("location", ""))


def check_security_headers(report: Report, headers: dict) -> None:
    csp = headers.get("content-security-policy", "")
    report.check("default-src 'self'" in csp and "frame-ancestors 'none'" in csp, "Content-Security-Policy is enforced", csp or "missing")
    hsts = headers.get("strict-transport-security", "")
    age = re.search(r"max-age=(\d+)", hsts)
    report.check(bool(age) and int(age.group(1)) >= 31536000, "HSTS max-age is at least one year", hsts or "missing")
    report.check(headers.get("x-content-type-options", "").lower() == "nosniff", "X-Content-Type-Options: nosniff")
    report.check(bool(headers.get("referrer-policy")), "Referrer-Policy is set")
    report.check("camera=()" in headers.get("permissions-policy", ""), "Permissions-Policy is set")
    report.check(headers.get("cross-origin-opener-policy", "") == "same-origin", "Cross-Origin-Opener-Policy: same-origin")


def og_image(html: str) -> str:
    match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    return match.group(1) if match else ""


def run(base: str, get=fetch) -> Report:
    report = Report()
    home = get(base + "/")
    report.check(home.status == 200, "Homepage answers 200", str(home.status))
    check_security_headers(report, home.headers)

    plain = get(base.replace("https://", "http://") + "/", follow=False)
    report.check(plain.status in (301, 308) and plain.location.startswith("https://"), "HTTP redirects to HTTPS", f"{plain.status} {plain.location}")

    french = get(base + "/fr/")
    report.check(french.status == 200 and b'<html lang="fr"' in french.body, "French homepage /fr/ is served in French")

    for path, needle in (
        ("/sw.js", b"const SHELL_URLS"),
        ("/offline/", b"You are offline"),
        ("/manifest.webmanifest", b'"start_url"'),
        ("/sitemap.xml", b"/fr/"),
    ):
        response = get(base + path)
        report.check(response.status == 200 and needle in response.body, f"{path} is served")

    for path, minimum in (("/search-index.json", 30), ("/assets/data/sky-catalog.json", 1)):
        response = get(base + path)
        try:
            data = json.loads(response.body)
            size = len(data if isinstance(data, list) else data.get("stars", []))
            report.check(size >= minimum, f"{path} is valid JSON", f"{size} entries")
        except ValueError:
            report.check(False, f"{path} is valid JSON", f"status {response.status}")

    post = get(base + "/blog/2026/07/a-star-for-my-father/")
    for page, label in ((home, "homepage"), (post, "A Star for My Father")):
        image = og_image(page.body.decode("utf-8", "replace"))
        response = get(image) if image else Response(0, {})
        report.check(response.status == 200 and response.headers.get("content-type", "").startswith("image/"),
                     f"Share image loads ({label})", image or "no og:image")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="https://dominicdapice.com")
    args = parser.parse_args(argv)
    report = run(args.base.rstrip("/"))
    print(report.markdown())
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
