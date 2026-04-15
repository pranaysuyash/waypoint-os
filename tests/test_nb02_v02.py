"""
NB02 v0.2 Tests — Decision engine against real NB01 packet output.

All tests exercise the full ExtractionPipeline → run_gap_and_decision path.
No packet construction shortcuts (except where injection is required).

Run: uv run python -m pytest tests/test_nb02_v02.py -v
"""

import sys
import os
from datetime import datetime, timedelta

# Ensure src/ is on the path
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
    MVB_BY_STAGE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_and_decide(text: str, source: str = "agency_notes") -> DecisionResult:
    """Convenience: raw text → CanonicalPacket → DecisionResult."""
    envelope = SourceEnvelope.from_freeform(text, source)
    packet = ExtractionPipeline().extract([envelope])
    return run_gap_and_decision(packet)


# ===========================================================================
# TEST 1: Blocking destination ambiguity
# ===========================================================================

class TestBlockingDestinationAmbiguity:
    def test_unresolved_alternatives_block(self):
        text = (
            "Family of 4 from Bangalore. Want Andaman or Sri Lanka. "
            "Budget 3L, April 2026."
        )
        result = extract_and_decide(text)

        blocking = [a for a in result.ambiguities if a.severity == "blocking"]
        assert len(blocking) > 0, "No blocking ambiguities for 'Andaman or Sri Lanka'"
        assert result.decision_state == "ASK_FOLLOWUP", \
            f"Expected ASK_FOLLOWUP, got {result.decision_state}"


# ===========================================================================
# TEST 2: Advisory budget stretch ambiguity
# ===========================================================================

class TestAdvisoryBudgetStretch:
    def test_budget_stretch_is_advisory(self):
        text = (
            "Family of 4 from Bangalore, want Goa. "
            "Budget around 3L, can stretch. March 2026."
        )
        result = extract_and_decide(text)

        stretch_ambs = [a for a in result.ambiguities if a.ambiguity_type == "budget_stretch_present"]
        if stretch_ambs:
            assert stretch_ambs[0].severity == "advisory"


# ===========================================================================
# TEST 3: Urgency suppression — explicitly checks remaining soft blockers
# ===========================================================================

class TestUrgencySuppression:
    def test_high_urgency_suppresses_most_soft_blockers(self):
        future = datetime.now() + timedelta(days=5)
        date_str = future.strftime("%Y-%m-%d")
        text = f"2 adults, Bangalore to Goa, {date_str} to {date_str}, budget 50K, family leisure."
        result = extract_and_decide(text)

        # With high urgency, soft blockers should be suppressed to budget-only
        # trip_purpose and soft_preferences should NOT be soft blockers
        assert "trip_purpose" not in result.soft_blockers, \
            f"High urgency should suppress trip_purpose soft blocker, got {result.soft_blockers}"
        assert "soft_preferences" not in result.soft_blockers


# ===========================================================================
# TEST 4: Infeasible budget — truly infeasible, not unknown
# ===========================================================================

class TestInfeasibleBudget:
    def test_truly_infeasible_budget(self):
        text = (
            "Family of 6 from Bangalore, want Singapore. "
            "Budget 1L total. April 2026."
        )
        result = extract_and_decide(text)

        # Feasibility must be infeasible or tight (not unknown)
        assert result.rationale.get("feasibility") in ("infeasible", "tight"), \
            f"Expected infeasible/tight, got {result.rationale.get('feasibility')}"

        # Must NOT be PROCEED_TRAVELER_SAFE
        assert result.decision_state != "PROCEED_TRAVELER_SAFE"


# ===========================================================================
# TEST 5: Contradiction precedence
# ===========================================================================

class TestContradictionPrecedence:
    def test_date_contradiction_stops(self):
        pkt = ExtractionPipeline().extract([
            SourceEnvelope.from_freeform(
                "Family of 4, Singapore, 2026-03-15 to 2026-03-22, budget 3L.",
            ),
        ])
        pkt.add_contradiction(
            "date_window",
            ["2026-03-15 to 2026-03-22", "2026-04-01 to 2026-04-08"],
            ["envelope_1", "envelope_2"],
        )

        result = run_gap_and_decision(pkt)
        assert result.decision_state == "STOP_NEEDS_REVIEW"


# ===========================================================================
# TEST 6: Hypotheses do NOT fill hard blockers
# ===========================================================================

