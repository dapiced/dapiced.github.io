# Final Site Hardening Design (E4)

- **Status:** approved for autonomous implementation
- **Date:** 2026-10-01
- **Base:** `main` at `c92e05e`, including merged PRs #90 and #91
- **Scope:** final roadmap hardening only; no redesign, new analytics provider, service worker, offline cache, push, install prompt, or unrelated refactoring

## 1. Objective

Finish E4 by making the published site safer to consume, safer to generate, and
clearer about ownership. The implementation keeps the existing Jekyll layouts,
dark visual palette, GoatCounter integration, and normal browser navigation
while adding native browser metadata, a minimal manifest, explicit licensing,
fail-closed APOD publication rules, stronger generated-content validation, and
the remaining review fixes from the roadmap audit.

Success means the repository has one authoritative hardening contract, CI and
workflow tests protect every changed behavior, invalid generated content cannot
auto-merge, and the built site contains no malformed APOD entry or stale
metadata.

## 2. Decisions and boundaries

### 2.1 Browser metadata and manifest

The default layout remains the single source for shared `<head>` metadata.
It will add:

- `<meta name="theme-color" content="#04060f">`;
- `<meta name="color-scheme" content="dark">`;
- `<link rel="manifest" href="/site.webmanifest">`.

The stylesheet will declare the matching native preference with
`color-scheme: dark`. The manifest is a small static JSON file with the site
name, short name, start URL, display mode, dark background/theme colors, and
only icons that already exist and have a valid browser-supported size/type.
No service worker or install-specific behavior will be introduced. The
manifest must not change ordinary navigation or imply offline support.

### 2.2 Analytics and privacy

GoatCounter remains the sole analytics/counter provider. No second analytics
script, tag manager, cookie banner, preconnect, or tracking endpoint will be
added. README documentation will state that the site uses GoatCounter for
lightweight page counters and that the repository does not add behavioral
profiling or advertising tracking. This is an operational description, not a
legal privacy guarantee.

### 2.3 License scope

Add a root `LICENSE` containing an MIT license for repository source code only.
The file will explicitly exclude authored articles, portfolio text, personal
media, and branding, which remain copyright Dominic D'Apice/all rights
reserved unless a file states otherwise. Third-party assets retain their
original licenses. README will explain the split scope and avoid implying that
the whole repository is MIT-licensed.

### 2.4 Cosmic Daily rights and validation

`evaluate_media_rights` becomes a deterministic metadata gate:

- non-image media remains unsupported and skipped;
- blank or missing copyright is not treated as legal clearance;
- an explicit NASA/public-domain category supported by the current APOD
  contract may be allowed;
- third-party copyright is a manual-review result and is never auto-published;
- any unknown or incomplete rights metadata fails closed.

The CLI will emit a distinct manual-review result, write no article or image
for it, and return a successful workflow outcome only when the workflow can
stop without auto-merging. The workflow must create or leave an explicit,
validated PR open for manual-review content, while validation failures and
malformed content prevent the merge. No code will claim legal certainty from
metadata alone.

Structured APOD validation will parse complete front matter and required
content fields instead of loose substring checks. It will require sensible
positive image dimensions above a conservative minimum, reject generic or
malformed source output, reject known APOD navigation/footer boilerplate, and
verify the referenced image. The exact malformed 2026-10-01 payload is a
regression fixture. The malformed tracked `_apod` entry and its image will be
removed. Failure paths are explicit and fail closed; the workflow never
merges a PR when validation or rights review is incomplete.

### 2.5 Remaining review fixes

The hardening pass also includes:

- use `Authorization: Bearer {token}` in repo-card refreshes without logging
  the token;
- allow IndexNow on successful deployment completion and intentional manual
  dispatch only, never on a successful manual Pages build without deployment;
- change the first topic/card-level headings on `/now/` and `/blog/` from
  `h3` to `h2` while preserving the existing CSS appearance;
- add exact intrinsic dimensions from the SVG `viewBox` to the two tracked
  editorial images missing `width`/`height`;
- remove the completed one-time Pages migration instruction and correct the
  README description of `_data/repos.json` refreshes;
- update E3 status/checklists only to reflect the actual merged PR history.

