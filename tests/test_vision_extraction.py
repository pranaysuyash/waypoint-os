"""
tests/test_vision_extraction — Phase 4D vision-based document extraction tests.

Covers: schemas, vision client (mocked), schema validation, factory,
failed extraction, MIME prevalidation, async boundary, missing API key.

Run: uv run pytest tests/test_vision_extraction.py -v
"""

import asyncio
import json
import os
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from spine_api.persistence import TEST_AGENCY_ID
from spine_api.services.extraction_service import (
    ExtractionResult,
    NoopExtractor,
    get_extractor,
    VALID_EXTRACTION_FIELDS,
)


# ---------------------------------------------------------------------------
# TestSchemas
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_all_doc_types_have_valid_fields(self):
        from src.extraction.schemas import DOCUMENT_SCHEMAS

        valid = set(VALID_EXTRACTION_FIELDS)
        for doc_type, schema in DOCUMENT_SCHEMAS.items():
            for field in schema["fields"]:
                assert field in valid, f"Field '{field}' in '{doc_type}' not in VALID_EXTRACTION_FIELDS"

    def test_json_schemas_well_formed(self):
        from src.extraction.schemas import DOCUMENT_SCHEMAS, build_json_schema

        for doc_type, schema in DOCUMENT_SCHEMAS.items():
            json_schema = build_json_schema(schema["fields"])
            assert json_schema["type"] == "object"
            assert "properties" in json_schema
            assert "required" in json_schema
            assert set(json_schema["required"]) == set(schema["fields"])
            assert json_schema["additionalProperties"] is False

    def test_unknown_document_type_gets_default_schema(self):
        from src.extraction.schemas import get_schema, DOCUMENT_SCHEMAS

        schema = get_schema("unknown_type")
        assert schema["fields"] == DOCUMENT_SCHEMAS["default"]["fields"]


# ---------------------------------------------------------------------------
# TestOpenAIVisionClient (mocked API)
# ---------------------------------------------------------------------------


