"""
tests/test_booking_data — Phase 3B booking data tests.

Covers: encryption, endpoints, stage gate, optimistic lock,
audit, validation, readiness, mutation guards.

Run: uv run pytest tests/test_booking_data.py -v
"""

import os
import pytest
from unittest.mock import MagicMock

from spine_api.persistence import TEST_AGENCY_ID
from intake.readiness import compute_readiness, _check_booking_ready


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_BOOKING_DATA = {
    "travelers": [
        {
            "traveler_id": "adult_1",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "passport_number": "X1234567",
        },
        {
            "traveler_id": "adult_2",
            "full_name": "Jane Doe",
            "date_of_birth": "1992-03-20",
        },
    ],
    "payer": {"name": "John Doe", "email": "john@example.com", "phone": "+91-9999999999"},
    "special_requirements": "Vegetarian meals",
    "booking_notes": "Window seat preferred",
}

VALID_PAYMENT_TRACKING = {
    **VALID_BOOKING_DATA,
    "payment_tracking": {
        "agreed_amount": 120000.0,
        "currency": "INR",
        "amount_paid": 50000.0,
        "payment_status": "partially_paid",
        "payment_method": "bank_transfer",
        "payment_reference": "UTR-123456",
        "payment_proof_url": "https://example.test/proof.pdf",
        "refund_status": "not_applicable",
        "notes": "Deposit received from payer.",
    },
}

BOOKING_DATA_NO_TRAVELERS = {
    "travelers": [],
    "payer": {"name": "Payer"},
}

BOOKING_DATA_NO_FULL_NAME = {
    "travelers": [{"traveler_id": "a1", "full_name": "", "date_of_birth": "2000-01-01"}],
    "payer": {"name": "Payer"},
}

BOOKING_DATA_NO_DOB = {
    "travelers": [{"traveler_id": "a1", "full_name": "Alice", "date_of_birth": ""}],
    "payer": {"name": "Payer"},
}

BOOKING_DATA_NO_PAYER = {
    "travelers": [{"traveler_id": "a1", "full_name": "Alice", "date_of_birth": "2000-01-01"}],
}


@pytest.fixture()
def created_trip_id(session_client):
    """Create a trip directly via TripStore and return its ID."""
    from spine_api.persistence import TripStore

    trip_data = {
        "source": "test_booking_fixture",
        "agency_id": TEST_AGENCY_ID,
        "status": "assigned",
        "stage": "proposal",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
    }
    trip_id = TripStore.save_trip(trip_data, agency_id=TEST_AGENCY_ID)
    yield trip_id
    try:
        TripStore.delete_trip(trip_id)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def allow_beta_privacy(monkeypatch):
    """Allow beta privacy mode so booking_data with PII can be stored in tests."""
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")


# ---------------------------------------------------------------------------
# 1. Encryption: booking_data is blob-encrypted
# ---------------------------------------------------------------------------

class TestBookingDataEncryption:
    def test_booking_data_round_trips_through_encrypt_decrypt(self):
        from spine_api.persistence import SQLTripStore
        encrypted = SQLTripStore._encrypt_field_for_storage("booking_data", VALID_BOOKING_DATA)
        assert isinstance(encrypted, dict)
        assert encrypted.get("__encrypted_blob") is True
        # Sentinel PII must not appear in raw ciphertext
        ciphertext = encrypted.get("ciphertext", "")
        assert "John Doe" not in ciphertext
        assert "1990-01-15" not in ciphertext
        assert "X1234567" not in ciphertext
        assert "john@example.com" not in ciphertext
        assert "+91-9999999999" not in ciphertext
        # Round-trip
        decrypted = SQLTripStore._decrypt_field_from_storage("booking_data", encrypted)
        assert decrypted["travelers"][0]["full_name"] == "John Doe"
        assert decrypted["travelers"][0]["passport_number"] == "X1234567"
        assert decrypted["payer"]["email"] == "john@example.com"

    def test_booking_data_none_encrypts_to_none(self):
        from spine_api.persistence import SQLTripStore
        assert SQLTripStore._encrypt_field_for_storage("booking_data", None) is None
        assert SQLTripStore._decrypt_field_from_storage("booking_data", None) is None

    def test_to_dict_excludes_booking_data(self):
        from spine_api.persistence import SQLTripStore
        trip_obj = MagicMock()
        trip_obj.booking_data = {"travelers": [{"full_name": "Secret"}]}
        result = SQLTripStore._to_dict(trip_obj)
        assert "booking_data" not in result


