"""
tests/test_epistemic_engine_deep.py — Unit tests for PER-0922/0923 epistemic engine capabilities.
"""

import time
from src.intake.epistemic_engine import (
    EpistemicCategory,
    EpistemicEngine,
    ProvenanceSlot,
)


def test_confidence_temporal_decay():
    """Verify confidence score decays over time for volatile unconfirmed attributes."""
    # Verified 10 days ago at 0.90 confidence with 0.05/day decay
    ten_days_ago = time.time() - (10 * 86400)
    slot = ProvenanceSlot(
        field_name="flight_quote_usd",
        value=1250.0,
        category=EpistemicCategory.INFERRED,
        confidence=0.90,
        last_verified_at=ten_days_ago,
        decay_rate_per_day=0.05,
    )

    decayed = EpistemicEngine.calculate_decayed_confidence(slot)
    # Expected: 0.90 - (10 * 0.05) = 0.40
    assert decayed == 0.40


def test_epistemic_conflict_detection():
    """Verify detecting direct contradictions between conversational turns."""
    existing = {
        "destination": ProvenanceSlot(
            field_name="destination",
            value="Tokyo",
            category=EpistemicCategory.FACT,
            confidence=0.98,
            source_turn_id="turn_1",
        )
    }

    new_turn = {
        "destination": ProvenanceSlot(
            field_name="destination",
            value="Paris",
            category=EpistemicCategory.FACT,
            confidence=0.95,
            source_turn_id="turn_3",
        )
    }

    conflicts = EpistemicEngine.detect_conflicts(existing, new_turn)
    assert len(conflicts) == 1
    assert conflicts[0].field_name == "destination"
    assert conflicts[0].previous_value == "Tokyo"
    assert conflicts[0].new_value == "Paris"
    assert conflicts[0].severity == "BLOCKING"


def test_implicit_constraint_extraction():
    """Verify extracting implicit requirements from natural language cues."""
    prompt = "Looking for a 2-week trip to Italy with my wife and 6-month-old baby."
    implicit = EpistemicEngine.extract_implicit_constraints(prompt)

    assert implicit["requires_infant_bassinet"] is True
    assert implicit["avoid_tight_connections"] is True
    assert implicit["pacing_constraint"] == "RELAXED"


def test_json_ld_proof_graph_generation():
    """Verify JSON-LD proof graph serialization for epistemic auditability."""
    slots = {
        "departure_city": ProvenanceSlot(
            field_name="departure_city",
            value="New York",
            category=EpistemicCategory.FACT,
            confidence=1.0,
            source_turn_id="email_inbound_01",
            extracted_snippet="Flying out from NYC on Oct 5th",
        )
    }

    proof = EpistemicEngine.generate_json_ld_proof_graph("trip_proof_99", slots)
    assert proof["@type"] == "TripEpistemicManifest"
    assert proof["tripId"] == "trip_proof_99"
    assert len(proof["claims"]) == 1
    assert proof["claims"][0]["claimValue"] == "New York"
    assert proof["claims"][0]["epistemicCategory"] == "FACT"
