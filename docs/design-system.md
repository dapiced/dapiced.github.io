# Design system

Direction: **mission control at night**. Dense but calm information, cold colours,
one warm light: Vincenzo's gold. References: astronomy and *Interstellar* (mission
screens, the father's signal across space and time). Nothing from the film itself
(images, fonts, quotes, music) is used.

## Themes

| Token | Night (default) | Dawn (`[data-theme="light"]`) | Use |
|---|---|---|---|
| `--bg` / `--bg2` | `#04060f` / `#0b1226` | `#f6f4ef` / `#e4ebf6` | page, sky gradient |
| `--panel` / `--panel-2` | `#0d1526` / `#101a30` | `#ffffff` / `#f3f1ea` | cards |
| `--border` | `#22304f` | `#d6d2c6` | lines |
| `--heading` / `--text` | `#e6edf3` / `#c9d1d9` | `#10151f` / `#1f2633` | text |
| `--muted` / `--faint` | `#8b949e` / `#6e7f9b` | `#4a5468` / `#566174` | secondary text |
| `--cyan` / `--lightblue` | `#58a6ff` / `#79c0ff` | `#0b5cad` / `#0a4f96` | links, signal |
| `--violet` | `#bc8cff` | `#6a3fb5` | secondary accent |
| `--gold` | `#e3b341` | `#8a5d00` | **Vincenzo only** |

- Colours with an alpha use `rgb(var(--rgb-…) / 0.5)`; no raw `rgba()` outside print.
- **Gold is reserved for Vincenzo D'Apice** (his star's coordinates, the dedication,
  the star tooltip, 12 September). `tests/test_design_system.py` enforces the list.
- Choice order: saved choice, then `prefers-color-scheme`, then Night.
  `assets/js/theme-init.js` runs before the first paint (no flash, no inline script,
  so the CSP needs no hash). At Dawn the stars fade out and only Vincenzo's star stays.
- Contrast is checked by axe in both themes on every page (`tools/site-checks/browser`).

## Typography (self-hosted, OFL, 79 KiB in total, budget 90 KiB)

| Role | Font | Where |
|---|---|---|
| Display | Archivo, pinned to Expanded width (wdth 125, wght 600–800, Latin subset) | hero, section and article titles |
| Text | IBM Plex Sans 400 / 600 | everything else |
| Instruments | IBM Plex Mono 400 | eyebrows, metadata, terminal lines |
| Vincenzo | Georgia italic (system) | motto and dedication |

Only Plex Sans 400 is preloaded. Archivo is subset with fontTools:
`fonttools varLib.instancer archivo-latin-wdth-normal.woff2 wdth=125 wght=600:800`
then `pyftsubset … --flavor=woff2` (Latin + French punctuation).

## Spacing and motion

- Spacing: 4 px base, `--space-1` (0.25 rem) to `--space-8` (4 rem).
- Motion: `--dur-fast` 120 ms (feedback), `--dur` 200 ms (UI), `--dur-slow` 480 ms
  (theme change, page transitions); easing `--ease`.
- Page transitions use the View Transitions API (`@view-transition`), a cross-fade
  ignored by browsers that do not support it.
- `prefers-reduced-motion: reduce` turns off transitions, the reveal animation, the
  twinkling and the shooting stars; a click on Vincenzo's star still plays its signal.
