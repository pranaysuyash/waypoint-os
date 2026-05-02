"""
tests/test_readiness_engine — Behavioral tests for the computed readiness model.

The readiness engine is a pure computation: packet in, readiness out.
No side effects, no stage mutation.
"""

import pytest

from intake.packet_models import CanonicalPacket, Slot
from intake.readiness import (
    compute_readiness,
    ReadinessResult,
    TierDetail,
    TIER_ORDER,
    TIER_FIELDS,
    TIER_STAGE_MAP,
)


def _make_packet(**fact_values) -> CanonicalPacket:
    """Build a minimal CanonicalPacket with the given facts populated."""
    packet = CanonicalPacket(packet_id="test-readiness")
    for name, value in fact_values.items():
        packet.facts[name] = Slot(value=value, confidence=0.9, authority_level="explicit_user")
    return packet


# Facts that satisfy each tier
INTAKE_MINIMUM_FACTS = {
    "destination_candidates": "Singapore",
    "date_window": "June 2026",
}

QUOTE_READY_FACTS = {
    **INTAKE_MINIMUM_FACTS,
    "origin_city": "Bangalore",
    "party_size": 4,
    "budget_raw_text": "2.5L INR",
    "trip_purpose": "Family Leisure",
}

PROPOSAL_READY_FACTS = {
    **QUOTE_READY_FACTS,
    "trip_priorities": "Kid-friendly activities",
    "date_flexibility": "Moderate",
}

BOOKING_READY_FACTS = {
    **PROPOSAL_READY_FACTS,
    "traveler_identities": "List of travelers",
    "primary_payer": "John Doe",
    "emergency_contacts": "Jane Doe +91-9876543210",
}


class TestComputeReadiness:
    """Core readiness computation tests."""

    def test_empty_packet_has_no_ready_tier(self):
        packet = _make_packet()
        result = compute_readiness(packet)
        assert result.highest_ready_tier is None
        assert result.missing_for_next == ["destination_candidates", "date_window"]

    def test_intake_minimum_met(self):
        packet = _make_packet(**INTAKE_MINIMUM_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "intake_minimum"
        assert result.suggested_next_stage == "discovery"
        assert result.tiers["intake_minimum"].ready is True
        assert result.tiers["quote_ready"].ready is False

    def test_quote_ready_met(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
        assert result.suggested_next_stage == "shortlist"
        assert result.tiers["quote_ready"].ready is True
        assert result.tiers["proposal_ready"].ready is False

    def test_proposal_ready_met(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "proposal_ready"
        assert result.suggested_next_stage == "proposal"
        assert result.tiers["proposal_ready"].ready is True
        assert result.tiers["booking_ready"].ready is False

    def test_booking_ready_met(self):
        packet = _make_packet(**BOOKING_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "booking_ready"
        assert result.suggested_next_stage == "booking"
        assert result.tiers["booking_ready"].ready is True

    def test_should_auto_advance_stage_is_always_false(self):
        # Even when fully booking-ready, auto advance is False
        packet = _make_packet(**BOOKING_READY_FACTS)
        result = compute_readiness(packet)
        assert result.should_auto_advance_stage is False

    def test_partial_tier_shows_unmet_fields(self):
        # Has intake_minimum but missing budget_raw_text from quote_ready
        partial = {k: v for k, v in QUOTE_READY_FACTS.items() if k != "budget_raw_text"}
        packet = _make_packet(**partial)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "intake_minimum"
        assert "budget_raw_text" in result.missing_for_next
        assert result.tiers["quote_ready"].unmet == ["budget_raw_text"]

    def test_missing_for_next_when_highest_is_quote_ready(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
        # Missing proposal_ready fields
        assert "trip_priorities" in result.missing_for_next
        assert "date_flexibility" in result.missing_for_next

    def test_tier_order_is_cumulative(self):
        """Higher tiers include all fields from lower tiers (cumulative readiness)."""
        for i in range(1, len(TIER_ORDER)):
            lower = TIER_FIELDS[TIER_ORDER[i - 1]]
            upper = TIER_FIELDS[TIER_ORDER[i]]
            # QUOTE_READY includes INTAKE_MINIMUM fields, so lower must be subset of upper
            assert set(lower).issubset(set(upper)), (
                f"Tiers {TIER_ORDER[i-1]} fields not subset of {TIER_ORDER[i]}: "
                f"missing {set(lower) - set(upper)}"
            )

    def test_to_dict_produces_serializable_shape(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        d = result.to_dict()

        assert d["highest_ready_tier"] == "quote_ready"
        assert d["suggested_next_stage"] == "shortlist"
        assert d["should_auto_advance_stage"] is False
        assert isinstance(d["tiers"], dict)
        assert "quote_ready" in d["tiers"]
        assert d["tiers"]["quote_ready"]["ready"] is True
        assert isinstance(d["tiers"]["quote_ready"]["met"], list)

    def test_suggested_next_stage_maps_correctly(self):
        for tier, stage in TIER_STAGE_MAP.items():
            assert isinstance(stage, str)
            assert stage in ("discovery", "shortlist", "proposal", "booking")


class TestTierDetails:
    """Test individual tier detail structure."""

    def test_each_tier_has_met_and_unmet(self):
        packet = _make_packet(**INTAKE_MINIMUM_FACTS)
        result = compute_readiness(packet)
        for tier_name in TIER_ORDER:
            detail = result.tiers[tier_name]
            assert isinstance(detail, TierDetail)
            assert isinstance(detail.met, list)
            assert isinstance(detail.unmet, list)
            assert detail.ready == (len(detail.unmet) == 0)

    def test_met_plus_unmet_equals_tier_fields(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        for tier_name in TIER_ORDER:
            detail = result.tiers[tier_name]
            expected_fields = TIER_FIELDS[tier_name]
            assert sorted(detail.met + detail.unmet) == sorted(expected_fields)
