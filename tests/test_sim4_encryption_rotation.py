"""
FND-0327 (Sim #4): a trip encrypted under one ENCRYPTION_KEY must stay
*readable as a trip* under another key — with an explicit unreadable marker
and warnings — never a 500 from json.loads(ciphertext), and the rotation tool
must bring the row back.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from spine_api.persistence import SQLTripStore
from src.security import encryption as enc
from tools.reencrypt_trip_rows import RotationReport, rotate_row

KEY_A = Fernet.generate_key().decode()
KEY_B = Fernet.generate_key().decode()
KEY_C = Fernet.generate_key().decode()


@pytest.fixture
def use_key(monkeypatch):
    def _set(key: str):
        monkeypatch.setenv("ENCRYPTION_KEY", key)
        enc._clear_fernet_cache()
    yield _set
    enc._clear_fernet_cache()


def test_blob_carries_kid_and_decrypts_under_same_key(use_key):
    use_key(KEY_A)
    blob = SQLTripStore._encrypt_blob({"hotel": "ground floor"})
    assert blob["v"] == 2 and blob["kid"] == enc.key_fingerprint()
    assert SQLTripStore._decrypt_blob(blob) == {"hotel": "ground floor"}


def test_foreign_key_blob_yields_marker_not_crash(use_key):
    use_key(KEY_A)
    blob = SQLTripStore._encrypt_blob({"hotel": "ground floor"})
    kid_a = blob["kid"]
    use_key(KEY_B)
    out = SQLTripStore._decrypt_blob(blob)  # must not raise
    assert out["__unreadable"] is True
    assert out["reason"] == "encryption_key_mismatch"
    assert out["kid_expected"] == kid_a and out["kid_active"] == enc.key_fingerprint()
    assert "reencrypt_trip_rows" in out["remediation"]


def test_legacy_plaintext_blob_passes_through(use_key):
    use_key(KEY_A)
    assert SQLTripStore._decrypt_blob({"legacy": True}) == {"legacy": True}
    assert SQLTripStore._decrypt_blob(None) is None


def test_foreign_key_pii_string_becomes_sentinel_not_ciphertext(use_key):
    use_key(KEY_A)
    stored = SQLTripStore._encrypt_pii({"customer_name": "Meera Krishnan", "budget": 40000})
    assert enc.looks_like_fernet_token(stored["customer_name"])
    use_key(KEY_B)
    out = SQLTripStore._decrypt_pii(stored)
    assert out["customer_name"] == SQLTripStore.UNREADABLE_PII_SENTINEL
    assert out["budget"] == 40000
    # legacy plaintext at a PII key is still returned as-is
    assert SQLTripStore._decrypt_pii({"customer_name": "Plain Name"})["customer_name"] == "Plain Name"


def test_to_dict_surfaces_encryption_warnings(use_key):
    use_key(KEY_A)
    foreign = SQLTripStore._encrypt_blob({"bundle": 1})
    use_key(KEY_B)
    trip_obj = SimpleNamespace(
        id="trip_x", run_id=None, agency_id="ag", user_id=None, assigned_to_id=None,
        source="sim", status="new", stage="discovery", follow_up_due_date=None,
        party_composition=None, pace_preference=None, date_year_confidence=None,
        lead_source=None, activity_provenance=None, extracted={}, validation={},
        decision={}, strategy=None, traveler_bundle=foreign, internal_bundle=None,
        safety=None, frontier_result=None, fees=None, raw_input={}, analytics=None,
        booking_data=None, pending_booking_data=None, booking_data_source=None,
        created_at=None, updated_at=None,
    )
    res = SQLTripStore._to_dict(trip_obj)
    assert res["traveler_bundle"]["__unreadable"] is True
    assert res["encryption_warnings"][0]["field"] == "traveler_bundle"
    assert res["encryption_warnings"][0]["kid_expected"] == foreign["kid"]


def test_rotation_tool_restores_readability_and_reports_unreadable(use_key):
    use_key(KEY_A)
    blob_a = SQLTripStore._encrypt_blob({"deposit": 100})
    pii_a = SQLTripStore._encrypt_pii({"customer_name": "Kavya Nair", "n": 1})
    use_key(KEY_C)
    blob_c = SQLTripStore._encrypt_blob({"other": True})
    row = {"id": "trip_r", "traveler_bundle": blob_a, "internal_bundle": blob_c, "safety": None,
           "fees": {"legacy": "plain"}, "frontier_result": None, "booking_data": None,
           "pending_booking_data": None, "extracted": pii_a, "raw_input": {}, "analytics": None}
    report = RotationReport()
    changes = rotate_row(row, Fernet(KEY_A.encode()), Fernet(KEY_B.encode()), "kidB", report)
    assert set(changes) == {"traveler_bundle", "extracted"}
    assert report.unreadable == [("trip_r", "internal_bundle")]
    assert report.fields_legacy_plain >= 1
    use_key(KEY_B)
    assert SQLTripStore._decrypt_blob(changes["traveler_bundle"]) == {"deposit": 100}
    assert SQLTripStore._decrypt_pii(changes["extracted"])["customer_name"] == "Kavya Nair"