# ---------------------------------------------------------------------------
# 2. Readiness: booking_ready validation
# ---------------------------------------------------------------------------

class TestBookingReadinessValidation:
    def test_valid_booking_data_is_ready(self):
        result = _check_booking_ready({}, VALID_BOOKING_DATA)
        assert result.ready is True
        assert "booking_data" in result.met
        assert result.unmet == []

    def test_none_booking_data_not_ready(self):
        result = _check_booking_ready({}, None)
        assert result.ready is False
        assert "booking_data" in result.unmet

    def test_empty_booking_data_not_ready(self):
        result = _check_booking_ready({}, {})
        assert result.ready is False

    def test_no_travelers_not_ready(self):
        result = _check_booking_ready({}, BOOKING_DATA_NO_TRAVELERS)
        assert result.ready is False
        assert "travelers" in result.unmet

    def test_blank_full_name_not_ready(self):
        result = _check_booking_ready({}, BOOKING_DATA_NO_FULL_NAME)
        assert result.ready is False
        assert any("full_name" in u for u in result.unmet)

    def test_blank_dob_not_ready(self):
        result = _check_booking_ready({}, BOOKING_DATA_NO_DOB)
        assert result.ready is False
        assert any("date_of_birth" in u for u in result.unmet)

    def test_no_payer_not_ready(self):
        result = _check_booking_ready({}, BOOKING_DATA_NO_PAYER)
        assert result.ready is False
        assert "payer_name" in result.unmet


# ---------------------------------------------------------------------------
# 3. Endpoint tests
# ---------------------------------------------------------------------------