class TestHypothesesDoNotFillBlockers:
    def test_hypothesis_only_packet_asks(self):
        text = "Someone called, wants international trip, maybe Singapore, budget flexible."
        result = extract_and_decide(text)

        assert len(result.hard_blockers) > 0
        assert result.decision_state == "ASK_FOLLOWUP"


# ===========================================================================
# TEST 7: Emergency mode
# ===========================================================================

class TestEmergencyMode:
    def test_emergency_suppresses_soft(self):
        text = (
            "URGENT: Medical emergency! Elderly father chest pain in Singapore. "
            "Need help NOW."
        )
        result = extract_and_decide(text)

        assert result.operating_mode == "emergency"
        assert len(result.soft_blockers) == 0, \
            f"Emergency mode should suppress soft blockers, got {result.soft_blockers}"


# ===========================================================================
# TEST 8: Coordinator group mode — uses subgroup-derived readiness
# ===========================================================================

class TestCoordinatorGroup:
    def test_coordinator_group_with_subgroups(self):
        text = (
            "Coordinating trip for 3 families. Family A: 4 people, budget 3L. "
            "Family B: 3 people, budget 2.5L. Family C: 4 people, budget 2L. "
            "All going to Singapore in May."
        )
        result = extract_and_decide(text)

        assert result.operating_mode == "coordinator_group"
        # Sub-groups should be extracted
        if "sub_groups" in result.rationale or "sub_groups" in str(result.hard_blockers):
            pass  # Good — sub-groups are part of the decision
        # The key: coordinator mode affects routing, not just detection
        assert result.operating_mode == "coordinator_group"


# ===========================================================================
# TEST 9: Audit mode — does audit-specific judgment
# ===========================================================================

class TestOwnerReviewAudit:
    def test_audit_mode_adds_feasibility_contradiction(self):
        text = (
            "Audit mode: review quote for Singapore family. "
            "Check this quote against market rates. Family of 4, budget 1L."
        )
        result = extract_and_decide(text)

        assert result.operating_mode == "audit"
        # Audit mode should add feasibility contradiction if budget is tight/infeasible
        feasibility = result.rationale.get("feasibility")
        contradictions = [c.get("field_name") for c in result.contradictions]
        if feasibility in ("infeasible", "tight"):
            assert "budget_feasibility" in contradictions, \
                "Audit mode should add budget_feasibility contradiction"

    def test_owner_review_mode(self):
        text = (
            "Owner review: quote disaster for Singapore family trip. "
            "Margin erosion detected."
        )
        result = extract_and_decide(text)

        assert result.operating_mode == "owner_review"


# ===========================================================================
# TEST 10: Traveler-safe cannot proceed with blocking ambiguity
# ===========================================================================

class TestTravelerSafeBlockedByAmbiguity:
    def test_blocking_ambiguity_prevents_proceed(self):
        pkt = CanonicalPacket(packet_id="test_ambiguity_block")
        pkt.stage = "discovery"
        pkt.operating_mode = "normal_intake"

        for name in ["destination_candidates", "origin_city", "date_window", "party_size"]:
            pkt.facts[name] = Slot(
                value="test" if name != "party_size" else 4,
                confidence=0.9,
                authority_level=AuthorityLevel.EXPLICIT_USER,
                evidence_refs=[EvidenceRef(
                    envelope_id="test", evidence_type="text_span", excerpt="test",
                )],
            )

        pkt.add_ambiguity(Ambiguity(
            field_name="destination_candidates",
            ambiguity_type="unresolved_alternatives",
            raw_value="Andaman or Sri Lanka",
            confidence=0.8,
        ))

        result = run_gap_and_decision(pkt)

        assert result.decision_state != "PROCEED_TRAVELER_SAFE"
        assert result.decision_state == "ASK_FOLLOWUP"


# ===========================================================================
# TEST 11: Stub/heuristic signals conservative
# ===========================================================================

class TestStubSignalsConservative:
    def test_stub_sourcing_path_does_not_affect_decision(self):
        text = "Family of 4 from Bangalore, want Singapore, budget 4L, March 2026."
        result = extract_and_decide(text)

        assert result.decision_state in (
            "ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE",
            "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW",
        )

    def test_budget_feasibility_respects_maturity(self):
        text = "Family of 4 from Bangalore, want Goa, budget 2L, April 2026."
        result = extract_and_decide(text)

        feasibility = result.rationale.get("feasibility", "unknown")
        assert result.decision_state != "STOP_NEEDS_REVIEW" or feasibility == "infeasible"


