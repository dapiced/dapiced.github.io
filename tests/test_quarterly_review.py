"""Quarterly review (tools/site-checks/quarterly_review.py and its workflow):
quarter arithmetic, a report built from the repository even with no API,
GoatCounter numbers read from the documented v0 fields, minimal permissions."""
import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("quarterly_review", ROOT / "tools" / "site-checks" / "quarterly_review.py")
qr = importlib.util.module_from_spec(spec)
sys.modules["quarterly_review"] = qr
spec.loader.exec_module(qr)

WORKFLOW = yaml.safe_load((ROOT / ".github" / "workflows" / "quarterly-review.yml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("today, label", [
    (date(2027, 1, 1), "2026-Q4"), (date(2026, 10, 1), "2026-Q3"),
    (date(2026, 4, 15), "2026-Q1"), (date(2026, 7, 1), "2026-Q2"),
])
def test_previous_quarter(today, label):
    assert qr.Quarter.previous(today).label == label


def test_quarter_bounds():
    q4 = qr.Quarter.parse("2026-Q4")
    assert (q4.start, q4.end) == (date(2026, 10, 1), date(2027, 1, 1))
    with pytest.raises(SystemExit):
        qr.Quarter.parse("2026-T4")


def write(folder: Path, name: str, front: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(f"---\n{front}\n---\nbody\n", encoding="utf-8")


def test_report_without_any_api(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GOATCOUNTER_TOKEN", raising=False)
    write(tmp_path / "_posts", "2026-10-02-a.md", 'title: "A"\nlang: en\ntranslation_url: /blog/2026/10/b/')
    write(tmp_path / "_posts", "2026-10-02-b.md", 'title: "B"\nlang: fr\ntranslation_url: /blog/2026/10/a/')
    write(tmp_path / "_posts", "2026-11-03-c.md", 'title: "C"')
    write(tmp_path / "_posts", "2026-11-04-draft.md", 'title: "Draft"\npublished: false')
    write(tmp_path / "_posts", "2026-09-30-old.md", 'title: "Old"')
    write(tmp_path / "_apod", "2026-10-05-x.md", 'title: "X"')
    text = qr.report(qr.Quarter.parse("2026-Q4"), root=tmp_path)
    assert "**3 billet(s)**" in text and "2 EN, 1 FR" in text
    assert "Draft" not in text.split("## Qualité")[0].split("sans version française")[0]
    assert "**1 image(s) du jour**" in text
    assert "- C" in text and "- Old" in text  # EN posts without a French version
    assert "indisponible (GITHUB_REPOSITORY absent)" in text
    assert "section sautée" in text and "## À remplir" in text


def test_goatcounter_fields(monkeypatch):
    monkeypatch.setenv("GOATCOUNTER_TOKEN", "test-token")
    seen = []

    def fake(url, headers):
        seen.append((url, headers))
        if "/stats/total" in url:
            return {"total": 200, "total_events": 0, "total_utc": 200}
        if "/stats/hits" in url:
            return {"hits": [{"path": "/blog/x/", "count": 50}], "more": False}
        return {"stats": [{"name": "www.linkedin.com", "count": 80}, {"name": "Google", "count": 40}], "more": False}

    lines = "\n".join(qr.goatcounter_section(qr.Quarter.parse("2026-Q4"), fake))
    assert "**200 visiteurs**" in lines and "40 % venus de LinkedIn" in lines and "✅" in lines
    assert "/blog/x/ : 50" in lines and "Google : 40" in lines
    assert all(h["Authorization"] == "Bearer test-token" for _, h in seen)
    assert "start=2026-10-01T00%3A00%3A00Z" in seen[0][0] and "end=2027-01-01T00%3A00%3A00Z" in seen[0][0]


def test_workflow_is_quarterly_with_minimal_permissions():
    triggers = WORKFLOW.get("on") or WORKFLOW.get(True)
    assert triggers["schedule"] == [{"cron": "23 13 1 1,4,7,10 *"}]
    assert WORKFLOW["permissions"] == {}
    assert WORKFLOW["jobs"]["review"]["permissions"] == {"contents": "read", "actions": "read", "issues": "write"}


def test_goatcounter_token_only_reaches_the_report_step():
    text = (ROOT / ".github" / "workflows" / "quarterly-review.yml").read_text(encoding="utf-8")
    assert text.count("secrets.GOATCOUNTER_API_TOKEN") == 1
    steps = WORKFLOW["jobs"]["review"]["steps"]
    with_secret = [s["name"] for s in steps if "GOATCOUNTER_API_TOKEN" in str(s.get("env", {}))]
    assert with_secret == ["Write the review"]


def test_a_rerun_comments_instead_of_editing_the_issue():
    step = next(s for s in WORKFLOW["jobs"]["review"]["steps"] if s["name"] == "Open one issue per quarter")
    assert "gh issue comment" in step["run"] and "gh issue create" in step["run"]
    assert "gh issue edit" not in step["run"]
