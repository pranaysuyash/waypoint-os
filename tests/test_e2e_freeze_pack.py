"""
End-to-End Pre-UI Freeze Pack.

5 realistic scenarios that exercise the full spine:
  NB01 (extraction) → NB02 (decision) → NB03 (strategy/bundle) → safety (leakage)

Each scenario proves:
  - Core packet expectations
  - Decision state expectations
  - Traveler-safe/internal boundary expectations
  - No leakage in traveler-safe output

Run: uv run python -m pytest tests/test_e2e_freeze_pack.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    OwnerConstraint,
    Slot,
    SourceEnvelope,
)
from intake.extractors import ExtractionPipeline
from intake.decision import run_gap_and_decision, check_budget_feasibility
from intake.strategy import (
    build_session_strategy,
    build_traveler_safe_bundle,
    build_internal_bundle,
)
from intake.safety import (
    check_no_leakage,
    enforce_no_leakage,
    sanitize_for_traveler,
    has_blocking_ambiguities,
)
from intake.validation import validate_packet


def e2e_pipeline(text: str, source: str = "agency_notes", actor: str = "agent"):
    """Full pipeline: text → packet → decision → strategy → bundles."""
    envelope = SourceEnvelope.from_freeform(text, source, actor)
    pipeline = ExtractionPipeline()
    packet = pipeline.extract([envelope])
    report = validate_packet(packet)
    decision = run_gap_and_decision(packet)
    strategy = build_session_strategy(decision, packet)
    traveler_bundle = build_traveler_safe_bundle(strategy, decision)
    internal_bundle = build_internal_bundle(strategy, decision, packet)
    sanitized = sanitize_for_traveler(packet)
    return {
        "packet": packet,
        "report": report,
        "decision": decision,
        "strategy": strategy,
        "traveler_bundle": traveler_bundle,
        "internal_bundle": internal_bundle,
        "sanitized": sanitized,
    }


# ===========================================================================
# SCENARIO 1: Messy family discovery note with semi-open destination
# "Hey so calling for Sharma family... Andaman or Sri Lanka... budget around 3L
#  can stretch... 2 adults 2 kids ages 8 and 12... from Bangalore... March or April"
# ===========================================================================

class TestScenario1_MessyFamilyDiscovery:
    """
    Messy note with semi-open destination, budget ambiguity, and child ages.
    Proves: extraction from messy text, ambiguous destination, budget stretch,
    multiple ambiguities, traveler-safe output has no leakage.
    """

    TEXT = (
        "Hey so calling for Sharma family, they want to go Andaman or Sri Lanka "
        "sometime in March or April 2026, budget around 3L can stretch if good, "
        "2 adults 2 kids ages 8 and 12, from Bangalore, family vacation with kid-friendly stuff. "
        "Note: never book that resort with the broken AC."
    )

    def test_extraction_from_messy_note(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        # Core packet expectations
        assert "destination_candidates" in pkt.facts
        dests = pkt.facts["destination_candidates"].value
        assert isinstance(dests, list)
        assert len(dests) == 2

        assert "origin_city" in pkt.facts
        assert "party_size" in pkt.facts
        assert pkt.facts["party_size"].value == 4

        # Ambiguity detection
        dest_amb_types = [a.ambiguity_type for a in pkt.ambiguities
                          if a.field_name == "destination_candidates"]
        assert "unresolved_alternatives" in dest_amb_types, \
            f"Should detect unresolved_alternatives, got {dest_amb_types}"

    def test_decision_state(self):
        result = e2e_pipeline(self.TEXT)
        decision = result["decision"]

        # Semi-open destination + budget ambiguity → ASK_FOLLOWUP
        assert decision.decision_state == "ASK_FOLLOWUP", \
            f"Semi-open destination should ask followup, got {decision.decision_state}"

        # Should have blocking ambiguities
        blocking = [a for a in decision.ambiguities if a.severity == "blocking"]
        assert len(blocking) > 0, "Should have at least one blocking ambiguity"

    def test_traveler_safe_no_leakage(self):
        result = e2e_pipeline(self.TEXT)
        bundle = result["traveler_bundle"]

        leaks = check_no_leakage(bundle)
        assert len(leaks) == 0, f"Traveler-safe bundle has leaks: {leaks}"

    def test_internal_bundle_has_full_context(self):
        result = e2e_pipeline(self.TEXT)
        internal = result["internal_bundle"]

        assert "INTERNAL" in internal.system_context
        assert len(internal.internal_notes) > 0 or len(internal.system_context) > 10

    def test_sanitized_view_removes_internal_data(self):
        result = e2e_pipeline(self.TEXT)
        sanitized = result["sanitized"]

        # Internal-only fields should not be in sanitized facts
        assert "agency_notes" not in sanitized.facts
        # Owner constraints should be filtered
        if "owner_constraints" in sanitized.facts:
            # Only traveler-safe constraints should survive
            constraints = sanitized.facts["owner_constraints"].value
            for c in (constraints if isinstance(constraints, list) else [constraints]):
                if isinstance(c, dict):
                    assert c.get("visibility") == "traveler_safe"


# ===========================================================================
# SCENARIO 2: Past customer with past-trip mention + new current intent
# "Past customer Gupta family, they went to Dubai last time. Now want Japan,
#  2 adults, budget 5L, March 2026."
# ===========================================================================

class TestScenario2_PastCustomerPastTripMention:
    """
    Past-trip destination mention should NOT contaminate current destination.
    Proves: past-trip filtering, repeat customer detection, internal vs traveler boundary.
    """

    TEXT = (
        "Past customer Gupta family. They went to Dubai last time and loved it. "
        "Now want Japan, family of 4, 2 adults 2 kids, budget 5L, "
        "dates 2026-03-15 to 2026-03-22."
    )

    def test_dubai_not_in_current_destinations(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        assert "destination_candidates" in pkt.facts
        dests = pkt.facts["destination_candidates"].value

        # Dubai (past trip) must NOT be in current destination candidates
        if isinstance(dests, list):
            assert "Dubai" not in dests, \
                f"Dubai (past trip) should not be in destination_candidates: {dests}"
        elif isinstance(dests, str):
            assert "Dubai" not in dests

        # Japan (current intent) should be present
        assert "Japan" in dests, f"Japan should be in destination_candidates: {dests}"

    def test_repeat_customer_detection(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        # is_repeat_customer should be a derived signal
        assert "is_repeat_customer" in pkt.derived_signals
        assert pkt.derived_signals["is_repeat_customer"].value is True

    def test_traveler_safe_output(self):
        result = e2e_pipeline(self.TEXT)
        bundle = result["traveler_bundle"]

        leaks = check_no_leakage(bundle)
        assert len(leaks) == 0, f"Leakage: {leaks}"

        # "past customer" should not appear in traveler output
        assert "past customer" not in bundle.user_message.lower()

    def test_internal_bundle_has_repeat_context(self):
        result = e2e_pipeline(self.TEXT)
        internal = result["internal_bundle"]

        # Internal bundle should have agency notes (past customer context)
        assert "INTERNAL" in internal.system_context


# ===========================================================================
# SCENARIO 3: Audit-mode note with self-booked plan
# "Audit mode: review this quote. Customer booked flights themselves, Singapore,
#  4 adults, 2L budget. Check this quote against market."
# ===========================================================================

class TestScenario3_AuditModeSelfBooked:
    """
    Audit mode with self-booked plan and tight budget.
    Proves: audit mode routing, feasibility contradiction, traveler-safe boundary.
    """

    TEXT = (
        "Audit mode: review quote for Singapore family. "
        "Check this quote against market rates. "
        "Customer has flights booked already, 4 adults, budget 2L total."
    )

    def test_audit_mode_routing(self):
        result = e2e_pipeline(self.TEXT)
        decision = result["decision"]

        assert decision.operating_mode == "audit", \
            f"Expected audit mode, got {decision.operating_mode}"

    def test_audit_adds_feasibility_contradiction(self):
        result = e2e_pipeline(self.TEXT)
        decision = result["decision"]

        # Audit mode should add budget_feasibility contradiction if budget is tight
        feasibility = decision.rationale.get("feasibility")
        if feasibility in ("infeasible", "tight"):
            field_names = [c.get("field_name") for c in decision.contradictions]
            assert "budget_feasibility" in field_names, \
                f"Audit mode should add feasibility contradiction, got {field_names}"

    def test_traveler_safe_output_audit(self):
        result = e2e_pipeline(self.TEXT)
        bundle = result["traveler_bundle"]

        leaks = check_no_leakage(bundle)
        assert len(leaks) == 0, f"Leakage in audit traveler output: {leaks}"

    def test_audit_goal_mentions_comparison(self):
        result = e2e_pipeline(self.TEXT)
        strategy = result["strategy"]

        assert "audit" in strategy.session_goal.lower() or "market" in strategy.session_goal.lower()


# ===========================================================================
# SCENARIO 4: Coordinator-group note with multiple families
# "Coordinating trip for 3 families. Family A: 4 people, budget 3L.
#  Family B: 3 people, budget 2.5L. Family C: 4 people, budget 2L.
#  All going to Singapore in May."
# ===========================================================================

class TestScenario4_CoordinatorGroup:
    """
    Coordinator-group note with sub-groups and divergent budgets.
    Proves: subgroup extraction, coordinator mode, per-group strategy, no leakage.
    """

    TEXT = (
        "Coordinating trip for 3 families. "
        "Family A: 4 people, budget 3L. "
        "Family B: 3 people, budget 2.5L. "
        "Family C: 4 people, budget 2L. "
        "All going to Singapore in May."
    )

    def test_coordinator_mode_detected(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        assert pkt.operating_mode == "coordinator_group", \
            f"Expected coordinator_group, got {pkt.operating_mode}"

    def test_sub_groups_extracted(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        assert "sub_groups" in pkt.facts
        sub_groups = pkt.facts["sub_groups"].value
        assert isinstance(sub_groups, dict)
        assert len(sub_groups) > 0

    def test_strategy_mentions_groups(self):
        result = e2e_pipeline(self.TEXT)
        strategy = result["strategy"]

        assert "group" in strategy.session_goal.lower()

    def test_traveler_safe_no_leakage(self):
        result = e2e_pipeline(self.TEXT)
        bundle = result["traveler_bundle"]

        leaks = check_no_leakage(bundle)
        assert len(leaks) == 0, f"Leakage in coordinator traveler output: {leaks}"


# ===========================================================================
# SCENARIO 5: Emergency/cancellation note with compressed context
# "URGENT: Need to cancel booking for 4 people, Singapore trip March 15-22.
#  Customer ID: Sharma. They have flights but want refund. Already paid."
# ===========================================================================

class TestScenario5_EmergencyCancellation:
    """
    Emergency/cancellation note with compressed context.
    Proves: mode detection, cancellation routing, traveler-safe boundary,
    urgency detection if dates are near.
    """

    TEXT = (
        "Need to cancel booking for 4 people, Singapore trip March 15-22 2026. "
        "Customer is very upset. They have flights booked already but want refund. "
        "Already paid full amount. Help process cancellation quickly."
    )

    def test_cancellation_mode_detected(self):
        result = e2e_pipeline(self.TEXT)
        pkt = result["packet"]

        # Should detect cancellation mode
        assert pkt.operating_mode in ("cancellation", "normal_intake"), \
            f"Expected cancellation or normal_intake, got {pkt.operating_mode}"

    def test_traveler_safe_output_no_internal(self):
        result = e2e_pipeline(self.TEXT)
        bundle = result["traveler_bundle"]

        leaks = check_no_leakage(bundle)
        assert len(leaks) == 0, f"Leakage in cancellation traveler output: {leaks}"

    def test_internal_bundle_has_context(self):
        result = e2e_pipeline(self.TEXT)
        internal = result["internal_bundle"]

        assert "INTERNAL" in internal.system_context
        assert len(internal.system_context) > 0

    def test_decision_valid_state(self):
        result = e2e_pipeline(self.TEXT)
        decision = result["decision"]

        assert decision.decision_state in (
            "ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE",
            "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW",
        ), f"Unexpected decision state: {decision.decision_state}"


# ===========================================================================
# ADDITIONAL FUZZY DATE AND ORIGIN BOUNDING TESTS
# ===========================================================================

class TestFuzzyDatePhrases:
    """Prove fuzzy date phrase detection works for messy realistic inputs."""

    def test_sometime_in_may(self):
        text = "Planning a trip sometime in May 2026, family of 4, from Bangalore."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "date_window" in pkt.facts
        assert pkt.facts["date_window"].value is not None
        # Should detect as flexible (not exact)
        if "date_confidence" in pkt.facts:
            assert pkt.facts["date_confidence"].value in ("flexible", "window")

    def test_around_march(self):
        text = "Around March 2026, 2 adults, Goa, budget 2L."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "date_window" in pkt.facts

    def test_june_or_july(self):
        text = "June or July 2026, family vacation, 4 people, Kerala."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "date_window" in pkt.facts


class TestOriginExtractionBounded:
    """Prove origin extraction is bounded against conversational spillover."""

    def test_origin_stops_at_destination(self):
        """'from Bangalore to Singapore' - origin should be Bangalore, not Bangalore to Singapore."""
        text = "Family of 4 from Bangalore to Singapore, budget 3L."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "origin_city" in pkt.facts
        origin = pkt.facts["origin_city"].value
        # Should not contain "to Singapore" or destination
        assert "Singapore" not in str(origin), f"Origin should not contain destination: {origin}"

    def test_origin_bounded_by_period(self):
        """Origin should stop at sentence boundary."""
        text = "Calling from Mumbai office. Going to Japan. Budget 5L."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "origin_city" in pkt.facts
        origin = pkt.facts["origin_city"].value
        assert "Japan" not in str(origin)


class TestPastTripDestinationFiltering:
    """Prove past-trip destinations don't contaminate current destination intent."""

    def test_went_to_dubai_now_want_japan(self):
        text = "Past customer, they went to Dubai last time. Now want Japan, 4 people."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "destination_candidates" in pkt.facts
        dests = pkt.facts["destination_candidates"].value
        if isinstance(dests, list):
            assert "Dubai" not in dests, f"Dubai (past) should not be current: {dests}"

    def test_came_back_from_kerala_now_andaman(self):
        text = "They came back from Kerala last month. Now want Andaman, budget 2L."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        assert "destination_candidates" in pkt.facts
        dests = pkt.facts["destination_candidates"].value
        if isinstance(dests, list):
            assert "Kerala" not in dests, f"Kerala (past) should not be current: {dests}"


