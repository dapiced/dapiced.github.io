# `/now/` Page Freshness Design (E3)

- **Status:** approved for autonomous implementation
- **Date:** 2026-10-01
- **Scope:** refresh the existing `/now/` page with durable public facts and add a single low-noise GitHub reminder when the page has not been reviewed for 90 days. This is not a visual redesign and does not include E4.

## 1. Objective

Keep `/now/` useful without turning it into a stream of short-lived status updates. The page will describe four durable areas already supported by the public site, while a scheduled GitHub Actions workflow will create one stable issue when the page's explicit `updated` date becomes stale.

The implementation will:

1. set the page's `updated` front-matter date to `2026-10-01`;
2. retain the current layout, tone, links, location, headings, responsive behavior, SEO, analytics, and external-link safety;
3. replace the brittle quantified migration statement with a durable platform/IaC/CI/CD theme;
4. validate the exact `updated: YYYY-MM-DD` front-matter field with a standard-library Python checker;
5. run a monthly, read-only freshness check and create one issue only when no matching open issue exists.

## 2. Audience and success criteria

The primary reader wants a quick, credible answer to what Dominic is focused on now. The page succeeds when its four themes remain accurate beyond a single project milestone, its claims are traceable to existing public site content, and stale content produces one actionable reminder without noisy monthly comments or automated edits.

The maintenance workflow succeeds when:

- malformed, missing, or future page dates fail clearly;
- a date exactly at the 90-day threshold is stale;
- normal pull-request CI checks date validity and generated output but does not fail solely because the date is older than 90 days;
- a scheduled run creates `Refresh /now/ page` only when no matching open issue exists;
- an existing matching open issue causes no comment, label, close, edit, or duplicate issue;
- the notification job has only `issues: write` and does not check out the repository.

## 3. Content boundaries

The page will contain these four concise themes:

1. **Studying:** finishing the University Certificate in Data Science at Université TÉLUQ.
2. **Competing:** practicing and competing on Kaggle.
3. **Building:** building and operating Azure and Databricks platforms for AI workloads with infrastructure as code and CI/CD.
4. **Learning and sharing:** deepening MLOps/DataOps practice and writing practical lessons on the blog.

These statements are limited to existing public site content. They must not claim that the certificate is complete, name an employer, add a new credential, disclose private milestones, invent project counts, or state that a specific migration remains active. The existing `~200 projects / 1,500 repositories` claim is removed.

## 4. Approaches considered

### 4.1 Recommended: source-date checker plus scheduled issue notification

Keep the date in the page front matter, parse it with a small standard-library Python CLI, and call that CLI from both pull-request CI and a monthly workflow. The scheduled workflow separates the read-only check from the issue-writing notification job.

**Advantages:** no new runtime dependency, one authoritative date, deterministic tests, clear least-privilege boundary, and no automated page edits or pull requests.

**Trade-off:** the workflow needs a small GitHub API script or CLI invocation to de-duplicate open issues. This is acceptable because issue creation is intentionally the only write operation.

### 4.2 GitHub issue form or repository dispatch service

Use a prebuilt issue form or an external scheduler to manage reminders.

**Trade-off:** adds configuration or a third-party service without improving the simple date-based decision. It also weakens the repository-local audit trail.

### 4.3 CI failure after 90 days

Make all pull requests fail if `/now/` is stale.

**Trade-off:** unrelated changes would be blocked by a maintenance reminder. The approved behavior keeps staleness non-blocking in CI and reserves reminders for the scheduled workflow.

The design selects approach 4.1.

## 5. Page structure and rendering

`now/index.html` will continue to use the default layout and its existing section/card structure. The front matter will retain the page title, description, keywords, and exact scalar field:

```yaml
updated: 2026-10-01
```

The visible date will continue to render from `page.updated`, so the source date and displayed date cannot drift. The four existing cards remain concise and use the current semantic `h1`/`h3` hierarchy. The current Montréal line, nownownow.com links, blog link, analytics, and safe external links remain unchanged unless a wording adjustment is required to remove the unsupported migration claim.

No new data file, client-side state, or page-specific layout is needed.

## 6. Freshness checker

Create `tools/site-checks/check_now_freshness.py` using only Python's standard library. Its responsibilities are deliberately small:

