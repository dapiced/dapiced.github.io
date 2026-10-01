# Site Data Migration Implementation Plan

> **Status:** Implementation completed and validated in [PR #87](https://github.com/dapiced/dapiced.github.io/pull/87); PR remains open and unmerged.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the approved homepage presentation data out of inline HTML into four YAML files and keep the current page output behavior identical.

**Architecture:** Keep the existing Jekyll layout structure intact and only swap static strings for Liquid loops backed by `_data/*.yml`. Add a small Python schema validator and targeted pytest coverage to guard the extracted YAML values and preserve existing HTML semantics.

**Tech Stack:** Jekyll 4.4, Liquid, YAML, Python 3.11, pytest.

**Spec:** `docs/superpowers/specs/2026-10-01-site-data-migration-design.md`

## Global Constraints

- Only the E2 homepage / navigation presentation data moves to `_data/navigation.yml`, `_data/skills.yml`, `_data/timeline.yml`, and `_data/resources.yml`.
- The hero, About section, animated roles, project cards, blog preview, and all E1/E3/E4 work remain outside scope.
- Preserve exact labels, ordering, CSS classes, accessibility attributes, and `target` / `rel` behaviors already in production.
- The static validation layer must catch missing or malformed data before the Jekyll build is trusted.
- The site must continue to build and render without changing the visual design or navigation semantics.

## Review Focus

- Navigation item order and external-link attributes must remain byte-for-byte aligned with the current markup.
- Skill groups must preserve domain names and tag order without reflowing the existing layout.
- Timeline entries must retain year, role, and description text while keeping the same DOM classes.
- Off-duty cards must keep title, message, icon, link target, and CTA copy exactly as they appear today.
- The validation layer must fail on schema drift and missing fields before a broken homepage reaches the build.

---

### Task 1: Add the E2 data files and assert the schema

**Files:**
- Create: `_data/navigation.yml`
- Create: `_data/skills.yml`
- Create: `_data/timeline.yml`
- Create: `_data/resources.yml`
- Create: `tools/site-checks/validate_site_data.py`
- Create: `tests/test_site_data.py`

**Interfaces:**
- Consumes: the exact output currently rendered in `_layouts/default.html` and `index.html`.
- Produces: a YAML-backed contract the Liquid templates and validation script both use.

- [x] **Step 1: Write the failing validation test**

```python
def test_site_data_files_match_required_schema():
    data = load_site_data()
    assert isinstance(data["navigation"], list)
    assert isinstance(data["skills"], list)
    assert isinstance(data["timeline"], list)
    assert isinstance(data["resources"], list)
    assert data["navigation"][0]["label"] == "About"
    assert data["skills"][0]["domain"] == "Cloud & Data"
    assert data["timeline"][0]["year"] == "2026 - NOW"
    assert data["resources"][0]["title"] == "Astronomy"
```

- [x] **Step 2: Run the new test to verify it fails before the files exist**

Run: `pytest tests/test_site_data.py -q`
Expected: FAIL because the required `_data/*.yml` files and validator do not exist yet.

- [x] **Step 3: Implement `_data/*.yml` and the validator**

Create the four YAML files with the exact current labels, ordering, and values from the homepage and header. Add `tools/site-checks/validate_site_data.py` to ensure the YAML files exist, load cleanly, contain the required keys, and keep the same sequence and external-link attributes.

- [x] **Step 4: Run the targeted validation and confirm it passes**

Run: `pytest tests/test_site_data.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add _data/navigation.yml _data/skills.yml _data/timeline.yml _data/resources.yml tools/site-checks/validate_site_data.py tests/test_site_data.py
git commit -m "feat: add site data yaml contracts" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Replace the static nav and homepage blocks with Liquid loops

**Files:**
- Modify: `_layouts/default.html`
- Modify: `index.html`
- Modify: README.md

**Interfaces:**
- Consumes: `site.data.navigation`, `site.data.skills`, `site.data.timeline`, `site.data.resources`.
- Produces: HTML identical in structure and classes to the current page.

- [x] **Step 1: Update the navigation loop**

Replace the inlined header list with a Liquid loop over `site.data.navigation`, preserving each item’s `label`, `href`, `class`, `target`, and `rel` values exactly.

- [x] **Step 2: Update the skills, timeline, and off-duty loops**

Render the corresponding sections using the YAML data while matching the exact current DOM structure: `.skill-row`, `.skill-domain`, `.tag`, `.tl-item`, `.tl-year`, `.tl-role`, `.tl-desc`, `.beyond-card`, `.icon`, `.beyond-more`.

- [x] **Step 3: Update the repo docs**

Add a README section describing the new `_data/` files, their purpose, and their expected schema.

- [x] **Step 4: Run the focused validation**

Run: `pytest tests/test_site_data.py -q && bundle exec jekyll build`
Expected: the data contract passes and the Jekyll site builds without template errors.

- [x] **Step 5: Commit**

```bash
git add _layouts/default.html index.html README.md
git commit -m "feat: render homepage data from yaml" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Full Python suite and Jekyll verification

**Files:**
- Validate: existing Python suite and Jekyll build output.

**Interfaces:**
- Consumes: the repository test suite and the generated site build.
- Produces: evidence that E2 is safe to push.

- [x] **Step 1: Run the Python suite**

Run: `pytest -q`
Expected: full repository Python suite passes.

- [x] **Step 2: Run the Jekyll build**

Run: `bundle exec jekyll build`
Expected: the static site builds successfully with the extracted YAML data and Liquid loops.

- [x] **Step 3: Review the generated homepage structure**

Sanity-check built HTML to confirm the skills, timeline, and off-duty cards still render with the expected class names and text from the YAML source.

- [x] **Step 4: Commit any final documentation or validation cleanups**

```bash
git add README.md tools/site-checks/validate_site_data.py tests/test_site_data.py
git commit -m "docs: finalize site data validation" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: PR creation and check review

**Files:**
- N/A; repository branch and PR metadata only.

**Interfaces:**
- Consumes: validated branch and GitHub repo state.
- Produces: PR to `main` and evidence from GitHub checks.

- [x] **Step 1: Push the branch**

Run: `git push -u origin dapiced-site-data-migration`
Expected: branch is published to GitHub.

- [x] **Step 2: Create the PR**

Run: `gh pr create --base main --head dapiced-site-data-migration --title "feat: extract homepage data into yaml" --body "## Summary\n\n- move the E2 homepage and navigation presentation data into `_data/*.yml`\n- render the matching homepage blocks with Liquid loops\n- add static schema validation and pytest coverage\n- validate the Python suite plus the Jekyll build"`
Expected: PR opens and is ready for check review.

- [x] **Step 3: Review GitHub checks**

Run: `gh pr checks` and inspect any failing jobs.
Expected: all required checks pass, or any failures are fixed and re-pushed before handoff.

- [x] **Step 4: Send the final handoff**

Report the PR link, commits, validation commands, and check status to the user/coordinator without merging the PR.
