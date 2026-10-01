# Cosmic Daily

Cosmic Daily generates a daily NASA APOD entry for the site's `_apod/` collection (published under `/sky/`) while respecting the project’s conventions and safety checks.

## Local setup

```bash
cd tools/cosmic-daily
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .[dev]
```

Create a local `.env` file from `.env.example` and set `NASA_API_KEY`.

For the GitHub Actions publishing flow, add the same value as a repository secret named
`NASA_API_KEY_OFFICIAL` (the name the `Cosmic Daily` workflow reads) in the repository settings.

## Commands

```bash
python -m cosmic_daily preview
python -m cosmic_daily generate
python -m cosmic_daily check
```

The default mode is `preview`.

## Notes

- `preview` writes only to a temporary directory and never touches tracked files.
- `generate` writes `_apod/YYYY-MM-DD-slug.md` and the corresponding WebP image when the media is eligible.
  The entry stays factual: title, date, credit, NASA's explanation and the source link. An optional
  `note:` field can be added by hand to the front matter; the generator never writes it.
- Old entries were migrated from `_posts/`; their former `/blog/...` URLs redirect through
  `redirect_from`. Duplicate detection still scans both folders.
- `check` validates front matter and image references for a generated article.
- Video entries are skipped, not failed: `preview` and `generate` print `Skipped: …` and exit 0,
  and the workflow records the reason in the run summary. Publishing a video day stays a manual
  decision.
- The image is fetched from `hdurl` first, then from `url` when the HD file answers 403/404 or
  cannot fit the size budget; the command fails only when every candidate fails.
- The repository workflow dispatch action supports `publish=false` for preview-only runs and `publish=true` to generate a branch and PR.
- Scheduled runs open a PR, validate it and squash-merge it automatically. A failure opens an
  issue titled `Cosmic Daily: echec le YYYY-MM-DD`; a re-run of the same day comments on the
  existing open issue instead of creating another one.
