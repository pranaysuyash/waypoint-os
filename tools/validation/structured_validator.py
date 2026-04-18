#!/usr/bin/env python3
"""
Structured Validation for Hybrid Decision Engine.

Tests the engine with properly structured CanonicalPackets containing
facts and derived_signals (as would come from NB01 normalizer).

This gives a more accurate picture of real-world performance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from intake.packet_models import CanonicalPacket, Slot
from decision import create_hybrid_engine


def create_test_packets() -> List[Dict[str, Any]]:
    """Create structured test packets with facts."""
    test_cases = []

    # Test 1: Elderly travelers to Maldives (high risk)
    test_cases.append({
        "name": "Elderly + Maldives",
        "packet": CanonicalPacket(
            packet_id="TEST-001",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"elderly": 2, "adults": 0}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Maldives"], authority_level="explicit_user"),
                "resolved_destination": Slot(value="Maldives", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"elderly_mobility_risk": "high"},
    })

    # Test 2: Elderly travelers to Singapore (low risk)
    test_cases.append({
        "name": "Elderly + Singapore",
        "packet": CanonicalPacket(
            packet_id="TEST-002",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"elderly": 1, "adults": 1}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Singapore"], authority_level="explicit_user"),
                "resolved_destination": Slot(value="Singapore", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"elderly_mobility_risk": "low"},
    })

    # Test 3: Toddler + short trip (medium risk)
    test_cases.append({
        "name": "Toddler + Short Trip",
        "packet": CanonicalPacket(
            packet_id="TEST-003",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"toddlers": 1, "adults": 2}, authority_level="explicit_user"),
                "child_ages": Slot(value=[2], authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
                "duration_days": Slot(value=5, authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"toddler_pacing_risk": "medium"},
    })

    # Test 4: Toddler + long trip (high risk)
    test_cases.append({
        "name": "Toddler + Long Trip",
        "packet": CanonicalPacket(
            packet_id="TEST-004",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"toddlers": 1, "adults": 2}, authority_level="explicit_user"),
                "child_ages": Slot(value=[3], authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa", "Kerala"], authority_level="explicit_user"),
                "duration_days": Slot(value=10, authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"toddler_pacing_risk": "high"},
    })

    # Test 5: Budget feasible
    test_cases.append({
        "name": "Budget Feasible (Goa)",
        "packet": CanonicalPacket(
            packet_id="TEST-005",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "budget_min": Slot(value=50000, authority_level="explicit_user"),
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Goa", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"budget_feasibility": "feasible"},
    })

    # Test 6: Budget infeasible
    test_cases.append({
        "name": "Budget Infeasible (Singapore)",
        "packet": CanonicalPacket(
            packet_id="TEST-006",
            stage="booking",
            operating_mode="normal_intake",
            facts={
                "budget_min": Slot(value=50000, authority_level="explicit_user"),
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Singapore", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"budget_feasibility": "infeasible"},
    })

    # Test 7: Visa timeline risk (high urgency)
    test_cases.append({
        "name": "Visa Timeline Risk (High Urgency)",
        "packet": CanonicalPacket(
            packet_id="TEST-007",
            stage="booking",
            operating_mode="normal_intake",
            facts={
                "resolved_destination": Slot(value="USA", authority_level="explicit_user"),
                "visa_status": Slot(
                    value={"requirement": "required", "status": "not_applied"},
                    authority_level="explicit_user"
                ),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
                "urgency": Slot(value="high", authority_level="derived_signal"),
            },
        ),
        "expected": {"visa_timeline_risk": "high"},
    })

    # Test 8: Multi-generational composition (medium risk - 2 concerns: multi-gen + multiple elderly)
    test_cases.append({
        "name": "Multi-Generational Family",
        "packet": CanonicalPacket(
            packet_id="TEST-008",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(
                    value={"elderly": 2, "adults": 2, "children": 2, "toddlers": 1},
                    authority_level="explicit_user"
                ),
                "destination_candidates": Slot(value=["Kerala"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "medium"},  # Fixed: 2 concerns = medium, not high
    })

    # Test 9: Simple adult group (low risk)
    test_cases.append({
        "name": "Adult-Only Group",
        "packet": CanonicalPacket(
            packet_id="TEST-009",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"adults": 4}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "low"},
    })

    # Test 10: Domestic - no visa needed
    test_cases.append({
        "name": "Domestic - No Visa",
        "packet": CanonicalPacket(
            packet_id="TEST-010",
            stage="booking",
            operating_mode="normal_intake",
            facts={
                "resolved_destination": Slot(value="Goa", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"visa_timeline_risk": "low"},
    })

    # Test 11: Large group (>8) - medium composition risk (1 concern only)
    test_cases.append({
        "name": "Large Group (Medium Risk)",
        "packet": CanonicalPacket(
            packet_id="TEST-011",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(
                    value={"adults": 10},
                    authority_level="explicit_user"
                ),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "medium"},  # 1 concern (large party) = medium, need 3+ for high
    })

    # Test 12: Single adult with many dependents - medium composition risk (1 concern only)
    test_cases.append({
        "name": "Single Adult + Many Dependents",
        "packet": CanonicalPacket(
            packet_id="TEST-012",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(
                    value={"adults": 1, "children": 3, "toddlers": 1},
                    authority_level="explicit_user"
                ),
                "destination_candidates": Slot(value=["Kerala"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "medium"},  # 1 concern (single adult) = medium, need 3+ for high
    })

    # Test 13: Very high complexity - multiple concerns
    test_cases.append({
        "name": "Very High Complexity (3+ concerns)",
        "packet": CanonicalPacket(
            packet_id="TEST-013",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(
                    value={"elderly": 2, "adults": 1, "children": 2, "toddlers": 2},
                    authority_level="explicit_user"
                ),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "high"},  # Multi-gen + large party (7) + multiple toddlers + single adult with dependents = 4 concerns
    })

    # Test 14: Elderly to Bhutan (high risk destination)
    test_cases.append({
        "name": "Elderly + Bhutan (High Risk)",
        "packet": CanonicalPacket(
            packet_id="TEST-014",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"elderly": 2, "adults": 0}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Bhutan"], authority_level="explicit_user"),
                "resolved_destination": Slot(value="Bhutan", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"elderly_mobility_risk": "high"},
    })

    # Test 15: Visa timeline - low urgency
    test_cases.append({
        "name": "Visa Timeline Risk (Low Urgency)",
        "packet": CanonicalPacket(
            packet_id="TEST-015",
            stage="booking",
            operating_mode="normal_intake",
            facts={
                "resolved_destination": Slot(value="USA", authority_level="explicit_user"),
                "visa_status": Slot(
                    value={"requirement": "required", "status": "not_applied"},
                    authority_level="explicit_user"
                ),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
                "urgency": Slot(value="low", authority_level="derived_signal"),
            },
        ),
        "expected": {"visa_timeline_risk": "low"},
    })

    # Test 16: International trip with toddlers - medium to high risk
    test_cases.append({
        "name": "Toddler + International Trip",
        "packet": CanonicalPacket(
            packet_id="TEST-016",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"toddlers": 1, "adults": 2}, authority_level="explicit_user"),
                "child_ages": Slot(value=[2], authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Singapore", "Malaysia"], authority_level="explicit_user"),
                "duration_days": Slot(value=7, authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"toddler_pacing_risk": "high"},  # International + toddler
    })

    # Test 17: Budget check for international destination
    test_cases.append({
        "name": "Budget Feasible (International)",
        "packet": CanonicalPacket(
            packet_id="TEST-017",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "budget_min": Slot(value=200000, authority_level="explicit_user"),
                "party_size": Slot(value=2, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Singapore", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"budget_feasibility": "feasible"},
    })

    # Test 18: Budget infeasible for international
    test_cases.append({
        "name": "Budget Infeasible (International)",
        "packet": CanonicalPacket(
            packet_id="TEST-018",
            stage="booking",
            operating_mode="normal_intake",
            facts={
                "budget_min": Slot(value=50000, authority_level="explicit_user"),
                "party_size": Slot(value=4, authority_level="explicit_user"),
                "resolved_destination": Slot(value="Europe", authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="international", authority_level="derived_signal"),
            },
        ),
        "expected": {"budget_feasibility": "infeasible"},
    })

    # Test 19: Simple couple - low risk across all
    test_cases.append({
        "name": "Simple Couple (Low Risk)",
        "packet": CanonicalPacket(
            packet_id="TEST-019",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"adults": 2}, authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {"composition_risk": "low"},
    })

    # Test 20: Young family with enough budget - all green
    test_cases.append({
        "name": "Young Family - All Green",
        "packet": CanonicalPacket(
            packet_id="TEST-020",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "party_composition": Slot(value={"adults": 2, "children": 2}, authority_level="explicit_user"),
                "child_ages": Slot(value=[8, 12], authority_level="explicit_user"),
                "destination_candidates": Slot(value=["Goa"], authority_level="explicit_user"),
                "duration_days": Slot(value=5, authority_level="explicit_user"),
                "budget_min": Slot(value=100000, authority_level="explicit_user"),
                "party_size": Slot(value=4, authority_level="explicit_user"),
            },
            derived_signals={
                "domestic_or_international": Slot(value="domestic", authority_level="derived_signal"),
            },
        ),
        "expected": {
            "composition_risk": "low",
            # No toddler_pacing_risk expectation - rule returns None (no toddlers)
            "budget_feasibility": "feasible",
        },
    })

    return test_cases


def run_structured_validation():
    """Run structured validation with proper packets."""
    print("=" * 70)
    print("HYBRID ENGINE STRUCTURED VALIDATION")
    print("=" * 70)
    print()

    # Initialize engine
    print("Initializing hybrid engine...")
    engine = create_hybrid_engine(
        enable_cache=True,
        enable_rules=True,
        enable_llm=False,  # Disable LLM for testing
    )
    print("Engine ready (Rules + Cache enabled, LLM disabled)")
    print()

    # Load test cases
    test_cases = create_test_packets()
    print(f"Loaded {len(test_cases)} test cases")
    print()

    # Clear cache to ensure fresh results
    print("Clearing cache for fresh validation...")
    engine.cache_storage.clear_all()
    print("Cache cleared")
    print()

    # Decision types to test
    decision_types = [
        "elderly_mobility_risk",
        "toddler_pacing_risk",
        "budget_feasibility",
        "visa_timeline_risk",
        "composition_risk",
    ]

    # Track results
    results = []
    stats = {
        "total": 0,
        "rule_hits": 0,
        "cache_hits": 0,
        "llm_calls": 0,
        "defaults": 0,
        "correct": 0,
        "incorrect": 0,
    }

    print("Running test cases...")
    print("-" * 70)

    for test_case in test_cases:
        name = test_case["name"]
        packet = test_case["packet"]
        expected = test_case.get("expected", {})

        print(f"\n[{name}]")

        case_results = {
            "name": name,
            "decisions": [],
        }

        for decision_type in decision_types:
            try:
                result = engine.decide(decision_type, packet)
                stats["total"] += 1

                # Track source
                if result.source == "rule":
                    stats["rule_hits"] += 1
                elif result.source == "cache":
                    stats["cache_hits"] += 1
                elif result.source == "llm":
                    stats["llm_calls"] += 1
                elif result.source == "default":
                    stats["defaults"] += 1

                # Get actual risk level
                decision = result.decision
                if isinstance(decision, dict):
                    risk_level = decision.get("risk_level", "unknown")
                    feasible = decision.get("feasible", None)
                else:
                    risk_level = "unknown"
                    feasible = None

                # Determine expected value
                if decision_type in expected:
                    expected_value = expected[decision_type]
                    if expected_value in ("low", "medium", "high"):
                        if risk_level == expected_value:
                            stats["correct"] += 1
                            status = "✓"
                        else:
                            stats["incorrect"] += 1
                            status = f"✗ (expected {expected_value}, got {risk_level})"
                    elif expected_value == "feasible":
                        if feasible is True:
                            stats["correct"] += 1
                            status = "✓"
                        else:
                            stats["incorrect"] += 1
                            status = f"✗ (expected feasible, got {feasible})"
                    elif expected_value == "infeasible":
                        if feasible is False:
                            stats["correct"] += 1
                            status = "✓"
                        else:
                            stats["incorrect"] += 1
                            status = f"✗ (expected infeasible, got {feasible})"
                    else:
                        status = "-"
                else:
                    status = "-"

                case_results["decisions"].append({
                    "type": decision_type,
                    "source": result.source,
                    "risk_level": risk_level,
                    "feasible": feasible,
                    "status": status,
                })

                print(f"  {decision_type:25} {result.source:8} risk={risk_level:8} {status}")

            except Exception as e:
                print(f"  {decision_type}: ERROR - {str(e)[:40]}")

        results.append(case_results)

    # Print summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print()

    rule_rate = stats["rule_hits"] / stats["total"] if stats["total"] > 0 else 0
    cache_rate = stats["cache_hits"] / stats["total"] if stats["total"] > 0 else 0
    free_rate = (stats["rule_hits"] + stats["cache_hits"]) / stats["total"] if stats["total"] > 0 else 0
    accuracy = stats["correct"] / (stats["correct"] + stats["incorrect"]) if (stats["correct"] + stats["incorrect"]) > 0 else 0

    print(f"Total decisions: {stats['total']}")
    print()
    print(f"Rule hits:    {stats['rule_hits']:3} ({rule_rate:.1%})")
    print(f"Cache hits:   {stats['cache_hits']:3} ({cache_rate:.1%})")
    print(f"LLM calls:    {stats['llm_calls']:3}")
    print(f"Defaults:     {stats['defaults']:3}")
    print()
    print(f"Free decisions: {free_rate:.1%}")
    print()
    print(f"Accuracy: {stats['correct']}/{stats['correct'] + stats['incorrect']} = {accuracy:.1%}")
    print()

    # Calculate cost savings
    # Assume LLM cost of ₹0.50 per decision
    llm_cost_per_decision = 0.5
    llm_total_cost = stats["total"] * llm_cost_per_decision
    actual_cost = stats["llm_calls"] * llm_cost_per_decision
    savings = llm_total_cost - actual_cost

    print(f"Cost Analysis (with LLM @ ₹{llm_cost_per_decision}/decision):")
    print(f"  Without cache/rules: ₹{llm_total_cost:.2f}")
    print(f"  With hybrid engine:  ₹{actual_cost:.2f}")
    print(f"  Savings:            ₹{savings:.2f} ({savings/llm_total_cost:.1%})")
    print()

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = results_dir / f"structured_validation_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump({
            "summary": stats,
            "rates": {
                "rule_hit_rate": rule_rate,
                "cache_hit_rate": cache_rate,
                "free_decision_rate": free_rate,
                "accuracy": accuracy,
            },
            "cost_analysis": {
                "llm_cost_per_decision": llm_cost_per_decision,
                "total_without_hybrid": llm_total_cost,
                "actual_cost": actual_cost,
                "savings": savings,
                "savings_percent": savings / llm_total_cost if llm_total_cost > 0 else 0,
            },
            "test_cases": results,
        }, f, indent=2)

    print(f"Results saved to: {results_file.relative_to(Path.cwd())}")

    return stats


if __name__ == "__main__":
    run_structured_validation()
