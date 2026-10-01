# Blog Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Help readers find relevant authored posts quickly and make long-form posts easier to read, without bringing APOD content into the blog experience.

**Architecture:** Generate tag archives, the search index, the table of contents, and related posts at Jekyll build time. Use a small dependency-free browser search module and progressive enhancement for the blog index; keep generated HTML useful without JavaScript. Deliver all five tasks as staged commits in one Lot D pull request.

**Tech Stack:** Jekyll 4.4, Liquid, Kramdown, `jekyll-archives` 2.x, vanilla JavaScript, Node's built-in test runner, Python 3.11 standard library for generated-output checks.

**Spec:** `docs/superpowers/specs/2026-09-30-blog-discovery-design.md`

## Global Constraints

- Lot D is **one pull request**; the five tasks below are staged commits and review checkpoints within that PR, not separate PRs.
- Add `jekyll-archives` 2.x, which supports Jekyll 4; enable tag archives only at `/blog/tag/:name/`.
- Search only authored `site.posts` by title, excerpt, and tags. Keep all APOD `/sky/` content out of search, tags, and related posts.
- Keep all 10 listed posts in `/blog/` HTML; enhance the list to show 8 initially. Do not add server pagination.
- Search stays local: no external service, CDN library, client framework, `package.json`, or DOM-test dependency.
- Match search tokens with lowercase Unicode NFD accent removal and normalized punctuation; every token must match a field.
- Generate a TOC only when at least 3 usable h2/h3 headings are present; reuse Kramdown heading IDs.
- Show no more than 3 related authored posts, exclude the current post and its translation, prefer the current language, and fall back to English.
- Preserve the 103-test `tools/cosmic-daily` Python baseline, including the repo-data workflow and homepage-project tests. Extend existing CI workflow assertions rather than changing or relocating the repo-data tests.
- Keep topic pages editorial. Portfolio tags remain non-links; blog post tags link to archives.
- Each task's supporting README, CSS, i18n, and CI changes ship in the same task commit that needs them. Commits 3–5 may be prepared in any order once commits 1–2 are in place.

## Review Focus

- Search-index values containing quotes, accents, or punctuation must remain valid JSON; own this with the JSON parser check in Task 2, and keep result fields as text by rendering them with DOM `textContent`.
- A punctuation-only query must not become an empty-token match that returns every post; own it with `search_punctuation_only_query_returns_no_results` in Task 2.
- Search results must satisfy every query token and retain deterministic tag/title/excerpt/date ranking; own it with the multi-token and ranking unit tests in Task 2.
- A fragment targeting a post initially hidden after item 8 must not leave that target hidden, and keyboard activation must move focus to item 9; own it with the static contract check plus the manual URL-fragment/keyboard check in Task 3.
- Translation pairs must not recommend themselves across either direction, and French posts must prefer French before English fallback; own it with related-post output checks for both Prophet pages in Task 5.

---

### Task 1: Tag archives and linked post tags

