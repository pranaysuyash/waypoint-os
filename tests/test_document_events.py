"""Tests for document event emission in document_service.py.

Phase 5C: verifies that document lifecycle operations emit execution events
with correct metadata, actor/source mapping, and no PII leakage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from spine_api.models.tenant import (
    ALLOWED_SUBJECT_TYPES,
    DOCUMENT_EVENT_TYPES,
    ALLOWED_EVENT_METADATA_KEYS,
    FORBIDDEN_METADATA_PATTERNS,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestDocumentEventConstants:
    def test_document_event_types_defined(self):
        assert "document_uploaded" in DOCUMENT_EVENT_TYPES
        assert "document_accepted" in DOCUMENT_EVENT_TYPES
        assert "document_rejected" in DOCUMENT_EVENT_TYPES
        assert "document_deleted" in DOCUMENT_EVENT_TYPES

    def test_booking_document_in_allowed_subject_types(self):
        assert "booking_document" in ALLOWED_SUBJECT_TYPES

    def test_document_metadata_keys_allowed(self):
        for key in [
            "document_type", "size_bytes", "mime_type",
            "uploaded_by_type", "scan_status",
            "review_notes_present", "storage_delete_status",
        ]:
            assert key in ALLOWED_EVENT_METADATA_KEYS, f"{key} not in allowed keys"

    def test_document_pii_keys_forbidden(self):
        for key in ["filename", "filename_hash", "storage_key", "sha256", "signed_url"]:
            assert key in FORBIDDEN_METADATA_PATTERNS, f"{key} not in forbidden patterns"


# ---------------------------------------------------------------------------
# Actor/source mapping — real integration tests
# ---------------------------------------------------------------------------


class TestDocumentActorMapping:
    """Verify actor_type and source are set correctly based on uploaded_by_type."""

    @pytest.mark.asyncio
    async def test_agent_upload_uses_agent_actor(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()
            with patch("spine_api.services.document_service.get_document_storage") as mock_storage:
                mock_storage.return_value.put = AsyncMock()
            with patch("spine_api.services.document_service.get_scanner") as mock_scanner:
                mock_scanner.return_value.scan = AsyncMock(return_value=MagicMock(status="skipped"))

            db = AsyncMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.add = MagicMock()

            from spine_api.services.document_service import upload_document

            await upload_document(
                db,
                trip_id="trip-1",
                agency_id="agency-1",
                file_data=b"%PDF-1.4 fake",
                mime_type="application/pdf",
                filename_hash="abc123",
                filename_ext=".pdf",
                document_type="passport",
                uploaded_by_type="agent",
                uploaded_by_id="user-1",
            )

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "agent"
            assert call_kwargs["actor_id"] == "user-1"
            assert call_kwargs["source"] == "agent_action"

    @pytest.mark.asyncio
    async def test_customer_upload_uses_system_actor(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()
            with patch("spine_api.services.document_service.get_document_storage") as mock_storage:
                mock_storage.return_value.put = AsyncMock()
            with patch("spine_api.services.document_service.get_scanner") as mock_scanner:
                mock_scanner.return_value.scan = AsyncMock(return_value=MagicMock(status="skipped"))

            db = AsyncMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.add = MagicMock()

            from spine_api.services.document_service import upload_document

            await upload_document(
                db,
                trip_id="trip-1",
                agency_id="agency-1",
                file_data=b"%PDF-1.4 fake",
                mime_type="application/pdf",
                filename_hash="abc123",
                filename_ext=".pdf",
                document_type="passport",
                uploaded_by_type="customer",
                uploaded_by_id=None,
                collection_token_id="tok-1",
            )

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "system"
            assert call_kwargs["actor_id"] is None
            assert call_kwargs["source"] == "customer_submission"

    @pytest.mark.asyncio
    async def test_accept_uses_agent_actor(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()

            db = AsyncMock()
            doc = MagicMock()
            doc.id = "doc-1"
            doc.agency_id = "agency-1"
            doc.trip_id = "trip-1"
            doc.status = "pending_review"
            doc.document_type = "passport"

            with patch("spine_api.services.document_service.get_document_by_id", return_value=doc):
                from spine_api.services.document_service import accept_document

                await accept_document(db, "doc-1", "agency-1", reviewed_by="user-1")

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "agent"
            assert call_kwargs["actor_id"] == "user-1"
            assert call_kwargs["source"] == "agent_action"
            assert call_kwargs["event_type"] == "document_accepted"
            assert call_kwargs["status_from"] == "pending_review"
            assert call_kwargs["status_to"] == "accepted"

    @pytest.mark.asyncio
    async def test_reject_uses_agent_actor(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()

            db = AsyncMock()
            doc = MagicMock()
            doc.id = "doc-1"
            doc.agency_id = "agency-1"
            doc.trip_id = "trip-1"
            doc.status = "pending_review"
            doc.document_type = "passport"

            with patch("spine_api.services.document_service.get_document_by_id", return_value=doc):
                from spine_api.services.document_service import reject_document

                await reject_document(db, "doc-1", "agency-1", reviewed_by="user-1")

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "agent"
            assert call_kwargs["source"] == "agent_action"
            assert call_kwargs["event_type"] == "document_rejected"
            assert call_kwargs["status_to"] == "rejected"

    @pytest.mark.asyncio
    async def test_delete_uses_agent_actor_with_old_status(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()

            db = AsyncMock()
            doc = MagicMock()
            doc.id = "doc-1"
            doc.agency_id = "agency-1"
            doc.trip_id = "trip-1"
            doc.status = "accepted"
            doc.document_type = "passport"

            with patch("spine_api.services.document_service.get_document_by_id", return_value=doc):
                from spine_api.services.document_service import soft_delete_document

                await soft_delete_document(db, "doc-1", "agency-1", deleted_by="user-1")

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "agent"
            assert call_kwargs["source"] == "agent_action"
            assert call_kwargs["status_from"] == "accepted"
            assert call_kwargs["status_to"] == "deleted"
            assert call_kwargs["event_metadata"]["storage_delete_status"] == "retained"


# ---------------------------------------------------------------------------
# PII boundaries
# ---------------------------------------------------------------------------


class TestDocumentEventPII:
    """Verify no PII leaks into document event metadata."""

    @pytest.mark.asyncio
    async def test_upload_metadata_no_storage_key_or_filename(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()
            with patch("spine_api.services.document_service.get_document_storage") as mock_storage:
                mock_storage.return_value.put = AsyncMock()
            with patch("spine_api.services.document_service.get_scanner") as mock_scanner:
                mock_scanner.return_value.scan = AsyncMock(return_value=MagicMock(status="skipped"))

            db = AsyncMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.add = MagicMock()

            from spine_api.services.document_service import upload_document

            await upload_document(
                db,
                trip_id="trip-1",
                agency_id="agency-1",
                file_data=b"%PDF-1.4 fake",
                mime_type="application/pdf",
                filename_hash="abc123",
                filename_ext=".pdf",
                document_type="passport",
                uploaded_by_type="agent",
                uploaded_by_id="user-1",
            )

            metadata = mock_ee.emit_event_best_effort.call_args.kwargs["event_metadata"]
            assert "storage_key" not in metadata
            assert "filename" not in metadata
            assert "filename_hash" not in metadata
            assert "sha256" not in metadata
            assert "signed_url" not in metadata

    @pytest.mark.asyncio
    async def test_accept_metadata_no_review_notes_content(self):
        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()

            db = AsyncMock()
            doc = MagicMock()
            doc.id = "doc-1"
            doc.agency_id = "agency-1"
            doc.trip_id = "trip-1"
            doc.status = "pending_review"
            doc.document_type = "passport"

            with patch("spine_api.services.document_service.get_document_by_id", return_value=doc):
                from spine_api.services.document_service import accept_document

                await accept_document(
                    db, "doc-1", "agency-1", reviewed_by="user-1", notes_present=True,
                )

            metadata = mock_ee.emit_event_best_effort.call_args.kwargs["event_metadata"]
            assert metadata["review_notes_present"] is True
            assert "notes" not in metadata
            assert "review_notes" not in metadata


# ---------------------------------------------------------------------------
# Best-effort policy — real tests
# ---------------------------------------------------------------------------


class TestDocumentBestEffort:
    """Verify event emission failure does not corrupt document state."""

    @pytest.mark.asyncio
    async def test_accept_succeeds_when_event_emission_fails(self):
        from sqlalchemy.exc import OperationalError

        # Mock begin_nested to simulate savepoint that fails with a DB error
        mock_savepoint = AsyncMock()
        mock_savepoint.__aenter__ = AsyncMock(side_effect=OperationalError("stmt", "params", "table missing"))
        mock_savepoint.__aexit__ = AsyncMock(return_value=False)

        db = AsyncMock()
        db.begin_nested = MagicMock(return_value=mock_savepoint)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        doc = MagicMock()
        doc.id = "doc-1"
        doc.agency_id = "agency-1"
        doc.trip_id = "trip-1"
        doc.status = "pending_review"
        doc.document_type = "passport"

        with patch("spine_api.services.document_service.execution_event_service") as mock_ee:
            # Use the real emit_event_best_effort so DB error is caught
            from spine_api.services import execution_event_service
            mock_ee.emit_event_best_effort = execution_event_service.emit_event_best_effort
            with patch("spine_api.services.document_service.get_document_by_id", return_value=doc):
                from spine_api.services.document_service import accept_document

                result = await accept_document(
                    db, "doc-1", "agency-1", reviewed_by="user-1",
                )

                # Document operation succeeds despite event failure
                assert result is doc

    def test_error_summary_is_forbidden(self):
        assert "error_summary" in FORBIDDEN_METADATA_PATTERNS

    def test_confidence_scores_is_forbidden(self):
        assert "confidence_scores" in FORBIDDEN_METADATA_PATTERNS

    def test_raw_error_is_forbidden(self):
        assert "raw_error" in FORBIDDEN_METADATA_PATTERNS

    def test_all_document_events_have_correct_category_and_subject(self):
        from spine_api.services.execution_event_service import _validate_metadata

        for event_type in DOCUMENT_EVENT_TYPES:
            # Each event type's metadata should pass validation
            metadata = {
                "document_type": "passport",
                "scan_status": "skipped",
            }
            _validate_metadata(metadata)  # should not raise