## 3. File and interface map

### Shared site and content

- Modify `_layouts/default.html`: shared theme metadata, manifest link, and
  unchanged GoatCounter-only script.
- Modify `assets/css/style.css`: dark native `color-scheme`.
- Add `site.webmanifest`: static manifest contract.
- Modify `now/index.html` and `blog/index.html`: semantic heading levels only.
- Modify the two specified `_posts/2026-07-02-*.md` files: SVG-derived
  intrinsic dimensions.
- Add/remove only the malformed APOD fixture and its generated image.

### Automation and validation

- Modify `tools/cosmic-daily/cosmic_daily/rights_policy.py` and `cli.py`:
  rights decisions and manual-review output.
- Modify `tools/cosmic-daily/cosmic_daily/article_generator.py` or a focused
  validator module: complete front matter/content validation.
- Modify `tools/cosmic-daily/tests/*`: rights, malformed payload, CLI, and
  workflow safety contracts.
- Modify `.github/workflows/cosmic-daily.yml`: manual-review PRs cannot
  auto-merge; permissions remain least-privilege.
- Modify `tools/repo_cards/generate_repo_data.py` and its tests.
- Modify `.github/workflows/indexnow.yml` and workflow contract tests.
- Add/update site contract tests for metadata, manifest, headings, dimensions,
  license scope, generated output, links, and artifact scans.

### Documentation and licensing

- Add root `LICENSE`.
- Modify `README.md`.
- Modify the E3 implementation plan status/checklist only after validation.
- Add this spec and the implementation plan required by the process.

## 4. Error handling and workflow semantics

Validation errors must produce non-zero commands, clear messages, and no
success-shaped fallback. Rights manual review is a safe, explicit terminal
state for a generated candidate: the workflow may retain a PR with a summary
and request human review, but it must not run `gh pr merge`. A malformed
article, missing image, invalid dimensions, boilerplate, or incomplete
front matter fails validation and blocks merge. Existing failure reporting
continues to use the repository's issue path without adding permissions.

IndexNow remains permissionless and receives URLs only after a successful
deployment completion event, plus an intentional `workflow_dispatch`; a
manual Pages build that only uploads an artifact cannot trigger it.

## 5. Testing and verification

Implementation is TDD. Each behavior change gets a focused RED test, the
smallest implementation, and a GREEN run before its surgical commit.

Required verification includes:

1. focused Python, Node, workflow-YAML, and generated-output contracts;
2. rights cases for missing/blank copyright, supported NASA/public-domain
   metadata, third-party copyright/manual review, video, and malformed APOD;
3. CLI/workflow checks proving manual review and validation failures cannot
   auto-merge;
4. manifest JSON/schema, linked asset, content-type, and generated-layout
   checks;
5. full `python -m pytest -q`, the separate Cosmic Daily suite, Node tests,
   all workflow contract tests, and a clean Ruby 3.4 Docker Jekyll build;
6. generated internal-link and asset crawl covering feeds, APOD feed,
   sitemap, redirects, `/now/`, `/resume/`, blog search/tags/TOC/related
   posts, and homepage data counts;
7. `git diff --check`, tracked-tree artifact/secret scans, and representative
   mobile Lighthouse checks when tooling permits.

The final branch receives a fresh independent whole-branch review. Critical
and Important findings are fixed test-first; Minor findings are either fixed
or documented with a concrete reasoned rejection. The E4 plan is checked off
only after this validation.

## 6. Self-review

- **Placeholders:** none; thresholds, paths, statuses, and workflow outcomes
  are explicit.
- **Contradictions:** “manual review is successful” is intentionally distinct
  from “validated and mergeable”; only the latter can reach auto-merge.
- **Scope:** all changes serve E4 or a confirmed review finding; no redesign,
  service worker, new analytics, or unrelated dependency is included.
- **Ambiguity resolved:** existing icons are reused only when their actual
  dimensions satisfy manifest requirements; otherwise no speculative icon is
  generated. NASA/public-domain allowance is based on the current metadata
  contract, not a legal conclusion.
- **Operational boundary:** the manifest is descriptive browser metadata, not
  a PWA feature, and GoatCounter is the only counter provider.