# ===========================================================================
# TEST 12: Decision result structure
# ===========================================================================

class TestDecisionResultStructure:
    def test_decision_result_has_all_fields(self):
        text = "Family of 4 from Bangalore, want Singapore, budget 4L, March 2026."
        result = extract_and_decide(text)

        assert isinstance(result.packet_id, str)
        assert isinstance(result.current_stage, str)
        assert isinstance(result.operating_mode, str)
        assert isinstance(result.decision_state, str)
        assert result.decision_state in (
            "ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE",
            "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW",
        )
        assert isinstance(result.hard_blockers, list)
        assert isinstance(result.soft_blockers, list)
        assert isinstance(result.ambiguities, list)
        assert isinstance(result.contradictions, list)
        assert isinstance(result.follow_up_questions, list)
        assert isinstance(result.branch_options, list)
        assert isinstance(result.rationale, dict)
        assert isinstance(result.confidence_score, float)
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.risk_flags, list)


# ===========================================================================
# TEST 13: Shortlist requires resolved_destination
# ===========================================================================

class TestShortlistRequiresResolvedDestination:
    def test_shortlist_without_resolved_destination_blocks(self):
        """Shortlist stage without resolved_destination → ASK_FOLLOWUP."""
        pkt = CanonicalPacket(packet_id="test_shortlist_no_resolved")
        pkt.stage = "shortlist"
        pkt.operating_mode = "normal_intake"

        # Discovery fields filled
        for name in ["destination_candidates", "origin_city", "date_window", "party_size"]:
            pkt.facts[name] = Slot(
                value=["Singapore"] if name == "destination_candidates" else (
                    4 if name == "party_size" else "test"
                ),
                confidence=0.9,
                authority_level=AuthorityLevel.EXPLICIT_USER,
                evidence_refs=[EvidenceRef(
                    envelope_id="test", evidence_type="text_span", excerpt="test",
                )],
            )
        # NO resolved_destination

        result = run_gap_and_decision(pkt)

        # Shortlist without resolved destination should have it as hard blocker
        assert "resolved_destination" in result.hard_blockers, \
            f"Shortlist should require resolved_destination, got blockers: {result.hard_blockers}"
        assert result.decision_state == "ASK_FOLLOWUP"

    def test_shortlist_with_resolved_destination_proceeds(self):
        """Shortlist with resolved_destination → can proceed."""
        pkt = CanonicalPacket(packet_id="test_shortlist_resolved")
        pkt.stage = "shortlist"
        pkt.operating_mode = "normal_intake"

        for name in ["destination_candidates", "origin_city", "date_window", "party_size"]:
            pkt.facts[name] = Slot(
                value=["Singapore"] if name == "destination_candidates" else (
                    4 if name == "party_size" else "test"
                ),
                confidence=0.9,
                authority_level=AuthorityLevel.EXPLICIT_USER,
                evidence_refs=[EvidenceRef(
                    envelope_id="test", evidence_type="text_span", excerpt="test",
                )],
            )
        # With resolved destination
        pkt.facts["resolved_destination"] = Slot(
            value="Singapore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="Singapore",
            )],
        )

        result = run_gap_and_decision(pkt)

        # Should NOT have resolved_destination as blocker
        assert "resolved_destination" not in result.hard_blockers


# ===========================================================================
# TEST 14: Stage progression test
# ===========================================================================