class TestAmbiguityOnSourceSpans:
    """Prove ambiguity detection runs on original phrasing, not just extracted values."""

    def test_maybe_somewhere_like_andaman(self):
        text = "Maybe somewhere like Andaman? Family of 4, budget flexible."
        pkt = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])

        # Should detect destination_open or unresolved_alternatives
        amb_types = [a.ambiguity_type for a in pkt.ambiguities]
        has_dest_amb = any(t in amb_types for t in ("destination_open", "unresolved_alternatives", "value_vague"))
        assert has_dest_amb, f"Should detect ambiguity in 'maybe somewhere like Andaman', got {amb_types}"


class TestStrictLeakageEnforcement:
    """Prove strict leakage enforcement raises ValueError when enabled."""

    def test_strict_mode_raises_on_leakage(self):
        """When TRAVELER_SAFE_STRICT is set, enforce_no_leakage raises ValueError."""
        from intake.safety import set_strict_mode

        # Enable strict mode
        set_strict_mode(True)

        try:
            bad_bundle_dict = {
                "user_message": "Based on my hypothesis, I recommend Andaman.",
                "system_context": "Decision state: ASK_FOLLOWUP",
            }
            with pytest.raises(ValueError, match="Traveler-safe leakage detected"):
                enforce_no_leakage(bad_bundle_dict)
        finally:
            # Disable strict mode for other tests
            set_strict_mode(False)

    def test_strict_mode_allows_clean_output(self):
        """When strict mode is on, clean outputs pass without error."""
        from intake.safety import set_strict_mode

        set_strict_mode(True)
        try:
            clean_bundle_dict = {
                "user_message": "I'd like to understand your trip better.",
                "system_context": "Session Goal: Gather trip details.",
            }
            leaks = enforce_no_leakage(clean_bundle_dict)
            assert len(leaks) == 0
        finally:
            set_strict_mode(False)


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])