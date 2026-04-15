#!/usr/bin/env python3
"""
Comprehensive test suite for Notebook 02: Gap and Decision
===========================================================

Test design philosophy:
  Every test answers ONE of these questions:
  1. "Does this component do what the code says it does?" (implementation correctness)
  2. "Does this component NOT do what it shouldn't do?" (invariant preservation)
  3. "What happens at the boundaries?" (edge cases)
  4. "What happens when inputs are weird?" (robustness)

Run: uv run python notebooks/test_02_comprehensive.py
"""

import json
import sys
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Tuple
from enum import IntEnum

# =============================================================================
# IMPORT THE NOTEBOOK CODE
# =============================================================================
# Ensure notebook cell imports can resolve project modules before exec.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# We extract all code cells from the notebook and exec them, then run tests
# against the resulting namespace. This is the most honest way to test the
# actual notebook code without copying it.

def load_notebook_namespace():
    """Load all code from the notebook into a namespace dict."""
    nb_path = os.path.join(os.path.dirname(__file__), "02_gap_and_decision.ipynb")
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    namespace = {}
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = cell['source']
            if isinstance(source, list):
                source = ''.join(source)
            try:
                exec(source, namespace)
            except Exception as e:
                print(f"ERROR loading cell: {e}")
                print(f"  Source preview: {source[:120]}")
                raise
    return namespace

ns = load_notebook_namespace()

from intake.packet_models import CanonicalPacket as CanonicalPacketModel, Slot, EvidenceRef, UnknownField, AuthorityLevel
from intake.decision import (
    run_gap_and_decision as run_gap_and_decision_src,
    MVB_BY_STAGE,
    LEGACY_ALIASES,
    CONTRADICTION_ACTIONS,
    CONTRADICTION_FIELD_MAP,
    calculate_confidence as calculate_confidence_src,
    classify_contradiction,
    get_contradiction_action,
    resolve_field,
    field_fills_blocker,
    DecisionResult,
)

# Compatibility wrapper for legacy test constructors.
def CanonicalPacket(*args, **kwargs):
    packet_id = kwargs.pop("packet_id", None)
    if packet_id is None and args:
        packet_id = args[0]
    if packet_id is None:
        packet_id = "compat_packet"

    kwargs.pop("created_at", None)
    kwargs.pop("last_updated", None)

    pkt = CanonicalPacketModel(packet_id=packet_id)
    for key in (
        "schema_version", "stage", "operating_mode", "decision_state",
        "facts", "derived_signals", "hypotheses", "ambiguities",
        "unknowns", "contradictions", "source_envelope_ids",
        "revision_count", "event_cursor", "events",
    ):
        if key in kwargs:
            setattr(pkt, key, kwargs.pop(key))
    return pkt

# Pull functions from notebook namespace when present, otherwise fallback to src/intake.
run_gap_and_decision = ns.get('run_gap_and_decision', run_gap_and_decision_src)
calculate_confidence = ns.get('calculate_confidence', calculate_confidence_src)
FIELD_ALIASES = ns.get('FIELD_ALIASES', LEGACY_ALIASES)
CONTRADICTION_HANDLING = ns.get('CONTRADICTION_HANDLING', CONTRADICTION_ACTIONS)
AUTHORITY_WEIGHTS = ns.get('AUTHORITY_WEIGHTS', {
    "manual_override": 1.0,
    "explicit_user": 0.95,
    "imported_structured": 0.85,
    "explicit_owner": 0.8,
    "derived_signal": 0.6,
    "soft_hypothesis": 0.35,
    "unknown": 0.2,
})
detect_contradictions = ns.get('detect_contradictions', lambda packet: packet.contradictions)
is_fact = ns.get(
    'is_fact',
    lambda slot: slot is not None and AuthorityLevel.is_fact(slot.authority_level),
)
is_derived_signal = ns.get(
    'is_derived_signal',
    lambda slot: slot is not None and slot.authority_level == AuthorityLevel.DERIVED_SIGNAL,
)
is_hypothesis = ns.get(
    'is_hypothesis',
    lambda slot: slot is not None and slot.authority_level == AuthorityLevel.SOFT_HYPOTHESIS,
)

# =============================================================================
# TEST FRAMEWORK (minimal, no dependencies)
# =============================================================================

_passed = 0
_failed = 0
_errors = 0
_results = []

def test(name, fn):
    """Run a single test function."""
    global _passed, _failed, _errors
    try:
        fn()
        _passed += 1
        _results.append(("PASS", name, None))
        print(f"  PASS: {name}")
    except AssertionError as e:
        _failed += 1
        _results.append(("FAIL", name, str(e)))
        print(f"  FAIL: {name}")
        print(f"        → {e}")
    except Exception as e:
        _errors += 1
        _results.append(("ERR", name, str(e)))
        print(f"  ERR!: {name}")
        print(f"        → {type(e).__name__}: {e}")


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# =============================================================================
# DIMENSION 1: BLOCKER RESOLUTION (core correctness)
# =============================================================================
#
# Thinking: The MVB defines what fields MUST exist at each stage. A blocker is
# "unresolved" when no fact or derived_signal provides that field. The key
# invariants are:
#   - Facts fill blockers (any authority that is_fact() = True)
#   - Derived signals fill blockers
#   - Hypotheses do NOT fill blockers (this is the contract rule)
#   - Unknown authority does NOT fill blockers
#   - Missing fields = unresolved blocker

section("DIMENSION 1: BLOCKER RESOLUTION")


# Test 1.1: Empty packet → all 4 discovery hard blockers unresolved
# Why: This is the baseline. If nothing exists, everything should be blocked.
# This tests the most fundamental invariant: absence = blocker.
def t_empty_packet_all_hard_blockers():
    pkt = CanonicalPacket(
        packet_id="empty", created_at="now", last_updated="now", stage="discovery")
    r = run_gap_and_decision(pkt)
    assert set(r.hard_blockers) == {"destination_city", "origin_city", "travel_dates", "traveler_count"}, \
        f"Expected 4 blockers, got {r.hard_blockers}"
    assert len(r.soft_blockers) == 3, f"Expected 3 soft blockers, got {r.soft_blockers}"
    assert r.decision_state == "ASK_FOLLOWUP"

test("Empty packet → all 4 discovery hard blockers", t_empty_packet_all_hard_blockers)


