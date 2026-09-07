from __future__ import annotations

from cosmic_daily.article_generator import generate_article
from cosmic_daily.nasa_client import APODRecord


def test_generate_article_includes_required_fields():
    apod = APODRecord(
        date="2024-03-15",
        title="A Fine Example",
        media_type="image",
        url="https://example.com/image.jpg",
        hdurl="https://example.com/image-hd.jpg",
        explanation="Example explanation for the APOD article.",
        copyright="Jane Photographer",
        apod_url="https://apod.nasa.gov/apod/ap20240315.html",
    )

    front_matter, article = generate_article(apod, "/assets/img/apod/2024-03-15-a-fine-example.webp", 1200, 800)
    assert "title: \"APOD: A Fine Example\"" in front_matter
    assert "tags: [astronomy, nasa, apod]" in front_matter
    assert "apod_date: 2024-03-15" in front_matter
    assert 'apod_url: "https://apod.nasa.gov/apod/ap20240315.html"' in front_matter
    assert "generated_by: cosmic-daily" in front_matter
    assert "Why it caught my attention" in article
    assert "Jane Photographer" in article
    assert "https://apod.nasa.gov/apod/ap20240315.html" in article
