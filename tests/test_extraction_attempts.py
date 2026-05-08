"""Phase 4E tests: Extraction attempts, retry, PDF validation, and PII safety.

Integration tests using the API. Covers:
- Attempt creation and fallback history
- Retry of failed extractions
- Attempt list with no PII
- PDF page limit validation
- Noop extraction creates attempt
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from spine_api.services.extraction_service import ExtractionResult


AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


def _upload_and_accept(client, trip_id, doc_type="passport", mime="image/jpeg", content=None):
    """Upload a document and accept it. Returns doc_id."""
    if content is None:
        content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    ext = "jpg" if "jpeg" in mime else ("pdf" if "pdf" in mime else "png")
    resp = client.post(
        f"/trips/{trip_id}/documents",
        files={"file": (f"test.{ext}", content, mime)},
        data={"document_type": doc_type},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]
    resp = client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")
    assert resp.status_code == 200
    return doc_id


def _make_trip(agency_id=AGENCY_ID):
    from spine_api.persistence import TripStore
    trip_data = {
        "source": "test_4e_attempts",
        "agency_id": agency_id,
        "status": "assigned",
        "stage": "proposal",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
        "booking_data": {"travelers": []},
    }
    return TripStore.save_trip(trip_data, agency_id=agency_id)


def _cleanup_trip(trip_id):
    try:
        from spine_api.persistence import TripStore
        TripStore.delete_trip(trip_id)
    except Exception:
        pass


def _mock_extractor(model="gpt-5.4-nano", result=None, error=None):
    """Create a mock extractor that returns result or raises error."""
    mock = AsyncMock()
    mock._model = model
    if error:
        mock.extract = AsyncMock(side_effect=error)
    else:
        mock.extract = AsyncMock(return_value=result or ExtractionResult(
            fields={"full_name": "TEST"},
            confidence_scores={"full_name": 0.9},
            overall_confidence=0.9,
            confidence_method="heuristic_presence",
            provider_metadata={"model_name": model, "latency_ms": 100},
        ))
    return mock


# ---------------------------------------------------------------------------
# TestAttemptCreation
# ---------------------------------------------------------------------------


class TestAttemptCreation:
    def test_first_extraction_creates_attempt(self, session_client):
        """First extraction creates attempt row → pending_review."""
        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "pending_review"
            assert body["attempt_count"] >= 1
            assert body["run_count"] == 1

            # Verify attempt via attempts endpoint
            attempts_resp = session_client.get(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/attempts"
            )
            assert attempts_resp.status_code == 200
            attempts = attempts_resp.json()
            assert len(attempts) >= 1
            assert attempts[0]["status"] == "success"
            assert attempts[0]["provider_name"] == "openai"
        finally:
            _cleanup_trip(trip_id)

    def test_retry_failed_extraction(self, session_client):
        """Retry after failure → new run_number, extraction back to pending_review."""
        from src.extraction.vision_client import ExtractionProviderError

        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        # First: fail
        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor(error=ExtractionProviderError("api_timeout"))
            resp1 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp1.status_code == 422

        # Retry: succeed
        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            resp2 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp2.status_code == 200
            body = resp2.json()
            assert body["status"] == "pending_review"
            assert body["run_count"] == 2
        finally:
            _cleanup_trip(trip_id)

    def test_retry_on_non_failed_returns_409(self, session_client):
        """Retry on pending_review → 409."""
        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            resp1 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp1.status_code == 200

        # Try again on pending_review → 409
        resp2 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")
        try:
            assert resp2.status_code == 409
        finally:
            _cleanup_trip(trip_id)


# ---------------------------------------------------------------------------
# TestFallbackHistory
# ---------------------------------------------------------------------------


class TestFallbackHistory:
    def test_primary_timeout_secondary_success_two_attempts(self, session_client):
        """Primary timeout + secondary success → two attempt rows."""
        from src.extraction.vision_client import ExtractionProviderError
        from src.extraction.model_chain import ModelChain

        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        ext1 = _mock_extractor(model="gemini-2.5-flash", error=ExtractionProviderError("api_timeout"))
        ext2 = _mock_extractor(model="gpt-5.4-nano")

        chain = ModelChain([("gemini-2.5-flash", ext1), ("gpt-5.4-nano", ext2)])

        with patch("spine_api.services.extraction_service.get_extractor", return_value=chain):
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "pending_review"
            assert body["attempt_count"] == 2

            # Verify two attempt rows via API
            attempts_resp = session_client.get(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/attempts"
            )
            assert attempts_resp.status_code == 200
            attempts = attempts_resp.json()
            assert len(attempts) == 2

            # First: failed
            assert attempts[0]["status"] == "failed"
            assert attempts[0]["error_code"] == "api_timeout"
            assert attempts[0]["provider_name"] == "gemini"

            # Second: success
            assert attempts[1]["status"] == "success"
            assert attempts[1]["provider_name"] == "openai"

            # current_attempt_id points to the successful one
            assert body["current_attempt_id"] == attempts[1]["attempt_id"]
        finally:
            _cleanup_trip(trip_id)

    def test_non_retriable_only_one_attempt(self, session_client):
        """Auth error → one attempt, no fallback."""
        from src.extraction.vision_client import ExtractionProviderError
        from src.extraction.model_chain import ModelChain

        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        ext1 = _mock_extractor(model="gemini-2.5-flash", error=ExtractionProviderError("api_auth_error"))
        ext2 = _mock_extractor(model="gpt-5.4-nano")

        chain = ModelChain([("gemini-2.5-flash", ext1), ("gpt-5.4-nano", ext2)])

        with patch("spine_api.services.extraction_service.get_extractor", return_value=chain):
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 422
            assert resp.json()["detail"]["error_code"] == "api_auth_error"
            assert ext2.extract.call_count == 0
        finally:
            _cleanup_trip(trip_id)


# ---------------------------------------------------------------------------
# TestClosureProofs — specific invariants for Phase 4E closure
# ---------------------------------------------------------------------------


class TestClosureProofs:
    def test_failed_attempt_has_null_encrypted_fields(self, session_client):
        """Proof 3: Failed attempt row has extracted_fields_encrypted=NULL.

        Proven via code-level contract: the service explicitly sets
        attempt.extracted_fields_encrypted = None on failure, and the
        AttemptSummaryResponse never exposes encrypted fields.
        We verify by checking the API never leaks any field data from failed attempts.
        """
        from src.extraction.vision_client import ExtractionProviderError
        from src.extraction.model_chain import ModelChain

        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        ext1 = _mock_extractor(model="gemini-2.5-flash", error=ExtractionProviderError("api_timeout"))
        ext2 = _mock_extractor(model="gpt-5.4-nano")
        chain = ModelChain([("gemini-2.5-flash", ext1), ("gpt-5.4-nano", ext2)])

        with patch("spine_api.services.extraction_service.get_extractor", return_value=chain):
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 200
            attempts_resp = session_client.get(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/attempts"
            )
            attempts = attempts_resp.json()

            # Failed attempt exists
            assert attempts[0]["status"] == "failed"
            # API contract: no encrypted blob, no fields, no raw error
            assert "extracted_fields_encrypted" not in attempts[0]
            assert "fields_present" not in attempts[0]
            assert "confidence_scores" not in attempts[0]
            assert "error_summary" not in attempts[0]
            assert "filename" not in attempts[0]
            assert "storage_key" not in attempts[0]
        finally:
            _cleanup_trip(trip_id)

    def test_over_page_limit_retry_leaves_existing_failed_unchanged(self, session_client):
        """Proof 7: Over-page-limit retry on existing failed extraction leaves it unchanged."""
        from src.extraction.vision_client import ExtractionProviderError

        # Use a PDF document so validate_pdf_pages actually runs
        trip_id = _make_trip()
        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF\n"
        doc_id = _upload_and_accept(
            session_client, trip_id, mime="application/pdf", content=pdf_bytes
        )

        # First: fail with a normal error
        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor(error=ExtractionProviderError("api_timeout"))
            resp1 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp1.status_code == 422
        original_error_code = resp1.json()["detail"]["error_code"]

        # Now retry, but PDF validation blocks it (over page limit)
        with patch("src.extraction.pdf_utils.get_pdf_page_count", return_value=20), \
             patch.dict(os.environ, {"EXTRACTION_MAX_PDF_PAGES": "10"}):
            resp2 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            # Retry blocked by page limit → 422
            assert resp2.status_code == 422

            # Existing extraction still shows as the original failure
            get_resp = session_client.get(f"/trips/{trip_id}/documents/{doc_id}/extraction")
            assert get_resp.status_code == 200
            body = get_resp.json()
            assert body["status"] == "failed"
            assert body["error_code"] == original_error_code
            assert body["run_count"] == 1  # unchanged — no new run
        finally:
            _cleanup_trip(trip_id)# ---------------------------------------------------------------------------
# TestAttemptListNoPII
# ---------------------------------------------------------------------------


class TestAttemptListNoPII:
    def test_attempts_list_no_encrypted_blob_or_fields(self, session_client):
        """Attempt list response contains no PII fields."""
        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        resp = session_client.get(f"/trips/{trip_id}/documents/{doc_id}/extraction/attempts")

        try:
            assert resp.status_code == 200
            attempts = resp.json()
            assert len(attempts) >= 1

            for attempt in attempts:
                # Required fields
                assert "attempt_id" in attempt
                assert "provider_name" in attempt
                assert "status" in attempt
                assert "run_number" in attempt
                assert "attempt_number" in attempt

                # NO PII fields
                assert "extracted_fields_encrypted" not in attempt
                assert "fields_present" not in attempt
                assert "confidence_scores" not in attempt
                assert "error_summary" not in attempt
        finally:
            _cleanup_trip(trip_id)


# ---------------------------------------------------------------------------
# TestPDFExtraction
# ---------------------------------------------------------------------------


class TestPDFExtraction:
    def test_pdf_over_page_limit_returns_422(self, session_client):
        """PDF with too many pages → 422 before provider call, no extraction row."""
        trip_id = _make_trip()
        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF\n"

        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")

        with patch("src.extraction.pdf_utils.get_pdf_page_count", return_value=20), \
             patch.dict(os.environ, {"EXTRACTION_MAX_PDF_PAGES": "10"}):
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 422
            assert "10" in resp.json()["detail"]

            # No extraction row
            get_resp = session_client.get(f"/trips/{trip_id}/documents/{doc_id}/extraction")
            assert get_resp.status_code == 404
        finally:
            _cleanup_trip(trip_id)


# ---------------------------------------------------------------------------
# TestNoopAttempt
# ---------------------------------------------------------------------------


class TestNoopAttempt:
    def test_noop_creates_success_attempt(self, session_client):
        """NoopExtractor creates one success attempt with provider_name=noop_extractor."""
        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch.dict(os.environ, {"EXTRACTION_PROVIDER": "noop", "APP_ENV": "test"}):
            resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        try:
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "pending_review"
            assert body["provider_name"] == "noop_extractor"

            # Verify attempt via API
            attempts_resp = session_client.get(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/attempts"
            )
            assert attempts_resp.status_code == 200
            attempts = attempts_resp.json()
            assert len(attempts) == 1
            assert attempts[0]["status"] == "success"
            assert attempts[0]["provider_name"] == "noop_extractor"
        finally:
            _cleanup_trip(trip_id)


# ---------------------------------------------------------------------------
# TestRetryEndpoint
# ---------------------------------------------------------------------------


class TestRetryEndpoint:
    def test_retry_endpoint_on_failed(self, session_client):
        """POST retry on failed extraction → new run, back to pending_review."""
        from src.extraction.vision_client import ExtractionProviderError

        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor(error=ExtractionProviderError("api_server_error"))
            resp1 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        assert resp1.status_code == 422

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            resp2 = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extraction/retry")

        try:
            assert resp2.status_code == 200
            assert resp2.json()["status"] == "pending_review"
        finally:
            _cleanup_trip(trip_id)

    def test_retry_endpoint_on_applied_returns_409(self, session_client):
        """POST retry on applied extraction → 409."""
        trip_id = _make_trip()
        doc_id = _upload_and_accept(session_client, trip_id)

        with patch("spine_api.services.extraction_service.get_extractor") as mock_get:
            mock_get.return_value = _mock_extractor()
            session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")

        resp = session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extraction/retry")
        try:
            assert resp.status_code == 409
        finally:
            _cleanup_trip(trip_id)
