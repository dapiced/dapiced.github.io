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


def test_allows_credits_made_only_of_nasa_centers_and_mission_partners():
    # Real APOD credits from October 2026.
    for credit in (
        "NASA / GSFC / Arizona State Univ. / Lunar Reconnaissance Orbiter",
        "HiRISE, MRO, LPL (U. Arizona), NASA",
        "NASA, JPL-Caltech",
        "Image Credit: NASA, JPL-Caltech, MSSS",
    ):
        decision = evaluate_media_rights("image", credit)
        assert decision.status == "allowed", credit
        assert decision.allowed is True


def test_keeps_any_non_nasa_name_in_manual_review():
    # Real APOD credits from October 2026, plus mixed NASA/partner credits.
    for credit in (
        "Tom Williams",
        "Neelam and Ajay Talwar",
        "ESA, CAS, SMILE, UVI",
        "NASA, ESA, STScI",
        "International Gemini Observatory/NOIRLab/NSF/AURA",
        "Image Credit: NASA, JPL-Caltech, MSSS - Panorama: Andrew Bodrov",
    ):
        decision = evaluate_media_rights("image", credit)
        assert decision.status == "manual_review", credit
        assert decision.allowed is False


def test_copyright_or_license_mention_is_never_auto_published():
    for credit in ("Copyright: NASA", "NASA © 2026", "NASA (license: CC BY 4.0)"):
        assert evaluate_media_rights("image", credit).status == "manual_review", credit