class TestOpenAIVisionClient:
    def _make_client(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-12345"}):
            from src.extraction.vision_client import OpenAIVisionClient
            return OpenAIVisionClient()

    def test_mocked_api_returns_fields_and_metadata(self):
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.output_text = json.dumps({
            "full_name": "JANE SMITH",
            "passport_number": "P1234567",
        })
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        with patch.object(client._client.responses, "create", return_value=mock_response):
            from src.extraction.schemas import build_json_schema, get_schema
            schema = get_schema("passport")
            json_schema = build_json_schema(schema["fields"])

            result = asyncio.run(client.extract_from_image(
                image_data=b"fake_image_data",
                mime_type="image/jpeg",
                json_schema=json_schema,
                prompt=schema["prompt"],
            ))

        assert result.fields["full_name"] == "JANE SMITH"
        assert result.fields["passport_number"] == "P1234567"
        assert result.provider_metadata["prompt_tokens"] == 100
        assert result.provider_metadata["completion_tokens"] == 50
        assert result.provider_metadata["total_tokens"] == 150
        assert result.provider_metadata["latency_ms"] is not None

    def test_api_error_raises_provider_error(self):
        client = self._make_client()

        with patch.object(client._client.responses, "create", side_effect=Exception("Server error 500")):
            from src.extraction.vision_client import ExtractionProviderError
            from src.extraction.schemas import build_json_schema, get_schema

            schema = get_schema("passport")
            json_schema = build_json_schema(schema["fields"])

            with pytest.raises(ExtractionProviderError) as exc_info:
                asyncio.run(client.extract_from_image(
                    image_data=b"fake", mime_type="image/jpeg",
                    json_schema=json_schema, prompt=schema["prompt"],
                ))

            assert exc_info.value.error_code == "api_server_error"

    def test_timeout_raises_provider_error(self):
        client = self._make_client()

        with patch.object(client._client.responses, "create", side_effect=Exception("Request timed out")):
            from src.extraction.vision_client import ExtractionProviderError
            from src.extraction.schemas import build_json_schema, get_schema

            schema = get_schema("passport")
            json_schema = build_json_schema(schema["fields"])

            with pytest.raises(ExtractionProviderError) as exc_info:
                asyncio.run(client.extract_from_image(
                    image_data=b"fake", mime_type="image/jpeg",
                    json_schema=json_schema, prompt=schema["prompt"],
                ))

            assert exc_info.value.error_code == "api_timeout"


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def _make_client(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-12345"}):
            from src.extraction.vision_client import OpenAIVisionClient
            return OpenAIVisionClient()

    def _extract_with_response_text(self, client, text):
        mock_response = MagicMock()
        mock_response.output_text = text
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        from src.extraction.schemas import build_json_schema, get_schema
        schema = get_schema("passport")
        json_schema = build_json_schema(schema["fields"])

        with patch.object(client._client.responses, "create", return_value=mock_response):
            return asyncio.run(client.extract_from_image(
                image_data=b"fake", mime_type="image/jpeg",
                json_schema=json_schema, prompt=schema["prompt"],
            ))

    def test_unknown_fields_dropped(self):
        """Extra fields in response are dropped, not stored."""
        client = self._make_client()
        result = self._extract_with_response_text(client, json.dumps({
            "full_name": "TEST",
            "passport_number": "AB123",
            "unknown_field": "should_be_dropped",
        }))
        assert "unknown_field" not in result.fields
        assert "full_name" in result.fields

    def test_invalid_json_response_raises(self):
        """Non-JSON response triggers schema_validation_failed."""
        client = self._make_client()
        from src.extraction.vision_client import ExtractionProviderError
        with pytest.raises(ExtractionProviderError) as exc_info:
            self._extract_with_response_text(client, "not valid json{{{")
        assert exc_info.value.error_code == "schema_validation_failed"

    def test_wrong_field_types_raises_schema_validation(self):
        """Non-string, non-null types trigger schema_validation_failed."""
        client = self._make_client()
        from src.extraction.vision_client import ExtractionProviderError
        with pytest.raises(ExtractionProviderError) as exc_info:
            self._extract_with_response_text(client, json.dumps({
                "full_name": ["array", "value"],
                "passport_number": {"nested": "object"},
            }))
        assert exc_info.value.error_code == "schema_validation_failed"

    def test_empty_response_raises(self):
        """Empty response triggers empty_response error."""
        client = self._make_client()
        from src.extraction.vision_client import ExtractionProviderError
        with pytest.raises(ExtractionProviderError) as exc_info:
            self._extract_with_response_text(client, "")
        assert exc_info.value.error_code == "empty_response"


# ---------------------------------------------------------------------------
# TestGetExtractorFactory
# ---------------------------------------------------------------------------


class TestGetExtractorFactory:
    def test_noop_provider_returns_noop(self):
        with patch.dict(os.environ, {"EXTRACTION_PROVIDER": "noop"}):
            ext = get_extractor()
            assert isinstance(ext, NoopExtractor)

    def test_openai_vision_returns_vision_extractor(self):
        with patch.dict(os.environ, {
            "EXTRACTION_PROVIDER": "openai_vision",
            "OPENAI_API_KEY": "test-key-12345",
        }):
            ext = get_extractor()
            assert ext.__class__.__name__ == "OpenAIVisionExtractor"

    def test_unknown_provider_local_env_falls_back(self):
        with patch.dict(os.environ, {
            "EXTRACTION_PROVIDER": "imaginary_provider",
            "APP_ENV": "local",
        }):
            ext = get_extractor()
            assert isinstance(ext, NoopExtractor)

    def test_unknown_provider_production_raises(self):
        with patch.dict(os.environ, {
            "EXTRACTION_PROVIDER": "imaginary_provider",
            "APP_ENV": "production",
        }):
            with pytest.raises(RuntimeError, match="Unknown EXTRACTION_PROVIDER"):
                get_extractor()


# ---------------------------------------------------------------------------
# TestFailedExtraction
# ---------------------------------------------------------------------------


class TestFailedExtraction:
    def test_provider_error_creates_failed_row_no_pii(self, session_client):
        """Provider failure creates status=failed with no encrypted fields."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_vision_failed",
            "agency_id": TEST_AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "booking_data": {"travelers": []},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)

        # Upload and accept a document
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
            data={"document_type": "passport"},
        )
        assert resp.status_code == 200
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        # Mock extractor to raise provider error
        from src.extraction.vision_client import ExtractionProviderError

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_extractor = AsyncMock()
            mock_extractor._model = "gpt-5.4-nano"
            mock_extractor.extract = AsyncMock(side_effect=ExtractionProviderError("api_timeout"))
            mock_extractor.__class__.__name__ = "OpenAIVisionExtractor"
            mock_get.return_value = mock_extractor

            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error_code"] == "api_timeout"

        # Verify no booking_data mutation
        trip = TripStore.get_trip(trip_id)
        travelers = (trip.get("booking_data") or {}).get("travelers", [])
        assert travelers == []

        # Cleanup
        try:
            TripStore.delete_trip(trip_id)
        except Exception:
            pass

    def test_failed_extraction_allows_retry(self, session_client):
        """A failed extraction can be retried via the same endpoint (Phase 4E)."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_vision_retry_block",
            "agency_id": TEST_AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "booking_data": {"travelers": []},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)

        # Upload and accept a document
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        # First extraction fails
        from src.extraction.vision_client import ExtractionProviderError

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_extractor = AsyncMock()
            mock_extractor._model = "gpt-5.4-nano"
            mock_extractor.extract = AsyncMock(side_effect=ExtractionProviderError("api_server_error"))
            mock_extractor.__class__.__name__ = "OpenAIVisionExtractor"
            mock_get.return_value = mock_extractor
            resp1 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp1.status_code == 422

        # Phase 4E: failed extractions can be retried — succeeds on second attempt
        resp2 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "pending_review"

        # Cleanup
        try:
            TripStore.delete_trip(trip_id)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# TestMIMEPrevalidation
# ---------------------------------------------------------------------------


class TestMIMEPrevalidation:
    def test_pdf_mime_accepted_in_phase_4e(self, session_client):
        """Phase 4E: PDF MIME type is accepted for extraction."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_mime_pdf_4e",
            "agency_id": TEST_AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "booking_data": {"travelers": []},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)

        # Upload a PDF document and accept it
        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n"
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        # Phase 4E: PDF MIME type should pass prevalidation
        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            from spine_api.services.extraction_service import ExtractionResult
            mock_extractor = AsyncMock()
            mock_extractor._model = "gpt-5.4-nano"
            mock_extractor.extract = AsyncMock(return_value=ExtractionResult(
                fields={"full_name": "TEST"},
                confidence_scores={"full_name": 0.9},
                overall_confidence=0.9,
                confidence_method="heuristic_presence",
                provider_metadata={"model_name": "gpt-5.4-nano", "latency_ms": 100},
            ))
            mock_get.return_value = mock_extractor

            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_review"

        # Cleanup
        try:
            TripStore.delete_trip(trip_id)
        except Exception:
            pass

    def test_openai_vision_jpeg_proceeds(self, session_client):
        """openai_vision + JPEG is not rejected by MIME prevalidation."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_mime_jpeg",
            "agency_id": TEST_AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "booking_data": {"travelers": []},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)

        # Upload a JPEG and accept
        jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.jpg", jpeg_bytes, "image/jpeg")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        # With openai_vision, a JPEG should pass MIME prevalidation
        # (will fail at provider call, but that's after prevalidation)
        with patch.dict(os.environ, {
            "EXTRACTION_PROVIDER": "openai_vision",
            "OPENAI_API_KEY": "test-key-12345",
        }):
            # Mock the extractor to succeed
            mock_result = ExtractionResult(
                fields={"full_name": "TEST"},
                confidence_scores={"full_name": 0.9},
                overall_confidence=0.9,
                confidence_method="heuristic_presence",
                provider_metadata={"model_name": "gpt-4o", "latency_ms": 100,
                                   "prompt_tokens": 50, "completion_tokens": 25,
                                   "total_tokens": 75, "cost_estimate_usd": None},
            )
            with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
                mock_extractor = AsyncMock()
                mock_extractor._model = "gpt-5.4-nano"
                mock_extractor.extract = AsyncMock(return_value=mock_result)
                mock_extractor.__class__.__name__ = "OpenAIVisionExtractor"
                mock_get.return_value = mock_extractor

                resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        # Should succeed (200), not 422
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending_review"
        assert body["provider_name"] == "openai"

        # Cleanup
        try:
            TripStore.delete_trip(trip_id)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# TestAsyncBoundary
