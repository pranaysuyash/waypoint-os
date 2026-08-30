"""
tests/test_epistemic_integrity.py — Unit tests for Epistemic Integrity (PER-0922/PER-0923).

Verifies:
  - EpistemicStatus enum definitions and Slot integration
  - AssumptionRecord structure and lifecycle
  - Unacknowledged critical assumptions trigger decision engine risk flags
  - Operator acknowledgement clears epistemic risk flags
"""

from src.intake.packet_models import (
    CanonicalPacket,
    Slot,
    EpistemicStatus,
    AssumptionRecord,
    AuthorityLevel,
)
from src.intake.decision import generate_risk_flags


def test_epistemic_status_enum():
    assert EpistemicStatus.FACT == "FACT"
    assert EpistemicStatus.INFERRED == "INFERRED"
    assert EpistemicStatus.ASSUMED == "ASSUMED"
    assert EpistemicStatus.UNKNOWN == "UNKNOWN"


def test_slot_epistemic_status():
    slot = Slot(
        value="Paris",
        confidence=0.95,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        epistemic_status=EpistemicStatus.FACT,
    )
    d = slot.to_dict()
    assert d["epistemic_status"] == "FACT"
    assert d["value"] == "Paris"


def test_assumption_record_to_dict():
    rec = AssumptionRecord(
        slot_name="budget_min",
        assumed_value=150000,
        rationale="Default minimum budget for 2 adults in Europe for 7 days",
        criticality="critical",
        acknowledged_by_operator=False,
    )
    d = rec.to_dict()
    assert d["slot_name"] == "budget_min"
    assert d["assumed_value"] == 150000
    assert d["criticality"] == "critical"
    assert d["acknowledged_by_operator"] is False


def test_unacknowledged_critical_assumption_generates_risk_flag():
    packet = CanonicalPacket(packet_id="pkt_test_1")
    packet.stage = "discovery"
    packet.set_fact("destination_candidates", Slot(
        value=["Bali"],
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    ))
    
    # Add an unacknowledged critical assumption
    packet.assumptions.append(AssumptionRecord(
        slot_name="departure_airport",
        assumed_value="BOM",
        rationale="Inferred from user IP / agency default",
        criticality="critical",
        acknowledged_by_operator=False,
    ))

    flags = generate_risk_flags(packet, stage="discovery")
    assumption_flags = [f for f in flags if f.get("flag") == "unacknowledged_critical_assumption"]
    assert len(assumption_flags) == 1
    assert "departure_airport" in assumption_flags[0]["message"]
    assert assumption_flags[0]["severity"] == "high"


def test_acknowledged_critical_assumption_clears_risk_flag():
    packet = CanonicalPacket(packet_id="pkt_test_2")
    packet.stage = "discovery"
    packet.set_fact("destination_candidates", Slot(
        value=["Bali"],
        confidence=1.0,
        authority_level=AuthorityLevel.EXPLICIT_USER,
    ))
    
    # Add an acknowledged critical assumption
    packet.assumptions.append(AssumptionRecord(
        slot_name="departure_airport",
        assumed_value="BOM",
        rationale="Inferred from user IP / agency default",
        criticality="critical",
        acknowledged_by_operator=True,
    ))

    flags = generate_risk_flags(packet, stage="discovery")
    assumption_flags = [f for f in flags if f.get("flag") == "unacknowledged_critical_assumption"]
    assert len(assumption_flags) == 0
