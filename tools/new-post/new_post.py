#!/usr/bin/env python3
"""Create a blog post, or an EN/FR pair, ready to write.

The mechanical parts of a post are where things break: two files that must
point at each other (lang, translation_url, translation_label), a date that
must not be in the future (Jekyll silently skips future posts, which hid the
Prophet posts for a day), slugs, and tags that should reuse the existing ones.
This tool writes all of that, plus a skeleton with an "In brief" box whose
three bullets double as the LinkedIn post.

New posts start with `published: false`: placeholders can never go live by
accident. Remove that line when the post is ready (tests/test_posts.py also
refuses a published post that still holds a placeholder).

Usage (from the repository root):
    python tools/new-post/new_post.py --title-en "What I learned about XGBoost" \\
        --title-fr "Ce que j'ai appris sur XGBoost" --tags machine-learning,kaggle
    python tools/new-post/new_post.py --title-fr "Notes de terrain" --tags meta --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
POSTS = ROOT / "_posts"
MONTREAL = ZoneInfo("America/Toronto")

# Marks every line the author still has to write. A published post must not
# contain it (tests/test_posts.py).
PLACEHOLDER = "✍️ TODO"
MAX_SLUG = 60
MAX_DESCRIPTION = 160

LABELS = {
    # translation_label is shown on the OTHER language's page, in the language
    # of the version it links to.
    "en": {"label": "🇬🇧 Read this article in English", "brief": "In brief",
           "description": "one-sentence summary"},
    "fr": {"label": "🇫🇷 Lire cet article en français", "brief": "En bref",
           "description": "résumé en une phrase"},
}

SKELETON = {
    "en": """> **{brief}**
> - {todo} first takeaway, one line.
> - {todo} second takeaway.
> - {todo} third takeaway. These three bullets are the LinkedIn post.
{{: .in-brief }}

{todo} Opening: why this post, why now. One short paragraph.

## {todo} First section

{todo}

## What I take away

{todo}

## Sources

- {todo} link to the primary source.
""",
    "fr": """> **{brief}**
> - {todo} premier point à retenir, une ligne.
> - {todo} deuxième point.
> - {todo} troisième point. Ces trois puces font le post LinkedIn.
{{: .in-brief }}

{todo} Ouverture : pourquoi ce billet, pourquoi maintenant. Un court paragraphe.

## {todo} Première section

{todo}

## Ce que j'en retiens

{todo}

## Sources

- {todo} lien vers la source principale.
""",
}


@dataclass
class Post:
    lang: str
    title: str
    slug: str
    description: str

    def path(self, date: datetime) -> Path:
        return POSTS / f"{date:%Y-%m-%d}-{self.slug}.md"

    def url(self, date: datetime) -> str:
        # _config.yml: permalink: /blog/:year/:month/:title/
        return f"/blog/{date:%Y}/{date:%m}/{self.slug}/"


def slugify(title: str) -> str:
    """'Ce que j'ai appris sur Prophet' -> 'ce-que-jai-appris-sur-prophet'."""
    text = unicodedata.normalize("NFKD", title)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"['’`]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > MAX_SLUG:
        text = text[:MAX_SLUG].rsplit("-", 1)[0]
    return text


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def existing_tags() -> set[str]:
    tags: set[str] = set()
    for path in POSTS.glob("*.md"):
        tags.update(str(t) for t in front_matter(path).get("tags") or [])
    return tags


def default_date(now: datetime | None = None) -> datetime:
    # A few minutes in the past, in Montréal time: never a future post.
    now = now or datetime.now(MONTREAL)
    return (now - timedelta(minutes=5)).replace(second=0, microsecond=0)


def parse_date(value: str) -> datetime:
    date = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=MONTREAL)
    if date > datetime.now(MONTREAL):
        raise SystemExit(f"--date {value} is in the future: Jekyll would not publish the post.")
    return date


