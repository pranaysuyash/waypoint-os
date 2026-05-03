"""
tests/test_stage_transitions — Behavioral tests for durable stage transitions.

Phase 2B: PATCH /trips/{trip_id}/stage endpoint.
"""

import pytest
from unittest.mock import MagicMock

from intake.packet_models import CanonicalPacket, Slot
from intake.readiness import compute_readiness


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_packet(**fact_values):
    packet = CanonicalPacket(packet_id="test-stage")
    for name, value in fact_values.items():
        packet.facts[name] = Slot(value=value, confidence=0.9, authority_level="explicit_user")
    return packet


def _full_pipeline_outputs():
    return {
        "traveler_bundle": {"traveler_name": "Jane Doe"},
        "internal_bundle": {"session_goal": "Build proposal"},
        "safety": {"leaks": [], "is_safe": True},
        "fees": {"total_base_fee": 150},
        "decision": {
            "decision_state": "PROCEED_INTERNAL_DRAFT",
            "hard_blockers": [],
        },
    }


QUOTE_READY_FACTS = {
    "destination_candidates": "Singapore",
    "date_window": "June 2026",
    "origin_city": "Bangalore",
    "party_size": 4,
    "budget_raw_text": "2.5L INR",
    "trip_purpose": "Family Leisure",
}


def _get_any_trip_id(session_client):
    """Get any trip ID from the /trips endpoint."""
    resp = session_client.get("/trips")
    body = resp.json()
    items = body.get("items", [])
    if not items:
        pytest.skip("No trips in database")
    return items[0]["id"]


# ---------------------------------------------------------------------------
# Stage persistence tests (model-level)
# ---------------------------------------------------------------------------

class TestStagePersistence:
    """Verify stage field persists through save/load cycle."""

    def test_default_stage_is_discovery(self):
        from spine_api.models.trips import Trip
        trip = Trip(id="test-stage-default")
        # SQLAlchemy mapped_column default applies at DB flush, not Python init
        # But we can check the column default value
        from spine_api.models.trips import Trip as TripModel
        stage_col = TripModel.__table__.c.stage
        assert stage_col.default.arg == "discovery"

    def test_stage_persists_on_save(self):
        """Verify _to_dict includes stage."""
        from spine_api.persistence import SQLTripStore
        trip_obj = MagicMock()
        trip_obj.id = "trip_stage_test"
        trip_obj.stage = "shortlist"
        trip_obj.status = "assigned"
        trip_obj.run_id = None
        trip_obj.agency_id = "agency-1"
        trip_obj.user_id = None
        trip_obj.source = "test"
        trip_obj.follow_up_due_date = None
        trip_obj.party_composition = None
        trip_obj.pace_preference = None
        trip_obj.date_year_confidence = None
        trip_obj.lead_source = None
        trip_obj.activity_provenance = None
        trip_obj.extracted = {}
        trip_obj.validation = {}
        trip_obj.decision = {}
        trip_obj.strategy = None
        trip_obj.traveler_bundle = None
        trip_obj.internal_bundle = None
        trip_obj.safety = {}
        trip_obj.frontier_result = None
        trip_obj.fees = None
        trip_obj.raw_input = {}
        trip_obj.analytics = None
        trip_obj.created_at = None
        trip_obj.updated_at = None

        result = SQLTripStore._to_dict(trip_obj)
        assert result["stage"] == "shortlist"

    def test_build_processed_trip_includes_stage(self):
        """Verify _build_processed_trip derives stage from spine output."""
        from spine_api.persistence import _build_processed_trip

        spine_output = {
            "meta": {"stage": "shortlist"},
            "packet": {"stage": "discovery"},
            "validation": {},
        }
        result = _build_processed_trip(
            spine_output=spine_output,
            source="test",
            user_id="user-1",
            follow_up_due_date=None,
            party_composition=None,
            pace_preference=None,
            date_year_confidence=None,
            lead_source=None,
            activity_provenance=None,
            trip_status="assigned",
        )
        assert result["stage"] == "shortlist"

    def test_build_processed_trip_defaults_to_discovery(self):
        """When no stage in meta or packet, default to discovery."""
        from spine_api.persistence import _build_processed_trip

        spine_output = {
            "meta": {},
            "packet": {},
            "validation": {},
        }
        result = _build_processed_trip(
            spine_output=spine_output,
            source="test",
            user_id="user-1",
            follow_up_due_date=None,
            party_composition=None,
            pace_preference=None,
            date_year_confidence=None,
            lead_source=None,
            activity_provenance=None,
            trip_status="new",
        )
        assert result["stage"] == "discovery"


# ---------------------------------------------------------------------------
# Stage transition endpoint tests
# ---------------------------------------------------------------------------

