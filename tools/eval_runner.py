#!/usr/bin/env python3
"""
Eval Runner - Validate fixtures against NB02 decision engine.

This tool runs policy-only and end-to-end evaluations of test fixtures
through the NB02 decision engine, validating decision states, blockers,
and follow-up questions.

Usage:
    cd /Users/pranay/Projects/travel_agency_agent
    python tools/eval_runner.py
"""

import json
import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add src to path
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from intake.packet_models import CanonicalPacket, Slot, EvidenceRef, UnknownField
from intake.decision import run_gap_and_decision, DecisionResult, LEGACY_ALIASES

# Add fixtures path
sys.path.insert(0, PROJECT_ROOT)

from data.fixtures.raw_fixtures import RAW_FIXTURES
from data.fixtures.packet_fixtures import PACKET_FIXTURES

print(f"Raw fixtures: {len(RAW_FIXTURES)}")
print(f"Packet fixtures: {len(PACKET_FIXTURES)}")


@dataclass
class EvalResult:
    fixture_id: str
    mode: str
    passed: bool
    checks: List[Dict[str, Any]]
    decision_state_actual: str
    decision_state_expected: str
    errors: List[str]


def packet_from_raw_fixture(fixture: Dict[str, Any]) -> CanonicalPacket:
    """Convert a raw fixture's expected extracted fields into a CanonicalPacket."""
    facts = {}
    expected = fixture["expected"]
    extracted = expected.get("extracted_fields", {})

    for field_name, field_info in extracted.items():
        # Handle both dict and simple string values
        if isinstance(field_info, dict):
            value = field_info.get("value")
            auth = field_info.get("authority", "explicit_owner")
            conf = field_info.get("confidence", 0.8)
        else:
            value = field_info
            auth = "explicit_owner"
            conf = 0.8

        # Map v0.1 field names to v0.2 canonical names if needed
        canonical_name = LEGACY_ALIASES.get(field_name, field_name)
        facts[canonical_name] = Slot(value=value, confidence=conf, authority_level=auth)

    # Build unknowns
    unknowns = []
    for uf in expected.get("expected_unknowns", []):
        unknowns.append(UnknownField(field_name=uf, reason="not_extracted_yet"))

    # Build contradictions from expected
    contradictions = []
    for ctype in expected.get("expected_contradictions", []):
        # v0.2: Map to canonical field names
        field_map = {
            "date_conflict": "date_window",
            "destination_conflict": "destination_candidates",
            "budget_conflict": "budget_min",
            "traveler_count_conflict": "party_size",
            "origin_conflict": "origin_city",
        }
        fname = field_map.get(ctype, ctype)
        # Try to extract values from the facts
        if fname in facts and isinstance(facts[fname].value, list):
            values = facts[fname].value
        else:
            values = ["value_a", "value_b"]
        contradictions.append({
            "field_name": fname,
            "values": values,
            "sources": ["fixture_source"]
        })

    return CanonicalPacket(
        packet_id=fixture["fixture_id"],
        facts=facts,
        unknowns=unknowns,
        contradictions=contradictions,
        stage="discovery",
    )


def evaluate_packet_fixture(fixture: Dict[str, Any]) -> EvalResult:
    """Evaluate a CanonicalPacket fixture through NB02."""
    checks = []
    errors = []
    expected = fixture["expected"]

    # v0.2: Get packet from fixture
    packet = fixture.get("packet")
    if packet is None:
        # If no packet, create one from extracted fields
        packet = packet_from_raw_fixture(fixture)

    try:
        decision = run_gap_and_decision(packet)
    except Exception as e:
        return EvalResult(
            fixture_id=fixture["fixture_id"],
            mode="policy",
            passed=False,
            checks=[],
            decision_state_actual="ERROR",
            decision_state_expected=expected.get("nb02_decision_state", expected.get("decision_state", "unknown")),
            errors=[str(e)],
        )

    expected_state = expected.get("nb02_decision_state", expected.get("decision_state"))

    # Check 1: Decision state correctness
    state_ok = decision.decision_state == expected_state
    checks.append({
        "check": "decision_state",
        "passed": state_ok,
        "expected": expected_state,
        "actual": decision.decision_state,
    })

    # Check 2: Hard blocker correctness
    expected_hard = expected.get("nb02_hard_blockers", expected.get("hard_blockers", []))
    if expected_hard:
        expected_blockers = set(expected_hard) if isinstance(expected_hard, list) else {expected_hard}
        actual_blockers = set(decision.hard_blockers)
        blockers_ok = expected_blockers == actual_blockers
        checks.append({
            "check": "hard_blockers",
            "passed": blockers_ok,
            "expected": sorted(expected_blockers),
            "actual": sorted(actual_blockers),
        })

    # Check 3: Question count minimum
    if "question_count_min" in expected:
        min_q = expected["question_count_min"]
        actual_q = len(decision.follow_up_questions)
        q_ok = actual_q >= min_q
        checks.append({
            "check": "question_count_min",
            "passed": q_ok,
            "expected_min": min_q,
            "actual": actual_q,
        })

    passed = all(c["passed"] for c in checks)

    return EvalResult(
        fixture_id=fixture["fixture_id"],
        mode="policy",
        passed=passed,
        checks=checks,
        decision_state_actual=decision.decision_state,
        decision_state_expected=expected_state,
        errors=errors,
    )


