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
    ("seated_show", "elderly"): (
        "recommend",
        "Seated activity is well-suited for elderly travelers.",
    ),
    ("cultural", "toddler"): (
        "discourage",
        "Cultural activities may not engage toddlers.",
    ),
    ("cultural", "elderly"): (
        "recommend",
        "Cultural activities are generally suitable for elderly travelers.",
    ),
    ("water_based", "elderly"): (
        "discourage",
        "Water-based activities may pose challenges for elderly travelers.",
    ),
    ("height_required", "elderly"): (
        "discourage",
        "Height-based activities may not be suitable for elderly travelers.",
    ),
}


def _tier_rank(tier: str) -> int:
    return TIER_ORDER.index(tier)


def _pick_most_conservative_tier(tiers: List[str]) -> str:
    """Pick the lowest tier when multiple rules fire."""
    if not tiers:
        return "neutral"
    return sorted(tiers, key=_tier_rank)[0]


def _downgrade_tier(current_tier: str) -> str:
    """Downgrade tier by one level."""
    index = TIER_ORDER.index(current_tier)
    if index == 0:
        return current_tier
    return TIER_ORDER[index - 1]


def _upgrade_tier(current_tier: str) -> str:
    """Upgrade tier by one level."""
    index = TIER_ORDER.index(current_tier)
    if index == len(TIER_ORDER) - 1:
        return current_tier
    return TIER_ORDER[index + 1]


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

    # Age-based exclusions
    if participant.age is not None and activity.min_age is not None and participant.age < activity.min_age:
        hard_exclusions.append(
            f"Participant age {participant.age} is below minimum age {activity.min_age}."
        )
    if participant.age is not None and activity.max_age is not None and participant.age > activity.max_age:
        hard_exclusions.append(
            f"Participant age {participant.age} exceeds maximum age {activity.max_age}."
        )

    # Weight-based exclusions (if weight is available in participant metadata)
    participant_weight = participant.metadata.get("weight_kg") if hasattr(participant, "metadata") else None
    if participant_weight is not None and activity.max_weight_kg is not None:
        if participant_weight > activity.max_weight_kg:
            hard_exclusions.append(
                f"Participant weight {participant_weight}kg exceeds maximum weight {activity.max_weight_kg}kg."
            )

    # Tag-based rules
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

    # Intensity-based scoring
    intensity_scores = {
        "light": 0.9,
        "moderate": 0.7,
        "high": 0.4,
        "extreme": 0.2,
    }
    
    # Adjust intensity score based on participant type
    if participant.label == "elderly":
        # Elderly prefer lower intensity
        intensity_modifier = {
            "light": 1.0,
            "moderate": 0.8,
            "high": 0.5,
            "extreme": 0.2,
        }
    elif participant.label == "toddler":
        # Toddlers prefer moderate intensity
        intensity_modifier = {
            "light": 0.9,
            "moderate": 1.0,
            "high": 0.6,
            "extreme": 0.1,
        }
    else:
        # Default modifier
        intensity_modifier = {
            "light": 1.0,
            "moderate": 1.0,
            "high": 1.0,
            "extreme": 1.0,
        }
    
    base_intensity_score = intensity_scores.get(activity.intensity, 0.5)
    modifier = intensity_modifier.get(activity.intensity, 1.0)
    score_components["intensity"] = base_intensity_score * modifier

    # Determine final tier
    if hard_exclusions:
        tier = "exclude"
    else:
        tier = _pick_most_conservative_tier(fired_tiers)
        
        # Adjust tier based on intensity score
        intensity_score = score_components.get("intensity", 0.5)
        if intensity_score < 0.3:
            tier = _downgrade_tier(tier)
        elif intensity_score > 0.8:
            tier = _upgrade_tier(tier)

    score = TIER_SCORE[tier]

    field_confidence = {
        "intensity": 0.95 if activity.intensity in {"light", "moderate", "high", "extreme"} else 0.4,
        "age_bounds": 0.95 if activity.min_age is not None or activity.max_age is not None else 0.6,
        "tags": 0.8 if activity.tags else 0.0,
        "duration": 0.8 if activity.duration_hours is not None else 0.0,
        "weight_bounds": 0.9 if activity.max_weight_kg is not None else 0.5,
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

