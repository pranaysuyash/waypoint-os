"""
Trip State Contract — Refresh Parity & Encryption Regression Tests.

Verifies the dual encryption model:
  - Private compartments (traveler_bundle, internal_bundle, safety, fees,
    frontier_result) are blob-encrypted — entire JSON becomes one Fernet token.
  - PII-key fields (extracted, raw_input) use recursive key-level encryption.

Also verifies:
  1. _build_processed_trip produces all 9 compartments
  2. Blob encrypt/decrypt round-trips are symmetric
  3. PII key-level encrypt/decrypt round-trips are symmetric
  4. Private compartments have NO plaintext after blob encryption (sentinel test)
  5. _encrypt_field_for_storage / _decrypt_field_from_storage unified path
  6. FileTripStore round-trips all compartments unchanged
  7. update_trip applies the same encryption as save_trip
"""

import json
import sys
import pytest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

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

# Private compartments that use blob encryption (whole JSON → one token).
PRIVATE_BLOB_COMPARTMENTS = [
    "traveler_bundle",
    "internal_bundle",
    "safety",
    "fees",
    "frontier_result",
]

# Sentinel strings that must NEVER appear in raw encrypted storage.
SENTINEL = "DO_NOT_STORE_ME_PLAINTEXT_"


# ===========================================================================
# 1. _build_processed_trip produces all compartments
# ===========================================================================

class TestBuildProcessedTrip:
    def test_all_nine_compartments_present(self):
        trip = _make_full_trip_data()
        missing = [c for c in PIPELINE_COMPARTMENTS if c not in trip]
        assert not missing, f"Missing compartments: {missing}"

    def test_frontier_result_preserved(self):
        trip = _make_full_trip_data()
        fr = trip["frontier_result"]
        assert fr is not None
        assert fr["ghost_triggered"] is True
        assert fr["sentiment_score"] == 0.78

    def test_fees_preserved(self):
        trip = _make_full_trip_data()
        assert trip["fees"]["total_base_fee"] == 150

    def test_traveler_bundle_preserved(self):
        trip = _make_full_trip_data()
        assert trip["traveler_bundle"]["traveler_name"] == "Jane Doe"

    def test_safety_preserved(self):
        trip = _make_full_trip_data()
        assert trip["safety"]["leakage_check"]["passed"] is True


# ===========================================================================
# 2. Blob encryption round-trip (private compartments)
# ===========================================================================

class TestBlobEncryption:
    """Verify _encrypt_blob / _decrypt_blob for private compartments."""

    def test_blob_round_trip(self):
        data = {"sentiment_score": 0.78, "ghost_triggered": True, "intel": "secret"}
        encrypted = SQLTripStore._encrypt_blob(data)
        decrypted = SQLTripStore._decrypt_blob(encrypted)

        assert decrypted == data
        assert encrypted["__encrypted_blob"] is True
        assert "ciphertext" in encrypted

    def test_blob_no_plaintext_content(self):
        """After blob encryption, no original string should be findable."""
        data = {"agent_notes": "sensitive margin data", "margin_estimate": 0.22}
        encrypted = SQLTripStore._encrypt_blob(data)
        serialized = json.dumps(encrypted)

        assert "sensitive margin data" not in serialized
        assert "margin_estimate" not in serialized

    def test_blob_none_passes_through(self):
        assert SQLTripStore._encrypt_blob(None) is None
        assert SQLTripStore._decrypt_blob(None) is None

    def test_blob_preserves_types(self):
        data = {
            "bool": True,
            "int": 42,
            "float": 3.14,
            "string": "hello",
            "list": [1, 2, 3],
            "nested": {"a": {"b": "deep"}},
        }
        encrypted = SQLTripStore._encrypt_blob(data)
        decrypted = SQLTripStore._decrypt_blob(encrypted)
        assert decrypted == data

    def test_plaintext_dict_passes_through_decrypt(self):
        """Pre-migration plaintext data should pass through _decrypt_blob unchanged."""
        data = {"old_field": "old_value"}
        assert SQLTripStore._decrypt_blob(data) == data

    def test_blob_wraps_structure_correctly(self):
        """Encrypted blob must have the __encrypted_blob wrapper shape."""
        data = {"key": "value"}
        encrypted = SQLTripStore._encrypt_blob(data)

        assert isinstance(encrypted, dict)
        assert encrypted["__encrypted_blob"] is True
        assert encrypted["v"] == 1
        assert isinstance(encrypted["ciphertext"], str)
        assert len(encrypted["ciphertext"]) > 0