**Files:**
- Create: `_layouts/tag-archive.html`
- Create: `_includes/post-item.html`
- Create: `tools/site-checks/check_blog_discovery.py`
- Modify: `Gemfile`, `Gemfile.lock`, `_config.yml`
- Modify: `blog/index.html`, `_includes/topic-posts.html`, `_includes/article-meta.html`
- Modify: `assets/css/style.css`
- Modify: `.github/workflows/ci.yml`, `tools/cosmic-daily/tests/test_workflows.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `_includes/post-item.html` accepts `post=post` and renders one `.post-item` `<li>` with the post link, date, visitor-count placeholder, linked tags, optional translation link, and excerpt. Use `{% include post-item.html post=post %}` from the blog index, topic pages, and tag archive.
- Produces: `_layouts/tag-archive.html` declares `layout: default`, consumes the plugin's `page.tag` and `page.posts`, sorts newest first, filters out French posts only when at least one non-French post exists, and otherwise lists `page.posts`. Give every archive a tag-specific title and meta description for `jekyll-seo-tag`.
- Produces: `python tools/site-checks/check_blog_discovery.py` reads `_site/`, reports failed invariants to stderr, and exits nonzero on failure. Start with archive and APOD/tag-link checks; later tasks extend this same checker.
- Consumes: existing `.post-list`, `.post-item`, `.tag`, `localized-date.html`, and existing post language/translation fields.

- [ ] **Step 1: Write the archive and workflow checks.** Add archive assertions to `check_blog_discovery.py`: every authored post tag has a generated `_site/blog/tag/<slug>/index.html`; `machine-learning` lists exactly `/blog/2026/09/what-i-learned-about-facebook-prophet/`, `/blog/2026/08/autonomous-ai-agents-2026/`, and `/blog/2026/08/forty-years-of-losing-to-a-tree/`; APOD-only `apod` and `nasa` archives are absent; archive links do not point into `/sky/`; every `.tag` on `/blog/`, topic pages, posts, and archives is a link to a generated archive; portfolio tags remain spans. Extend the existing `test_ci_builds_the_site` and `test_ci_smoke_checks_the_generated_output` assertions to require the site-job checker/setup step and the tag-archive smoke path.
- [ ] **Step 2: Run the checks against the unchanged build to verify they fail for the missing archive feature.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Expected: build succeeds on the baseline bundle, then the checker fails because `/blog/tag/machine-learning/` has not been generated. In the Python package working directory, `python -m pytest tests/test_workflows.py -q` fails the new setup/checker and smoke-path assertions.
- [ ] **Step 3: Add the plugin and archive layout.** Add `jekyll-archives` 2.x to `Gemfile`, run `bundle install` to update `Gemfile.lock`, and configure only `tags`, layout `tag-archive`, permalink `/blog/tag/:name/`, and `slug_mode: default` in `_config.yml`. Implement the `#<tag>` heading/count, newest-first filtered-or-fallback post list, link to `/blog/`, and tag-specific title/meta description through `jekyll-seo-tag` in the default layout. Add the search link in Task 2, when its target exists.
- [ ] **Step 4: Extract and link post-list markup.** Implement `post-item.html` and replace the duplicated list item in `blog/index.html` and `_includes/topic-posts.html`. In `_includes/article-meta.html`, link tags only when `page.collection == "posts"`; keep portfolio tags as spans. Link tags in the new shared post item. Add visible focus and consistent hover styles for `.tag` links.
- [ ] **Step 5: Wire and verify CI and docs.** In the `site` job of `.github/workflows/ci.yml`, add `actions/setup-python@v7` with Python 3.11 and run the checker after the build and existing smoke/redirect checks. Add `_site/blog/tag/machine-learning/index.html` to the existing smoke loop. Update `test_workflows.py` assertions. Update README writing/structure/deploy guidance: tags are lowercase slugs, archives are generated by `jekyll-archives`, and the Actions-based Jekyll build is required.
- [ ] **Step 6: Run the task checks and commit.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Run from `tools/cosmic-daily`: `python -m pytest tests/test_workflows.py -q`

  Expected: both pass; the checker confirms all authored tag archives and the three expected `machine-learning` posts, with no APOD leakage.

  ```bash
  git add Gemfile Gemfile.lock _config.yml _layouts/tag-archive.html _includes/post-item.html _includes/topic-posts.html _includes/article-meta.html blog/index.html assets/css/style.css tools/site-checks/check_blog_discovery.py .github/workflows/ci.yml tools/cosmic-daily/tests/test_workflows.py README.md
  git commit -m "feat: add authored blog tag archives"
  ```

### Task 2: Local search

**Files:**
- Create: `blog/search/index.html`, `blog/search.json`
- Create: `assets/js/blog-search-core.js`, `assets/js/blog-search.js`
- Create: `tools/site-checks/js/blog-search-core.test.js`
- Modify: `_layouts/default.html`, `_data/i18n.yml`
- Modify: `tools/site-checks/check_blog_discovery.py`
- Modify: `.github/workflows/ci.yml`, `tools/cosmic-daily/tests/test_workflows.py`
- Modify: `blog/index.html`, `_layouts/tag-archive.html`, `README.md`

