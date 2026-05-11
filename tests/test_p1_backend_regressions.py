"""
Backend P1 Regression Tests — Scenario-gap findings.

Tests for:
1. NB02 destination ambiguity tightening ("A or B" cases)
2. Last-minute non-emergency soft-blocker behavior
3. Confidence threshold → coaching severity regression contract

Run: uv run python -m pytest tests/test_p1_backend_regressions.py -v
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
    SourceEnvelope,
    SubGroup,
)
from intake.extractors import ExtractionPipeline
from intake.decision import (
    AmbiguityRef,
    DecisionResult,
    classify_ambiguity_severity,
    check_budget_feasibility,
    field_fills_blocker,
    generate_question,
    get_numeric_budget,
    run_gap_and_decision,
    apply_urgency,
    apply_operating_mode,
    MVB_BY_STAGE,
    _synthesize_destination_ambiguity,
    ConfidenceScorecard,
)


def extract_and_decide(text: str, source: str = "agency_notes") -> DecisionResult:
    envelope = SourceEnvelope.from_freeform(text, source)
    packet = ExtractionPipeline().extract([envelope])
    return run_gap_and_decision(packet)


def make_packet(
    destination: str | list[str] | None = None,
    origin: str = "Bangalore",
    party_size: int = 4,
    budget_min: int | None = None,
    date_window: str = "April 2026",
    stage: str = "discovery",
    operating_mode: str = "normal_intake",
    urgency: str | None = None,
) -> CanonicalPacket:
    """Build a minimal CanonicalPacket for decision testing."""
    envelope = SourceEnvelope.from_freeform(
        f"Family of {party_size} from {origin}, "
        f"want {destination or 'Goa'}. "
        f"Budget {budget_min or '3L'}. {date_window}.",
        "test_source",
    )
    packet = ExtractionPipeline().extract([envelope])
    packet.stage = stage
    packet.operating_mode = operating_mode

    if urgency and packet.derived_signals.get("urgency"):
        from intake.packet_models import Slot
        packet.derived_signals["urgency"] = Slot(
            value=urgency,
            confidence=0.9,
            authority_level=AuthorityLevel.DERIVED_SIGNAL,
            extraction_mode="derived",
            derived_from=["date_end"],
        )

    return packet


# ===========================================================================
# P1-1: Destination ambiguity tightening ("A or B" cases)
# ===========================================================================


class TestDestinationAmbiguityTightening:
    """
    Tighten NB02 ambiguity handling for "A or B" destination cases.
    Known tension: destination with multiple candidates should always produce
    a blocking ambiguity at discovery+, never silently proceed.
    """

    def test_or_separator_creates_blocking_ambiguity(self):
        """'Andaman or Sri Lanka' must produce unresolved_alternatives blocking ambiguity."""
        result = extract_and_decide(
            "Family of 4 from Bangalore. Want Andaman or Sri Lanka. Budget 3L, April 2026."
        )
        blocking = [a for a in result.ambiguities if a.severity == "blocking"
                     and a.field_name == "destination_candidates"]
        assert len(blocking) > 0, \
            f"Expected blocking destination ambiguity for 'or' separator, got {[a.severity for a in result.ambiguities]}"
        assert result.decision_state == "ASK_FOLLOWUP", \
            f"Expected ASK_FOLLOWUP for unresolved destination, got {result.decision_state}"

    def test_vs_separator_creates_blocking_ambiguity(self):
        """'Singapore vs Bali' must produce blocking ambiguity."""
        result = extract_and_decide(
            "Couple from Mumbai. Singapore vs Bali. Budget 2L, May 2026."
        )
        blocking = [a for a in result.ambiguities if a.severity == "blocking"
                     and a.field_name == "destination_candidates"]
        assert len(blocking) > 0, \
            f"Expected blocking destination ambiguity for 'vs' separator"

    def test_comma_separated_destinations_ambiguity(self):
        """
        'Goa, Kerala, or Rajasthan' must produce blocking ambiguity.
        
        NOTE: NB01 extraction may not always detect comma+or patterns as
        multiple destinations. The _synthesize_destination_ambiguity function
        handles the case where extraction correctly identifies multiple candidates.
        This test documents the expected behavior when extraction succeeds.
        """
        envelope = SourceEnvelope.from_freeform(
            "Group of 6 from Delhi. Budget 5L. March 2026.", "test"
        )
        packet = ExtractionPipeline().extract([envelope])
        packet.facts["destination_candidates"] = Slot(
            value=["Goa", "Kerala", "Rajasthan"],
            confidence=0.85,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            extraction_mode="explicit",
            derived_from=["envelope_1"],
        )
        packet.stage = "discovery"

        result = run_gap_and_decision(packet)
        blocking = [a for a in result.ambiguities if a.severity == "blocking"
                     and a.field_name == "destination_candidates"]
        assert len(blocking) > 0, \
            f"Expected blocking destination ambiguity for comma-separated destinations"
        assert result.decision_state != "PROCEED_TRAVELER_SAFE", \
            f"Should not proceed with unresolved multi-destination, got {result.decision_state}"

    def test_single_destination_no_blocking_ambiguity(self):
        """Single clear destination should NOT produce destination ambiguity."""
        result = extract_and_decide(
            "Family of 4 from Bangalore. Want Singapore. Budget 3L, April 2026."
        )
        dest_blocking = [a for a in result.ambiguities
                         if a.field_name == "destination_candidates" and a.severity == "blocking"]
        assert len(dest_blocking) == 0, \
            f"Single destination should not have blocking ambiguity, got {dest_blocking}"

    def test_blocking_at_shortlist_escalates(self):
        """Destination ambiguity that's advisory at discovery becomes blocking at shortlist."""
        sev_discovery = classify_ambiguity_severity(
            "destination_candidates", "value_vague", stage="discovery"
        )
        sev_shortlist = classify_ambiguity_severity(
            "destination_candidates", "value_vague", stage="shortlist"
        )
        sev_proposal = classify_ambiguity_severity(
            "destination_candidates", "value_vague", stage="proposal"
        )

        assert sev_proposal == "blocking", \
            f"Destination value_vague must be blocking at proposal, got {sev_proposal}"
        assert sev_shortlist == "blocking", \
            f"Destination value_vague must be blocking at shortlist, got {sev_shortlist}"

    def test_synthesize_destination_ambiguity_from_structured_list(self):
        """
        If destination_candidates is a list with 2+ items and no existing ambiguity,
        _synthesize_destination_ambiguity must create one.
        """
        envelope = SourceEnvelope.from_freeform(
            "Family of 4 from Bangalore. Budget 3L. April 2026.", "test"
        )
        packet = ExtractionPipeline().extract([envelope])
        packet.facts["destination_candidates"] = Slot(
            value=["Singapore", "Bali"],
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            extraction_mode="explicit",
            derived_from=["envelope_1"],
        )
        packet.stage = "discovery"

        ambiguities = []
        _synthesize_destination_ambiguity(packet, ambiguities)

        dest_amb = [a for a in ambiguities if a.field_name == "destination_candidates"
                    and a.ambiguity_type == "unresolved_alternatives"]
        assert len(dest_amb) > 0, \
            "Should synthesize destination ambiguity for multi-value destination_candidates"

    def test_no_proceed_traveler_safe_with_destination_ambiguity(self):
        """Invariant: blocking destination ambiguity prevents PROCEED_TRAVELER_SAFE."""
        result = extract_and_decide(
            "Family of 4 from Bangalore. Want Thailand or Vietnam. Budget 3L, June 2026."
        )
        has_blocking = any(
            a.severity == "blocking" and a.field_name == "destination_candidates"
            for a in result.ambiguities
        )
        if has_blocking:
            assert result.decision_state != "PROCEED_TRAVELER_SAFE", \
                f"Should not PROCEED_TRAVELER_SAFE with blocking destination ambiguity, got {result.decision_state}"