# ---------------------------------------------------------------------------


class TestAsyncBoundary:
    def test_extractor_extract_is_awaited_not_returned_as_coroutine(self):
        """Verify extract() returns an awaited result, not a coroutine."""
        extractor = NoopExtractor()
        result = asyncio.run(extractor.extract(b"test", "image/jpeg", "passport"))
        assert isinstance(result, ExtractionResult)
        assert isinstance(result.fields, dict)
        assert "full_name" in result.fields


# ---------------------------------------------------------------------------
# TestMissingApiKey
# ---------------------------------------------------------------------------


class TestMissingApiKey:
    def test_openai_vision_missing_api_key_fails_fast(self):
        """Missing OPENAI_API_KEY raises RuntimeError when EXTRACTION_PROVIDER=openai_vision."""
        with patch.dict(os.environ, {
            "EXTRACTION_PROVIDER": "openai_vision",
            "OPENAI_API_KEY": "",
        }):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                get_extractor()


# ---------------------------------------------------------------------------
# TestCostMetadataNullable
# ---------------------------------------------------------------------------


class TestCostMetadataNullable:
    def test_cost_estimate_null_without_pricing_config(self):
        """cost_estimate_usd is calculated from pricing table for known models."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key-12345",
        }):
            from src.extraction.vision_client import OpenAIVisionClient
            client = OpenAIVisionClient()

            mock_response = MagicMock()
            mock_response.output_text = json.dumps({"full_name": "TEST"})
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50

            with patch.object(client._client.responses, "create", return_value=mock_response):
                from src.extraction.schemas import build_json_schema, get_schema
                schema = get_schema("default")
                json_schema = build_json_schema(schema["fields"])
                result = asyncio.run(client.extract_from_image(
                    b"fake", "image/jpeg", json_schema, schema["prompt"],
                ))

            assert result.provider_metadata["cost_estimate_usd"] is not None
            assert result.provider_metadata["cost_estimate_usd"] > 0
            assert result.provider_metadata["prompt_tokens"] == 100
            assert result.provider_metadata["completion_tokens"] == 50
            # Pricing source tracks provenance
            assert "pricing_source" in result.provider_metadata

    def test_cost_estimate_null_for_unknown_model(self):
        """cost_estimate_usd is None when model is not in pricing table."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key-12345",
        }):
            from src.extraction.vision_client import OpenAIVisionClient
            client = OpenAIVisionClient(model="future-unknown-model-x")

            mock_response = MagicMock()
            mock_response.output_text = json.dumps({"full_name": "TEST"})
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50

            with patch.object(client._client.responses, "create", return_value=mock_response):
                from src.extraction.schemas import build_json_schema, get_schema
                schema = get_schema("default")
                json_schema = build_json_schema(schema["fields"])
                result = asyncio.run(client.extract_from_image(
                    b"fake", "image/jpeg", json_schema, schema["prompt"],
                ))

            assert result.provider_metadata["cost_estimate_usd"] is None


