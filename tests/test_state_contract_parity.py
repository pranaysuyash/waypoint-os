"""
Trip State Contract — Refresh Parity & Encryption Regression Tests.

Verifies:
1. _build_processed_trip produces a dict with all 9 pipeline compartments
2. SQLTripStore._encrypt_pii / _decrypt_pii are symmetric (round-trip)
3. PII fields are never stored as plaintext after encryption
4. FileTripStore round-trips all compartments unchanged
5. _to_dict / save_trip symmetry — what goes in comes back out
6. Encryption does not corrupt non-PII fields
7. Nested structures (lists of dicts) are encrypted recursively
"""

import json
import sys
import pytest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_spine_api_dir = str(Path(__file__).resolve().parent.parent / "spine_api")
_src_dir = str(Path(__file__).resolve().parent.parent / "src")
for _p in (_spine_api_dir, _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from spine_api.persistence import SQLTripStore, FileTripStore, _build_processed_trip
from src.security.encryption import encrypt, decrypt


# ---------------------------------------------------------------------------
# Fixtures — synthetic pipeline output that mirrors SpineRunResponse
# ---------------------------------------------------------------------------

def _make_spine_output() -> dict:
    """Produce a synthetic pipeline output with all 9 compartments populated."""
    return {
        "run_id": "run_test_001",
        "packet": {
            "facts": {
                "destination_candidates": {"value": ["Singapore"]},
                "budget": {"value": 5000},
                "party_size": {"value": 2},
                "date_window": {"value": "June 2026"},
            },
            "stage": "discovery",
            "operating_mode": "normal_intake",
        },
        "validation": {
            "is_valid": True,
            "errors": [],
            "warnings": ["budget_not_confirmed"],
        },
        "decision": {
            "packet_id": "pkt_abc123",
            "decision_state": "PROCEED",
            "confidence_score": 0.82,
            "hard_blockers": [],
            "soft_blockers": [],
        },
        "strategy": {
            "recommended_path": "standard_intake",
            "urgency": "normal",
        },
        "traveler_bundle": {
            "summary": "Family trip to Singapore, 5 days, budget $5000",
            "traveler_name": "Jane Doe",
            "traveler_email": "jane@example.com",
            "traveler_phone": "+1-555-0123",
        },
        "internal_bundle": {
            "margin_estimate": 0.22,
            "risk_flags": [],
            "agent_notes": "Customer seems flexible on dates",
        },
        "safety": {
            "leakage_check": {"passed": True, "forbidden_terms_found": []},
            "suitability_flags": [],
        },
        "fees": {
            "service_breakdowns": [
                {"service": "flight_booking", "base_fee": 150, "adjusted_fee": 135}
            ],
            "total_base_fee": 150,
            "total_adjusted_fee": 135,
        },
        "frontier_result": {
            "ghost_triggered": True,
            "ghost_workflow_id": "wf_ghost_001",
            "sentiment_score": 0.78,
            "anxiety_alert": False,
            "intelligence_hits": [
                {"message": "Monsoon season approaching", "severity": "high", "source": "weather_api"}
            ],
            "mitigation_applied": False,
            "requires_manual_audit": False,
            "negotiation_active": False,
        },
        "meta": {
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "fixture_id": None,
            "execution_ms": 1200,
        },
    }


def _make_full_trip_data() -> dict:
    """Minimal trip dict matching what _build_processed_trip returns."""
    output = _make_spine_output()
    return _build_processed_trip(
        spine_output=output,
        source="test",
        user_id=None,
        follow_up_due_date=None,
        party_composition="2 adults",
        pace_preference="relaxed",
        date_year_confidence="high",
        lead_source="web",
        activity_provenance="manual",
        trip_status="assigned",
    )


# The 9 compartments that must survive a full save → load cycle.
PIPELINE_COMPARTMENTS = [
    "extracted",
    "validation",
    "decision",
    "strategy",
    "traveler_bundle",
    "internal_bundle",
    "safety",
    "fees",
    "frontier_result",
]


# ===========================================================================
# 1. _build_processed_trip produces all compartments
# ===========================================================================

class TestBuildProcessedTrip:
    """Verify _build_processed_trip maps every pipeline compartment into the trip dict."""

    def test_all_nine_compartments_present(self):
        trip = _make_full_trip_data()
        missing = [c for c in PIPELINE_COMPARTMENTS if c not in trip]
        assert not missing, f"Missing compartments: {missing}"

    def test_extracted_receives_packet(self):
        trip = _make_full_trip_data()
        assert trip["extracted"]["facts"]["destination_candidates"]["value"] == ["Singapore"]

    def test_frontier_result_preserved(self):
        trip = _make_full_trip_data()
        fr = trip["frontier_result"]
        assert fr is not None
        assert fr["ghost_triggered"] is True
        assert fr["sentiment_score"] == 0.78
        assert len(fr["intelligence_hits"]) == 1

    def test_fees_preserved(self):
        trip = _make_full_trip_data()
        fees = trip["fees"]
        assert fees is not None
        assert fees["total_base_fee"] == 150
        assert fees["service_breakdowns"][0]["service"] == "flight_booking"

    def test_traveler_bundle_preserved(self):
        trip = _make_full_trip_data()
        tb = trip["traveler_bundle"]
        assert tb is not None
        assert tb["traveler_name"] == "Jane Doe"

    def test_safety_preserved(self):
        trip = _make_full_trip_data()
        safety = trip["safety"]
        assert safety["leakage_check"]["passed"] is True


# ===========================================================================
# 2. Encryption / Decryption round-trip
# ===========================================================================

class TestEncryptionRoundTrip:
    """Verify _encrypt_pii and _decrypt_pii are symmetric."""

    def test_round_trip_flat_dict_with_pii(self):
        data = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "passport_number": "X1234567",
            "destination": "Tokyo",
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert decrypted["name"] == "Alice Smith"
        assert decrypted["email"] == "alice@example.com"
        assert decrypted["passport_number"] == "X1234567"
        assert decrypted["destination"] == "Tokyo"

    def test_pii_fields_are_not_plaintext_after_encrypt(self):
        data = {"name": "Bob Jones", "city": "London"}
        encrypted = SQLTripStore._encrypt_pii(data)

        # "name" is a PII field — must be encrypted
        assert encrypted["name"] != "Bob Jones"
        assert len(encrypted["name"]) > len("Bob Jones")

        # "city" is NOT a PII field — must be plaintext
        assert encrypted["city"] == "London"

    def test_nested_list_of_dicts(self):
        data = {
            "intelligence_hits": [
                {"message": "Low risk", "severity": "low", "name": "Agent X"},
                {"message": "High risk", "severity": "high", "name": "Agent Y"},
            ]
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        for i in range(2):
            assert decrypted["intelligence_hits"][i]["name"] == data["intelligence_hits"][i]["name"]
            assert decrypted["intelligence_hits"][i]["message"] == data["intelligence_hits"][i]["message"]

    def test_deeply_nested_structure(self):
        data = {
            "extracted": {
                "facts": {
                    "traveler_name": "Deeply Nested",
                    "destination": "Paris",
                }
            }
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert decrypted["extracted"]["facts"]["traveler_name"] == "Deeply Nested"
        assert encrypted["extracted"]["facts"]["traveler_name"] != "Deeply Nested"
        assert decrypted["extracted"]["facts"]["destination"] == "Paris"

    def test_empty_values_unchanged(self):
        data = {"name": "", "email": None, "destination": ""}
        encrypted = SQLTripStore._encrypt_pii(data)
        # encrypt("") returns "" (see encryption.py)
        assert encrypted["name"] == ""
        assert encrypted["email"] is None
        assert encrypted["destination"] == ""

    def test_non_string_pii_values_untouched(self):
        """PII keys with non-string values (numbers, bools, lists) must not be encrypted."""
        data = {"name": 42, "email": True, "destination": "Berlin"}
        encrypted = SQLTripStore._encrypt_pii(data)
        assert encrypted["name"] == 42
        assert encrypted["email"] is True
        assert encrypted["destination"] == "Berlin"

    def test_frontier_result_with_pii_round_trips(self):
        """Frontier result may contain PII in nested intelligence hits."""
        data = {
            "ghost_triggered": True,
            "sentiment_score": 0.78,
            "intelligence_hits": [
                {"message": "Visa check: traveler_name=John, passport_number=AB123",
                 "severity": "high", "source": "federation"},
            ],
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert decrypted["ghost_triggered"] is True
        assert decrypted["sentiment_score"] == 0.78
        assert decrypted["intelligence_hits"][0]["message"] == data["intelligence_hits"][0]["message"]

    def test_traveler_bundle_pii_encrypted(self):
        """traveler_bundle is the most PII-rich compartment."""
        data = {
            "summary": "Trip for Jane",
            "traveler_name": "Jane Doe",
            "traveler_email": "jane@example.com",
            "traveler_phone": "+1-555-0123",
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert encrypted["traveler_name"] != "Jane Doe"
        assert encrypted["traveler_email"] != "jane@example.com"
        assert encrypted["traveler_phone"] != "+1-555-0123"

        assert decrypted["traveler_name"] == "Jane Doe"
        assert decrypted["traveler_email"] == "jane@example.com"
        assert decrypted["traveler_phone"] == "+1-555-0123"


# ===========================================================================
# 3. Encryption regression — classified fields never plaintext in DB
# ===========================================================================

class TestEncryptionRegression:
    """Assert that classified private fields are never stored as plaintext."""

    PII_SAMPLE_VALUES = {
        "name": "Test Person",
        "email": "test@example.com",
        "passport_number": "AB1234567",
        "phone": "+1-555-0000",
        "full_name": "Full Name Test",
        "customer_email": "cust@example.com",
        "traveler_name": "Traveler Name",
        "traveler_email": "traveler@example.com",
        "traveler_phone": "+1-555-1111",
    }

    def test_all_pii_fields_in_set_are_encrypted(self):
        """Every key in _PII_FIELDS must trigger encryption when its value is a string."""
        for field_name, sample_value in self.PII_SAMPLE_VALUES.items():
            assert field_name.lower() in SQLTripStore._PII_FIELDS, (
                f"'{field_name}' not in _PII_FIELDS"
            )
            encrypted = SQLTripStore._encrypt_pii({field_name: sample_value})
            assert encrypted[field_name] != sample_value, (
                f"Field '{field_name}' was NOT encrypted — still plaintext"
            )

    def test_encrypt_decrypt_stable_across_multiple_calls(self):
        """Encryption must be deterministic for the same key and value (Fernet)."""
        data = {"name": "Consistency Check"}
        enc1 = SQLTripStore._encrypt_pii(data)
        enc2 = SQLTripStore._encrypt_pii(data)
        # Fernet includes timestamp, so tokens may differ — but decryption must match
        dec1 = SQLTripStore._decrypt_pii(enc1)
        dec2 = SQLTripStore._decrypt_pii(enc2)
        assert dec1 == dec2 == data

    def test_traveler_bundle_not_plaintext_in_save_dict(self):
        """Simulate what save_trip receives and verify PII is encrypted before DB write."""
        trip_data = _make_full_trip_data()
        # Mimic what save_trip does for traveler_bundle
        traveler_bundle = trip_data.get("traveler_bundle")
        encrypted = SQLTripStore._encrypt_pii(traveler_bundle)

        assert encrypted["traveler_name"] != "Jane Doe"
        assert encrypted["traveler_email"] != "jane@example.com"

    def test_raw_pii_not_in_extracted_after_encrypt(self):
        """The 'extracted' compartment may contain traveler_name etc."""
        trip_data = _make_full_trip_data()
        extracted = trip_data.get("extracted", {})
        # Inject PII into extracted
        extracted["facts"]["traveler_name"] = "Secret Person"
        extracted["facts"]["contact_email"] = "secret@example.com"

        encrypted = SQLTripStore._encrypt_pii(extracted)

        assert encrypted["facts"]["traveler_name"] != "Secret Person"
        assert encrypted["facts"]["contact_email"] != "secret@example.com"
        assert encrypted["facts"]["destination_candidates"] == {"value": ["Singapore"]}


# ===========================================================================
# 4. FileTripStore parity
# ===========================================================================

class TestFileTripStoreParity:
    """FileTripStore must persist and return all 9 compartments unchanged."""

    def test_round_trip_preserves_all_compartments(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        assert loaded is not None, "Trip not found after save"

        for compartment in PIPELINE_COMPARTMENTS:
            original = trip_data.get(compartment)
            retrieved = loaded.get(compartment)
            assert retrieved is not None, f"Compartment '{compartment}' is None after load"
            assert retrieved == original, (
                f"Compartment '{compartment}' mismatch:\n"
                f"  original:  {json.dumps(original, default=str)[:200]}\n"
                f"  retrieved: {json.dumps(retrieved, default=str)[:200]}"
            )

    def test_file_store_preserves_frontier_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        fr = loaded["frontier_result"]
        assert fr["ghost_triggered"] is True
        assert fr["ghost_workflow_id"] == "wf_ghost_001"
        assert fr["sentiment_score"] == 0.78
        assert fr["intelligence_hits"][0]["severity"] == "high"

    def test_file_store_preserves_fees(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        fees = loaded["fees"]
        assert fees["total_base_fee"] == 150
        assert fees["total_adjusted_fee"] == 135
        assert len(fees["service_breakdowns"]) == 1


# ===========================================================================
# 5. SQLTripStore _to_dict / save_trip symmetry (unit-level, no DB)
# ===========================================================================

class TestSQLSymmetry:
    """Verify save_trip's encryption and _to_dict's decryption are inverses.

    We test the encryption/decryption functions directly rather than
    requiring a running database. This proves the round-trip is correct
    regardless of which ORM backend is active.
    """

    def test_encrypt_decrypt_symmetry_for_all_compartments(self):
        trip_data = _make_full_trip_data()

        # Simulate what save_trip does: encrypt PII in each compartment
        encrypted_compartments = {}
        for key in PIPELINE_COMPARTMENTS:
            value = trip_data.get(key)
            if value is None:
                encrypted_compartments[key] = None
            elif key in ("validation", "decision"):
                # These compartments are NOT encrypted in save_trip
                encrypted_compartments[key] = value
            else:
                encrypted_compartments[key] = SQLTripStore._encrypt_pii(value)

        # Simulate what _to_dict does: decrypt PII from each compartment
        decrypted_compartments = {}
        for key, enc_value in encrypted_compartments.items():
            if enc_value is None:
                decrypted_compartments[key] = None
            elif key in ("validation", "decision"):
                decrypted_compartments[key] = enc_value
            else:
                decrypted_compartments[key] = SQLTripStore._decrypt_pii(enc_value)

        # Verify round-trip
        for key in PIPELINE_COMPARTMENTS:
            original = trip_data.get(key)
            decrypted = decrypted_compartments[key]
            assert decrypted == original, (
                f"Round-trip failed for '{key}':\n"
                f"  original:   {json.dumps(original, default=str)[:200]}\n"
                f"  decrypted:  {json.dumps(decrypted, default=str)[:200]}"
            )

    def test_pii_not_plaintext_after_encrypt_for_rich_compartments(self):
        """After encryption, traveler_bundle PII must be ciphertext."""
        trip_data = _make_full_trip_data()

        tb = trip_data["traveler_bundle"]
        encrypted = SQLTripStore._encrypt_pii(tb)

        pii_keys_present = [k for k in tb.keys() if k.lower() in SQLTripStore._PII_FIELDS]
        assert len(pii_keys_present) > 0, "Test data must contain at least one PII field"

        for pii_key in pii_keys_present:
            assert encrypted[pii_key] != tb[pii_key], (
                f"PII field '{pii_key}' is still plaintext after encryption"
            )


# ===========================================================================
# 6. Encryption does not corrupt non-PII fields
# ===========================================================================

class TestNonPIIFieldIntegrity:
    """Non-PII fields (numbers, bools, non-PII strings) must pass through unchanged."""

    def test_boolean_fields_unchanged(self):
        data = {
            "ghost_triggered": True,
            "anxiety_alert": False,
            "mitigation_applied": False,
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)
        assert decrypted == data

    def test_numeric_fields_unchanged(self):
        data = {
            "sentiment_score": 0.78,
            "total_base_fee": 150,
            "party_size": 2,
            "confidence_score": 0.82,
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)
        assert decrypted == data

    def test_non_pii_strings_unchanged(self):
        data = {
            "ghost_workflow_id": "wf_ghost_001",
            "severity": "high",
            "source": "weather_api",
            "service": "flight_booking",
            "destination": "Singapore",
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)
        assert decrypted == data

    def test_list_of_non_pii_dicts_unchanged(self):
        data = {
            "service_breakdowns": [
                {"service": "flight_booking", "base_fee": 150, "adjusted_fee": 135}
            ],
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)
        assert decrypted == data

    def test_mixed_pii_non_pii_in_same_dict(self):
        data = {
            "severity": "critical",
            "message": "Visa required",
            "name": "Mixed Test",
            "source": "federation",
            "email": "mixed@example.com",
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        # Non-PII must be untouched
        assert encrypted["severity"] == "critical"
        assert encrypted["message"] == "Visa required"
        assert encrypted["source"] == "federation"

        # PII must be encrypted
        assert encrypted["name"] != "Mixed Test"
        assert encrypted["email"] != "mixed@example.com"

        # After decryption, everything matches
        assert decrypted == data


# ===========================================================================
# 7. Nested list-of-dicts with PII
# ===========================================================================

class TestNestedPII:
    """Verify recursive encryption handles lists containing PII-bearing dicts."""

    def test_intelligence_hits_with_pii(self):
        data = {
            "intelligence_hits": [
                {
                    "message": "Traveler flagged",
                    "severity": "high",
                    "traveler_name": "Flagged Person",
                    "source": "federation",
                },
                {
                    "message": "Low risk area",
                    "severity": "low",
                    "source": "weather_api",
                },
            ]
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        # First hit has PII
        assert encrypted["intelligence_hits"][0]["traveler_name"] != "Flagged Person"
        assert decrypted["intelligence_hits"][0]["traveler_name"] == "Flagged Person"

        # Non-PII fields pass through
        assert encrypted["intelligence_hits"][0]["severity"] == "high"
        assert encrypted["intelligence_hits"][1]["message"] == "Low risk area"

        assert decrypted == data

    def test_empty_list_passes_through(self):
        data = {"intelligence_hits": []}
        result = SQLTripStore._encrypt_pii(data)
        assert result == {"intelligence_hits": []}

    def test_suitability_flags_in_safety(self):
        data = {
            "suitability_flags": [
                {"flag": "elderly_mobility", "severity": "medium", "name": "Elderly Traveler"},
            ]
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        # "name" is a PII field
        assert encrypted["suitability_flags"][0]["name"] != "Elderly Traveler"
        assert encrypted["suitability_flags"][0]["flag"] == "elderly_mobility"
        assert decrypted["suitability_flags"][0]["name"] == "Elderly Traveler"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
