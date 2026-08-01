"""
tests/test_privacy_guard_nlp.py — Test suite for SpaCy Layer 2 NLP PII guard.

Tests three scenarios:
1. NLP enabled but spacy not installed → graceful fail-open (regex layer still works)
2. NLP disabled via env var → falls back to regex without crash
3. With spacy available: PERSON entity detection in freeform text
4. Fixture data with names → passes (fixture ID exempts it)

Run with NLP layer disabled (safe in CI without the model):
    NLP_PII_GUARD_ENABLED=0 RUNNING_TESTS=1 DATA_PRIVACY_MODE=beta uv run pytest tests/test_privacy_guard_nlp.py -v

Run with NLP layer enabled (requires en_core_web_sm):
    NLP_PII_GUARD_ENABLED=1 RUNNING_TESTS=1 DATA_PRIVACY_MODE=dogfood uv run pytest tests/test_privacy_guard_nlp.py -v
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock


# ===========================================================================
# HELPERS
# ===========================================================================

def _reset_privacy_guard_nlp_state():
    """Reset the lazy-load state so tests don't share NLP model cache."""
    import src.security.privacy_guard as pg
    pg._nlp_model = None
    pg._nlp_load_attempted = False


# ===========================================================================
# PART 1: NLP disabled via env var — always safe (no model needed)
# ===========================================================================

class TestNLPGuardDisabled:
    """When NLP_PII_GUARD_ENABLED=0, the guard falls back to regex-only mode."""

    def test_disabled_via_env_does_not_crash(self):
        """NLP disabled → _nlp_scan_for_person_entities returns empty list."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()
        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "0"}):
            result = pg._nlp_scan_for_person_entities("My name is Priya Sharma")
        assert result == [], f"Expected empty list when NLP disabled, got: {result}"

    def test_disabled_check_trip_data_still_uses_regex(self):
        """Regex layer (Layer 1) still works when NLP is disabled."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()
        with patch.dict(os.environ, {
            "NLP_PII_GUARD_ENABLED": "0",
            "DATA_PRIVACY_MODE": "dogfood",
        }):
            trip_with_email = {
                "raw_input": {
                    "fixture_id": None,
                    "raw_note": "Contact: priya.sharma@example.com for booking."
                }
            }
            with pytest.raises(pg.PrivacyGuardError) as exc_info:
                pg.check_trip_data(trip_with_email)
            assert "email" in str(exc_info.value).lower(), (
                f"Should catch email via regex Layer 1. Got: {exc_info.value}"
            )

    def test_disabled_env_values(self):
        """All falsy env var values correctly disable NLP guard."""
        import src.security.privacy_guard as pg
        for falsy in ("0", "false", "no", "off", "False", "NO"):
            with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": falsy}):
                assert not pg._is_nlp_guard_enabled(), (
                    f"Expected NLP disabled for env value '{falsy}'"
                )

    def test_enabled_env_values(self):
        """Truthy env var values correctly enable NLP guard."""
        import src.security.privacy_guard as pg
        for truthy in ("1", "true", "yes", "True", "YES", ""):
            with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": truthy}):
                assert pg._is_nlp_guard_enabled(), (
                    f"Expected NLP enabled for env value '{truthy}'"
                )


# ===========================================================================
# PART 2: SpaCy not installed — graceful fail-open
# ===========================================================================

class TestNLPSpacyNotInstalled:
    """When spacy is not installed, guard fails open (no crash, no false block)."""

    def test_spacy_import_error_falls_open(self):
        """ImportError from spacy → _nlp_scan returns [] without crashing."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "1"}):
            # Mock spacy as not importable
            with patch.dict(sys.modules, {"spacy": None}):
                result = pg._nlp_scan_for_person_entities("My name is Priya Sharma")
        # After failed import, model is None → returns []
        assert result == [], f"Should fail-open on spacy ImportError. Got: {result}"

    def test_spacy_os_error_falls_open(self):
        """OSError (model not found) → _nlp_scan returns [] without crashing."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        mock_spacy = MagicMock()
        mock_spacy.load.side_effect = OSError("Model not found")

        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "1"}):
            with patch.dict(sys.modules, {"spacy": mock_spacy}):
                result = pg._nlp_scan_for_person_entities("My name is Priya Sharma")
        assert result == [], f"Should fail-open on spacy OSError. Got: {result}"


# ===========================================================================
# PART 3: SpaCy available — PERSON entity detection
# ===========================================================================

