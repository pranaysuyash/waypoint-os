"""
Unit tests for fee calculation module.

Tests risk-adjusted fee calculation based on suitability risks.
"""
import pytest
from src.fees.calculation import FeeCalculator, calculate_trip_fees


class TestFeeCalculator:
    """Test the FeeCalculator class."""

    def test_base_fees(self):
        """Test base fee calculation without risks."""
        # Flights: 2 tickets * $500 = $1000
        breakdown = FeeCalculator.calculate_adjusted_fee("flights", 2, [])
        assert breakdown.base_fee == 1000.0
        assert breakdown.adjusted_fee == 1000.0
        assert breakdown.risk_multiplier == 1.0
        assert breakdown.risk_severity == "low"
        assert "No significant risks" in breakdown.explanation

    def test_medium_risk_multiplier(self):
        """Test fee adjustment with medium risk."""
        risks = [{"severity": "medium", "category": "health"}]
        breakdown = FeeCalculator.calculate_adjusted_fee("flights", 1, risks)
        assert breakdown.base_fee == 500.0
        assert breakdown.adjusted_fee == 600.0  # 500 * 1.2
        assert breakdown.risk_multiplier == 1.2
        assert breakdown.risk_severity == "medium"

    def test_high_risk_multiplier(self):
        """Test fee adjustment with high risk."""
        risks = [{"severity": "high", "category": "security"}]
        breakdown = FeeCalculator.calculate_adjusted_fee("accommodations", 3, risks)
        assert breakdown.base_fee == 900.0  # 3 nights * $300
        assert breakdown.adjusted_fee == 1260.0  # 900 * 1.4
        assert breakdown.risk_multiplier == 1.4
        assert breakdown.risk_severity == "high"

    def test_critical_risk_multiplier(self):
        """Test fee adjustment with critical risk."""
        risks = [{"severity": "critical", "category": "emergency"}]
        breakdown = FeeCalculator.calculate_adjusted_fee("activities", 4, risks)
        assert breakdown.base_fee == 400.0  # 4 activities * $100
        assert breakdown.adjusted_fee == 800.0  # 400 * 2.0
        assert breakdown.risk_multiplier == 2.0
        assert breakdown.risk_severity == "critical"

    def test_multiple_risks_highest_severity(self):
        """Test that highest severity risk determines multiplier."""
        risks = [
            {"severity": "low", "category": "weather"},
            {"severity": "high", "category": "health"},
            {"severity": "medium", "category": "logistics"}
        ]
        breakdown = FeeCalculator.calculate_adjusted_fee("flights", 1, risks)
        assert breakdown.risk_multiplier == 1.4  # High risk multiplier
        assert breakdown.risk_severity == "high"

    def test_unknown_service_type(self):
        """Test handling of unknown service types."""
        breakdown = FeeCalculator.calculate_adjusted_fee("unknown", 1, [])
        assert breakdown.base_fee == 0.0
        assert breakdown.adjusted_fee == 0.0
        assert "Unknown service type" in breakdown.explanation


class TestCalculateTripFees:
    """Test the calculate_trip_fees function."""

    def test_trip_fees_basic(self):
        """Test basic trip fee calculation."""
        packet = {
            "facts": {
                "party_size": {"value": 2},
                "duration_nights": {"value": 3}
            }
        }
        decision = {
            "risk_flags": []
        }

        result = calculate_trip_fees(packet, decision)

        # Check structure
        assert "service_breakdowns" in result
        assert "total_base_fee" in result
        assert "total_adjusted_fee" in result
        assert "fee_adjustment" in result
        assert "risk_summary" in result

        # Check calculations
        # Flights: 2 people * 2 flights * $500 = $2000
        # Accommodations: 3 nights * 2 people * $300 = $1800
        # Activities: 4 days * 2 activities * 2 people * $100 = $1600
        # Total base: $5400
        assert result["total_base_fee"] == 5400.0
        assert result["total_adjusted_fee"] == 5400.0  # No risks
        assert result["fee_adjustment"] == 0.0

    def test_trip_fees_with_risks(self):
        """Test trip fee calculation with risks."""
        packet = {
            "facts": {
                "party_size": {"value": 1},
                "duration_nights": {"value": 1}
            }
        }
        decision = {
            "risk_flags": [
                {"severity": "high", "category": "health"},
                {"severity": "medium", "category": "weather"}
            ]
        }

        result = calculate_trip_fees(packet, decision)

        # Flights: 1 person * 2 flights * $500 = $1000 * 1.4 = $1400
        # Accommodations: 1 night * 1 person * $300 = $300 * 1.4 = $420
        # Activities: 2 days * 2 activities * 1 person * $100 = $400 * 1.4 = $560
        # Total adjusted: $2380
        assert result["total_base_fee"] == 1700.0
        assert result["total_adjusted_fee"] == 2380.0
        assert result["fee_adjustment"] == 680.0
        assert "Highest risk: high" in result["risk_summary"]

    def test_trip_fees_empty_packet(self):
        """Test trip fee calculation with minimal packet data."""
        packet = {"facts": {}}
        decision = {"risk_flags": []}

        result = calculate_trip_fees(packet, decision)

        # Should use defaults: 1 person, 1 night
        # Flights: 1 * 2 * $500 = $1000
        # Accommodations: 1 * 1 * $300 = $300
        # Activities: 2 * 2 * 1 * $100 = $400
        # Total: $1700
        assert result["total_base_fee"] == 1700.0
        assert result["total_adjusted_fee"] == 1700.0

    def test_trip_fees_party_size_list(self):
        """Test handling when party_size is a list."""
        packet = {
            "facts": {
                "party_size": {"value": ["adult1", "adult2", "child1"]},  # 3 people
                "duration_nights": {"value": 2}
            }
        }
        decision = {"risk_flags": []}

        result = calculate_trip_fees(packet, decision)

        # Flights: 3 people * 2 flights * $500 = $3000
        # Accommodations: 2 nights * 3 people * $300 = $1800
        # Activities: 3 days * 2 activities * 3 people * $100 = $1800
        # Total: $6600
        assert result["total_base_fee"] == 6600.0