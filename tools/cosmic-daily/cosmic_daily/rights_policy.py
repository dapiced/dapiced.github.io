from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RightsDecision:
    status: str
    allowed: bool
    reason: str


def evaluate_media_rights(media_type: str, copyright: Optional[str] = None) -> RightsDecision:
    normalized = (media_type or "").strip().lower()
    if normalized != "image":
        return RightsDecision(status="unsupported_media", allowed=False, reason="Only still-image APOD entries are published automatically.")

    credit = (copyright or "").strip().lower()
    if credit in {"nasa", "public domain", "nasa / public domain", "nasa/public domain"}:
        return RightsDecision(status="allowed", allowed=True, reason="APOD metadata identifies the image as NASA/public-domain material.")

    return RightsDecision(
        status="manual_review",
        allowed=False,
        reason="APOD rights metadata is missing, incomplete, or names a third-party copyright holder; manual rights review is required.",
    )
