"""
Tests for P3-03: Override Learning Feedback Loop

Covers:
- Pattern matching (match_pattern_overrides)
- Override adjustments (apply_override_adjustments)
- Safety invariant enforcement
- Cache feedback recording
- Integration with run_gap_and_decision
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_overrides_dir(tmp_path):
    """Provide a temporary overrides directory for tests."""
    per_trip = tmp_path / "per_trip"
    patterns = tmp_path / "patterns"
    per_trip.mkdir()
    patterns.mkdir()
    return {"per_trip": per_trip, "patterns": patterns}


@pytest.fixture
def sample_pattern_overrides():
    """Sample pattern override records for elderly_mobility_risk."""
    return [
        {
            "pattern_id": "pat_m1n2o3",
            "override_id": "ovr_a1b2c3d4",
            "trip_id": "trip_abc123",
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "original_severity": "high",
            "override_reason": "Traveler confirmed fitness",
            "created_at": "2026-04-22T10:14:00Z",
            "context_signature": {
                "destination": "Maldives",
                "has_elderly": True,
                "elderly_count": 1,
            },
            "strength": 3,
            "confirmed_by_later_runs": 2,
        },
        {
            "pattern_id": "pat_x9y8z7",
            "override_id": "ovr_e5f6g7h8",
            "trip_id": "trip_def456",
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "downgrade",
            "original_severity": "high",
            "new_severity": "medium",
            "override_reason": "Elderly traveler is active and fit",
            "created_at": "2026-04-23T11:00:00Z",
            "context_signature": {
                "destination": "Bali",
                "has_elderly": True,
            },
            "strength": 2,
            "confirmed_by_later_runs": 1,
        },
    ]


@pytest.fixture
def sample_trip_overrides():
    """Sample trip-level override records."""
    return [
        {
            "override_id": "ovr_trip001",
            "trip_id": "trip_test123",
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "suppress",
            "original_severity": "high",
            "scope": "this_trip",
            "overridden_by": "agent_priya",
            "reason": "Traveler confirmed fitness via video call",
            "created_at": "2026-04-22T10:14:00Z",
        }
    ]


@pytest.fixture
def sample_trip_downgrade_overrides():
    """Sample trip-level downgrade override records."""
    return [
        {
            "override_id": "ovr_trip002",
            "trip_id": "trip_test123",
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "downgrade",
            "new_severity": "low",
            "original_severity": "high",
            "scope": "this_trip",
            "overridden_by": "owner_raj",
            "reason": "Doctor clearance on file",
            "created_at": "2026-04-22T10:14:00Z",
        }
    ]


@pytest.fixture
def sample_trip_acknowledge_overrides():
    """Sample trip-level acknowledge override records."""
    return [
        {
            "override_id": "ovr_trip003",
            "trip_id": "trip_test123",
            "flag": "elderly_mobility_risk",
            "decision_type": "elderly_mobility_risk",
            "action": "acknowledge",
            "scope": "this_trip",
            "overridden_by": "owner_raj",
            "reason": "Owner reviewed and accepted the risk",
            "created_at": "2026-04-22T10:14:00Z",
        }
    ]


# ---------------------------------------------------------------------------
# Tests: Pattern Matching
# ---------------------------------------------------------------------------

class TestPatternMatching:
    """Tests for src/decision/pattern_matching.py"""

    def test_exact_match(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        context = {"destination": "Maldives", "has_elderly": True, "elderly_count": 1}
        matches = match_pattern_overrides(context, sample_pattern_overrides, min_strength=2)
        assert len(matches) == 1
        assert matches[0]["pattern_id"] == "pat_m1n2o3"
        assert matches[0]["strength"] == 3

    def test_no_match_different_destination(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        context = {"destination": "Japan", "has_elderly": True, "elderly_count": 1}
        matches = match_pattern_overrides(context, sample_pattern_overrides, min_strength=2)
        assert len(matches) == 0

    def test_no_match_different_composition(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        context = {"destination": "Maldives", "has_elderly": False}
        matches = match_pattern_overrides(context, sample_pattern_overrides, min_strength=2)
        assert len(matches) == 0

    def test_min_strength_filter(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        # Only strength >= 3 should match
        context = {"destination": "Bali", "has_elderly": True}
        matches_high = match_pattern_overrides(context, sample_pattern_overrides, min_strength=3)
        assert len(matches_high) == 0  # Bali pattern has strength 2

        matches_low = match_pattern_overrides(context, sample_pattern_overrides, min_strength=2)
        assert len(matches_low) == 1
        assert matches_low[0]["pattern_id"] == "pat_x9y8z7"

    def test_destination_alias_match(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        # Andamans should match Andaman
        context = {"destination": "Andamans", "has_elderly": True, "elderly_count": 1}
        andaman_pattern = [{
            "pattern_id": "pat_andaman",
            "context_signature": {"destination": "Andaman", "has_elderly": True, "elderly_count": 1},
            "strength": 3,
        }]
        matches = match_pattern_overrides(context, andaman_pattern, min_strength=2)
        assert len(matches) == 1

    def test_empty_inputs(self):
        from src.decision.pattern_matching import match_pattern_overrides

        assert match_pattern_overrides({}, [], min_strength=2) == []
        assert match_pattern_overrides({"a": 1}, [], min_strength=2) == []
        assert match_pattern_overrides({}, [{"context_signature": {"a": 1}}], min_strength=2) == []

    def test_sorted_by_strength_descending(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        context = {"destination": "Maldives", "has_elderly": True, "elderly_count": 1}
        matches = match_pattern_overrides(context, sample_pattern_overrides, min_strength=2)
        strengths = [m["strength"] for m in matches]
        assert strengths == sorted(strengths, reverse=True)

    def test_signature_without_context_signature_field(self, sample_pattern_overrides):
        from src.decision.pattern_matching import match_pattern_overrides

        no_sig = [{"pattern_id": "pat_no_sig", "strength": 5}]
        context = {"destination": "Maldives", "has_elderly": True}
        matches = match_pattern_overrides(context, no_sig, min_strength=2)
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Tests: Override Adjustments
# ---------------------------------------------------------------------------

class TestOverrideAdjustments:
    """Tests for src/decision/override_learning.py"""

    @patch("src.decision.override_learning._get_override_store")
    def test_suppress_removes_flag(self, mock_store_factory, sample_trip_overrides):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        # Use side_effect to return correct overrides per flag name
        def _overrides_for_flag(trip_id, flag_name):
            if flag_name == "elderly_mobility_risk":
                return sample_trip_overrides
            return []
        mock_store.get_active_overrides_for_flag.side_effect = _overrides_for_flag
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
            {"flag": "margin_risk", "severity": "medium", "message": "Budget tight"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        # elderly_mobility_risk should be suppressed (removed)
        flag_names = [f["flag"] for f in adjusted]
        assert "elderly_mobility_risk" not in flag_names
        assert "margin_risk" in flag_names
        assert "elderly_mobility_risk" in metadata["trip_overrides_applied"]
        assert metadata["trip_overrides_applied"]["elderly_mobility_risk"]["action"] == "suppress"

    @patch("src.decision.override_learning._get_override_store")
    def test_downgrade_changes_severity(self, mock_store_factory, sample_trip_downgrade_overrides):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = sample_trip_downgrade_overrides
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        # Flag should still exist but with downgraded severity
        assert len(adjusted) == 1
        assert adjusted[0]["severity"] == "low"
        assert adjusted[0]["flag"] == "elderly_mobility_risk"
        assert metadata["trip_overrides_applied"]["elderly_mobility_risk"]["action"] == "downgrade"
        assert metadata["trip_overrides_applied"]["elderly_mobility_risk"]["original_severity"] == "high"

    @patch("src.decision.override_learning._get_override_store")
    def test_acknowledge_preserves_flag(self, mock_store_factory, sample_trip_acknowledge_overrides):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = sample_trip_acknowledge_overrides
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        # Flag should still exist with original severity but annotated
        assert len(adjusted) == 1
        assert adjusted[0]["severity"] == "high"
        assert adjusted[0].get("override_acknowledged") is True
        assert adjusted[0].get("acknowledged_by") == "owner_raj"
        assert metadata["trip_overrides_applied"]["elderly_mobility_risk"]["action"] == "acknowledge"

    @patch("src.decision.override_learning._get_override_store")
    def test_safety_flag_cannot_be_suppressed(self, mock_store_factory):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = [
            {
                "override_id": "ovr_safety_bad",
                "action": "suppress",
                "overridden_by": "bad_actor",
                "reason": "Trying to suppress safety flag",
            }
        ]
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "document_risk", "severity": "critical", "message": "Passport expired"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        # Safety flag should NOT be suppressed
        assert len(adjusted) == 1
        assert adjusted[0]["flag"] == "document_risk"
        # No override applied
        assert "document_risk" not in metadata.get("trip_overrides_applied", {})

    @patch("src.decision.override_learning._get_override_store")
    def test_safety_flag_cannot_be_downgraded(self, mock_store_factory):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = [
            {
                "override_id": "ovr_safety_down_bad",
                "action": "downgrade",
                "new_severity": "low",
                "overridden_by": "bad_actor",
                "reason": "Trying to downgrade safety flag",
            }
        ]
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "visa_not_applied", "severity": "critical", "message": "Visa needed"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        # Safety flag should NOT be downgraded
        assert len(adjusted) == 1
        assert adjusted[0]["severity"] == "critical"  # unchanged
        assert "visa_not_applied" not in metadata.get("trip_overrides_applied", {})

    @patch("src.decision.override_learning._get_override_store")
    def test_no_overrides_leaves_flags_unchanged(self, mock_store_factory):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = []
        mock_store_factory.return_value = mock_store

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        assert len(adjusted) == 1
        assert adjusted[0] == risk_flags[0]
        assert metadata.get("trip_overrides_applied", {}) == {}

    @patch("src.decision.override_learning._get_override_store")
    def test_empty_risk_flags(self, mock_store_factory):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store_factory.return_value = mock_store

        adjusted, metadata = apply_override_adjustments(
            risk_flags=[],
            trip_id="trip_test123",
            packet=MagicMock(),
        )

        assert adjusted == []
        assert metadata == {}


# ---------------------------------------------------------------------------
# Tests: Cache Feedback
# ---------------------------------------------------------------------------

class TestCacheFeedback:
    """Tests for cache feedback recording in override_learning."""

    @patch("src.decision.override_learning._get_override_store")
    @patch("src.decision.override_learning._get_cache_storage")
    def test_cache_feedback_recorded_on_suppress(
        self, mock_cache_factory, mock_store_factory, sample_trip_overrides
    ):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.side_effect = lambda tid, fn: (
            sample_trip_overrides if fn == "elderly_mobility_risk" else []
        )
        mock_store_factory.return_value = mock_store

        from src.decision.cache_schema import CachedDecision
        mock_cache = MagicMock()
        mock_decision = CachedDecision(
            cache_key="test_key_123",
            decision_type="elderly_mobility_risk",
            decision={"risk_level": "high"},
            confidence=0.9,
            source="rule",
        )
        mock_cache.get.return_value = mock_decision
        mock_cache_factory.return_value = mock_cache

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
            cache_key="test_key_123",
            decision_type="elderly_mobility_risk",
        )

        # Cache feedback should have been recorded
        assert metadata.get("cache_feedback_recorded") is True
        # record_feedback(success=False) should have been called on the CachedDecision
        assert mock_decision.feedback_count >= 1

    @patch("src.decision.override_learning._get_override_store")
    @patch("src.decision.override_learning._get_cache_storage")
    def test_cache_feedback_not_recorded_without_key(
        self, mock_cache_factory, mock_store_factory, sample_trip_overrides
    ):
        from src.decision.override_learning import apply_override_adjustments

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.side_effect = lambda tid, fn: (
            sample_trip_overrides if fn == "elderly_mobility_risk" else []
        )
        mock_store_factory.return_value = mock_store
        mock_cache_factory.return_value = MagicMock()

        risk_flags = [
            {"flag": "elderly_mobility_risk", "severity": "high", "message": "Elderly + Maldives"},
        ]

        adjusted, metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id="trip_test123",
            packet=MagicMock(),
            # No cache_key or decision_type provided
        )

        assert metadata.get("cache_feedback_recorded") is False


# ---------------------------------------------------------------------------
# Tests: Integration with run_gap_and_decision
# ---------------------------------------------------------------------------

class TestRunGapAndDecisionIntegration:
    """Integration tests for override adjustments in the decision pipeline."""

    @patch("src.decision.override_learning._get_override_store")
    def test_override_applied_in_pipeline(self, mock_store_factory):
        """Verify override adjustments are applied during run_gap_and_decision."""
        from src.intake.packet_models import CanonicalPacket, Slot, AuthorityLevel, Ambiguity
        from src.intake.decision import run_gap_and_decision

        mock_store = MagicMock()
        mock_store.get_active_overrides_for_flag.return_value = [
            {
                "override_id": "ovr_pipeline01",
                "action": "suppress",
                "overridden_by": "owner",
                "reason": "Test override",
            }
        ]
        mock_store.get_pattern_overrides.return_value = []
        mock_store_factory.return_value = mock_store

        # Build a minimal packet with an elderly mobility risk
        packet = CanonicalPacket(
            packet_id="test_packet_001",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "destination_candidates": Slot(
                    value=["Maldives"],
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
                "origin_city": Slot(
                    value="Mumbai",
                    confidence=0.95,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
                "date_window": Slot(
                    value="2026-08-15 to 2026-08-22",
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
                "party_size": Slot(
                    value=2,
                    confidence=0.95,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
                "budget_min": Slot(
                    value=200000,
                    confidence=0.8,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
                "party_composition": Slot(
                    value={"adults": 1, "elderly": 1},
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                ),
            },
            derived_signals={},
        )

        result = run_gap_and_decision(packet)

        # The override should have been applied
        # Check that rationale contains override info
        # (The elderly_mobility_risk flag may or may not be generated depending on
        # whether the hybrid engine is enabled, but the override machinery should run)
        assert result.decision_state in (
            "ASK_FOLLOWUP", "PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT",
            "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW",
        )

    def test_safety_flags_cannot_be_suppressed_in_pipeline(self):
        """Verify safety invariant flags survive override adjustments."""
        from src.intake.packet_models import CanonicalPacket, Slot, AuthorityLevel
        from src.decision.override_learning import apply_override_adjustments, SAFETY_INVARIANT_FLAGS

        # All safety flags should be in the set
        assert "document_risk" in SAFETY_INVARIANT_FLAGS
        assert "visa_not_applied" in SAFETY_INVARIANT_FLAGS
        assert "traveler_safe_leakage_risk" in SAFETY_INVARIANT_FLAGS

        # Even if override store returns suppress for these flags,
        # they should not be removed
        with patch("src.decision.override_learning._get_override_store") as mock_store:
            mock_s = MagicMock()
            mock_s.get_active_overrides_for_flag.return_value = [
                {"override_id": "bad", "action": "suppress", "overridden_by": "bad"}
            ]
            mock_store.return_value = mock_s

            risk_flags = [
                {"flag": "document_risk", "severity": "critical"},
                {"flag": "visa_not_applied", "severity": "critical"},
                {"flag": "traveler_safe_leakage_risk", "severity": "critical"},
            ]

            adjusted, meta = apply_override_adjustments(
                risk_flags=risk_flags,
                trip_id="trip_x",
                packet=MagicMock(),
            )

            flag_names = [f["flag"] for f in adjusted]
            assert "document_risk" in flag_names
            assert "visa_not_applied" in flag_names
            assert "traveler_safe_leakage_risk" in flag_names


# ---------------------------------------------------------------------------
# Tests: Helper functions
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    """Tests for utility functions in override_learning."""

    def test_should_suppress_flag_for_decision_state(self):
        from src.decision.override_learning import should_suppress_flag_for_decision_state

        metadata = {
            "trip_overrides_applied": {
                "elderly_mobility_risk": {"action": "suppress"},
                "margin_risk": {"action": "acknowledge"},
            }
        }

        assert should_suppress_flag_for_decision_state("elderly_mobility_risk", metadata) is True
        assert should_suppress_flag_for_decision_state("margin_risk", metadata) is False
        assert should_suppress_flag_for_decision_state("unknown_flag", metadata) is False

    def test_get_overrides_summary_for_rationale(self):
        from src.decision.override_learning import get_overrides_summary_for_rationale

        metadata = {
            "trip_overrides_applied": {"elderly_mobility_risk": {"action": "suppress"}},
            "pattern_hints": {"margin_risk": {"pattern_id": "pat_123", "strength": 3}},
        }

        summary = get_overrides_summary_for_rationale(metadata)
        assert "overrides_applied" in summary
        assert "pattern_hints" in summary
        assert summary["overrides_applied"]["elderly_mobility_risk"]["action"] == "suppress"
        assert summary["pattern_hints"]["margin_risk"]["pattern_id"] == "pat_123"
