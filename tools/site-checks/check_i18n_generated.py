#!/usr/bin/env python3
"""Checks the generated bilingual chrome after `jekyll build`.

- every page declares <html lang>, a full og:locale (fr_CA / en_CA) that matches
  it, and French pages render the French navigation, footer and buttons;
- every page with a translation_url links to it with reciprocal hreflang
  alternates and a language switch in the header;
- every other page still shows the switch, pointing to the homepage of the
  other language (/ or /fr/).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"


def fail(message: str) -> None:
    print(f"i18n check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    i18n = yaml.safe_load((ROOT / "_data" / "i18n.yml").read_text(encoding="utf-8"))
    navigation = yaml.safe_load((ROOT / "_data" / "navigation.yml").read_text(encoding="utf-8"))
    missing = sorted(set(i18n["en"]) - set(i18n["fr"]))
    if missing:
        fail(f"_data/i18n.yml fr is missing keys: {missing}")

    pages = [p for p in SITE.rglob("*.html") if 'http-equiv="refresh"' not in p.read_text(encoding="utf-8", errors="ignore")]
    french = 0
    pairs = 0
    for page in pages:
        html = page.read_text(encoding="utf-8")
        lang_match = re.search(r'<html lang="([a-z]{2})"', html)
        if not lang_match:
            continue  # standalone files without the default layout
        lang = lang_match.group(1)
        rel = page.relative_to(SITE)
        locale = re.search(r'<meta property="og:locale" content="([^"]+)"', html)
        if locale and locale.group(1) != f"{lang}_CA":
            fail(f"{rel}: og:locale {locale.group(1)} does not match lang {lang}")
        if lang == "fr":
            french += 1
            for item in navigation:
                if f">{item['label_fr']}</a>" not in html:
                    fail(f"{rel}: French navigation label '{item['label_fr']}' missing")
            for key in ("nav_label", "footer_projects", "theme_to_light", "dedication"):
                if i18n["fr"][key].replace("'", "&#39;") not in html and i18n["fr"][key] not in html:
                    fail(f"{rel}: French chrome string '{key}' missing")
        switch = re.search(r'<a class="lang-switch" href="([^"]+)" hreflang="([a-z]{2})"', html)
        alternate = re.findall(r'<link rel="alternate" hreflang="([a-z-]+)" href="([^"]+)">', html)
        home_switch = re.search(r'<a class="lang-switch lang-switch-home" href="([^"]+)" hreflang="([a-z]{2})"', html)
        if not switch and not home_switch:
            fail(f"{rel}: no language switch in the header")
        if home_switch:
            target, target_lang = home_switch.groups()
            expected = "/fr/" if lang == "en" else "/"
            if target != expected or target_lang == lang:
                fail(f"{rel}: untranslated page should switch to {expected}, not {target}")
        if switch:
            pairs += 1
            target, target_lang = switch.groups()
            if target_lang == lang:
                fail(f"{rel}: language switch points to the same language")
            if not any(h == target_lang and href.endswith(target) for h, href in alternate):
                fail(f"{rel}: no hreflang={target_lang} alternate for {target}")
            target_file = SITE / target.strip("/") / "index.html"
            if not target_file.is_file():
                fail(f"{rel}: translation {target} does not exist")
            if f'hreflang="{lang}"' not in target_file.read_text(encoding="utf-8"):
                fail(f"{rel}: {target} does not link back with hreflang={lang}")
    if french == 0:
        fail("no French page found")
    print(f"i18n check passed: {french} French pages, {pairs} pages with a language switch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
