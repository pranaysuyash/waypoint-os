"""
Decision policy conformance tests for NB02 v0.2 runtime behavior.

These tests lock policy contracts defined in specs/decision_policy.md
against src/intake/decision.py without modifying runtime logic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from intake.constants import DECISION_STATES
from intake.decision import field_fills_blocker, run_gap_and_decision
from intake.packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
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


def _base_packet(stage: str = "discovery", operating_mode: str = "normal_intake") -> CanonicalPacket:
    pkt = CanonicalPacket(packet_id=f"policy_{stage}_{operating_mode}")
    pkt.stage = stage
    pkt.operating_mode = operating_mode
    return pkt


def _fill_discovery_hard_blockers(pkt: CanonicalPacket) -> CanonicalPacket:
    pkt.facts["destination_candidates"] = _slot(["Singapore"])
    pkt.facts["origin_city"] = _slot("Bangalore")
    pkt.facts["date_window"] = _slot("2026-06-10 to 2026-06-15")
    pkt.facts["party_size"] = _slot(2)
    return pkt


def test_decision_state_is_from_allowed_contract_enum():
    pkt = _base_packet()
    result = run_gap_and_decision(pkt)
    assert result.decision_state in DECISION_STATES


def test_hard_blockers_imply_ask_followup():
    pkt = _base_packet(stage="discovery")
    # No discovery hard blockers are filled.
    result = run_gap_and_decision(pkt)

    assert result.hard_blockers, "Expected missing hard blockers for empty discovery packet."
    assert result.decision_state == "ASK_FOLLOWUP"


def test_critical_date_contradiction_forces_stop_needs_review():
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.add_contradiction(
        "date_window",
        ["2026-06-10 to 2026-06-15", "2026-08-01 to 2026-08-07"],
        ["env_a", "env_b"],
    )

    result = run_gap_and_decision(pkt)
    assert result.decision_state == "STOP_NEEDS_REVIEW"


def test_critical_document_contradiction_forces_stop_needs_review():
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.add_contradiction(
        "passport_status",
        ["all_valid", "expired_for_one_traveler"],
        ["env_a", "env_b"],
    )

    result = run_gap_and_decision(pkt)
    assert result.decision_state == "STOP_NEEDS_REVIEW"


def test_blocking_ambiguity_cannot_be_proceed_traveler_safe():
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery", operating_mode="post_trip"))
    pkt.add_ambiguity(
        Ambiguity(
            field_name="destination_candidates",
            ambiguity_type="unresolved_alternatives",
            raw_value="Singapore or Japan",
            confidence=0.9,
            evidence_refs=_ev("Singapore or Japan"),
        )
    )

    result = run_gap_and_decision(pkt)
    assert any(a.severity == "blocking" for a in result.ambiguities)
    assert result.decision_state != "PROCEED_TRAVELER_SAFE"
    assert result.decision_state == "ASK_FOLLOWUP"


def test_high_priority_party_conflict_reaches_declared_ask_action():
    """Party-size conflicts affect pricing and must not silently draft a quote."""
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.facts["party_size"] = _slot([3, 5])
    pkt.facts["trip_purpose"] = _slot("leisure")
    pkt.facts["soft_preferences"] = _slot("none")
    pkt.contradictions.append({
        "field_name": "party_size",
        "values": [3, 5],
        "sources": ["call", "crm"],
    })

    result = run_gap_and_decision(pkt)

    assert result.decision_state == "ASK_FOLLOWUP"
    assert any(q["field_name"] == "party_size" for q in result.follow_up_questions)


def test_high_priority_origin_conflict_reaches_declared_ask_action():
    """Origin conflicts change availability/routing and require confirmation."""
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.facts["origin_city"] = _slot(["Bangalore", "Mumbai"])
    pkt.facts["trip_purpose"] = _slot("leisure")
    pkt.facts["soft_preferences"] = _slot("none")
    pkt.contradictions.append({
        "field_name": "origin_city",
        "values": ["Bangalore", "Mumbai"],
        "sources": ["owner", "crm"],
    })

    result = run_gap_and_decision(pkt)

    assert result.decision_state == "ASK_FOLLOWUP"
    assert any(q["field_name"] == "origin_city" for q in result.follow_up_questions)


def test_budget_representations_are_one_or_group():
    """Either raw budget evidence or its normalized value satisfies the one budget dimension."""
    for field_name, value in (("budget_min", 200000), ("budget_raw_text", "2L")):
        pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
        pkt.facts[field_name] = _slot(value)
        pkt.facts["trip_purpose"] = _slot("leisure")
        pkt.facts["soft_preferences"] = _slot("none")

        result = run_gap_and_decision(pkt)

        assert "budget_min" not in result.soft_blockers
        assert "budget_raw_text" not in result.soft_blockers


def test_missing_budget_or_group_emits_one_canonical_blocker():
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    result = run_gap_and_decision(pkt)

    assert result.soft_blockers.count("budget_min") == 1
    assert "budget_raw_text" not in result.soft_blockers


def test_blank_and_empty_collection_values_do_not_fill_blockers():
    for value in ("", "   ", [], {}, (), set()):
        slot = _slot(value)
        assert not field_fills_blocker(slot, [], "destination_candidates"), repr(value)


def test_stop_action_wins_over_ask_action_for_mixed_conflicts():
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.facts["trip_purpose"] = _slot("leisure")
    pkt.facts["soft_preferences"] = _slot("none")
    pkt.contradictions.extend([
        {"field_name": "party_size", "values": [3, 5], "sources": ["a", "b"]},
        {"field_name": "date_window", "values": ["2026-01", "2026-02"], "sources": ["a", "b"]},
    ])

    result = run_gap_and_decision(pkt)

    assert result.decision_state == "STOP_NEEDS_REVIEW"


def test_low_confidence_fully_populated_packet_is_traveler_safe():
    """Decision policy v0.3: no confidence fallback exists.

    specs/decision_policy.md v0.2 documented a `overall_confidence < 0.6 →
    PROCEED_INTERNAL_DRAFT` fallback that the runtime deliberately removed
    (N01 triage, 2026-09-02 §2.2). This test pins the removal: a fully
    populated packet with low slot confidence must stay traveler-safe.
    Re-introducing the fallback makes this test fail.
    """
    pkt = _base_packet(stage="discovery")
    for field_name, value in (
        ("destination_candidates", ["Singapore"]),
        ("origin_city", "Bangalore"),
        ("date_window", "2026-06-10 to 2026-06-15"),
        ("party_size", 2),
        ("budget_min", 200000),
        ("trip_purpose", "leisure"),
        ("soft_preferences", "none"),
    ):
        pkt.facts[field_name] = _slot(value, confidence=0.2)

    result = run_gap_and_decision(pkt)

    assert not result.hard_blockers
    assert not result.soft_blockers
    assert result.decision_state == "PROCEED_TRAVELER_SAFE"


def test_budget_infeasibility_is_stage_gated():
    """Decision policy v0.3: budget_feasibility is a hard blocker only in
    proposal/booking; discovery/shortlist carries it as a soft blocker."""
    def _infeasible(stage: str) -> CanonicalPacket:
        pkt = _fill_discovery_hard_blockers(_base_packet(stage=stage))
        pkt.facts["budget_min"] = _slot(1)  # absurdly low vs any destination minimum
        pkt.facts["trip_purpose"] = _slot("leisure")
        pkt.facts["soft_preferences"] = _slot("none")
        return pkt

    discovery = run_gap_and_decision(_infeasible("discovery"))
    assert "budget_feasibility" in discovery.soft_blockers
    assert "budget_feasibility" not in discovery.hard_blockers

    proposal = run_gap_and_decision(_infeasible("proposal"))
    assert "budget_feasibility" in proposal.hard_blockers


def test_general_conflict_emits_followup_question():
    """Decision policy v0.3: the contradiction→question mapping is one-to-one.

    general_conflict declares ASK_FOLLOWUP in CONTRADICTION_ACTIONS but was
    never actionable (medium priority excluded from every escalation set), so
    a detected conflict on an unmapped field was silently dropped — no
    question, no state effect. The declared action must be honored: the
    conflict produces a user-facing question and ASK_FOLLOWUP (when nothing
    stronger applies).
    """
    pkt = _fill_discovery_hard_blockers(_base_packet(stage="discovery"))
    pkt.facts["trip_purpose"] = _slot("leisure")
    pkt.facts["soft_preferences"] = _slot("none")
    pkt.contradictions.append({
        "field_name": "seat_preference",
        "values": ["window", "aisle"],
        "sources": ["call", "whatsapp"],
    })

    result = run_gap_and_decision(pkt)

    assert result.decision_state == "ASK_FOLLOWUP"
    assert any(
        q["field_name"] == "seat_preference" for q in result.follow_up_questions
    )
