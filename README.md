# dapiced.github.io

Personal site and blog of **Dominic D'Apice** - Developer, Azure Infrastructure AI.

**Live at [dominicdapice.com](https://dominicdapice.com/)** - custom domain (`CNAME`, DNS on Cloudflare), built with [Jekyll](https://jekyllrb.com/) on GitHub Pages, deep-space theme matching the [GitHub profile](https://github.com/dapiced).

## Writing a new blog post

Add a Markdown file to `_posts/` named `YYYY-MM-DD-slug.md`:

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
- Photos: resize to ~1600 px max and convert to WebP before committing; always set
  `width`/`height` + `loading="lazy"` (the first image of a post can stay eager).

Push to `main` - GitHub Pages rebuilds and publishes automatically in about a minute.

## Structure

- `index.html` - homepage (hero, about, projects, skills, timeline, blog preview).
  Project cards are static HTML (indexable without JS) refreshed live from the GitHub API.
- `blog/index.html` - post listing
- `404.html` - custom not-found page
- `_posts/` - blog posts (Markdown)
- `_layouts/` - page shells (`default.html` with Person JSON-LD, `post.html` with giscus comments + mermaid)
- `assets/` - CSS, JS (starfield, typed roles, projects fetch), favicon, images, videos
- `_config.yml` - Jekyll config: canonical `url`, SEO/feed/sitemap plugins, default og:image, social links

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
