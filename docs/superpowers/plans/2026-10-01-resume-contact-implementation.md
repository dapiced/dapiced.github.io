# Resume and Contact Page Implementation Plan

> **Status:** approved for autonomous execution; implementation pending.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a professional, responsive, print-friendly `/resume/` page that renders shared career and skill data and makes LinkedIn the clear public contact route.

**Architecture:** Add one Jekyll page using the existing default layout and direct Liquid loops over `_data/timeline.yml` and `_data/skills.yml`. Extend the existing CSS, JavaScript, Python validation, and CI paths narrowly so the new page inherits global SEO, analytics, navigation, accessibility, and visual conventions without a new layout or dependency.

**Tech Stack:** Jekyll 4.4, Liquid, HTML, CSS, vanilla JavaScript, Python 3.11, pytest, Node test runner, GitHub Actions, Ruby 3.4.

**Spec:** `docs/superpowers/specs/2026-10-01-resume-contact-design.md`

## Global Constraints

- LinkedIn (`https://www.linkedin.com/in/dapiced/`) is the only public contact channel; do not expose or infer an email address, phone number, form, or third-party service.
- `_data/timeline.yml` and `_data/skills.yml` remain the only sources for career and skill values.
- Reuse existing site copy for the professional summary, current role, public profiles, and Montréal location; do not invent claims.
- Keep the current default layout, visual language, responsive behavior, SEO metadata, analytics, and external-link safety.
- Add print-friendly HTML/CSS and progressive enhancement with `window.print()`; do not generate or commit a PDF.
- Retain the existing LinkedIn `Contact` navigation item and add the smallest coherent `Resume` link.
- E3 `/now/`, E4 finishing work, and unrelated redesign or refactoring remain outside scope.
- Add no runtime or test dependencies.

## Review Focus

- A generated resume with missing, reordered, or duplicated timeline/skill content must fail post-build validation.
- A no-JavaScript visitor must still see the complete resume and retain the browser's normal print capability.
- External public profile links must use HTTPS with `target="_blank"` and `rel="noopener"`; LinkedIn must remain the only contact CTA.
- Narrow screens must not rely on the desktop two-column experience layout or overflow action controls.
- Printed output must hide site chrome and controls while retaining readable experience, skills, location, and public-profile information.

---

### Task 1: Add failing source-contract tests

**Files:**
- Create: `tests/test_resume_page.py`
- Modify: `tests/test_site_data.py`

**Interfaces:**
- Consumes: `_data/navigation.yml`, `_data/timeline.yml`, `_data/skills.yml`, existing layout and asset paths.
- Produces: source-level requirements for the resume page, navigation item, print hook, accessibility structure, responsive styles, and non-duplication.

- [ ] **Step 1: Write the failing navigation contract assertion**

Update `test_site_data_files_match_required_schema()` to expect `{"label": "Resume", "href": "/resume/"}` immediately after `Timeline`, while retaining the existing LinkedIn Contact item and its `_blank` / `noopener` attributes.

- [ ] **Step 2: Write failing resume-template tests**

Create focused tests asserting:

```python
def test_resume_template_reuses_shared_timeline_and_skills():
    template = (ROOT / "resume" / "index.html").read_text(encoding="utf-8")
    assert "{% for item in site.data.timeline %}" in template
    assert "{% for group in site.data.skills %}" in template
    assert_no_shared_values_are_hard_coded(template)


def test_resume_template_has_accessible_contact_and_print_controls():
    template = (ROOT / "resume" / "index.html").read_text(encoding="utf-8")
    assert 'href="https://www.linkedin.com/in/dapiced/"' in template
    assert 'target="_blank"' in template
    assert 'rel="noopener"' in template
    assert 'data-print-resume' in template
    assert "<button" in template
```

Also assert one `h1`, section headings for experience and technical capabilities, Montréal copy, semantic lists, supporting profile links, and the absence of `mailto:`, `<form`, and duplicated timeline/skill values.

- [ ] **Step 3: Write failing asset-contract tests**

Add tests asserting `assets/css/style.css` contains scoped `.resume-*`, narrow-screen `@media`, and `@media print` rules that hide `.nav`, `.footer`, `#starfield`, and `.resume-actions`; assert `assets/js/main.js` finds `[data-print-resume]` and calls `window.print()`.

- [ ] **Step 4: Run the focused tests to verify failure**

Run:

```powershell
python -m pytest tests/test_resume_page.py tests/test_site_data.py -q
```

Expected: FAIL because `resume/index.html`, resume styles, print JavaScript, and the navigation item do not exist.

- [ ] **Step 5: Commit the failing tests**

