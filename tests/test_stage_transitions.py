"""
tests/test_stage_transitions — Behavioral tests for durable stage transitions.

Phase 2B: PATCH /trips/{trip_id}/stage endpoint.

Tests create their own trip fixtures via TripStore.save_trip() — never depend
on pre-existing trips or pytest.skip when the DB is empty.
"""

import pytest
from unittest.mock import MagicMock

from spine_api.persistence import TEST_AGENCY_ID
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


@pytest.fixture()
def created_trip_id(session_client):
    """Create a trip directly via TripStore and return its ID.

    Uses the same agency_id as session_client's JWT so ownership checks pass.
    Cleans up the trip file after the test.
    """
    from spine_api.persistence import TripStore

    trip_data = {
        "source": "test_stage_fixture",
        "agency_id": TEST_AGENCY_ID,
        "status": "assigned",
        "stage": "discovery",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    yield trip_id
    # Cleanup
    try:
        TripStore.delete_trip(trip_id)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Stage persistence tests (model-level)
# ---------------------------------------------------------------------------

class TestStagePersistence:
    """Verify stage field persists through save/load cycle."""

    def test_default_stage_is_discovery(self):
        from spine_api.models.trips import Trip
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

    def test_valid_transition(self, session_client, created_trip_id):
        trip_id = created_trip_id

        trip_resp = session_client.get(f"/trips/{trip_id}")
        old_stage = trip_resp.json().get("stage", "discovery")

        target = "shortlist" if old_stage != "shortlist" else "proposal"

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Test transition"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["changed"] is True
        assert body["old_stage"] == old_stage
        assert body["new_stage"] == target

        # Verify persisted
        trip_resp2 = session_client.get(f"/trips/{trip_id}")
        assert trip_resp2.json().get("stage") == target

    def test_invalid_target_stage_returns_422(self, session_client, created_trip_id):
        trip_id = created_trip_id

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": "invalid_stage", "reason": "Bad stage"},
        )
        assert resp.status_code == 422

    def test_expected_current_stage_mismatch_returns_409(self, session_client, created_trip_id):
        trip_id = created_trip_id

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={
                "target_stage": "shortlist",
                "reason": "Conflict test",
                "expected_current_stage": "wrong_stage",
            },
        )
        assert resp.status_code == 409

    def test_same_stage_returns_changed_false(self, session_client, created_trip_id):
        trip_id = created_trip_id

        trip_resp = session_client.get(f"/trips/{trip_id}")
        current_stage = trip_resp.json().get("stage", "discovery")

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": current_stage, "reason": "Same stage"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["changed"] is False

    def test_status_not_affected_by_stage_change(self, session_client, created_trip_id):
        trip_id = created_trip_id

        trip_resp = session_client.get(f"/trips/{trip_id}")
        original_status = trip_resp.json().get("status")

        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": "shortlist", "reason": "Status test"},
        )

        trip_resp2 = session_client.get(f"/trips/{trip_id}")
        assert trip_resp2.json().get("status") == original_status

    def test_audit_event_written(self, session_client, created_trip_id):
        """Verify stage_transition audit event is logged."""
        from spine_api.persistence import AuditStore
        trip_id = created_trip_id

        trip_resp = session_client.get(f"/trips/{trip_id}")
        old_stage = trip_resp.json().get("stage", "discovery")
        target = "shortlist" if old_stage != "shortlist" else "proposal"

        session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": target, "reason": "Audit test"},
        )

        # Check that AuditStore has a stage_transition event
        events = AuditStore.get_events(limit=200)
        stage_events = [
            e for e in events
            if e.get("type") == "stage_transition"
            and e.get("details", {}).get("trip_id") == trip_id
        ]
        assert len(stage_events) >= 1, f"No stage_transition events found for {trip_id}"
        evt = stage_events[-1]
        details = evt.get("details", {})
        assert details.get("from") == old_stage
        assert details.get("to") == target
        assert details.get("trigger") == "manual"

    def test_generic_patch_rejects_stage(self, session_client, created_trip_id):
        """Generic PATCH /trips/{trip_id} must reject stage changes."""
        trip_id = created_trip_id

        resp = session_client.patch(
            f"/trips/{trip_id}",
            json={"stage": "booking"},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "stage" in resp.json().get("detail", "").lower()

        # Verify stage was NOT changed
        trip_resp = session_client.get(f"/trips/{trip_id}")
        assert trip_resp.json().get("stage") == "discovery"

    def test_generic_patch_still_works_for_status(self, session_client, created_trip_id):
        """Generic PATCH still works for non-stage fields."""
        trip_id = created_trip_id

        resp = session_client.patch(
            f"/trips/{trip_id}",
            json={"status": "in_progress"},
        )
        # Should not reject — only stage is blocked
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        trip_resp = session_client.get(f"/trips/{trip_id}")
        assert trip_resp.json().get("status") == "in_progress"


# ---------------------------------------------------------------------------
# Readiness + stage integration
# ---------------------------------------------------------------------------

class TestReadinessStageIntegration:
    """Verify readiness computation doesn't mutate stage."""

    def test_compute_readiness_does_not_mutate_packet_stage(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        original_stage = packet.stage
        result = compute_readiness(packet)
        assert result.suggested_next_stage == "shortlist"
        assert packet.stage == original_stage

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

    def test_readiness_snapshot_included_in_stage_response(self, session_client, created_trip_id):
        """Verify the stage transition response includes readiness from validation."""
        trip_id = created_trip_id

        # Set validation with readiness
        from spine_api.persistence import TripStore
        trip = TripStore.get_trip_for_agency(trip_id, TEST_AGENCY_ID)
        trip["validation"] = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "readiness": {
                "highest_ready_tier": "quote_ready",
                "suggested_next_stage": "shortlist",
            },
        }
        TripStore.update_trip_for_agency(trip_id, TEST_AGENCY_ID, {"validation": trip["validation"]})

        resp = session_client.patch(
            f"/trips/{trip_id}/stage",
            json={"target_stage": "shortlist", "reason": "Readiness test"},
        )
        body = resp.json()
        assert "readiness" in body
        assert body["readiness"] is not None
        assert body["readiness"]["highest_ready_tier"] == "quote_ready"