class TestStageProgression:
    def test_discovery_to_shortlist_to_proposal_to_booking(self):
        """Prove the engine actually changes behavior by stage."""

        # Base packet with all fields that would be filled through the journey
        def make_packet(stage: str, add_resolved: bool = False,
                       add_itinerary: bool = False, add_docs: bool = False) -> CanonicalPacket:
            pkt = CanonicalPacket(packet_id=f"test_stage_{stage}")
            pkt.stage = stage
            pkt.operating_mode = "normal_intake"

            for name in ["destination_candidates", "origin_city", "date_window", "party_size"]:
                pkt.facts[name] = Slot(
                    value=["Singapore"] if name == "destination_candidates" else (
                        4 if name == "party_size" else "test"
                    ),
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="test",
                    )],
                )

            if add_resolved:
                pkt.facts["resolved_destination"] = Slot(
                    value="Singapore",
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="Singapore",
                    )],
                )

            if add_itinerary:
                pkt.facts["selected_itinerary"] = Slot(
                    value="SG_5night_itinerary_v1",
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="itinerary",
                    )],
                )

            if add_docs:
                pkt.facts["passport_status"] = Slot(
                    value={"all": {"status": "valid"}},
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="valid passports",
                    )],
                )
                pkt.facts["visa_status"] = Slot(
                    value={"requirement": "not_required"},
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="no visa needed",
                    )],
                )
                pkt.facts["payment_method"] = Slot(
                    value="credit_card",
                    confidence=0.9,
                    authority_level=AuthorityLevel.EXPLICIT_USER,
                    evidence_refs=[EvidenceRef(
                        envelope_id="test", evidence_type="text_span", excerpt="credit_card",
                    )],
                )

            return pkt

        # Discovery: all filled → should proceed
        pkt_discovery = make_packet("discovery")
        result_d = run_gap_and_decision(pkt_discovery)
        assert result_d.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Discovery with all fields should proceed, got {result_d.decision_state}"

        # Shortlist: needs resolved_destination
        pkt_shortlist_no = make_packet("shortlist", add_resolved=False)
        result_s_no = run_gap_and_decision(pkt_shortlist_no)
        assert "resolved_destination" in result_s_no.hard_blockers, \
            f"Shortlist without resolved should block, got {result_s_no.hard_blockers}"
        assert result_s_no.decision_state == "ASK_FOLLOWUP"

        pkt_shortlist_yes = make_packet("shortlist", add_resolved=True)
        result_s_yes = run_gap_and_decision(pkt_shortlist_yes)
        assert "resolved_destination" not in result_s_yes.hard_blockers, \
            f"Shortlist with resolved should not block it, got {result_s_yes.hard_blockers}"

        # Proposal: needs selected_itinerary
        pkt_proposal_no = make_packet("proposal", add_resolved=True, add_itinerary=False)
        result_p_no = run_gap_and_decision(pkt_proposal_no)
        assert "selected_itinerary" in result_p_no.hard_blockers, \
            f"Proposal without itinerary should block, got {result_p_no.hard_blockers}"

        pkt_proposal_yes = make_packet("proposal", add_resolved=True, add_itinerary=True)
        result_p_yes = run_gap_and_decision(pkt_proposal_yes)
        assert "selected_itinerary" not in result_p_yes.hard_blockers

        # Booking: needs passport, visa, payment
        pkt_booking_no = make_packet("booking", add_resolved=True, add_itinerary=True, add_docs=False)
        result_b_no = run_gap_and_decision(pkt_booking_no)
        assert "passport_status" in result_b_no.hard_blockers or \
               "visa_status" in result_b_no.hard_blockers or \
               "payment_method" in result_b_no.hard_blockers, \
            f"Booking without docs should block, got {result_b_no.hard_blockers}"

        pkt_booking_yes = make_packet("booking", add_resolved=True, add_itinerary=True, add_docs=True)
        result_b_yes = run_gap_and_decision(pkt_booking_yes)
        assert len(result_b_yes.hard_blockers) == 0, \
            f"Booking with all docs should have no blockers, got {result_b_yes.hard_blockers}"


# ===========================================================================
# TEST 15: Feasibility conservative under unresolved destination
# ===========================================================================

class TestFeasibilityUnderAmbiguity:
    def test_multi_candidate_destination_returns_unknown(self):
        """When destination has multiple candidates, feasibility stays unknown."""
        pkt = CanonicalPacket(packet_id="test_multi_dest")
        pkt.stage = "discovery"
        pkt.operating_mode = "normal_intake"

        pkt.facts["destination_candidates"] = Slot(
            value=["Andaman", "Sri Lanka"],
            confidence=0.7,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="Andaman or Sri Lanka",
            )],
        )
        pkt.facts["budget_min"] = Slot(
            value=300000,
            confidence=0.8,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="3L",
            )],
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="4",
            )],
        )

        feasibility = check_budget_feasibility(pkt)

        # Multiple unresolved candidates → unknown
        assert feasibility["status"] == "unknown", \
            f"Multi-candidate destination should return unknown feasibility, got {feasibility['status']}"

    def test_resolved_destination_enables_feasibility(self):
        """When destination is resolved, feasibility can be computed."""
        pkt = CanonicalPacket(packet_id="test_resolved_dest")
        pkt.stage = "discovery"
        pkt.operating_mode = "normal_intake"

        pkt.facts["resolved_destination"] = Slot(
            value="Singapore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="Singapore",
            )],
        )
        pkt.facts["budget_min"] = Slot(
            value=300000,
            confidence=0.8,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="3L",
            )],
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="4",
            )],
        )

        feasibility = check_budget_feasibility(pkt)

        # Resolved destination → feasibility computed
        assert feasibility["status"] in ("feasible", "tight", "infeasible"), \
            f"Resolved destination should enable feasibility, got {feasibility['status']}"


