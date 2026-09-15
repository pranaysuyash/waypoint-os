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
    SourceEnvelope,
)
from src.intake.decision import generate_risk_flags
from src.intake.extractors import ExtractionPipeline


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


# --- FND-0124: production assumption producer (extraction -> register) ---

def test_pipeline_registers_defaulted_budget_slots_as_assumptions():
    """An intake with a defaulted field must carry a provenance-labeled
    assumption entry in the packet's AssumptionRegister (FND-0124)."""
    packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(
        "Planning a trip to Bali for 4 people in March 2027. Budget 500000."
    )])
    by_slot = {a.slot_name: a for a in packet.assumptions}
    # budget without a currency marker -> system default currency is ASSUMED
    assert "budget_currency" in by_slot
    bc = by_slot["budget_currency"]
    assert bc.criticality == "critical"
    assert bc.acknowledged_by_operator is False
    assert bc.rationale  # provenance: explain the default
    assert bc.assumed_value == packet.facts["budget_currency"].value
    # budget without a flexibility marker -> golden convention "soft"
    assert "budget_flexibility" in by_slot
    assert by_slot["budget_flexibility"].criticality == "advisory"
    # the underlying facts are epistemically labeled ASSUMED, not FACT
    assert packet.facts["budget_currency"].epistemic_status == EpistemicStatus.ASSUMED


def test_pipeline_does_not_assume_explicit_values():
    """Explicit traveler input must not be registered as an assumption."""
    packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(
        "Trip to Bali for 4 in March 2027, budget USD 5000 for the whole group."
    )])
    assert packet.facts["budget_currency"].epistemic_status == EpistemicStatus.FACT
    assert packet.facts["budget_scope"].epistemic_status == EpistemicStatus.FACT
    assert "budget_currency" not in [a.slot_name for a in packet.assumptions]
    assert "budget_scope" not in [a.slot_name for a in packet.assumptions]


def test_assumptions_survive_packet_serialization():
    """Contract test: CanonicalPacket.to_dict preserves the assumption
    register end-to-end (F-37 slice fixed the drop; this locks it in)."""
    packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(
        "Planning a trip to Bali for 4 people in March 2027. Budget 500000."
    )])
    assert len(packet.assumptions) > 0
    d = packet.to_dict()
    assert len(d["assumptions"]) == len(packet.assumptions)
    entry = d["assumptions"][0]
    assert entry["slot_name"] == packet.assumptions[0].slot_name
    assert entry["criticality"] == packet.assumptions[0].criticality
    assert entry["assumed_value"] == packet.assumptions[0].assumed_value
