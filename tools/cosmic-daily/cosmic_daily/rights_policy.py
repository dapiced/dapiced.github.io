from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RightsDecision:
    status: str
    allowed: bool
    reason: str


# Credit parts that identify NASA itself, its centers, or the operators and
# instruments of NASA missions whose imagery NASA releases for reuse with
# credit. A credit is published automatically only when EVERY part of it is in
# this list; any other name (a photographer, ESA, NOIRLab, an observatory...)
# keeps the entry in manual review. Compared lower-case, after splitting the
# credit on "/", ",", ";", "&", " and " and " - ".
NASA_CREDIT_PARTS = frozenset(
    {
        "nasa",
        "public domain",
        # Centers and laboratories.
        "gsfc",
        "nasa gsfc",
        "goddard space flight center",
        "nasa's goddard space flight center",
        "jpl",
        "jpl-caltech",
        "nasa jpl",
        "caltech",
        "msfc",
        "jsc",
        "ksc",
        "nasa ames",
        "ames research center",
        "jhuapl",
        "johns hopkins apl",
        "stsci",
        # Mission operators and instruments.
        "msss",
        "malin space science systems",
        "arizona state univ.",
        "arizona state university",
        "asu",
        "lunar reconnaissance orbiter",
        "lro",
        "lroc",
        "hirise",
        "mro",
        "lpl (u. arizona)",
        "lpl",
        "u. arizona",
        "university of arizona",
        "swri",
        "southwest research institute",
    }
)
CREDIT_PREFIX = re.compile(r"^\s*(?:image\s+)?credit\s*:\s*", re.IGNORECASE)
CREDIT_SEPARATORS = re.compile(r"\s*(?:[/,;&]|\s-\s|\band\b)\s*", re.IGNORECASE)
# A credit that mentions copyright or a license is never auto-published, even
# when every name in it looks like NASA.
COPYRIGHT_MARKERS = re.compile(r"copyright|©|\(c\)|licen[cs]e", re.IGNORECASE)


def _is_nasa_credit(credit: str) -> bool:
    if COPYRIGHT_MARKERS.search(credit):
        return False
    stripped = CREDIT_PREFIX.sub("", credit)
    parts = [part.strip().lower() for part in CREDIT_SEPARATORS.split(stripped)]
    parts = [part for part in parts if part]
    return bool(parts) and all(part in NASA_CREDIT_PARTS for part in parts)


def evaluate_media_rights(media_type: str, copyright: Optional[str] = None) -> RightsDecision:
    normalized = (media_type or "").strip().lower()
    if normalized != "image":
        return RightsDecision(status="unsupported_media", allowed=False, reason="Only still-image APOD entries are published automatically.")

    credit = (copyright or "").strip()
    if _is_nasa_credit(credit):
        return RightsDecision(
            status="allowed",
            allowed=True,
            reason="APOD credit names only NASA, its centers, or NASA mission partners.",
        )

    return RightsDecision(
        status="manual_review",
        allowed=False,
        reason="APOD rights metadata is missing, incomplete, or names a third-party copyright holder; manual rights review is required.",
    )