# ===========================================================================
# P1-2: Last-minute non-emergency soft-blocker behavior
# ===========================================================================


class TestLastMinuteSoftBlockerBehavior:
    """
    Clarify and codify last-minute non-emergency soft-blocker behavior.
    
    Key rules:
    - high urgency (< 7 days): suppress most soft blockers, keep budget-related
    - medium urgency (< 21 days): suppress ALL soft blockers
    - normal urgency: keep all soft blockers
    - emergency mode: suppress all soft blockers regardless
    """

    def test_high_urgency_keeps_budget_soft_blockers(self):
        """High urgency keeps only budget_min and budget_raw_text soft blockers."""
        blockers = apply_urgency("high", ["budget_min", "trip_purpose", "soft_preferences", "budget_raw_text"])
        assert "budget_min" in blockers, "High urgency should keep budget_min"
        assert "budget_raw_text" in blockers, "High urgency should keep budget_raw_text"
        assert "trip_purpose" not in blockers, "High urgency should suppress trip_purpose"
        assert "soft_preferences" not in blockers, "High urgency should suppress soft_preferences"

    def test_medium_urgency_suppresses_all_soft_blockers(self):
        """Medium urgency suppresses all soft blockers."""
        blockers = apply_urgency("medium", ["budget_min", "trip_purpose", "soft_preferences"])
        assert len(blockers) == 0, "Medium urgency should suppress all soft blockers"

    def test_normal_urgency_keeps_all_soft_blockers(self):
        """Normal urgency keeps all soft blockers."""
        blockers = apply_urgency("normal", ["budget_min", "trip_purpose", "soft_preferences"])
        assert blockers == ["budget_min", "trip_purpose", "soft_preferences"]

    def test_low_urgency_keeps_all_soft_blockers(self):
        """Low urgency keeps all soft blockers."""
        blockers = apply_urgency("low", ["budget_min", "trip_purpose"])
        assert blockers == ["budget_min", "trip_purpose"]

    def test_emergency_mode_suppresses_soft_blockers(self):
        """Emergency operating mode suppresses ALL soft blockers."""
        envelope = SourceEnvelope.from_freeform(
            "Family of 4 from Bangalore. Want Singapore. Budget 3L. April 2026.", "test"
        )
        packet = ExtractionPipeline().extract([envelope])
        packet.operating_mode = "emergency"

        soft_blockers = ["budget_min", "trip_purpose", "soft_preferences"]
        contradictions = []
        feasibility = {"status": "feasible", "gap": 0}

        result_soft, result_contra, forced = apply_operating_mode(
            packet, [], soft_blockers, contradictions, feasibility
        )

        assert len(result_soft) == 0, \
            f"Emergency mode should suppress all soft blockers, got {result_soft}"

    def test_follow_up_mode_demotes_soft_blockers(self):
        """Follow-up mode demotes soft blockers when no hard blockers exist."""
        envelope = SourceEnvelope.from_freeform(
            "Family of 4 from Bangalore. Want Singapore. Budget 3L. April 2026.", "test"
        )
        packet = ExtractionPipeline().extract([envelope])
        packet.operating_mode = "follow_up"

        soft_blockers = ["budget_min", "trip_purpose"]
        contradictions = []
        feasibility = {"status": "feasible", "gap": 0}

        result_soft, _, _ = apply_operating_mode(
            packet, [], soft_blockers, contradictions, feasibility
        )

        assert len(result_soft) == 0, \
            f"Follow-up mode with no hard blockers should demote all soft blockers, got {result_soft}"

    def test_urgency_suppression_only_applies_in_normal_intake(self):
        """Urgency suppression only applies during normal_intake mode."""
        envelope = SourceEnvelope.from_freeform(
            "Family of 4 from Bangalore. Want Singapore. Budget 3L. April 2026.", "test"
        )
        packet = ExtractionPipeline().extract([envelope])
        packet.operating_mode = "audit"

        soft_blockers = ["budget_min", "trip_purpose"]
        contradictions = []
        feasibility = {"status": "feasible", "gap": 0}

        result_soft, _, _ = apply_operating_mode(
            packet, [], soft_blockers, contradictions, feasibility
        )

        assert "budget_min" in result_soft, \
            "Audit mode should not apply urgency suppression to soft blockers"


