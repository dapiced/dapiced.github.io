from __future__ import annotations

from cosmic_daily.rights_policy import evaluate_media_rights


def test_allows_nasa_image():
    decision = evaluate_media_rights("image", "NASA")
    assert decision.allowed is True
    assert decision.status == "allowed"


def test_rejects_external_copyright():
    decision = evaluate_media_rights("image", "Jane Photographer")
    assert decision.allowed is False
    assert decision.status == "review_required"


def test_rejects_video():
    decision = evaluate_media_rights("video")
    assert decision.allowed is False
    assert decision.status == "unsupported_media"