class TestBookingDataEndpoints:
    def test_get_missing_trip_returns_404(self, session_client):
        resp = session_client.get("/trips/nonexistent-trip/booking-data")
        assert resp.status_code == 404

    def test_get_existing_trip_returns_envelope(self, session_client, created_trip_id):
        resp = session_client.get(f"/trips/{created_trip_id}/booking-data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trip_id"] == created_trip_id
        assert data["booking_data"] is None
        assert "stage" in data
        assert "readiness" in data
        assert "updated_at" in data

    def test_patch_creates_booking_data(self, session_client, created_trip_id):
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["booking_data"] is not None
        assert data["booking_data"]["travelers"][0]["full_name"] == "John Doe"

    def test_patch_updates_existing_booking_data(self, session_client, created_trip_id):
        # Create
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        # Update
        updated = {**VALID_BOOKING_DATA, "special_requirements": "Vegan meals"}
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": updated},
        )
        assert resp.status_code == 200
        assert resp.json()["booking_data"]["special_requirements"] == "Vegan meals"

    def test_patch_accepts_payment_tracking_and_computes_balance(self, session_client, created_trip_id):
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_PAYMENT_TRACKING},
        )
        assert resp.status_code == 200
        tracking = resp.json()["booking_data"]["payment_tracking"]
        assert tracking["tracking_only"] is True
        assert tracking["payment_status"] == "partially_paid"
        assert tracking["refund_status"] == "not_applicable"
        assert tracking["balance_due"] == 70000.0

    def test_patch_recomputes_client_supplied_balance(self, session_client, created_trip_id):
        payload = {
            **VALID_PAYMENT_TRACKING,
            "payment_tracking": {
                **VALID_PAYMENT_TRACKING["payment_tracking"],
                "balance_due": 1.0,
            },
        }
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": payload},
        )
        assert resp.status_code == 200
        assert resp.json()["booking_data"]["payment_tracking"]["balance_due"] == 70000.0

    def test_patch_rejects_negative_payment_tracking_amounts(self, session_client, created_trip_id):
        payload = {
            **VALID_PAYMENT_TRACKING,
            "payment_tracking": {
                **VALID_PAYMENT_TRACKING["payment_tracking"],
                "amount_paid": -1.0,
            },
        }
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": payload},
        )
        assert resp.status_code == 422

    def test_patch_discovery_stage_returns_403(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore
        TripStore.update_trip(created_trip_id, {"stage": "discovery"})
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        assert resp.status_code == 403

    def test_patch_optimistic_lock_conflict(self, session_client, created_trip_id):
        # Create with initial data
        r1 = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        old_updated_at = r1.json()["updated_at"]
        # Update again (changes updated_at)
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        # Try with stale updated_at
        resp = session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={
                "booking_data": VALID_BOOKING_DATA,
                "expected_updated_at": old_updated_at,
            },
        )
        assert resp.status_code == 409

    def test_generic_patch_rejects_booking_data(self, session_client, created_trip_id):
        resp = session_client.patch(
            f"/trips/{created_trip_id}",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        assert resp.status_code == 400
        assert "booking-data" in resp.json()["detail"].lower()

    def test_patch_does_not_mutate_stage(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore
        TripStore.update_trip(created_trip_id, {"stage": "proposal"})
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        trip = TripStore.get_trip(created_trip_id)
        assert trip["stage"] == "proposal"

    def test_patch_does_not_mutate_packet(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore
        original_extracted = TripStore.get_trip(created_trip_id).get("extracted")
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        after = TripStore.get_trip(created_trip_id)
        assert after["extracted"] == original_extracted

    def test_generic_get_excludes_booking_data(self, session_client, created_trip_id):
        from spine_api.persistence import TripStore
        # Save booking data via dedicated endpoint
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        # Generic GET must not include booking_data
        resp = session_client.get(f"/trips/{created_trip_id}")
        assert resp.status_code == 200
        assert "booking_data" not in resp.json()


# ---------------------------------------------------------------------------
# 4. Audit
# ---------------------------------------------------------------------------

class TestBookingDataAudit:
    def test_audit_event_written_without_raw_pii(self, session_client, created_trip_id):
        from spine_api.persistence import AuditStore
        events_before = len(AuditStore.get_events_for_trip(created_trip_id))
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_BOOKING_DATA},
        )
        events = AuditStore.get_events_for_trip(created_trip_id)
        assert len(events) > events_before
        latest = events[-1]
        assert latest["type"] == "booking_data_updated"
        details = latest["details"]
        assert details["traveler_count"] == 2
        assert details["has_payer"] is True
        assert details["has_passport_data"] is True
        # No raw PII
        details_str = str(details)
        assert "John Doe" not in details_str
        assert "1990-01-15" not in details_str
        assert "X1234567" not in details_str
        assert "john@example.com" not in details_str
        assert "+91-9999999999" not in details_str

    def test_payment_tracking_audit_uses_metadata_only(self, session_client, created_trip_id):
        from spine_api.persistence import AuditStore
        session_client.patch(
            f"/trips/{created_trip_id}/booking-data",
            json={"booking_data": VALID_PAYMENT_TRACKING},
        )
        latest = AuditStore.get_events_for_trip(created_trip_id)[-1]
        details = latest["details"]
        assert "payment_tracking" in details["fields_changed"]
        assert details["has_payment_tracking"] is True
        assert details["payment_status"] == "partially_paid"
        assert details["has_payment_reference"] is True
        assert details["has_payment_proof_url"] is True
        details_str = str(details)
        assert "UTR-123456" not in details_str
        assert "https://example.test/proof.pdf" not in details_str


# ---------------------------------------------------------------------------
# 5. Validation (Pydantic)
# ---------------------------------------------------------------------------

class TestBookingDataValidation:
    def test_empty_travelers_rejected(self):
        from pydantic import ValidationError
        from spine_api.server import BookingDataModel
        with pytest.raises(ValidationError):
            BookingDataModel(travelers=[], payer=None)

    def test_valid_booking_data_passes(self):
        from spine_api.server import BookingDataModel
        bd = BookingDataModel(**VALID_BOOKING_DATA)
        assert len(bd.travelers) == 2
        assert bd.payer.name == "John Doe"

    def test_booking_data_with_only_required_fields(self):
        from spine_api.server import BookingDataModel
        bd = BookingDataModel(
            travelers=[
                {"traveler_id": "a1", "full_name": "Alice", "date_of_birth": "2000-01-01"},
            ],
        )
        assert bd.travelers[0].full_name == "Alice"
        assert bd.payer is None


# ---------------------------------------------------------------------------
# 6. Atomic booking update (update_trip_if_version)
# ---------------------------------------------------------------------------

class TestAtomicBookingUpdate:
    def test_update_trip_if_version_success_file_backend(self, tmp_path, monkeypatch):
        """update_trip_if_version succeeds when version matches."""
        from spine_api.persistence import FileTripStore, TRIPS_DIR
        from pathlib import Path
        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        trips_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)

        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        trip_id = FileTripStore.save_trip({"id": "t1", "raw_note": "hello", "agency_id": "agency_a", "updated_at": now}, agency_id="agency_a")
        trip = FileTripStore.get_trip(trip_id)
        original_updated_at = trip["updated_at"]

        result = FileTripStore.update_trip_if_version(
            trip_id,
            {"status": "completed"},
            expected_updated_at=original_updated_at,
        )
        assert result is not None
        assert result["status"] == "completed"

    def test_update_trip_if_version_fails_on_mismatch_file_backend(self, tmp_path, monkeypatch):
        """update_trip_if_version returns None when version does not match (no 409 to client)."""
        from spine_api.persistence import FileTripStore, TRIPS_DIR
        from pathlib import Path
        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        trips_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)

        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        trip_id = FileTripStore.save_trip({"id": "t2", "raw_note": "hello", "agency_id": "agency_a", "updated_at": now}, agency_id="agency_a")

        result = FileTripStore.update_trip_if_version(
            trip_id,
            {"status": "completed"},
            expected_updated_at="2099-01-01T00:00:00",
        )
        assert result is None

    def test_update_trip_if_version_preserves_old_data_on_failure(self, tmp_path, monkeypatch):
        """When update_trip_if_version returns None, the trip data is unchanged."""
        from spine_api.persistence import FileTripStore, TRIPS_DIR
        from pathlib import Path
        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        trips_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)

        import datetime as _dt
        now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        trip_id = FileTripStore.save_trip({"id": "t3", "raw_note": "original", "agency_id": "agency_a", "updated_at": now}, agency_id="agency_a")
        trip_before = FileTripStore.get_trip(trip_id)

        FileTripStore.update_trip_if_version(
            trip_id,
            {"raw_note": "overwritten"},
            expected_updated_at="2099-01-01T00:00:00",
        )
        trip_after = FileTripStore.get_trip(trip_id)
        assert trip_after["raw_note"] == "original"
        assert trip_after["updated_at"] == trip_before["updated_at"]


