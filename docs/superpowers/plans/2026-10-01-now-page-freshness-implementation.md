# `/now/` Page Freshness Implementation Plan

**Status:** implementation completed and validated; PR publication pending.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh `/now/` with four durable public themes and add a non-blocking 90-day freshness reminder that creates one stable GitHub issue.

**Architecture:** Keep the existing Jekyll page and visual structure, with the exact `updated` front-matter date as the source of truth. Add a standard-library Python CLI for parsing/date math and a monthly GitHub Actions workflow with a read-only check job separated from a least-privilege issue notification job.

**Tech Stack:** Jekyll 4.4, Liquid, HTML, Python 3.11 standard library, pytest, Node test runner, GitHub Actions, GitHub CLI/API, Ruby 3.4.

**Spec:** `docs/superpowers/specs/2026-10-01-now-page-freshness-design.md`

## Global Constraints

- Keep the existing `/now/` structure, tone, SEO, analytics, responsive behavior, semantic headings, Montréal line, nownownow.com links, and safe external-link attributes.
- Use exactly four durable themes: finishing the University Certificate in Data Science; practicing/competing on Kaggle; building/operating Azure and Databricks platforms for AI workloads with IaC/CI/CD; deepening MLOps/DataOps and writing practical lessons on the blog.
- Do not claim certificate completion, employers, new credentials, private milestones, project counts, or a specific active migration.
- Remove the `~200 projects / 1,500 repositories` migration claim.
- The freshness checker uses only the Python standard library, defaults to 90 days, accepts `--today`, rejects missing/duplicate/invalid/future dates, and distinguishes invalid input from valid staleness.
- CI validates date validity and generated `/now/` output but never fails solely because the page is older than 90 days.
- The workflow has `workflow_dispatch`, cron `17 14 1 * *`, top-level `permissions: {}`, no checkout in the notification job, and only `issues: write` for that job.
- The notification title is exactly `Refresh /now/ page`; an existing matching open issue causes no duplicate and no comment.
- Do not alter `/resume/`, homepage, blog discovery, Cosmic Daily, analytics, theme, manifest, or license.

## Review Focus

- A date exactly 90 calendar days old is stale, while a date 89 days old is fresh; test both boundaries in the checker task.
- A page with two `updated` lines must fail rather than silently selecting one; test duplicate fields in the checker task.
- A stale result must be a valid checker result so scheduled notification can run, while malformed/future input must fail; test exit codes and JSON in the checker task.
- The notification job must not inherit checkout or contents permissions; test workflow structure and permissions in the workflow-contract task.
- Existing open issue matching must suppress both duplicate creation and comments; test the exact shell/API de-duplication contract in the workflow-contract task.

---

### Task 1: Define the `/now/` source contract

**Files:**
- Create: `tests/test_now_page.py`
- Modify: `tests/test_site_data.py` only if a shared CI contract assertion is needed

**Interfaces:**
- Consumes: `now/index.html`, existing public links and wording conventions.
- Produces: focused source assertions for the exact date, four themes, removed claims, semantic structure, and safe links.

- [x] **Step 1: Write failing page-contract tests**

Add tests that read `now/index.html` and assert:

```python
assert re.search(r"^updated:\s*2026-10-01\s*$", template, re.MULTILINE)
assert template.count('class="beyond-card reveal"') == 4
assert "University Certificate in Data Science" in template
assert "Kaggle" in template
assert "Azure" in template and "Databricks" in template
assert "MLOps / DataOps" in template and 'href="/blog/"' in template
assert "~200" not in template
assert "1,500" not in template
assert "Azure DevOps Pipelines to GitHub Actions" not in template
assert "Montréal, Canada" in template
assert "https://nownownow.com/about" in template
assert "https://nownownow.com/p/1Fe6" in template
```

Also assert one `h1`, four `h3` headings, `page.updated` rendering, `target="_blank"`/`rel="noopener"` for both nownownow links, and no claim that the certificate is complete.