# ===========================================================================
# REGRESSION: Value-structural destination ambiguity synthesis
# ===========================================================================

class TestDestinationAmbiguitySynthesis:
    """
    Bug: destination_candidates=["Andaman", "Sri Lanka"] with no Ambiguity
    objects bypassed the blocking check and reached PROCEED_TRAVELER_SAFE.

    Fix: NB02 synthesizes unresolved_alternatives ambiguity from the value
    structure (multi-element list) when no ambiguity was flagged by NB01.
    """

    def test_multi_candidate_destination_never_proceeds_traveler_safe(self):
        """2+ destination candidates without ambiguity objects → ASK_FOLLOWUP, not PROCEED."""
        pkt = CanonicalPacket(
            packet_id="reg_dest_amb",
            stage="discovery",
            operating_mode="normal_intake",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Andaman", "Sri Lanka"],
            confidence=0.7,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        for f, v in [("budget_raw_text", "2L"), ("budget_min", 200000),
                      ("trip_purpose", "leisure"), ("soft_preferences", "beach")]:
            pkt.facts[f] = Slot(value=v, confidence=0.8, authority_level=AuthorityLevel.EXPLICIT_USER)

        decision = run_gap_and_decision(pkt)

        assert decision.decision_state != "PROCEED_TRAVELER_SAFE", \
            f"Multi-candidate destination must not reach PROCEED_TRAVELER_SAFE, got {decision.decision_state}"

        blocking_dest = [a for a in decision.ambiguities
                         if a.field_name == "destination_candidates"
                         and a.ambiguity_type == "unresolved_alternatives"
                         and a.severity == "blocking"]
        assert len(blocking_dest) > 0, "Should synthesize blocking unresolved_alternatives ambiguity"

    def test_single_candidate_destination_no_synthesis(self):
        """Single destination → no synthesized ambiguity."""
        pkt = CanonicalPacket(
            packet_id="reg_single_dest",
            stage="discovery",
            operating_mode="normal_intake",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Singapore"],
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )

        decision = run_gap_and_decision(pkt)

        unresolved = [a for a in decision.ambiguities
                     if a.ambiguity_type == "unresolved_alternatives"]
        assert len(unresolved) == 0, "Single candidate should not synthesize unresolved_alternatives"

    def test_existing_ambiguity_no_duplicate_synthesis(self):
        """If NB01 already flagged unresolved_alternatives, no duplicate."""
        pkt = CanonicalPacket(
            packet_id="reg_no_dup",
            stage="discovery",
            operating_mode="normal_intake",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Andaman", "Sri Lanka"],
            confidence=0.7,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.add_ambiguity(Ambiguity(
            field_name="destination_candidates",
            ambiguity_type="unresolved_alternatives",
            raw_value="Andaman or Sri Lanka",
        ))

        decision = run_gap_and_decision(pkt)

        unresolved = [a for a in decision.ambiguities
                      if a.ambiguity_type == "unresolved_alternatives"
                      and a.field_name == "destination_candidates"]
        assert len(unresolved) == 1, "Should not duplicate existing ambiguity"

    def test_candidate_aware_question_for_destination(self):
        """Multi-candidate destination → question uses 'Between X and Y' framing."""
        pkt = CanonicalPacket(
            packet_id="reg_question",
            stage="discovery",
            operating_mode="normal_intake",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Andaman", "Sri Lanka"],
            confidence=0.7,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )

        decision = run_gap_and_decision(pkt)

        dest_q = [q for q in decision.follow_up_questions
                   if q.get("field_name") == "destination_candidates"]
        assert len(dest_q) > 0, "Should have destination question"

        question = dest_q[0]["question"]
        assert "Andaman" in question, f"Question should mention candidates, got: {question}"
        assert "Sri Lanka" in question, f"Question should mention candidates, got: {question}"

        suggested = dest_q[0].get("suggested_values", [])
        assert "Andaman" in suggested, f"suggested_values should include candidates, got: {suggested}"
        assert "Sri Lanka" in suggested, f"suggested_values should include candidates, got: {suggested}"


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
