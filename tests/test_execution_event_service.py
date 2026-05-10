"""Tests for execution event service — pure unit tests, no DB."""

import pytest

from spine_api.services.execution_event_service import (
    _validate_metadata,
    emit_event,
    get_timeline,
    TimelineEvent,
    TimelineResult,
)
from spine_api.models.tenant import (
    ALLOWED_EVENT_METADATA_KEYS,
    FORBIDDEN_METADATA_PATTERNS,
    EVENT_CATEGORIES,
    TASK_EVENT_TYPES,
    CONFIRMATION_EVENT_TYPES,
)


# ── Metadata validation ──────────────────────────────────────────────────────

class TestMetadataValidation:
    def test_allowed_keys_pass(self):
        _validate_metadata({"task_type": "verify_passport"})  # should not raise

    def test_multiple_allowed_keys(self):
        _validate_metadata({
            "task_type": "confirm_flights",
            "blocker_code": "missing_document",
            "evidence_ref_count": 3,
        })

    def test_forbidden_key_supplier_name(self):
        with pytest.raises(ValueError):
            _validate_metadata({"supplier_name": "Emirates"})

    def test_forbidden_key_confirmation_number(self):
        with pytest.raises(ValueError):
            _validate_metadata({"confirmation_number": "ABC123"})

    def test_forbidden_key_notes(self):
        with pytest.raises(ValueError):
            _validate_metadata({"notes": "some text"})

    def test_forbidden_key_substring_match(self):
        """Keys containing forbidden patterns are also rejected."""
        with pytest.raises(ValueError):
            _validate_metadata({"traveler_name_extra": "value"})

    def test_none_metadata_passes(self):
        _validate_metadata(None)

    def test_empty_metadata_passes(self):
        _validate_metadata({})

    def test_unknown_key_rejected_by_allowlist(self):
        with pytest.raises(ValueError, match="not in allowlist"):
            _validate_metadata({"customer_email": "test@example.com"})

    def test_arbitrary_key_rejected_by_allowlist(self):
        with pytest.raises(ValueError, match="not in allowlist"):
            _validate_metadata({"random_field": "value"})

    def test_fields_applied_rejected_fields_applied_count_accepted(self):
        with pytest.raises(ValueError):
            _validate_metadata({"fields_applied": ["full_name", "passport_number"]})
        _validate_metadata({"fields_applied_count": 3})

    def test_error_summary_rejected_by_allowlist(self):
        with pytest.raises(ValueError):
            _validate_metadata({"error_summary": "something went wrong"})


# ── Constants ─────────────────────────────────────────────────────────────────

class TestEventConstants:
    def test_event_categories(self):
        assert set(EVENT_CATEGORIES) == {"task", "confirmation", "document", "extraction"}

    def test_task_event_types(self):
        assert "task_created" in TASK_EVENT_TYPES
        assert "task_completed" in TASK_EVENT_TYPES
        assert "task_blocked" in TASK_EVENT_TYPES
        assert "task_ready" in TASK_EVENT_TYPES
        assert "task_started" in TASK_EVENT_TYPES
        assert "task_waiting" in TASK_EVENT_TYPES
        assert "task_cancelled" in TASK_EVENT_TYPES
        assert len(TASK_EVENT_TYPES) == 7

    def test_confirmation_event_types(self):
        assert "confirmation_created" in CONFIRMATION_EVENT_TYPES
        assert "confirmation_updated" in CONFIRMATION_EVENT_TYPES
        assert "confirmation_recorded" in CONFIRMATION_EVENT_TYPES
        assert "confirmation_verified" in CONFIRMATION_EVENT_TYPES
        assert "confirmation_voided" in CONFIRMATION_EVENT_TYPES
        assert len(CONFIRMATION_EVENT_TYPES) == 5

    def test_allowed_metadata_keys(self):
        assert "task_type" in ALLOWED_EVENT_METADATA_KEYS
        assert "confirmation_type" in ALLOWED_EVENT_METADATA_KEYS
        assert "blocker_code" in ALLOWED_EVENT_METADATA_KEYS
        assert "evidence_ref_count" in ALLOWED_EVENT_METADATA_KEYS
        assert "supplier_name" not in ALLOWED_EVENT_METADATA_KEYS
        assert "confirmation_number" not in ALLOWED_EVENT_METADATA_KEYS

    def test_forbidden_patterns(self):
        assert "supplier_name" in FORBIDDEN_METADATA_PATTERNS
        assert "confirmation_number" in FORBIDDEN_METADATA_PATTERNS
        assert "notes" in FORBIDDEN_METADATA_PATTERNS
        assert "passport_number" in FORBIDDEN_METADATA_PATTERNS
        assert "blocker_refs" in FORBIDDEN_METADATA_PATTERNS


