"""
Epistemic Provenance & Conflict Arbiter Tests (PER-0922, PER-0923).
"""

from src.intake.epistemic_arbiter import (
    EpistemicArbiter,
    EpistemicStatus,
    ProvenanceSlot,
)


def test_provenance_slot_hash_and_creation():
    slot = ProvenanceSlot(
        slot_name="budget_usd",
        value=5000,
        epistemic_status=EpistemicStatus.EXTRACTED,
        confidence_score=0.95,
        source_turn_id="TURN-1",
        extracted_snippet="our max budget is 5000 dollars",
    )
    assert len(slot.provenance_hash) == 16
    assert slot.confidence_score == 0.95


def test_conversational_conflict_detection():
    slots = [
        ProvenanceSlot("departure_time", "08:00", EpistemicStatus.EXTRACTED, 0.9, "TURN-1", "morning around 8am"),
        ProvenanceSlot("departure_time", "19:00", EpistemicStatus.EXTRACTED, 0.9, "TURN-3", "actually after work at 7pm"),
    ]
    conflicts = EpistemicArbiter.detect_conflicts(slots)
    assert len(conflicts) == 1
    assert conflicts[0].slot_name == "departure_time"
    assert conflicts[0].turn_a_value == "08:00"
    assert conflicts[0].turn_b_value == "19:00"


def test_implicit_and_negative_constraint_extraction():
    text = "We are traveling with our 6-month baby to Rome. Please no Boeing 737 MAX and avoid Ryanair."
    res = EpistemicArbiter.extract_implicit_and_negative_constraints(text)
    assert "requires_infant_bassinet" in res["implicit_needs"]
    assert "AIRCRAFT_EXCLUDE:B737_MAX" in res["excluded_preferences"]
    assert "AIRLINE_EXCLUDE:FR" in res["excluded_preferences"]


def test_json_ld_proof_graph_export():
    slots = [
        ProvenanceSlot("destination", "Rome", EpistemicStatus.FACT, 1.0, "TURN-1", "visiting Rome"),
    ]
    graph = EpistemicArbiter.generate_json_ld_proof_graph("TRIP-123", slots)
    assert graph["@type"] == "EpistemicProofGraph"
    assert len(graph["assertions"]) == 1
    assert graph["assertions"][0]["proofHash"] == slots[0].provenance_hash