**Interfaces:**
- Produces: `window.BlogSearchCore.normalize(value)` returns normalized text; `window.BlogSearchCore.searchPosts(posts, query)` returns matching post records ordered by score descending, then date descending. In Node, `module.exports` exposes the same object behind the `typeof module !== "undefined"` guard.
- Consumes: search records have `title`, `url`, `date`, `lang`, `tags`, and plain-text `excerpt`; browser UI loads the local JSON and calls `searchPosts`.
- Produces: search page scripts load with `defer` only on pages marked `blog_search: true`; the default layout loads core before UI.

- [ ] **Step 1: Write pure-function tests first.** Add Node tests named `normalize_removes_accents_and_normalizes_hyphens`, `search_requires_every_token_across_fields`, `search_scores_tag_then_title_then_excerpt`, `search_breaks_score_ties_by_newest_date`, `search_empty_query_returns_no_results`, and `search_punctuation_only_query_returns_no_results`. Include `"donnees"` against `"Données"` and `"machine learning"` against the `machine-learning` tag.
- [ ] **Step 2: Run the tests to verify they fail before the module exists.**

  Run: `node --test tools/site-checks/js/`

  Expected: FAIL because `blog-search-core.js` does not exist/export `normalize` and `searchPosts`.
- [ ] **Step 3: Implement the dependency-free core.** Normalize with lowercase, Unicode NFD and combining-mark removal; replace runs of non-alphanumeric characters with one space; split into nonempty tokens. A post matches only if each token occurs in at least one normalized field. For each token, score 3 for a tag match, else 2 for a title match, else 1 for an excerpt match. Sort by total score descending and ISO date descending.
- [ ] **Step 4: Run the core tests to verify they pass.**

  Run: `node --test tools/site-checks/js/`

  Expected: all six tests pass with no npm install or package manifest.
- [ ] **Step 5: Add the generated search index and accessible page.** In `blog/search.json`, use `layout: null`, `permalink: /blog/search.json`, `sitemap: false`, and `jsonify` for every value. Loop over all `site.posts`; use `description` when present, otherwise plain-text normalized/truncated excerpt at 280 characters. Add the labelled GET form, results region, polite live status, and server-rendered no-JS note/link/full `site.tags` archive list to `blog/search/index.html`.
- [ ] **Step 6: Add browser wiring and translations.** Add the approved search strings under both `en` and `fr`. Mark the page `blog_search: true`; in `_layouts/default.html` load core then UI with `defer` only for that marker. In `blog-search.js`, prefill from `?q=`, fetch `/blog/search.json` once, debounce input about 150 ms, intercept submit, update history with `replaceState`, render title/date/FR marker/excerpt/tag links using DOM methods and text content, preserve fallback and show localized `search_error` on fetch failure, and source all visible text from Liquid-rendered data attributes. Format result counts with localized `search_results`, `search_one_result`, and `search_none`; an empty normalized query shows no results and no status. Link search from the blog index and archive. Update README with `/blog/search/` and `/blog/search.json`.
- [ ] **Step 7: Extend generated-output and CI checks.** Extend the checker to parse `search.json`, require 11 authored records with all required fields and existing post URLs, reject `/sky/` URLs, verify the search page fallback and tag links, and ensure the page/JSON paths are smoke-checked. Extend existing workflow assertions for `actions/setup-node@v6`, `node-version: lts/*`, and the Node test command.
- [ ] **Step 8: Run the tests and build, then commit.**

  Run: `node --test tools/site-checks/js/`

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Run from `tools/cosmic-daily`: `python -m pytest tests/test_workflows.py -q`

  Expected: Node tests pass; the checker parses valid JSON with 11 posts, no `/sky/` URLs, and a server-rendered fallback; workflow assertions pass.

  Manual: submit a query that returns an excerpt containing quotation marks or ampersands and verify it is shown as literal text, not interpreted markup.

  ```bash
  git add blog/search/index.html blog/search.json assets/js/blog-search-core.js assets/js/blog-search.js tools/site-checks/js/blog-search-core.test.js tools/site-checks/check_blog_discovery.py _layouts/default.html _data/i18n.yml blog/index.html _layouts/tag-archive.html .github/workflows/ci.yml tools/cosmic-daily/tests/test_workflows.py README.md
  git commit -m "feat: add local blog search"
  ```

### Task 3: Progressive Show more

