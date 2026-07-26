---
title: "TIL - Cache-busting CSS on GitHub Pages with site.time"
date: 2026-07-26
tags: [jekyll, github-pages, ci-cd]
---

Browsers cache stylesheets hard, and GitHub Pages has no asset pipeline to
fingerprint filenames. Result: you push a CSS change, the site rebuilds, and
half your visitors still see the old design.

The zero-dependency fix: append the build timestamp as a query string. Jekyll
exposes `site.time` (the moment the site was built), so every deploy mints a
fresh URL:

{% raw %}
```html
<link rel="stylesheet" href="/assets/css/style.css?v={{ site.time | date: '%s' }}">
```
{% endraw %}

The query string doesn't change the file served - it just makes the URL unique
per build, so caches treat it as a new resource. Same trick works for any
static asset that changes between deploys.

Ops reflex worth keeping: if you can't version the artifact, version the URL.
