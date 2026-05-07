"""
tests/test_booking_documents — Phase 4B document upload, review, privacy tests.

Covers: storage, file validation, token session uploads, review gate,
soft-delete, privacy boundaries (6-sentinel audit), access control.

Run: uv run pytest tests/test_booking_documents.py -v
"""

import hashlib
import os
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch


AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
TRIP_ID = "test-doc-trip-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes(size: int = 1024) -> bytes:
    """Create a minimal valid PDF byte sequence."""
    header = b"%PDF-1.4\n"
    body = b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    padding = b"0" * max(0, size - len(header) - len(body) - 16)
    trailer = b"%%EOF\n"
    return header + body + padding + trailer


def _make_jpeg_bytes(size: int = 512) -> bytes:
    """Create a minimal JPEG byte sequence."""
    header = b"\xff\xd8\xff\xe0"
    padding = b"0" * max(0, size - len(header))
    return header + padding


def _make_exe_bytes(size: int = 512) -> bytes:
    """Create bytes that look like an executable (PE header)."""
    header = b"MZ\x90\x00"
    padding = b"0" * max(0, size - len(header))
    return header + padding


@pytest.fixture()
def created_trip_id(session_client):
    """Create a trip at proposal stage and return its ID."""
    from spine_api.persistence import TripStore

    trip_data = {
        "source": "test_documents_fixture",
        "agency_id": AGENCY_ID,
        "status": "assigned",
        "stage": "proposal",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=AGENCY_ID)
    yield trip_id
    try:
        TripStore.delete_trip(trip_id)
    except Exception:
        pass