```powershell
git add tests/test_resume_page.py tests/test_site_data.py
git commit -m "test: define resume page contract" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Implement the resume page and contact path

**Files:**
- Create: `resume/index.html`
- Modify: `_data/navigation.yml`
- Modify: `tools/site-checks/validate_site_data.py`
- Modify: `assets/css/style.css`
- Modify: `assets/js/main.js`

**Interfaces:**
- Consumes: `site.data.timeline`, `site.data.skills`, default layout front matter, existing `.btn` and `.tag` styles.
- Produces: `/resume/`, `[data-print-resume]`, `.resume-page`, `.resume-experience-list`, `.resume-skill-groups`, and an internal Resume navigation item.

- [ ] **Step 1: Add the navigation item and update its approved contract**

Insert `Resume` with `/resume/` immediately after `Timeline` in `_data/navigation.yml`, then make the same ordered change in `APPROVED_SITE_DATA["navigation"]`.

- [ ] **Step 2: Create the semantic Jekyll page**

Create `resume/index.html` with:

- `layout: default`;
- page-specific title, description, and keywords;
- one `h1` for Dominic D'Apice;
- current role and `Montréal, Canada`;
- a concise summary grounded in the homepage About copy;
- a `Contact on LinkedIn` external `.btn.btn-primary` link;
- a `<button type="button" class="btn btn-ghost" data-print-resume>Print / save as PDF</button>`;
- `<ol class="resume-experience-list">` rendered from `site.data.timeline`;
- `<ul class="resume-skill-groups">` rendered from `site.data.skills`;
- a profiles/contact section with LinkedIn, GitHub, Kaggle, and Hugging Face external links.

Escape all shared data values through Liquid. Do not add career or skill values to front matter or static markup.

- [ ] **Step 3: Add scoped responsive and print styles**

Append a resume section to `assets/css/style.css` using existing variables and spacing. Use a two-column experience row above `700px`, one column below it, and wrapping action/profile lists.

Add `@media print` rules that switch to a white document, hide `.nav`, `.footer`, `#starfield`, `.skip-link`, and `.resume-actions`, remove panel decoration, preserve readable links, and apply `break-inside: avoid` to experience and skill items.

- [ ] **Step 4: Add progressive print enhancement**

In `assets/js/main.js`, query `[data-print-resume]`; when present, attach one click listener that calls `window.print()`. Keep all existing behavior unchanged when the control is absent.

- [ ] **Step 5: Run focused tests to verify pass**

Run:

```powershell
python -m pytest tests/test_resume_page.py tests/test_site_data.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit the implementation**

```powershell
git add resume/index.html _data/navigation.yml tools/site-checks/validate_site_data.py assets/css/style.css assets/js/main.js
git commit -m "feat: add printable resume page" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Validate generated resume output and CI

**Files:**
- Modify: `tools/site-checks/check_site_data_html.py`
- Modify: `tests/test_site_data.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `_site/resume/index.html`, validator-loaded shared data, generated default-layout HTML.
- Produces: `parse_rendered_resume(html: str) -> dict[str, Any]` and `validate_rendered_resume(root: Path | str) -> dict[str, int]`, called by the checker CLI after a build.

- [ ] **Step 1: Write failing parser and generated-output tests**

Add tests for:

```python
def test_html_parser_extracts_rendered_resume_contract():
    rendered = checker.parse_rendered_resume(RESUME_HTML_FIXTURE)
    assert rendered["timeline"] == EXPECTED_TIMELINE
    assert rendered["skills"] == EXPECTED_SKILLS
    assert rendered["headings"] == [
        "Dominic D'Apice",
        "Experience",
        "Technical capabilities",
        "Profiles and contact",
    ]
    assert rendered["contact_links"] == [EXPECTED_LINKEDIN_CONTACT]
    assert rendered["has_print_control"] is True
```

Define `EXPECTED_TIMELINE`, `EXPECTED_SKILLS`, and `EXPECTED_LINKEDIN_CONTACT` from the fixture content in the test module. Add temporary-directory validation tests proving missing resume output fails clearly, reordered shared data fails, unsafe external-link attributes fail, and a `mailto:` or form fails.

- [ ] **Step 2: Run parser tests to verify failure**

Run:

```powershell
python -m pytest tests/test_site_data.py -q
```

Expected: FAIL because the resume parser and validator do not exist.

- [ ] **Step 3: Implement generated resume parsing and validation**

Extend the existing HTML checker with a focused parser that captures:

- `.resume-experience-item` year, role, and description;
- `.resume-skill-group` domain and tags;
- resume `h1` / `h2` text;
- `.resume-contact-link` href, target, rel, and label;
- presence of `[data-print-resume]`, forms, and `mailto:` links.

Implement `validate_rendered_resume(root)` to require `_site/resume/index.html`, compare parsed timeline and skills with `load_site_data(root)`, require the expected heading sequence, require LinkedIn as the only contact link, and reject forms, `mailto:`, or unsafe external profile links. Update `main()` to validate both homepage and resume output and report both counts.

- [ ] **Step 4: Add the generated page to CI protection**

Add `_site/resume/index.html` to the existing generated-output file loop. Keep the existing checker invocation in place because its CLI now validates both pages.

- [ ] **Step 5: Run focused tests and a Jekyll build**

Run:

```powershell
python -m pytest tests/test_site_data.py tests/test_resume_page.py -q
bundle exec jekyll build
python tools/site-checks/check_site_data_html.py
```

Expected: all tests PASS; Jekyll builds; checker reports matching homepage and resume data.

- [ ] **Step 6: Commit generated-output protection**

```powershell
git add tools/site-checks/check_site_data_html.py tests/test_site_data.py .github/workflows/ci.yml
git commit -m "test: validate generated resume output" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: Document ownership and validate the implementation

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: completed page and validation commands.
- Produces: contributor guidance for `/resume/`, shared data ownership, print behavior, and LinkedIn-only contact.

