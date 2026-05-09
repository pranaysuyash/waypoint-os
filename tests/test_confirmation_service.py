"""Tests for confirmation service — pure unit tests, no DB."""

import pytest

from spine_api.models.tenant import (
    CONFIRMATION_VALID_TRANSITIONS,
    CONFIRMATION_TYPES,
    CONFIRMATION_STATUSES,
    NOTES_MAX_LENGTH,
    ALLOWED_EVIDENCE_REF_TYPES,
)
from spine_api.services.confirmation_service import (
    _validate_evidence_refs,
    NOTES_MAX_LENGTH as SVC_NOTES_MAX,
)
from spine_api.services.private_fields import encrypt_field, decrypt_field, encrypt_blob, decrypt_blob


# ── State machine ────────────────────────────────────────────────────────────

class TestConfirmationStateMachine:
    def test_draft_to_recorded(self):
        assert "recorded" in CONFIRMATION_VALID_TRANSITIONS["draft"]

    def test_draft_to_voided(self):
        assert "voided" in CONFIRMATION_VALID_TRANSITIONS["draft"]

    def test_recorded_to_verified(self):
        assert "verified" in CONFIRMATION_VALID_TRANSITIONS["recorded"]

    def test_recorded_to_voided(self):
        assert "voided" in CONFIRMATION_VALID_TRANSITIONS["recorded"]

    def test_verified_to_voided(self):
        assert "voided" in CONFIRMATION_VALID_TRANSITIONS["verified"]

    def test_voided_has_no_transitions(self):
        assert CONFIRMATION_VALID_TRANSITIONS["voided"] == set()

    def test_draft_cannot_go_to_verified(self):
        assert "verified" not in CONFIRMATION_VALID_TRANSITIONS["draft"]

    def test_verified_cannot_go_to_recorded(self):
        assert "recorded" not in CONFIRMATION_VALID_TRANSITIONS["verified"]

    def test_recorded_cannot_go_to_draft(self):
        assert "draft" not in CONFIRMATION_VALID_TRANSITIONS["recorded"]

    def test_voided_cannot_go_to_draft(self):
        assert "draft" not in CONFIRMATION_VALID_TRANSITIONS["voided"]


# ── Encryption helpers ────────────────────────────────────────────────────────

class TestEncryptionHelpers:
    def test_encrypt_decrypt_round_trip(self):
        original = "Emirates Airlines"
        encrypted = encrypt_field(original)
        assert encrypted is not None
        assert encrypted.get("__encrypted_blob") is True
        decrypted = decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_none_returns_none(self):
        assert encrypt_field(None) is None

    def test_encrypt_empty_returns_none(self):
        assert encrypt_field("") is None

    def test_encrypt_whitespace_stripped(self):
        encrypted = encrypt_field("  value  ")
        decrypted = decrypt_field(encrypted)
        assert decrypted == "value"

    def test_decrypt_none_returns_none(self):
        assert decrypt_field(None) is None

    def test_blob_round_trip(self):
        data = {"key": "value", "nested": {"a": 1}}
        encrypted = encrypt_blob(data)
        decrypted = decrypt_blob(encrypted)
        assert decrypted == data

    def test_blob_none_returns_none(self):
        assert encrypt_blob(None) is None
        assert decrypt_blob(None) is None


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_confirmation_types(self):
        assert "flight" in CONFIRMATION_TYPES
        assert "hotel" in CONFIRMATION_TYPES
        assert "insurance" in CONFIRMATION_TYPES
        assert "payment" in CONFIRMATION_TYPES
        assert "other" in CONFIRMATION_TYPES

    def test_confirmation_statuses(self):
        assert set(CONFIRMATION_STATUSES) == {"draft", "recorded", "verified", "voided"}

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 2000
        assert SVC_NOTES_MAX == 2000

    def test_evidence_ref_types(self):
        assert "booking_document" in ALLOWED_EVIDENCE_REF_TYPES
        assert "document_extraction" in ALLOWED_EVIDENCE_REF_TYPES
        assert "extraction_attempt" in ALLOWED_EVIDENCE_REF_TYPES
        assert "booking_task" in ALLOWED_EVIDENCE_REF_TYPES


# ── Evidence ref validation ──────────────────────────────────────────────────

class TestEvidenceRefValidation:
    def test_valid_refs_pass(self):
        refs = [
            {"type": "booking_document", "id": "doc-1"},
            {"type": "booking_task", "id": "task-1"},
        ]
        _validate_evidence_refs(refs)  # should not raise

    def test_invalid_type_rejected(self):
        with pytest.raises(ValueError, match="Invalid evidence ref type"):
            _validate_evidence_refs([{"type": "random_string", "id": "x"}])

    def test_missing_id_rejected(self):
        with pytest.raises(ValueError, match="must have 'type' and 'id'"):
            _validate_evidence_refs([{"type": "booking_task"}])

    def test_missing_type_rejected(self):
        with pytest.raises(ValueError, match="must have 'type' and 'id'"):
            _validate_evidence_refs([{"id": "task-1"}])

    def test_none_refs_pass(self):
        _validate_evidence_refs(None)  # should not raise

    def test_empty_refs_pass(self):
        _validate_evidence_refs([])  # should not raise

    def test_non_dict_ref_rejected(self):
        with pytest.raises(ValueError, match="must be a dict"):
            _validate_evidence_refs(["not_a_dict"])
