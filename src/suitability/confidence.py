"""
suitability.confidence — deterministic confidence and diagnostics helpers.
"""

from __future__ import annotations

from typing import Dict, List

from .models import ActivityDefinition, SuitabilityContext


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp a value between [minimum, maximum]."""
    return max(minimum, min(maximum, value))


def compute_confidence(field_confidence: Dict[str, float]) -> float:
    """
    Compute confidence as weighted mean of provided field confidences.

    Empty confidence maps return 0.0 to make missing signal explicit.
    """
    if not field_confidence:
        return 0.0
    values = [clamp(v) for v in field_confidence.values()]
    return round(sum(values) / len(values), 4)


def collect_missing_signals(
    activity: ActivityDefinition,
    context: SuitabilityContext,
) -> List[str]:
    """Return deterministic missing-signal diagnostics."""
    missing: List[str] = []

    if activity.duration_hours is None:
        missing.append("duration_hours")
    if activity.intensity not in {"light", "moderate", "high", "extreme"}:
        missing.append("intensity")
    if activity.min_age is None and activity.max_age is None:
        missing.append("age_bounds")
    if not activity.tags:
        missing.append("tags")
    if not context.destination_keys:
        missing.append("destination_keys")

    return missing

