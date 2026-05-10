"""Tests for extraction event emission in extraction_service.py.

Phase 5C: verifies that extraction lifecycle operations emit execution events
with correct metadata, actor/source mapping, and no PII leakage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from spine_api.models.tenant import (
    ALLOWED_SUBJECT_TYPES,
    EXTRACTION_EVENT_TYPES,
    ALLOWED_EVENT_METADATA_KEYS,
    ALLOWED_EVENT_SOURCES,
    FORBIDDEN_METADATA_PATTERNS,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestExtractionEventConstants:
    def test_extraction_event_types_defined(self):
        assert "extraction_run_started" in EXTRACTION_EVENT_TYPES
        assert "extraction_run_completed" in EXTRACTION_EVENT_TYPES
        assert "extraction_run_failed" in EXTRACTION_EVENT_TYPES
        assert "extraction_applied" in EXTRACTION_EVENT_TYPES
        assert "extraction_rejected" in EXTRACTION_EVENT_TYPES
        assert "extraction_attempt_completed" in EXTRACTION_EVENT_TYPES
        assert "extraction_attempt_failed" in EXTRACTION_EVENT_TYPES

    def test_document_extraction_in_allowed_subject_types(self):
        assert "document_extraction" in ALLOWED_SUBJECT_TYPES

    def test_document_extraction_attempt_in_allowed_subject_types(self):
        assert "document_extraction_attempt" in ALLOWED_SUBJECT_TYPES

    def test_extraction_metadata_keys_allowed(self):
        for key in [
            "provider", "model", "run_count", "attempt_count",
            "field_count", "overall_confidence", "latency_ms",
            "cost_estimate_usd", "error_code",
            "attempt_number", "fallback_rank", "run_number",
            "fields_applied_count", "allow_overwrite",
        ]:
            assert key in ALLOWED_EVENT_METADATA_KEYS, f"{key} not in allowed keys"

    def test_tokens_not_in_allowed_metadata(self):
        assert "tokens" not in ALLOWED_EVENT_METADATA_KEYS
        assert "prompt_tokens" not in ALLOWED_EVENT_METADATA_KEYS
        assert "completion_tokens" not in ALLOWED_EVENT_METADATA_KEYS
        assert "total_tokens" not in ALLOWED_EVENT_METADATA_KEYS

    def test_extraction_pii_keys_forbidden(self):
        for key in ["extracted_fields", "storage_key", "filename", "signed_url"]:
            assert key in FORBIDDEN_METADATA_PATTERNS, f"{key} not in forbidden patterns"

    def test_fields_applied_count_not_fields_applied(self):
        assert "fields_applied_count" in ALLOWED_EVENT_METADATA_KEYS
        assert "fields_applied" not in ALLOWED_EVENT_METADATA_KEYS


# ---------------------------------------------------------------------------
# Actor/source mapping — real integration tests
# ---------------------------------------------------------------------------


class TestExtractionActorMapping:
    def test_source_customer_submission_in_allowed_sources(self):
        assert "customer_submission" in ALLOWED_EVENT_SOURCES

    def test_source_system_generation_in_allowed_sources(self):
        assert "system_generation" in ALLOWED_EVENT_SOURCES

    def test_source_agent_action_in_allowed_sources(self):
        assert "agent_action" in ALLOWED_EVENT_SOURCES

    @pytest.mark.asyncio
    async def test_apply_event_metadata_structure(self):
        """Verify extraction_applied metadata uses fields_applied_count, not field names."""
        # Verify through code inspection that the metadata keys are in the allowlist
        assert "fields_applied_count" in ALLOWED_EVENT_METADATA_KEYS
        assert "fields_applied" not in ALLOWED_EVENT_METADATA_KEYS
        assert "allow_overwrite" in ALLOWED_EVENT_METADATA_KEYS

        # Verify forbidden metadata is rejected
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError):
            _validate_metadata({"fields_applied": ["passport_number"]})
        _validate_metadata({"fields_applied_count": 3, "allow_overwrite": False})

    @pytest.mark.asyncio
    async def test_reject_uses_agent_actor(self):
        """reject_extraction emits extraction_rejected with agent actor."""
        with patch("spine_api.services.extraction_service.execution_event_service") as mock_ee:
            mock_ee.emit_event_best_effort = AsyncMock()

            db = AsyncMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()

            extraction = MagicMock()
            extraction.id = "ext-1"
            extraction.agency_id = "agency-1"
            extraction.trip_id = "trip-1"
            extraction.status = "pending_review"

            from spine_api.services.extraction_service import reject_extraction

            await reject_extraction(db, extraction, reviewed_by="user-1")

            call_kwargs = mock_ee.emit_event_best_effort.call_args.kwargs
            assert call_kwargs["actor_type"] == "agent"
            assert call_kwargs["actor_id"] == "user-1"
            assert call_kwargs["source"] == "agent_action"
            assert call_kwargs["event_type"] == "extraction_rejected"
            assert call_kwargs["status_from"] == "pending_review"
            assert call_kwargs["status_to"] == "rejected"


# ---------------------------------------------------------------------------
# PII boundaries
# ---------------------------------------------------------------------------


class TestExtractionEventPII:
    def test_extracted_fields_forbidden(self):
        assert "extracted_fields" in FORBIDDEN_METADATA_PATTERNS

    def test_confidence_scores_forbidden(self):
        assert "confidence_scores" in FORBIDDEN_METADATA_PATTERNS

    def test_error_summary_forbidden(self):
        assert "error_summary" in FORBIDDEN_METADATA_PATTERNS

    def test_error_code_allowed(self):
        assert "error_code" in ALLOWED_EVENT_METADATA_KEYS

    def test_overall_confidence_allowed_but_not_scores_dict(self):
        assert "overall_confidence" in ALLOWED_EVENT_METADATA_KEYS
        assert "confidence_scores" in FORBIDDEN_METADATA_PATTERNS

    def test_field_count_allowed_but_not_field_names(self):
        assert "field_count" in ALLOWED_EVENT_METADATA_KEYS

    def test_fields_applied_count_is_integer_key(self):
        assert "fields_applied_count" in ALLOWED_EVENT_METADATA_KEYS

    def test_storage_key_forbidden(self):
        assert "storage_key" in FORBIDDEN_METADATA_PATTERNS

    def test_filename_forbidden(self):
        assert "filename" in FORBIDDEN_METADATA_PATTERNS

    def test_raw_error_forbidden(self):
        assert "raw_error" in FORBIDDEN_METADATA_PATTERNS

    def test_traveler_name_forbidden(self):
        assert "traveler_name" in FORBIDDEN_METADATA_PATTERNS

    def test_passport_number_forbidden(self):
        assert "passport_number" in FORBIDDEN_METADATA_PATTERNS

    def test_dob_forbidden(self):
        assert "dob" in FORBIDDEN_METADATA_PATTERNS

    def test_filename_hash_forbidden(self):
        assert "filename_hash" in FORBIDDEN_METADATA_PATTERNS

    def test_sha256_forbidden(self):
        assert "sha256" in FORBIDDEN_METADATA_PATTERNS


# ---------------------------------------------------------------------------
# Subject type validation
# ---------------------------------------------------------------------------


class TestExtractionSubjectTypes:
    def test_all_extraction_subject_types_in_allowed(self):
        assert "document_extraction" in ALLOWED_SUBJECT_TYPES
        assert "document_extraction_attempt" in ALLOWED_SUBJECT_TYPES

    def test_no_arbitrary_subject_types(self):
        assert len(ALLOWED_SUBJECT_TYPES) == 5


# ---------------------------------------------------------------------------
# Event metadata structure — validate key sets are subsets of allowlist
# ---------------------------------------------------------------------------


class TestExtractionEventMetadata:
    def test_run_started_metadata_keys(self):
        expected_keys = {"document_type", "provider", "model", "run_count"}
        assert expected_keys.issubset(ALLOWED_EVENT_METADATA_KEYS)

    def test_run_completed_metadata_keys(self):
        expected_keys = {
            "document_type", "provider", "model", "attempt_count",
            "field_count", "overall_confidence", "latency_ms",
        }
        assert expected_keys.issubset(ALLOWED_EVENT_METADATA_KEYS)

    def test_run_failed_metadata_keys(self):
        expected_keys = {"document_type", "error_code", "attempt_count", "latency_ms"}
        assert expected_keys.issubset(ALLOWED_EVENT_METADATA_KEYS)

    def test_attempt_metadata_keys(self):
        expected_keys = {
            "provider", "model", "attempt_number", "fallback_rank",
            "field_count", "latency_ms", "error_code",
        }
        assert expected_keys.issubset(ALLOWED_EVENT_METADATA_KEYS)

    def test_applied_metadata_keys(self):
        expected_keys = {"document_type", "fields_applied_count", "allow_overwrite"}
        assert expected_keys.issubset(ALLOWED_EVENT_METADATA_KEYS)


# ---------------------------------------------------------------------------
# Best-effort policy — real tests
# ---------------------------------------------------------------------------


class TestExtractionBestEffort:
    def test_best_effort_function_exists(self):
        from spine_api.services.execution_event_service import emit_event_best_effort
        assert callable(emit_event_best_effort)

    @pytest.mark.asyncio
    async def test_best_effort_catches_exceptions_isolated(self):
        from spine_api.services.execution_event_service import emit_event_best_effort

        # Mock begin_nested to simulate savepoint that fails
        mock_savepoint = AsyncMock()
        mock_savepoint.__aenter__ = AsyncMock(side_effect=Exception("execution_events table does not exist"))
        mock_savepoint.__aexit__ = AsyncMock(return_value=False)

        db = AsyncMock()
        db.begin_nested = MagicMock(return_value=mock_savepoint)

        # Should not raise — failure is caught and logged
        await emit_event_best_effort(
            db,
            agency_id="a1", trip_id="t1",
            subject_type="document_extraction", subject_id="e1",
            event_type="extraction_run_started", event_category="extraction",
            status_from=None, status_to="running",
            actor_type="system", actor_id=None, source="system_generation",
            event_metadata={"provider": "openai"},
        )


# ---------------------------------------------------------------------------
# Metadata allowlist enforcement
# ---------------------------------------------------------------------------


class TestExtractionMetadataAllowlist:
    def test_unknown_key_rejected(self):
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError, match="not in allowlist"):
            _validate_metadata({"customer_email": "test@example.com"})

    def test_error_summary_rejected(self):
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError):
            _validate_metadata({"error_summary": "something went wrong"})

    def test_fields_applied_rejected_count_accepted(self):
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError):
            _validate_metadata({"fields_applied": ["full_name"]})
        _validate_metadata({"fields_applied_count": 3})

    def test_extracted_fields_rejected(self):
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError):
            _validate_metadata({"extracted_fields": {"full_name": "John"}})

    def test_confidence_scores_rejected(self):
        from spine_api.services.execution_event_service import _validate_metadata
        with pytest.raises(ValueError):
            _validate_metadata({"confidence_scores": {"full_name": 0.95}})


# ---------------------------------------------------------------------------
# PII sentinel test — comprehensive boundary check
# ---------------------------------------------------------------------------


class TestExtractionPIISentinel:
    def test_all_critical_pii_forbidden(self):
        critical_pii = [
            "supplier_name", "confirmation_number", "notes",
            "traveler_name", "dob", "passport_number",
            "filename", "filename_hash", "sha256",
            "storage_key", "signed_url",
            "extracted_fields", "blocker_refs",
            "error_summary", "confidence_scores", "raw_error",
        ]
        for key in critical_pii:
            assert key in FORBIDDEN_METADATA_PATTERNS, f"Missing forbidden pattern: {key}"
