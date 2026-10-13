"""Offline support: the service worker (sw.js) caches the shell it declares,
falls back to the "Signal lost" page in the reader's language, and is
registered by main.js. The browser check lives in
tools/site-checks/browser/pwa-check.mjs."""
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SW = (ROOT / "sw.js").read_text(encoding="utf-8")


def test_shell_lists_only_files_that_exist():
    shell = SW.split("{%- capture shell -%}", 1)[1].split("{%- endcapture -%}", 1)[0]
    for line in filter(None, (l.strip() for l in shell.splitlines())):
        asset = re.match(r"{{ '([^']+)' \| asset_digest }}", line)
        path = asset.group(1) if asset else line
        target = ROOT / path.strip("/")
        assert target.is_file() or (target / "index.html").is_file(), path


def test_offline_pages_are_a_hidden_translation_pair():
    for page, other in (("offline", "/fr/hors-ligne/"), ("fr/hors-ligne", "/offline/")):
        text = (ROOT / page / "index.html").read_text(encoding="utf-8")
        front = yaml.safe_load(text.split("---", 2)[1])
        assert front["sitemap"] is False and front["translation_url"] == other
        assert "offline.js" in text


def test_worker_strategy():
    assert 'request.mode === "navigate"' in SW
    assert '"/fr/hors-ligne/" : "/offline/"' in SW
    assert "url.origin !== self.location.origin" in SW  # third parties untouched
    assert "{{ shell | strip | text_digest }}" in SW     # new assets, new worker


def test_main_registers_the_worker():
    main = (ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8")
    assert 'navigator.serviceWorker.register("/sw.js")' in main