- [ ] **Step 1: Update README structure documentation**

Add `resume/index.html` to the Structure section. Explain that the page renders timeline and skills directly from `_data/timeline.yml` and `_data/skills.yml`, uses LinkedIn as the public contact path, and offers browser printing rather than a committed PDF.

- [ ] **Step 2: Run focused validation**

Run:

```powershell
python -m pytest tests/test_resume_page.py tests/test_site_data.py -q
python tools/site-checks/validate_site_data.py
```

Expected: PASS.

- [ ] **Step 3: Run the full Python suite**

Run:

```powershell
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run relevant Node tests**

Run:

```powershell
node --test tools/site-checks/js/*.test.js
```

Expected: PASS.

- [ ] **Step 5: Run the Ruby 3.4 Jekyll build and output checker**

Run locally under Ruby 3.4, or with the repository mounted into a Ruby 3.4 container:

```powershell
bundle exec jekyll build
python tools/site-checks/check_site_data_html.py
```

Expected: build and generated-output validation PASS; `_site/resume/index.html` is non-empty.

- [ ] **Step 6: Run repository hygiene checks**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only intentional changes are present.

- [ ] **Step 7: Commit documentation**

```powershell
git add README.md
git commit -m "docs: document resume data ownership" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Independent review and fresh validation

**Files:**
- Modify as needed: files identified by review findings.
- Modify: `docs/superpowers/plans/2026-10-01-resume-contact-implementation.md`

**Interfaces:**
- Consumes: full branch diff from `main`, passing local validation, design spec, and implementation plan.
- Produces: reviewed implementation, test-first fixes for meaningful findings, and a completed plan record.

- [ ] **Step 1: Request an independent whole-branch code review**

Ask a fresh reviewer to inspect `main...HEAD` for correctness, accessibility, source-of-truth drift, print behavior, generated validation, and regression risk. Require precise file/line findings and ignore style-only preferences.

- [ ] **Step 2: Reproduce each meaningful finding with a failing test**

For each accepted finding, add or tighten a focused test and run it to confirm failure before changing product or validation code.

- [ ] **Step 3: Implement minimal fixes and rerun targeted tests**

Change only the files needed for accepted findings. Rerun the new tests until they pass.

- [ ] **Step 4: Run fresh complete validation**

Repeat:

```powershell
python -m pytest tests/test_resume_page.py tests/test_site_data.py -q
python -m pytest -q
node --test tools/site-checks/js/*.test.js
bundle exec jekyll build
python tools/site-checks/validate_site_data.py
python tools/site-checks/check_site_data_html.py
git diff --check
```

Expected: all commands PASS.

- [ ] **Step 5: Mark this plan completed**

Change every completed step to `- [x]` and set the top status to `implementation completed and validated; PR pending checks`. Do this only after Step 4 succeeds.

- [ ] **Step 6: Commit review fixes and completed plan**

```powershell
git add -u
git commit -m "docs: mark resume implementation complete" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Publish the pull request and wait for checks

**Files:**
- N/A; repository branch and GitHub metadata only.

**Interfaces:**
- Consumes: clean, validated branch with all commits.
- Produces: one non-draft pull request to `main`, published commit SHAs, and GitHub check evidence.

- [ ] **Step 1: Push the focused branch**

Run:

```powershell
git push -u origin dapiced-resume-contact-page
```

Expected: branch is published and tracks the remote.

- [ ] **Step 2: Open a non-draft PR with `gh`**

Run `gh pr create --base main --head dapiced-resume-contact-page` with a concise summary, test evidence, scope decisions, and no merge action.

Expected: one open, non-draft PR targeting `main`.

- [ ] **Step 3: Wait for GitHub checks**

Run:

```powershell
gh pr checks --watch
```

Expected: all required checks pass. If a check fails because of this branch, reproduce it locally, fix it test-first, commit, push, and watch again.

- [ ] **Step 4: Confirm clean worktree and collect handoff evidence**

Run:

```powershell
git status --short --branch
git --no-pager log --oneline main..HEAD
gh pr view --json url,number,state,isDraft,baseRefName,headRefName,statusCheckRollup
```

Expected: clean tracking branch, non-draft open PR to `main`, complete commit list, and passing checks.

- [ ] **Step 5: Report to the coordinator**

Send the PR URL, commit SHAs, exact validation commands and results, independent review findings/fixes, key scope decisions, and clean worktree status. Do not merge.
