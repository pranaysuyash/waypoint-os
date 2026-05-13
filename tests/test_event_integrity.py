"""Tests for Phase 5D event integrity validation.

Verifies that field-level validators reject bad inputs, that
emit_event_best_effort raises on programmer bugs but swallows DB errors,
and that event_type/category pairing rejects unknown types.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from spine_api.services.execution_event_service import (
    _validate_subject_type,
    _validate_source,
    _validate_category,
    _validate_event_type_category,
    _validate_actor_type,
    _validate_all,
    emit_event_best_effort,
)
from spine_api.models.tenant import (
    ALLOWED_SUBJECT_TYPES,
    ALLOWED_EVENT_SOURCES,
    ALLOWED_ACTOR_TYPES,
    EVENT_CATEGORIES,
)


# ---------------------------------------------------------------------------
# Subject type validation
# ---------------------------------------------------------------------------


class TestValidateSubjectType:
    def test_valid_subject_types_accepted(self):
        for st in ALLOWED_SUBJECT_TYPES:
            _validate_subject_type(st)

    def test_invalid_subject_type_raises(self):
        with pytest.raises(ValueError, match="Invalid subject_type"):
            _validate_subject_type("nonexistent_thing")


# ---------------------------------------------------------------------------
# Source validation
# ---------------------------------------------------------------------------


class TestValidateSource:
    def test_valid_sources_accepted(self):
        for src in ALLOWED_EVENT_SOURCES:
            _validate_source(src)

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError, match="Invalid source"):
            _validate_source("manual_entry")


# ---------------------------------------------------------------------------
# Category validation
# ---------------------------------------------------------------------------


class TestValidateCategory:
    def test_valid_categories_accepted(self):
        for cat in EVENT_CATEGORIES:
            _validate_category(cat)

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Invalid event_category"):
            _validate_category("billing")


# ---------------------------------------------------------------------------
# Event type / category pairing
# ---------------------------------------------------------------------------


class TestValidateEventTypeCategory:
    def test_task_event_type_with_task_category(self):
        _validate_event_type_category("task_created", "task")

    def test_confirmation_event_type_with_confirmation_category(self):
        _validate_event_type_category("confirmation_recorded", "confirmation")

    def test_document_event_type_with_document_category(self):
        _validate_event_type_category("document_uploaded", "document")

    def test_extraction_event_type_with_task_category_rejected(self):
        with pytest.raises(ValueError, match="not valid for category"):
            _validate_event_type_category("extraction_run_started", "task")

    def test_unknown_event_type_rejected(self):
        with pytest.raises(ValueError, match="not valid for category"):
            _validate_event_type_category("made_up_event", "task")

    def test_unknown_category_rejected(self):
        with pytest.raises(ValueError, match="Unknown event_category"):
            _validate_event_type_category("task_created", "billing")


# ---------------------------------------------------------------------------
# Actor type validation
# ---------------------------------------------------------------------------


class TestValidateActorType:
    def test_valid_actor_types_accepted(self):
        for at in ALLOWED_ACTOR_TYPES:
            _validate_actor_type(at)

    def test_invalid_actor_type_raises(self):
        with pytest.raises(ValueError, match="Invalid actor_type"):
            _validate_actor_type("customer")


# ---------------------------------------------------------------------------
# _validate_all — integration of all validators
# ---------------------------------------------------------------------------


class TestValidateAll:
    def test_valid_params_pass(self):
        _validate_all(
            subject_type="booking_task",
            source="agent_action",
            event_category="task",
            event_type="task_created",
            actor_type="agent",
            event_metadata={"task_type": "confirm_flights"},
        )

    def test_invalid_subject_type_raises(self):
        with pytest.raises(ValueError, match="Invalid subject_type"):
            _validate_all(
                subject_type="bad",
                source="agent_action",
                event_category="task",
                event_type="task_created",
                actor_type="agent",
                event_metadata=None,
            )


# ---------------------------------------------------------------------------
# emit_event_best_effort semantics
# ---------------------------------------------------------------------------


class TestBestEffortSemantics:
    @pytest.mark.asyncio
    async def test_invalid_subject_type_raises_not_swallowed(self):
        """Validation error must raise — it's a programmer bug."""
        db = AsyncMock()
        with pytest.raises(ValueError, match="Invalid subject_type"):
            await emit_event_best_effort(
                db,
                agency_id="a1", trip_id="t1",
                subject_type="bad_type", subject_id="s1",
                event_type="task_created", event_category="task",
                status_from=None, status_to="not_started",
                actor_type="system", actor_id=None, source="system_generation",
                event_metadata=None,
            )

    @pytest.mark.asyncio
    async def test_invalid_metadata_key_raises_not_swallowed(self):
        """Bad metadata key must raise — it's a programmer bug."""
        db = AsyncMock()
        with pytest.raises(ValueError):
            await emit_event_best_effort(
                db,
                agency_id="a1", trip_id="t1",
                subject_type="booking_task", subject_id="s1",
                event_type="task_created", event_category="task",
                status_from=None, status_to="not_started",
                actor_type="system", actor_id=None, source="system_generation",
                event_metadata={"customer_email": "leak@example.com"},
            )

    @pytest.mark.asyncio
    async def test_db_insert_failure_is_swallowed(self):
        """DB-level failure is caught and logged, not raised."""
        mock_savepoint = AsyncMock()
        mock_savepoint.__aenter__ = AsyncMock(side_effect=SQLAlchemyError("table missing"))
        mock_savepoint.__aexit__ = AsyncMock(return_value=False)

        db = AsyncMock()
        db.begin_nested = MagicMock(return_value=mock_savepoint)

        # Should NOT raise
        await emit_event_best_effort(
            db,
            agency_id="a1", trip_id="t1",
            subject_type="booking_task", subject_id="s1",
            event_type="task_created", event_category="task",
            status_from=None, status_to="not_started",
            actor_type="system", actor_id=None, source="system_generation",
            event_metadata={"task_type": "confirm_flights"},
        )
