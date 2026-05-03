"""
tests/test_readiness_engine — Behavioral tests for the computed readiness model.

The readiness engine is a pure computation: packet + pipeline outputs in, readiness out.
No side effects, no stage mutation.

ChatGPT review requirements:
- booking_ready must be false until booking_data exists
- proposal_ready must depend on pipeline outputs (bundles, fees, safety)
- Empty/None values should not count as met
- compute_readiness must never mutate packet.stage
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
        if isinstance(value, Slot):
            packet.facts[name] = value
        else:
            packet.facts[name] = Slot(value=value, confidence=0.9, authority_level="explicit_user")
    return packet


# Facts that satisfy each fact-based tier
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

# Pipeline outputs that satisfy proposal_ready
FULL_PIPELINE_OUTPUTS = {
    "traveler_bundle": {"traveler_name": "Jane Doe"},
    "internal_bundle": {"session_goal": "Build proposal"},
    "safety": {"leaks": [], "is_safe": True},
    "fees": {"total_base_fee": 150},
    "decision": {
        "decision_state": "PROCEED_INTERNAL_DRAFT",
        "hard_blockers": [],
    },
}


class TestIntakeMinimum:
    """intake_minimum: destination + dates with usable values."""

    def test_met(self):
        packet = _make_packet(**INTAKE_MINIMUM_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "intake_minimum"
        assert result.suggested_next_stage == "discovery"
        assert result.tiers["intake_minimum"].ready is True

    def test_empty_packet_has_no_ready_tier(self):
        packet = _make_packet()
        result = compute_readiness(packet)
        assert result.highest_ready_tier is None
        assert result.missing_for_next == ["destination_candidates", "date_window"]

    def test_empty_string_does_not_count_as_met(self):
        packet = _make_packet(destination_candidates="", date_window="June 2026")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet

    def test_none_value_does_not_count_as_met(self):
        packet = _make_packet(destination_candidates=None, date_window="June 2026")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet

    def test_empty_list_does_not_count_as_met(self):
        packet = _make_packet(destination_candidates=[], date_window="June 2026")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet

    def test_empty_dict_does_not_count_as_met(self):
        packet = _make_packet(destination_candidates={}, date_window="June 2026")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet

    def test_whitespace_only_does_not_count_as_met(self):
        packet = _make_packet(destination_candidates="   ", date_window="June 2026")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet


class TestQuoteReady:
    """quote_ready: 6 MVB fields with usable values."""

    def test_met(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
        assert result.suggested_next_stage == "shortlist"
        assert result.tiers["quote_ready"].ready is True
        assert result.tiers["proposal_ready"].ready is False

    def test_partial_tier_shows_unmet_fields(self):
        partial = {k: v for k, v in QUOTE_READY_FACTS.items() if k != "budget_raw_text"}
        packet = _make_packet(**partial)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "intake_minimum"
        assert "budget_raw_text" in result.tiers["quote_ready"].unmet


class TestProposalReady:
    """proposal_ready: quote_ready facts + pipeline outputs (bundles, fees, safety pass)."""

    def test_met_with_all_pipeline_outputs(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            decision=FULL_PIPELINE_OUTPUTS["decision"],
        )
        assert result.highest_ready_tier == "proposal_ready"
        assert result.suggested_next_stage == "proposal"
        assert result.tiers["proposal_ready"].ready is True
        assert result.tiers["booking_ready"].ready is False

    def test_false_when_fees_missing(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=None,
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "fees" in result.tiers["proposal_ready"].unmet

    def test_false_when_traveler_bundle_missing(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=None,
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "traveler_bundle" in result.tiers["proposal_ready"].unmet

    def test_false_when_internal_bundle_missing(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=None,
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "internal_bundle" in result.tiers["proposal_ready"].unmet

    def test_false_when_leakage_fails(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety={"leaks": [{"field": "internal_margin"}], "is_safe": False},
            fees=FULL_PIPELINE_OUTPUTS["fees"],
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "safety_pass" in result.tiers["proposal_ready"].unmet

    def test_false_when_decision_has_critical_suitability_blocker(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            decision={
                "decision_state": "STOP_NEEDS_REVIEW",
                "hard_blockers": ["suitability_critical_flags_present"],
            },
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "no_critical_blockers" in result.tiers["proposal_ready"].unmet

    def test_false_when_safety_missing(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=None,
            fees=FULL_PIPELINE_OUTPUTS["fees"],
        )
        assert result.tiers["proposal_ready"].ready is False
        assert "safety" in result.tiers["proposal_ready"].unmet

    def test_false_without_pipeline_outputs(self):
        """Only facts, no pipeline outputs → quote_ready at most."""
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
        assert result.tiers["proposal_ready"].ready is False


class TestBookingReady:
    """booking_ready: always false until booking_data exists."""

    def test_false_without_booking_data(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            booking_data=None,
        )
        assert result.tiers["booking_ready"].ready is False
        assert "booking_data" in result.tiers["booking_ready"].unmet

    def test_false_even_with_traveler_facts_in_packet(self):
        """booking_ready cannot be faked from packet facts alone."""
        booking_facts = {
            **PROPOSAL_READY_FACTS,
            "traveler_identities": "John Doe, Jane Doe",
            "primary_payer": "John Doe",
            "emergency_contacts": "Jane Doe +91-9876543210",
        }
        packet = _make_packet(**booking_facts)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            booking_data=None,
        )
        assert result.tiers["booking_ready"].ready is False

    def test_true_with_booking_data(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            booking_data={
                "travelers": [{
                    "traveler_id": "adult_1",
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                }],
                "payer": {"name": "Jane Doe"},
            },
        )
        assert result.tiers["booking_ready"].ready is True
        assert result.highest_ready_tier == "booking_ready"
        assert result.suggested_next_stage == "booking"

    def test_false_with_empty_booking_data(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            booking_data={},
        )
        assert result.tiers["booking_ready"].ready is False


class TestInvariants:
    """Cross-cutting invariants that must always hold."""

    def test_should_auto_advance_stage_is_always_false(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(
            packet,
            traveler_bundle=FULL_PIPELINE_OUTPUTS["traveler_bundle"],
            internal_bundle=FULL_PIPELINE_OUTPUTS["internal_bundle"],
            safety=FULL_PIPELINE_OUTPUTS["safety"],
            fees=FULL_PIPELINE_OUTPUTS["fees"],
            booking_data={
                "travelers": [{
                    "traveler_id": "adult_1",
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                }],
                "payer": {"name": "Jane Doe"},
            },
        )
        assert result.should_auto_advance_stage is False

    def test_compute_readiness_never_mutates_packet_stage(self):
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        original_stage = getattr(packet, "stage", None)
        _ = compute_readiness(packet)
        assert getattr(packet, "stage", None) == original_stage

    def test_tier_order_is_cumulative_for_fact_tiers(self):
        """intake_minimum fields ⊂ quote_ready fields."""
        lower = set(TIER_FIELDS["intake_minimum"])
        upper = set(TIER_FIELDS["quote_ready"])
        assert lower.issubset(upper)

    def test_to_dict_produces_serializable_shape(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        d = result.to_dict()

        assert d["highest_ready_tier"] == "quote_ready"
        assert d["suggested_next_stage"] == "shortlist"
        assert d["should_auto_advance_stage"] is False
        assert isinstance(d["tiers"], dict)
        assert d["tiers"]["quote_ready"]["ready"] is True
        assert isinstance(d["tiers"]["quote_ready"]["met"], list)

    def test_suggested_next_stage_maps_correctly(self):
        for tier, stage in TIER_STAGE_MAP.items():
            assert isinstance(stage, str)
            assert stage in ("discovery", "shortlist", "proposal", "booking")

    def test_met_plus_unmet_equals_tier_fields(self):
        """For fact-based tiers, met + unmet covers all tier fields."""
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        for tier_name in ("intake_minimum", "quote_ready"):
            detail = result.tiers[tier_name]
            expected = TIER_FIELDS[tier_name]
            assert sorted(detail.met + detail.unmet) == sorted(expected)

    def test_missing_for_next_shows_delta(self):
        packet = _make_packet(**QUOTE_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
        # Missing items for proposal_ready (pipeline outputs + delta fields)
        assert len(result.missing_for_next) > 0


class TestEdgeCases:
    """Edge cases and regression guards."""

    def test_slot_object_with_empty_value_not_counted(self):
        """A Slot with value="" should not count as met."""
        packet = _make_packet()
        packet.facts["destination_candidates"] = Slot(value="", confidence=0.9, authority_level="explicit_user")
        packet.facts["date_window"] = Slot(value="June 2026", confidence=0.9, authority_level="explicit_user")
        result = compute_readiness(packet)
        assert "destination_candidates" in result.tiers["intake_minimum"].unmet

    def test_tier_detail_structure(self):
        packet = _make_packet(**INTAKE_MINIMUM_FACTS)
        result = compute_readiness(packet)
        for tier_name in TIER_ORDER:
            detail = result.tiers[tier_name]
            assert isinstance(detail, TierDetail)
            assert isinstance(detail.met, list)
            assert isinstance(detail.unmet, list)
            assert detail.ready == (len(detail.unmet) == 0)

    def test_no_pipeline_outputs_caps_at_quote_ready(self):
        """Without any pipeline outputs, highest tier is quote_ready at most."""
        packet = _make_packet(**PROPOSAL_READY_FACTS)
        result = compute_readiness(packet)
        assert result.highest_ready_tier == "quote_ready"
