"""
tests/test_booking_data — Phase 3B booking data tests.

Covers: encryption, endpoints, stage gate, optimistic lock,
audit, validation, readiness, mutation guards.

Run: uv run pytest tests/test_booking_data.py -v
"""

import os
import pytest
from unittest.mock import MagicMock

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
        "agency_id": "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
        "status": "assigned",
        "stage": "proposal",
        "extracted": {},
        "validation": {},
        "decision": {},
        "raw_input": {},
    }
    trip_id = TripStore.save_trip(trip_data, agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b")
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
