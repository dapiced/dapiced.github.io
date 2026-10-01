from __future__ import annotations

from cosmic_daily.article_generator import generate_article
from cosmic_daily.nasa_client import APODRecord


def _apod(**overrides) -> APODRecord:
    values = dict(
        date="2024-03-15",
        title="A Fine Example",
        media_type="image",
        url="https://example.com/image.jpg",
        hdurl="https://example.com/image-hd.jpg",
        explanation="Example explanation for the APOD article.",
        copyright="Jane Photographer",
        apod_url="https://apod.nasa.gov/apod/ap20240315.html",
    )
    values.update(overrides)
    return APODRecord(**values)


def test_generate_article_includes_required_fields():
    front_matter, article = generate_article(_apod(), "/assets/img/apod/2024-03-15-a-fine-example.webp", 1200, 800)
    assert "layout: apod\n" in front_matter
    assert 'title: "A Fine Example"' in front_matter
    assert "date: 2024-03-15 08:00:00 -0400" in front_matter
    assert "tags: [astronomy, nasa, apod]" in front_matter
    assert "image: /assets/img/apod/2024-03-15-a-fine-example.webp" in front_matter
    assert "image_width: 1200" in front_matter
    assert "image_height: 800" in front_matter
    assert 'credit: "Jane Photographer"' in front_matter
    assert "apod_date: 2024-03-15" in front_matter
    assert 'apod_url: "https://apod.nasa.gov/apod/ap20240315.html"' in front_matter
    assert "generated_by: cosmic-daily" in front_matter
    assert article.startswith(front_matter)
    assert "Example explanation for the APOD article." in article


def test_generate_article_is_factual_without_boilerplate_or_note():
    _, article = generate_article(_apod(), "/assets/img/apod/x.webp", 1200, 800)
    assert "Why it caught my attention" not in article
    assert "Each day, the NASA APOD archive" not in article
    assert "APOD:" not in article
    # The personal note is optional and only ever written by a human.
    assert "note:" not in article


def test_generate_article_keeps_full_explanation():
    long_text = " ".join(["word"] * 400)
    _, article = generate_article(_apod(explanation=long_text), "/assets/img/apod/x.webp", 1200, 800)
    assert long_text in article
    assert "..." not in article


def test_generate_article_preserves_missing_rights_as_manual_review():
    front_matter, _ = generate_article(
        _apod(title='The "Pillars" Again', copyright=None), "/assets/img/apod/x.webp", 1200, 800
    )
    assert 'title: "The \\"Pillars\\" Again"' in front_matter
    assert 'credit: "Rights metadata unavailable"' in front_matter
    assert "rights_status: manual_review" in front_matter
    assert 'credit: "NASA"' not in front_matter
