# Site Data Migration Design (E2)

- **Status:** implementation completed and validated in PR #87; PR remains open and unmerged
- **Date:** 2026-10-01
- **Scope:** design only. This document defines the E2 data extraction for the homepage and global navigation without altering the hero, About section, animated roles, or the rest of E1/E3/E4 work.

## 1. Objective

Move the static presentation values that are currently hard-coded in the homepage and the main navigation into four dedicated YAML data files while keeping the rendered HTML and behavior identical. The approved E2 scope is intentionally narrow:

1. Extract navigation labels, URLs, CSS classes, and external-link attributes into `_data/navigation.yml`.
2. Extract the skill groups and tags into `_data/skills.yml`.
3. Extract the timeline rows into `_data/timeline.yml`.
4. Extract the off-duty resource cards into `_data/resources.yml`.
5. Replace the corresponding HTML blocks with Liquid loops that keep the exact order, labels, URLs, classes, and accessibility behavior.

The design deliberately excludes the hero, About copy, typed roles, project cards, blog preview, and any broader redesign work.

## 2. Non-goals

- Any redesign of typography, spacing, or layout outside the exact data extraction scope.
- Changing the hero, mission statement, or animated role logic.
- Moving the project cards, blog preview, or any data already sourced from APIs or Jekyll collections.
- Editing E1, E3, or E4 work beyond the E2 data layer.
- Adding new pages or changing URLs.

## 3. Current state

The site uses a Jekyll build with `_data/` as the source of truth for structured presentation values. The homepage and the main navigation currently embed the labels and markdown-specific markup directly in HTML, creating duplication in the template and making copy updates harder. The accepted fix is to move only the data that is currently printed verbatim into YAML and keep the same HTML structure and CSS classes around it.

The current page already exposes the exact structure we need to preserve:

- top-level navigation is a list of anchors in `_layouts/default.html`
- skills are grouped rows with `.skill-row` and `.tag` spans in `index.html`
- timeline items are `.tl-item` entries with year, role, and description in `index.html`
- beyond/off-duty cards are `.beyond-card` entries in `index.html`

The design keeps those exact semantics and the current attribute behavior (`target`, `rel`, `aria-label`, `aria-controls`, etc.) while moving the values into YAML.

## 4. Shared definitions

**Navigation item:** one anchor in the site header.

**Skill group:** one row under the skills section with a domain label and a list of tags.

**Timeline item:** one timeline record with year, role, and description.

**Resource card:** one off-duty card with icon, title, description, destination link, and CTA label.

## 5. Data contracts

### 5.1 `_data/navigation.yml`

A list of navigation items, in the exact current order. Each item contains:

- `label`: visible text rendered in the anchor
- `href`: destination URL
- `class`: empty string or a CSS class such as `nav-labml` or `nav-gh`
- `target`: optional `"_blank"`
- `rel`: optional `"noopener"` for external links

This file powers the header nav but does not change the overall layout or menu behavior.

### 5.2 `_data/skills.yml`

A list of groups, in the current display order. Each group contains:

- `domain`: visible label such as `Cloud & Data`
- `tags`: ordered list of tag labels

The output remains one `.skill-row` with `.skill-domain` and `.tag` spans in the exact same order.

### 5.3 `_data/timeline.yml`

A list of timeline entries, in the current timeline order. Each entry contains:

- `year`: string shown in the left column
- `role`: string shown as the role title
- `description`: string shown as the descriptive copy

The output remains one `.tl-item` with `.tl-year`, `.tl-role`, and `.tl-desc` text in the same order.

### 5.4 `_data/resources.yml`

A list of off-duty cards, in the current order. Each card contains:

- `icon`: emoji shown in the card header
- `title`: card title
- `description`: descriptive paragraph
- `href`: destination page or section
- `more`: CTA label shown at the bottom of the card

The output remains one `.beyond-card` anchor with the existing CSS classes and same text.

## 6. Rendering rules

- Preserve the exact HTML structure and class names already in use.
- Keep the current order of entries exactly as authored.
- Preserve `target="_blank"` and `rel="noopener"` only where the current markup has them.
- Preserve `aria-label` and other accessibility attributes already present on the menu and links.
- Keep the existing `nav-toggle` and mobile menu behavior untouched.
- Use Liquid loops only for the values moved into YAML; do not rewrite unrelated template logic.
- Keep the visual design unchanged by reusing the same classes, wrappers, and text.

## 7. Validation requirements

A static validation layer will guard the data and prevent data drift:

- all four YAML files exist and load cleanly
- each file matches the expected schema for its content type
- every required field is present
- list item order is preserved as authored
- external links include the expected `target` and `rel` values
- the off-duty cards, skill tags, and timeline entries remain in the intended order

The validation should be runnable as a Python script and covered by a focused pytest file. It is a fast safety check, not a replacement for the Jekyll build.

## 8. Acceptance criteria

The E2 work is complete when all of the following are true:

- `_data/navigation.yml`, `_data/skills.yml`, `_data/timeline.yml`, and `_data/resources.yml` exist and reflect the current published content.
- The navigation, skills rows, timeline items, and off-duty cards render from Liquid loops without changing any labels or order.
- All current CSS classes and external-link behavior remain intact.
- The generated HTML still includes the same anchor text, URLs, and accessibility attributes.
- Static validation passes for the YAML schema and data integrity.
- The Python test suite passes.
- The Jekyll build succeeds and the generated pages still render correctly.

## 9. Implementation notes

This migration is intentionally narrow and data-only. The approved fix is not a site redesign and should not introduce new template abstractions beyond the minimal Liquid loops required by E2.