**Files:**
- Create: `assets/js/blog-index.js`
- Modify: `blog/index.html`, `_includes/post-item.html`, `_layouts/default.html`
- Modify: `_data/i18n.yml`, `tools/site-checks/check_blog_discovery.py`
- Modify: `README.md`

**Interfaces:**
- Produces: when `page.blog_index` is true, the default layout loads `blog-index.js` with `defer`; the script is inert unless `#all-posts[data-initial="8"]` exists and has more than 8 `.post-item` children.
- Consumes: post item IDs use `post-{{ post.slug }}`; the button's translated label and item count are supplied through data attributes.

- [ ] **Step 1: Add failing static checks.** Extend the checker to require all 10 listed-post links in rendered `/blog/`, `ul#all-posts[data-initial="8"]`, stable `post-<slug>` item IDs, and no server-side omission.
- [ ] **Step 2: Run the build/checker to verify the index contract fails.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Expected: FAIL because the list id/data attribute and item IDs are not present; confirm all 10 links were already in HTML.
- [ ] **Step 3: Add progressive enhancement.** Mark the blog index `blog_index: true`, add the list ID and initial-count attribute, add `post-{{ post.slug }}` to each shared item, and conditionally load `blog-index.js` with `defer`. The script hides items 9 onward only when more than 8 exist, inserts the translated button immediately after the list with `aria-controls="all-posts"` and `aria-expanded="false"`, reveals all items on activation, changes `aria-expanded` to true, focuses item 9's `.post-link`, then removes the button. If the current fragment identifies an item that would be hidden, leave the list fully visible. Do not add `.reveal` to post items: `main.js`'s observer only observes `.reveal`, so the new items stay visible.
- [ ] **Step 4: Add `show_more` data and verify.** Supply the count and translated label from `_data/i18n.yml` through attributes; extend the checker to verify the script hook, default count, and complete server HTML. Add README guidance that all posts remain in HTML and the initial display is progressive.
- [ ] **Step 5: Run generated-output checks and the manual behavior checklist, then commit.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Manual: with JS, verify 8 visible, keyboard focus reaches the button, Enter and Space reveal all, focus lands on item 9 and the button is removed; with JS disabled, all 10 remain visible and no button appears; test a `#post-<slug>` fragment for a post after item 8; verify reduced-motion mode does not trigger smooth scrolling/reveal animation.

  Expected: static checks pass and every manual item passes.

  ```bash
  git add assets/js/blog-index.js blog/index.html _includes/post-item.html _layouts/default.html _data/i18n.yml tools/site-checks/check_blog_discovery.py README.md
  git commit -m "feat: progressively reveal blog posts"
  ```

### Task 4: Long-post table of contents

**Files:**
- Create: `_includes/post-toc.html`
- Modify: `_layouts/post.html`, `assets/css/style.css`, `_data/i18n.yml`
- Modify: `tools/site-checks/check_blog_discovery.py`, `README.md`

**Interfaces:**
- Produces: `post-toc.html` reads rendered `content`, extracts h2/h3 headings with existing IDs and stripped text, and emits nothing unless at least 3 usable headings exist.
- Consumes: `_layouts/post.html` passes the current page language through existing `site.data.i18n[lang]` resolution.

- [ ] **Step 1: Add failing TOC output checks.** Extend the checker to count h2/h3 within each post content, require a TOC for pages with at least 3 usable headings, require each TOC fragment to target an ID on that page, reject duplicate TOC IDs, verify h3 nesting under its preceding h2 (or top level before any h2), and verify `nothingness` has no TOC.
- [ ] **Step 2: Run the build/checker to verify the long-post TOC assertion fails.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Expected: FAIL because long posts have no `nav.post-toc` yet.
- [ ] **Step 3: Implement server-side TOC generation.** Render the include between article metadata and `.post-content`. Split the rendered content by heading tags, retain the Kramdown `id` verbatim, strip heading markup for link text, skip headings without IDs, and preserve heading order while nesting h3 entries under the previous h2. Keep an h3 before any h2 at top level. Render the TOC heading from `toc_title` with the fixed `id="post-toc-title"`; Task 4's checker fails if a post heading collides with that ID.
- [ ] **Step 4: Add spacing and motion behavior.** Use `id="post-toc-title"` for the TOC heading and make the checker fail if a post heading collides with that ID. Add `scroll-margin-top: 6rem` to post h2/h3 targets. Do not add custom smooth scrolling; native anchor navigation respects reduced motion. Add `On this page` / `Sur cette page` to i18n and README guidance to author sections with `##` and `###`.
- [ ] **Step 5: Run build/output and keyboard checks, then commit.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Manual: open a long post, tab through TOC links, verify each target is visible below the sticky header, and use Back to return to the TOC; check the French TOC heading on the French Prophet post and native jumps with reduced motion enabled.

  Expected: all generated anchors resolve to same-page IDs; TOCs appear only at the 3-heading threshold; manual keyboard checks pass.

  ```bash
  git add _includes/post-toc.html _layouts/post.html assets/css/style.css _data/i18n.yml tools/site-checks/check_blog_discovery.py README.md
  git commit -m "feat: add tables of contents to long posts"
  ```

