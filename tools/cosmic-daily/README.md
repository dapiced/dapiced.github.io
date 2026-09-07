# Cosmic Daily

Cosmic Daily generates a daily NASA APOD article for this Jekyll blog while respecting the project’s conventions and safety checks.

## Local setup

```bash
cd tools/cosmic-daily
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .[dev]
```

Create a local `.env` file from `.env.example` and set `NASA_API_KEY`.

For the GitHub Actions publishing flow, add the same value as a repository secret named `NASA_API_KEY` in the repository settings before enabling the manual `Cosmic Daily` workflow.

## Commands

```bash
python -m cosmic_daily preview
python -m cosmic_daily generate
python -m cosmic_daily check
```

The default mode is `preview`.

## Notes

- `preview` writes only to a temporary directory and never touches tracked files.
- `generate` creates a Jekyll post and the corresponding WebP image when the media is eligible.
- `check` validates front matter and image references for a generated article.
- Video entries and external-copyright cases are treated as human review only.
- The repository workflow dispatch action supports `publish=false` for preview-only runs and `publish=true` to generate a branch and PR.
