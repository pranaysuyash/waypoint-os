"""Executable current-state probes for product contracts D-01 through D-03.

These tests intentionally describe the pre-ratification boundary.  They do not
claim that the observed aliases are the desired product contract; they prevent
future work from silently treating compatibility fields as canonical truth
until the owner-ratified migration is implemented.
"""

from datetime import datetime

from src.intake.extractors import ExtractionPipeline, _extract_destination_candidates
from src.intake.packet_models import SourceEnvelope


def _freeform(text: str) -> SourceEnvelope:
    return SourceEnvelope(
        envelope_id="d01-d03-probe",
        source_system="contract_probe",
        actor_type="traveler",
        received_at=datetime.now().isoformat(),
        content=text,
        content_type="freeform_text",
    )


def _structured(payload: dict) -> SourceEnvelope:
    return SourceEnvelope(
        envelope_id="d01-d03-structured-probe",
        source_system="contract_probe",
        actor_type="traveler",
        received_at=datetime.now().isoformat(),
        content=payload,
        content_type="structured_json",
    )


def test_d01_date_interval_has_no_canonical_duration_projection_yet():
    packet = ExtractionPipeline().extract([
        _freeform(
            "We are going to Tokyo from 2026-10-01 to 2026-10-06. "
            "2 adults. Budget USD 5000."
        )
    ])

    assert packet.facts["date_start"].value == "2026-10-01"
    assert packet.facts["date_end"].value == "2026-10-06"
    assert not {
        "trip_nights",
        "trip_days",
        "duration_amount",
        "duration_unit",
    }.intersection(packet.facts)


def test_d01_structured_duration_is_accepted_as_unitless_compatibility_fact():
    packet = ExtractionPipeline().extract([
        _structured({
            "duration": 5,
            "destination": "Tokyo",
            "dates": "2026-10-01 to 2026-10-06",
        })
    ])

    assert packet.facts["duration"].value == 5
    assert not {"duration_amount", "duration_unit", "trip_nights", "trip_days"}.intersection(
        packet.facts
    )


def test_d02_flight_inclusiveness_is_not_yet_a_first_class_fact():
    for qualifier in (
        "not sure if that includes flights",
        "excluding flights",
        "including flights",
    ):
        packet = ExtractionPipeline().extract([
            _freeform(
                f"Tokyo, 2026-10-01 to 2026-10-06. 2 adults. "
                f"Budget USD 5000 {qualifier}."
            )
        ])

        assert "flights_inclusiveness" not in packet.facts
        assert packet.facts["budget_min"].value == 5000


def test_d03_country_only_is_currently_coerced_into_destination_candidates():
    candidates, status, _raw = _extract_destination_candidates(
        "10 days in Japan, you pick"
    )

    assert candidates == ["Japan"]
    assert status == "definite"


def test_d03_country_and_city_scope_collide_in_one_untyped_candidate_list():
    candidates, status, _raw = _extract_destination_candidates(
        "Japan, thinking Tokyo + Kyoto"
    )

    # Current behavior is intentionally pinned as evidence of the gap: the
    # country and city candidates share one slot.  The exact candidate set
    # may improve independently, but no typed scope is emitted yet.
    assert candidates == ["Japan", "Tokyo", "Kyoto"]
    assert status == "semi_open"


def test_d03_city_set_has_no_independent_country_scope_fact():
    packet = ExtractionPipeline().extract([
        _freeform("Tokyo + Kyoto. 2 adults. Budget USD 5000.")
    ])

    assert packet.facts["destination_candidates"].value == ["Tokyo", "Kyoto"]
    assert "destination_countries" not in packet.facts
    assert "destination_scope" not in packet.facts
