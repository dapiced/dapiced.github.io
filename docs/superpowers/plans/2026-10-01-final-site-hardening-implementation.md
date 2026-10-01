# Final Site Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete E4 by hardening browser metadata, licensing, generated APOD safety, workflow contracts, accessibility structure, and published-output validation.

**Architecture:** Keep Jekyll's default layout as the shared metadata boundary, add a static manifest and root license, and isolate Cosmic Daily rights/content validation in deterministic Python functions used by both CLI and workflow checks. Protect every behavior with focused source/workflow/generated-output tests, then run the complete site build and crawl before opening one non-draft PR.

**Tech Stack:** Jekyll 4.4, Ruby 3.4 Docker, Python 3.11/pytest, Node test runner, GitHub Actions YAML, GitHub CLI, static HTML/JSON/XML checks.

**Spec:** `docs/superpowers/specs/2026-10-01-final-site-hardening-design.md`

## Global Constraints

- Keep GoatCounter as the sole analytics/counter provider; add no second tracker, tag manager, cookie banner, or preconnect.
- Add exactly `theme-color="#04060f"`, dark `color-scheme`, and `/site.webmanifest` metadata without a service worker, offline cache, push, install prompt, or navigation change.
- Use only existing valid branded icons in the manifest; do not invent icons unless browser requirements prove an additional deterministic asset is necessary.
- MIT applies only to repository source code; authored articles, portfolio text, personal media, and branding remain copyright Dominic D'Apice/all rights reserved unless stated otherwise; third-party assets retain their licenses.
- Cosmic Daily must fail closed for incomplete/third-party rights metadata and must never auto-merge manual-review or invalid content.
- The malformed `_apod/2026-10-01-nasa-science.md` entry and its generated image must not remain in source or generated output.
- Use the `Authorization: Bearer` scheme with a runtime secret value for GitHub API calls and never log token values.
- IndexNow may run after successful main deployment completion or intentional manual dispatch, never after a manual Pages build that did not deploy.
- Preserve existing CSS appearance, lazy loading, alt text, normal links, analytics, and site content except for the specified fixes.
- Every behavior change uses TDD: RED focused test, run, minimal GREEN implementation, run, surgical commit with the required Copilot trailer.

## Review Focus

- A rights record with `copyright: ""` or omitted metadata must not become publishable; pin this in `tools/cosmic-daily/tests/test_rights_policy.py`.
- A NASA/public-domain record must use the current accepted metadata shape, while an unknown category must route to manual review; pin both cases in the rights-policy tests.
- A malformed APOD can contain plausible substrings but still include a 121x102 image or APOD navigation boilerplate; pin the complete payload rejection in `tools/cosmic-daily/tests/test_cli.py` and validator tests.
- A manually dispatched Pages build can succeed without deployment; pin the IndexNow event/condition contract in `tools/cosmic-daily/tests/test_workflows.py`.
- A manifest link or heading fix can be present in source but absent from generated layouts; pin representative generated pages in `tests/test_generated_site.py` (or the existing generated-output contract module).

---

## File map and interfaces

### Shared site boundary

- Create: `site.webmanifest` — valid static manifest with `name`, `short_name`, `start_url`, `display`, `background_color`, `theme_color`, and valid existing icon references.
- Modify: `_layouts/default.html` — shared theme metadata and manifest link; preserve the one GoatCounter script.
- Modify: `assets/css/style.css` — add `color-scheme: dark` at the root/site scope without changing palette tokens.
- Modify: `tests/test_generated_site.py` or the existing site contract tests — source and rendered metadata/manifest contracts.

### Content, license, and accessibility

- Create: `LICENSE` — scoped MIT notice and exclusions.
- Modify: `README.md` — license boundary, GoatCounter boundary, manifest note, repo-data source of truth, and remove completed migration instruction.
- Modify: `now/index.html`, `blog/index.html` — first card/topic level uses `h2`, with existing classes/styles preserved.
- Modify: `_posts/2026-07-02-a-star-for-my-father.md`, `_posts/2026-07-02-nothingness-has-no-address.md` — exact SVG intrinsic dimensions on the two currently missing editorial images.
- Modify: `tests/test_site_data.py` and/or focused content tests — heading and intrinsic-dimension contracts.

### Cosmic Daily

