"""docs/infra/ruleset-main.json: what the main ruleset enforces, and that the
automations it applies to can still merge their own pull requests."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULESET = json.loads((ROOT / "docs" / "infra" / "ruleset-main.json").read_text(encoding="utf-8"))


def rule(kind):
    return next(r for r in RULESET["rules"] if r["type"] == kind)


def test_no_required_status_checks():
    # Checks from a workflow_dispatch CI run are never attached to a PR opened
    # with the GITHUB_TOKEN, so required checks would block the Cosmic Daily
    # auto-merge forever (PR #137). Cosmic Daily waits on its own CI instead.
    assert "required_status_checks" not in {r["type"] for r in RULESET["rules"]}


def test_main_takes_pull_requests_only_and_keeps_its_history():
    assert RULESET["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH"]
    assert {"pull_request", "non_fast_forward", "deletion"} <= {r["type"] for r in RULESET["rules"]}
    assert rule("pull_request")["parameters"]["required_approving_review_count"] == 0


def test_bot_commits_need_no_human_approval():
    # GitHub turns this on when the key is absent; it then waits for a human
    # approval on every PR whose commits come from github-actions[bot], which
    # blocked the Cosmic Daily auto-merge (PR #137).
    assert rule("pull_request")["parameters"]["require_extra_approval_for_unattributed_changes"] is False


def test_bypass_is_admin_only_and_only_when_merging_a_pr():
    # GitHub Actions (app 15368) cannot be a bypass actor: the import fails
    # with "contains an invalid actor".
    assert RULESET["bypass_actors"] == [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}]


def test_cosmic_daily_merges_only_after_its_ci_passed():
    text = (ROOT / ".github" / "workflows" / "cosmic-daily.yml").read_text(encoding="utf-8")
    assert 'gh run watch "$run_id" --exit-status' in text
    assert "gh pr merge" in text
    assert text.index("gh run watch") < text.index("gh pr merge")


def test_automation_prs_run_ci_themselves():
    for workflow in ("cosmic-daily.yml", "repo-data.yml"):
        text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
        assert "gh workflow run ci.yml" in text, workflow
