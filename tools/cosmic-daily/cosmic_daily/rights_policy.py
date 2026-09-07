from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RightsDecision:
    status: str
    allowed: bool
    reason: str


def _looks_like_nasa_credit(value: str) -> bool:
    upper = value.upper()
    return "NASA" in upper or "APOD" in upper or "JPL" in upper or "SPACE TELESCOPE" in upper


def evaluate_media_rights(media_type: str, copyright: Optional[str] = None) -> RightsDecision:
    normalized = (media_type or "").strip().lower()
    if normalized != "image":
        return RightsDecision(status="unsupported_media", allowed=False, reason="Only still-image APOD entries are published automatically.")

    if copyright is None or not str(copyright).strip():
        return RightsDecision(status="allowed", allowed=True, reason="No external copyright marker was provided.")

    credit = str(copyright).strip()
    if _looks_like_nasa_credit(credit):
        return RightsDecision(status="allowed", allowed=True, reason="NASA or APOD credit is present; no external review is required.")

    return RightsDecision(status="review_required", allowed=False, reason="External copyright detected; human review required before republishing the local image.")
