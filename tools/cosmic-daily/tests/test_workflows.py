"""Static checks on the GitHub Actions workflows and Dependabot config.

These run in the normal pytest suite so a broken deployment pipeline is caught
before it reaches `main`. They parse the YAML instead of grepping text: the
point is to pin the triggers, permissions and essential steps, not wording.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
PAGES_WORKFLOW_NAME = "Deploy to GitHub Pages"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML reads the bare `on:` key as the boolean True (YAML 1.1 rules).
    if True in data:
        data["on"] = data.pop(True)
    return data


def steps_of(job: dict) -> list[dict]:
    return job.get("steps", [])


def uses_action(job: dict, action: str) -> bool:
    return any(str(step.get("uses", "")).startswith(action) for step in steps_of(job))


def run_commands(job: dict) -> str:
    return "\n".join(str(step.get("run", "")) for step in steps_of(job))


@pytest.fixture(scope="module")
def pages() -> dict:
    return load(WORKFLOWS / "pages.yml")


@pytest.fixture(scope="module")
def ci() -> dict:
    return load(WORKFLOWS / "ci.yml")


@pytest.fixture(scope="module")
def indexnow() -> dict:
    return load(WORKFLOWS / "indexnow.yml")


# --- Pages deployment -------------------------------------------------------


def test_pages_workflow_name_is_stable(pages):
    # indexnow.yml keys its workflow_run trigger on this exact name.
    assert pages["name"] == PAGES_WORKFLOW_NAME


def test_pages_triggers_on_main_push_only(pages):
    triggers = pages["on"]
    assert triggers["push"]["branches"] == ["main"]
    assert "workflow_dispatch" in triggers
    # ci.yml covers pull requests; the deploy workflow must not request
    # pages/id-token write permissions on untrusted PR builds.
    assert "pull_request" not in triggers


def test_pages_permissions_are_minimal_and_sufficient(pages):
    assert pages["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }


def test_pages_serializes_deployments(pages):
    concurrency = pages["concurrency"]
    assert concurrency["group"] == "pages"
    # A queued deploy must wait, not be dropped: never cancel in progress.
    assert concurrency["cancel-in-progress"] is False


def test_pages_build_uses_the_repo_gemfile(pages):
    build = pages["jobs"]["build"]
    assert uses_action(build, "ruby/setup-ruby@")
    setup = next(s for s in steps_of(build) if str(s.get("uses", "")).startswith("ruby/setup-ruby@"))
    assert setup["with"]["bundler-cache"] is True
    assert "bundle exec jekyll build" in run_commands(build)


def test_pages_build_publishes_an_artifact(pages):
    build = pages["jobs"]["build"]
    assert uses_action(build, "actions/configure-pages@")
    assert uses_action(build, "actions/upload-pages-artifact@")


def test_pages_deploy_only_runs_for_main_pushes(pages):
    deploy = pages["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    condition = deploy["if"]
    assert "github.event_name == 'push'" in condition
    assert "refs/heads/main" in condition


def test_pages_deploy_targets_the_github_pages_environment(pages):
    deploy = pages["jobs"]["deploy"]
    assert deploy["environment"]["name"] == "github-pages"
    assert uses_action(deploy, "actions/deploy-pages@")


# --- CI ---------------------------------------------------------------------


def test_ci_runs_on_pull_requests_and_main(ci):
    triggers = ci["on"]
    assert "pull_request" in triggers
    assert triggers["push"]["branches"] == ["main"]


def test_ci_is_read_only(ci):
    assert ci["permissions"] == {"contents": "read"}


def test_ci_builds_the_site(ci):
    site = ci["jobs"]["site"]
    assert uses_action(site, "ruby/setup-ruby@")
    assert "bundle exec jekyll build" in run_commands(site)
    assert uses_action(site, "actions/setup-python@v7")
    setup = next(
        s for s in steps_of(site) if str(s.get("uses", "")).startswith("actions/setup-python@v7")
    )
    assert setup["with"]["python-version"] == "3.11"
    assert "tools/site-checks/check_blog_discovery.py" in run_commands(site)
    assert run_commands(site).index("bundle exec jekyll build") < run_commands(site).index(
        "check_blog_discovery.py"
    )


def test_ci_smoke_checks_the_generated_output(ci):
    commands = run_commands(ci["jobs"]["site"])
    for expected in (
        "_site/sky/index.html",
        "_site/feed.xml",
        "_site/feed/apod.xml",
        "_site/blog/tag/machine-learning/index.html",
    ):
        assert expected in commands


def test_ci_installs_cosmic_daily_and_runs_pytest(ci):
    tools = ci["jobs"]["cosmic-daily"]
    assert uses_action(tools, "actions/setup-python@")
    setup = next(
        s for s in steps_of(tools) if str(s.get("uses", "")).startswith("actions/setup-python@")
    )
    assert setup["with"]["cache"] == "pip"
    commands = run_commands(tools)
    assert "pip install -e .[dev]" in commands
    assert "pytest" in commands


# --- IndexNow ---------------------------------------------------------------


def test_indexnow_waits_for_the_deployment_instead_of_sleeping(indexnow):
    raw = (WORKFLOWS / "indexnow.yml").read_text(encoding="utf-8")
    assert "sleep" not in raw


def test_indexnow_is_chained_to_a_successful_pages_deployment(indexnow):
    triggers = indexnow["on"]
    assert triggers["workflow_run"]["workflows"] == [PAGES_WORKFLOW_NAME]
    assert triggers["workflow_run"]["types"] == ["completed"]
    # A second trigger on push would submit the same URLs twice per publish.
    assert "push" not in triggers


def test_indexnow_skips_failed_or_non_main_deployments(indexnow):
    condition = indexnow["jobs"]["indexnow"]["if"]
    assert "github.event.workflow_run.conclusion == 'success'" in condition
    assert "github.event.workflow_run.head_branch == 'main'" in condition


def test_indexnow_requests_no_token_permissions(indexnow):
    assert indexnow["permissions"] == {}


# --- Cosmic Daily -----------------------------------------------------------


@pytest.fixture(scope="module")
def cosmic() -> dict:
    return load(WORKFLOWS / "cosmic-daily.yml")


def test_cosmic_daily_triggers_are_scheduled_and_manual_only(cosmic):
    triggers = cosmic["on"]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] == [{"cron": "0 12 * * *"}]
    # No pull_request / issue_comment trigger: this workflow holds write
    # permissions and must never run from a fork or a comment.
    assert set(triggers["workflow_dispatch"]["inputs"]) == {"date", "publish"}


def test_cosmic_daily_grants_no_default_permissions(cosmic):
    assert cosmic["permissions"] == {}


def test_cosmic_daily_generation_job_can_only_commit_and_open_prs(cosmic):
    assert cosmic["jobs"]["cosmic-daily"]["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
    }


def test_failure_reporting_is_a_separate_job_limited_to_issues(cosmic):
    report = cosmic["jobs"]["report-failure"]
    assert report["permissions"] == {"issues": "write"}
    assert report["needs"] == "cosmic-daily"
    assert report["if"] == "failure()"


def test_failure_report_receives_the_log_tail_from_the_generation_job(cosmic):
    outputs = cosmic["jobs"]["cosmic-daily"]["outputs"]
    assert {"target-date", "log-tail", "pull-request"} <= set(outputs)
    report = yaml.safe_dump(cosmic["jobs"]["report-failure"])
    # The tail is passed through the job output (as an env var, so untrusted
    # log content never reaches the shell as an expression) and decoded there.
    assert "needs.cosmic-daily.outputs.log-tail" in report
    assert "base64" in run_commands(cosmic["jobs"]["report-failure"])


def test_failure_report_opens_or_comments_a_single_issue(cosmic):
    commands = run_commands(cosmic["jobs"]["report-failure"])
    assert "gh issue list" in commands
    assert "gh issue comment" in commands
    assert "gh issue create" in commands


def test_cosmic_daily_actions_stay_pinned(cosmic):
    job = cosmic["jobs"]["cosmic-daily"]
    used = {str(step["uses"]) for step in steps_of(job) if step.get("uses")}
    assert used == {
        "actions/checkout@v7",
        "actions/setup-python@v7",
        "peter-evans/create-pull-request@v8",
    }


def test_cosmic_daily_still_validates_before_merging(cosmic):
    commands = run_commands(cosmic["jobs"]["cosmic-daily"])
    assert "python -m cosmic_daily check" in commands
    assert "gh pr merge" in commands


# --- Repo data refresh ------------------------------------------------------


@pytest.fixture(scope="module")
def repo_data() -> dict:
    return load(WORKFLOWS / "repo-data.yml")


def test_repo_data_refresh_is_scheduled_and_manual(repo_data):
    triggers = repo_data["on"]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] and triggers["schedule"][0]["cron"]


def test_repo_data_refresh_grants_no_default_permissions(repo_data):
    assert repo_data["permissions"] == {}


def test_repo_data_refresh_job_can_only_commit_and_open_prs(repo_data):
    assert repo_data["jobs"]["refresh"]["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
    }


def test_repo_data_refresh_runs_the_generator(repo_data):
    commands = run_commands(repo_data["jobs"]["refresh"])
    assert "tools/repo_cards/generate_repo_data.py" in commands


def test_repo_data_refresh_opens_a_pull_request_instead_of_pushing_to_main(repo_data):
    job = repo_data["jobs"]["refresh"]
    assert uses_action(job, "peter-evans/create-pull-request@v8")
    commands = run_commands(job)
    assert "git push" not in commands


def test_repo_data_refresh_uses_the_default_token_only(repo_data):
    raw = (WORKFLOWS / "repo-data.yml").read_text(encoding="utf-8")
    assert "secrets.GITHUB_TOKEN" in raw
    assert raw.count("secrets.") == raw.count("secrets.GITHUB_TOKEN")


# --- Dependabot -------------------------------------------------------------


@pytest.fixture(scope="module")
def dependabot() -> dict:
    return load(REPO_ROOT / ".github" / "dependabot.yml")


def test_dependabot_covers_actions_bundler_and_pip(dependabot):
    updates = {(u["package-ecosystem"], u["directory"]) for u in dependabot["updates"]}
    assert ("github-actions", "/") in updates
    assert ("bundler", "/") in updates
    assert ("pip", "/tools/cosmic-daily") in updates


def test_dependabot_checks_weekly(dependabot):
    assert all(u["schedule"]["interval"] == "weekly" for u in dependabot["updates"])


def test_dependabot_groups_updates_into_single_prs(dependabot):
    assert all(u.get("groups") for u in dependabot["updates"])