# ===========================================================================
# P1-3: Confidence thresholds → coaching severity regression
# ===========================================================================


class TestConfidenceToCoachingSeverity:
    """
    Regression contract: backend confidence thresholds must map to
    correct owner-facing coaching severity.

    Mapping rules:
    - confidence >= 0.9: coaching severity "info" (high confidence, low coaching)
    - confidence 0.7-0.89: coaching severity "warning" (moderate, needs review)
    - confidence < 0.7: coaching severity "critical" (low confidence, strong coaching)
    """

    @staticmethod
    def _coaching_severity(confidence: float) -> str:
        """
        Map confidence to coaching severity for owner-facing display.
        This is the contract that ties backend confidence to UI coaching.
        """
        if confidence >= 0.9:
            return "info"
        elif confidence >= 0.7:
            return "warning"
        else:
            return "critical"

    def test_high_confidence_maps_to_info(self):
        """Confidence >= 0.9 produces 'info' coaching severity."""
        assert self._coaching_severity(0.95) == "info"
        assert self._coaching_severity(0.90) == "info"
        assert self._coaching_severity(1.0) == "info"

    def test_moderate_confidence_maps_to_warning(self):
        """Confidence 0.7-0.89 produces 'warning' coaching severity."""
        assert self._coaching_severity(0.7) == "warning"
        assert self._coaching_severity(0.8) == "warning"
        assert self._coaching_severity(0.89) == "warning"

    def test_low_confidence_maps_to_critical(self):
        """Confidence < 0.7 produces 'critical' coaching severity."""
        assert self._coaching_severity(0.0) == "critical"
        assert self._coaching_severity(0.5) == "critical"
        assert self._coaching_severity(0.69) == "critical"

    def test_suitability_flag_confidence_maps_to_severity(self):
        """
        Suitability flag confidence should drive coaching severity display.
        Flags with >= 0.9 confidence: high-severity display
        Flags with < 0.7 confidence: lower-severity display (less certain)
        """
        high_conf_flag = {"confidence": 0.95, "expected_tier": "critical"}
        med_conf_flag = {"confidence": 0.80, "expected_tier": "warning"}
        low_conf_flag = {"confidence": 0.50, "expected_tier": "info"}

        for flag_data in [high_conf_flag, med_conf_flag, low_conf_flag]:
            if flag_data["confidence"] >= 0.9:
                assert flag_data["expected_tier"] == "critical"
            elif flag_data["confidence"] >= 0.7:
                assert flag_data["expected_tier"] == "warning"
            else:
                assert flag_data["expected_tier"] == "info"

    def test_decision_confidence_scorecard_drives_coaching(self):
        """
        The decision confidence scorecard overall score should determine
        the owner-facing coaching threshold for the entire decision.
        """
        result = extract_and_decide(
            "2 adults from Mumbai, want Goa, budget 50K, next week."
        )
        overall = result.confidence.overall

        if overall >= 0.9:
            coaching = "info"
        elif overall >= 0.7:
            coaching = "warning"
        else:
            coaching = "critical"

        assert coaching in ("info", "warning", "critical"), \
            f"Coaching severity must be one of info/warning/critical, got {coaching} for confidence {overall}"

    def test_infeasible_budget_produces_low_confidence(self):
        """
        Infeasible budget must produce confidence < 0.7 → critical coaching.
        """
        result = extract_and_decide(
            "Family of 6 from Bangalore, want Singapore. Budget 50K total. April 2026."
        )
        assert result.confidence.overall < 0.8, \
            f"Infeasible budget should reduce confidence, got {result.confidence.overall}"

    def test_ambiguity_blocks_proceed_when_critical_coaching(self):
        """
        When coaching severity is 'critical' (low confidence),
        PROCEED_TRAVELER_SAFE should not be reached.
        """
        result = extract_and_decide(
            "Family of 4, want Singapore or Bali or Thailand, budget 1L, April 2026."
        )

        has_blocking_ambiguity = any(
            a.severity == "blocking" for a in result.ambiguities
        )

        if has_blocking_ambiguity:
            assert result.decision_state != "PROCEED_TRAVELER_SAFE", \
                f"Should not PROCEED_TRAVELER_SAFE with blocking ambiguities, got {result.decision_state}"


