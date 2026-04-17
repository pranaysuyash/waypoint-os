"""
tests.test_decision_rules — Unit tests for decision rules.

Tests for individual rule functions in the hybrid engine.
"""

import pytest
from src.intake.packet_models import CanonicalPacket, Slot
from src.decision.rules import (
    rule_elderly_mobility_risk,
    rule_toddler_pacing_risk,
    rule_budget_feasibility,
    rule_visa_timeline_risk,
    rule_composition_risk,
)


class TestElderlyMobilityRule:
    """Tests for elderly mobility risk rule."""

    def test_no_elderly_returns_none(self):
        """Test that rule returns None when no elderly travelers."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(value={"adults": 2}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Maldives"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_elderly_mobility_risk(packet)
        assert result is None

    def test_elderly_with_risky_destination(self):
        """Test high risk for elderly + Maldives."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(value={"elderly": 1}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Maldives"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_elderly_mobility_risk(packet)
        assert result is not None
        assert result["risk_level"] == "high"
        assert "Maldives" in result["reasoning"]
        assert len(result["recommendations"]) > 0

    def test_elderly_with_safe_destination(self):
        """Test low risk for elderly + Singapore."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(value={"elderly": 1}, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Singapore", authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_elderly_mobility_risk(packet)
        assert result is not None
        assert result["risk_level"] == "low"


class TestToddlerPacingRule:
    """Tests for toddler pacing risk rule."""

    def test_no_toddlers_returns_none(self):
        """Test that rule returns None when no toddlers."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(value={"adults": 2, "children": 2}, authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_toddler_pacing_risk(packet)
        assert result is None

    def test_toddler_short_trip(self):
        """Test medium risk for toddler + short trip."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "child_ages": Slot(value=[2, 5], authority_level="explicit_user"),
                "duration_days": Slot(value=5, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_toddler_pacing_risk(packet)
        assert result is not None
        assert result["risk_level"] == "medium"
        assert result["toddler_ages"] == [2]

    def test_toddler_long_trip_high_risk(self):
        """Test high risk for toddler + long trip."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "child_ages": Slot(value=[3], authority_level="explicit_user"),
                "duration_days": Slot(value=10, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_toddler_pacing_risk(packet)
        assert result is not None
        assert result["risk_level"] == "high"
        assert "10 days" in result["reasoning"]


class TestBudgetFeasibilityRule:
    """Tests for budget feasibility rule."""

    def test_no_budget_returns_none(self):
        """Test that rule returns None when no budget provided."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_budget_feasibility(packet)
        assert result is None

    def test_feasible_budget(self):
        """Test feasible budget scenario."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "budget_min": Slot(value=50000, authority_level="explicit_user"),
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Goa", authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_budget_feasibility(packet)
        assert result is not None
        assert result["feasible"] is True
        assert result["risk_level"] == "low"

    def test_infeasible_budget(self):
        """Test infeasible budget scenario."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "budget_min": Slot(value=20000, authority_level="explicit_user"),
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Singapore", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        )

        result = rule_budget_feasibility(packet)
        assert result is not None
        assert result["feasible"] is False
        assert result["risk_level"] == "high"


class TestVisaTimelineRule:
    """Tests for visa timeline risk rule."""

    def test_domestic_no_visa(self):
        """Test that domestic trips return low risk."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "resolved_destination": Slot(value="Goa", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        )

        result = rule_visa_timeline_risk(packet)
        assert result is not None
        assert result["risk_level"] == "low"
        assert result["visa_lead_time_days"] == 0

    def test_international_visa_required_high_urgency(self):
        """Test high urgency with visa required."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "resolved_destination": Slot(value="USA", authority_level="explicit_user"),
                "visa_status": Slot(
                    value={"requirement": "required", "status": "not_applied"},
                    authority_level="explicit_user",
                ),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
                "urgency": Slot(value="high", authority_level="derived_signal"),
            },
        )

        result = rule_visa_timeline_risk(packet)
        assert result is not None
        assert result["risk_level"] == "high"
        assert result["visa_lead_time_days"] > 0


class TestCompositionRiskRule:
    """Tests for composition risk rule."""

    def test_adult_only_low_risk(self):
        """Test that adult-only groups have low risk."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(value={"adults": 4}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_composition_risk(packet)
        assert result is not None
        assert result["risk_level"] == "low"
        assert len(result["concerns"]) == 0

    def test_multi_generational_medium_risk(self):
        """Test medium risk for multi-generational group."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(
                    value={"adults": 2, "elderly": 1, "children": 2},
                    authority_level="explicit_user",
                ),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_composition_risk(packet)
        assert result is not None
        assert result["risk_level"] == "medium"
        assert len(result["concerns"]) > 0
        assert len(result["recommendations"]) > 0

    def test_large_party_high_risk(self):
        """Test high risk for large party with multiple concerns."""
        packet = CanonicalPacket(
            packet_id="test",
            facts={
                "party_composition": Slot(
                    value={"adults": 1, "elderly": 2, "children": 4, "toddlers": 1},
                    authority_level="explicit_user",
                ),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={},
        )

        result = rule_composition_risk(packet)
        assert result is not None
        assert result["risk_level"] == "high"
        assert result["party_size"] == 8
