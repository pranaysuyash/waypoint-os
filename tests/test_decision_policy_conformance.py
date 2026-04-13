"""
Decision policy conformance tests for NB02 v0.2 runtime behavior.

These tests lock policy contracts defined in specs/decision_policy.md
against src/intake/decision.py without modifying runtime logic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from intake.decision import DECISION_STATES, run_gap_and_decision
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