- [x] **Step 2: Run the focused tests to verify the current page fails**

Run:

```powershell
python -m pytest tests/test_now_page.py -q
```

Expected: FAIL because the current date and migration card violate the new contract.

- [x] **Step 3: Commit the failing contract**

```powershell
git add tests/test_now_page.py
git commit -m "test: define now page freshness content contract" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Implement durable `/now/` content

**Files:**
- Modify: `now/index.html`

**Interfaces:**
- Consumes: Task 1 source contract and public content named in the spec.
- Produces: four concise cards titled `Studying`, `Competing`, `Building`, and `Learning and sharing`, with `updated: 2026-10-01`.

- [x] **Step 1: Update the page content**

Change only the front matter date/description/keywords and the four card headings/prose needed to express the approved themes. Keep the current section shell, inline styles, links, metadata rendering, and card classes. Replace the migration card instead of adding a fifth card.

- [x] **Step 2: Run the page-contract tests**

Run:

```powershell
python -m pytest tests/test_now_page.py -q
```

Expected: PASS.

- [x] **Step 3: Commit the page refresh**

```powershell
git add now/index.html
git commit -m "content: refresh now page themes" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Add the standard-library freshness checker

**Files:**
- Create: `tools/site-checks/check_now_freshness.py`
- Create: `tests/test_now_freshness.py`

**Interfaces:**
- Consumes: `now/index.html` or a caller-provided page path.
- Produces: importable `parse_updated_date(text: str) -> date`, `assess_freshness(updated: date, today: date, threshold_days: int = 90) -> FreshnessResult`, and CLI exit/output behavior.

- [x] **Step 1: Write failing parser/date tests**

Cover valid exact front matter, missing field, duplicate field, malformed date, future date, threshold `89/90/91` age boundaries, injected today date, and invalid negative threshold. Assert `FreshnessResult` exposes `updated`, `today`, `age_days`, `threshold_days`, and `stale`.

- [x] **Step 2: Write failing CLI tests**

Invoke `main()` or a subprocess against temporary pages and assert:

- fresh page returns exit code `0`;
- stale page returns exit code `2`;
- missing/invalid/future page returns exit code `1`;
- default output includes `updated=`, `age_days=`, `threshold_days=`, and `stale=`;
- `--format json` emits stable JSON keys and boolean `stale`;
- `--today` and `--threshold-days` are honored.

- [x] **Step 3: Run checker tests to verify failure**

Run:

```powershell
python -m pytest tests/test_now_freshness.py -q
```

Expected: FAIL because the checker module does not exist.

- [x] **Step 4: Implement the checker**

Define a small immutable result type, parse only front matter between the first two `---` delimiters, require exactly one line matching `^updated:\s*(\d{4}-\d{2}-\d{2})\s*$`, use `datetime.date.fromisoformat`, and calculate `(today - updated).days`. Keep stale as a result with exit code `2`; reserve exit code `1` for invalid arguments or page/date input.

- [x] **Step 5: Run checker tests to verify pass**

Run:

```powershell
python -m pytest tests/test_now_freshness.py -q
```

Expected: PASS.

- [x] **Step 6: Commit the checker and tests**

```powershell
git add tools/site-checks/check_now_freshness.py tests/test_now_freshness.py
git commit -m "feat: add now page freshness checker" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: Add workflow/source contracts and scheduled reminder

**Files:**
- Create: `tests/test_now_workflow.py`
- Create: `.github/workflows/now-freshness.yml`

**Interfaces:**
- Consumes: Task 3 CLI output and GitHub Actions `GITHUB_OUTPUT`, `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `GITHUB_SERVER_URL`, and `GITHUB_RUN_ID`.
- Produces: monthly/manual workflow with `check` outputs `updated`, `age`, `stale`, and a conditional `notify` job.

- [x] **Step 1: Write failing workflow contract tests**

