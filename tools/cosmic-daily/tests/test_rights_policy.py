from __future__ import annotations

from cosmic_daily.rights_policy import UNATTRIBUTED_CREDIT, evaluate_media_rights


def test_allows_nasa_image():
    decision = evaluate_media_rights("image", "NASA")
    assert decision.allowed is True
    assert decision.status == "allowed"


def test_allows_image_with_third_party_credit():
    # Owner's choice (2026-10-11): third-party images are republished with credit.
    decision = evaluate_media_rights("image", "Jane Photographer")
    assert decision.allowed is True
    assert decision.status == "allowed"


def test_routes_missing_or_blank_copyright_to_manual_review():
    for copyright_value in (None, "", "   ", UNATTRIBUTED_CREDIT):
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


def test_allows_any_credited_still_image():
    # Real APOD credits from October 2026: photographers, agencies, mixed.
    for credit in (
        "Tom Williams",
        "NSF, B. Gudbjartsson, IceCube Collaboration",
        "ESA, CAS, SMILE, UVI",
        "NASA, ESA, STScI",
        "International Gemini Observatory/NOIRLab/NSF/AURA",
        "Copyright: John Entwistle",
    ):
        decision = evaluate_media_rights("image", credit)
        assert decision.status == "allowed", credit
        assert decision.allowed is True
