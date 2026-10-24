from spine_api.services.trip_lifecycle_service import build_reassessment_request_from_trip

from copy import deepcopy


def _corrected_trip() -> dict:
    return {
        "id": "trip_corrections",
        "party": 2,
        "tripPurpose": "beach holiday",
        "raw_input": {"submission": {"raw_note": "Two adults want a beach holiday.",
                                     "structured_json": {"party_size": 2, "trip_purpose": "beach holiday"}}},
        "extracted": {"facts": {
            "party_size": {"value": 5, "authority_level": "explicit_user", "extraction_mode": "traveler_ask_link"},
            "trip_purpose": {"value": "pilgrimage", "authority_level": "explicit_user", "extraction_mode": "traveler_ask_link"},
        }},
    }


def test_reassessment_projects_latest_canonical_answers_before_legacy_columns():
    trip = _corrected_trip()
    original = deepcopy(trip)
    request = build_reassessment_request_from_trip(trip)
    assert request["structured_json"]["party_size"] == 5
    assert request["structured_json"]["trip_purpose"] == "pilgrimage"
    assert request["raw_note"] == "Two adults want a beach holiday."
    assert trip == original


def test_reassessment_keeps_explicit_clear_distinct_from_unmentioned_fields():
    trip = _corrected_trip()
    trip["extracted"]["facts"]["budget_raw_text"] = {
        "value": None, "authority_level": "explicit_user", "extraction_mode": "manual_entry",
        "epistemic_status": "UNKNOWN",
    }
    trip["raw_input"]["submission"]["structured_json"]["budget"] = "USD 1000"
    request = build_reassessment_request_from_trip(trip)
    assert "budget" in request["structured_json"]
    assert request["structured_json"]["budget"] is None
    assert "duration" not in request["structured_json"]


def test_canonical_projection_does_not_resurrect_submission_values_after_corrections():
    from spine_api.services.inbox_projection import resolve_trip_field

    trip = _corrected_trip()
    trip["raw_input"]["submission"]["structured_json"]["origin"] = "Mumbai"
    trip["extracted"]["facts"]["origin_city"] = {
        "value": None, "authority_level": "explicit_user", "extraction_mode": "manual_entry",
    }
    assert resolve_trip_field(trip, "party_size") == 5
    assert resolve_trip_field(trip, "trip_purpose") == "pilgrimage"
    assert resolve_trip_field(trip, "origin") == "TBD"


def test_clear_party_does_not_turn_into_a_solo_traveler():
    from spine_api.services.inbox_projection import resolve_trip_field

    trip = _corrected_trip()
    trip["extracted"]["facts"]["party_size"]["value"] = None
    assert resolve_trip_field(trip, "party_size") == 0


def test_budget_evidence_resolution_preserves_decimal_and_currency_uncertainty():
    from decimal import Decimal
    from spine_api.services.inbox_projection import resolve_trip_budget

    trip = {"extracted": {"facts": {
        "budget": {"value": Decimal("123.456")},
        "budget_currency": {"value": "KWD", "epistemic_status": "FACT"},
    }}}
    assert resolve_trip_budget(trip) == (Decimal("123.456"), "KWD")
    trip["extracted"]["facts"]["budget_currency"]["epistemic_status"] = "ASSUMED"
    assert resolve_trip_budget(trip) == (Decimal("123.456"), None)
    trip["raw_input"] = {"submission": {"structured_json": {"budget": 10000, "currency": "USD"}}}
    trip["extracted"]["facts"]["budget_raw_text"] = {
        "value": None, "authority_level": "explicit_user", "extraction_mode": "manual_entry",
    }
    assert resolve_trip_budget(trip) == (None, None)


def test_trusted_reassessment_replaces_prior_destinations_and_allows_party_decrease():
    from spine_api.services.trip_lifecycle_service import build_reassessment_envelope_from_trip
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope

    trip = _corrected_trip()
    trip["extracted"]["facts"].update({
        "party_size": {"value": 2, "authority_level": "explicit_user", "extraction_mode": "manual_entry",
                       "evidence_refs": [{"envelope_id": "operator_edit", "evidence_type": "manual_entry",
                                          "excerpt": "2 travelers", "ref_id": "edit_2"}]},
        "destination_candidates": {"value": ["Japan"], "authority_level": "explicit_user", "extraction_mode": "manual_entry"},
    })
    pipeline = ExtractionPipeline()
    packet = pipeline.extract([
        SourceEnvelope.from_freeform("Five adults traveling from Mumbai to Italy for a beach holiday."),
        build_reassessment_envelope_from_trip(trip),
    ])
    assert packet.facts["party_size"].value == 2
    assert packet.facts["destination_candidates"].value == ["Japan"]
    assert packet.facts["party_size"].authority_level == "explicit_user"
    assert packet.facts["party_size"].evidence_refs[0].ref_id == "edit_2"


def test_trusted_clear_survives_repeated_reassessment_and_remains_blocking():
    from spine_api.services.trip_lifecycle_service import build_reassessment_envelope_from_trip
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope
    from src.intake.validation import blocking_unknowns, classify_missing_fields

    trip = _corrected_trip()
    trip["extracted"]["facts"]["origin_city"] = {
        "value": None, "authority_level": "explicit_user", "extraction_mode": "manual_entry",
        "epistemic_status": "UNKNOWN",
    }
    for _ in range(2):
        packet = ExtractionPipeline().extract([
            SourceEnvelope.from_freeform("Two adults traveling from Mumbai to Italy."),
            build_reassessment_envelope_from_trip(trip),
        ])
        assert packet.facts["origin_city"].value is None
        assert "origin_city" in classify_missing_fields(packet)
        assert "origin_city" in {item["field_name"] for item in blocking_unknowns(packet)}
        assert next(u for u in packet.unknowns if u.field_name == "origin_city").reason == "intentionally_unknown"
        trip["extracted"] = packet.to_dict()


def test_build_reassessment_request_preserves_manual_edits_in_structured_overlay() -> None:
    trip = {
        "id": "trip_123",
        "stage": "discovery",
        "raw_input": {
            "submission": {
                "raw_note": "Original traveler note",
                "structured_json": {"lead_source": "whatsapp"},
            },
            "retention_consent": True,
        },
        "origin": "Mumbai",
        "destination": "Italy",
        "budget": "₹3.5L",
        "dateWindow": "10 Jun to 17 Jun",
        "tripPurpose": "family leisure",
        "tripPriorities": "beach villa",
        "dateFlexibility": "flexible by 2 days",
        "follow_up_due_date": "2026-06-25T10:00:00+05:30",
        "pace_preference": "relaxed",
        "lead_source": "call",
        "activity_provenance": "repeat client",
        "date_year_confidence": "high",
        "extracted": {"facts": {"origin_city": {"value": "Mumbai"}}},
    }

    request = build_reassessment_request_from_trip(trip)

    assert request["raw_note"] == "Original traveler note"
    assert request["structured_json"] == {
        "lead_source": "call",
        "origin": "Mumbai",
        "destination": "Italy",
        "budget": "₹3.5L",
        "dates": "10 Jun to 17 Jun",
        "date_window": "10 Jun to 17 Jun",
        "trip_purpose": "family leisure",
        "trip_priorities": "beach villa",
        "date_flexibility": "flexible by 2 days",
        "follow_up_due_date": "2026-06-25T10:00:00+05:30",
        "pace_preference": "relaxed",
        "activity_provenance": "repeat client",
        "date_year_confidence": "high",
    }
