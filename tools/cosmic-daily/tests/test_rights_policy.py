from __future__ import annotations

from cosmic_daily.rights_policy import evaluate_media_rights


def test_allows_nasa_image():
    decision = evaluate_media_rights("image", "NASA")
    assert decision.allowed is True
    assert decision.status == "allowed"


def test_routes_image_with_external_copyright_to_manual_review():
    decision = evaluate_media_rights("image", "Jane Photographer")
    assert decision.allowed is False
    assert decision.status == "manual_review"


def test_routes_missing_or_blank_copyright_to_manual_review():
    for copyright_value in (None, "", "   "):
        decision = evaluate_media_rights("image", copyright_value)
        assert decision.allowed is False
        assert decision.status == "manual_review"


def test_allows_explicit_nasa_public_domain_metadata():
    for copyright_value in ("NASA", "NASA / Public Domain", "Public domain"):
        decision = evaluate_media_rights("image", copyright_value)
        assert decision.allowed is True
        assert decision.status == "allowed"


def test_rejects_video():
    decision = evaluate_media_rights("video")
    assert decision.allowed is False
    assert decision.status == "unsupported_media"