Read the YAML as text/parsed YAML and assert:

- `workflow_dispatch` and cron `17 14 1 * *` are present;
- top-level permissions are `{}`;
- `check` has checkout, setup-python, and the checker command with default threshold;
- `check` exposes `updated`, `age`, and `stale` outputs;
- `notify` needs `check`, runs only when `needs.check.outputs.stale == 'true'`, has `permissions: {"issues": "write"}`, and has no checkout;
- exact issue title appears;
- body includes update date, age, threshold, and run URL;
- open-issue lookup is title-scoped and creation is guarded;
- no comment, label, close, edit, secret, or third-party service behavior appears.

- [x] **Step 2: Run workflow tests to verify failure**

Run:

```powershell
python -m pytest tests/test_now_workflow.py -q
```

Expected: FAIL because the workflow does not exist.

- [x] **Step 3: Implement the workflow**

Use a shell step in `check` to run the checker in JSON mode, write outputs to `$GITHUB_OUTPUT`, and allow exit code `2` without converting staleness into a failed job. Use a separate `notify` shell step with `gh issue list --state open --search 'in:title "Refresh /now/ page"'` and `gh issue create` only when the exact title is absent. The notification step must use the run URL constructed from `${{ github.server_url }}`, `${{ github.repository }}`, and `${{ github.run_id }}`.

- [x] **Step 4: Run workflow tests to verify pass**

Run:

```powershell
python -m pytest tests/test_now_workflow.py -q
```

Expected: PASS.

- [x] **Step 5: Commit the workflow**

```powershell
git add .github/workflows/now-freshness.yml tests/test_now_workflow.py
git commit -m "ci: add now page freshness reminder" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Validate generated `/now/` output and integrate CI

**Files:**
- Modify: `tools/site-checks/check_now_freshness.py` only if a reusable generated-output helper is appropriate
- Modify: `tests/test_now_freshness.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `_site/now/index.html` after Jekyll build and Task 3 checker.
- Produces: post-build protection that requires generated `/now/` output and rejects the removed claim without applying staleness as a CI failure.

- [x] **Step 1: Write failing generated-output tests**

Add a test that creates a temporary `_site/now/index.html` and asserts the generated-output helper accepts the current date/card structure, rejects missing/empty output, and rejects the removed quantified claim. Keep a stale date valid for this post-build check.

- [x] **Step 2: Implement the generated-output check and CI integration**

Add a narrow helper or explicit CI command after `bundle exec jekyll build`. Run the source checker separately before the build with an invocation that rejects malformed/future dates but tolerates stale exit code `2`; after the build, validate `_site/now/index.html` exists, is non-empty, contains `2026-10-01` rendered output, and has no removed claim. Add `_site/now/index.html` to the required output list.

- [x] **Step 3: Run focused and source checks**

Run:

```powershell
python -m pytest tests/test_now_page.py tests/test_now_freshness.py tests/test_now_workflow.py -q
python tools/site-checks/check_now_freshness.py now/index.html --today 2026-10-01
```

Expected: PASS with exit code `0` for the injected current date.

- [x] **Step 4: Commit CI protection**

```powershell
git add .github/workflows/ci.yml tools/site-checks/check_now_freshness.py tests/test_now_freshness.py
git commit -m "ci: validate generated now page output" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Document ownership and maintenance

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: completed `/now/` page, checker CLI, and workflow behavior.
- Produces: contributor documentation for manual ownership, the 90-day threshold, non-blocking CI, stable issue reminder, and `workflow_dispatch`.

- [x] **Step 1: Update README**

Document `now/index.html` in Structure and add a maintenance paragraph under Automation. State that the `updated` front-matter date is the source of truth, the default threshold is 90 days, CI checks validity/generated output without failing for age, and `.github/workflows/now-freshness.yml` runs monthly or manually and creates one `Refresh /now/ page` issue without comments or auto-edits.

- [x] **Step 2: Commit documentation**

```powershell
git add README.md
git commit -m "docs: document now page freshness ownership" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 7: Independent review, fixes, and complete validation