- Modify: `tools/cosmic-daily/cosmic_daily/rights_policy.py` — `evaluate_media_rights(media_type: str, copyright: str | None = None, rights_category: str | None = None) -> RightsDecision`.
- Modify: `tools/cosmic-daily/cosmic_daily/nasa_client.py` — preserve supported APOD metadata in `APODRecord` without silently inventing rights.
- Create or modify: `tools/cosmic-daily/cosmic_daily/content_validator.py` — `validate_generated_article(content: str, image_path: Path) -> ValidationResult`, validating complete front matter, dimensions, source fields, and boilerplate.
- Modify: `tools/cosmic-daily/cosmic_daily/cli.py` — manual-review result, validator invocation, explicit exit semantics, and no generated files on unsafe rights.
- Modify: `tools/cosmic-daily/tests/test_rights_policy.py`, `test_cli.py`, `test_article_generator.py`, and validator tests — RED/GREEN safety coverage.
- Modify: `.github/workflows/cosmic-daily.yml` — manual-review PR remains open and cannot reach merge; invalid validation remains a failure.
- Remove: `_apod/2026-10-01-nasa-science.md` and its exact generated APOD image path.

### Other automation

- Modify: `tools/repo_cards/generate_repo_data.py` and its tests — Bearer header and redacted-token assertions.
- Modify: `.github/workflows/indexnow.yml` and `tools/cosmic-daily/tests/test_workflows.py` — deployment-only workflow-run condition plus intentional dispatch.

### Final documentation/status

- Modify: `docs/superpowers/plans/2026-10-01-now-page-freshness-implementation.md` — only after validation, mark merged #90/#91 history accurately.
- Add no temporary, build, coverage, cache, or planning artifacts to the repository.

## Task 1: Browser metadata, manifest, and analytics boundary

- [ ] **Step 1: Write failing source/generated contracts** in `tests/test_generated_site.py` (or the existing site contract file): assert the default layout contains the exact theme-color, dark color-scheme, manifest link, and exactly one GoatCounter script; assert the manifest has required keys, valid JSON, root-relative icon URLs, no service-worker/install/offline fields, and only existing supported icon assets.
- [ ] **Step 2: Run the focused tests to verify RED.** Run `python -m pytest tests/test_generated_site.py -q`; expected failures identify missing metadata/manifest.
- [ ] **Step 3: Implement the minimal shared boundary.** Add `site.webmanifest`, the two meta tags and link in `_layouts/default.html`, and `color-scheme: dark` in `assets/css/style.css`; do not add preconnect or another analytics provider.
- [ ] **Step 4: Run focused tests to verify GREEN.** Run `python -m pytest tests/test_generated_site.py -q`; expected PASS.
- [ ] **Step 5: Commit.** `git add site.webmanifest _layouts/default.html assets/css/style.css tests/test_generated_site.py && git commit -m "feat: add native dark site metadata" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 2: License and maintainer documentation

- [ ] **Step 1: Write failing documentation contracts.** Add tests that require `LICENSE` to state MIT source-code scope and explicit exclusions, README to identify `_data/repos.json` as the rendered project-card source refreshed by workflow, README to describe GoatCounter as sole counter, and README to omit the completed one-time Pages migration instruction.
- [ ] **Step 2: Run the focused tests to verify RED.** Run `python -m pytest tests/test_documentation_contract.py -q`; expected failure because the root license and corrected wording are absent.
- [ ] **Step 3: Add the scoped license and README edits.** Keep the license human-readable and explicit about personal/third-party content; update only stale automation and ownership statements.
- [ ] **Step 4: Run focused tests to verify GREEN.** Run `python -m pytest tests/test_documentation_contract.py -q`.
- [ ] **Step 5: Commit.** `git add LICENSE README.md tests/test_documentation_contract.py && git commit -m "docs: define site ownership and analytics boundaries" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 3: Cosmic Daily rights policy