### Task 5: Related authored posts

**Files:**
- Create: `_includes/related-posts.html`
- Modify: `_layouts/post.html`, `_data/i18n.yml`
- Modify: `tools/site-checks/check_blog_discovery.py`, `README.md`

**Interfaces:**
- Produces: `related-posts.html` reads the current page and `site.posts`, computes shared-tag scores, orders by score descending then date descending, applies language preference/fallback, and emits a section only when at least one candidate remains.
- Consumes: `page.url`, `page.tags`, `page.lang`, `page.translation_url`, `post.translation_url`, and `related_title` from i18n.

- [ ] **Step 1: Add failing related-output checks.** Extend the checker to assert every post has at most 3 related links, no self or translation link, all recommended posts share at least one tag, order is score/date descending, English Prophet does not recommend French, and French Prophet prefers same-language results before English fallback.
- [ ] **Step 2: Run the build/checker to verify related-content assertions fail.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Expected: FAIL because posts do not yet contain a related section.
- [ ] **Step 3: Implement the Liquid include and layout placement.** Build a sortable key from zero-padded shared-tag score, formatted date, and URL; sort and reverse for score/date descending and deterministic URL ordering. Exclude current URL, `translation_url`, and candidates whose `translation_url` points back to the current URL. Select current-language candidates first; append English candidates only until 3 results are reached, skipping already selected posts. Render after `.post-content` and before comments.
- [ ] **Step 4: Add localized heading and no-results behavior.** Add `Related posts` / `Articles connexes` to i18n. Render no section at all when no positive-score candidate remains. Render each selected post's title, date, and linked tags. Extend the checker to validate the generated section and translation/language rules. Add README notes that recommendations use shared tags and may be absent for sparse tags.
- [ ] **Step 5: Run final checks and commit.**

  Run: `bundle exec jekyll build && python tools/site-checks/check_blog_discovery.py`

  Run: `node --test tools/site-checks/js/`

  Run from `tools/cosmic-daily`: `python -m pytest -q`

  Expected: build and checker pass; Node tests pass; all 103 existing Python tests pass, including repo-data workflow and homepage-project checks. Complete the Task 3 accessibility checklist and the full checklist in spec section 7.4 before merging.

  ```bash
  git add _includes/related-posts.html _layouts/post.html _data/i18n.yml tools/site-checks/check_blog_discovery.py README.md
  git commit -m "feat: show related blog posts"
  ```

## Final one-PR acceptance

- One PR contains the five task commits; do not split them into separate PRs.
- `bundle exec jekyll build` succeeds; `/blog/tag/machine-learning/`, `/blog/search/`, and `/blog/search.json` exist.
- `python tools/site-checks/check_blog_discovery.py` passes against the generated `_site`.
- `node --test tools/site-checks/js/` passes with no third-party dependencies.
- From `tools/cosmic-daily`, `python -m pytest -q` passes the 103-test baseline.
- The `.github/workflows/ci.yml` `site` job runs build, existing smoke and redirect checks, the standard-library discovery checker, and Node tests; the separate `cosmic-daily` job continues running the same Python suite, including the repo-data workflow tests.
- The GitHub Actions Pages workflow remains unchanged; it already installs the Gemfile and builds with Jekyll 4.
- Record all manual keyboard, no-JavaScript, reduced-motion, focus, and contrast checks from spec section 7.4 in the PR description.