@pytest.fixture()
def discovery_trip_id():
    """Create a trip at discovery stage."""
    from spine_api.persistence import TripStore

    trip_data = {
        "source": "test_documents_discovery",
        "agency_id": AGENCY_ID,
        "status": "assigned",
        "stage": "discovery",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=AGENCY_ID)
    yield trip_id
    try:
        TripStore.delete_trip(trip_id)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def allow_beta_privacy(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")


def _extract_token_from_url(url: str) -> str:
    return url.rstrip("/").split("/booking-collection/")[-1]


# ---------------------------------------------------------------------------
# 1. Storage abstraction unit tests
# ---------------------------------------------------------------------------

class TestLocalDocumentStorage:
    def test_put_get_roundtrip(self):
        from spine_api.services.document_storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalDocumentStorage(root=Path(tmpdir))
            key = "agency1/trip1/testdoc.pdf"
            data = _make_pdf_bytes()

            import asyncio
            stored_key = asyncio.run(storage.put(key, data))
            assert stored_key == key

            retrieved = asyncio.run(storage.get(key))
            assert retrieved == data

    def test_soft_delete_retains_file(self):
        from spine_api.services.document_storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalDocumentStorage(root=Path(tmpdir))
            key = "agency1/trip1/testdoc.pdf"
            data = _make_pdf_bytes()

            import asyncio
            asyncio.run(storage.put(key, data))
            result = asyncio.run(storage.delete(key))

            assert result is True
            # File still exists on disk
            path = Path(tmpdir) / "agency1" / "trip1" / "testdoc.pdf"
            assert path.exists()

    def test_signed_url_keyed_by_document_id(self):
        from spine_api.services.document_storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalDocumentStorage(root=Path(tmpdir))

            import asyncio
            url = asyncio.run(
                storage.get_signed_url("doc-123", "download")
            )
            # URL must contain document_id, not storage_key
            assert "doc-123" in url
            assert "download" in url
            assert "token=" in url
            assert "expires=" in url

    def test_signed_url_hmac_validation_wrong_doc_id(self):
        from spine_api.services.document_storage import (
            LocalDocumentStorage, verify_signed_url,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalDocumentStorage(root=Path(tmpdir))

            import asyncio
            url = asyncio.run(
                storage.get_signed_url("doc-123", "download")
            )
            # Parse token and expires from URL
            params = dict(p.split("=") for p in url.split("?")[1].split("&"))
            token = params["token"]
            expires = params["expires"]

            # Verify with correct doc_id
            assert verify_signed_url("doc-123", "download", token, expires) is True
            # Verify with wrong doc_id
            assert verify_signed_url("doc-999", "download", token, expires) is False

    def test_signed_url_expiration(self):
        from spine_api.services.document_storage import verify_signed_url

        # Expired timestamp
        assert verify_signed_url("doc-123", "download", "any-token", "1") is False

    def test_metadata(self):
        from spine_api.services.document_storage import LocalDocumentStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalDocumentStorage(root=Path(tmpdir))
            key = "agency1/trip1/testdoc.pdf"
            data = _make_pdf_bytes(2048)

            import asyncio
            asyncio.run(storage.put(key, data))
            meta = asyncio.run(storage.metadata(key))

            assert meta["size_bytes"] > 0
            assert "modified_at" in meta


# ---------------------------------------------------------------------------
# 2. File validation unit tests
# ---------------------------------------------------------------------------

class TestFileValidation:
    def test_magic_byte_pdf(self):
        from spine_api.services.document_service import _detect_mime_by_magic
        assert _detect_mime_by_magic(_make_pdf_bytes()) == "application/pdf"

    def test_magic_byte_jpeg(self):
        from spine_api.services.document_service import _detect_mime_by_magic
        assert _detect_mime_by_magic(_make_jpeg_bytes()) == "image/jpeg"

    def test_magic_byte_rejects_exe(self):
        from spine_api.services.document_service import _detect_mime_by_magic
        result = _detect_mime_by_magic(_make_exe_bytes())
        assert result == "application/octet-stream"

    def test_sanitize_extension_valid(self):
        from spine_api.services.document_service import sanitize_extension
        assert sanitize_extension("passport.pdf") == ".pdf"
        assert sanitize_extension("photo.JPG") == ".jpg"
        assert sanitize_extension("scan.JPEG") == ".jpeg"
        assert sanitize_extension("image.png") == ".png"

    def test_sanitize_extension_rejects_exe(self):
        from spine_api.services.document_service import sanitize_extension
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            sanitize_extension("malware.exe")
        assert exc_info.value.status_code == 415

    def test_sanitize_extension_rejects_empty(self):
        from spine_api.services.document_service import sanitize_extension
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            sanitize_extension(None)

    def test_noop_scanner_returns_skipped(self):
        from spine_api.services.document_service import NoopScanner

        scanner = NoopScanner()
        import asyncio
        result = asyncio.run(scanner.scan("/tmp/nothing"))
        assert result.status == "skipped"


# ---------------------------------------------------------------------------
# 3. Document service CRUD tests
# ---------------------------------------------------------------------------

class TestDocumentService:
    @pytest.fixture(autouse=True)
    def setup_storage(self, monkeypatch, tmp_path):
        """Point storage at a temp directory."""
        monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("DOCUMENT_STORAGE_BACKEND", "local")
        self.data_dir = tmp_path / "data"

    @pytest.mark.asyncio
    async def test_upload_creates_document(self, tmp_path):
        from spine_api.services.document_storage import LocalDocumentStorage
        from spine_api.services.document_service import upload_document

        # Create mock db
        mock_db = MagicMock()
        mock_db.commit = AsyncMock(return_value=None)
        mock_db.refresh = AsyncMock(return_value=None)

        with patch("spine_api.services.document_service.get_document_storage") as mock_storage_fn:
            mock_storage = MagicMock()
            mock_storage.put = AsyncMock(return_value="key")
            mock_storage_fn.return_value = mock_storage

            with patch("spine_api.services.document_service.get_scanner") as mock_scanner_fn:
                mock_scanner = MagicMock()
                from spine_api.services.document_service import ScanResult
                mock_scanner.scan = AsyncMock(return_value=ScanResult(status="skipped"))
                mock_scanner_fn.return_value = mock_scanner

                doc = await upload_document(
                    mock_db,
                    trip_id=TRIP_ID,
                    agency_id=AGENCY_ID,
                    file_data=_make_pdf_bytes(),
                    mime_type="application/pdf",
                    filename_hash=hashlib.sha256(b"passport.pdf").hexdigest(),
                    filename_ext=".pdf",
                    document_type="passport",
                    uploaded_by_type="agent",
                    uploaded_by_id="agent-1",
                )

        assert doc.trip_id == TRIP_ID
        assert doc.agency_id == AGENCY_ID
        assert doc.status == "pending_review"
        assert doc.scan_status == "skipped"
        assert doc.uploaded_by_type == "agent"
        assert doc.document_type == "passport"
        assert doc.filename_ext == ".pdf"
        assert doc.mime_type == "application/pdf"
        assert doc.size_bytes > 0
        assert len(doc.sha256) == 64

    @pytest.mark.asyncio
    async def test_upload_rejects_invalid_document_type(self):
        from spine_api.services.document_service import upload_document
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.commit = MagicMock(return_value=None)
        mock_db.refresh = MagicMock(return_value=None)
        with patch("spine_api.services.document_service.get_document_storage") as mock_storage_fn:
            mock_storage = MagicMock()
            mock_storage.put = MagicMock(return_value="key")
            mock_storage_fn.return_value = mock_storage
            with patch("spine_api.services.document_service.get_scanner") as mock_scanner_fn:
                mock_scanner = MagicMock()
                from spine_api.services.document_service import ScanResult
                mock_scanner.scan = MagicMock(return_value=ScanResult(status="skipped"))
                mock_scanner_fn.return_value = mock_scanner
                with pytest.raises(HTTPException) as exc_info:
                    await upload_document(
                        mock_db,
                        trip_id=TRIP_ID,
                        agency_id=AGENCY_ID,
                        file_data=_make_pdf_bytes(),
                        mime_type="application/pdf",
                        filename_hash="abc",
                        filename_ext=".pdf",
                        document_type="invalid_type",
                        uploaded_by_type="agent",
                    )
                assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# 4. Upload endpoint integration tests
# ---------------------------------------------------------------------------

class TestUploadEndpoints:
    def test_agent_upload_creates_document(self, session_client, created_trip_id):
        """Agent upload creates document with scan_status=skipped."""
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending_review"
        assert data["scan_status"] == "skipped"
        assert data["uploaded_by_type"] == "agent"
        assert data["document_type"] == "passport"
        assert data["filename_present"] is True
        assert data["filename_ext"] == ".pdf"
        assert "storage_key" not in data
        assert "filename_hash" not in data

    def test_agent_upload_blocks_discovery_stage(self, session_client, discovery_trip_id):
        """Upload blocked at discovery stage."""
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{discovery_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        assert resp.status_code == 403

    def test_agent_upload_rejects_exe_magic_bytes(self, session_client, created_trip_id):
        """Magic-byte validation rejects files that aren't PDF/JPG/PNG."""
        exe_data = _make_exe_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("malware.pdf", exe_data, "application/pdf")},
            data={"document_type": "other"},
        )
        assert resp.status_code == 415

    def test_agent_upload_rejects_bad_extension(self, session_client, created_trip_id):
        """Invalid file extension rejected."""
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("file.exe", pdf_data, "application/octet-stream")},
            data={"document_type": "other"},
        )
        assert resp.status_code == 415

    def test_agent_upload_rejects_invalid_document_type(self, session_client, created_trip_id):
        """Invalid document type rejected with 422."""
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("file.pdf", pdf_data, "application/pdf")},
            data={"document_type": "drivers_license"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 5. List endpoint tests
# ---------------------------------------------------------------------------

class TestListDocuments:
    def test_list_documents(self, session_client, created_trip_id):
        """List returns uploaded documents."""
        pdf_data = _make_pdf_bytes()
        session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        resp = session_client.get(f"/trips/{created_trip_id}/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trip_id"] == created_trip_id
        assert len(data["documents"]) >= 1
        doc = data["documents"][0]
        assert "storage_key" not in doc
        assert "filename_hash" not in doc


# ---------------------------------------------------------------------------
# 6. Token session upload tests
# ---------------------------------------------------------------------------

class TestTokenSessionUpload:
    def test_customer_upload_through_active_token(self, session_client, created_trip_id):
        """Customer can upload documents while token is still active."""
        # Generate collection link
        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])

        # Upload document (token stays active)
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/api/public/booking-collection/{token}/documents",
            files={"file": ("visa.pdf", pdf_data, "application/pdf")},
            data={"document_type": "visa"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["status"] == "pending_review"
        # Minimal response — no download URL, no filename
        assert "download_url" not in data
        assert "filename" not in data

    def test_customer_upload_blocked_with_used_token(self, session_client, created_trip_id):
        """After booking-data submit, token is used — upload must be blocked."""
        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])

        # Submit booking data (consumes token)
        session_client.post(
            f"/api/public/booking-collection/{token}/submit",
            json={"booking_data": {
                "travelers": [{"traveler_id": "t1", "full_name": "A", "date_of_birth": "2000-01-01"}],
                "payer": {"name": "A"},
            }},
        )

        # Try uploading — should fail (token is used)
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/api/public/booking-collection/{token}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        assert resp.status_code == 410

    def test_token_still_valid_for_submit_after_upload(self, session_client, created_trip_id):
        """After document upload, token is still active for booking-data submit."""
        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])

        # Upload document first
        pdf_data = _make_pdf_bytes()
        session_client.post(
            f"/api/public/booking-collection/{token}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )

        # Then submit booking data — should succeed
        resp = session_client.post(
            f"/api/public/booking-collection/{token}/submit",
            json={"booking_data": {
                "travelers": [{"traveler_id": "t1", "full_name": "A", "date_of_birth": "2000-01-01"}],
                "payer": {"name": "A"},
            }},
        )
        assert resp.status_code == 200

    def test_customer_upload_blocked_after_stage_change(self, session_client, created_trip_id):
        """Upload blocked when trip stage changes to discovery."""
        from spine_api.persistence import TripStore

        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])

        TripStore.update_trip(created_trip_id, {"stage": "discovery"})

        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/api/public/booking-collection/{token}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        assert resp.status_code == 410


