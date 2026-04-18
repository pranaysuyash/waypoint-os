"""
suitability.context_rules — Tier 2 deterministic day/trip coherence checks.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from .models import (
    ActivityDefinition,
    ActivitySuitability,
    ParticipantRef,
    StructuredRisk,
    SuitabilityContext,
)

INTENSITY_WEIGHT: Dict[str, float] = {
    "light": 0.25,
    "moderate": 0.5,
    "high": 0.75,
    "extreme": 1.0,
}

DAY_INTENSITY_THRESHOLDS: Dict[str, float] = {
    "elderly": 1.5,
    "toddler": 1.75,
}


def _downgrade_tier(current_tier: str) -> str:
    order = ["exclude", "discourage", "neutral", "recommend", "strong_recommend"]
    index = order.index(current_tier)
    if index == 0:
        return current_tier
    return order[index - 1]


def _severity_to_penalty(severity: str) -> float:
    if severity == "critical":
        return 0.25
    if severity == "high":
        return 0.2
    if severity == "medium":
        return 0.12
    return 0.06


def _sum_intensity(activities: List[ActivityDefinition]) -> float:
    return sum(INTENSITY_WEIGHT.get(a.intensity, 0.5) for a in activities)


def apply_tour_context_rules(
    base: ActivitySuitability,
    activity: ActivityDefinition,
    participant: ParticipantRef,
    context: SuitabilityContext,
) -> ActivitySuitability:
    """Apply Tier 2 sequence rules and return an updated suitability output."""
    risks: List[StructuredRisk] = list(base.generated_risks)
    warnings = list(base.warnings)
    score = base.score
    tier = base.tier

    day_activities = list(context.day_activities)
    if all(a.activity_id != activity.activity_id for a in day_activities):
        day_activities.append(activity)

    participant_threshold = DAY_INTENSITY_THRESHOLDS.get(participant.label)
    day_intensity = _sum_intensity(day_activities)
    if participant_threshold is not None and day_intensity > participant_threshold:
        severity = "high" if day_intensity - participant_threshold >= 0.5 else "medium"
        risks.append(
            StructuredRisk(
                flag="cumulative_fatigue_risk",
                severity=severity,
                category="pacing",
                message=(
                    f"Cumulative day intensity {day_intensity:.2f} exceeds "
                    f"{participant.label} threshold {participant_threshold:.2f}."
                ),
                details={"day_intensity": day_intensity, "threshold": participant_threshold},
                affected_travelers=[participant.ref_id],
                mitigation_suggestions=["Insert a light or rest block on the same day."],
                rule_id="tier2_cumulative_intensity",
            )
        )

    high_or_extreme = [a for a in day_activities if a.intensity in {"high", "extreme"}]
    if len(high_or_extreme) >= 2 and participant.label in {"elderly", "toddler"}:
        risks.append(
            StructuredRisk(
                flag="back_to_back_strain",
                severity="medium",
                category="pacing",
                message="Back-to-back high intensity activities increase fatigue risk.",
                details={"count_high_intensity": len(high_or_extreme)},
                affected_travelers=[participant.ref_id],
                mitigation_suggestions=["Split high-intensity activities across separate days."],
                rule_id="tier2_back_to_back_intensity",
            )
        )

    total_day_duration = sum(a.duration_hours or 0 for a in day_activities)
    if participant.label in {"elderly", "toddler"} and total_day_duration > 8:
        risks.append(
            StructuredRisk(
                flag="day_duration_overload",
                severity="medium",
                category="pacing",
                message=f"Total day duration {total_day_duration:.1f}h exceeds comfort threshold.",
                details={"duration_hours": total_day_duration},
                affected_travelers=[participant.ref_id],
                mitigation_suggestions=["Move one activity to next day or shorten session durations."],
                rule_id="tier2_duration_overload",
            )
        )

    if (
        context.destination_climate == "tropical_humid"
        and participant.label == "elderly"
        and ("walking_heavy" in activity.tags or "physical_intense" in activity.tags)
    ):
        risks.append(
            StructuredRisk(
                flag="climate_amplified_exertion",
                severity="high",
                category="seasonality",
                message="Tropical humidity amplifies exertion risk for elderly travelers.",
                details={"destination_climate": context.destination_climate},
                affected_travelers=[participant.ref_id],
                mitigation_suggestions=["Prefer early morning slot and include hydration/rest windows."],
                rule_id="tier2_climate_amplifier",
            )
        )

    if participant.label == "elderly" and activity.intensity in {"high", "extreme"}:
        recent = context.trip_activities[-2:]
        if len(recent) == 2 and all(a.intensity in {"high", "extreme"} for a in recent):
            if all(a.intensity != "light" for a in recent):
                risks.append(
                    StructuredRisk(
                        flag="insufficient_recovery",
                        severity="medium",
                        category="pacing",
                        message="Trip sequence lacks a light-recovery day before next high-intensity activity.",
                        details={"recent_intensities": [a.intensity for a in recent]},
                        affected_travelers=[participant.ref_id],
                        mitigation_suggestions=["Insert a light activity day before this segment."],
                        rule_id="tier2_recovery_gap",
                    )
                )

    for risk in risks[len(base.generated_risks):]:
        warnings.append(risk.message)
        score = max(0.0, score - _severity_to_penalty(risk.severity))
        tier = _downgrade_tier(tier)

    return replace(
        base,
        score=round(score, 4),
        tier=tier,
        warnings=warnings,
        generated_risks=risks,
    )

