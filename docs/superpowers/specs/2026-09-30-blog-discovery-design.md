# Lot D: blog discovery and long-form reading

- **Status:** approved design, awaiting review of this specification
- **Date:** 2026-09-30
- **Scope:** specification only. No product code ships with this document.

## 1. Objective

Help readers find the authored posts that interest them quickly, and make long posts easier to read. The approved design has five parts:

1. Real tag archive pages at `/blog/tag/<tag>/`, with every `#tag` rendered as a link.
2. A local search page at `/blog/search/`, backed by a Jekyll-generated `/blog/search.json`.
3. A progressive "Show more" on `/blog/`.
4. A table of contents on long posts.
5. Up to three related posts at the end of each post.

The NASA APOD content under `/sky/` is out of scope for all five. It must never appear in blog search, tag archives or related posts.

## 2. Non-goals

- Server-side pagination of `/blog/`. There are 11 authored posts, one of which is a French translation, so pagination would add URLs without helping anyone.
- Full-text search over post bodies. Search covers title, excerpt and tags only.
- Any external search service, CDN-hosted library or client-side framework.
- Changes to the curated topic pages (`/blog/ai/`, `/blog/astronomy/`, `/blog/infrastructure/`, `/blog/machine-learning/`, `/blog/physics/`). They stay editorial. Tag archives are generated and sit alongside them.
- Translating the navigation or footer. They remain in English on purpose, as they are today.
- Tag pages or search for portfolio items or APOD entries.

## 3. Current state (main @ b302ff4)

These facts constrain the design.