def evaluate_raw_fixture(fixture: Dict[str, Any]) -> EvalResult:
    """Evaluate a raw fixture through simulated NB01 → NB02."""
    packet = packet_from_raw_fixture(fixture)
    expected = fixture["expected"]

    policy_fixture = {
        "fixture_id": fixture["fixture_id"],
        "packet": packet,
        "expected": expected,
    }

    return evaluate_packet_fixture(policy_fixture)


# Run Mode 2: Policy-Only (Packet fixtures)
print("\n" + "=" * 60)
print("  MODE 2: Policy-Only (CanonicalPacket → NB02)")
print("=" * 60)

policy_results = []
for fid, fixture in PACKET_FIXTURES.items():
    result = evaluate_packet_fixture(fixture)
    policy_results.append(result)
    status = "PASS" if result.passed else "FAIL"
    print(f"  [{status}] {fid}: {result.decision_state_actual} (expected: {result.decision_state_expected})")
    if result.errors:
        for e in result.errors:
            print(f"         ERROR: {e}")

# Run Mode 1: End-to-End (Raw fixtures)
print("\n" + "=" * 60)
print("  MODE 1: End-to-End (Raw → NB02)")
print("=" * 60)

e2e_results = []
for fid, fixture in RAW_FIXTURES.items():
    result = evaluate_raw_fixture(fixture)
    e2e_results.append(result)
    status = "PASS" if result.passed else "FAIL"
    print(f"  [{status}] {fid}: {result.decision_state_actual} (expected: {result.decision_state_expected})")
    if result.errors:
        for e in result.errors:
            print(f"         ERROR: {e}")

# Summary
print("\n" + "=" * 60)
print("  EVALUATION SUMMARY")
print("=" * 60)

policy_pass = sum(1 for r in policy_results if r.passed)
e2e_pass = sum(1 for r in e2e_results if r.passed)
all_pass = policy_pass + e2e_pass
all_total = len(policy_results) + len(e2e_results)

print(f"\n  Mode 2 (Policy-Only): {policy_pass}/{len(policy_results)} passed")
print(f"  Mode 1 (End-to-End): {e2e_pass}/{len(e2e_results)} passed")
print(f"\n  Overall: {all_pass}/{all_total} passed ({all_pass/all_total*100:.0f}%)")

# Save results
all_results = []
for r in policy_results + e2e_results:
    all_results.append({
        "fixture_id": r.fixture_id,
        "mode": r.mode,
        "passed": r.passed,
        "decision_state_actual": r.decision_state_actual,
        "decision_state_expected": r.decision_state_expected,
        "checks": r.checks,
        "errors": r.errors,
    })

results_path = os.path.join(PROJECT_ROOT, "data/fixtures/eval_results.json")
with open(results_path, 'w') as f:
    json.dump(all_results, f, indent=2, default=str)
print(f"\n  Results saved to {results_path}")

# Detail failures
if all_pass < all_total:
    print("\n" + "=" * 60)
    print("  FAILURES")
    print("=" * 60)
    for r in policy_results + e2e_results:
        if not r.passed:
            print(f"\n  {r.fixture_id}:")
            for c in r.checks:
                if not c["passed"]:
                    print(f"    ✗ {c['check']}")
                    if "expected" in c:
                        print(f"      Expected: {c['expected']}")
                    if "actual" in c:
                        print(f"      Actual: {c['actual']}")

# Exit with error code if any failures
sys.exit(0 if all_pass == all_total else 1)