class TestNLPPersonDetection:
    """
    Tests that use a mocked SpaCy model (no real model download needed).

    Uses a mock that mimics spacy.load(model).pipe() behavior to validate
    that the privacy_guard correctly calls spacy and processes results.
    """

    def _make_mock_nlp(self, entities: list[tuple[str, str]]):
        """Create a mock spacy nlp() object that returns given entities."""
        def mock_ent(text_val: str, label_val: str):
            return MagicMock(text=text_val, label_=label_val)

        mock_doc = MagicMock()
        mock_doc.ents = [mock_ent(ent_text, ent_label) for ent_text, ent_label in entities]

        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc
        return mock_nlp

    def test_person_entity_detected_in_freeform_note(self):
        """PERSON entity detected by _nlp_scan_for_person_entities via mock.

        Note: We test the NLP function directly rather than via _is_likely_real_user_data
        because 'note' is in _FREEFORM_FIELD_NAMES, so Layer 1 catches it first.
        To isolate Layer 2, we test the NLP scan function directly.
        """
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        mock_nlp = self._make_mock_nlp([("Priya Sharma", "PERSON")])

        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "1"}):
            with patch.object(pg, "_get_nlp_model", return_value=mock_nlp):
                result = pg._nlp_scan_for_person_entities(
                    "Hi my name is Priya Sharma and I want to book a trip."
                )

        assert "Priya Sharma" in result, f"Should detect PERSON entity. Got: {result}"


    def test_no_person_entity_in_clean_travel_text(self):
        """Clean travel copy with no PERSON entities → NLP returns empty list.

        Tests _nlp_scan_for_person_entities directly to isolate Layer 2
        from Layer 1 freeform detection.
        """
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        mock_nlp = self._make_mock_nlp([])  # No entities found

        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "1"}):
            with patch.object(pg, "_get_nlp_model", return_value=mock_nlp):
                result = pg._nlp_scan_for_person_entities(
                    "Looking for a luxury safari in Kenya for 10 nights."
                )

        assert result == [], f"Clean travel text should return no persons. Got: {result}"


    def test_gpe_and_org_entities_not_blocked(self):
        """GPE (location) and ORG entities are not included — only PERSON is PII.

        Tests _nlp_scan_for_person_entities directly to isolate Layer 2.
        """
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        # SpaCy finds Taj Mahal Hotels (ORG) and Maldives (GPE), but no PERSON
        mock_nlp = self._make_mock_nlp([
            ("Taj Mahal Hotels", "ORG"),
            ("Maldives", "GPE"),
        ])

        with patch.dict(os.environ, {"NLP_PII_GUARD_ENABLED": "1"}):
            with patch.object(pg, "_get_nlp_model", return_value=mock_nlp):
                result = pg._nlp_scan_for_person_entities(
                    "Book Taj Mahal Hotels in Maldives for 7 nights."
                )

        assert result == [], f"ORG/GPE entities should not be returned. Got: {result}"

    def test_fixture_data_with_person_name_not_blocked(self):
        """Known fixture data is exempt even if SpaCy finds a PERSON entity."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        mock_nlp = self._make_mock_nlp([("John Doe", "PERSON")])

        with patch.dict(os.environ, {
            "NLP_PII_GUARD_ENABLED": "1",
            "DATA_PRIVACY_MODE": "dogfood",
        }):
            with patch.object(pg, "_get_nlp_model", return_value=mock_nlp):
                fixture_trip = {
                    "raw_input": {
                        "fixture_id": "fixture_001",
                        "raw_note": "Contact: John Doe",
                    },
                    "source": "fixture",
                }
                reason = pg._is_likely_real_user_data(fixture_trip)

        # Fixture is exempt from freeform/NLP checks (fixture_id present → bypass)
        assert reason is None, (
            f"Fixture data should be exempt from NLP block. Got: {reason}"
        )

    def test_nlp_exception_during_scan_falls_open(self):
        """If SpaCy raises during scan (e.g. OOM), guard fails open (no block)."""
        import src.security.privacy_guard as pg
        _reset_privacy_guard_nlp_state()

        mock_nlp = MagicMock()
        mock_nlp.side_effect = RuntimeError("SpaCy OOM")

        with patch.dict(os.environ, {
            "NLP_PII_GUARD_ENABLED": "1",
            "DATA_PRIVACY_MODE": "dogfood",
        }):
            with patch.object(pg, "_get_nlp_model", return_value=mock_nlp):
                result = pg._nlp_scan_for_person_entities("My name is Priya")
        # Exception during scan → returns empty list (fail-open)
        assert result == [], f"Exception during scan should fail-open. Got: {result}"
