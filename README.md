# dapiced.github.io

Personal site and blog of **Dominic D'Apice** -Developer, Azure Infrastructure AI.

**Live at [dapiced.github.io](https://dapiced.github.io)** built with [Jekyll](https://jekyllrb.com/) on GitHub Pages, deep-space theme matching the [GitHub profile](https://github.com/dapiced).

## Writing a new blog post

Add a Markdown file to `_posts/` named `YYYY-MM-DD-slug.md`:

```markdown
---
layout: post
title: "My post title"
date: 2026-07-15 09:00:00 -0400
tags: [azure, ansible]
---

Post content in Markdown…
```

Push to `main` -GitHub Pages rebuilds and publishes automatically in about a minute.

## Structure

- `index.html` -homepage (hero, about, live projects via GitHub API, skills, timeline, blog preview)
- `blog/index.html` -post listing
- `_posts/` -blog posts (Markdown)
- `_layouts/` -page shells (`default.html`, `post.html`)
- `assets/` -CSS, JS (starfield, typed roles, projects fetch), favicon
- `_config.yml` -Jekyll config (SEO, feed, sitemap plugins)
