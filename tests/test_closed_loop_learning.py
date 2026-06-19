"""
Tests for the closed-loop learning pipeline (P0).

Covers:
- learn_from_operator_override() entry point
- _extract_trip_context_signature()
- _enrich_pattern_with_context()
- _check_and_graduate()
- Rollout mode metadata
- Disabled learn_from_overrides path
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.decision.override_learning import (
    GRADUATION_THRESHOLD,
    ROLLOUT_MODE_DISABLED,
    ROLLOUT_MODE_GRADUATED,
    ROLLOUT_MODE_NONE,
    ROLLOUT_MODE_PATTERN_ENRICHED,
    _check_and_graduate,
    _extract_trip_context_signature,
    _enrich_pattern_with_context,
    learn_from_operator_override,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_trip_data() -> dict:
    """A trip with extracted packet data for context extraction."""
    return {
        "id": "trip_test001",
        "agency_id": "test-agency",
        "extracted": {
            "facts": {
                "destination_candidates": ["Bali, Indonesia"],
                "resolved_destination": "Bali",
                "party_composition": {"adults": 2, "elderly": 1, "toddler": 0},
                "party_size": 3,
                "duration_days": 10,
                "budget_min": 5000,
                "child_ages": [],
            },
            "derived_signals": {
                "domestic_or_international": "international",
                "urgency": "medium",
            },
        },
    }


@pytest.fixture
def sample_override_data() -> dict:
    """A typical operator override record."""
    return {
        "flag": "elderly_mobility_risk",
        "decision_type": "elderly_mobility_risk",
        "action": "suppress",
        "scope": "this_trip",
        "overridden_by": "owner@test.com",
        "reason": "Elderly traveler is experienced and capable",
    }


@pytest.fixture
def sample_pattern_override_data() -> dict:
    """An override with pattern scope."""
    return {
        "flag": "elderly_mobility_risk",
        "decision_type": "elderly_mobility_risk",
        "action": "suppress",
        "scope": "pattern",
        "overridden_by": "owner@test.com",
        "reason": "Pattern: elderly travelers to Bali are always capable",
    }


# ---------------------------------------------------------------------------
# _extract_trip_context_signature
# ---------------------------------------------------------------------------

class TestExtractTripContextSignature:
    def test_extracts_destination(self, sample_trip_data, monkeypatch):
        mock_trip_store = MagicMock()
        mock_trip_store.get_trip = MagicMock(return_value=sample_trip_data)
        # Patch the lazy import inside _extract_trip_context_signature
        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            mock_trip_store.get_trip,
        )
        result = _extract_trip_context_signature("trip_test001", "elderly_mobility_risk")

        assert result is not None
        assert result["destination"] == "Bali, Indonesia"
        assert result["has_elderly"] is True
        assert result["elderly_count"] == 1
        assert result["has_toddler"] is False
        assert result["party_size"] == 3
        assert result["duration_days"] == 10

    def test_returns_none_for_missing_trip(self, monkeypatch):
        mock_trip_store = MagicMock()
        mock_trip_store.get_trip = MagicMock(return_value=None)
        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            mock_trip_store.get_trip,
        )
        result = _extract_trip_context_signature("nonexistent_trip", "budget_feasibility")
        assert result is None

    def test_returns_none_for_empty_extracted(self, monkeypatch):
        mock_trip_store = MagicMock()
        mock_trip_store.get_trip = MagicMock(return_value={"id": "trip_empty", "extracted": {}})
        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            mock_trip_store.get_trip,
        )
        result = _extract_trip_context_signature("trip_empty", "budget_feasibility")
        assert result is None

    def test_extracts_intl_domestic(self, sample_trip_data, monkeypatch):
        mock_trip_store = MagicMock()
        mock_trip_store.get_trip = MagicMock(return_value=sample_trip_data)
        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            mock_trip_store.get_trip,
        )
        result = _extract_trip_context_signature("trip_test001", "visa_timeline_risk")
        assert result is not None
        assert result["domestic_or_intl"] == "international"
        assert result["urgency"] == "medium"


# ---------------------------------------------------------------------------
# _enrich_pattern_with_context
# ---------------------------------------------------------------------------

class TestEnrichPatternWithContext:
    def test_creates_new_pattern_when_no_match(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []

        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "scope": "pattern",
            "overridden_by": "owner@test.com",
            "reason": "Test",
        }
        context = {"destination": "Bali", "has_elderly": True}

        result = _enrich_pattern_with_context(mock_store, override_data, context, "elderly_mobility_risk")
        assert result is True
        mock_store._add_pattern_override.assert_called_once()
        created = mock_store._add_pattern_override.call_args[0][0]
        assert created["context_signature"] == context
        assert created["strength"] == 1
        assert created["pattern_id"].startswith("pat_")
        # Verify no trip-specific fields leaked
        assert "trip_id" not in created
        assert "override_id" not in created

    def test_strengthens_existing_matching_pattern(self, monkeypatch):
        existing_pattern = {
            "pattern_id": "pat_existing",
            "strength": 2,
            "confirmed_by_later_runs": 1,
            "context_signature": {"destination": "Bali", "has_elderly": True},
            "action": "suppress",
        }
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = [existing_pattern]
        mock_store.OVERRIDES_PATTERNS_DIR = Path(tempfile.mkdtemp())

        override_data = {
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "scope": "pattern",
            "overridden_by": "owner@test.com",
            "reason": "Test",
        }
        context = {"destination": "Bali", "has_elderly": True}

        result = _enrich_pattern_with_context(mock_store, override_data, context, "elderly_mobility_risk")
        assert result is True
        assert existing_pattern["strength"] == 3
        assert existing_pattern["confirmed_by_later_runs"] == 2
        mock_store._add_pattern_override.assert_not_called()


# ---------------------------------------------------------------------------
# _check_and_graduate
# ---------------------------------------------------------------------------

class TestCheckAndGraduate:
    def test_returns_none_below_threshold(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []

        # Only 1 override in per-trip files (below threshold of 3)
        overrides_dir = Path(tempfile.mkdtemp())
        trip_file = overrides_dir / "trip_other.jsonl"
        with open(trip_file, "w") as f:
            json.dump({
                "flag": "elderly_mobility_risk",
                "decision_type": "elderly_mobility_risk",
                "trip_id": "trip_other",
                "action": "suppress",
            }, f)

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", overrides_dir):
            result = _check_and_graduate(
                "trip_test001", "elderly_mobility_risk", "elderly_mobility_risk",
                {"destination": "Bali"}, override_store=mock_store, graduation_threshold=3,
            )
        assert result is None

    def test_graduates_at_threshold(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []

        overrides_dir = Path(tempfile.mkdtemp())
        # Create 2 overrides from different trips (threshold - 1)
        for i in range(2):
            trip_file = overrides_dir / f"trip_other_{i}.jsonl"
            with open(trip_file, "w") as f:
                json.dump({
                    "flag": "elderly_mobility_risk",
                    "decision_type": "elderly_mobility_risk",
                    "trip_id": f"trip_other_{i}",
                    "action": "suppress",
                }, f)

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", overrides_dir):
            result = _check_and_graduate(
                "trip_test001", "elderly_mobility_risk", "elderly_mobility_risk",
                {"destination": "Bali"}, override_store=mock_store, graduation_threshold=3,
            )

        assert result is not None
        assert result["graduated_from"] == "trip_level"
        assert result["strength"] == 3
        assert result["action"] == "suppress"
        mock_store._add_pattern_override.assert_called_once()

    def test_does_not_graduate_when_pattern_exists(self, monkeypatch):
        existing_pattern = {
            "pattern_id": "pat_existing",
            "context_signature": {"destination": "Bali"},
        }
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = [existing_pattern]

        overrides_dir = Path(tempfile.mkdtemp())
        for i in range(3):
            trip_file = overrides_dir / f"trip_other_{i}.jsonl"
            with open(trip_file, "w") as f:
                json.dump({
                    "flag": "elderly_mobility_risk",
                    "decision_type": "elderly_mobility_risk",
                    "trip_id": f"trip_other_{i}",
                    "action": "suppress",
                }, f)

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", overrides_dir):
            result = _check_and_graduate(
                "trip_test001", "elderly_mobility_risk", "elderly_mobility_risk",
                {"destination": "Bali"}, override_store=mock_store, graduation_threshold=3,
            )
        assert result is None

    def test_inherits_dominant_action(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []

        overrides_dir = Path(tempfile.mkdtemp())
        # 2 downgrade + 1 suppress → dominant is downgrade
        actions = ["downgrade", "downgrade", "suppress"]
        for i, act in enumerate(actions):
            trip_file = overrides_dir / f"trip_other_{i}.jsonl"
            with open(trip_file, "w") as f:
                json.dump({
                    "flag": "elderly_mobility_risk",
                    "decision_type": "elderly_mobility_risk",
                    "trip_id": f"trip_other_{i}",
                    "action": act,
                }, f)

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", overrides_dir):
            result = _check_and_graduate(
                "trip_test001", "elderly_mobility_risk", "elderly_mobility_risk",
                {"destination": "Bali"}, override_store=mock_store, graduation_threshold=3,
            )

        assert result is not None
        assert result["action"] == "downgrade"


# ---------------------------------------------------------------------------
# learn_from_operator_override
# ---------------------------------------------------------------------------

class TestLearnFromOperatorOverride:
    def test_disabled_returns_disabled_mode(self):
        result = learn_from_operator_override(
            "trip_test001", {"flag": "elderly_mobility_risk"}, learn_from_overrides_enabled=False,
        )
        assert result["rollout_mode"] == ROLLOUT_MODE_DISABLED
        assert result["mutations_applied"] == []

    def test_this_trip_scope_no_pattern_enrichment(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []
        mock_trip = {"id": "trip_test001", "extracted": {"facts": {"destination_candidates": ["Bali"]}}}
        empty_overrides_dir = Path(tempfile.mkdtemp())

        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            MagicMock(return_value=mock_trip),
        )
        monkeypatch.setattr(
            "src.decision.override_learning._get_override_store",
            lambda: mock_store,
        )

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", empty_overrides_dir):
            result = learn_from_operator_override(
                "trip_test001",
                {"flag": "elderly_mobility_risk", "decision_type": "elderly_mobility_risk",
                 "action": "suppress", "scope": "this_trip", "overridden_by": "owner@test.com",
                 "reason": "Test"},
                learn_from_overrides_enabled=True,
            )

        assert result["rollout_mode"] == ROLLOUT_MODE_NONE
        assert "pattern_context_enriched" not in result["mutations_applied"]

    def test_pattern_scope_enriches_context(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []
        mock_trip = {
            "id": "trip_test001",
            "extracted": {"facts": {"destination_candidates": ["Bali"]}},
        }
        empty_overrides_dir = Path(tempfile.mkdtemp())

        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            MagicMock(return_value=mock_trip),
        )
        monkeypatch.setattr(
            "src.decision.override_learning._get_override_store",
            lambda: mock_store,
        )

        with patch("spine_api.persistence.OVERRIDES_PER_TRIP_DIR", empty_overrides_dir):
            result = learn_from_operator_override(
                "trip_test001",
                {"flag": "elderly_mobility_risk", "decision_type": "elderly_mobility_risk",
                 "action": "suppress", "scope": "pattern", "overridden_by": "owner@test.com",
                 "reason": "Test"},
                learn_from_overrides_enabled=True,
            )

        assert "pattern_context_enriched" in result["mutations_applied"]
        assert result["context_signature"] is not None
        assert result["context_signature"]["destination"] == "Bali"
        mock_store._add_pattern_override.assert_called_once()

    def test_returns_structured_metadata(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.get_pattern_overrides.return_value = []

        monkeypatch.setattr(
            "spine_api.persistence.TripStore.get_trip",
            MagicMock(return_value=None),
        )
        monkeypatch.setattr(
            "src.decision.override_learning._get_override_store",
            lambda: mock_store,
        )

        result = learn_from_operator_override(
            "trip_test001",
            {"flag": "elderly_mobility_risk", "action": "suppress", "scope": "this_trip",
             "overridden_by": "owner@test.com", "reason": "Test"},
            learn_from_overrides_enabled=True,
        )

        assert "rollout_mode" in result
        assert "mutations_applied" in result
        assert "context_signature" in result
        assert "graduation_created" in result
        assert "cache_invalidated" in result
        assert isinstance(result["mutations_applied"], list)
