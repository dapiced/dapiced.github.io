from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "now-freshness.yml"


def load_workflow() -> tuple[str, dict]:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    if True in workflow and "on" not in workflow:
        workflow["on"] = workflow.pop(True)
    return text, workflow


def test_workflow_runs_monthly_and_manually():
    text, workflow = load_workflow()

    assert workflow["on"]["workflow_dispatch"] is None
    assert workflow["on"]["schedule"] == [{"cron": "17 14 1 * *"}]
    assert re.search(r"python tools/site-checks/check_now_freshness\.py", text)


def test_workflow_separates_read_only_check_and_stale_notification():
    text, workflow = load_workflow()
    check = workflow["jobs"]["check"]
    notify = workflow["jobs"]["notify"]

    assert check["permissions"] == {"contents": "read"}
    assert notify["permissions"] == {"issues": "write"}
    assert any(step.get("uses", "").startswith("actions/checkout@") for step in check["steps"])
    assert not any(step.get("uses", "").startswith("actions/checkout@") for step in notify["steps"])
    assert notify["if"] == "needs.check.outputs.stale == 'true'"
    notify_step = notify["steps"][0]
    assert "needs.check.outputs.updated" in notify_step["env"]["UPDATED"]
    assert "needs.check.outputs.age_days" in notify_step["env"]["AGE_DAYS"]

    assert workflow["permissions"] == {}
    assert "gh api" in text
    assert "gh issue create" in text
    assert "Refresh /now/ page" in text
    assert 'if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]' in text
    assert "set -euo pipefail" in text
    assert "gh issue comment" not in text
    assert "actions/github-script" not in text


def test_workflow_notification_deduplicates_open_issue_without_labels_or_checkout():
    text, workflow = load_workflow()
    notify_text = "\n".join(
        step.get("run", "") for step in workflow["jobs"]["notify"]["steps"]
    )

    assert "gh api" in notify_text
    assert "--paginate" in notify_text
    assert "state=open&per_page=100" in notify_text
    assert "pull_request" in notify_text
    assert 'open_titles="$(gh api' in notify_text
    assert 'grep -Fx "Refresh /now/ page" >/dev/null' in notify_text
    assert "grep -Fxq" not in notify_text
    assert "gh issue list" not in notify_text
    assert "issues: write" in text
    assert "labels" not in notify_text
    assert "checkout" not in notify_text.lower()
    assert "comment" not in notify_text.lower()


def test_workflow_issue_lookup_fails_closed_before_exact_title_check():
    _, workflow = load_workflow()
    notify_text = "\n".join(
        step.get("run", "") for step in workflow["jobs"]["notify"]["steps"]
    )

    lookup_start = notify_text.index('open_titles="$(gh api')
    lookup_end = notify_text.index(')"', lookup_start)
    exact_title_check = notify_text.index('grep -Fx "Refresh /now/ page"')

    assert lookup_start < lookup_end < exact_title_check
    assert "|| true" not in notify_text[lookup_start:lookup_end]