**Files:**
- Modify: files identified by review only
- Modify: `docs/superpowers/plans/2026-10-01-now-page-freshness-implementation.md`

**Interfaces:**
- Consumes: full `main...HEAD` diff, spec, plan, and passing focused tests.
- Produces: whole-branch review record, test-first fixes for Critical/Important findings, completed plan checkboxes, and fresh validation evidence.

- [x] **Step 1: Request independent whole-branch review**

Ask a fresh reviewer to inspect content boundaries, date parsing, exit semantics, workflow permissions, issue de-duplication, generated output, and regression risk. Require precise findings and ignore style-only preferences.

- [x] **Step 2: Reproduce accepted findings with failing tests**

For every accepted Critical/Important finding, add or tighten a focused test before changing implementation. Document reasoned rejections in the final handoff if any finding is intentionally not applied.

- [x] **Step 3: Implement minimal fixes and rerun targeted tests**

Change only the necessary files and rerun the affected focused tests until passing.

- [x] **Step 4: Run complete validation**

Run all of:

```powershell
python -m pytest tests/test_now_page.py tests/test_now_freshness.py tests/test_now_workflow.py -q
python -m pytest -q
node --test tools/site-checks/js/*.test.js
python tools/site-checks/check_now_freshness.py now/index.html --today 2026-10-01
python tools/site-checks/check_now_freshness.py now/index.html --today 2026-12-30; $LASTEXITCODE
docker run --rm -v "${PWD}:/site" -w /site ruby:3.4 bash -lc "bundle install --jobs 4 --retry 3 && bundle exec jekyll build"
python tools/site-checks/check_now_freshness.py _site/now/index.html --today 2026-10-01
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/now-freshness.yml').read_text())"
git diff --check
```

Expected: focused/full Python, Node, CLI fresh/stale boundary, Docker Jekyll build, generated-output, YAML parsing, and diff checks all pass. The future check is expected to return invalid-date exit `1`; the stale check is expected to return `2` where applicable.

- [x] **Step 5: Mark the plan complete**

Change every completed checkbox to `- [x]` and set the header status to `implementation completed and validated; PR open/non-merged` only after fresh validation succeeds.

- [x] **Step 6: Commit review fixes and completed plan**

```powershell
git add -u
git commit -m "docs: complete now page freshness implementation" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 8: Publish the non-draft pull request

**Files:**
- None beyond Git metadata and GitHub PR state.

**Interfaces:**
- Consumes: clean validated branch.
- Produces: one open, non-draft PR targeting `main`, with checks observed and no merge.

- [ ] **Step 1: Push the branch**

```powershell
git push -u origin dapiced-now-page-freshness
```

- [ ] **Step 2: Open one non-draft PR**

Use authenticated `gh pr create --base main --head dapiced-now-page-freshness` with a concise description of scope, validation, workflow schedule/permissions, and explicit non-goals. Do not merge.

- [ ] **Step 3: Wait for checks**

Run:

```powershell
gh pr checks --watch
```

If a branch-caused check fails, reproduce it locally, add a failing test first, fix it, rerun validation, push, and watch again.

- [ ] **Step 4: Confirm clean/open/non-merged state**

Run:

```powershell
git status --short --branch
git --no-pager log --oneline main..HEAD
gh pr view --json url,number,state,isDraft,baseRefName,headRefName,mergeCommit,statusCheckRollup
```

Expected: clean worktree, one open non-draft PR to `main`, no merge commit, and checks passing or explicitly reported if GitHub infrastructure is unavailable.

- [ ] **Step 5: Report to the coordinator**

Send the PR URL, final SHA, commit list, exact validation results, review findings/fixes or reasoned rejections, workflow schedule/permissions, and open/non-merged status to the coordinator session.