- read `now/index.html`;
- parse exactly one front-matter line matching `^updated:\s*(\d{4}-\d{2}-\d{2})\s*$`;
- reject missing, duplicate, malformed, and future dates;
- accept a configurable threshold in days, defaulting to `90`;
- accept an injectable `--today YYYY-MM-DD` for deterministic tests;
- calculate age in whole calendar days;
- report the date, age, threshold, and stale status in stable machine-readable output;
- return distinct non-zero exit codes for invalid input versus a valid stale page.

The CLI will provide a human-readable default suitable for Actions logs and a stable `--format json` mode for workflow outputs. Staleness is a valid result, not a parser error; the scheduled workflow must be able to continue and expose that result.

## 7. GitHub Actions workflow

Add `.github/workflows/now-freshness.yml` with:

- `workflow_dispatch`;
- a monthly cron at a reasonable UTC time, selected as `17 14 1 * *`;
- top-level `permissions: {}`;
- a read-only `check` job that checks out the repository, sets up Python, runs the checker with the default 90-day threshold, and exposes `updated`, `age`, and `stale` job outputs;
- a separate `notify` job that runs only when `check` reports stale, grants only `issues: write`, performs no checkout, and uses the GitHub CLI/API available on the runner to find open issues with the exact title `Refresh /now/ page`;
- issue creation only when no matching open issue exists.

The issue body will include the last update date, age, 90-day threshold, and the run URL. It will not add labels, comment on an existing issue, close issues, edit the page, open a PR, send email, use secrets, or call a third-party service. `GITHUB_TOKEN` is the repository-provided token used only in the notification job.

## 8. CI integration and generated output

Extend the existing source checks so CI always validates the front-matter date and future-date rule, but does not fail an unrelated pull request because the page is stale. After the existing Jekyll build, add a narrow generated-output check for `_site/now/index.html` that verifies the page exists, is non-empty, contains the rendered update date, and does not contain the removed quantified claim. This protects the actual published artifact without coupling the rest of the site to the reminder threshold.

## 9. Testing strategy

Implementation follows TDD.

Focused Python tests will cover:

- the four approved themes and updated date;
- removal of the quantified migration claim and active-migration wording;
- exact front-matter parsing, missing/duplicate/invalid/future dates;
- age arithmetic and the stale boundary at 90 days;
- injected today dates, threshold validation, JSON output, and exit codes;
- generated `/now/` output checks.

Workflow/source tests will cover:

- manual and monthly triggers;
- check/notification job separation;
- top-level and job-level least permissions;
- no checkout in the notification job;
- exact open-issue de-duplication and no commenting behavior;
- issue body fields and run URL.

The existing Python, Node, Jekyll, and static checks remain part of validation.

## 10. Documentation

Update `README.md` to identify `/now/` as a manually maintained page, document the `updated` field and 90-day threshold, explain that scheduled Actions creates one stable reminder issue, and point maintainers to `workflow_dispatch` for a manual check. The documentation will distinguish non-blocking CI validation from scheduled staleness notification.

## 11. Non-goals

- Redesigning `/now/` or changing the site's theme.
- Altering `/resume/`, the homepage, blog discovery, Cosmic Daily, analytics, manifest, or license.
- Auto-editing the page or opening an automated PR.
- Adding labels, comments, email notifications, secrets, or third-party services.
- Treating stale content as a pull-request failure.
- Claiming certificate completion, employer information, new credentials, private milestones, project counts, or an active named migration.

## 12. Acceptance criteria

E3 is complete when:

- `now/index.html` has `updated: 2026-10-01` and exactly four approved durable themes;
- the old quantified migration claim and unsupported active-migration wording are absent;
- the page preserves current structure, links, Montréal, semantics, responsive behavior, SEO, analytics, and safe external-link attributes;
- the standard-library checker validates source dates, future dates, age math, threshold boundaries, injected today values, output, and exit codes;
- the monthly/manual workflow has the specified triggers, permissions, separated jobs, no checkout in notification, stable issue de-duplication, and no comments;
- CI validates date/output without failing solely for staleness;
- README documents ownership and maintenance behavior;
- focused tests, the full Python suite, Node tests, Ruby 3.4 Docker Jekyll build, generated-output checks, YAML parsing, and `git diff --check` pass;
- the branch has one non-draft open PR targeting `main` and has not been merged.