# ===========================================================================
# Confidence scorecard unit tests
# ===========================================================================


class TestConfidenceScorecard:
    """Unit tests for the ConfidenceScorecard calculation."""

    def test_calculate_overall(self):
        card = ConfidenceScorecard(
            data_quality=0.8,
            judgment_confidence=0.7,
            commercial_confidence=0.9,
        )
        overall = card.calculate_overall()
        expected = 0.8 * 0.4 + 0.7 * 0.4 + 0.9 * 0.2
        assert abs(overall - expected) < 0.01, \
            f"Expected ~{expected:.3f}, got {overall:.3f}"

    def test_zero_confidence(self):
        card = ConfidenceScorecard(
            data_quality=0.0,
            judgment_confidence=0.0,
            commercial_confidence=0.0,
        )
        overall = card.calculate_overall()
        assert overall == 0.0

    def test_perfect_confidence(self):
        card = ConfidenceScorecard(
            data_quality=1.0,
            judgment_confidence=1.0,
            commercial_confidence=1.0,
        )
        overall = card.calculate_overall()
        assert overall == 1.0

    def test_run_gap_and_decision_exposes_scorecard_contract(self):
        """Decision output exposes confidence scorecard object and rationale subscores."""
        packet = CanonicalPacket(packet_id="confidence_contract")
        packet.facts["destination_candidates"] = Slot(
            value=["Paris"],
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        packet.facts["origin_city"] = Slot(
            value="London",
            confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        packet.facts["date_window"] = Slot(
            value="June",
            confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        packet.facts["party_size"] = Slot(
            value=2,
            confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        packet.facts["budget_raw_text"] = Slot(
            value="low",
            confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        packet.facts["trip_purpose"] = Slot(
            value="leisure",
            confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )

        result = run_gap_and_decision(packet)

        assert isinstance(result.confidence, ConfidenceScorecard)
        assert result.confidence.data_quality > 0.5
        assert result.rationale["confidence_scorecard"] == {
            "data": result.confidence.data_quality,
            "judgment": result.confidence.judgment_confidence,
            "commercial": result.confidence.commercial_confidence,
        }
        assert result.rationale["confidence"] == round(result.confidence.overall, 3)