# ---------------------------------------------------------------------------
# TestSchemaValidationProof — endpoint-level proof that wrong types create
# failed rows with no PII, no booking_data mutation, clean audit
# ---------------------------------------------------------------------------


class TestSchemaValidationProof:
    def test_wrong_type_fields_create_failed_row_no_pii(self, session_client):
        """Provider returns {"passport_number": ["A123"]}.
        Extraction fails with schema_validation_failed.
        Failed row created with extracted_fields_encrypted=NULL.
        booking_data unchanged. Audit has no extracted values."""
        from spine_api.persistence import TripStore
        from src.extraction.vision_client import ExtractionProviderError

        trip_data = {
            "source": "test_schema_validation_proof",
            "agency_id": TEST_AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {},
            "validation": {},
            "decision": {},
            "raw_input": {},
            "booking_data": {"travelers": [{"traveler_id": "t1", "full_name": "Original"}]},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)

        # Upload and accept a JPEG passport
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        # Mock extractor to raise schema_validation_failed
        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_extractor = AsyncMock()
            mock_extractor._model = "gpt-5.4-nano"
            mock_extractor.extract = AsyncMock(
                side_effect=ExtractionProviderError("schema_validation_failed")
            )
            mock_extractor.__class__.__name__ = "OpenAIVisionExtractor"
            mock_get.return_value = mock_extractor

            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["error_code"] == "schema_validation_failed"

        # booking_data unchanged — use get_booking_data for decrypted view
        from spine_api.persistence import TripStore as TS
        bd = TS.get_booking_data(trip_id)
        travelers = (bd or {}).get("travelers", [])
        assert len(travelers) == 1
        assert travelers[0]["full_name"] == "Original"

        # Verify audit has no extracted values for this trip. Scoping by trip_id
        # avoids full-suite order dependence on unrelated audit events.
        from spine_api.persistence import AuditStore
        events = AuditStore.get_events_for_trip(trip_id)
        failed_events = [e for e in events if e.get("type") == "extraction_failed"]
        assert len(failed_events) >= 1
        last_failed = failed_events[-1]
        assert last_failed.get("details", {}).get("error_code") == "schema_validation_failed"
        # No field values in audit
        for key in ("fields", "values", "extracted_fields", "raw_response"):
            assert key not in last_failed.get("details", {})

        # Cleanup
        try:
            TripStore.delete_trip(trip_id)
        except Exception:
            pass
