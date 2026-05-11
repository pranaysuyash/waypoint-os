"""Activity-category D6 rule runner."""

from __future__ import annotations

from typing import Any

from src.suitability.models import ActivityDefinition, ParticipantRef, StructuredRisk, SuitabilityContext
from src.suitability.options import LOW_UTILITY_THRESHOLD, build_itinerary_option

from ..fixtures import AuditFixture


def _int_value(value: Any) -> int:
    return value if isinstance(value, int) and value > 0 else 0


def _participants_from_composition(composition: dict[str, Any]) -> list[ParticipantRef]:
    participants: list[ParticipantRef] = []
    for index in range(_int_value(composition.get("adults"))):
        participants.append(ParticipantRef(kind="person", ref_id=f"adult_{index + 1}", label="adult"))
    for index in range(_int_value(composition.get("elderly"))):
        participants.append(ParticipantRef(kind="person", ref_id=f"elderly_{index + 1}", label="elderly", age=70))
    toddler_count = _int_value(composition.get("toddlers"))
    toddler_count = max(toddler_count, _int_value(composition.get("toddler")))
    for index in range(toddler_count):
        participants.append(ParticipantRef(kind="person", ref_id=f"toddler_{index + 1}", label="toddler", age=3))
    child_ages = composition.get("child_ages")
    if isinstance(child_ages, list):
        for index, raw_age in enumerate(child_ages):
            if isinstance(raw_age, (int, float)):
                age = int(raw_age)
                participants.append(
                    ParticipantRef(
                        kind="person",
                        ref_id=f"child_{index + 1}",
                        label="toddler" if age < 5 else "child",
                        age=age,
                    )
                )
    return participants


def _activity_from_payload(payload: dict[str, Any]) -> ActivityDefinition:
    return ActivityDefinition(
        activity_id=str(payload.get("activity_id") or payload.get("id") or "activity"),
        canonical_name=str(payload.get("canonical_name") or payload.get("name") or payload.get("activity_id") or "Activity"),
        source="static",
        destination_keys=[str(item) for item in payload.get("destination_keys") or []],
        tags=[str(item) for item in payload.get("tags") or []],
        intensity=str(payload.get("intensity") or "moderate"),
        duration_hours=float(payload["duration_hours"]) if isinstance(payload.get("duration_hours"), (int, float)) else None,
        cost_per_person=int(payload["cost_per_person"]) if isinstance(payload.get("cost_per_person"), (int, float)) else None,
        min_age=int(payload["min_age"]) if isinstance(payload.get("min_age"), int) else None,
        max_age=int(payload["max_age"]) if isinstance(payload.get("max_age"), int) else None,
    )


def run_activity_fixture(fixture: AuditFixture) -> list[StructuredRisk]:
    """Run the activity analyzer for one D6 fixture and emit measured risks."""

    subject = fixture.subject
    if fixture.category != "activity":
        return []
    composition = subject.get("party_composition") if isinstance(subject.get("party_composition"), dict) else {}
    activities_payload = subject.get("activities") if isinstance(subject.get("activities"), list) else []
    participants = _participants_from_composition(composition)
    activities = [_activity_from_payload(item) for item in activities_payload if isinstance(item, dict)]
    if not participants or not activities:
        return []

    destination_keys = [str(item) for item in subject.get("destination_keys") or []]
    option = build_itinerary_option(
        option_id=str(subject.get("subject_id") or fixture.fixture_id),
        title=str(subject.get("title") or fixture.fixture_id),
        destination_keys=destination_keys,
        activities=activities,
        participants=participants,
        context=SuitabilityContext(destination_keys=destination_keys),
    )
    findings: list[StructuredRisk] = []
    low_utility_people = [
        person_id
        for person_id, utility in option.utility_by_person.items()
        if utility.low_utility_activity_ids
    ]
    if low_utility_people:
        findings.append(
            StructuredRisk(
                flag="low_utility_activity",
                severity="high",
                category="activity",
                message=(
                    "One or more travelers have activities below "
                    f"{LOW_UTILITY_THRESHOLD:.0f}% utility."
                ),
                affected_travelers=low_utility_people,
                details={
                    "option_id": option.option_id,
                    "low_utility_by_person": {
                        person_id: utility.low_utility_activity_ids
                        for person_id, utility in option.utility_by_person.items()
                        if utility.low_utility_activity_ids
                    },
                },
                rule_id="d6_activity_low_utility_v1",
            )
        )
    if option.wasted_spend.total_amount > 0:
        affected = sorted(
            {
                participant
                for item in option.wasted_spend.items
                for participant in item.affected_participants
            }
        )
        findings.append(
            StructuredRisk(
                flag="wasted_spend",
                severity="medium",
                category="activity",
                message="The itinerary includes measurable low-utility spend.",
                affected_travelers=affected,
                details={
                    "option_id": option.option_id,
                    "total_amount": option.wasted_spend.total_amount,
                    "ratio": option.wasted_spend.ratio,
                    "items": [
                        {
                            "activity_id": item.activity_id,
                            "amount": item.amount,
                            "affected_participants": item.affected_participants,
                        }
                        for item in option.wasted_spend.items
                    ],
                },
                rule_id="d6_activity_wasted_spend_v1",
            )
        )
    return findings
