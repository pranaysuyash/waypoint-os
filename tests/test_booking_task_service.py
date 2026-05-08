"""Tests for booking task service layer — pure unit tests, no DB."""

import pytest

from spine_api.services.booking_task_service import (
    _generation_hash,
    _make_title,
    _validate_transition,
    _compute_task_candidates,
    TERMINAL_STATUSES,
    SYSTEM_SOURCES,
)


# ── Generation hash ────────────────────────────────────────────────────────

class TestGenerationHash:
    def test_deterministic(self):
        h1 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1", None)
        h2 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1", None)
        assert h1 == h2

    def test_different_agency_different_hash(self):
        h1 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1", None)
        h2 = _generation_hash("a2", "t1", "verify_passport", "readiness_generated", "tv-1", None)
        assert h1 != h2

    def test_different_task_type_different_hash(self):
        h1 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1", None)
        h2 = _generation_hash("a1", "t1", "verify_insurance", "readiness_generated", "tv-1", None)
        assert h1 != h2

    def test_no_traveler_same_hash_as_empty(self):
        h1 = _generation_hash("a1", "t1", "confirm_flights", "readiness_generated", None, None)
        h2 = _generation_hash("a1", "t1", "confirm_flights", "readiness_generated", "", None)
        assert h1 == h2

    def test_blocker_refs_key_order_invariant(self):
        h1 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1",
                              {"traveler_id": "tv-1", "document_type": "passport"})
        h2 = _generation_hash("a1", "t1", "verify_passport", "readiness_generated", "tv-1",
                              {"document_type": "passport", "traveler_id": "tv-1"})
        assert h1 == h2

    def test_hash_length_32(self):
        h = _generation_hash("a1", "t1", "confirm_flights", "readiness_generated", None, None)
        assert len(h) == 32


# ── Title generation ────────────────────────────────────────────────────────

class TestMakeTitle:
    def test_template_with_ordinal(self):
        assert _make_title("verify_passport", 1) == "Verify passport for Traveler 1"
        assert _make_title("verify_traveler_details", 3) == "Verify traveler details for Traveler 3"

    def test_template_without_ordinal(self):
        assert _make_title("confirm_flights") == "Confirm flights"
        assert _make_title("send_final_confirmation") == "Send final confirmation"

    def test_unknown_type_falls_back(self):
        assert _make_title("custom_step") == "Custom Step"

    def test_no_pii_in_title(self):
        title = _make_title("verify_passport", 1)
        assert "passport" in title.lower()
        # No name, number, or other PII
        assert "John" not in title
        assert "ABC123" not in title


# ── Transition validation ───────────────────────────────────────────────────

class TestTransitionValidation:
    def test_same_status_ok(self):
        _validate_transition("not_started", "not_started")

    def test_valid_not_started_to_ready(self):
        _validate_transition("not_started", "ready")

    def test_valid_not_started_to_blocked(self):
        _validate_transition("not_started", "blocked")

    def test_valid_not_started_to_cancelled(self):
        _validate_transition("not_started", "cancelled")

    def test_invalid_not_started_to_completed(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            _validate_transition("not_started", "completed")

    def test_valid_in_progress_to_completed(self):
        _validate_transition("in_progress", "completed")

    def test_valid_in_progress_to_waiting(self):
        _validate_transition("in_progress", "waiting_on_customer")

    def test_invalid_completed_to_anything(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            _validate_transition("completed", "in_progress")

    def test_invalid_cancelled_to_anything(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            _validate_transition("cancelled", "not_started")

    def test_blocked_cannot_complete(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            _validate_transition("blocked", "completed")

    def test_blocked_to_ready(self):
        _validate_transition("blocked", "ready")


# ── Constants ───────────────────────────────────────────────────────────────

class TestConstants:
    def test_terminal_statuses(self):
        assert TERMINAL_STATUSES == frozenset({"completed", "cancelled"})

    def test_system_sources(self):
        assert "readiness_generated" in SYSTEM_SOURCES
        assert "agent_created" not in SYSTEM_SOURCES


# ── Task candidates ─────────────────────────────────────────────────────────

class TestComputeTaskCandidates:
    def _state(self, travelers=None, documents=None, extractions=None):
        return {
            "booking_data": {"travelers": travelers or []},
            "documents": documents or [],
            "extractions": extractions or [],
        }

    def test_no_travelers_no_tasks(self):
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=[]))
        assert candidates == []

    def test_one_traveler_generates_per_traveler_tasks(self):
        travelers = [{"traveler_id": "tv-1", "full_name": "John Doe", "date_of_birth": "1990-01-01"}]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        types = [c["task_type"] for c in candidates]
        assert "verify_traveler_details" in types
        assert "verify_passport" in types
        assert "verify_insurance" in types
        # Booking-level tasks
        assert "confirm_flights" in types
        assert "confirm_hotels" in types
        assert "collect_payment_proof" in types
        assert "send_final_confirmation" in types

    def test_missing_traveler_fields_causes_blocker(self):
        travelers = [{"traveler_id": "tv-1"}]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        vtd = [c for c in candidates if c["task_type"] == "verify_traveler_details"]
        assert len(vtd) == 1
        assert vtd[0]["blocker_code"] == "missing_booking_data"
        assert vtd[0]["blocker_refs"] is not None

    def test_complete_traveler_no_blocker(self):
        travelers = [{"traveler_id": "tv-1", "full_name": "John", "date_of_birth": "1990-01-01"}]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        vtd = [c for c in candidates if c["task_type"] == "verify_traveler_details"]
        assert len(vtd) == 1
        assert vtd[0]["blocker_code"] is None

    def test_passport_missing_field_blocked(self):
        travelers = [{"traveler_id": "tv-1", "full_name": "John", "date_of_birth": "1990-01-01"}]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        vp = [c for c in candidates if c["task_type"] == "verify_passport"]
        assert len(vp) == 1
        assert vp[0]["blocker_code"] == "missing_passport_field"

    def test_candidates_include_agency_and_trip(self):
        travelers = [{"traveler_id": "tv-1", "full_name": "John", "date_of_birth": "1990-01-01"}]
        candidates = _compute_task_candidates("trip-42", "agency-99", self._state(travelers=travelers))

        for c in candidates:
            assert c["agency_id"] == "agency-99"
            assert c["trip_id"] == "trip-42"

    def test_two_travelers_generates_double_per_traveler_tasks(self):
        travelers = [
            {"traveler_id": "tv-1", "full_name": "A", "date_of_birth": "1990-01-01"},
            {"traveler_id": "tv-2", "full_name": "B", "date_of_birth": "1991-01-01"},
        ]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        vtd = [c for c in candidates if c["task_type"] == "verify_traveler_details"]
        assert len(vtd) == 2
        ordinals = {c["traveler_ordinal"] for c in vtd}
        assert ordinals == {1, 2}

    def test_empty_state_returns_empty(self):
        candidates = _compute_task_candidates("t1", "a1", {})
        assert candidates == []

    def test_booking_level_tasks_have_no_traveler(self):
        travelers = [{"traveler_id": "tv-1", "full_name": "John", "date_of_birth": "1990-01-01"}]
        candidates = _compute_task_candidates("t1", "a1", self._state(travelers=travelers))

        booking_tasks = [c for c in candidates if c["task_type"] in
                         ("confirm_flights", "confirm_hotels", "collect_payment_proof", "send_final_confirmation")]
        for bt in booking_tasks:
            assert bt["traveler_id"] is None
            assert bt["traveler_ordinal"] is None
            assert bt["blocker_code"] is None