class TestStageTransitionEndpoint:
    """Test PATCH /trips/{trip_id}/stage endpoint behavior."""

    def test_valid_transition(self, session_client):
        trip_id = _get_any_trip_id(session_client)

        trip_resp = session_client.get(f"/trips/{trip_id}")
        old_stage = trip_resp.json().get("stage", "discovery")

        target = "shortlist" if old_stage != "shortlist" else "proposal"

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Test transition"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["changed"] is True
        assert body["old_stage"] == old_stage
        assert body["new_stage"] == target

        # Verify persisted
        trip_resp2 = session_client.get(f"/trips/{trip_id}")
        assert trip_resp2.json().get("stage") == target

        # Revert for test isolation
        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": old_stage, "reason": "Test cleanup"},
        )

    def test_invalid_target_stage_returns_422(self, session_client):
        trip_id = _get_any_trip_id(session_client)

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": "invalid_stage", "reason": "Bad stage"},
        )
        assert resp.status_code == 422

    def test_expected_current_stage_mismatch_returns_409(self, session_client):
        trip_id = _get_any_trip_id(session_client)

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={
                "target_stage": "shortlist",
                "reason": "Conflict test",
                "expected_current_stage": "wrong_stage",
            },
        )
        assert resp.status_code == 409

    def test_same_stage_returns_changed_false(self, session_client):
        trip_id = _get_any_trip_id(session_client)

        trip_resp = session_client.get(f"/trips/{trip_id}")
        current_stage = trip_resp.json().get("stage", "discovery")

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": current_stage, "reason": "Same stage"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["changed"] is False

    def test_status_not_affected_by_stage_change(self, session_client):
        trip_id = _get_any_trip_id(session_client)

        trip_resp = session_client.get(f"/trips/{trip_id}")
        original_status = trip_resp.json().get("status")
        old_stage = trip_resp.json().get("stage", "discovery")

        target = "shortlist" if old_stage != "shortlist" else "proposal"
        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Status test"},
        )

        trip_resp2 = session_client.get(f"/trips/{trip_id}")
        assert trip_resp2.json().get("status") == original_status

        # Cleanup
        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": old_stage, "reason": "Cleanup"},
        )

    def test_audit_event_written(self, session_client):
        """Verify stage_transition audit event is logged."""
        from spine_api.persistence import AuditStore
        trip_id = _get_any_trip_id(session_client)

        trip_resp = session_client.get(f"/trips/{trip_id}")
        old_stage = trip_resp.json().get("stage", "discovery")
        target = "shortlist" if old_stage != "shortlist" else "proposal"

        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Audit test"},
        )

        # Check that AuditStore has a stage_transition event
        # Use get_events (not get_events_for_trip) because audit_bridge writes
        # resource_id as a separate field, not nested inside details.trip_id
        events = AuditStore.get_events() if hasattr(AuditStore, "get_events") else []
        stage_events = [
            e for e in events
            if e.get("type") == "stage_transition"
            and e.get("details", {}).get("to") == target
        ]
        assert len(stage_events) >= 1, f"No stage_transition events found for {trip_id}"
        evt = stage_events[-1]
        details = evt.get("details", {})
        assert details.get("from") == old_stage
        assert details.get("to") == target
        assert details.get("trigger") == "manual"

        # Cleanup
        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": old_stage, "reason": "Cleanup"},
        )


# ---------------------------------------------------------------------------
# Readiness + stage integration
# ---------------------------------------------------------------------------

class TestReadinessStageIntegration:
    """Verify readiness computation doesn't mutate stage."""

    def test_compute_readiness_does_not_mutate_packet_stage(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        original_stage = packet.stage  # CanonicalPacket has its own stage field
        result = compute_readiness(packet)
        assert result.suggested_next_stage == "shortlist"
        assert packet.stage == original_stage  # Stage should be unchanged

    def test_readiness_suggests_shortlist_for_quote_ready(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        outputs = _full_pipeline_outputs()
        result = compute_readiness(
            packet,
            traveler_bundle=outputs["traveler_bundle"],
            internal_bundle=outputs["internal_bundle"],
            safety=outputs["safety"],
            fees=outputs["fees"],
            decision=outputs["decision"],
        )
        assert result.highest_ready_tier == "quote_ready"
        assert result.suggested_next_stage == "shortlist"

    def test_readiness_snapshot_included_in_stage_response(self, session_client):
        """Verify the stage transition response includes readiness from validation."""
        trip_id = _get_any_trip_id(session_client)
        trip_resp = session_client.get(f"/trips/{trip_id}")
        old_stage = trip_resp.json().get("stage", "discovery")
        target = "shortlist" if old_stage != "shortlist" else "proposal"

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Readiness test"},
        )
        body = resp.json()
        # readiness field should be present (may be null if no validation)
        assert "readiness" in body

        # Cleanup
        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": old_stage, "reason": "Cleanup"},
        )