# ── Privacy invariants ────────────────────────────────────────────────────────

class TestPrivacyInvariants:
    """Verify that event types and metadata never include PII."""

    def test_task_events_have_no_title(self):
        for et in TASK_EVENT_TYPES:
            assert "title" not in et.lower()

    def test_task_events_have_no_description(self):
        for et in TASK_EVENT_TYPES:
            assert "description" not in et.lower()

    def test_confirmation_events_have_no_supplier(self):
        for et in CONFIRMATION_EVENT_TYPES:
            assert "supplier" not in et.lower()

    def test_confirmation_events_have_no_number(self):
        for et in CONFIRMATION_EVENT_TYPES:
            assert "number" not in et.lower()

    def test_allowed_metadata_excludes_all_pii(self):
        pii_keys = [
            "supplier_name", "confirmation_number", "notes",
            "traveler_name", "dob", "passport_number",
            "filename", "storage_key", "extracted_fields",
        ]
        for key in pii_keys:
            assert key not in ALLOWED_EVENT_METADATA_KEYS, f"PII key {key} should not be allowed"

    def test_forbidden_patterns_covers_critical_pii(self):
        critical = ["supplier_name", "confirmation_number", "notes", "passport_number"]
        for pattern in critical:
            assert pattern in FORBIDDEN_METADATA_PATTERNS


# ── TimelineEvent data class ─────────────────────────────────────────────────

class TestTimelineEventDataclass:
    def test_construction(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        event = TimelineEvent(
            event_type="task_created",
            event_category="task",
            subject_type="booking_task",
            subject_id="task-1",
            status_from=None,
            status_to="not_started",
            actor_type="system",
            actor_id=None,
            source="system_generation",
            event_metadata={"task_type": "verify_passport"},
            created_at=now,
        )
        assert event.event_type == "task_created"
        assert event.actor_type == "system"
        assert event.actor_id is None
        assert event.source == "system_generation"

    def test_agent_actor(self):
        event = TimelineEvent(
            event_type="task_completed",
            event_category="task",
            subject_type="booking_task",
            subject_id="task-1",
            status_from="in_progress",
            status_to="completed",
            actor_type="agent",
            actor_id="user-1",
            source="agent_action",
            event_metadata={"task_type": "confirm_flights"},
            created_at=None,
        )
        assert event.actor_type == "agent"
        assert event.actor_id == "user-1"

    def test_reconciliation_source(self):
        event = TimelineEvent(
            event_type="task_ready",
            event_category="task",
            subject_type="booking_task",
            subject_id="task-1",
            status_from="blocked",
            status_to="ready",
            actor_type="system",
            actor_id=None,
            source="reconciliation",
            event_metadata={"task_type": "verify_passport"},
            created_at=None,
        )
        assert event.source == "reconciliation"


# ── TimelineResult data class ────────────────────────────────────────────────

class TestTimelineResult:
    def test_empty_result(self):
        result = TimelineResult(events=[], summary={"total": 0, "task": 0, "confirmation": 0, "document": 0, "extraction": 0})
        assert len(result.events) == 0
        assert result.summary["total"] == 0

    def test_summary_counts(self):
        result = TimelineResult(
            events=["e1", "e2"],
            summary={"total": 2, "task": 1, "confirmation": 1, "document": 0, "extraction": 0},
        )
        assert result.summary["task"] == 1
        assert result.summary["confirmation"] == 1
