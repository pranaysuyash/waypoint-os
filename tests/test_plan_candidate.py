"""
tests/test_plan_candidate.py — Pass 2A: PlanCandidate bridge artifact tests.

Coverage:
- Normal candidate construction from valid packet
- Traveler-safe dict hardening: excludes all internal/system fields
- Fact allowlist: only TRAVELER_SAFE_FACT_FIELDS marked safe (deny-by-default)
- Risk categories: decision risk_flags default traveler_safe=False
- Critical suitability flags never traveler-safe
- Internal terms blocked from traveler-safe dict
- traveler_status uses safe mapped values only
- traveler_summary is deterministic from decision_state
- Orchestration integration: plan_candidate on SpineResult
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.packet_models import (
    CanonicalPacket,
    Slot,
    SuitabilityFlag,
    AuthorityLevel,
    EvidenceRef,
)
from intake.decision import (
    DecisionResult,
    run_gap_and_decision,
)
from intake.strategy import (
    build_session_strategy,
    SessionStrategy,
    PromptBundle,
)
from intake.plan_candidate import (
    build_plan_candidate,
    PlanCandidate,
    TravelerSnapshot,
    TRAVELER_SAFE_FACT_FIELDS,
    _TRAVELER_STATUS_MAP,
    _TRAVELER_SUMMARY_MAP,
    _INTERNAL_ONLY_RISK_TERMS,
    _INTERNAL_ONLY_RISK_CATEGORIES,
)
from intake.constants import DECISION_STATES


# These terms must NEVER appear in the traveler-safe dict output.
INTERNAL_ONLY_TERMS = {
    "margin", "hypothesis", "contradiction", "blocker",
    "owner_constraint", "internal_only", "agency_note",
    "confidence", "decision_state", "next_action",
    "operator_review", "owner_review", "traveler-facing",
    "escalate", "senior review",
}

# These fields must NEVER be keys in the traveler-safe dict.
INTERNAL_ONLY_FIELDS = {
    "decision_state", "next_action", "operating_mode", "strategy_goal",
    "readiness", "commercial", "fees", "budget_breakdown",
    "intent_scores", "assumptions", "missing_inputs",
}

# These are the ONLY allowed top-level keys in traveler-safe dict.
TRAVELER_SAFE_ALLOWED_KEYS = {
    "plan_id", "stage", "traveler_snapshot", "constraints",
    "risks", "traveler_status", "traveler_summary",
    "suitability_flags", "schema_version",
}


def make_minimal_packet(mode="normal_intake") -> CanonicalPacket:
    pkt = CanonicalPacket(packet_id="test_minimal", operating_mode=mode)
    pkt.facts["destination_candidates"] = Slot(
        value=["Singapore"], confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="Singapore")],
    )
    pkt.facts["origin_city"] = Slot(
        value="Bangalore", confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="Bangalore")],
    )
    pkt.facts["date_window"] = Slot(
        value="March 2026", confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="March")],
    )
    pkt.facts["party_size"] = Slot(
        value=4, confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="4")],
    )
    return pkt


def make_full_packet() -> CanonicalPacket:
    pkt = make_minimal_packet()
    pkt.facts["party_composition"] = Slot(
        value={"adults": 2, "elderly": 2, "children": 0}, confidence=0.95,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    pkt.facts["trip_purpose"] = Slot(
        value="leisure", confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    pkt.facts["pace_preference"] = Slot(
        value="relaxed", confidence=0.8,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    pkt.facts["budget_min"] = Slot(
        value=50000, confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    pkt.facts["budget_raw_text"] = Slot(
        value="5L", confidence=0.9,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    )
    return pkt


class TestPlanCandidateConstruction:
    def test_builds_from_valid_packet(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        assert isinstance(candidate, PlanCandidate)
        assert candidate.plan_id == f"plan_{packet.packet_id}"
        assert candidate.decision_state == decision.decision_state

    def test_traveler_snapshot_populated(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        snap = candidate.traveler_snapshot
        assert snap.destination_candidates == ["Singapore"]
        assert snap.party_size == 4
        assert snap.party_composition == {"adults": 2, "elderly": 2, "children": 0}

    def test_missing_inputs_tracked(self):
        packet = CanonicalPacket(packet_id="test_empty")
        decision = DecisionResult(
            packet_id="test_empty", current_stage="discovery",
            operating_mode="normal_intake", decision_state="ASK_FOLLOWUP",
        )
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        assert "destination_candidates" in candidate.missing_inputs


class TestReadinessMapping:
    def test_stop_needs_review_maps_to_blocked(self):
        packet = make_full_packet()
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="STOP_NEEDS_REVIEW")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        assert candidate.readiness == "blocked"

    def test_branch_options_maps_to_internal_draft(self):
        packet = make_full_packet()
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="BRANCH_OPTIONS")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        assert candidate.readiness == "internal_draft"

    def test_proceed_traveler_safe_maps_to_traveler_safe(self):
        packet = make_full_packet()
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="PROCEED_TRAVELER_SAFE")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        assert candidate.readiness == "traveler_safe"


class TestFactAllowlist:
    def test_allowlist_fields_are_traveler_safe(self):
        for field_name in TRAVELER_SAFE_FACT_FIELDS:
            packet = make_full_packet()
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode="normal_intake", decision_state="PROCEED_INTERNAL_DRAFT")
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            fact_constraints = [c for c in candidate.constraints
                                if c.source == "fact" and c.field == field_name]
            if fact_constraints:
                for c in fact_constraints:
                    assert c.traveler_safe, f"{field_name} should be traveler-safe"

    def test_non_allowlist_facts_are_not_traveler_safe(self):
        packet = make_full_packet()
        packet.facts["owner_constraints"] = Slot(
            value="margin_above_15", confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="PROCEED_INTERNAL_DRAFT")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        ow_constraints = [c for c in candidate.constraints
                          if c.field == "owner_constraints"]
        assert len(ow_constraints) > 0, "owner_constraints fact should produce a constraint"
        assert not ow_constraints[0].traveler_safe

    def test_passport_status_not_traveler_safe(self):
        packet = make_full_packet()
        packet.facts["passport_status"] = Slot(
            value="valid", confidence=1.0,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="PROCEED_INTERNAL_DRAFT")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        pp_constraints = [c for c in candidate.constraints if c.field == "passport_status"]
        assert len(pp_constraints) > 0
        assert not pp_constraints[0].traveler_safe

    def test_unknown_facts_default_to_not_safe(self):
        """Any fact not in the allowlist must default to traveler_safe=False."""
        packet = make_full_packet()
        packet.facts["custom_internal_field"] = Slot(
            value="some_value", confidence=0.9,
            authority_level=AuthorityLevel.EXPLICIT_USER,
        )
        decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                  operating_mode="normal_intake", decision_state="PROCEED_INTERNAL_DRAFT")
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        cc = [c for c in candidate.constraints if c.field == "custom_internal_field"]
        assert len(cc) > 0
        assert not cc[0].traveler_safe


class TestTravelerSafeDict:
    """Comprehensive tests for to_traveler_safe_dict() exclusion rules."""

    def test_excludes_decision_state(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "decision_state" not in safe

    def test_excludes_next_action(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "next_action" not in safe

    def test_excludes_operating_mode(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "operating_mode" not in safe

    def test_excludes_strategy_goal(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "strategy_goal" not in safe

    def test_excludes_readiness(self):
        """Raw readiness (blocked/internal_draft/traveler_safe) must not appear."""
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "readiness" not in safe

    def test_excludes_commercial(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy, fees={"total": 50000})
        safe = candidate.to_traveler_safe_dict()
        assert "commercial" not in safe

    def test_excludes_fees_key(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy, fees={"total": 50000})
        safe = candidate.to_traveler_safe_dict()
        safe_str = json.dumps(safe)
        assert '"fees"' not in safe_str

    def test_excludes_budget_breakdown(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "budget_breakdown" not in safe

    def test_excludes_intent_scores(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "intent_scores" not in safe

    def test_excludes_assumptions(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "assumptions" not in safe

    def test_excludes_missing_inputs(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "missing_inputs" not in safe

    def test_excludes_confidence(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "confidence" not in safe

    def test_no_internal_terms_in_output(self):
        packet = make_full_packet()
        packet.suitability_flags = [
            SuitabilityFlag(flag_type="elderly_intensity", severity="critical",
                            reason="Elderly traveler — hypothesis: may not tolerate heat",
                            confidence=0.95)
        ]
        decision = run_gap_and_decision(packet)
        decision.risk_flags = [
            {"flag": "margin_low", "severity": "high", "category": "margin",
             "message": "Margin below floor — owner must review"}
        ]
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        safe_str = json.dumps(safe).lower()
        for term in INTERNAL_ONLY_TERMS:
            assert term not in safe_str, f"'{term}' leaked into traveler-safe dict"

    def test_traveler_status_uses_safe_mapped_values(self):
        """traveler_status must only be one of the safe mapped values."""
        safe_statuses = set(_TRAVELER_STATUS_MAP.values())
        for state in DECISION_STATES:
            packet = make_full_packet()
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode="normal_intake", decision_state=state)
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            safe = candidate.to_traveler_safe_dict()
            assert safe["traveler_status"] in safe_statuses, \
                f"traveler_status '{safe['traveler_status']}' not in safe set for state={state}"

    def test_traveler_summary_is_deterministic(self):
        """traveler_summary comes from decision_state map, never from strategy_goal."""
        for state in DECISION_STATES:
            packet = make_full_packet()
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode="normal_intake", decision_state=state)
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            safe = candidate.to_traveler_safe_dict()
            expected = _TRAVELER_SUMMARY_MAP.get(state, "We are reviewing your trip request.")
            assert safe["traveler_summary"] == expected, \
                f"traveler_summary mismatch for state={state}"

    def test_traveler_summary_no_internal_terms(self):
        for state in DECISION_STATES:
            packet = make_full_packet()
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode="normal_intake", decision_state=state)
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            safe = candidate.to_traveler_safe_dict()
            summary_lower = safe["traveler_summary"].lower()
            for term in INTERNAL_ONLY_TERMS:
                assert term not in summary_lower, \
                    f"'{term}' found in traveler_summary for state={state}"

    def test_only_allowed_keys_in_traveler_safe_dict(self):
        """The traveler-safe dict must contain ONLY these keys."""
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        for key in safe:
            assert key in TRAVELER_SAFE_ALLOWED_KEYS, \
                f"Unexpected key '{key}' in traveler-safe dict"

    def test_critical_suitability_not_traveler_safe(self):
        packet = make_full_packet()
        packet.suitability_flags = [
            SuitabilityFlag(flag_type="elderly_scuba", severity="critical",
                            reason="Elderly traveler cannot safely participate",
                            confidence=0.95)
        ]
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        risk = [r for r in candidate.risks if r.flag == "elderly_scuba"][0]
        assert not risk.traveler_safe

    def test_all_canonical_states_produce_valid_safe_dict(self):
        for state in DECISION_STATES:
            packet = make_full_packet()
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode="normal_intake", decision_state=state)
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            safe = candidate.to_traveler_safe_dict()
            assert "plan_id" in safe
            assert "traveler_status" in safe
            assert "traveler_summary" in safe
            for forbidden_key in INTERNAL_ONLY_FIELDS:
                assert forbidden_key not in safe, f"'{forbidden_key}' leaked for state={state}"

    def test_includes_traveler_safe_fields(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        safe = candidate.to_traveler_safe_dict()
        assert "plan_id" in safe
        assert "traveler_snapshot" in safe
        assert "traveler_status" in safe
        assert "traveler_summary" in safe
        assert safe["traveler_snapshot"]["destination_candidates"] == ["Singapore"]

    def test_operating_mode_never_in_traveler_safe(self):
        """operating_mode must NEVER appear regardless of mode value."""
        for mode in ("normal_intake", "follow_up", "post_trip", "audit", "emergency"):
            packet = make_minimal_packet(mode=mode)
            decision = DecisionResult(packet_id=packet.packet_id, current_stage="discovery",
                                      operating_mode=mode, decision_state="PROCEED_INTERNAL_DRAFT")
            strategy = build_session_strategy(decision, packet)
            candidate = build_plan_candidate(packet, decision, strategy)
            safe = candidate.to_traveler_safe_dict()
            assert "operating_mode" not in safe, f"operating_mode leaked for mode={mode}"


class TestOrchestrationIntegration:
    def test_spine_result_has_plan_candidate(self):
        from intake.orchestration import run_spine_once
        from intake.packet_models import SourceEnvelope
        envelope = SourceEnvelope(
            envelope_id="test_env", source_system="traveler_form",
            actor_type="traveler", received_at=datetime.now().isoformat(),
            content={"party_composition": {"adults": 2}, "destination": "Singapore",
                     "origin": "Bangalore", "date_window": "March 2026",
                     "party_size": 2, "budget": "5L"},
            content_type="structured_json",
        )
        result = run_spine_once([envelope], stage="discovery")
        assert result.plan_candidate is not None
        assert isinstance(result.plan_candidate, PlanCandidate)

    def test_traveler_bundle_unchanged(self):
        from intake.orchestration import run_spine_once
        from intake.packet_models import SourceEnvelope
        envelope = SourceEnvelope(
            envelope_id="test_env", source_system="traveler_form",
            actor_type="traveler", received_at=datetime.now().isoformat(),
            content={"party_composition": {"adults": 2}, "destination": "Singapore",
                     "origin": "Bangalore", "date_window": "March 2026",
                     "party_size": 2, "budget": "5L"},
            content_type="structured_json",
        )
        result = run_spine_once([envelope], stage="discovery")
        assert isinstance(result.traveler_bundle, PromptBundle)
        tdict = result.traveler_bundle.to_dict()
        assert "system_context" in tdict
        assert "user_message" in tdict

    def test_leakage_check_still_runs(self):
        from intake.orchestration import run_spine_once
        from intake.packet_models import SourceEnvelope
        envelope = SourceEnvelope(
            envelope_id="test_env", source_system="traveler_form",
            actor_type="traveler", received_at=datetime.now().isoformat(),
            content={"party_composition": {"adults": 2}, "destination": "Singapore",
                     "origin": "Bangalore", "date_window": "March 2026",
                     "party_size": 2, "budget": "5L"},
            content_type="structured_json",
        )
        result = run_spine_once([envelope], stage="discovery")
        assert "leaks" in result.leakage_result
        assert "is_safe" in result.leakage_result


class TestPlanCandidateSerialization:
    def test_internal_dict_includes_commercial(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy, fees={"total": 50000})
        d = candidate.to_internal_dict()
        assert "commercial" in d
        assert d["commercial"]["fees"] == {"total": 50000}

    def test_internal_dict_includes_all_sections(self):
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        d = candidate.to_internal_dict()
        for key in ("packet_id", "decision_state", "operating_mode",
                     "traveler_snapshot", "constraints", "risks",
                     "commercial", "suitability_flags", "readiness",
                     "missing_inputs", "next_action"):
            assert key in d, f"'{key}' missing from internal dict"

    def test_internal_dict_may_contain_internal_fields(self):
        """Internal dict is expected to have internal fields."""
        packet = make_full_packet()
        decision = run_gap_and_decision(packet)
        strategy = build_session_strategy(decision, packet)
        candidate = build_plan_candidate(packet, decision, strategy)
        d = candidate.to_internal_dict()
        assert "decision_state" in d
        assert "next_action" in d
        assert "operating_mode" in d
        assert "strategy_goal" in d
        assert "readiness" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