- [ ] **Step 1: Write failing rights tests.** Add cases for image + missing copyright, blank copyright, `NASA`/supported public-domain metadata, explicit third-party copyright, unknown category, and video. Assert `RightsDecision.status`, `allowed`, and a manual-review reason; update the misleading external-copyright test.
- [ ] **Step 2: Run RED.** Run `python -m pytest tools/cosmic-daily/tests/test_rights_policy.py -q`; expected failure because third-party and incomplete metadata currently allow.
- [ ] **Step 3: Implement `evaluate_media_rights(...) -> RightsDecision`.** Allow only still images with the current explicit NASA/public-domain metadata shape; return `manual_review` for third-party, missing, blank, or unknown rights metadata; retain `unsupported_media` for non-images.
- [ ] **Step 4: Run GREEN.** Run `python -m pytest tools/cosmic-daily/tests/test_rights_policy.py -q`.
- [ ] **Step 5: Commit.** `git add tools/cosmic-daily/cosmic_daily/rights_policy.py tools/cosmic-daily/tests/test_rights_policy.py && git commit -m "fix: fail closed on APOD image rights" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 4: Structured APOD validation and malformed regression

- [ ] **Step 1: Write failing validator/CLI tests.** Add a fixture equivalent to the malformed 2026-10-01 payload (generic title, 121x102 image, APOD navigation/migration/footer boilerplate) and assert `validate_generated_article` rejects it; add accepted complete front matter, positive dimensions above the minimum, required title/explanation/source fields, missing-image, duplicate-field, and boilerplate cases.
- [ ] **Step 2: Run RED.** Run `python -m pytest tools/cosmic-daily/tests/test_content_validator.py tools/cosmic-daily/tests/test_cli.py -q`; expected failures because validation is substring-based or absent.
- [ ] **Step 3: Implement `ValidationResult` and `validate_generated_article(content: str, image_path: Path) -> ValidationResult`.** Parse the first front-matter document, require exactly one complete set of fields, validate image dimensions against a conservative minimum and the referenced file, reject known APOD navigation/footer phrases and generic generated output, and return explicit errors.
- [ ] **Step 4: Integrate CLI generation/check.** Invoke rights validation before image/article writes where possible and structured validation before success output; manual review creates no generated article/image, while invalid content returns `EXIT_ERROR`.
- [ ] **Step 5: Remove the malformed tracked entry/image and run GREEN.** Run `python -m pytest tools/cosmic-daily/tests/test_content_validator.py tools/cosmic-daily/tests/test_cli.py tools/cosmic-daily/tests/test_article_generator.py -q`; expected PASS and no generated files from rejected fixtures.
- [ ] **Step 6: Commit.** `git add tools/cosmic-daily _apod tests && git rm _apod/2026-10-01-nasa-science.md <exact-image-path> && git commit -m "fix: reject malformed APOD output" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 5: Cosmic Daily workflow fail-closed behavior

- [ ] **Step 1: Write failing workflow/CLI integration contracts.** Assert the workflow distinguishes `manual_review` from `generated`, includes an explicit human-review PR summary, gates `gh pr merge` on validated generated output only, and never merges after validation failure or manual review.
- [ ] **Step 2: Run RED.** Run `python -m pytest tools/cosmic-daily/tests/test_workflows.py tools/cosmic-daily/tests/test_cli.py -q`; expected failure against the unconditional merge.
- [ ] **Step 3: Implement the smallest workflow gate.** Carry the CLI result through `GITHUB_OUTPUT`; create a PR for manual review with no merge step, preserve failure reporting, and keep permissions limited to `contents: write`/`pull-requests: write` for generation and `issues: write` for failure reporting.
- [ ] **Step 4: Run GREEN.** Run the focused workflow and Cosmic Daily tests.
- [ ] **Step 5: Commit.** `git add .github/workflows/cosmic-daily.yml tools/cosmic-daily/tests/test_workflows.py tools/cosmic-daily/tests/test_cli.py && git commit -m "ci: keep APOD manual review out of auto-merge" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 6: Repo-card authorization and IndexNow trigger contracts

- [ ] **Step 1: Write failing tests.** Assert repo-card requests use the `Authorization: Bearer` scheme and never the literal placeholder or token in logs; assert IndexNow has `workflow_run` completion plus `workflow_dispatch`, and its condition permits manual dispatch or successful main deployment completion only.
- [ ] **Step 2: Run RED.** Run `python -m pytest tools/repo_cards/tests -q tools/cosmic-daily/tests/test_workflows.py -q`; expected failures for the placeholder header and permissive manual workflow-run condition.
- [ ] **Step 3: Implement both fixes.** Change only the request header construction and the IndexNow event/condition; keep `permissions: {}` and avoid any deployment-less manual Pages path.
- [ ] **Step 4: Run GREEN.** Re-run the focused tests and `git diff --check`.
- [ ] **Step 5: Commit.** `git add tools/repo_cards .github/workflows/indexnow.yml tools/cosmic-daily/tests/test_workflows.py && git commit -m "fix: harden refresh and indexing triggers" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 7: Heading order and editorial image dimensions