# ---------------------------------------------------------------------------
# 7. Tenant-scoped trip lookups (get_trip_for_agency)
# ---------------------------------------------------------------------------

class TestTenantScopedTripLookup:
    def test_get_trip_for_agency_returns_trip_for_correct_agency(self, tmp_path, monkeypatch):
        from spine_api.persistence import FileTripStore, TRIPS_DIR
        from pathlib import Path
        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        trips_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)

        FileTripStore.save_trip({"id": "t1", "agency_id": "agency_a"}, agency_id="agency_a")
        FileTripStore.save_trip({"id": "t2", "agency_id": "agency_b"}, agency_id="agency_b")

        trip_a = FileTripStore.get_trip_for_agency("t1", "agency_a")
        assert trip_a is not None
        assert trip_a["id"] == "t1"

        trip_wrong = FileTripStore.get_trip_for_agency("t1", "agency_b")
        assert trip_wrong is None

    def test_get_trip_for_agency_returns_none_for_missing_trip(self, tmp_path, monkeypatch):
        from spine_api.persistence import FileTripStore, TRIPS_DIR
        from pathlib import Path
        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        trips_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)

        result = FileTripStore.get_trip_for_agency("nonexistent", "agency_a")
        assert result is None


# ---------------------------------------------------------------------------
# 8. Fixture seeding — no agency_id reassignment
# ---------------------------------------------------------------------------

class TestFixtureSeedingNoReassignment:
    def test_seed_does_not_reassign_existing_trip(self, tmp_path, monkeypatch):
        """_seed_scenario_for_agency must never rewrite agency_id on existing trips."""
        monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
        from pathlib import Path
        from spine_api.persistence import FileTripStore, TRIPS_DIR, DATA_DIR
        from spine_api.server import _seed_scenario_for_agency

        data_dir = tmp_path / "data"
        trips_dir = data_dir / "trips"
        fixtures_dir = data_dir / "fixtures"
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        trips_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", trips_dir)
        monkeypatch.setattr("spine_api.persistence.DATA_DIR", data_dir)
        monkeypatch.setattr("spine_api.server.PROJECT_ROOT", tmp_path)

        # Create a fixture file
        import json
        fixture = [{"id": "trip_f1", "status": "new", "created_at": "2026-01-01T00:00:00"}]
        fixture_path = fixtures_dir / "test_fixture.json"
        fixture_path.write_text(json.dumps(fixture))

        # Seed for agency_a
        monkeypatch.setenv("SEED_SCENARIO", "test_fixture")
        count_a = _seed_scenario_for_agency("agency_a")
        assert count_a == 1
        trip = FileTripStore.get_trip("trip_f1")
        assert trip["agency_id"] == "agency_a"

        # Seed again for agency_b — must NOT reassign
        count_b = _seed_scenario_for_agency("agency_b")
        assert count_b == 0  # Skipped, not reassigned
        trip_after = FileTripStore.get_trip("trip_f1")
        assert trip_after["agency_id"] == "agency_a"  # Unchanged
