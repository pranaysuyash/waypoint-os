"""A transfer station is evidence about a leg, not a city-valued trip fact."""

import pytest

from src.intake.extractors import ExtractionPipeline
from src.intake.packet_models import SourceEnvelope


def _envelope(content, content_type="freeform_text"):
    return SourceEnvelope(
        envelope_id="rail-place-role",
        source_system="test",
        actor_type="traveler",
        received_at="2026-11-25T09:00:00Z",
        content=content,
        content_type=content_type,
    )


@pytest.mark.parametrize("leg", [
    "TGV INOUI from Gare de Lyon.",
    "RER B from Gare du Nord.",
    "driver pickup at Gare du Nord.",
    "onward train, and I do not have the operator or station.",
])
def test_disruption_station_does_not_create_trip_endpoints(leg):
    note = "Our Eurostar to Paris is delayed today. We expect to miss the separately booked " + leg
    packet = ExtractionPipeline().extract([_envelope(note)])
    assert "origin_city" not in packet.facts
    assert packet.facts["destination_candidates"].value == ["Paris"]
    assert packet.facts["destination_status"].value == "definite"


@pytest.mark.parametrize(("note", "origin", "destination"), [
    ("From London to Lyon. Meeting at Gare de Lyon.", "London", "Lyon"),
    ("Meeting at Gare du Nord. Flying from Lyon to Tokyo.", "Lyon", "Tokyo"),
    ("Origin city: Paris. Destination: Lyon. Pickup at Paris Gare de Lyon.", "Paris", "Lyon"),
    ("Origin city: Lyon. Destination: Paris. Pickup at GARE DE LYON.", "Lyon", "Paris"),
])
def test_station_name_does_not_hide_independent_city_facts(note, origin, destination):
    packet = ExtractionPipeline().extract([_envelope(note)])
    assert packet.facts["origin_city"].value == origin
    assert packet.facts["destination_candidates"].value == [destination]


def test_station_alone_leaves_city_endpoints_open():
    packet = ExtractionPipeline().extract([_envelope("Gare de Lyon.")])
    assert "origin_city" not in packet.facts
    assert not packet.facts["destination_candidates"].value


def test_station_detail_preserves_structured_endpoints():
    packet = ExtractionPipeline().extract([
        _envelope({"origin_city": "London", "destination": "Lyon"}, "structured_json"),
        _envelope("Pickup at Gare du Nord."),
    ])
    assert packet.facts["origin_city"].value == "London"
    assert packet.facts["destination_candidates"].value == ["Lyon"]


@pytest.mark.parametrize(("note", "value"), [
    ("The hotel needs an advance. We expect to miss the separately booked TGV INOUI from Gare de Lyon.", "has_existing_booking"),
    ("We already booked our flights. Please check the hotel.", "has_flights_booked"),
    ("The hotel is booked.", "has_existing_booking"),
    ("Only the hotel is booked.", "has_hotel_only"),
    ("We have nothing booked yet.", "nothing_booked"),
    ("We haven't booked anything yet.", "nothing_booked"),
    ("Already booked.", "has_existing_booking"),
    ("We have an itinerary", "has_existing_itinerary"),
    ("The driver is separately booked.", "has_existing_booking"),
    ("Only the hotel is booked. Our train is separately booked.", "has_existing_booking"),
    ("The train is delayed.", None),
    ("The flights aren't booked.", None),
    ("Are the flights booked?", None),
    ("If the train is separately booked, will they hold a taxi?", None),
    ("Not sure whether the hotel is already booked.", None),
    ("We want the flights booked tomorrow.", None),
    ("I don't have an itinerary.", None),
    ("Nothing booked except the train.", None),
    ("We have nothing booked. The train is booked.", None),
])
def test_traveler_plan_needs_booking_evidence(note, value):
    packet = ExtractionPipeline().extract([_envelope(note)])
    fact = packet.facts.get("traveler_plan")
    if value is None:
        assert fact is None
    else:
        assert fact.value == value
        assert fact.evidence_refs[0].excerpt in note


@pytest.mark.parametrize(("separate_destination", "expected"), [
    ("", []),
    (" We are traveling to Alpha.", ["Alpha"]),
])
def test_hotel_name_requires_independent_destination_mention(separate_destination, expected):
    note = (
        "Hotel Alpha requires a deposit and says cancellation is free. "
        "Hotel Beta requires a deposit and says cancellation is free. "
        "Hotel Alpha confirms its deposit is nonrefundable."
    ) + separate_destination
    packet = ExtractionPipeline().extract([_envelope(note)])
    slot = packet.facts.get("destination_candidates")
    assert (slot.value if slot else []) == expected


@pytest.mark.parametrize(("prefix", "ferry_destination", "expected_origin", "expected_destination"), [
    ("", "Belfast", None, "Belfast"),
    ("From Glasgow to Belfast. ", "Belfast", "Glasgow", "Belfast"),
    ("We are traveling to Cairnryan. ", "Cairnryan", None, "Cairnryan"),
])
def test_vehicle_ferry_distinguishes_port_operator_and_trip_endpoints(
    prefix, ferry_destination, expected_origin, expected_destination,
):
    note = (
        f"{prefix}Our rental car will reach Cairnryan port at 03:00 local time. "
        f"Our 03:30 Stena Line ferry to {ferry_destination} shows vehicle check-in closes at 02:45 on the e-ticket."
    )
    packet = ExtractionPipeline().extract([_envelope(note)])
    assert packet.facts["destination_candidates"].value == [expected_destination]
    origin = packet.facts.get("origin_city")
    assert (origin.value if origin else None) == expected_origin
