from spine_api.services.trip_lifecycle_service import build_reassessment_request_from_trip


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
