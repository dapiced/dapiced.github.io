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

    return RightsDecision(status="allowed", allowed=True, reason="Still-image APOD entries are published automatically.")