# Test 1.2: One fact fills one blocker → only 3 blockers remain
# Why: Tests the per-field independence of blocker checking. Each field is
# checked separately; filling one should not affect the others.
def t_one_fact_fills_one_blocker():
    pkt = CanonicalPacket(packet_id="one", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert "origin_city" not in r.hard_blockers
    assert len(r.hard_blockers) == 3, f"Expected 3 blockers, got {r.hard_blockers}"

test("One fact fills one blocker → 3 remain", t_one_fact_fills_one_blocker)


# Test 1.3: All hard blockers filled by facts → zero hard blockers
# Why: Tests the happy path. Every required field present as a fact.
def t_all_hard_blockers_filled_by_facts():
    pkt = CanonicalPacket(packet_id="all", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.95, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.95, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0, f"Expected 0 blockers, got {r.hard_blockers}"

test("All hard blockers filled by facts → 0 blockers", t_all_hard_blockers_filled_by_facts)


# Test 1.4: Derived signal fills a hard blocker (contract requirement)
# Why: The contract explicitly says derived signals CAN fill blockers.
# If this doesn't work, the contract is broken.
def t_derived_signal_fills_blocker():
    pkt = CanonicalPacket(packet_id="derived", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_owner"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_owner"),
        },
        derived_signals={
            "destination_city": Slot(value="Singapore", confidence=0.75, authority_level="derived_signal"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert "destination_city" not in r.hard_blockers, \
        f"derived_signal should fill destination_city, got blockers: {r.hard_blockers}"
    assert len(r.hard_blockers) == 0, f"Expected 0 blockers, got {r.hard_blockers}"

test("Derived signal fills a hard blocker", t_derived_signal_fills_blocker)


# Test 1.5: Hypothesis does NOT fill a hard blocker (contract requirement)
# Why: The contract says hypotheses do NOT fill blockers. This is the most
# important safety invariant — a guess should never be treated as a fact.
def t_hypothesis_does_not_fill_blocker():
    pkt = CanonicalPacket(packet_id="hyp", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_owner"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_owner"),
        },
        hypotheses={
            "destination_city": Slot(value="Singapore", confidence=0.99, authority_level="soft_hypothesis"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert "destination_city" in r.hard_blockers, \
        f"Hypothesis should NOT fill destination_city, but it did. Blockers: {r.hard_blockers}"

test("Hypothesis does NOT fill a hard blocker (even at 0.99 confidence)", t_hypothesis_does_not_fill_blocker)


# Test 1.6: Unknown authority does NOT fill a hard blocker
# Why: If a slot exists but has authority_level="unknown", it means the system
# tried and failed to classify it. Should not count as filled.
def t_unknown_authority_does_not_fill_blocker():
    pkt = CanonicalPacket(packet_id="unk", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="???", confidence=0.0, authority_level="unknown"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_owner"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_owner"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert "destination_city" in r.hard_blockers, \
        f"Unknown authority should NOT fill blocker. Blockers: {r.hard_blockers}"

test("Unknown authority does NOT fill a hard blocker", t_unknown_authority_does_not_fill_blocker)


# Test 1.7: Only 1 fact present → 3 blockers remain (discovery)
# Why: Same as 1.2 but verifying the count is exactly right.
def t_only_one_of_four_blockers_filled():
    pkt = CanonicalPacket(packet_id="one2", created_at="now", last_updated="now",
        facts={"traveler_count": Slot(value=2, confidence=0.9, authority_level="explicit_user")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 3, f"Expected 3, got {r.hard_blockers}"
    assert "traveler_count" not in r.hard_blockers

test("Only 1 of 4 blockers filled → 3 remain", t_only_one_of_four_blockers_filled)


# Test 1.8: Soft blockers are identified when hard blockers are all filled
# Why: Soft blockers are separate from hard blockers. They should appear when
# hard blockers are satisfied.
def t_soft_blockers_identified():
    pkt = CanonicalPacket(packet_id="soft", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0
    assert "budget_range" in r.soft_blockers
    assert "trip_purpose" in r.soft_blockers
    assert "traveler_preferences" in r.soft_blockers

test("Soft blockers identified when hard blockers filled", t_soft_blockers_identified)


# Test 1.9: Soft blocker satisfied by hypothesis → no soft blocker
# Why: Unlike hard blockers, soft blockers CAN be satisfied by hypotheses.
# This tests the asymmetry: hypotheses can fill soft but not hard blockers.
def t_soft_blocker_satisfied_by_hypothesis():
    pkt = CanonicalPacket(packet_id="soft_hyp", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        hypotheses={
            "budget_range": Slot(value="mid", confidence=0.5, authority_level="soft_hypothesis"),
            "trip_purpose": Slot(value="leisure", confidence=0.4, authority_level="soft_hypothesis"),
            "traveler_preferences": Slot(value="relaxed", confidence=0.5, authority_level="soft_hypothesis"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0
    assert len(r.soft_blockers) == 0, f"Soft blockers should be satisfied by hypotheses, got {r.soft_blockers}"

test("Soft blockers satisfied by hypotheses", t_soft_blocker_satisfied_by_hypothesis)


# Test 1.10: Manual override fills a blocker (highest authority)
# Why: Tests that manual_override authority works as a fact-level authority.
def t_manual_override_fills_blocker():
    pkt = CanonicalPacket(packet_id="manual", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=1.0, authority_level="manual_override"),
            "origin_city": Slot(value="Bangalore", confidence=1.0, authority_level="manual_override"),
            "travel_dates": Slot(value="2026-03-15", confidence=1.0, authority_level="manual_override"),
            "traveler_count": Slot(value=3, confidence=1.0, authority_level="manual_override"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0

test("Manual override fills a blocker", t_manual_override_fills_blocker)


# Test 1.11: Imported structured data fills a blocker
# Why: Tests imported_structured as a fact-level authority (level 3).
def t_imported_structured_fills_blocker():
    pkt = CanonicalPacket(packet_id="imported", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.85, authority_level="imported_structured"),
            "origin_city": Slot(value="Bangalore", confidence=0.85, authority_level="imported_structured"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.85, authority_level="imported_structured"),
            "traveler_count": Slot(value=3, confidence=0.85, authority_level="imported_structured"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0

test("Imported structured data fills a blocker", t_imported_structured_fills_blocker)


# =============================================================================
# DIMENSION 2: STAGE PROGRESSION (MVB changes per stage)
# =============================================================================
#
# Thinking: Each stage has MORE hard blockers than the previous. The system
# should catch new blockers when the stage changes. This is the "increasing
# bar" test.
#
# discovery: 4 hard blockers
# shortlist: 5 hard blockers (adds selected_destinations)
# proposal:  6 hard blockers (adds selected_itinerary)
# booking:   8 hard blockers (adds traveler_details, payment_method)

section("DIMENSION 2: STAGE PROGRESSION")


# Test 2.1: Discovery-complete packet fails at shortlist (missing selected_destinations)
# Why: Shortlist adds selected_destinations. A packet that's fine for discovery
# should fail at shortlist.
def t_discovery_packet_fails_shortlist():
    pkt = CanonicalPacket(packet_id="disc", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt, current_stage="shortlist")
    assert "selected_destinations" in r.hard_blockers, \
        f"Shortlist should require selected_destinations. Blockers: {r.hard_blockers}"
    assert len(r.hard_blockers) >= 1

test("Discovery-complete packet fails at shortlist (missing selected_destinations)", t_discovery_packet_fails_shortlist)


# Test 2.2: Shortlist-complete packet fails at proposal (missing selected_itinerary)
# Why: Proposal adds selected_itinerary on top of shortlist blockers.
def t_shortlist_packet_fails_proposal():
    pkt = CanonicalPacket(packet_id="short", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "selected_destinations": Slot(value=["Singapore", "Malaysia"], confidence=0.8, authority_level="explicit_user"),
        },
        stage="shortlist")
    r = run_gap_and_decision(pkt, current_stage="proposal")
    assert "selected_itinerary" in r.hard_blockers, \
        f"Proposal should require selected_itinerary. Blockers: {r.hard_blockers}"

test("Shortlist-complete packet fails at proposal (missing selected_itinerary)", t_shortlist_packet_fails_proposal)


# Test 2.3: Proposal-complete packet fails at booking (missing traveler_details, payment_method)
# Why: Booking adds the most blockers. This tests the full escalation.
def t_proposal_packet_fails_booking():
    pkt = CanonicalPacket(packet_id="prop", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "selected_destinations": Slot(value=["Singapore"], confidence=0.8, authority_level="explicit_user"),
            "selected_itinerary": Slot(value="pkg_001", confidence=0.8, authority_level="explicit_user"),
        },
        stage="proposal")
    r = run_gap_and_decision(pkt, current_stage="booking")
    assert "traveler_details" in r.hard_blockers
    assert "payment_method" in r.hard_blockers
    assert len(r.hard_blockers) >= 2

test("Proposal-complete packet fails at booking (2+ new blockers)", t_proposal_packet_fails_booking)


# Test 2.4: Full booking packet → PROCEED_TRAVELER_SAFE
# Why: The full happy path. All 8 booking blockers + all soft blockers (none for booking).
def t_full_booking_packet_succeeds():
    pkt = CanonicalPacket(packet_id="book", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "selected_destinations": Slot(value=["Singapore"], confidence=0.8, authority_level="explicit_user"),
            "selected_itinerary": Slot(value="pkg_001", confidence=0.8, authority_level="explicit_user"),
            "traveler_details": Slot(value={"names": ["John", "Jane", "Baby"]}, confidence=0.9, authority_level="explicit_user"),
            "payment_method": Slot(value="credit_card", confidence=0.9, authority_level="explicit_user"),
        },
        stage="booking")
    r = run_gap_and_decision(pkt, current_stage="booking")
    assert r.decision_state == "PROCEED_TRAVELER_SAFE"
    assert len(r.hard_blockers) == 0
    assert len(r.soft_blockers) == 0

test("Full booking packet → PROCEED_TRAVELER_SAFE", t_full_booking_packet_succeeds)


# Test 2.5: Stage defaults to packet.stage when not overridden
# Why: If caller doesn't pass current_stage, should use packet.stage.
def t_stage_defaults_to_packet_stage():
    pkt = CanonicalPacket(packet_id="def", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)  # no current_stage
    assert r.current_stage == "discovery"
    assert len(r.hard_blockers) == 0  # discovery blockers all filled

test("Stage defaults to packet.stage", t_stage_defaults_to_packet_stage)


# Test 2.6: Stage can be overridden via current_stage parameter
# Why: Tests that the caller can force a different stage than the packet's stage.
def t_stage_override():
    pkt = CanonicalPacket(packet_id="override", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")},
        stage="discovery")
    r = run_gap_and_decision(pkt, current_stage="shortlist")
    assert r.current_stage == "shortlist"
    # Shortlist has 5 blockers, we only have 1 filled
    assert len(r.hard_blockers) == 4

test("Stage override via current_stage parameter", t_stage_override)


# =============================================================================
# DIMENSION 3: CONTRADICTION DETECTION & ROUTING
# =============================================================================
#
# Thinking: Contradictions are the "danger" path. The system has 5 contradiction
# types with different actions:
#   - date_conflict → STOP_NEEDS_REVIEW (most severe)
#   - destination_conflict → ASK_FOLLOWUP
#   - traveler_count_conflict → ASK_FOLLOWUP
#   - origin_conflict → ASK_FOLLOWUP
#   - budget_conflict → BRANCH_OPTIONS (only when no hard blockers)
#
# The key invariants:
#   - Critical contradictions block everything
#   - Date conflict = STOP, not ASK (special case)
#   - Budget contradictions only branch when hard blockers are cleared
#   - General contradictions default to ASK_FOLLOWUP

section("DIMENSION 3: CONTRADICTION DETECTION & ROUTING")


# Test 3.1: Pre-existing date contradiction → STOP_NEEDS_REVIEW
# Why: date_conflict is the only critical contradiction that triggers STOP.
# This is the "circuit breaker" test.
def t_date_contradiction_stops():
    pkt = CanonicalPacket(packet_id="date_stop", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "STOP_NEEDS_REVIEW", f"Date contradiction should STOP, got {r.decision_state}"

test("Pre-existing date contradiction → STOP_NEEDS_REVIEW", t_date_contradiction_stops)


# Test 3.2: Destination contradiction → ASK_FOLLOWUP (not STOP)
# Why: Destination conflict is critical but should ASK, not STOP. Tests the
# branching logic in the decision engine.
def t_destination_contradiction_asks():
    pkt = CanonicalPacket(packet_id="dest_ask", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "destination_city", "values": ["Singapore", "Thailand"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "ASK_FOLLOWUP", f"Destination should ASK, got {r.decision_state}"

test("Destination contradiction → ASK_FOLLOWUP (not STOP)", t_destination_contradiction_asks)


# Test 3.3: Traveler count contradiction → ASK_FOLLOWUP
# Why: Same pattern as destination but for a different field. Tests field
# mapping correctness.
def t_traveler_count_contradiction_asks():
    pkt = CanonicalPacket(packet_id="count_ask", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "traveler_count", "values": [3, 5], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "ASK_FOLLOWUP"

test("Traveler count contradiction → ASK_FOLLOWUP", t_traveler_count_contradiction_asks)


# Test 3.4: Origin contradiction → ASK_FOLLOWUP
# Why: Tests origin field routing in contradiction classification.
def t_origin_contradiction_asks():
    pkt = CanonicalPacket(packet_id="orig_ask", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "origin_city", "values": ["Bangalore", "Mumbai"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "ASK_FOLLOWUP"

test("Origin contradiction → ASK_FOLLOWUP", t_origin_contradiction_asks)


# Test 3.5: Budget contradiction → BRANCH_OPTIONS (when no hard blockers)
# Why: Budget conflict is the only one that branches. But ONLY when hard
# blockers are clear. Tests the conditional branching logic.
def t_budget_contradiction_branches():
    pkt = CanonicalPacket(packet_id="branch", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "budget_range": Slot(value=["budget", "premium"], confidence=0.6, authority_level="explicit_owner"),
        },
        contradictions=[
            {"field_name": "budget_range", "values": ["budget", "premium"], "sources": ["env3", "env4"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "BRANCH_OPTIONS", f"Budget should branch, got {r.decision_state}"
    assert len(r.branch_options) > 0

test("Budget contradiction → BRANCH_OPTIONS (no hard blockers)", t_budget_contradiction_branches)


# Test 3.6: Budget contradiction does NOT branch when hard blockers exist
# Why: The branch path has a guard: `if budget_contradictions and not hard_blockers`.
# If hard blockers exist, ASK_FOLLOWUP should win.
def t_budget_no_branch_with_blockers():
    pkt = CanonicalPacket(packet_id="no_branch", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            # Missing origin_city, travel_dates, traveler_count
            "budget_range": Slot(value=["budget", "premium"], confidence=0.6, authority_level="explicit_owner"),
        },
        contradictions=[
            {"field_name": "budget_range", "values": ["budget", "premium"], "sources": ["env3", "env4"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    # Hard blockers exist (origin_city, travel_dates, traveler_count)
    # So ASK_FOLLOWUP wins over BRANCH_OPTIONS
    assert r.decision_state == "ASK_FOLLOWUP", f"Should ASK when blockers exist, got {r.decision_state}"

test("Budget contradiction does NOT branch when hard blockers exist", t_budget_no_branch_with_blockers)


# Test 3.7: Multi-source contradiction detected from evidence refs
# Why: The detect_contradictions function finds contradictions from evidence
# refs (multiple envelopes with different excerpts). This tests that path.
def t_multi_source_contradiction_detected():
    pkt = CanonicalPacket(packet_id="multi", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(
                value="Singapore",
                confidence=0.7,
                authority_level="explicit_owner",
                evidence_refs=[
                    EvidenceRef(ref_id="r1", envelope_id="env1", evidence_type="text_span", excerpt="Singapore"),
                    EvidenceRef(ref_id="r2", envelope_id="env2", evidence_type="text_span", excerpt="Thailand"),
                ]
            ),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_owner"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_owner"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    # Multi-source with different excerpts should trigger contradiction detection
    assert len(r.contradictions) > 0, "Should detect multi-source contradiction"
    # Destination conflict is critical → ASK_FOLLOWUP (not STOP, because it's not date)
    assert r.decision_state == "ASK_FOLLOWUP"

test("Multi-source contradiction detected from evidence refs", t_multi_source_contradiction_detected)


# Test 3.8: General contradiction (unknown field) → ASK_FOLLOWUP
# Why: Tests the default fallback for contradictions not in the field map.
def t_general_contradiction_asks():
    pkt = CanonicalPacket(packet_id="general", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "some_weird_field": Slot(value="x", confidence=0.5, authority_level="explicit_owner"),
        },
        contradictions=[
            {"field_name": "some_weird_field", "values": ["x", "y"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    # General contradiction is not critical → no stop, no hard blockers → continue
    # Should proceed to next check: no soft blockers → PROCEED_TRAVELER_SAFE
    # Wait, some_weird_field is a fact, not a soft blocker, so soft blockers still exist
    assert r.decision_state == "PROCEED_INTERNAL_DRAFT"  # soft blockers still exist

test("General contradiction → doesn't block (falls through)", t_general_contradiction_asks)


# Test 3.9: Multiple critical contradictions → STOP (date wins)
# Why: If both date AND destination contradictions exist, date should trigger STOP.
def t_multiple_critical_contradictions_date_wins():
    pkt = CanonicalPacket(packet_id="multi_crit", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
            {"field_name": "destination_city", "values": ["Singapore", "Thailand"], "sources": ["env1", "env3"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "STOP_NEEDS_REVIEW"

test("Multiple critical contradictions → date triggers STOP", t_multiple_critical_contradictions_date_wins)


# Test 3.10: Contradiction on alias field (date_window → date_conflict)
# Why: Tests that contradiction classification works with aliased field names.
def t_contradiction_on_alias_field():
    ctype = classify_contradiction("date_window")
    assert ctype == "date_conflict", f"date_window should map to date_conflict, got {ctype}"
    ctype2 = classify_contradiction("budget_total")
    assert ctype2 == "budget_conflict", f"budget_total should map to budget_conflict, got {ctype2}"

test("Contradiction classification works with alias field names", t_contradiction_on_alias_field)


# Test 3.11: Contradiction on unmapped field → general_conflict
# Why: Unknown fields should fall back to general_conflict.
def t_unmapped_field_general_conflict():
    ctype = classify_contradiction("random_field")
    assert ctype == "general_conflict"
    action = get_contradiction_action("general_conflict")
    assert action["action"] == "ASK_FOLLOWUP"
    assert action["priority"] == "medium"

test("Unmapped contradiction field → general_conflict (default ASK)", t_unmapped_field_general_conflict)


# Test 3.12: Contradiction with no hard blockers but date → still STOP
# Why: Date contradiction should STOP even if all hard blockers are filled.
# The contradiction check happens BEFORE blocker check in the decision flow.
def t_date_contradiction_stops_even_with_blockers_filled():
    pkt = CanonicalPacket(packet_id="date_stop2", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "budget_range": Slot(value="mid", confidence=0.8, authority_level="explicit_user"),
            "trip_purpose": Slot(value="leisure", confidence=0.8, authority_level="explicit_user"),
            "traveler_preferences": Slot(value="relaxed", confidence=0.8, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "STOP_NEEDS_REVIEW", \
        f"Date should STOP even with all blockers filled, got {r.decision_state}"

test("Date contradiction → STOP even when all hard blockers filled", t_date_contradiction_stops_even_with_blockers_filled)


# =============================================================================
# DIMENSION 4: DECISION STATE MACHINE (all 5 states + transitions)
# =============================================================================
#
# Thinking: The decision state machine is a priority-ordered cascade:
#   1. Critical contradictions → STOP or ASK
#   2. Hard blockers → ASK
#   3. Budget contradictions → BRANCH
#   4. Confidence >= threshold AND no soft blockers → PROCEED_TRAVELER_SAFE
#   5. Soft blockers → PROCEED_INTERNAL_DRAFT
#   6. Confidence < threshold → PROCEED_INTERNAL_DRAFT
#   7. Fallback → PROCEED_TRAVELER_SAFE
#
# Each state needs at least one test. Some states have sub-variants.

section("DIMENSION 4: DECISION STATE MACHINE")


# Test 4.1: ASK_FOLLOWUP — when hard blockers exist
# Why: The most common decision. Tests that questions are generated.
def t_ask_followup_has_questions():
    pkt = CanonicalPacket(packet_id="ask", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "ASK_FOLLOWUP"
    assert len(r.follow_up_questions) == 3  # 3 blockers remaining
    # Questions should have the right structure
    for q in r.follow_up_questions:
        assert "question" in q
        assert "priority" in q
        assert q["priority"] == "critical"
        assert "field_name" in q

test("ASK_FOLLOWUP → questions generated with correct structure", t_ask_followup_has_questions)


# Test 4.2: PROCEED_TRAVELER_SAFE → complete packet, no questions, no blockers
# Why: The "happy path" decision. All fields filled, no contradictions.
def t_proceed_traveler_safe():
    pkt = CanonicalPacket(packet_id="safe", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "budget_range": Slot(value="mid", confidence=0.8, authority_level="explicit_user"),
            "trip_purpose": Slot(value="leisure", confidence=0.8, authority_level="explicit_user"),
            "traveler_preferences": Slot(value="relaxed", confidence=0.8, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "PROCEED_TRAVELER_SAFE"
    assert len(r.follow_up_questions) == 0
    assert len(r.hard_blockers) == 0
    assert len(r.soft_blockers) == 0

test("PROCEED_TRAVELER_SAFE → no questions, no blockers", t_proceed_traveler_safe)


# Test 4.3: PROCEED_INTERNAL_DRAFT → soft blockers exist
# Why: The system can draft internally but isn't confident enough to share
# with travelers. Tests soft blocker question generation.
def t_proceed_internal_draft():
    pkt = CanonicalPacket(packet_id="draft", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "PROCEED_INTERNAL_DRAFT"
    assert len(r.soft_blockers) > 0
    # Soft blocker questions should exist
    assert len(r.follow_up_questions) > 0

test("PROCEED_INTERNAL_DRAFT → soft blocker questions generated", t_proceed_internal_draft)


# Test 4.4: BRANCH_OPTIONS → budget contradiction, no blockers
# Why: Multiple valid paths. Tests branch option generation.
def t_branch_options_structure():
    pkt = CanonicalPacket(packet_id="branch2", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "budget_range": Slot(value=["budget", "premium"], confidence=0.6, authority_level="explicit_owner"),
        },
        contradictions=[
            {"field_name": "budget_range", "values": ["budget", "premium"], "sources": ["env3", "env4"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "BRANCH_OPTIONS"
    assert len(r.branch_options) > 0
    assert "label" in r.branch_options[0]
    assert "description" in r.branch_options[0]

test("BRANCH_OPTIONS → branch options have correct structure", t_branch_options_structure)


# Test 4.5: STOP_NEEDS_REVIEW → date contradiction
# Why: The "circuit breaker." Already tested in 3.1, but re-verify the output structure.
def t_stop_needs_review_structure():
    pkt = CanonicalPacket(packet_id="stop2", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "STOP_NEEDS_REVIEW"
    assert len(r.follow_up_questions) > 0
    assert r.rationale.get("reason") is not None

test("STOP_NEEDS_REVIEW → output structure correct", t_stop_needs_review_structure)


# Test 4.6: Exactly one decision state is returned (never None, never multiple)
# Why: The contract says "exactly one of 5 output states." This is an invariant.
def t_exactly_one_decision():
    valid_states = {"ASK_FOLLOWUP", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE", "BRANCH_OPTIONS", "STOP_NEEDS_REVIEW"}
    packets = [
        CanonicalPacket(packet_id="e1", created_at="now", last_updated="now", stage="discovery"),
        CanonicalPacket(packet_id="e2", created_at="now", last_updated="now",
            facts={
                "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
                "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
                "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
                "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
                "budget_range": Slot(value="mid", confidence=0.8, authority_level="explicit_user"),
                "trip_purpose": Slot(value="leisure", confidence=0.8, authority_level="explicit_user"),
                "traveler_preferences": Slot(value="relaxed", confidence=0.8, authority_level="explicit_user"),
            }, stage="discovery"),
        CanonicalPacket(packet_id="e3", created_at="now", last_updated="now",
            facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
            stage="discovery"),
    ]
    for pkt in packets:
        r = run_gap_and_decision(pkt)
        assert r.decision_state in valid_states, f"Invalid state: {r.decision_state}"

test("Exactly one valid decision state returned (never None, never multiple)", t_exactly_one_decision)


# =============================================================================
# DIMENSION 5: CONFIDENCE SCORING
# =============================================================================
#
# Thinking: Confidence is authority-weighted:
#   - Each fact: confidence * AUTHORITY_WEIGHTS[authority_level]
#   - Averaged across all facts
#   - Hypotheses add 0.2 * avg(hyp_conf * 0.5) — but soft_hypothesis weight = 0.0
#   - Unknowns penalize: -0.1 per unknown
#   - Clamped to [0.0, 1.0]
#
# Key invariants:
#   - Empty packet → 0.0
#   - Hypotheses don't meaningfully boost (weight = 0.0)
#   - More unknowns → lower confidence
#   - High authority + high confidence → high score

section("DIMENSION 5: CONFIDENCE SCORING")


# Test 5.1: Empty packet → confidence = 0.0
# Why: No facts, no hypotheses, no unknowns → 0.0 baseline.
def t_confidence_empty_packet():
    pkt = CanonicalPacket(packet_id="c0", created_at="now", last_updated="now")
    c = calculate_confidence(pkt)
    assert c == 0.0, f"Empty packet should be 0.0, got {c}"

test("Empty packet → confidence = 0.0", t_confidence_empty_packet)


# Test 5.2: Single high-confidence fact with high authority → high confidence
# Why: Tests the basic calculation: 0.95 * 0.95 = 0.9025
def t_confidence_single_strong_fact():
    pkt = CanonicalPacket(packet_id="c1", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.95, authority_level="explicit_user")})
    c = calculate_confidence(pkt)
    expected = 0.95 * 0.95  # confidence * auth_weight
    assert abs(c - expected) < 0.01, f"Expected ~{expected}, got {c}"

test("Single high-confidence fact → confidence ≈ 0.90", t_confidence_single_strong_fact)


# Test 5.3: Hypotheses don't boost confidence (weight = 0.0)
# Why: The critical fix from the review. soft_hypothesis weight = 0.0 means
# hypotheses should NOT affect the fact_weight at all. They add 0.0 to the
# hypothesis_weight since 0.0 * 0.5 = 0.0.
# Actually, wait — the code does: hypothesis_weight += slot.confidence * 0.5
# NOT hypothesis_weight += slot.confidence * AUTHORITY_WEIGHTS["soft_hypothesis"]
# So hypotheses still add some via the * 0.5 discount, even though their
# AUTHORITY_WEIGHT is 0.0.
# The AUTHORITY_WEIGHTS are only used for facts. Hypotheses get a flat 0.5x.
# So this test verifies: hypotheses DO add a little, but much less than facts.
def t_confidence_hypothesis_discounted():
    # Packet with only a hypothesis
    pkt = CanonicalPacket(packet_id="c_hyp", created_at="now", last_updated="now",
        hypotheses={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="soft_hypothesis")})
    c = calculate_confidence(pkt)
    # fact_weight = 0.0 (no facts)
    # hypothesis_weight = 0.9 * 0.5 / 1 = 0.45
    # raw = 0.0 + (0.45 * 0.2) - 0.0 = 0.09
    expected = 0.09
    assert abs(c - expected) < 0.01, f"Expected ~{expected}, got {c}"

test("Hypothesis confidence is heavily discounted (0.5x * 0.2x = 0.1x)", t_confidence_hypothesis_discounted)


# Test 5.4: More unknowns → lower confidence (penalty of 0.1 each)
# Why: Each unknown penalizes by 0.1. Tests the penalty mechanism.
def t_confidence_unknown_penalty():
    pkt = CanonicalPacket(packet_id="c_unk", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")},
        unknowns=[
            UnknownField(field_name="dates", reason="not_present_in_source"),
            UnknownField(field_name="budget", reason="not_present_in_source"),
        ])
    c = calculate_confidence(pkt)
    # fact_weight = 0.9 * 0.95 = 0.855 / 1 = 0.855
    # hypothesis_weight = 0.0
    # unknown_penalty = 2 * 0.1 = 0.2
    # raw = 0.855 + 0.0 - 0.2 = 0.655
    expected = 0.655
    assert abs(c - expected) < 0.01, f"Expected ~{expected}, got {c}"

test("Unknown fields penalize confidence (0.1 each)", t_confidence_unknown_penalty)


# Test 5.5: Confidence is clamped to [0.0, 1.0]
# Why: With enough unknowns, raw confidence could go negative. Should clamp to 0.0.
def t_confidence_clamped_to_zero():
    pkt = CanonicalPacket(packet_id="c_neg", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.3, authority_level="explicit_owner")},
        unknowns=[UnknownField(field_name=f"f{i}", reason="x") for i in range(20)])
    c = calculate_confidence(pkt)
    # fact_weight = 0.3 * 0.80 = 0.24 / 1 = 0.24
    # unknown_penalty = 20 * 0.1 = 2.0
    # raw = 0.24 - 2.0 = -1.76 → clamped to 0.0
    assert c == 0.0, f"Should clamp to 0.0, got {c}"

test("Confidence clamped to 0.0 when heavily penalized", t_confidence_clamped_to_zero)


# Test 5.6: Confidence clamped to 1.0 when very high
# Why: Should never exceed 1.0.
def t_confidence_clamped_to_one():
    # Hard to exceed 1.0 with the averaging formula, but test the clamp exists
    pkt = CanonicalPacket(packet_id="c_max", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=1.0, authority_level="manual_override"),
            "origin_city": Slot(value="Bangalore", confidence=1.0, authority_level="manual_override"),
        })
    c = calculate_confidence(pkt)
    assert c <= 1.0, f"Should not exceed 1.0, got {c}"
    # manual_override weight = 1.0, confidence = 1.0 → avg = 1.0
    assert c == 1.0

test("Confidence clamped to 1.0 (manual_override at 1.0)", t_confidence_clamped_to_one)


# Test 5.7: Multiple facts averaged, not summed
# Why: Confidence should be an average across facts, not a sum.
# Two facts at 0.9 with weight 0.95 should give ~0.855, not 1.71.
def t_confidence_averaged_not_summed():
    pkt = CanonicalPacket(packet_id="c_avg", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
        })
    c = calculate_confidence(pkt)
    # Each: 0.9 * 0.95 = 0.855, avg = (0.855 + 0.855) / 2 = 0.855
    expected = 0.855
    assert abs(c - expected) < 0.01, f"Expected ~{expected}, got {c}"

test("Multiple facts averaged (not summed)", t_confidence_averaged_not_summed)


# Test 5.8: Low authority fact → lower weight
# Why: explicit_owner (0.80) < explicit_user (0.95). Tests authority weighting.
def t_confidence_lower_authority():
    pkt = CanonicalPacket(packet_id="c_low", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_owner")})
    c_owner = calculate_confidence(pkt)

    pkt2 = CanonicalPacket(packet_id="c_high", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")})
    c_user = calculate_confidence(pkt2)

    assert c_owner < c_user, f"explicit_owner ({c_owner}) should be < explicit_user ({c_user})"

test("Lower authority → lower confidence (explicit_owner < explicit_user)", t_confidence_lower_authority)


# =============================================================================
# DIMENSION 6: ALIAS RESOLUTION
# =============================================================================
#
# Thinking: The FIELD_ALIASES map lets the system find fields by alternate names.
# This is tested through resolve_field(). Key invariants:
#   - Direct match takes priority over alias match
#   - Facts take priority over derived_signals which take priority over hypotheses
#   - Aliases work across all layers

section("DIMENSION 6: ALIAS RESOLUTION")


# Test 6.1: Alias "departure_city" resolves to "origin_city"
# Why: Tests that an alias in facts resolves the canonical field.
def t_alias_departure_city():
    pkt = CanonicalPacket(packet_id="alias1", created_at="now", last_updated="now",
        facts={"departure_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")})
    slot = resolve_field(pkt, "origin_city")
    assert slot is not None
    assert slot.value == "Bangalore"
    assert field_fills_blocker(slot)

test("Alias 'departure_city' resolves to 'origin_city'", t_alias_departure_city)


# Test 6.2: Alias "dest_city" resolves to "destination_city"
# Why: Another alias test.
def t_alias_dest_city():
    pkt = CanonicalPacket(packet_id="alias2", created_at="now", last_updated="now",
        facts={"dest_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")})
    slot = resolve_field(pkt, "destination_city")
    assert slot is not None
    assert slot.value == "Singapore"

test("Alias 'dest_city' resolves to 'destination_city'", t_alias_dest_city)


# Test 6.3: Alias "date_window" resolves to "travel_dates"
# Why: Tests date alias.
def t_alias_date_window():
    pkt = CanonicalPacket(packet_id="alias3", created_at="now", last_updated="now",
        facts={"date_window": Slot(value="March 2026", confidence=0.8, authority_level="explicit_owner")})
    slot = resolve_field(pkt, "travel_dates")
    assert slot is not None
    assert slot.value == "March 2026"

test("Alias 'date_window' resolves to 'travel_dates'", t_alias_date_window)


# Test 6.4: Alias "group_size" resolves to "traveler_count"
# Why: Tests traveler count alias.
def t_alias_group_size():
    pkt = CanonicalPacket(packet_id="alias4", created_at="now", last_updated="now",
        facts={"group_size": Slot(value=5, confidence=0.9, authority_level="explicit_owner")})
    slot = resolve_field(pkt, "traveler_count")
    assert slot is not None
    assert slot.value == 5
    assert field_fills_blocker(slot)

test("Alias 'group_size' resolves to 'traveler_count'", t_alias_group_size)


# Test 6.5: Alias works in derived_signals layer
# Why: Aliases should work across all layers, not just facts.
def t_alias_in_derived_signals():
    pkt = CanonicalPacket(packet_id="alias5", created_at="now", last_updated="now",
        derived_signals={"departure_city": Slot(value="Bangalore", confidence=0.7, authority_level="derived_signal")})
    slot = resolve_field(pkt, "origin_city")
    assert slot is not None
    assert slot.value == "Bangalore"
    assert field_fills_blocker(slot)  # derived_signal should fill blocker

test("Alias works in derived_signals layer", t_alias_in_derived_signals)


# Test 6.6: Alias works in hypotheses layer
# Why: Aliases should work for hypotheses too (but hypotheses don't fill blockers).
def t_alias_in_hypotheses():
    pkt = CanonicalPacket(packet_id="alias6", created_at="now", last_updated="now",
        hypotheses={"dest_city": Slot(value="Singapore", confidence=0.5, authority_level="soft_hypothesis")})
    slot = resolve_field(pkt, "destination_city")
    assert slot is not None
    assert slot.value == "Singapore"
    assert not field_fills_blocker(slot)  # hypothesis should NOT fill blocker

test("Alias works in hypotheses layer (but doesn't fill blocker)", t_alias_in_hypotheses)


# Test 6.7: Direct match preferred over alias match
# Why: If both "origin_city" and "departure_city" exist, direct match wins.
def t_direct_match_preferred_over_alias():
    pkt = CanonicalPacket(packet_id="alias7", created_at="now", last_updated="now",
        facts={
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "departure_city": Slot(value="Mumbai", confidence=0.5, authority_level="explicit_owner"),
        })
    slot = resolve_field(pkt, "origin_city")
    assert slot.value == "Bangalore", f"Direct match should win, got {slot.value}"

test("Direct match preferred over alias match", t_direct_match_preferred_over_alias)


# Test 6.8: Facts preferred over derived_signals for same field
# Why: resolve_field checks facts → derived_signals → hypotheses in order.
def t_facts_preferred_over_derived_signals():
    pkt = CanonicalPacket(packet_id="alias8", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")},
        derived_signals={"destination_city": Slot(value="Malaysia", confidence=0.7, authority_level="derived_signal")})
    slot = resolve_field(pkt, "destination_city")
    assert slot.value == "Singapore", f"Facts should win, got {slot.value}"

test("Facts preferred over derived_signals for same field", t_facts_preferred_over_derived_signals)


# Test 6.9: Unknown field → resolve_field returns None
# Why: If no match exists anywhere, should return None (not crash).
def t_unknown_field_returns_none():
    pkt = CanonicalPacket(packet_id="alias9", created_at="now", last_updated="now")
    slot = resolve_field(pkt, "nonexistent_field")
    assert slot is None

test("Unknown field → resolve_field returns None", t_unknown_field_returns_none)


# =============================================================================
# DIMENSION 7: FOLLOW-UP QUESTION GENERATION
# =============================================================================
#
# Thinking: Questions are generated for blockers. They have:
#   - field_name
#   - question (from template)
#   - priority (critical for hard blockers, high/medium for soft)
#   - can_infer (True if hypothesis exists)
#   - inference_confidence (hypothesis.conf * 0.3 for hard blockers)
#   - suggested_values (from hypothesis)

section("DIMENSION 7: FOLLOW-UP QUESTION GENERATION")


# Test 7.1: Question templates are populated for all hard blockers
# Why: Each hard blocker should get a human-readable question.
def t_question_templates_populated():
    pkt = CanonicalPacket(packet_id="q1", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.follow_up_questions) == 3
    for q in r.follow_up_questions:
        assert q["question"] != ""
        assert q["question"] != f"Can you provide details for: {q['field_name']}?"  # Should use template

test("Question templates populated for all hard blockers", t_question_templates_populated)


# Test 7.2: Questions ordered by priority (critical first)
# Why: Hard blockers should be critical, soft blockers high/medium.
def t_questions_ordered_by_priority():
    pkt = CanonicalPacket(packet_id="q2", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    priorities = [q["priority"] for q in r.follow_up_questions]
    assert all(p == "critical" for p in priorities), f"All should be critical, got {priorities}"

test("Hard blocker questions all have 'critical' priority", t_questions_ordered_by_priority)


# Test 7.3: Hypothesis provides can_infer hint with discounted confidence
# Why: When a hypothesis exists for a blocked field, the question should
# include can_infer=True and a suggested value.
def t_question_can_infer_hint():
    pkt = CanonicalPacket(packet_id="q3", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        hypotheses={"destination_city": Slot(value="Singapore", confidence=0.6, authority_level="soft_hypothesis")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    dest_q = [q for q in r.follow_up_questions if q["field_name"] == "destination_city"][0]
    assert dest_q["can_infer"] is True
    assert dest_q["inference_confidence"] > 0.0
    assert "Singapore" in dest_q["suggested_values"]

test("Hypothesis provides can_infer hint with suggested value", t_question_can_infer_hint)


# Test 7.4: Soft blocker questions generated with high/medium priority
# Why: Soft blockers should appear in questions when they're the reason for
# the PROCEED_INTERNAL_DRAFT decision.
def t_soft_blocker_questions():
    pkt = CanonicalPacket(packet_id="q4", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert r.decision_state == "PROCEED_INTERNAL_DRAFT"
    assert len(r.follow_up_questions) == 3  # 3 soft blockers
    for q in r.follow_up_questions:
        assert q["priority"] in ("high", "medium")

test("Soft blocker questions generated with high/medium priority", t_soft_blocker_questions)


# Test 7.5: Unknown field name gets default question
# Why: If a blocker field isn't in the template dict, it should get a default.
def t_default_question_for_unknown_field():
    # We can't easily add a new MVB field, but we can test _generate_question directly
    _generate_question = ns['_generate_question']
    q = _generate_question("completely_unknown_field")
    assert "completely_unknown_field" in q

test("Unknown field name gets default question", t_default_question_for_unknown_field)


# =============================================================================
# DIMENSION 8: EDGE CASES & ROBUSTNESS
# =============================================================================
#
# Thinking: What could go wrong with weird inputs?
#   - Packet with only derived_signals (no facts at all)
#   - Contradiction with empty values list
#   - Zero-confidence facts
#   - Very long field values
#   - Packet with contradictions but they're the same value (not really a contradiction)
#   - Multiple hypotheses for the same field
#   - Stage not in MVB_BY_STAGE (should default to discovery)

section("DIMENSION 8: EDGE CASES & ROBUSTNESS")


# Test 8.1: Packet with only derived_signals (no facts) → blockers filled
# Why: Tests that derived_signals alone can satisfy all blockers.
def t_only_derived_signals():
    pkt = CanonicalPacket(packet_id="edge1", created_at="now", last_updated="now",
        derived_signals={
            "destination_city": Slot(value="Singapore", confidence=0.7, authority_level="derived_signal"),
            "origin_city": Slot(value="Bangalore", confidence=0.7, authority_level="derived_signal"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.7, authority_level="derived_signal"),
            "traveler_count": Slot(value=3, confidence=0.7, authority_level="derived_signal"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0, f"Derived signals should fill all blockers, got {r.hard_blockers}"

test("Only derived_signals (no facts) → all blockers filled", t_only_derived_signals)


# Test 8.2: Zero-confidence fact → still fills blocker (but confidence is low)
# Why: A fact is a fact, even with 0.0 confidence. The blocker is filled,
# but the overall confidence score will be low.
def t_zero_confidence_fact_fills_blocker():
    pkt = CanonicalPacket(packet_id="edge2", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.0, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
            "budget_range": Slot(value="mid", confidence=0.8, authority_level="explicit_user"),
            "trip_purpose": Slot(value="leisure", confidence=0.8, authority_level="explicit_user"),
            "traveler_preferences": Slot(value="relaxed", confidence=0.8, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.hard_blockers) == 0  # Blocker is filled
    # But confidence should be lower due to the 0.0 fact
    c = calculate_confidence(pkt)
    assert c < 0.9, f"Confidence should be reduced due to 0.0 fact, got {c}"

test("Zero-confidence fact still fills blocker (confidence lowered)", t_zero_confidence_fact_fills_blocker)


# Test 8.3: Multiple contradictions with same values → detected as contradiction
# Why: The pre-existing contradictions list is passed through. Even if values
# are the same, if it's in the list, it counts.
def t_pre_existing_contradictions_passed_through():
    pkt = CanonicalPacket(packet_id="edge3", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        contradictions=[
            {"field_name": "travel_dates", "values": ["2026-03-15", "2026-04-01"], "sources": ["env1", "env2"]},
        ],
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.contradictions) >= 1
    assert r.decision_state == "STOP_NEEDS_REVIEW"

test("Pre-existing contradictions passed through", t_pre_existing_contradictions_passed_through)


# Test 8.4: Empty contradictions list → no contradictions detected
# Why: Baseline. If no contradictions and no blockers (but soft blockers exist),
# should go to PROCEED_INTERNAL_DRAFT.
def t_no_contradictions():
    pkt = CanonicalPacket(packet_id="edge4", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    r = run_gap_and_decision(pkt)
    assert len(r.contradictions) == 0

test("No contradictions when none provided and no multi-source evidence", t_no_contradictions)


# Test 8.5: Multiple unknowns stack their penalties
# Why: 5 unknowns → 0.5 penalty. Tests that penalties accumulate.
def t_multiple_unknowns_stack_penalty():
    pkt = CanonicalPacket(packet_id="edge5", created_at="now", last_updated="now",
        facts={"destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user")},
        unknowns=[UnknownField(field_name=f"f{i}", reason="x") for i in range(5)])
    c = calculate_confidence(pkt)
    # fact = 0.9 * 0.95 = 0.855 / 1 = 0.855
    # penalty = 5 * 0.1 = 0.5
    # raw = 0.855 - 0.5 = 0.355
    expected = 0.355
    assert abs(c - expected) < 0.01, f"Expected ~{expected}, got {c}"

test("Multiple unknowns stack penalty (5 unknowns = -0.5)", t_multiple_unknowns_stack_penalty)


# Test 8.6: Invalid stage defaults to discovery MVB
# Why: If stage is not in MVB_BY_STAGE, should default to discovery.
def t_invalid_stage_defaults_to_discovery_mvb():
    pkt = CanonicalPacket(packet_id="edge6", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="nonexistent_stage")
    r = run_gap_and_decision(pkt, current_stage="nonexistent_stage")
    # Should use empty MVB (not found → defaults to empty dict → no blockers)
    # Wait, let me check: MVB_BY_STAGE.get("nonexistent_stage", MVB_BY_STAGE["discovery"])
    # Actually it defaults to discovery MVB. So we should still have blockers.
    # Hmm, let me check the code... run_gap_and_decision uses:
    # mvb = mvb_config or MVB_BY_STAGE.get(stage, MVB_BY_STAGE["discovery"])
    # So it defaults to discovery. The test is that it doesn't crash.
    assert r.current_stage == "nonexistent_stage"
    # Hard blockers should still be the discovery ones (4)
    assert len(r.hard_blockers) == 3  # 1 filled (origin_city), 3 remaining

test("Invalid stage doesn't crash (defaults to discovery MVB)", t_invalid_stage_defaults_to_discovery_mvb)


# Test 8.7: Custom MVB config overrides the default
# Why: The pipeline accepts a custom mvb_config parameter.
def t_custom_mvb_config():
    pkt = CanonicalPacket(packet_id="edge7", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_user"),
        },
        stage="discovery")
    custom_mvb = {
        "hard_blockers": ["destination_city", "origin_city"],
        "soft_blockers": [],
    }
    r = run_gap_and_decision(pkt, mvb_config=custom_mvb)
    assert len(r.hard_blockers) == 0  # Only 2 blockers, both filled
    assert len(r.soft_blockers) == 0  # No soft blockers defined

test("Custom MVB config overrides default", t_custom_mvb_config)


# Test 8.8: Custom confidence threshold changes decision
# Why: A higher threshold should make it harder to PROCEED_TRAVELER_SAFE.
def t_custom_confidence_threshold():
    # Build a complete packet with moderate confidence
    pkt = CanonicalPacket(packet_id="edge8", created_at="now", last_updated="now",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_owner"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner"),
            "travel_dates": Slot(value="2026-03-15", confidence=0.9, authority_level="explicit_owner"),
            "traveler_count": Slot(value=3, confidence=0.9, authority_level="explicit_owner"),
            "budget_range": Slot(value="mid", confidence=0.9, authority_level="explicit_owner"),
            "trip_purpose": Slot(value="leisure", confidence=0.9, authority_level="explicit_owner"),
            "traveler_preferences": Slot(value="relaxed", confidence=0.9, authority_level="explicit_owner"),
        },
        stage="discovery")
    # explicit_owner weight = 0.80, confidence = 0.9 → avg = 0.72
    # This is above default threshold (0.6) → PROCEED_TRAVELER_SAFE
    r_default = run_gap_and_decision(pkt)
    assert r_default.decision_state == "PROCEED_TRAVELER_SAFE", \
        f"Default threshold: expected PROCEED_TRAVELER_SAFE, got {r_default.decision_state}"
    # With threshold=0.80: 0.72 < 0.80 → PROCEED_INTERNAL_DRAFT
    r_high = run_gap_and_decision(pkt, confidence_threshold=0.80)
    assert r_high.decision_state == "PROCEED_INTERNAL_DRAFT", \
        f"High threshold: expected PROCEED_INTERNAL_DRAFT, got {r_high.decision_state}"

test("Custom confidence threshold can change decision", t_custom_confidence_threshold)


# Test 8.9: All four authority levels that are facts → all fill blockers
# Why: manual_override, explicit_user, imported_structured, explicit_owner
# are all fact-level. Each should fill a blocker independently.
def t_all_fact_authorities_fill_blocker():
    for auth in ["manual_override", "explicit_user", "imported_structured", "explicit_owner"]:
        slot = Slot(value="X", confidence=0.9, authority_level=auth)
        assert field_fills_blocker(slot), f"{auth} should fill blocker"

test("All fact-level authorities (manual_override, explicit_user, imported_structured, explicit_owner) fill blockers", t_all_fact_authorities_fill_blocker)


# Test 8.10: Hypothesis authority does NOT fill blocker
# Why: The flip side of 8.9.
def t_hypothesis_authority_does_not_fill():
    slot = Slot(value="X", confidence=0.99, authority_level="soft_hypothesis")
    assert not field_fills_blocker(slot), "soft_hypothesis should NOT fill blocker"

test("soft_hypothesis does NOT fill blocker (even at 0.99 confidence)", t_hypothesis_authority_does_not_fill)


# Test 8.11: DecisionResult.to_dict() is JSON serializable
# Why: The output should be usable as a data transfer object.
def t_decision_result_serializable():
    pkt = CanonicalPacket(packet_id="serial", created_at="now", last_updated="now",
        facts={"origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_owner")},
        stage="discovery")
    r = run_gap_and_decision(pkt)
    d = r.to_dict()
    # Should not raise
    json.dumps(d, default=str)

test("DecisionResult.to_dict() is JSON serializable", t_decision_result_serializable)


# =============================================================================
# SUMMARY
# =============================================================================

section("SUMMARY")
print(f"\n  Passed:  {_passed}")
print(f"  Failed:  {_failed}")
print(f"  Errors:  {_errors}")
print(f"  Total:   {_passed + _failed + _errors}")
print(f"  Rate:    {_passed}/{_passed + _failed + _errors} = {_passed/(_passed+_failed+_errors)*100:.0f}%")

if _failed > 0:
    print(f"\n  FAILURES:")
    for status, name, msg in _results:
        if status == "FAIL":
            print(f"    ✗ {name}: {msg}")
if _errors > 0:
    print(f"\n  ERRORS:")
    for status, name, msg in _results:
        if status == "ERR":
            print(f"    ✗ {name}: {msg}")

sys.exit(0 if (_failed == 0 and _errors == 0) else 1)
