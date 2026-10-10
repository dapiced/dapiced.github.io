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

- `preview` generates and validates only in a temporary directory and never touches tracked files.
  Third-party, missing, or blank rights metadata is reported as manual review and still exits 0.
  Preview-only runs do not open failure issues.
- `generate` writes `_apod/YYYY-MM-DD-slug.md` and the corresponding WebP image for an
  explicitly allowed image or for a validated manual-review candidate.
  The entry stays factual: title, date, credit, NASA's explanation and the source link. An optional
  `note:` field can be added by hand to the front matter; the generator never writes it. Missing or
  blank rights metadata is preserved as `Rights metadata unavailable`, never rewritten as NASA.
- Old entries were migrated from `_posts/`; their former `/blog/...` URLs redirect through
  `redirect_from`. Duplicate detection still scans both folders.
- `check` validates front matter and image references for a generated article.
- Video entries are skipped, not failed: `preview` and `generate` print `Skipped: …` and exit 0,
  and the workflow records the reason in the run summary. Publishing a video day stays a manual
  decision.
- APOD moved to `science.nasa.gov` in autumn 2026, and `api.nasa.gov` now answers some days with
  placeholder data (title `NASA Science`, the NASA logo as image). When that happens the entry is
  read from `https://science.nasa.gov/apod/?date=YYMMDD` instead: title, explanation (without the
  "Tomorrow's picture" footer), credit line and image from the APOD media library. The credit is
  passed to the rights policy unchanged. If the page is for another date or its title, image or credit cannot be found, the
  day is skipped with `Skipped: APOD entry unavailable (...)` and exit 0, like a video day.
- The image is fetched from `hdurl` first, then from `url` when the HD file answers 403/404 or
  cannot fit the size budget; the command fails only when every candidate fails.
- PRs and merges made with the default `GITHUB_TOKEN` fire no workflow, so the job dispatches
  `ci.yml` on the generated PR branch and waits for it (a red CI stops the run before any merge),
  then dispatches `pages.yml` on `main` after an auto-merge so the entry is actually deployed.
  GitHub still creates an empty `pull_request` CI run for the bot's PR that never starts a job and
  turns red once the branch is deleted; the job cancels and deletes it (cosmetic, never blocking).
- The repository workflow dispatch action supports `publish=false` for preview-only runs and `publish=true` to generate a branch and PR.
- Scheduled runs auto-merge only explicit NASA/public-domain rights metadata accepted by the
  rights policy: a credit is accepted when every part of it (split on `/`, `,`, `;`, `&`, `and`,
  ` - `) is NASA, a NASA center, or a listed NASA mission partner such as JPL-Caltech, GSFC, MSSS,
  ASU/LRO or HiRISE/LPL (`NASA_CREDIT_PARTS` in `rights_policy.py`). Any other name, or any mention
  of copyright or a license, keeps the entry in manual review. Validated manual-review candidates remain open in a PR and are never auto-merged.
  Invalid images or content still fail and open an issue titled
  `Cosmic Daily: echec le YYYY-MM-DD`; a re-run of the same day comments on the existing open
  issue instead of creating another one.
