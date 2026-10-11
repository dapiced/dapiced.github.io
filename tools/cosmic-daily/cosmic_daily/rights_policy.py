from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Written as the credit when APOD gives none; read back by the validator as
# "no credit", never as a third-party name.
UNATTRIBUTED_CREDIT = "Rights metadata unavailable"


@dataclass(frozen=True)
class RightsDecision:
    status: str
    allowed: bool
    reason: str


def evaluate_media_rights(media_type: str, copyright: Optional[str] = None) -> RightsDecision:
    """Decide whether an APOD entry is published automatically.

    Owner's choice (2026-10-11): every still image is republished with its
    credit, third-party credits included, as on apod.nasa.gov itself. The one
    exception is a missing or blank credit: the entry could not attribute the
    image, so it stays in manual review.
    """
    normalized = (media_type or "").strip().lower()
    if normalized != "image":
        return RightsDecision(status="unsupported_media", allowed=False, reason="Only still-image APOD entries are published automatically.")

    credit = (copyright or "").strip()
    if credit and credit != UNATTRIBUTED_CREDIT:
        return RightsDecision(
            status="allowed",
            allowed=True,
            reason="Still-image APOD entries are republished with their credit.",
        )

    return RightsDecision(
        status="manual_review",
        allowed=False,
        reason="APOD credit is missing or blank, so the image cannot be attributed; manual review is required.",
    )