- **Build and deploy.** Jekyll ~4.4, with `jekyll-feed`, `jekyll-sitemap`, `jekyll-seo-tag` and `jekyll-redirect-from`. `.github/workflows/pages.yml` builds with Ruby 3.4 and deploys through GitHub Actions (PR #83), not the legacy Pages builder, so non-safelisted plugins work.
- **CI.** `.github/workflows/ci.yml` has two jobs. The `site` job runs `bundle exec jekyll build`, then a bash loop checking that a few generated files are non-empty, then a redirect check. The `cosmic-daily` job runs pytest on Python 3.11. The repository has no `package.json` and no JavaScript tests.
- **Content.** `_posts/` holds 11 posts with `layout: post` and a `tags: [...]` list. Tags are already lowercase, hyphenated slugs. The only bilingual pair is the Prophet post: `2026-09-26-ce-que-jai-appris-sur-facebook-prophet` (`lang: fr`) and `2026-09-26-what-i-learned-about-facebook-prophet` (`lang: en`). They link to each other through `translation_url` and `translation_label`, and they share identical tags. Posts without `lang` default to `site.lang` (`en`).
- **Tag overlap is thin.** Leaving the French post aside, there are 41 distinct tags. Only seven appear on more than one post: `machine-learning` (3), plus `data-science`, `python`, `dataops`, `kaggle`, `engineering` and `astronomy` (2 each). Most tag archives will list a single post, and several posts will have no related post at all. The design accepts this. Both features behave correctly with sparse data and get more useful as the blog grows.
- **APOD.** APOD entries live in the `_apod` collection (layout `apod`, permalink `/sky/...`) and carry tags such as `astronomy`, `nasa` and `apod`. They are not in the `posts` collection, so they are absent from `site.posts` and `site.tags`.
- **Blog index.** `blog/index.html` lists `site.posts | where_exp: "post", "post.lang != 'fr'"`, which is 10 items today. Readers reach the French translation through a "version française 🇫🇷" link on its English counterpart. Tags render as plain `#tag` text.
- **Topic pages.** `_includes/topic-posts.html` repeats the same list-item markup, filtered by the page's `topics:` front matter.
- **Post layout.** `_layouts/post.html` renders the header, `{% include article-meta.html %}`, then `div.post-content` with `{{ content }}`, comments and a back link. `article-meta.html` renders tags as `<span class="tag">#tag</span>` and is shared with the portfolio layout.
- **Headings.** Kramdown `auto_ids` is on by default. Posts use Markdown headings only, with no raw `<h2>` and no manual IDs. Ten of the eleven posts have three or more h2/h3 headings; `nothingness` has none.
- **i18n.** `_data/i18n.yml` holds `en` and `fr` strings, looked up via `page.lang`.
- **Front end.** One deferred script, `assets/js/main.js` (a single IIFE), and one stylesheet, `assets/css/style.css`. The stylesheet already has `:focus-visible`, `prefers-reduced-motion` rules and `.post-list` / `.post-item` styles. The default layout has a skip link and `main#main[tabindex="-1"]`.

## 4. Shared definitions

**Authored post:** any document in `site.posts`. That excludes `_apod` and `_portfolio` by construction.

**Listed post:** an authored post whose `lang` is not `fr`. This matches the existing index rule. A French post appears through its English counterpart's "version française" link.

**Post language:** `post.lang | default: site.lang`.

**Tag URL:** `/blog/tag/{{ tag | slugify }}/`. Tags are already slugs, so `slugify` is a safeguard. It must produce the same value as jekyll-archives (see 5.1).

**Translation of a post:** the post whose `url` equals the current post's `translation_url`. No other translation key exists, and this spec adds none.

## 5. Components

### 5.1 Tag archives

**Plugin.** Add `jekyll-archives` (2.x, which supports Jekyll 4) to the `Gemfile` and to `plugins:` in `_config.yml`, and commit the updated `Gemfile.lock`.

**Configuration** (`_config.yml`):

```yaml
jekyll-archives:
  enabled: [tags]
  layouts:
    tag: tag-archive
  permalinks:
    tag: /blog/tag/:name/
  slug_mode: default
```

Only tag archives are enabled. Year, month, day and category archives stay off.

**Layout** `_layouts/tag-archive.html` (based on `default`):

- An `h1` such as `#machine-learning`, plus a one-line count ("3 posts").
- The listed posts from `page.posts`, newest first, using the existing `.post-list` / `.post-item` markup. A French post carrying the tag is not listed separately, which is consistent with the index.
- If every post with the tag is French (not the case today), the archive lists those posts rather than rendering empty. Rule: list posts where `lang != 'fr'`; if that is empty, list `page.posts` as is.
- A link back to `/blog/` and a link to `/blog/search/`.
- A `<title>` and meta description through `jekyll-seo-tag`, so each archive works as a landing page from the sitemap.

**Tag links everywhere.** Every place that renders a post tag outputs `<a class="tag" href="TAG URL">#tag</a>`:

- `blog/index.html` (post list);
- `_includes/topic-posts.html` (topic pages);
- `_includes/article-meta.html`, **only when the page is a post** (`page.collection == "posts"`). Portfolio items keep the plain `<span class="tag">` because their tags have no archive;
- the tag archive layout itself, for the other tags of each listed post.

To avoid a fourth copy of the list-item markup, extract it into `_includes/post-item.html` and use it from the index, the topic pages and the tag archive. This is the only refactor in scope.

The existing `.tag` style (`style.css`, around lines 421–430) is reused. Links only need a visible `:focus-visible` state and a hover treatment consistent with the current hover rule.

**Without JavaScript:** tag archives are plain HTML and fully usable.

### 5.2 Search index and search page

**Index.** `blog/search.json` is a Liquid template with `layout: null`, `permalink: /blog/search.json` and `sitemap: false`. It loops over `site.posts` (EN and FR) and emits one object per authored post:

```json
{
  "title": "What I Learned About Facebook Prophet",
  "url": "/blog/2026/09/what-i-learned-about-facebook-prophet/",
  "date": "2026-09-26",
  "lang": "en",
  "tags": ["machine-learning", "data-science", "time-series", "forecasting", "prophet", "python", "kaggle"],
  "excerpt": "Plain-text excerpt, at most 280 characters."
}
```

- `excerpt` is `post.description` when set, otherwise `post.excerpt | strip_html | normalize_whitespace | truncate: 280`.
- Every value goes through `jsonify`, so quotes, accents and em dashes come out as valid JSON.
- `url` is `post.url | relative_url`.
- `date` is `post.date | date: "%Y-%m-%d"`.

**Page.** `blog/search/index.html` uses layout `default` and contains:

- A real `<form role="search" action="/blog/search/" method="get">` with a labelled `<input type="search" name="q">` and a submit button. Without JS, submitting reloads the page with `?q=`, which is harmless.
- A results region `<div id="search-results">` and a status line `<p id="search-status" role="status" aria-live="polite">`.
- **Fallback content**, rendered server-side and visible by default: a short note that search needs JavaScript, a link to `/blog/`, and the full list of tags from `site.tags`, each linking to its archive. The script hides the fallback once the index has loaded. If the fetch fails, the fallback stays visible and the status line reports the error.

**Script.** `assets/js/blog-search.js` is loaded with `defer` on the search page only. It:

1. reads `q` from the URL and prefills the input;
2. fetches `/blog/search.json` once;
3. on `input` (debounced to about 150 ms) and on submit (with `preventDefault`), runs the query, renders results and updates `?q=` with `history.replaceState`;
4. renders each result with its linked title, date, a "FR" marker for French posts, the excerpt and tag links, styled like `.post-item`;
5. sets the status text to "N results for "query"", "No results for "query"", or nothing when the query is empty. The strings come from i18n (see 5.6).

**Matching rules,** implemented as pure functions (see 6.3):

- Normalize the query and every field: lowercase, Unicode NFD with diacritics removed, and runs of non-alphanumeric characters collapsed to a single space. "Données" then matches "donnees", and "machine learning" matches the tag `machine-learning`.
- Split the query into tokens. A post matches only if **every** token is a substring of at least one of its normalized fields.
- Score each token as 3 if found in a tag, otherwise 2 if found in the title, otherwise 1 if found in the excerpt. Sort by total score descending, then by date descending.
- An empty query shows no results and no status.
- No fuzzy matching. With about ten posts, predictable substring matching is worth more than typo tolerance.

**Language.** Both versions of the Prophet post are indexed, so a reader searching in French finds the French version. No deduplication is applied; the "FR" marker makes the difference visible.

**Discoverability.** Add a search link on `/blog/` near the "All posts" heading, and on each tag archive. The main navigation does not change in this lot.

### 5.3 "Show more" on `/blog/`

- All listed posts stay in the HTML, for SEO and for readers without JS.
- The list gets an `id` (`all-posts`) and a `data-initial="8"` attribute.
- The behavior goes in a small deferred script. It can be a block in `main.js` or a separate `blog-index.js`; the implementation picks one. It runs only when that list exists and has more than 8 items:
  - adds the `hidden` attribute to items 9 and later;
  - inserts `<button type="button" aria-controls="all-posts" aria-expanded="false">` after the list, labelled "Show all posts (N more)" from i18n;
  - on activation, removes `hidden` from every item, sets `aria-expanded="true"`, moves focus to the link of the first revealed item and removes the button. There is no "Show less".
- If the URL fragment targets an item that would be hidden, the script leaves the whole list visible.
- With 10 listed posts today, 2 start hidden. With 8 or fewer, the script does nothing.
- The existing reveal animation (IntersectionObserver in `main.js`) must not leave newly shown items invisible. The implementation must confirm that revealed items reach the visible state, or exclude them from the effect.

### 5.4 Table of contents

**Rule.** A post gets a TOC when its rendered content has **at least three h2 or h3 headings, counted together**. That is how this spec reads "at least three sections". Today this covers 10 of the 11 posts.

**Generation.** Server-side, in `_includes/post-toc.html`, rendered from `_layouts/post.html` between the article meta and `div.post-content`. No plugin, no JavaScript.

- Split `content` on `<h2` and `<h3`, then extract each heading's `id` and its text (`strip_html`). The IDs come from Kramdown `auto_ids`. The implementation reuses those IDs as they are and never computes its own slugs, so links and targets cannot drift apart.
- Headings without an `id` are skipped. If fewer than three usable headings remain, nothing is rendered.
- Output:

```html
<nav class="post-toc" aria-labelledby="post-toc-title">
  <h2 id="post-toc-title">On this page</h2>
  <ol>
    <li><a href="#section-id">Section</a>
      <ol><li><a href="#sub-id">Subsection</a></li></ol>
    </li>
  </ol>
</nav>
```

- h3 entries nest under the preceding h2. An h3 that appears before any h2 is listed at the top level.
- The TOC heading text comes from i18n. The heading carries `id="post-toc-title"`; the implementation checks that no Kramdown ID in the post uses the same value.
- The TOC's own `h2` sits outside `div.post-content`, so it is not counted or listed.
- Targets get `scroll-margin-top` so the sticky header does not cover them. Any smooth scrolling respects `prefers-reduced-motion`.

**Layout.** The TOC sits inline above the content on every screen size. A sticky sidebar is out of scope for this lot.

### 5.5 Related posts

**Placement.** `_includes/related-posts.html`, rendered in `_layouts/post.html` after `div.post-content` and before the comments.

**Candidates.** All of `site.posts`, minus:

- the current post (`post.url == page.url`);
- its translation (`post.url == page.translation_url`);
- any post that names the current post as its translation (`post.translation_url == page.url`), which covers a pair linked in one direction only.

**Scoring.** The score is the number of tags shared with the current post. Candidates scoring 0 are dropped.

**Language preference.** Let L be the current post's language.

1. Take candidates in language L, sorted by score descending, then date descending.
2. If fewer than 3 were found, add English candidates (language `en`) in the same order, skipping any already chosen.
3. Keep at most 3.

On an English post, both steps select English posts, so French posts are never suggested there. On the French Prophet post, French candidates come first (none today), then English ones.

**Output.** A `<section aria-labelledby="related-title">` with an `h2` from i18n and a short list showing title, date and tag links. With no candidate left, nothing is rendered: no heading and no empty box.

**Implementation note.** Liquid cannot sort by a computed key. The expected approach builds a sortable string per candidate, such as a zero-padded score, then the date, then the URL, sorts the strings and walks them in reverse. Another approach is fine if it produces the same order. With 11 posts the build cost is negligible.

### 5.6 i18n strings

Add these keys to `_data/i18n.yml` under both `en` and `fr`:

| Key | en | fr |
|---|---|---|
| `toc_title` | On this page | Sur cette page |
| `related_title` | Related posts | Articles connexes |
| `show_more` | Show all posts ({n} more) | Afficher tous les articles ({n} de plus) |
| `search_label` | Search the blog | Rechercher dans le blogue |
| `search_results` | {n} results for "{q}" | {n} résultats pour « {q} » |
| `search_one_result` | 1 result for "{q}" | 1 résultat pour « {q} » |
| `search_none` | No results for "{q}" | Aucun résultat pour « {q} » |
| `search_nojs` | Search needs JavaScript. You can browse all posts or the tags below. | La recherche nécessite JavaScript. Vous pouvez parcourir tous les articles ou les étiquettes ci-dessous. |
| `search_error` | The search index could not be loaded. | L'index de recherche n'a pas pu être chargé. |

The search page, tag archives and blog index are English pages and use the `en` strings. Scripts read their strings from `data-*` attributes rendered by Liquid; no UI text is hard-coded in JavaScript. The `fr` strings matter today for the TOC and related posts on the French post.

## 6. Data contracts and invariants

### 6.1 URLs

| Path | Source | Notes |
|---|---|---|
| `/blog/tag/<tag>/` | jekyll-archives | one per tag in `site.tags` |
| `/blog/search/` | `blog/search/index.html` | included in the sitemap |
| `/blog/search.json` | `blog/search.json` | `sitemap: false` |

None of these may collide with an existing page. Posts live under `/blog/<year>/...`, and no topic page uses the slug `tag` or `search`, so there is no conflict today.

### 6.2 APOD exclusion

APOD is excluded by construction, because every feature reads only `site.posts` or `site.tags`. The checks in section 7 assert it anyway, so a future change (moving APOD into `_posts`, or adding `site.apod` to a loop) fails CI instead of leaking content into the blog.

### 6.3 Front-end module boundary

The search logic (normalize, tokenize, match, score, sort) lives in pure functions in `assets/js/blog-search-core.js`, with no DOM access. The file is a classic script: in the browser it exposes a single global namespace, and under Node it also assigns `module.exports` behind a `typeof module !== "undefined"` check. No bundler and no build step. `blog-search.js` handles DOM wiring only.

The TOC and related posts are computed in Liquid at build time and have no JavaScript.

## 7. Validation

### 7.1 Build

`bundle exec jekyll build` succeeds with no new warnings, locally and in both workflows.

### 7.2 Generated-output checks (CI, `site` job)

Add `tools/site-checks/check_blog_discovery.py`, which uses only the Python standard library (`json`, `html.parser`, `pathlib`) and runs after the build. It asserts the following.

- **Tag archives:** `_site/blog/tag/<slug>/index.html` exists for every tag of every authored post. Spot check: `machine-learning` lists exactly its 3 expected posts. No archive lists the French Prophet post while its English counterpart carries the same tag.
- **APOD exclusion:** `_site/blog/tag/apod/` and `_site/blog/tag/nasa/` do not exist, unless an authored post carries those tags. No archive page links to `/sky/`.
- **Tag links:** every `.tag` element on `/blog/`, the topic pages and the posts is an `<a>` whose `href` points to an existing archive. Portfolio pages keep non-link tags.
- **search.json:** it parses as JSON and has one entry per authored post (11 today), each with a non-empty `title`, `url`, `date`, `lang` and `tags`. No `url` starts with `/sky/`, and every `url` exists in `_site`.
- **Show more:** the HTML of `/blog/` contains all 10 listed post links, so nothing is dropped server-side.
- **TOC:** every post with three or more h2/h3 headings in its content has `nav.post-toc`, and every TOC `href="#x"` matches an `id="x"` in the same page. `nothingness` has no TOC.
- **Related posts:** no post's related section links to the post itself or its translation, no section holds more than 3 items, and the English Prophet post's section contains no French post.

The existing bash loop in `ci.yml` also checks `blog/search/index.html`, `blog/search.json` and `blog/tag/machine-learning/index.html`.

Python is used because CI already relies on it. The checks run as a new step of the `site` job, which therefore needs `actions/setup-python`.

### 7.3 JavaScript behavior

**Decision:** no jsdom, Playwright or other DOM test dependency in this lot. Adding a `package.json`, a lockfile and a DOM emulator for roughly 150 lines of front-end code would be disproportionate.

Instead:

- **Unit tests** for `blog-search-core.js` with Node's built-in runner: `node --test tools/site-checks/js/`. Zero npm dependencies, so no `package.json`. Cases cover accent-insensitive matching (`donnees` against `Données`), hyphenated tags (`machine learning` against `machine-learning`), multi-token AND, scoring order (tag, then title, then excerpt, then date), the empty query, and a punctuation-only query.
- **CI:** a step using `actions/setup-node` (current LTS) runs that command in the `site` job.
- **DOM wiring** for search and Show more is covered by the static checks in 7.2 and the manual checklist in 7.4. If DOM regressions appear later, a DOM test setup can be reconsidered in a separate lot.

### 7.4 Manual keyboard and accessibility checklist

Run on a local build before merging and record the result in the PR description.

1. `/blog/` with JS: 8 items are visible. Tab reaches the "Show all posts" button, and Enter or Space reveals every item. Focus lands on the 9th item's link, and the button is gone.
2. `/blog/` with JS disabled: all 10 items are visible and there is no button.
3. `/blog/search/`: the input has a visible label. Typing updates the results, and a screen reader announces the count. `?q=prophet` loads with results. Tab moves through result links in order. With JS disabled, the fallback tag list is visible and works.
4. A long post: the TOC comes right after the article meta. Each link moves to its section without the heading hiding under the header, and Back returns to the TOC.
5. Tag links on a post, on the index and on a topic page show the focus ring and open the right archive.
6. With `prefers-reduced-motion: reduce`, TOC jumps and Show more trigger no smooth scrolling or reveal animation.
7. New elements meet WCAG AA contrast in every color scheme the site supports, using the same tokens as `.tag` and `.post-item`.

### 7.5 CI summary

After this lot, the `site` job runs: build, the extended file checks, the redirect check, the Python discovery checks, then the Node unit tests. Any failing step fails the job.

## 8. Build and deploy impact

- **New gem:** `jekyll-archives`. This works because Pages deploys through Actions (`pages.yml`), which already runs `bundle install`, so the workflow needs no change. A legacy GitHub Pages build would silently skip the tag archives; the README must state this dependency.
- **New files:** `_layouts/tag-archive.html`, `_includes/post-item.html`, `_includes/post-toc.html`, `_includes/related-posts.html`, `blog/search/index.html`, `blog/search.json`, `assets/js/blog-search-core.js`, `assets/js/blog-search.js`, possibly `assets/js/blog-index.js`, `tools/site-checks/check_blog_discovery.py` and the Node tests under `tools/site-checks/js/`.
- **Modified files:** `Gemfile`, `Gemfile.lock`, `_config.yml`, `blog/index.html`, `_includes/topic-posts.html`, `_includes/article-meta.html`, `_layouts/post.html`, `_data/i18n.yml`, `assets/css/style.css`, `.github/workflows/ci.yml`, `README.md`.
- `tools/` is already listed in `exclude`, so the check scripts stay out of `_site`.
- **README:** document the tag archives (tags must stay lowercase slugs), the search index, the TOC rule (use `##` and `###` headings), and the dependency on the Actions-based deploy.

## 9. Rejected alternatives

| Option | Reason |
|---|---|
| Pagefind | Full-text search goes beyond what this blog needs, and it adds a post-build binary step to both workflows. Worth revisiting if the post count grows substantially. |
| Fuse.js or any CDN library | An external dependency for fuzzy matching that a ten-post index does not need. The no-CDN rule rules it out. |
| jekyll-paginate-v2 | Server-side pagination is unnecessary at this size. |
| jekyll-toc | A dependency for what a small Liquid include can do. It also applies its own ID handling, which could drift from Kramdown's. |
| jsdom or Playwright tests | Too much weight for the amount of JavaScript involved (see 7.3). |

## 10. Risks and open points

- **Sparse tags.** Most archives will hold one post, and several posts will show no related posts. This is expected. A later editorial pass could merge near-duplicate tags (for example `ai-agents` and `agentic-ai`), but that is outside this lot.
- **TOC parsing** depends on Kramdown's HTML shape (`<h2 id="...">`). Changing the Markdown engine or turning off `auto_ids` would break it. The TOC anchor check in 7.2 catches this.
- **Slug consistency.** If a future tag contains capitals, spaces or accents, the `slugify` link and the jekyll-archives URL must still agree. The tag-link check in 7.2 catches any mismatch.
- **Reveal animation** combined with Show more (5.3) needs a browser check; static checks cannot see it.
- **Translation linking** depends on `translation_url` being exact. A typo would let a translation appear as a related post. The related-posts check in 7.2 covers the current pair.

## 11. Suggested implementation order

1. `jekyll-archives`, the tag archive layout, the `post-item.html` include, tag links, and the Python checks for archives and APOD exclusion.
2. `search.json`, the search page, the core and DOM scripts, and the Node tests.
3. Show more on `/blog/`.
4. The TOC include.
5. The related posts include.

Add the i18n strings, CSS, README updates and CI wiring alongside the step that needs them. Each step can ship as its own pull request. Steps 3, 4 and 5 do not depend on each other.