def render(post: Post, date: datetime, tags: list[str], image: str | None,
           other: Post | None, ready: bool) -> str:
    q = lambda value: json.dumps(value, ensure_ascii=False)  # YAML-safe double quotes
    lines = ["---", "layout: post", f"title: {q(post.title)}",
             f"date: {date:%Y-%m-%d %H:%M:%S %z}", f"lang: {post.lang}",
             f"tags: [{', '.join(tags)}]", f"description: {q(post.description)}"]
    if image:
        lines.append(f"image: {image}")
    if other:
        lines.append(f"translation_url: {other.url(date)}")
        lines.append(f"translation_label: {q(LABELS[other.lang]['label'])}")
    if not ready:
        lines.append("published: false  # remove this line to publish")
    lines.append("---")
    body = SKELETON[post.lang].format(brief=LABELS[post.lang]["brief"], todo=PLACEHOLDER)
    return "\n".join(lines) + "\n\n" + body


def build(args: argparse.Namespace) -> list[tuple[Path, str]]:
    if not (args.title_en or args.title_fr):
        raise SystemExit("Give --title-en, --title-fr or both.")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if not tags:
        raise SystemExit("Give at least one tag with --tags.")
    bad = [t for t in tags if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", t)]
    if bad:
        raise SystemExit(f"Tags are lowercase-with-dashes: {', '.join(bad)}")
    unknown = sorted(set(tags) - existing_tags())
    if unknown and not args.new_tag:
        raise SystemExit(
            f"Unknown tags: {', '.join(unknown)}. Reuse an existing one "
            f"({', '.join(sorted(existing_tags()))}) or pass --new-tag."
        )

    date = parse_date(args.date) if args.date else default_date()
    posts = []
    for lang in ("en", "fr"):
        title = getattr(args, f"title_{lang}")
        if not title:
            continue
        description = (getattr(args, f"description_{lang}")
                       or f"{PLACEHOLDER} {LABELS[lang]['description']}, {MAX_DESCRIPTION} max.")
        if len(description) > MAX_DESCRIPTION:
            print(f"warning: {lang} description is {len(description)} characters; "
                  f"search engines cut after about {MAX_DESCRIPTION}.", file=sys.stderr)
        slug = getattr(args, f"slug_{lang}") or slugify(title)
        if not slug:
            raise SystemExit(f"Cannot build a slug from {title!r}; pass --slug-{lang}.")
        posts.append(Post(lang, title, slug, description))

    if len(posts) == 2 and posts[0].slug == posts[1].slug:
        raise SystemExit("Both versions would share the same URL; give different titles or --slug-fr.")

    files = []
    for post in posts:
        other = next((p for p in posts if p is not post), None)
        path = post.path(date)
        taken = [p.name for p in POSTS.glob(f"*-{post.slug}.md")]
        if taken:
            raise SystemExit(f"A post already uses the slug {post.slug!r}: {', '.join(taken)}")
        files.append((path, render(post, date, tags, args.image, other, args.ready)))
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--title-en")
    parser.add_argument("--title-fr")
    parser.add_argument("--tags", required=True, help="comma-separated, e.g. machine-learning,kaggle")
    parser.add_argument("--description-en")
    parser.add_argument("--description-fr")
    parser.add_argument("--slug-en")
    parser.add_argument("--slug-fr")
    parser.add_argument("--image", help="e.g. /assets/img/xgboost/cover.jpg (JPEG or WebP gets a photo share card)")
    parser.add_argument("--date", help='"YYYY-MM-DD HH:MM", Montréal time; default: now')
    parser.add_argument("--new-tag", action="store_true", help="allow tags no post uses yet")
    parser.add_argument("--ready", action="store_true", help="do not add published: false")
    parser.add_argument("--dry-run", action="store_true", help="print the files instead of writing them")
    args = parser.parse_args(argv)

    files = build(args)
    for path, content in files:
        if args.dry_run:
            print(f"===== {path.relative_to(ROOT)}\n{content}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"created {path.relative_to(ROOT)}")
    if not args.dry_run:
        print("\nNext: write, remove `published: false`, then run "
              "`python tools/og-cards/og_cards.py` and commit the card with the post.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
