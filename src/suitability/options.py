"""Canonical itinerary option construction and utility economics."""

from __future__ import annotations

from typing import Iterable

from .models import (
    ActivityDefinition,
    ActivitySuitability,
    ItineraryOption,
    ParticipantRef,
    PersonUtility,
    SuitabilityBundle,
    SuitabilityContext,
    WastedSpendItem,
    WastedSpendSummary,
)
from .scoring import evaluate_activity

LOW_UTILITY_THRESHOLD = 50.0
HIGH_UTILITY_THRESHOLD = 70.0


def _score_to_percentage(score: float) -> float:
    return max(0.0, min(100.0, score * 100.0))


def _cost_per_person(activity: ActivityDefinition) -> int:
    if activity.cost_per_person is None:
        return 0
    return max(0, int(activity.cost_per_person))


def build_suitability_bundle(
    activity: ActivityDefinition,
    participants: Iterable[ParticipantRef],
    context: SuitabilityContext,
) -> SuitabilityBundle:
    """Score one activity for all participants and compute group-level waste."""

    participant_list = list(participants)
    assessments = [evaluate_activity(activity, participant, context) for participant in participant_list]
    total_participants = len(assessments)
    group_score = sum(assessment.score for assessment in assessments) / total_participants if assessments else 0.0
    high_utility_count = sum(
        1 for assessment in assessments if _score_to_percentage(assessment.score) >= HIGH_UTILITY_THRESHOLD
    )
    cost_per_person = _cost_per_person(activity)
    total_cost = cost_per_person * total_participants
    wasted_spend_amount = sum(
        round(cost_per_person * (1.0 - max(0.0, min(1.0, assessment.score))))
        for assessment in assessments
        if _score_to_percentage(assessment.score) < LOW_UTILITY_THRESHOLD
    )
    wasted_spend_ratio = wasted_spend_amount / total_cost if total_cost else 0.0

    return SuitabilityBundle(
        activity_id=activity.activity_id,
        activity_name=activity.canonical_name,
        assessments=assessments,
        group_score=group_score,
        high_utility_count=high_utility_count,
        total_participants=total_participants,
        cost_per_person=cost_per_person,
        total_cost=total_cost,
        wasted_spend_ratio=wasted_spend_ratio,
        wasted_spend_amount=wasted_spend_amount,
    )


def _build_person_utility(
    participant: ParticipantRef,
    assessments: list[ActivitySuitability],
) -> PersonUtility:
    scores = {assessment.activity_id: _score_to_percentage(assessment.score) for assessment in assessments}
    utility = sum(scores.values()) / len(scores) if scores else 0.0
    low_utility = [
        assessment.activity_id
        for assessment in assessments
        if _score_to_percentage(assessment.score) < LOW_UTILITY_THRESHOLD
    ]
    excluded = [assessment.activity_id for assessment in assessments if not assessment.compatible]
    return PersonUtility(
        participant=participant,
        utility_percentage=utility,
        activity_scores=scores,
        low_utility_activity_ids=low_utility,
        excluded_activity_ids=excluded,
    )


def _build_wasted_spend_summary(bundles: list[SuitabilityBundle]) -> WastedSpendSummary:
    items: list[WastedSpendItem] = []
    total_cost = sum(bundle.total_cost for bundle in bundles)
    for bundle in bundles:
        affected = [
            assessment.participant.ref_id
            for assessment in bundle.assessments
            if _score_to_percentage(assessment.score) < LOW_UTILITY_THRESHOLD
        ]
        if not affected or bundle.wasted_spend_amount <= 0:
            continue
        affected_scores = [
            _score_to_percentage(assessment.score)
            for assessment in bundle.assessments
            if assessment.participant.ref_id in affected
        ]
        average_utility = sum(affected_scores) / len(affected_scores) if affected_scores else 0.0
        items.append(
            WastedSpendItem(
                activity_id=bundle.activity_id,
                activity_name=bundle.activity_name,
                affected_participants=affected,
                amount=bundle.wasted_spend_amount,
                average_utility_percentage=average_utility,
                reason=(
                    f"{len(affected)} participant(s) below "
                    f"{LOW_UTILITY_THRESHOLD:.0f}% utility for this activity."
                ),
            )
        )

    total_amount = sum(item.amount for item in items)
    return WastedSpendSummary(
        total_amount=total_amount,
        ratio=total_amount / total_cost if total_cost else 0.0,
        items=items,
    )


def build_itinerary_option(
    *,
    option_id: str,
    title: str,
    destination_keys: list[str],
    activities: list[ActivityDefinition],
    participants: list[ParticipantRef],
    context: SuitabilityContext,
    rank: int | None = None,
) -> ItineraryOption:
    """Build the canonical itinerary option artifact from activities and travelers."""

    bundles = [build_suitability_bundle(activity, participants, context) for activity in activities]
    assessments_by_participant: dict[str, list[ActivitySuitability]] = {
        participant.ref_id: [] for participant in participants
    }
    for bundle in bundles:
        for assessment in bundle.assessments:
            assessments_by_participant.setdefault(assessment.participant.ref_id, []).append(assessment)

    utility_by_person = {
        participant.ref_id: _build_person_utility(
            participant,
            assessments_by_participant.get(participant.ref_id, []),
        )
        for participant in participants
    }

    return ItineraryOption(
        option_id=option_id,
        title=title,
        destination_keys=destination_keys,
        activities=activities,
        participants=participants,
        suitability_bundles=bundles,
        utility_by_person=utility_by_person,
        wasted_spend=_build_wasted_spend_summary(bundles),
        total_cost=sum(bundle.total_cost for bundle in bundles),
        rank=rank,
    )
