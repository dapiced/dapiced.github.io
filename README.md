# dapiced.github.io

Personal site and blog of **Dominic D'Apice** - Developer, Azure Infrastructure AI.

**Live at [dominicdapice.com](https://dominicdapice.com/)** - custom domain (`CNAME`, DNS on Cloudflare), built with [Jekyll](https://jekyllrb.com/) on GitHub Pages, deep-space theme matching the [GitHub profile](https://github.com/dapiced).

## Writing a new blog post

The quickest way is the generator, which writes the file (or the linked EN/FR pair) with
a safe date, validated tags and an "In brief" box ready to fill
([`tools/new-post/README.md`](tools/new-post/README.md)):

```bash
python tools/new-post/new_post.py --title-en "What I learned about XGBoost" \
    --title-fr "Ce que j'ai appris sur XGBoost" --tags machine-learning,kaggle
```

By hand, add a Markdown file to `_posts/` named `YYYY-MM-DD-slug.md`:

```markdown
---
layout: post
title: "My post title"
date: 2026-07-15 09:00:00 -0400
tags: [azure, ansible]
description: "Search snippet, 120-160 characters - shown in Google results and social shares."
image: /assets/img/my-cover.jpg
---

Post content in Markdown…

![Descriptive alt text](/assets/img/my-photo.webp){: width="1600" height="1200" loading="lazy" }
```

- `description` and `image` are optional but recommended: `image` becomes the og:image
  social preview (JPG/PNG, ideally 1200x630 - falls back to `/assets/img/og-default.jpg`).
- Keep tags as lowercase hyphenated slugs; Jekyll generates a linked archive at
  `/blog/tag/<tag>/` for each authored-post tag.
- Use clear `##` and `###` sections in long posts; a server-rendered table of contents
  appears when a post has at least three such headings.
- Related posts use shared tags, prefer the same language and fall back to English; the
  section is omitted when no authored post shares a tag.
- Search authored posts at `/blog/search/`; the local index is generated at
  `/blog/search.json`. Tag archives remain available without JavaScript.
- The command palette (Ctrl K, ⌘K or `/` on any page) searches pages, posts, portfolio
  entries and Sky pictures through `/search-index.json`, and offers navigation, theme,
  language and `ping vincenzo`.
- Social share cards: after adding a post or changing its title, date or photo, run
  `python tools/og-cards/og_cards.py` and commit `assets/img/og/` (see
  [`tools/og-cards/README.md`](tools/og-cards/README.md); CI fails on a stale card).
- Photos: resize to ~1600 px max and convert to WebP before committing; always set
  `width`/`height` + `loading="lazy"` (the first image of a post can stay eager).
- Bilingual posts: publish two files (one per language) and cross-link them with
  `lang: fr|en`, `translation_url: /blog/YYYY/MM/other-slug/` and
  `translation_label: "🇬🇧 Read this article in English"` - the post layout renders
  the link under the title, exactly like the portfolio does. `lang: fr` also switches the
  page chrome to French (date, reading time, comments, giscus) and both pages get
  `hreflang` alternates. Posts with `lang: fr`
  are left out of the blog index, the topic pages and the homepage preview (they are
  reached through the English post's "version française" link, as in the portfolio);
  they still get their own URL and appear in `sitemap.xml` and `feed.xml`.

Push to `main` - the `pages.yml` workflow builds the site with the Gemfile and deploys it
to GitHub Pages in about a minute.

Renaming a published post changes its URL (`/blog/:year/:month/:title/` comes from the
file name). Keep the old address alive with `jekyll-redirect-from`:

```yaml
redirect_from:
  - /blog/2026/09/old-slug/
```

The plugin emits a redirect page at the old URL (kept out of `sitemap.xml`); update any
`translation_url` that pointed to the old slug.

## Structure

- `index.html` - homepage (hero, about, projects, skills, timeline, blog preview).
  Project cards are static HTML (indexable without JS) rendered from `_data/repos.json`,
  refreshed by workflow.
- `resume/index.html` - professional resume at `/resume/`. It renders experience and
  technical capabilities directly from `_data/timeline.yml` and `_data/skills.yml`,
  uses LinkedIn as the public contact path, and offers browser printing instead of a
  committed PDF.
- `blog/index.html` - post listing (all English posts remain in HTML for SEO and readers without JavaScript; JavaScript initially shows eight and provides a button to reveal the rest)
- `blog/search/` and `blog/search.json` - local search over authored post titles, excerpts and tags
- `sw.js` (service worker) + `offline/` and `fr/hors-ligne/` - offline support: pages
  already read stay available, unread ones fall back to "Signal lost"; checked by
  `tools/site-checks/browser/pwa-check.mjs`
- `search-index.json` + `assets/js/command-palette.js` - site-wide command palette,
  checked end to end by `tools/site-checks/browser/palette-check.mjs`
- `404.html` - custom not-found page
- `_posts/` - blog posts (Markdown)
- `_apod/` - daily NASA APOD entries (collection published under `/sky/`, own feed at `/feed/apod.xml`)
- `sky/index.html` (+ `fr/ciel/`) - "Montréal tonight" sky map (`assets/js/sky-map.js`,
  catalogue built by `tools/sky-map/build_catalog.py` from d3-celestial, BSD-3-Clause)
  and the image grid of the APOD entries
- `_portfolio/` - case studies (Markdown, `layout: portfolio`)
- `_layouts/` - page shells (`default.html` with Person JSON-LD and hreflang alternates,
  `post.html` / `portfolio.html` for articles)
- `_includes/` - shared fragments: `article-meta.html` (date, reading time, tags, translation
  link), `comments.html` (giscus), `mermaid.html`, `localized-date.html`, `topic-posts.html`
- `_data/i18n.yml` - interface strings in `en` and `fr`, picked by `page.lang`: the page chrome
  (navigation label, footer, theme and language buttons) and the article pages (dates,
  "min read", comments heading, giscus language, back links). French pages get the
  French chrome, a header switch to their `translation_url`, and `og:locale` `fr_CA`
  (`_plugins/page_locale.rb`); `tools/site-checks/check_i18n_generated.py` verifies it
- `_data/navigation.yml` - ordered header links (`label`, `label_fr`, `href`, and optional `class`,
  `target`, `rel`). Kept short on purpose (seven entries); secondary pages such as
  Projects, Resources and Contact live in the footer
- `_data/skills.yml` - ordered homepage skill groups (`domain` and an ordered `tags` list)
- `_data/timeline.yml` - ordered career entries (`year`, `role`, `description`). Together
  with `_data/skills.yml`, this is also the source of truth for `/resume/`; update these
  files rather than copying resume content into the page template.
- `_data/resources.yml` - ordered off-duty cards (`icon`, `title`, `description`, `href`,
  `more`)
- `assets/` - CSS, JS (starfield, typed roles, projects fetch), favicon, images, videos.
  `assets/icons/` holds the PNG app icons of the manifest; `assets/vendor/` holds
  third-party code served from this site (Mermaid, checksum-verified against the npm
  package, and GoatCounter's versioned `count.v5.js`) so no page depends on a CDN
- `_plugins/asset_digest.rb` - `{{ '/assets/css/style.css' | asset_digest }}` appends a
  hash of the file content (`?v=…`), so CSS and JS stay cached until they really change
- `_config.yml` - Jekyll config: canonical `url`, SEO/feed/sitemap plugins, default og:image, social links
- `tools/cosmic-daily/` - Python generator behind the daily APOD entries (excluded from the Jekyll build)
- `.github/workflows/` - automation, see below
- `.github/dependabot.yml` - weekly dependency updates (Actions, Bundler, pip)

The four homepage presentation files are validated with
`python tools/site-checks/validate_site_data.py`. Keep every list in display order and
preserve the navigation `target: _blank` / `rel: noopener` pair for external links.
After a Jekyll build, `python tools/site-checks/check_site_data_html.py` confirms that
the generated navigation, skills, timeline, and off-duty cards still match those files.

## Automation

- `production-health.yml` (weekly, Monday): checks the live site through Cloudflare
  (security headers, HTTPS redirect, service worker, search index, sky catalogue,
  share images; `tools/site-checks/check_production.py`) and runs Lighthouse on six
  real pages with GoatCounter and giscus loaded. A failure opens one
  "Production health" issue.

- **Cosmic Daily** (`cosmic-daily.yml`, daily at 12:00 UTC) fetches NASA's Astronomy Picture of
  the Day, converts the image to WebP, writes an entry in the `_apod/` collection (published under `/sky/`, kept out of the blog
  and its feed), opens a PR,
  validates it and squash-merges every credited still image, third-party credits included. An
  entry without a credit remains open for manual review; video days are skipped (the run
  summary says why), and a real failure opens an issue. Run it by hand from the Actions tab with
  a `date` to fill a gap.
  Each entry also gets a 640 px grid thumbnail in `assets/img/apod/thumbs/` (used by
  `/sky/` and the homepage card); `python -m cosmic_daily thumbnails` backfills missing ones.
  Details in [`tools/cosmic-daily/README.md`](tools/cosmic-daily/README.md).
- **Pages deployment** (`pages.yml`) builds the site with the Gemfile and publishes it on every
  push to `main`. The legacy GitHub Pages builder is pinned to Jekyll 3.x and ignores the
  Gemfile, so the plugin and Ruby versions were drifting from what runs locally. Blog tag
  archives depend on `jekyll-archives`, which is loaded through this Actions-based build.
- **CI** (`ci.yml`) runs on pull requests and on `main`: it builds the site, checks that the
  source contracts and generated pages remain valid, including `/now/`, checks that the pages
  the rest of the site links to exist (`/sky/`, both feeds, the sitemap, the 404 page, the
  `redirect_from` pages), and runs the Cosmic Daily test suite. It validates the `/now/`
  date but does not fail a pull request just because the page is older than the reminder
  threshold.
- **`/now/` freshness** (`now-freshness.yml`, monthly on the first day at 14:17 UTC) checks
  the exact `updated: YYYY-MM-DD` field with a 90-day threshold. When stale, it opens one
  stable `Refresh /now/ page` issue and does not comment on an existing issue. Run it
  manually from the Actions tab when you want an immediate check; update the page only after
  reviewing its durable public facts.
- **Quality gates** (in `ci.yml`, on every pull request): internal links with
  [lychee](https://lychee.cli.rs/) (offline), accessibility with axe-core (WCAG 2.2 A/AA,
  every sitemap page plus the 404, desktop and mobile; serious and critical issues fail),
  Lighthouse (median of 3 runs, thresholds in `tools/site-checks/browser/lighthouserc.json`)
  and a gitleaks scan of the whole history (reviewed false positives in `.gitleaksignore`).
  Run them locally after `bundle exec jekyll build`:
  `cd tools/site-checks/browser && npm ci && npx playwright install chromium && node axe-check.mjs && npx lhci autorun --config=lighthouserc.json`.
- **Preview** (`preview.yml`): every pull request is built and published to a separate
  Cloudflare Pages project (`https://pr-<n>.dominicdapice-preview.pages.dev`, noindex) and
  the PR gets a comment with the link. Production stays on GitHub Pages. Setup and token
  scope: [`docs/infra/cloudflare-preview.md`](docs/infra/cloudflare-preview.md).
- **External links** (`links-weekly.yml`, Mondays): checks every outbound link and opens a
  single "Broken external links" issue when some stop answering.
- **Dependabot** (`dependabot.yml`) opens weekly grouped PRs for the GitHub Actions, the
  Gemfile and the Cosmic Daily Python dependencies.
- **IndexNow** (`indexnow.yml`) submits every URL of the live sitemap to Bing once the Pages
  deployment has succeeded, so it reads the sitemap that was just published.

- **Analytics** uses GoatCounter as the sole counter provider. It receives page-view
  events without advertising profiles or a second analytics service; the site does not
  add tracking pixels or cross-site identity data.
- **License scope** is split deliberately: repository source code is MIT-licensed;
  authored writing, portfolio text, personal media, and branding remain all rights
  reserved unless a file says otherwise. Third-party assets keep their own licenses.

## SEO setup

- **Canonical domain** comes from `url:` in `_config.yml` - `jekyll-seo-tag` generates
  the canonical/og/twitter tags from it on every page.
- **`sitemap.xml` is not in the repo on purpose**: `jekyll-sitemap` generates it at build
  time with every page and post ([live here](https://dominicdapice.com/sitemap.xml)).
  Same for `feed.xml` (`jekyll-feed`).
- `robots.txt` - minimal allow-all + sitemap pointer. Never add `Disallow: /assets/`
  (it would hide CSS/JS/images from Google's renderer).
- `BingSiteAuth.xml` + `3678…d.txt` - Bing site verification and [IndexNow](https://www.indexnow.org/) key
  for instant URL submission to Bing.
- Google verification is a meta tag in `_layouts/default.html`.

## Design system

Night and Dawn themes, colour tokens, self-hosted fonts and motion rules are documented
in [`docs/design-system.md`](docs/design-system.md) and enforced by
`tests/test_design_system.py`.

## Editorial rules

- The author's current employer is never named on the site or in the repository;
  `tests/test_no_employer_mention.py` fails the build if it appears.
- Gold is reserved for references to Vincenzo D'Apice (his star, the dedication).

## Security headers

GitHub Pages cannot send custom headers; they are added by Cloudflare in front of the
site. The step-by-step setup and the tested Content-Security-Policy are in
[`docs/infra/cloudflare-phase0.md`](docs/infra/cloudflare-phase0.md). Do not add inline
`<script>` blocks or third-party script hosts without updating that policy.