- [ ] **Step 1: Write failing source contracts.** Assert `/now/` has one `h1` followed by four `h2` card headings with unchanged card classes, `/blog/` topic headings use `h2`, and the two named post images have width/height matching their SVG `viewBox` dimensions plus existing lazy/alt attributes.
- [ ] **Step 2: Run RED.** Run `python -m pytest tests/test_now_page.py tests/test_site_data.py tests/test_editorial_images.py -q`; expected failures for heading levels and missing dimensions.
- [ ] **Step 3: Implement semantic-only edits.** Change heading elements without changing CSS classes or copy; read exact `viewBox` values from `assets/img/etoile-vincenzo.svg` and `assets/img/nothingness-has-no-address.svg` and add those intrinsic dimensions to the corresponding `<img>` tags.
- [ ] **Step 4: Run GREEN.** Re-run focused source tests and inspect the two SVG `viewBox`/HTML pairs.
- [ ] **Step 5: Commit.** `git add now/index.html blog/index.html _posts/2026-07-02-a-star-for-my-father.md _posts/2026-07-02-nothingness-has-no-address.md tests && git commit -m "fix: restore heading order and image dimensions" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 8: E3 status and full generated-output contracts

- [ ] **Step 1: Write failing generated-output/site checks.** Extend the generated checker to require manifest/theme metadata on representative default-layout pages, reject the malformed APOD route/image, verify feeds/sitemap/redirects, `/now/`, `/resume/`, blog search/tags/TOC/related posts, and homepage repository-card counts; add a tracked-tree artifact/secret contract.
- [ ] **Step 2: Run RED against the pre-build or intentionally incomplete fixture.** Run the focused generated-output suite; expected failures identify missing checks.
- [ ] **Step 3: Implement only the reusable checks and update E3 documentation.** Keep generated-output checks deterministic and non-networked; mark E3 merged PR #90 and follow-up #91 accurately without rewriting history.
- [ ] **Step 4: Run GREEN.** Run `python -m pytest tests -q` for the focused site tests plus all workflow/YAML contracts.
- [ ] **Step 5: Commit.** `git add tests docs/superpowers/plans/2026-10-01-now-page-freshness-implementation.md && git commit -m "test: cover final generated site contracts" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"`.

## Task 9: Whole-site validation and publication

- [ ] **Step 1: Run full Python and Node suites.** Run `python -m pytest -q`, the separate Cosmic Daily suite from `tools/cosmic-daily`, and the repository Node tests; clean `_site` first so duplicate collection cannot mask failures. Expected: all pass.
- [ ] **Step 2: Build with Ruby 3.4 Docker.** Run the repository's Docker build command and every generated-output checker; expected successful Jekyll output with no malformed APOD route.
- [ ] **Step 3: Crawl and inspect.** Crawl all generated internal links/assets and inspect feed, APOD feed, sitemap, redirects, `/now/`, `/resume/`, blog search/tags/TOC/related posts, and homepage data counts. Expected: no broken internal references or missing assets.
- [ ] **Step 4: Run final hygiene checks.** Run `git diff --check`, tracked-tree artifact/secret scans, manifest JSON/schema/content-type checks, and representative mobile Lighthouse checks when available. Record non-blocking Lighthouse limitations explicitly.
- [ ] **Step 5: Request fresh independent whole-branch review.** Review all findings; fix Critical/Important findings test-first, assess Minor findings explicitly, and rerun affected tests plus the full validation as needed.
- [ ] **Step 6: Commit final documentation/checklist state and verify clean tree.** `git status --short` must be empty after the final commit; every commit includes the Copilot trailer.
- [ ] **Step 7: Push and open exactly one non-draft PR to `main`.** Use authenticated `gh` CLI, wait for checks, do not merge, and record the PR URL, final SHA, commit list, test/build/crawl/Lighthouse/artifact results, rights semantics, workflow permissions, license scope, and review dispositions.

## Plan self-review

- **Spec coverage:** metadata/manifest/analytics are Task 1; license/docs are Task 2; rights and malformed content are Tasks 3–5; repo-card/IndexNow are Task 6; accessibility/images are Task 7; generated output/E3 status are Task 8; full validation and PR constraints are Task 9.
- **Step scan:** each task has explicit RED, run, GREEN implementation, run, and commit boundaries; signatures are defined in the file map; no task relies on vague or unspecified behavior.
- **Type consistency:** `RightsDecision` is reused by policy, CLI, and workflow output; `ValidationResult` is consumed by CLI and tests; manifest and generated-output contracts share root-relative asset expectations.
- **Review focus:** all five failure modes have owning tests named in the Review Focus and repeated in their task's RED step.
- **Proportion:** the plan is a compact execution map rather than a code transcript; implementation bodies remain with the executor.
