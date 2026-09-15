"""
Canonical contract roundtrip tests for PATCH /trips/{id} → GET /trips/{id}.

These tests formally verify the end-to-end Strangler Fig canonical contract:
- Each patchable canonical field is written via PATCH
- GET must return the same value via TripResponse (using resolve_trip_field)
- State must survive a fresh GET (not just the PATCH response)
- Patching one field must not clobber another (cross-field preservation)
- The dual-write side effect must be observable in TripResponse.extracted.facts

Patchable canonical fields (as named in TripResponse):
    origin      — PATCH key: "origin"    → extracted.facts.origin_city.value
    destination — PATCH key: "destination" → extracted.facts.destination_candidates.value
    dateWindow  — PATCH key: "dateWindow" → extracted.facts.date_window.value
    party       — PATCH key: "party"     → extracted.facts.party_size.value
    budget      — PATCH key: "budget"    → extracted.facts.budget.value
    tripPurpose — PATCH key: "tripPurpose" → extracted.facts.trip_purpose.value

Note: tripType is intentionally NOT patchable via PATCH /trips/{id};
_sync_manual_trip_fields does not handle it.

Run: uv run python -m pytest tests/test_trip_canonical_roundtrip.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from spine_api.contract import TripResponse
from spine_api.persistence import TripStore, TEST_AGENCY_ID

pytestmark = pytest.mark.require_postgres

AGENCY_ID = TEST_AGENCY_ID


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def canonical_trip_id():
    """Create a bare trip with no extracted facts; yield its ID; clean up after."""
    unique = uuid4().hex[:12]
    trip_id = f"tc_roundtrip_{unique}"
    now = datetime.now(timezone.utc).isoformat()
    TripStore.save_trip(
        {
            "id": trip_id,
            "run_id": f"run_{unique}",
            "source": "pytest-canonical",
            "status": "assigned",
            "created_at": now,
            "updated_at": now,
            "extracted": {"facts": {}},
            "validation": {"is_valid": True, "errors": [], "warnings": []},
            "decision": {
                "decision_state": "ASK_FOLLOWUP",
                "hard_blockers": [],
                "soft_blockers": [],
            },
            "raw_input": {"fixture_id": "canonical-roundtrip-test"},
        },
        agency_id=AGENCY_ID,
    )
    try:
        yield trip_id
    finally:
        TripStore.delete_trip(trip_id)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_trip(client, trip_id: str) -> dict:
    resp = client.get(f"/trips/{trip_id}")
    assert resp.status_code == 200, f"GET /trips/{trip_id} failed: {resp.text}"
    return resp.json()


def _patch_trip(client, trip_id: str, payload: dict) -> dict:
    resp = client.patch(f"/trips/{trip_id}", json=payload)
    assert resp.status_code == 200, f"PATCH /trips/{trip_id} failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Individual canonical field roundtrips
# ---------------------------------------------------------------------------


class TestOriginRoundtrip:
    def test_patch_origin_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"origin": "New York"})
        assert result["origin"] == "New York"

    def test_patch_origin_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"origin": "New York"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["origin"] == "New York"

    def test_patch_origin_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write origin_city into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"origin": "Tokyo"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("origin_city", {}).get("value") == "Tokyo", (
            "PATCH must dual-write origin into extracted.facts.origin_city.value"
        )

    def test_patch_origin_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"origin": "London"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("origin_city", {}).get("authority_level") == "explicit_user"

    def test_manual_structured_overlay_wins_over_stale_extracted_origin(self):
        trip = {
            "id": "trip_overlay",
            "status": "assigned",
            "raw_input": {
                "submission": {
                    "structured_json": {
                        "origin": "Mumbai",
                    }
                }
            },
            "extracted": {
                "facts": {
                    "origin_city": {
                        "value": "TBD",
                        "confidence": 0.2,
                        "authority_level": "ai_guess",
                    }
                }
            },
        }

        result = TripResponse.from_dict(trip)

        assert result.origin == "Mumbai"


class TestDestinationRoundtrip:
    def test_patch_destination_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"destination": "Paris"})
        assert result["destination"] == "Paris"

    def test_patch_destination_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"destination": "Paris"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["destination"] == "Paris"

    def test_patch_destination_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"destination": "Rome"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        candidates = facts.get("destination_candidates", {})
        assert isinstance(candidates, dict), "destination_candidates must be a fact dict"
        value = candidates.get("value")
        assert isinstance(value, list) and "Rome" in value, (
            "PATCH must dual-write destination into extracted.facts.destination_candidates.value"
        )


class TestDateWindowRoundtrip:
    def test_patch_datewindow_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"dateWindow": "June 2026"})
        assert result["dateWindow"] == "June 2026"

    def test_patch_datewindow_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"dateWindow": "June 2026"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["dateWindow"] == "June 2026"

    def test_patch_datewindow_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"dateWindow": "July 4-14"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("date_window", {}).get("value") == "July 4-14"


class TestPartyRoundtrip:
    def test_patch_party_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"party": 4})
        assert result["party"] == 4

    def test_patch_party_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"party": 4})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["party"] == 4

    def test_patch_party_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"party": 2})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("party_size", {}).get("value") == 2


class TestBudgetRoundtrip:
    def test_patch_budget_numeric_string_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"budget": "5000"})
        # budget_numeric from _budget_value → float(5000) = 5000.0
        assert result["budget"] == 5000.0

    def test_patch_budget_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"budget": "5000"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["budget"] == 5000.0

    def test_patch_budget_currency_string_parsed_to_numeric(self, session_client, canonical_trip_id):
        """_parse_budget_amount must strip currency symbols and parse digits."""
        result = _patch_trip(session_client, canonical_trip_id, {"budget": "$8,500"})
        assert result["budget"] == 8500.0

    def test_patch_budget_compact_lakh_string_parsed_to_numeric(self, session_client, canonical_trip_id):
        """_parse_budget_amount must preserve compact units like lakhs."""
        result = _patch_trip(session_client, canonical_trip_id, {"budget": "₹3.5L"})
        assert result["budget"] == 350000.0
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("budget", {}).get("value") == 350000.0

    def test_patch_budget_dual_write_numeric_in_extracted(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"budget": "3000"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("budget", {}).get("value") == 3000.0

    def test_patch_budget_non_parseable_falls_back_to_raw_text(self, session_client, canonical_trip_id):
        """When budget string has no parseable number, raw text is stored and returned."""
        result = _patch_trip(session_client, canonical_trip_id, {"budget": "flexible"})
        # budget_numeric = 0 (no digits), budget_raw = "flexible" → TripResponse.budget = "flexible"
        assert result["budget"] == "flexible"


class TestTripPurposeRoundtrip:
    def test_patch_trip_purpose_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"tripPurpose": "family holiday"})
        assert result["tripPurpose"] == "family holiday"

    def test_patch_trip_purpose_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"tripPurpose": "honeymoon"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["tripPurpose"] == "honeymoon"

    def test_patch_trip_purpose_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"tripPurpose": "business"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("trip_purpose", {}).get("value") == "business"

    def test_patch_trip_purpose_business_promotes_trip_type(self, session_client, canonical_trip_id):
        """Corporate intent should surface as tripType business instead of default leisure."""
        _patch_trip(session_client, canonical_trip_id, {"tripPurpose": "business"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["tripType"] == "business"


# ---------------------------------------------------------------------------
# Phase 2 structured intake field roundtrips
# ---------------------------------------------------------------------------


class TestPartyCompositionRoundtrip:
    def test_patch_party_composition_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"party_composition": "2 adults, 1 child"})
        assert result["party_composition"] == "2 adults, 1 child"

    def test_patch_party_composition_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"party_composition": "3 adults, 2 children"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["party_composition"] == "3 adults, 2 children"

    def test_patch_party_composition_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write party_composition into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"party_composition": "1 adult, 1 infant"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("party_composition", {}).get("value") == "1 adult, 1 infant", (
            "PATCH must dual-write party_composition into extracted.facts.party_composition.value"
        )

    def test_patch_party_composition_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"party_composition": "4 adults"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("party_composition", {}).get("authority_level") == "explicit_user"


class TestPacePreferenceRoundtrip:
    def test_patch_pace_preference_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"pace_preference": "relaxed"})
        assert result["pace_preference"] == "relaxed"

    def test_patch_pace_preference_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"pace_preference": "moderate"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["pace_preference"] == "moderate"

    def test_patch_pace_preference_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write pace_preference into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"pace_preference": "fast"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("pace_preference", {}).get("value") == "fast", (
            "PATCH must dual-write pace_preference into extracted.facts.pace_preference.value"
        )

    def test_patch_pace_preference_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"pace_preference": "leisurely"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("pace_preference", {}).get("authority_level") == "explicit_user"


class TestDateYearConfidenceRoundtrip:
    def test_patch_date_year_confidence_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"date_year_confidence": "high"})
        assert result["date_year_confidence"] == "high"

    def test_patch_date_year_confidence_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"date_year_confidence": "medium"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["date_year_confidence"] == "medium"

    def test_patch_date_year_confidence_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write date_year_confidence into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"date_year_confidence": "low"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("date_year_confidence", {}).get("value") == "low", (
            "PATCH must dual-write date_year_confidence into extracted.facts.date_year_confidence.value"
        )

    def test_patch_date_year_confidence_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"date_year_confidence": "tentative"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("date_year_confidence", {}).get("authority_level") == "explicit_user"


class TestLeadSourceRoundtrip:
    def test_patch_lead_source_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"lead_source": "referral"})
        assert result["lead_source"] == "referral"

    def test_patch_lead_source_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"lead_source": "google_ads"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["lead_source"] == "google_ads"

    def test_patch_lead_source_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write lead_source into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"lead_source": "instagram"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("lead_source", {}).get("value") == "instagram", (
            "PATCH must dual-write lead_source into extracted.facts.lead_source.value"
        )

    def test_patch_lead_source_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"lead_source": "direct_call"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("lead_source", {}).get("authority_level") == "explicit_user"


class TestActivityProvenanceRoundtrip:
    def test_patch_activity_provenance_appears_in_patch_response(self, session_client, canonical_trip_id):
        result = _patch_trip(session_client, canonical_trip_id, {"activity_provenance": "direct_call"})
        assert result["activity_provenance"] == "direct_call"

    def test_patch_activity_provenance_persists_to_get(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"activity_provenance": "whatsapp"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["activity_provenance"] == "whatsapp"

    def test_patch_activity_provenance_dual_write_visible_in_extracted(self, session_client, canonical_trip_id):
        """_sync_manual_trip_fields must write activity_provenance into extracted.facts."""
        _patch_trip(session_client, canonical_trip_id, {"activity_provenance": "email"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("activity_provenance", {}).get("value") == "email", (
            "PATCH must dual-write activity_provenance into extracted.facts.activity_provenance.value"
        )

    def test_patch_activity_provenance_authority_is_explicit_user(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"activity_provenance": "website_form"})
        result = _get_trip(session_client, canonical_trip_id)
        facts = (result.get("extracted") or {}).get("facts", {})
        assert facts.get("activity_provenance", {}).get("authority_level") == "explicit_user"


# ---------------------------------------------------------------------------
# Cross-field preservation
# ---------------------------------------------------------------------------


class TestCrossFieldPreservation:
    def test_patch_origin_does_not_clobber_destination(self, session_client, canonical_trip_id):
        _patch_trip(session_client, canonical_trip_id, {"destination": "Barcelona"})
        _patch_trip(session_client, canonical_trip_id, {"origin": "Chicago"})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["destination"] == "Barcelona", "destination must survive an origin-only patch"
        assert result["origin"] == "Chicago"

    def test_compound_patch_all_fields_resolved(self, session_client, canonical_trip_id):
        """All core fields patched in a single request must appear in TripResponse."""
        _patch_trip(
            session_client,
            canonical_trip_id,
            {
                "origin": "Sydney",
                "destination": "Bali",
                "dateWindow": "August 2026",
                "party": 2,
                "budget": "7500",
            },
        )
        result = _get_trip(session_client, canonical_trip_id)
        assert result["origin"] == "Sydney"
        assert result["destination"] == "Bali"
        assert result["dateWindow"] == "August 2026"
        assert result["party"] == 2
        assert result["budget"] == 7500.0

    def test_sequential_patches_accumulate(self, session_client, canonical_trip_id):
        """Fields set in earlier patches must still be present after later patches."""
        _patch_trip(session_client, canonical_trip_id, {"origin": "Miami"})
        _patch_trip(session_client, canonical_trip_id, {"destination": "Cancun"})
        _patch_trip(session_client, canonical_trip_id, {"party": 6})
        result = _get_trip(session_client, canonical_trip_id)
        assert result["origin"] == "Miami"
        assert result["destination"] == "Cancun"
        assert result["party"] == 6

    def test_patch_response_matches_subsequent_get(self, session_client, canonical_trip_id):
        """State visible in PATCH response must be identical in the next GET."""
        patch_result = _patch_trip(
            session_client,
            canonical_trip_id,
            {"origin": "Dublin", "destination": "Lisbon"},
        )
        get_result = _get_trip(session_client, canonical_trip_id)
        assert get_result["origin"] == patch_result["origin"]
        assert get_result["destination"] == patch_result["destination"]


# ---------------------------------------------------------------------------
# TripResponse shape contract
# ---------------------------------------------------------------------------


class TestTripResponseShape:
    def test_get_returns_canonical_response_fields(self, session_client, canonical_trip_id):
        """GET /trips/{id} must return all TripResponse canonical fields."""
        result = _get_trip(session_client, canonical_trip_id)
        required = {"id", "status"}
        optional_canonical = {
            "origin", "destination", "dateWindow", "party", "budget",
            "tripType", "tripPurpose", "customerName",
            "party_composition", "pace_preference", "date_year_confidence",
            "activity_interests",
            "lead_source", "activity_provenance", "frontier_result",
        }
        assert required <= set(result), f"Missing required fields: {required - set(result)}"
        # All optional canonical fields present in schema (may be null)
        for field in optional_canonical:
            assert field in result, f"TripResponse must include '{field}' key (may be null)"

    def test_patch_returns_same_shape_as_get(self, session_client, canonical_trip_id):
        """PATCH response shape must match GET response shape."""
        patch_result = _patch_trip(session_client, canonical_trip_id, {"origin": "Toronto"})
        get_result = _get_trip(session_client, canonical_trip_id)
        # Both must contain the same top-level keys
        assert set(patch_result.keys()) == set(get_result.keys()), (
            "PATCH and GET must return the same TripResponse field set"
        )

    def test_from_dict_normalizes_list_trip_priorities(self):
        """Legacy/mis-shaped list values should still serialize into the string contract."""
        trip = {
            "id": "trip_listy",
            "status": "assigned",
            "trip_priorities": ["budget conscious", "relaxed pace"],
            "date_flexibility": ["plus or minus 2 days"],
            "activity_interests": ["sightseeing", "business offsite"],
        }

        result = TripResponse.from_dict(trip)

        assert result.trip_priorities == "budget conscious, relaxed pace"
        assert result.date_flexibility == "plus or minus 2 days"
        assert result.activity_interests == "sightseeing, business offsite"

    def test_from_dict_preserves_frontier_result(self):
        trip = {
            "id": "trip_frontier",
            "status": "assigned",
            "frontier_result": {
                "ghost_triggered": True,
                "sentiment_score": 0.84,
                "anxiety_alert": False,
            },
        }

        result = TripResponse.from_dict(trip)

        assert result.frontier_result is not None
        assert result.frontier_result.ghost_triggered is True
        assert result.frontier_result.sentiment_score == 0.84

    def test_from_dict_preserves_safety_payload(self):
        trip = {
            "id": "trip_safety",
            "status": "assigned",
            "safety": {
                "leaks": ["decision_state", "confidence_score"],
                "traveler_bundle_leaks": ["decision_state"],
                "sanitized_view_leaks": ["confidence_score"],
                "leakage_errors": ["decision_state", "confidence_score"],
                "leakage_passed": False,
                "strict_leakage": True,
                "is_safe": False,
            },
        }

        result = TripResponse.from_dict(trip)

        assert result.safety == trip["safety"]


# ---------------------------------------------------------------------------
# Assumption acknowledgment loop (FND-0291)
# ---------------------------------------------------------------------------


def _pipeline_extracted() -> dict:
    """Real producer output: budget without a currency marker yields
    ASSUMED-labeled facts and a populated assumption register."""
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope

    packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(
        "Planning a trip to Bali for 4 people in March 2027. Budget 500000."
    )])
    return packet.to_dict()


@pytest.fixture
def assumptions_trip_id():
    """Trip whose extracted block carries a real assumption register; cleaned up."""
    unique = uuid4().hex[:12]
    trip_id = f"tc_assumptions_{unique}"
    now = datetime.now(timezone.utc).isoformat()
    extracted = _pipeline_extracted()
    assert len(extracted["assumptions"]) > 0
    TripStore.save_trip(
        {
            "id": trip_id,
            "run_id": f"run_{unique}",
            "source": "pytest-canonical",
            "status": "assigned",
            "created_at": now,
            "updated_at": now,
            "extracted": extracted,
            "validation": {"is_valid": True, "errors": [], "warnings": []},
            "raw_input": {"fixture_id": "canonical-roundtrip-test"},
        },
        agency_id=AGENCY_ID,
    )
    try:
        yield trip_id
    finally:
        TripStore.delete_trip(trip_id)


def _assumptions_of(trip_payload: dict) -> list:
    extracted = trip_payload.get("extracted") or {}
    return extracted.get("assumptions") or []


class TestAssumptionActions:
    def test_confirm_marks_entry_acknowledged(self, session_client, assumptions_trip_id):
        result = _patch_trip(session_client, assumptions_trip_id, {
            "assumptionActions": [{"slotName": "budget_currency"}],
        })
        entry = next(a for a in _assumptions_of(result) if a["slot_name"] == "budget_currency")
        assert entry["acknowledged_by_operator"] is True
        assert entry["operator_notes"]

        persisted = _get_trip(session_client, assumptions_trip_id)
        entry = next(a for a in _assumptions_of(persisted) if a["slot_name"] == "budget_currency")
        assert entry["acknowledged_by_operator"] is True

    def test_correct_writes_explicit_user_fact_and_supersedes_entry(
        self, session_client, assumptions_trip_id,
    ):
        result = _patch_trip(session_client, assumptions_trip_id, {
            "assumptionActions": [{
                "slotName": "budget_currency",
                "correctedValue": "INR",
            }],
        })
        entry = next(a for a in _assumptions_of(result) if a["slot_name"] == "budget_currency")
        assert entry["acknowledged_by_operator"] is True
        assert "INR" in (entry["operator_notes"] or "")
        fact = (result["extracted"]["facts"] or {}).get("budget_currency")
        assert fact["value"] == "INR"
        assert fact["authority_level"] == "explicit_user"

    def test_unknown_slot_name_rejected(self, session_client, assumptions_trip_id):
        resp = session_client.patch(
            f"/trips/{assumptions_trip_id}",
            json={"assumptionActions": [{"slotName": "nonexistent_slot"}]},
        )
        assert resp.status_code == 422

    def test_budget_correction_supersedes_budget_assumptions(
        self, session_client, assumptions_trip_id,
    ):
        """The escalation must stop when the operator corrected the data via
        the existing repair surface — no separate acknowledgment needed."""
        _patch_trip(session_client, assumptions_trip_id, {"budget": "500000 INR total"})
        persisted = _get_trip(session_client, assumptions_trip_id)
        for slot_name in ("budget_currency", "budget_scope", "budget_flexibility"):
            entry = next(a for a in _assumptions_of(persisted) if a["slot_name"] == slot_name)
            assert entry["acknowledged_by_operator"] is True, slot_name
            assert "Superseded" in (entry["operator_notes"] or "")

    def test_acknowledged_register_clears_decision_escalation(
        self, session_client, assumptions_trip_id,
    ):
        """End-to-end loop closure: confirm via PATCH, rebuild the packet from
        the persisted trip, and the decision engine's
        unacknowledged_critical_assumption flag must be gone."""
        from src.intake.decision import generate_risk_flags
        from src.intake.packet_models import AssumptionRecord, CanonicalPacket

        _patch_trip(session_client, assumptions_trip_id, {
            "assumptionActions": [
                {"slotName": "budget_currency"},
                {"slotName": "budget_scope"},
            ],
        })
        persisted = _get_trip(session_client, assumptions_trip_id)

        packet = CanonicalPacket(packet_id=assumptions_trip_id)
        packet.assumptions = [
            AssumptionRecord(**entry) for entry in _assumptions_of(persisted)
        ]
        flags = generate_risk_flags(packet, stage="discovery")
        assert "unacknowledged_critical_assumption" not in [f["flag"] for f in flags]


class TestAcknowledgementCarryForward:
    """FND-0291: operator attestations survive draft reprocess. Pure merge
    logic — no store involved."""

    @staticmethod
    def _trip(assumptions: list) -> dict:
        return {"extracted": {"facts": {}, "assumptions": assumptions}}

    def test_acknowledged_entry_carried_into_new_register(self):
        from spine_api.persistence import _carry_forward_acknowledged_assumptions

        old = self._trip([{
            "slot_name": "budget_currency",
            "assumed_value": "USD",
            "rationale": "defaulted",
            "criticality": "critical",
            "acknowledged_by_operator": True,
            "operator_notes": "Confirmed by operator — system default is accurate.",
        }])
        new = self._trip([{
            "slot_name": "budget_currency",
            "assumed_value": "USD",
            "rationale": "defaulted",
            "criticality": "critical",
            "acknowledged_by_operator": False,
        }])

        _carry_forward_acknowledged_assumptions(new, old)

        entry = new["extracted"]["assumptions"][0]
        assert entry["acknowledged_by_operator"] is True
        assert entry["operator_notes"] == "Confirmed by operator — system default is accurate."

    def test_unacknowledged_entries_not_carried(self):
        from spine_api.persistence import _carry_forward_acknowledged_assumptions

        old = self._trip([{
            "slot_name": "budget_scope",
            "acknowledged_by_operator": False,
        }])
        new = self._trip([{
            "slot_name": "budget_scope",
            "acknowledged_by_operator": False,
        }])

        _carry_forward_acknowledged_assumptions(new, old)

        assert new["extracted"]["assumptions"][0]["acknowledged_by_operator"] is False

    def test_absent_slot_and_missing_registers_are_safe(self):
        from spine_api.persistence import _carry_forward_acknowledged_assumptions

        old = self._trip([{"slot_name": "budget_flexibility", "acknowledged_by_operator": True}])
        corrected = {"extracted": {"facts": {}, "assumptions": []}}
        _carry_forward_acknowledged_assumptions(corrected, old)
        assert corrected["extracted"]["assumptions"] == []

        no_register_old = {"extracted": {"facts": {}}}
        fresh = self._trip([{"slot_name": "budget_currency", "acknowledged_by_operator": False}])
        _carry_forward_acknowledged_assumptions(fresh, no_register_old)
        assert fresh["extracted"]["assumptions"][0]["acknowledged_by_operator"] is False
