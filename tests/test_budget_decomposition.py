"""
Tests for budget decomposition (per-bucket cost estimation).

Covers: decompose_budget(), BudgetBreakdownResult, CostBucketEstimate,
integration with run_gap_and_decision(), and the trip budget reality scenario.

Run: uv run python -m pytest tests/test_budget_decomposition.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from intake.packet_models import (
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
)
from intake.decision import (
    COST_BUCKET_NAMES,
    BudgetBreakdownResult,
    CostBucketEstimate,
    check_budget_feasibility,
    decompose_budget,
    run_gap_and_decision,
    BUDGET_BUCKET_RANGES,
    _DESTINATION_ALIASES,
    _get_composition_modifiers,
    _is_multi_destination,
    _resolve_bucket_table,
)


def _ev(excerpt: str = "test") -> list[EvidenceRef]:
    return [EvidenceRef(envelope_id="test_env", evidence_type="text_span", excerpt=excerpt)]


def _slot(value, authority=AuthorityLevel.EXPLICIT_USER, confidence=0.9) -> Slot:
    return Slot(
        value=value,
        confidence=confidence,
        authority_level=authority,
        evidence_refs=_ev(str(value)),
    )


def _signal_slot(value, maturity="heuristic", confidence=0.7) -> Slot:
    return Slot(
        value=value,
        confidence=confidence,
        authority_level=AuthorityLevel.DERIVED_SIGNAL,
        extraction_mode="derived",
        evidence_refs=_ev("computed"),
        maturity=maturity,
    )


def _base_packet(stage: str = "discovery", mode: str = "normal_intake") -> CanonicalPacket:
    pkt = CanonicalPacket(packet_id=f"budget_test_{stage}_{mode}")
    pkt.stage = stage
    pkt.operating_mode = mode
    return pkt


# =============================================================================
# Test 1: decompose_budget returns 8 buckets for Dubai
# =============================================================================
class TestBucketCoverage:
    def test_dubai_returns_all_8_buckets(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(5)
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 2, "children": 0, "toddlers": 1, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert len(result.buckets) == 8
        bucket_names = [b.bucket for b in result.buckets]
        for name in COST_BUCKET_NAMES:
            assert name in bucket_names, f"Missing bucket: {name}"

    def test_maldives_returns_all_8_buckets(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Maldives")
        pkt.facts["party_size"] = _slot(5)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert len(result.buckets) == 8

    def test_domestic_goa_returns_all_8_buckets(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(80000)
        pkt.facts["resolved_destination"] = _slot("Goa")
        pkt.facts["party_size"] = _slot(3)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("domestic")

        result = decompose_budget(pkt)
        assert len(result.buckets) == 8

    def test_unknown_destination_uses_international_defaults(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(300000)
        pkt.facts["resolved_destination"] = _slot("Atlantis")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert len(result.buckets) == 8
        assert result.maturity == "heuristic"


# =============================================================================
# Test 2: Verdict classification
# =============================================================================
class TestVerdictClassification:
    def test_realistic_when_budget_covers_high(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(5000000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert result.verdict == "realistic"

    def test_borderline_when_budget_between_low_and_high(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(120000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert result.verdict in ("realistic", "borderline")

    def test_not_realistic_when_budget_far_below_low(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(10000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(5)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert result.verdict == "not_realistic"

    def test_no_budget_returns_not_realistic(self):
        pkt = _base_packet()
        result = decompose_budget(pkt)
        assert result.verdict == "not_realistic"
        assert "budget_unknown" in result.risks

    def test_no_destination_returns_not_realistic(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(500000)
        result = decompose_budget(pkt)
        assert result.verdict == "not_realistic"
        assert "destination_unknown" in result.risks


# =============================================================================
# Test 3: Budget breakdown scenario — Dubai + Maldives family trip
# =============================================================================
class TestBudgetRealityScenario:
    def test_dubai_maldives_family_of_5_borderline(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["destination_candidates"] = _slot(["Dubai", "Maldives"])
        pkt.facts["party_size"] = _slot(5)
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 2, "children": 0, "toddlers": 1, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert result.verdict in ("borderline", "realistic", "not_realistic")
        assert len(result.buckets) == 8
        assert len(result.missing_buckets) >= 0
        assert result.budget_stated == 550000
        assert len(result.risks) > 0
        assert "transfer_complexity" in result.risks

    def test_dubai_maldives_generates_alternative(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(100000)
        pkt.facts["destination_candidates"] = _slot(["Dubai", "Maldives"])
        pkt.facts["party_size"] = _slot(5)
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 2, "children": 0, "toddlers": 1, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        if result.verdict in ("borderline", "not_realistic"):
            assert result.alternative is not None


# =============================================================================
# Test 4: Composition modifiers
# =============================================================================
class TestCompositionModifiers:
    def test_toddler_adds_risk(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(5)
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 0, "children": 0, "toddlers": 1, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert "toddler_addons" in result.risks

    def test_no_toddler_no_toddler_risk(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 0, "children": 0, "toddlers": 0, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert "toddler_addons" not in result.risks


# =============================================================================
# Test 5: Multi-destination penalties
# =============================================================================
class TestMultiDestination:
    def test_multi_dest_adds_transfer_complexity(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["destination_candidates"] = _slot(["Dubai", "Maldives"])
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert "transfer_complexity" in result.risks

    def test_single_dest_no_transfer_complexity(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert "transfer_complexity" not in result.risks


# =============================================================================
# Test 6: Integration with run_gap_and_decision
# =============================================================================
class TestGapAndDecisionIntegration:
    def test_decision_result_contains_budget_breakdown(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(550000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(5)
        pkt.facts["destination_candidates"] = _slot(["Dubai"])
        pkt.facts["origin_city"] = _slot("Mumbai")
        pkt.facts["date_window"] = _slot("October 2026")
        pkt.facts["budget_raw_text"] = _slot("5.5L")
        pkt.facts["trip_purpose"] = _slot("leisure")
        pkt.facts["party_composition"] = _slot(
            {"adults": 2, "teens": 2, "children": 0, "toddlers": 1, "elderly": 0}
        )
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = run_gap_and_decision(pkt)
        assert result.budget_breakdown is not None
        assert isinstance(result.budget_breakdown, BudgetBreakdownResult)
        assert len(result.budget_breakdown.buckets) == 8
        assert result.budget_breakdown.verdict in ("realistic", "borderline", "not_realistic")
        assert result.rationale.get("budget_verdict") is not None

    def test_decision_result_no_breakdown_without_destination(self):
        pkt = _base_packet()
        result = run_gap_and_decision(pkt)
        assert result.budget_breakdown is not None
        assert result.budget_breakdown.verdict == "not_realistic"

    def test_rationale_contains_budget_summary(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(300000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.facts["destination_candidates"] = _slot(["Dubai"])
        pkt.facts["origin_city"] = _slot("Mumbai")
        pkt.facts["date_window"] = _slot("October 2026")
        pkt.facts["budget_raw_text"] = _slot("3L")
        pkt.facts["trip_purpose"] = _slot("leisure")
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = run_gap_and_decision(pkt)
        assert "budget_verdict" in result.rationale
        assert "budget_total_low" in result.rationale
        assert "budget_total_high" in result.rationale


# =============================================================================
# Test 7: Bucket range integrity
# =============================================================================
class TestBucketRangeIntegrity:
    def test_all_destinations_have_all_8_buckets(self):
        for dest, ranges in BUDGET_BUCKET_RANGES.items():
            for bname in COST_BUCKET_NAMES:
                assert bname in ranges, f"Missing bucket '{bname}' for destination '{dest}'"

    def test_low_leq_high_for_all_ranges(self):
        for dest, ranges in BUDGET_BUCKET_RANGES.items():
            for bname, (low, high, weight) in ranges.items():
                assert low <= high, f"{dest}.{bname}: low={low} > high={high}"

    def test_weights_sum_approximately_to_1(self):
        for dest, ranges in BUDGET_BUCKET_RANGES.items():
            total_weight = sum(w for _, (_, _, w) in ranges.items())
            assert 0.9 <= total_weight <= 1.1, f"{dest}: weight sum = {total_weight}"


# =============================================================================
# Test 8: Destination aliasing
# =============================================================================
class TestDestinationAliasing:
    def test_tokyo_uses_japan_ranges(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(500000)
        pkt.facts["resolved_destination"] = _slot("Tokyo")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        assert len(result.buckets) == 8

    def test_andamans_aliased_to_andaman(self):
        assert _DESTINATION_ALIASES.get("Andamans") == "Andaman"

    def test_paris_aliased_to_europe(self):
        assert _DESTINATION_ALIASES.get("Paris") == "Europe"


# =============================================================================
# Test 9: Covered vs gap determination
# =============================================================================
class TestCoveredDetermination:
    def test_generous_budget_covers_all_buckets(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(10000000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        for b in result.buckets:
            if b.low > 0:
                assert b.covered, f"Bucket '{b.bucket}' should be covered with budget 1Cr"

    def test_tiny_budget_marks_most_as_gap(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(5000)
        pkt.facts["resolved_destination"] = _slot("Dubai")
        pkt.facts["party_size"] = _slot(2)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("international")

        result = decompose_budget(pkt)
        uncovered = [b.bucket for b in result.buckets if not b.covered and b.low > 0]
        assert len(uncovered) > 0


# =============================================================================
# Test 10: Domestic trip visa_insurance zero
# =============================================================================
class TestDomesticVisaInsurance:
    def test_domestic_visa_insurance_is_zero(self):
        pkt = _base_packet()
        pkt.facts["budget_min"] = _slot(80000)
        pkt.facts["resolved_destination"] = _slot("Goa")
        pkt.facts["party_size"] = _slot(3)
        pkt.derived_signals["domestic_or_international"] = _signal_slot("domestic")

        result = decompose_budget(pkt)
        visa_b = next((b for b in result.buckets if b.bucket == "visa_insurance"), None)
        assert visa_b is not None
        assert visa_b.low == 0
        assert visa_b.high == 0
        assert visa_b.notes is not None
        assert "domestic" in visa_b.notes.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])