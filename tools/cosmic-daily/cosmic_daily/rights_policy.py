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

    Owner's choice (2026-10-16): a video entry follows the same rule. Only one
    frame of the video is republished, with the video credit, and it links to
    the video on NASA's page; the video itself is never copied.

    Owner's choice (2026-10-18): a YouTube video follows the same rule, with
    its YouTube thumbnail as the one picture.
    """
    normalized = (media_type or "").strip().lower()
    if normalized not in {"image", "video"}:
        return RightsDecision(status="unsupported_media", allowed=False, reason="Only still-image and video APOD entries are published automatically.")

    credit = (copyright or "").strip()
    if credit and credit != UNATTRIBUTED_CREDIT:
        return RightsDecision(
            status="allowed",
            allowed=True,
            reason="APOD entries are republished with their credit (a video as one frame linking to NASA).",
        )

    return RightsDecision(
        status="manual_review",
        allowed=False,
        reason="APOD credit is missing or blank, so the entry cannot be attributed; manual review is required.",
    )