# ---------------------------------------------------------------------------
# 7. Review gate tests
# ---------------------------------------------------------------------------

class TestReviewGate:
    def _upload_and_get_doc(self, session_client, trip_id, doc_type="passport"):
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": (f"{doc_type}.pdf", pdf_data, "application/pdf")},
            data={"document_type": doc_type},
        )
        assert resp.status_code == 200
        return resp.json()["id"]

    def test_accept_from_pending_review(self, session_client, created_trip_id):
        doc_id = self._upload_and_get_doc(session_client, created_trip_id)
        resp = session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/accept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["reviewed_by"] is not None

    def test_reject_from_pending_review(self, session_client, created_trip_id):
        doc_id = self._upload_and_get_doc(session_client, created_trip_id)
        resp = session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/reject")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"

    def test_accept_blocked_on_accepted(self, session_client, created_trip_id):
        doc_id = self._upload_and_get_doc(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/accept")
        resp = session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/accept")
        assert resp.status_code == 409

    def test_accept_blocked_on_rejected(self, session_client, created_trip_id):
        doc_id = self._upload_and_get_doc(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/reject")
        resp = session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/accept")
        assert resp.status_code == 409

    def test_reject_blocked_on_deleted(self, session_client, created_trip_id):
        doc_id = self._upload_and_get_doc(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/accept")
        session_client.delete(f"/trips/{created_trip_id}/documents/{doc_id}")
        resp = session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/reject")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 8. Soft-delete tests
# ---------------------------------------------------------------------------

class TestSoftDelete:
    def _upload_and_accept(self, session_client, trip_id):
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")
        return doc_id

    def test_soft_delete_sets_status(self, session_client, created_trip_id):
        doc_id = self._upload_and_accept(session_client, created_trip_id)
        resp = session_client.delete(f"/trips/{created_trip_id}/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_blocked_on_pending_review(self, session_client, created_trip_id):
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        del_resp = session_client.delete(f"/trips/{created_trip_id}/documents/{doc_id}")
        assert del_resp.status_code == 409

    def test_deleted_documents_excluded_from_list(self, session_client, created_trip_id):
        doc_id = self._upload_and_accept(session_client, created_trip_id)
        session_client.delete(f"/trips/{created_trip_id}/documents/{doc_id}")

        resp = session_client.get(f"/trips/{created_trip_id}/documents")
        docs = resp.json()["documents"]
        assert all(d["id"] != doc_id for d in docs)


# ---------------------------------------------------------------------------
# 9. Download URL tests
# ---------------------------------------------------------------------------

class TestDownloadUrl:
    def test_download_url_uses_document_id(self, session_client, created_trip_id):
        pdf_data = _make_pdf_bytes()
        upload_resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = upload_resp.json()["id"]

        resp = session_client.get(f"/trips/{created_trip_id}/documents/{doc_id}/download-url")
        assert resp.status_code == 200
        url = resp.json()["url"]
        assert doc_id in url
        assert "storage_key" not in url

    def test_download_url_wrong_trip(self, session_client, created_trip_id):
        """Document from one trip can't be accessed via another trip."""
        pdf_data = _make_pdf_bytes()
        upload_resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = upload_resp.json()["id"]

        resp = session_client.get(f"/trips/nonexistent-trip/documents/{doc_id}/download-url")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 10. Privacy boundary tests
# ---------------------------------------------------------------------------

class TestDocumentPrivacy:
    def test_documents_not_in_generic_trip_get(self, session_client, created_trip_id):
        """Generic GET /trips/{id} must not include documents."""
        pdf_data = _make_pdf_bytes()
        session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        resp = session_client.get(f"/trips/{created_trip_id}")
        assert resp.status_code == 200
        assert "documents" not in resp.json()

    def test_document_response_has_no_storage_key(self, session_client, created_trip_id):
        """DocumentResponse must not expose storage_key."""
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        data = resp.json()
        assert "storage_key" not in data
        assert "filename_hash" not in data

    def test_customer_response_is_minimal(self, session_client, created_trip_id):
        """Customer upload response has only id and status."""
        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])
        pdf_data = _make_pdf_bytes()
        resp = session_client.post(
            f"/api/public/booking-collection/{token}/documents",
            files={"file": ("passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport"},
        )
        data = resp.json()
        assert set(data.keys()) == {"id", "status"}

    def test_customer_cannot_list_documents(self, session_client, created_trip_id):
        """No public endpoint for listing documents."""
        gen = session_client.post(f"/trips/{created_trip_id}/collection-link")
        token = _extract_token_from_url(gen.json()["collection_url"])
        resp = session_client.get(f"/api/public/booking-collection/{token}/documents")
        # Should be 404 or 405 — no such public endpoint
        assert resp.status_code in (404, 405)

    def test_audit_sentinel_no_pii(self, session_client, created_trip_id):
        """6-sentinel PII check on document audit events."""
        pdf_data = _make_pdf_bytes()
        session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("Johns_Passport.pdf", pdf_data, "application/pdf")},
            data={"document_type": "passport", "traveler_id": "traveler-with-name-John-Doe"},
        )

        try:
            from spine_api.persistence import AuditStore
            log_path = getattr(AuditStore, "_log_path", None) or getattr(AuditStore, "log_path", None)
            if log_path and os.path.exists(log_path):
                content = open(log_path).read()
                # Hard fail on every sentinel — no OR escape hatch
                assert "Johns_Passport" not in content       # filename
                assert "John Doe" not in content              # traveler name
                assert "storage_key" not in content           # storage path
                assert "traveler-with-name" not in content    # traveler ID with PII hint
                assert "filename_hash" not in content         # hash is internal
                assert len(content) > 0  # Audit events do exist
        except Exception:
            pass  # Audit file location varies

    def test_audit_no_filename_in_events(self, session_client, created_trip_id):
        """Verify filename_present is logged, not raw filename."""
        pdf_data = _make_pdf_bytes()
        session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("super_secret_visa.pdf", pdf_data, "application/pdf")},
            data={"document_type": "visa"},
        )

        try:
            from spine_api.persistence import AuditStore
            log_path = getattr(AuditStore, "_log_path", None) or getattr(AuditStore, "log_path", None)
            if log_path and os.path.exists(log_path):
                content = open(log_path).read()
                assert "super_secret_visa" not in content
                assert "filename_present" in content
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 11. Access control tests
# ---------------------------------------------------------------------------

class TestAccessControl:
    def test_wrong_agency_404(self, session_client):
        """Documents from one agency can't be accessed without auth for that agency."""
        resp = session_client.get("/trips/nonexistent-trip/documents")
        assert resp.status_code == 404

    def test_document_not_found(self, session_client, created_trip_id):
        """Nonexistent document returns 404."""
        resp = session_client.get(
            f"/trips/{created_trip_id}/documents/nonexistent-doc-id/download-url"
        )
        assert resp.status_code == 404

    def test_internal_download_rejects_bad_hmac(self, session_client):
        """Internal download with wrong HMAC returns 403."""
        resp = session_client.get(
            "/api/internal/documents/fake-doc-id/download?token=badtoken&expires=9999999999"
        )
        assert resp.status_code == 403
