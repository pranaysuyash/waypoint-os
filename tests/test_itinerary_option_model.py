from src.suitability.models import ActivityDefinition, ParticipantRef, SuitabilityContext
from src.suitability.options import build_itinerary_option


def test_itinerary_option_calculates_per_person_utility_and_waste():
    activities = [
        ActivityDefinition(
            activity_id="universal_studios",
            canonical_name="Universal Studios",
            source="static",
            tags=["height_required"],
            intensity="high",
            cost_per_person=5000,
            min_age=6,
        ),
        ActivityDefinition(
            activity_id="museum_visit",
            canonical_name="Museum Visit",
            source="static",
            tags=["seated_show", "cultural"],
            intensity="light",
            cost_per_person=1000,
        ),
    ]
    participants = [
        ParticipantRef(kind="person", ref_id="adult_1", label="adult", age=35),
        ParticipantRef(kind="person", ref_id="toddler_1", label="toddler", age=3),
        ParticipantRef(kind="person", ref_id="elderly_1", label="elderly", age=72),
    ]

    option = build_itinerary_option(
        option_id="sg_family_v1",
        title="Singapore Family Option",
        destination_keys=["singapore"],
        activities=activities,
        participants=participants,
        context=SuitabilityContext(destination_keys=["singapore"]),
    )

    assert option.option_id == "sg_family_v1"
    assert option.total_cost == 18000
    assert option.utility_by_person["adult_1"].utility_percentage > 50
    assert option.utility_by_person["toddler_1"].activity_scores["universal_studios"] == 0
    assert option.utility_by_person["toddler_1"].low_utility_activity_ids == ["universal_studios"]
    assert option.wasted_spend.total_amount > 0
    assert option.wasted_spend.items[0].activity_id == "universal_studios"
    assert "toddler_1" in option.wasted_spend.items[0].affected_participants


def test_itinerary_option_clamps_missing_cost_to_zero_without_losing_utility():
    activity = ActivityDefinition(
        activity_id="temple_visit",
        canonical_name="Temple Visit",
        source="static",
        tags=["seated_show", "cultural"],
        intensity="light",
        cost_per_person=None,
    )
    participant = ParticipantRef(kind="person", ref_id="elderly_1", label="elderly", age=70)

    option = build_itinerary_option(
        option_id="culture_v1",
        title="Culture Option",
        destination_keys=["jaipur"],
        activities=[activity],
        participants=[participant],
        context=SuitabilityContext(destination_keys=["jaipur"]),
    )

    assert option.total_cost == 0
    assert option.wasted_spend.total_amount == 0
    assert option.utility_by_person["elderly_1"].utility_percentage > 80