# ===========================================================================
# 3. PII key-level encryption round-trip
# ===========================================================================

class TestPIIKeyEncryption:
    """Verify _encrypt_pii / _decrypt_pii for PII-key fields."""

    def test_pii_keys_encrypt_non_pii_pass_through(self):
        data = {"name": "Alice", "destination": "Tokyo"}
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert encrypted["name"] != "Alice"
        assert encrypted["destination"] == "Tokyo"
        assert decrypted == data

    def test_nested_pii_in_lists(self):
        data = {
            "items": [
                {"name": "Agent X", "role": "analyst"},
                {"name": "Agent Y", "role": "manager"},
            ]
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert encrypted["items"][0]["name"] != "Agent X"
        assert encrypted["items"][0]["role"] == "analyst"
        assert decrypted == data

    def test_all_pii_fields_encrypt(self):
        for field_name in SQLTripStore._PII_FIELDS:
            encrypted = SQLTripStore._encrypt_pii({field_name: "test_value"})
            assert encrypted[field_name] != "test_value", (
                f"PII field '{field_name}' not encrypted"
            )

    def test_non_string_pii_values_untouched(self):
        data = {"name": 42, "email": True}
        encrypted = SQLTripStore._encrypt_pii(data)
        assert encrypted["name"] == 42
        assert encrypted["email"] is True


# ===========================================================================
# 4. Unified encrypt/decrypt field helper
# ===========================================================================

class TestUnifiedFieldHelper:
    """Verify _encrypt_field_for_storage / _decrypt_field_from_storage."""

    def test_private_fields_get_blob_encrypted(self):
        for field in PRIVATE_BLOB_COMPARTMENTS:
            data = {"some": "data", "nested": {"key": "value"}}
            encrypted = SQLTripStore._encrypt_field_for_storage(field, data)
            assert isinstance(encrypted, dict)
            assert encrypted.get("__encrypted_blob") is True, (
                f"Field '{field}' was not blob-encrypted"
            )
            decrypted = SQLTripStore._decrypt_field_from_storage(field, encrypted)
            assert decrypted == data

    def test_pii_key_fields_get_recursive_encryption(self):
        for field in ("extracted", "raw_input"):
            data = {"traveler_name": "Secret", "destination": "Paris"}
            encrypted = SQLTripStore._encrypt_field_for_storage(field, data)
            assert isinstance(encrypted, dict)
            assert encrypted.get("__encrypted_blob") is None, (
                f"Field '{field}' should use PII-key encryption, not blob"
            )
            assert encrypted["traveler_name"] != "Secret"
            assert encrypted["destination"] == "Paris"

    def test_unencrypted_fields_pass_through(self):
        for field in ("validation", "decision", "strategy", "status"):
            data = {"key": "value"}
            assert SQLTripStore._encrypt_field_for_storage(field, data) == data
            assert SQLTripStore._decrypt_field_from_storage(field, data) == data

    def test_none_values_handled(self):
        for field in PRIVATE_BLOB_COMPARTMENTS:
            assert SQLTripStore._encrypt_field_for_storage(field, None) is None
            assert SQLTripStore._decrypt_field_from_storage(field, None) is None

    def test_empty_safety_gets_empty_dict(self):
        """Empty safety dict stays empty (no blob wrapper for empty data)."""
        encrypted = SQLTripStore._encrypt_field_for_storage("safety", {})
        assert encrypted == {}

    def test_safety_with_data_gets_blob_encrypted(self):
        """Non-empty safety gets blob-encrypted."""
        encrypted = SQLTripStore._encrypt_field_for_storage("safety", {"leakage_check": {"passed": True}})
        assert encrypted.get("__encrypted_blob") is True


# ===========================================================================
# 5. Sentinel test — no plaintext in encrypted private compartments
# ===========================================================================

class TestSentinelEncryption:
    """Embed sentinel strings in private compartments and verify they are
    not present in the encrypted output. This is the test ChatGPT requested:
    put 'DO_NOT_STORE_ME_PLAINTEXT_*' in various fields and confirm the
    unified encryption path removes all of them from raw storage."""

    def _make_sentinel_trip_data(self) -> dict:
        """Trip data with sentinel strings in every private compartment."""
        trip = _make_full_trip_data()
        trip["internal_bundle"] = {
            "agent_notes": SENTINEL + "INTERNAL",
            "margin_estimate": 0.22,
        }
        trip["frontier_result"] = {
            "sentiment_score": 0.78,
            "intelligence_hits": [
                {"message": SENTINEL + "FRONTIER", "severity": "high", "source": "test"},
            ],
        }
        trip["fees"] = {
            "total_base_fee": 150,
            "service_breakdowns": [
                {"service": "booking", "base_fee": 100},
            ],
            "private_note": SENTINEL + "FEES",
        }
        trip["traveler_bundle"] = {
            "summary": SENTINEL + "TRAVELER_SUMMARY",
            "user_message": "Regular message",
        }
        trip["safety"] = {
            "leakage_check": {"passed": True},
            "internal_note": SENTINEL + "SAFETY",
        }
        return trip

    def test_sentinels_absent_from_blob_encrypted_storage(self):
        """After encrypting private compartments, no sentinel string appears in raw output."""
        trip = self._make_sentinel_trip_data()

        for field in PRIVATE_BLOB_COMPARTMENTS:
            value = trip.get(field)
            encrypted = SQLTripStore._encrypt_field_for_storage(field, value)
            raw_serialized = json.dumps(encrypted, default=str)

            assert SENTINEL not in raw_serialized, (
                f"Sentinel found in raw encrypted '{field}': {raw_serialized[:200]}"
            )

    def test_sentinels_recovered_after_decrypt(self):
        """After encrypt + decrypt round-trip, sentinel values are intact."""
        trip = self._make_sentinel_trip_data()

        for field in PRIVATE_BLOB_COMPARTMENTS:
            value = trip.get(field)
            encrypted = SQLTripStore._encrypt_field_for_storage(field, value)
            decrypted = SQLTripStore._decrypt_field_from_storage(field, encrypted)
            assert decrypted == value, (
                f"Round-trip failed for '{field}'"
            )

    def test_extracted_pii_keys_encrypted_but_non_pii_visible(self):
        """For PII-key fields, PII sentinels must be encrypted, non-PII can be visible."""
        trip = self._make_sentinel_trip_data()
        trip["extracted"] = {
            "facts": {
                "traveler_name": SENTINEL + "EXTRACTED_PII",
                "destination": SENTINEL + "EXTRACTED_NON_PII",
            }
        }

        encrypted = SQLTripStore._encrypt_field_for_storage("extracted", trip["extracted"])
        raw = json.dumps(encrypted, default=str)

        # traveler_name is PII — sentinel must be encrypted
        assert SENTINEL + "EXTRACTED_PII" not in raw

        # "destination" is NOT PII — it remains visible (by design for PII-key fields)
        assert SENTINEL + "EXTRACTED_NON_PII" in raw


# ===========================================================================
# 6. FileTripStore parity
# ===========================================================================

class TestFileTripStoreParity:
    def test_round_trip_preserves_all_compartments(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        assert loaded is not None
        for compartment in PIPELINE_COMPARTMENTS:
            assert loaded.get(compartment) == trip_data.get(compartment), (
                f"Compartment '{compartment}' mismatch"
            )

    def test_file_store_preserves_frontier_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        assert loaded["frontier_result"]["ghost_triggered"] is True
        assert loaded["frontier_result"]["sentiment_score"] == 0.78

    def test_file_store_preserves_fees(self, tmp_path, monkeypatch):
        monkeypatch.setattr("spine_api.persistence.TRIPS_DIR", tmp_path)
        monkeypatch.setattr("spine_api.persistence.ASSIGNMENTS_DIR", tmp_path)

        trip_data = _make_full_trip_data()
        trip_id = FileTripStore.save_trip(trip_data, agency_id="test_agency")
        loaded = FileTripStore.get_trip(trip_id)

        assert loaded["fees"]["total_base_fee"] == 150
        assert len(loaded["fees"]["service_breakdowns"]) == 1


# ===========================================================================
# 7. update_trip uses same encryption as save_trip
# ===========================================================================

class TestUpdateTripParity:
    """Verify _encrypt_field_for_storage is used for both save and update paths."""

    def test_all_private_fields_encrypted_via_storage_helper(self):
        """Every field in _PRIVATE_BLOB_FIELDS must go through blob encryption."""
        for field in SQLTripStore._PRIVATE_BLOB_FIELDS:
            data = {"test_key": "test_value", "nested": {"a": 1}}
            encrypted = SQLTripStore._encrypt_field_for_storage(field, data)
            assert encrypted.get("__encrypted_blob") is True, (
                f"Field '{field}' not blob-encrypted via unified helper"
            )

    def test_all_pii_key_fields_encrypted_via_storage_helper(self):
        """Every field in _PII_KEY_FIELDS must go through PII-key encryption."""
        for field in SQLTripStore._PII_KEY_FIELDS:
            data = {"name": "PII value", "destination": "non-PII"}
            encrypted = SQLTripStore._encrypt_field_for_storage(field, data)
            assert encrypted.get("__encrypted_blob") is None
            assert encrypted["name"] != "PII value"
            assert encrypted["destination"] == "non-PII"


# ===========================================================================
# 8. Non-PII field integrity under PII-key encryption
# ===========================================================================

class TestNonPIIFieldIntegrity:
    def test_mixed_pii_non_pii_in_same_dict(self):
        data = {
            "severity": "critical",
            "message": "Visa required",
            "name": "Test",
            "source": "federation",
            "email": "test@example.com",
        }
        encrypted = SQLTripStore._encrypt_pii(data)
        decrypted = SQLTripStore._decrypt_pii(encrypted)

        assert encrypted["severity"] == "critical"
        assert encrypted["message"] == "Visa required"
        assert encrypted["name"] != "Test"
        assert decrypted == data


# ===========================================================================
# 9. SQL raw-row sentinel — full save_path exercise
# ===========================================================================

class TestSQLRawRowSentinel:
    """Verify raw DB columns contain NO plaintext sentinels for private compartments."""

    @staticmethod
    def _ensure_test_agency():
        """Create the 'test_agency' agency in DB if it doesn't exist."""
        import asyncio as _asyncio
        from sqlalchemy import text
        from spine_api.persistence import tripstore_session_maker

        async def _run():
            async with tripstore_session_maker() as session:
                # Check by id or slug
                result = await session.execute(
                    text("SELECT 1 FROM agencies WHERE id = 'test_agency' OR slug = 'test-agency'")
                )
                if result.first() is None:
                    try:
                        await session.execute(
                            text(
                                "INSERT INTO agencies (id, slug, name, plan, settings, created_at, jurisdiction) "
                                "VALUES ('test_agency', 'test-agency', 'Test Agency', 'beta', '{}', NOW(), 'US')"
                            )
                        )
                        await session.commit()
                    except Exception:
                        await session.rollback()
                else:
                    # Already exists, make sure slug is correct
                    await session.execute(
                        text("UPDATE agencies SET slug = 'test-agency' WHERE id = 'test_agency'")
                    )
                    await session.commit()

        _asyncio.run(_run())

    def _make_sentinel_trip(self) -> dict:
        """Build a trip dict with sentinel markers for raw-column verification."""
        from tests.test_state_contract_parity import _make_full_trip_data
        trip = _make_full_trip_data()
        trip["internal_bundle"] = {
            "agent_notes": SENTINEL + "INTERNAL",
            "margin_estimate": 0.22,
        }
        trip["frontier_result"] = {
            "intelligence_hits": [
                {"message": SENTINEL + "FRONTIER", "severity": "high"},
            ],
        }
        trip["fees"] = {
            "total_base_fee": 150,
            "private_note": SENTINEL + "FEES",
        }
        trip["traveler_bundle"] = {
            "summary": SENTINEL + "TRAVELER",
        }
        trip["safety"] = {
            "leakage_check": {"passed": True},
            "internal_note": SENTINEL + "SAFETY",
        }
        return trip

    def test_save_path_raw_columns_no_plaintext(self, monkeypatch):
        """save_trip() must produce Trip kwargs with zero plaintext sentinels
        in any private compartment column."""
        import asyncio as _asyncio

        self._ensure_test_agency()

        trip_data = self._make_sentinel_trip()
        captured: dict = {}

        class CapturingTrip:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        async def _run():
            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()

            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_maker = MagicMock(return_value=mock_session)

            monkeypatch.setattr(
                "spine_api.persistence.tripstore_session_maker", mock_maker
            )
            monkeypatch.setattr(
                "spine_api.persistence.Trip", CapturingTrip
            )
            await SQLTripStore.save_trip(
                trip_data, agency_id="test_agency"
            )

        _asyncio.run(_run())

        for field in PRIVATE_BLOB_COMPARTMENTS:
            raw_value = captured.get(field)
            if raw_value is None:
                continue
            raw_serialized = json.dumps(raw_value, default=str)
            assert SENTINEL not in raw_serialized, (
                f"Plaintext sentinel in raw DB column '{field}': "
                f"{raw_serialized[:200]}"
            )

        _asyncio.run(_run())

        for field in PRIVATE_BLOB_COMPARTMENTS:
            raw_value = captured.get(field)
            if raw_value is None:
                continue
            raw_serialized = json.dumps(raw_value, default=str)
            assert SENTINEL not in raw_serialized, (
                f"Plaintext sentinel in raw DB column '{field}': "
                f"{raw_serialized[:200]}"
            )

    def test_save_path_raw_round_trip_preserves_data(self, monkeypatch):
        """After save + read through _to_dict, sentinel data is fully recovered."""
        import asyncio as _asyncio

        self._ensure_test_agency()

        trip_data = self._make_sentinel_trip()

        async def _run():
            # Mock Trip ORM object that stores encrypted values
            stored = {}

            class FakeTrip:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        stored[k] = v

                class __class__:
                    pass

            mock_session = AsyncMock()
            mock_session.get = AsyncMock(return_value=None)
            mock_session.add = MagicMock(side_effect=lambda obj: stored.update(obj.__dict__))
            mock_session.commit = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_maker = MagicMock(return_value=mock_session)

            monkeypatch.setattr(
                "spine_api.persistence.tripstore_session_maker", mock_maker
            )
            monkeypatch.setattr(
                "spine_api.persistence.Trip", FakeTrip
            )
            await SQLTripStore.save_trip(
                trip_data, agency_id="test_agency"
            )

            return stored

        stored = _asyncio.run(_run())

        # Decrypt each private compartment and verify sentinel survives
        for field in PRIVATE_BLOB_COMPARTMENTS:
            original = trip_data.get(field)
            if original is None:
                continue
            encrypted_value = stored.get(field)
            decrypted = SQLTripStore._decrypt_field_from_storage(field, encrypted_value)
            assert decrypted == original, (
                f"Round-trip failed for '{field}': {decrypted} != {original}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
