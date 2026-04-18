"""
suitability.scoring — Tier 1 deterministic activity suitability scorer.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .confidence import collect_missing_signals, compute_confidence
from .models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    SuitabilityContext,
)

TIER_ORDER = ["exclude", "discourage", "neutral", "recommend", "strong_recommend"]
TIER_SCORE = {
    "exclude": 0.0,
    "discourage": 0.3,
    "neutral": 0.5,
    "recommend": 0.75,
    "strong_recommend": 0.9,
}

TAG_RULES: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("water_based", "toddler"): ("exclude", "Water-based activity is unsafe for toddlers."),
    ("height_required", "toddler"): (
        "exclude",
        "Height-based participation restriction excludes toddler cohort.",
    ),
    ("physical_intense", "elderly"): (
        "discourage",
        "Physical intensity may create strain for elderly travelers.",
    ),
    ("walking_heavy", "elderly"): (
        "discourage",
        "Walking-heavy activity may not suit elderly mobility profile.",
    ),
    ("seated_show", "toddler"): (
        "recommend",
        "Seated, low-demand activity generally fits toddler-friendly pacing.",
    ),
}


def _tier_rank(tier: str) -> int:
    return TIER_ORDER.index(tier)


def _pick_most_conservative_tier(tiers: List[str]) -> str:
    """Pick the lowest tier when multiple rules fire."""
    if not tiers:
        return "neutral"
    return sorted(tiers, key=_tier_rank)[0]


def evaluate_activity(
    activity: ActivityDefinition,
    participant: ParticipantRef,
    context: SuitabilityContext,
) -> ActivitySuitability:
    """
    Tier 1 deterministic suitability evaluation for one activity/participant pair.
    """
    hard_exclusions: List[str] = []
    warnings: List[str] = []
    fired_tiers: List[str] = []
    score_components: Dict[str, float] = {}

    if participant.age is not None and activity.min_age is not None and participant.age < activity.min_age:
        hard_exclusions.append(
            f"Participant age {participant.age} is below minimum age {activity.min_age}."
        )
    if participant.age is not None and activity.max_age is not None and participant.age > activity.max_age:
        hard_exclusions.append(
            f"Participant age {participant.age} exceeds maximum age {activity.max_age}."
        )

    for tag in activity.tags:
        rule = TAG_RULES.get((tag, participant.label))
        if not rule:
            continue
        tier, reason = rule
        fired_tiers.append(tier)
        if tier == "exclude":
            hard_exclusions.append(reason)
        else:
            warnings.append(reason)
        score_components[f"tag::{tag}"] = TIER_SCORE[tier]

    if hard_exclusions:
        tier = "exclude"
    else:
        tier = _pick_most_conservative_tier(fired_tiers)

    score = TIER_SCORE[tier]

    field_confidence = {
        "intensity": 0.95 if activity.intensity in {"light", "moderate", "high", "extreme"} else 0.4,
        "age_bounds": 0.95 if activity.min_age is not None or activity.max_age is not None else 0.6,
        "tags": 0.8 if activity.tags else 0.0,
        "duration": 0.8 if activity.duration_hours is not None else 0.0,
    }
    confidence = compute_confidence(field_confidence)
    missing_signals = collect_missing_signals(activity, context)

    return ActivitySuitability(
        activity_id=activity.activity_id,
        participant=participant,
        compatible=tier != "exclude",
        score=score,
        confidence=confidence,
        tier=tier,
        hard_exclusion_reasons=hard_exclusions,
        warnings=warnings,
        score_components=score_components,
        missing_signals=missing_signals,
        scorer_id="heuristic_v1",
        scorer_version="1",
        source="rule",
    )

