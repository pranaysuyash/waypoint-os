"""
Tests for src/security/privacy_guard.py.

Covers:
- Fixture data passes in dogfood mode
- Email detected -> blocked
- Phone detected -> blocked
- Freeform text -> blocked
- Medical/health keywords -> blocked
- Default mode is dogfood
- Empty non-fixture trip is allowed (no PII)
"""

import os
import json
import pytest

from spine_api.persistence import TEST_AGENCY_ID

from src.security.privacy_guard import (
    check_trip_data,
    PrivacyGuardError,
    is_dogfood_mode,
    _is_known_fixture,
    _has_email,
    _has_phone,
    _has_medical_indicator,
    _has_freeform_user_input,
    _data_privacy_mode,
)


# =============================================================================
# Fixture: synthetic trip data (known patterns)
# =============================================================================

def _make_fixture_trip() -> dict:
    return {
        "raw_input": {
            "fixture_id": "clean_family_booking",
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "execution_ms": 87.5,
        },
        "source": "test_fixture",
        "status": "new",
    }


def _make_seed_trip() -> dict:
    return {
        "raw_input": {
            "fixture_id": None,
            "stage": "discovery",
        },
        "source": "seed_scenario",
        "status": "new",
    }


def _make_real_trip() -> dict:
    return {
        "raw_input": {
            "stage": "discovery",
            "operating_mode": "normal_intake",
        },
        "source": "spine_api",
        "status": "new",
    }


# =============================================================================
# Dogfood mode checks
# =============================================================================


class TestFixtureDataAllowed:
    """Known fixtures must pass the guard."""

    def test_fixture_id_in_raw_input(self):
        trip = _make_fixture_trip()
        check_trip_data(trip)

    def test_seed_scenario_source(self):
        trip = _make_seed_trip()
        check_trip_data(trip)

    def test_fixture_with_flexible_dates(self):
        trip = {
            "raw_input": {"fixture_id": "vague_lead"},
            "source": "fixture",
        }
        check_trip_data(trip)

    def test_fixture_with_budget_and_party(self):
        trip = {
            "raw_input": {"fixture_id": "dreamer_budget_vs_luxury"},
            "extracted": {
                "facts": {
                    "party_size": {"value": 4, "authority_level": "explicit_owner"},
                    "budget_min": {"value": "150000", "authority_level": "explicit_owner"},
                }
            },
            "source": "test_fixture",
        }
        check_trip_data(trip)


