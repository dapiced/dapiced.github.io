#!/usr/bin/env python3
"""Quarterly review: what the site published, how its checks did, who read it.

Run on the first day of each quarter by .github/workflows/quarterly-review.yml,
which opens the report as a "Quarterly review YYYY-Qn" issue. The plan sets
targets (two posts a month, French versions, LinkedIn as the first source of
readers); this puts the numbers in front of them once a quarter, with three
questions for the author at the end.

Sources, each optional except the repository itself:
- _posts/ and _apod/ for what was published;
- the GitHub API (GH_TOKEN, GITHUB_REPOSITORY) for the scheduled checks;
- the GoatCounter API (GOATCOUNTER_TOKEN, read-only) for visitors and referrers.
A missing source becomes a line saying so, never a failure.

Usage: python tools/site-checks/quarterly_review.py [--quarter 2026-Q4]
Default: the quarter that just ended.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
GOATCOUNTER = "https://dapiced.goatcounter.com"
POSTS_PER_QUARTER = 6  # the plan: two posts a month
WORKFLOWS = {
    "production-health.yml": "Santé de la production (hebdomadaire)",
    "links-weekly.yml": "Liens externes (hebdomadaire)",
    "cosmic-daily.yml": "Cosmic Daily (quotidien)",
}
USER_AGENT = "dominicdapice-quarterly-review (+https://github.com/dapiced/dapiced.github.io)"


@dataclass(frozen=True)
class Quarter:
    year: int
    number: int

    @property
    def start(self) -> date:
        return date(self.year, 3 * self.number - 2, 1)

    @property
    def end(self) -> date:  # exclusive
        return date(self.year + 1, 1, 1) if self.number == 4 else date(self.year, 3 * self.number + 1, 1)

    @property
    def label(self) -> str:
        return f"{self.year}-Q{self.number}"

    @classmethod
    def parse(cls, value: str) -> "Quarter":
        match = re.fullmatch(r"(\d{4})-Q([1-4])", value)
        if not match:
            raise SystemExit(f"--quarter must look like 2026-Q4, not {value!r}")
        return cls(int(match.group(1)), int(match.group(2)))

    @classmethod
    def previous(cls, today: date) -> "Quarter":
        current = (today.month - 1) // 3 + 1
        return cls(today.year - 1, 4) if current == 1 else cls(today.year, current - 1)


# --- Repository ---------------------------------------------------------------

def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return (yaml.safe_load(text.split("---", 2)[1]) or {}) if text.startswith("---") else {}


def published(folder: Path):
    for path in sorted(folder.glob("*.md")):
        data = front_matter(path)
        if data.get("published") is False:
            continue
        yield path, data, date.fromisoformat(path.name[:10])


def content_section(quarter: Quarter, root: Path = ROOT) -> list[str]:
    posts = [(p, d) for p, d, day in published(root / "_posts") if quarter.start <= day < quarter.end]
    by_lang = {"en": 0, "fr": 0}
    for _, data in posts:
        by_lang[data.get("lang", "en")] = by_lang.get(data.get("lang", "en"), 0) + 1
    apod = sum(1 for _, _, day in published(root / "_apod") if quarter.start <= day < quarter.end)
    untranslated = [d.get("title", p.stem) for p, d, _ in published(root / "_posts")
                    if d.get("lang", "en") == "en" and not d.get("translation_url")]

    verdict = "✅" if len(posts) >= POSTS_PER_QUARTER else "⚠️"
    lines = ["## Contenu", "",
             f"- {verdict} **{len(posts)} billet(s)** publiés (cible : {POSTS_PER_QUARTER}, soit deux par mois) : "
             f"{by_lang['en']} EN, {by_lang['fr']} FR."]
    for path, data in posts:
        lines.append(f"  - {path.name[:10]} · {data.get('lang', 'en').upper()} · {data.get('title', path.stem)}")
    lines.append(f"- **{apod} image(s) du jour** publiées par Cosmic Daily.")
    lines.append(f"- **{len(untranslated)} billet(s) EN sans version française**, tous trimestres confondus"
                 + (" :" if untranslated else "."))
    lines += [f"  - {title}" for title in untranslated]
    return lines


# --- GitHub Actions -------------------------------------------------------------

def http_json(url: str, headers: dict) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def workflow_runs(workflow: str, quarter: Quarter, get=http_json) -> list[dict]:
    token, repo = os.environ.get("GH_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise LookupError("GITHUB_REPOSITORY absent")
    headers = {"Accept": "application/vnd.github+json"}
    if token:  # optional for a public repository, but raises the rate limit
        headers["Authorization"] = f"Bearer {token}"
    runs, page = [], 1
    created = f"{quarter.start.isoformat()}..{(quarter.end - timedelta(days=1)).isoformat()}"
    while True:
        query = urllib.parse.urlencode({"created": created, "per_page": 100, "page": page, "status": "completed"})
        data = get(f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/runs?{query}", headers)
        batch = data.get("workflow_runs", [])
        runs += [r for r in batch if r.get("event") == "schedule"]
        if len(batch) < 100:
            return runs
        page += 1


def quality_section(quarter: Quarter, get=http_json) -> list[str]:
    lines = ["## Qualité", "", "Exécutions planifiées du trimestre :", ""]
    for workflow, label in WORKFLOWS.items():
        try:
            runs = workflow_runs(workflow, quarter, get)
        except (LookupError, urllib.error.URLError, ValueError) as error:
            lines.append(f"- {label} : indisponible ({error}).")
            continue
        if not runs:
            lines.append(f"- ➖ {label} : aucune exécution planifiée.")
            continue
        ok = sum(1 for r in runs if r.get("conclusion") == "success")
        failed = len(runs) - ok
        mark = "⚠️" if failed else "✅"
        lines.append(f"- {mark} {label} : {ok} réussie(s), {failed} en échec, sur {len(runs)}.")
    return lines


# --- GoatCounter ----------------------------------------------------------------

def goatcounter_section(quarter: Quarter, get=http_json) -> list[str]:
    lines = ["## Audience (GoatCounter)", ""]
    token = os.environ.get("GOATCOUNTER_TOKEN")
    if not token:
        return lines + ["- Pas de jeton `GOATCOUNTER_API_TOKEN` dans les secrets du dépôt : section sautée. "
                        "Voir `docs/quarterly-review.md`."]
    # RFC 3339, rounded to the hour (GoatCounter API v0); end is exclusive.
    params = urllib.parse.urlencode({"start": f"{quarter.start.isoformat()}T00:00:00Z",
                                     "end": f"{quarter.end.isoformat()}T00:00:00Z"})
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        total = get(f"{GOATCOUNTER}/api/v0/stats/total?{params}", headers)
        hits = get(f"{GOATCOUNTER}/api/v0/stats/hits?{params}&limit=5", headers)
        refs = get(f"{GOATCOUNTER}/api/v0/stats/toprefs?{params}&limit=10", headers)
    except (urllib.error.URLError, ValueError) as error:
        return lines + [f"- API indisponible ({error})."]

    visitors = int(total.get("total", 0) or 0)
    lines.append(f"- **{visitors} visiteurs** sur le trimestre.")
    referrers = refs.get("stats") or []
    linkedin = sum(int(r.get("count", 0) or 0) for r in referrers if "linkedin" in str(r.get("name", "")).lower())
    if visitors:
        share = 100 * linkedin / visitors
        mark = "✅" if share >= 35 else "⚠️"
        lines.append(f"- {mark} **{share:.0f} % venus de LinkedIn** (cible du plan : 35 %).")
    lines += ["", "Pages les plus lues :", ""]
    lines += [f"- {h.get('path', '?')} : {h.get('count', 0)}" for h in (hits.get("hits") or [])] or ["- aucune donnée"]
    lines += ["", "Principales sources :", ""]
    lines += [f"- {r.get('name') or '(direct)'} : {r.get('count', 0)}" for r in referrers] or ["- aucune donnée"]
    return lines


# --- Report ---------------------------------------------------------------------

def report(quarter: Quarter, get=http_json, root: Path = ROOT) -> str:
    sections = [
        [f"Revue du trimestre **{quarter.label}** ({quarter.start:%Y-%m-%d} au "
         f"{quarter.end - timedelta(days=1):%Y-%m-%d}), générée automatiquement."],
        content_section(quarter, root),
        quality_section(quarter, get),
        goatcounter_section(quarter, get),
        ["## Search Console", "",
         "- [ ] Ouvrir [Search Console](https://search.google.com/search-console) : impressions sur les "
         "requêtes cibles, pages FR indexées."],
        ["## À remplir", "",
         "- **Qu'est-ce qui a marché ?**", "- **Quoi arrêter ?**", "- **Prochain sujet ?**", "",
         "Fermer l'issue une fois remplie : elle reste comme trace du trimestre."],
    ]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quarter", help="e.g. 2026-Q4; default: the quarter that just ended")
    args = parser.parse_args(argv)
    quarter = Quarter.parse(args.quarter) if args.quarter else Quarter.previous(datetime.now(timezone.utc).date())
    print(report(quarter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
