"""Contracts of the design system (assets/css/style.css, docs/design-system.md)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "css" / "style.css").read_text(encoding="utf-8")
LAYOUT = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")

# Gold means Vincenzo D'Apice. These are the only places allowed to use it.
GOLD_SELECTORS = {
    ".hero-coords a:hover",          # coordinates of his star
    ".motto.vincenzo-day",           # 12 September, his birthday
    ".gold-tip",                     # tooltip of his star
    ".gold-tip .tip-name",
    ".footer-dedication a",
    ".footer-dedication a:hover",
    ".palette-output.palette-vincenzo",  # `ping vincenzo` in the command palette
}


def _block(selector: str) -> str:
    start = CSS.index(selector + " {")
    return CSS[start:CSS.index("}", start)]


def _rules():
    # Flat "selector { body }" pairs, good enough for this hand-written file.
    css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        yield " ".join(match.group(1).split()), match.group(2)


def test_gold_is_reserved_for_vincenzo():
    offenders = []
    for selector, body in _rules():
        if selector.startswith((":root", "[data-theme")):
            continue
        if "--gold" in body or "--rgb-gold" in body:
            if selector not in GOLD_SELECTORS:
                offenders.append(selector)
    assert not offenders, f"gold used outside Vincenzo's elements: {offenders}"


def test_dawn_theme_redefines_every_themed_colour():
    night = set(re.findall(r"(--[\w-]+):", _block(":root")))
    dawn = set(re.findall(r"(--[\w-]+):", _block('[data-theme="light"]')))
    # Accents shared by both themes and non-colour tokens are defined once.
    shared = {"--accent-blue", "--accent-violet", "--rgb-accent-blue", "--rgb-accent-violet",
              "--rgb-sky", "--font", "--mono", "--display", "--ease", "--dur-fast", "--dur",
              "--dur-slow"} | {t for t in night if t.startswith("--space-")}
    missing = sorted(night - dawn - shared)
    assert not missing, f"Dawn theme does not redefine: {missing}"


def test_no_hard_coded_rgba_outside_print():
    screen = CSS[: CSS.index("@media print")] + CSS[CSS.index("/* ---------- beyond"):]
    assert "rgba(" not in screen, "use rgb(var(--rgb-…) / alpha) tokens"


def test_self_hosted_fonts_stay_within_budget():
    urls = re.findall(r'url\("(/assets/fonts/[^"]+\.woff2)"\)', CSS)
    assert urls, "no @font-face found"
    total = sum((ROOT / url.lstrip("/")).stat().st_size for url in urls)
    assert total <= 90 * 1024, f"fonts weigh {total} bytes, budget is 90 KiB"
    for licence in ("OFL-Archivo.txt", "OFL-IBM-Plex.txt"):
        assert (ROOT / "assets" / "fonts" / licence).is_file()


def test_theme_is_applied_before_first_paint():
    head = LAYOUT[: LAYOUT.index("</head>")]
    init = head.index("/assets/js/theme-init.js")
    assert init < head.index("/assets/css/style.css")
    tag = head[head.rfind("<script", 0, init): head.index(">", init)]
    assert "defer" not in tag and "async" not in tag, "theme-init must block to avoid a flash"
