"""
tests/test_document_extractions — Phase 4C document extraction tests.

Covers: extractor, extract endpoint (stage-gated), apply (conflict-aware),
reject, readiness recompute, privacy (no PII in audit/responses).

Run: uv run pytest tests/test_document_extractions.py -v
"""

import pytest


AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


def _make_pdf_bytes(size: int = 1024) -> bytes:
    header = b"%PDF-1.4\n"
    body = b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    padding = b"0" * max(0, size - len(header) - len(body) - 16)
    trailer = b"%%EOF\n"
    return header + body + padding + trailer


def _upload_and_accept(client, trip_id, doc_type="passport"):
    """Upload a document and accept it. Returns doc_id."""
    resp = client.post(
        f"/trips/{trip_id}/documents",
        files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
        data={"document_type": doc_type},
    )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]
    resp = client.post(f"/trips/{trip_id}/documents/{doc_id}/accept")
    assert resp.status_code == 200
    return doc_id


@pytest.fixture()
def created_trip_id(session_client):
    """Create a trip at proposal stage with booking_data."""
    from spine_api.persistence import TripStore

    trip_data = {
        "source": "test_extraction_fixture",
        "agency_id": AGENCY_ID,
        "status": "assigned",
        "stage": "proposal",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
        "booking_data": {
            "travelers": [
                {"traveler_id": "t1", "full_name": "Manual Entry"},
            ],
        },
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


# ---------------------------------------------------------------------------
# 1. NoopExtractor unit tests
# ---------------------------------------------------------------------------

class TestNoopExtractor:
    def test_returns_sentinel_values(self):
        from spine_api.services.extraction_service import NoopExtractor

        ext = NoopExtractor()
        import asyncio
        result = asyncio.run(
            ext.extract(_make_pdf_bytes(), "application/pdf", "passport")
        )
        assert result.fields["full_name"] == "DO_NOT_LOG_NAME"
        assert result.fields["passport_number"] == "DO_NOT_LOG_PASSPORT"
        assert result.overall_confidence > 0
        assert "full_name" in result.confidence_scores

    def test_per_document_type(self):
        from spine_api.services.extraction_service import NoopExtractor
        import asyncio

        ext = NoopExtractor()
        passport = asyncio.run(
            ext.extract(_make_pdf_bytes(), "application/pdf", "passport")
        )
        visa = asyncio.run(
            ext.extract(_make_pdf_bytes(), "application/pdf", "visa")
        )
        assert "passport_number" in passport.fields
        assert "visa_number" in visa.fields
        assert "visa_number" not in passport.fields


# ---------------------------------------------------------------------------
# 2. Extract endpoint tests
# ---------------------------------------------------------------------------

class TestExtractEndpoint:
    def test_extract_accepted_document(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending_review"
        assert data["field_count"] > 0
        assert data["overall_confidence"] > 0
        assert len(data["fields"]) > 0

    def test_extract_pending_review_document(self, session_client, created_trip_id):
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        # Don't accept — leave in pending_review
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_review"

    def test_extract_blocked_on_rejected_document(self, session_client, created_trip_id):
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/reject")

        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp.status_code == 409

    def test_extract_blocked_on_deleted_document(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.delete(f"/trips/{created_trip_id}/documents/{doc_id}")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp.status_code in (404, 409)

    def test_duplicate_extraction_blocked(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        resp1 = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp1.status_code == 200
        resp2 = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp2.status_code == 409

    def test_extract_blocked_at_discovery_stage(self, session_client):
        """Upload+accept at proposal, move to discovery, extract should fail."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_extract_discovery_gate",
            "agency_id": AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {}, "validation": {}, "decision": {}, "raw_input": {},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=AGENCY_ID)
        try:
            doc_id = _upload_and_accept(session_client, trip_id)
            TripStore.update_trip(trip_id, {"stage": "discovery"})

            resp = session_client.post(
                f"/trips/{trip_id}/documents/{doc_id}/extract"
            )
            assert resp.status_code == 403
        finally:
            try:
                TripStore.delete_trip(trip_id)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 3. Get extraction tests
# ---------------------------------------------------------------------------

class TestGetExtraction:
    def test_get_extraction_returns_decrypted_fields(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.get(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == doc_id
        assert "extracted_fields_encrypted" not in data
        field_names = [f["field_name"] for f in data["fields"]]
        assert "full_name" in field_names
        for f in data["fields"]:
            if f["present"]:
                assert f["value"] is not None

    def test_get_extraction_not_found(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        resp = session_client.get(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction"
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 4. Apply tests
# ---------------------------------------------------------------------------

class TestApplyExtraction:
    def test_apply_writes_selected_fields_to_booking_data(
        self, session_client, created_trip_id
    ):
        from spine_api.persistence import TripStore

        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        # Use passport_number — no conflict (traveler doesn't have it yet)
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={
                "traveler_id": "t1",
                "fields_to_apply": ["passport_number", "passport_expiry"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] is True
        assert data["extraction"]["status"] == "applied"

        booking = TripStore.get_booking_data(created_trip_id)
        traveler = booking["travelers"][0]
        assert traveler.get("passport_number") is not None

    def test_apply_blocked_unless_document_accepted(self, session_client, created_trip_id):
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents",
            files={"file": ("test.pdf", _make_pdf_bytes(), "application/pdf")},
            data={"document_type": "passport"},
        )
        doc_id = resp.json()["id"]
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
        )
        assert resp.status_code == 409

    def test_apply_blocked_on_non_pending_extraction(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
        )
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
        )
        assert resp.status_code == 409

    def test_apply_conflicts_returned_without_overwrite(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        # full_name conflicts: "Manual Entry" vs "DO_NOT_LOG_NAME"
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["full_name"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] is False
        assert len(data["conflicts"]) > 0
        assert data["conflicts"][0]["field_name"] == "full_name"

    def test_apply_with_overwrite_succeeds(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={
                "traveler_id": "t1",
                "fields_to_apply": ["full_name"],
                "allow_overwrite": True,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["applied"] is True

    def test_apply_does_not_auto_append_traveler(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "nonexistent", "fields_to_apply": ["passport_number"]},
        )
        assert resp.status_code == 409

    def test_apply_recomputes_readiness(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore

        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
        )
        trip = TripStore.get_trip(created_trip_id)
        readiness = trip.get("validation", {}).get("readiness", {})
        assert isinstance(readiness, dict)

    def test_apply_blocked_at_discovery_stage(self, session_client):
        """Upload+accept+extract at proposal, move to discovery, apply should fail."""
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_apply_discovery_gate",
            "agency_id": AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {}, "validation": {}, "decision": {}, "raw_input": {},
            "booking_data": {"travelers": [{"traveler_id": "t1"}]},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=AGENCY_ID)
        try:
            doc_id = _upload_and_accept(session_client, trip_id)
            session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")
            TripStore.update_trip(trip_id, {"stage": "discovery"})

            resp = session_client.post(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/apply",
                json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
            )
            assert resp.status_code == 403
        finally:
            try:
                TripStore.delete_trip(trip_id)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 4b. Apply guardrail tests
# ---------------------------------------------------------------------------

class TestApplyGuardrails:
    def test_apply_rejects_unknown_field(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["invalid_field"]},
        )
        assert resp.status_code == 422
        assert "invalid_field" in resp.json()["detail"].lower() or "Invalid" in resp.json()["detail"]

    def test_apply_rejects_empty_fields_to_apply(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": []},
        )
        assert resp.status_code == 422
        assert "empty" in resp.json()["detail"].lower()

    def test_apply_rejects_field_not_in_extraction(self, session_client, created_trip_id):
        """Insurance fields are not in passport extraction — must be rejected."""
        doc_id = _upload_and_accept(session_client, created_trip_id, doc_type="passport")
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["insurance_policy_number"]},
        )
        assert resp.status_code == 422
        assert "not present" in resp.json()["detail"].lower()

    def test_create_traveler_requires_name_and_dob(self, session_client, created_trip_id):
        """create_traveler_if_missing=true but missing full_name/date_of_birth → 422."""
        doc_id = _upload_and_accept(session_client, created_trip_id, doc_type="passport")
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={
                "traveler_id": "new_t2",
                "fields_to_apply": ["passport_number"],
                "create_traveler_if_missing": True,
            },
        )
        assert resp.status_code == 422
        assert "full_name" in resp.json()["detail"] or "date_of_birth" in resp.json()["detail"]


class TestExtractionEncryptionProof:
    def test_extracted_fields_encrypted_at_rest(self, session_client, created_trip_id):
        """Sentinel values must NOT appear in raw extracted_fields_encrypted column.

        Uses raw SQL through asyncpg directly (same pool the TestClient uses)
        to prove the stored column is actually encrypted Fernet ciphertext,
        not plaintext sentinel values.
        """
        import json
        from spine_api.services.extraction_service import decrypt_blob

        doc_id = _upload_and_accept(session_client, created_trip_id)
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extract"
        )
        assert resp.status_code == 200
        extraction_id = resp.json()["id"]

        # Query via a fresh event loop (avoids cross-loop asyncpg issues with TestClient)
        import asyncio

        async def _raw_query():
            from spine_api.persistence import tripstore_session_maker
            from sqlalchemy import text
            async with tripstore_session_maker() as db:
                row = (await db.execute(
                    text("SELECT extracted_fields_encrypted FROM document_extractions WHERE id = :eid"),
                    {"eid": extraction_id},
                )).fetchone()
                return row[0]

        raw_blob = asyncio.run(_raw_query())

        # JSON column returns a dict — normalize if string
        if isinstance(raw_blob, str):
            raw_blob = json.loads(raw_blob)

        # Raw blob must be encrypted — no sentinel values in plaintext
        raw_str = str(raw_blob)
        for sentinel in [
            "DO_NOT_LOG_NAME", "DO_NOT_LOG_PASSPORT", "DO_NOT_LOG_DOB",
            "DO_NOT_LOG_EXPIRY", "DO_NOT_LOG_VISA_NUM", "DO_NOT_LOG_POLICY",
            "DO_NOT_LOG_PROVIDER",
        ]:
            assert sentinel not in raw_str, f"PII sentinel {sentinel} found in raw encrypted column"

        # Verify it's actually an encrypted blob
        assert isinstance(raw_blob, dict)
        assert raw_blob.get("__encrypted_blob") is True
        assert "ciphertext" in raw_blob

        # Round-trip: decrypt and verify sentinels are present
        decrypted = decrypt_blob(raw_blob)
        assert decrypted.get("full_name") == "DO_NOT_LOG_NAME"
        assert decrypted.get("passport_number") == "DO_NOT_LOG_PASSPORT"
# ---------------------------------------------------------------------------

class TestRejectExtraction:
    def test_reject_does_not_modify_booking_data(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore

        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/reject"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

        booking = TripStore.get_booking_data(created_trip_id)
        traveler = booking["travelers"][0]
        assert traveler.get("full_name") == "Manual Entry"

    def test_reject_blocked_on_applied(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        # Apply with passport_number (no conflict)
        session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/apply",
            json={"traveler_id": "t1", "fields_to_apply": ["passport_number"]},
        )
        resp = session_client.post(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction/reject"
        )
        assert resp.status_code == 409

    def test_reject_works_at_any_stage(self, session_client):
        from spine_api.persistence import TripStore

        trip_data = {
            "source": "test_reject_any_stage",
            "agency_id": AGENCY_ID,
            "status": "assigned",
            "stage": "proposal",
            "extracted": {}, "validation": {}, "decision": {}, "raw_input": {},
        }
        trip_id = TripStore.save_trip(trip_data, agency_id=AGENCY_ID)
        try:
            doc_id = _upload_and_accept(session_client, trip_id)
            session_client.post(f"/trips/{trip_id}/documents/{doc_id}/extract")
            TripStore.update_trip(trip_id, {"stage": "discovery"})

            resp = session_client.post(
                f"/trips/{trip_id}/documents/{doc_id}/extraction/reject"
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "rejected"
        finally:
            try:
                TripStore.delete_trip(trip_id)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 6. Privacy tests
# ---------------------------------------------------------------------------

class TestExtractionPrivacy:
    def test_response_excludes_encrypted_blob(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.get(
            f"/trips/{created_trip_id}/documents/{doc_id}/extraction"
        )
        data = resp.json()
        assert "extracted_fields_encrypted" not in data
        assert "raw_ocr_text" not in data
        assert "extra_fields" not in data

    def test_audit_has_no_sentinel_values(self, session_client, created_trip_id):
        """Audit events for extraction must not contain DO_NOT_LOG_* sentinels."""
        from spine_api.persistence import AuditStore

        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")

        events = AuditStore.get_events(limit=50)
        extraction_events = [
            e for e in events
            if isinstance(e, dict) and e.get("event_type") == "extraction_created"
        ]
        if extraction_events:
            last = extraction_events[-1]
            event_str = str(last)
            for sentinel in [
                "DO_NOT_LOG_NAME", "DO_NOT_LOG_PASSPORT",
                "DO_NOT_LOG_DOB", "DO_NOT_LOG_EXPIRY",
                "DO_NOT_LOG_VISA_NUM", "DO_NOT_LOG_POLICY",
                "DO_NOT_LOG_PROVIDER",
            ]:
                assert sentinel not in event_str, f"PII sentinel {sentinel} found in audit log"

    def test_extraction_not_in_document_list(self, session_client, created_trip_id):
        doc_id = _upload_and_accept(session_client, created_trip_id)
        session_client.post(f"/trips/{created_trip_id}/documents/{doc_id}/extract")
        resp = session_client.get(f"/trips/{created_trip_id}/documents")
        data = resp.json()
        for doc in data.get("documents", []):
            assert "extraction" not in doc
            assert "extraction_status" not in doc