class TestRealUserDataBlocked:
    """Non-fixture trips with human-like data must be blocked."""

    def test_email_in_raw_note(self):
        trip = {
            "raw_note": "Contact me at traveler@example.com for details",
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)
        assert "email" in str(exc.value).lower()

    def test_email_in_freeform_text(self):
        trip = {
            "raw_input": {
                "text": "My email is john.doe@email.com",
            },
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_email_in_extracted_facts(self):
        trip = {
            "extracted": {
                "facts": {
                    "contact_email": {
                        "value": "contact@traveler.com",
                        "authority_level": "explicit_owner",
                    }
                }
            },
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_phone_in_raw_note(self):
        trip = {
            "raw_note": "Call me at +91 98765 43210",
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_phone_in_freeform(self):
        trip = {
            "raw_input": {
                "freeform_text": "My number is 9876543210",
            },
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_freeform_notes_field(self):
        trip = {
            "notes": "This is a long freeform note from the user about their special needs and preferences for the trip",
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_medical_keyword_in_raw_note(self):
        trip = {
            "raw_note": "My father is diabetic and needs wheelchair access",
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_medical_keyword_in_freeform_text(self):
        trip = {
            "raw_input": {
                "text": "We have a child with severe allergies and asthma",
            },
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)

    def test_long_freeform_user_note(self):
        trip = {
            "raw_input": {
                "content": "This is a very long message from the user describing their entire travel plan, family composition, dietary restrictions, and medical conditions that we need to be aware of before booking anything",
            },
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            check_trip_data(trip)


class TestBenignDataAllowed:
    """Structured data without freeform user input should be allowed."""

    def test_empty_non_fixture_trip(self):
        trip = {"source": "spine_api"}
        check_trip_data(trip)

    def test_real_trip_no_fixture_id(self):
        trip = _make_real_trip()
        check_trip_data(trip)

    def test_structured_trip_with_fields(self):
        trip = {
            "source": "spine_api",
            "extracted": {
                "facts": {
                    "party_size": {"value": 4},
                    "destination": {"value": "Bali"},
                }
            },
        }
        check_trip_data(trip)

    def test_short_notes_ignored(self):
        trip = {"notes": "Short"}
        check_trip_data(trip)


class TestHeuristicDetails:
    """Unit tests for individual heuristic functions."""

    def test_email_detection_simple(self):
        data = {"text": "Reach me at user@domain.com"}
        assert _has_email(data) is not None

    def test_email_detection_none(self):
        data = {"text": "Just a normal message without any contact info"}
        assert _has_email(data) is None

    def test_phone_detection_indian(self):
        data = {"text": "Call +91 98765 43210"}
        assert _has_phone(data) is not None

    def test_phone_detection_none(self):
        data = {"text": "Some text without numbers"}
        assert _has_phone(data) is None

    def test_medical_detection_diabetic(self):
        data = {"text": "My father is diabetic"}
        assert _has_medical_indicator(data) is not None

    def test_medical_detection_none(self):
        data = {"text": "We want to go to Bali for vacation"}
        assert _has_medical_indicator(data) is None

    def test_fixture_detection_by_fixture_id(self):
        data = {"raw_input": {"fixture_id": "clean_family_booking"}}
        assert _is_known_fixture(data) is True

    def test_fixture_detection_by_source(self):
        data = {"source": "seed_scenario"}
        assert _is_known_fixture(data) is True

    def test_fixture_detection_unknown(self):
        data = {"source": "spine_api"}
        assert _is_known_fixture(data) is False

    def test_freeform_detection_content(self):
        data = {
            "raw_input": {"content": "Long user message " + "x" * 50}
        }
        assert _has_freeform_user_input(data) is not None

    def test_freeform_detection_short_ignored(self):
        data = {"notes": "Short"}
        assert _has_freeform_user_input(data) is None


class TestGuardOnTripStore:
    """Integration tests: guard actually blocks TripStore.save_trip."""

    def test_fixture_save_succeeds(self):
        from spine_api.persistence import TripStore

        trip = {
            "raw_input": {"fixture_id": "test_fixture", "execution_ms": 100},
            "source": "test",
            "agency_id": TEST_AGENCY_ID,
        }
        trip_id = TripStore.save_trip(trip)
        assert trip_id.startswith("trip_")

    def test_real_data_save_blocked(self):
        from spine_api.persistence import TripStore

        trip = {
            "raw_note": "Contact me at real.user@example.com",
            "source": "spine_api",
        }
        with pytest.raises(PrivacyGuardError) as exc:
            TripStore.save_trip(trip)
        assert "dogfood mode" in str(exc.value).lower()

    def test_tripstore_update_with_real_data_blocked(self):
        from spine_api.persistence import TripStore

        fixture_trip = {
            "raw_input": {"fixture_id": "update_test_fixture"},
            "source": "test",
            "agency_id": TEST_AGENCY_ID,
        }
        trip_id = TripStore.save_trip(fixture_trip)

        bad_update = {
            "raw_note": "My phone is +91 9876543210",
        }
        with pytest.raises(PrivacyGuardError):
            TripStore.update_trip(trip_id, bad_update)

    def test_mode_beta_allows(self, monkeypatch):
        monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
        from src.security.privacy_guard import check_trip_data

        trip = {"raw_note": "Real user data with email test@example.com"}
        # Should NOT raise in beta
        check_trip_data(trip)

    def test_mode_production_allows(self, monkeypatch):
        monkeypatch.setenv("DATA_PRIVACY_MODE", "production")
        from src.security.privacy_guard import check_trip_data

        trip = {"raw_note": "Real user data"}
        check_trip_data(trip)


class TestDefaultMode:
    """Default mode is dogfood."""

    def test_default_is_dogfood(self):
        assert is_dogfood_mode()


# =============================================================================
# agentNotes / agent_notes / owner_note freeform blocking
# =============================================================================

class TestAgentNotesBlocking:
    def test_agentNotes_camelcase_blocked_dogfood(self):
        trip = {
            "agentNotes": "This is a very long freeform note about the customer preferences for their upcoming trip",
            "source": "user_input",
        }
        with pytest.raises(PrivacyGuardError):
            check_trip_data(trip)

    def test_agent_notes_snakecase_blocked_dogfood(self):
        trip = {
            "agent_notes": "Detailed customer notes with sensitive travel preferences and itinerary",
            "source": "user_input",
        }
        with pytest.raises(PrivacyGuardError):
            check_trip_data(trip)

    def test_owner_note_blocked_dogfood(self):
        trip = {
            "owner_note": "Owner notes about customer preferences and special requirements",
            "source": "user_input",
        }
        with pytest.raises(PrivacyGuardError):
            check_trip_data(trip)

    def test_agentNotes_with_email_still_blocked(self):
        trip = {
            "agentNotes": "Customer email: john@example.com",
            "source": "user_input",
        }
        with pytest.raises(PrivacyGuardError):
            check_trip_data(trip)

    def test_agentNotes_with_phone_still_blocked(self):
        trip = {
            "agentNotes": "Call customer at 9876543210 for details",
            "source": "user_input",
        }
        with pytest.raises(PrivacyGuardError):
            check_trip_data(trip)

    def test_agentNotes_short_content_allowed(self):
        trip = {
            "agentNotes": "OK",
            "source": "user_input",
        }
        check_trip_data(trip)

    def test_agentNotes_fixture_allowed(self):
        trip = {
            "agentNotes": "This is a detailed customer note from the fixture",
            "raw_input": {"fixture_id": "clean_family_booking"},
        }
        check_trip_data(trip)

    def test_agentNotes_seed_scenario_allowed(self):
        trip = {
            "agentNotes": "Seeder agent note with scenarios",
            "source": "seed_scenario",
        }
        check_trip_data(trip)

    def test_agentNotes_beta_mode_allows(self, monkeypatch):
        monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
        from src.security.privacy_guard import check_trip_data
        trip = {
            "agentNotes": "Real user note with details about preferences",
            "source": "user_input",
        }
        check_trip_data(trip)
