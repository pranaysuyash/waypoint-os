#!/usr/bin/env python3
"""
Hybrid Decision Engine Validation Harness.

Runs test scenarios through the hybrid engine and measures:
- Cache hit rate
- Rule hit rate
- LLM call count
- Cost per decision
- Edge case discovery

Usage:
    python tools/validation/hybrid_engine_validator.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def load_scenarios() -> List[Dict[str, Any]]:
    """Load test scenarios from fixtures."""
    fixtures_dir = Path(__file__).parent.parent.parent / "data" / "fixtures" / "scenarios"
    scenarios = []

    for fixture_file in fixtures_dir.glob("SC-*.json"):
        try:
            with open(fixture_file) as f:
                scenario = json.load(f)
                scenarios.append(scenario)
        except Exception as e:
            print(f"Warning: Failed to load {fixture_file}: {e}")

    return scenarios


def create_test_packet(scenario: Dict[str, Any]):
    """Create a CanonicalPacket from a scenario."""
    from intake.packet_models import CanonicalPacket, Slot

    # Extract message content
    message = ""
    if "messages" in scenario:
        for msg in scenario.get("messages", []):
            if msg.get("role") == "user":
                message = msg.get("content", "")

    # Create a basic packet
    packet = CanonicalPacket(
        packet_id=scenario.get("fixture_id", "unknown"),
        schema_version="0.2",
        stage=scenario.get("stage", "discovery"),
        operating_mode="normal_intake",
        facts={
            "raw_message": Slot(value=message, authority_level="explicit_user"),
        },
        derived_signals={},
    )

    return packet, message


class ValidationResults:
    """Track validation metrics."""

    def __init__(self):
        self.start_time = datetime.now()
        self.total_scenarios = 0
        self.total_decisions = 0
        self.cache_hits = 0
        self.rule_hits = 0
        self.llm_calls = 0
        self.default_fallbacks = 0
        self.errors = []
        self.edge_cases = []
        self.decision_results = []

    def record_decision(self, result: Any, decision_type: str):
        """Record a decision result."""
        self.total_decisions += 1

        if hasattr(result, "source"):
            source = result.source
            if source == "cache":
                self.cache_hits += 1
            elif source == "rule":
                self.rule_hits += 1
            elif source == "llm":
                self.llm_calls += 1
            elif source == "default":
                self.default_fallbacks += 1

            self.decision_results.append({
                "decision_type": decision_type,
                "source": source,
                "confidence": getattr(result, "confidence", 0.0),
                "cost_inr": getattr(result, "cost_inr", 0.0),
            })

    def add_error(self, scenario_id: str, error: str, decision_type: str = ""):
        """Record an error."""
        self.errors.append({
            "scenario_id": scenario_id,
            "decision_type": decision_type,
            "error": error,
        })

    def add_edge_case(self, scenario_id: str, description: str):
        """Record an edge case discovery."""
        self.edge_cases.append({
            "scenario_id": scenario_id,
            "description": description,
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        duration = (datetime.now() - self.start_time).total_seconds()

        cache_hit_rate = self.cache_hits / self.total_decisions if self.total_decisions > 0 else 0
        rule_hit_rate = self.rule_hits / self.total_decisions if self.total_decisions > 0 else 0
        llm_call_rate = self.llm_calls / self.total_decisions if self.total_decisions > 0 else 0

        # Estimate costs
        total_cost = sum(r.get("cost_inr", 0) for r in self.decision_results)

        # Free decisions (cache + rules)
        free_decisions = self.cache_hits + self.rule_hits
        free_rate = free_decisions / self.total_decisions if self.total_decisions > 0 else 0

        return {
            "validation_date": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_scenarios": self.total_scenarios,
            "total_decisions": self.total_decisions,
            "cache_hits": self.cache_hits,
            "rule_hits": self.rule_hits,
            "llm_calls": self.llm_calls,
            "default_fallbacks": self.default_fallbacks,
            "errors": len(self.errors),
            "edge_cases_found": len(self.edge_cases),
            "cache_hit_rate": round(cache_hit_rate, 3),
            "rule_hit_rate": round(rule_hit_rate, 3),
            "llm_call_rate": round(llm_call_rate, 3),
            "free_decision_rate": round(free_rate, 3),
            "total_cost_inr": round(total_cost, 2),
            "avg_cost_per_decision": round(total_cost / self.total_decisions, 2) if self.total_decisions > 0 else 0,
        }


def run_validation():
    """Run the validation harness."""
    print("=" * 60)
    print("HYBRID DECISION ENGINE VALIDATION")
    print("=" * 60)
    print()

    # Load scenarios
    print("Loading test scenarios...")
    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} scenarios")
    print()

    if not scenarios:
        print("No scenarios found. Creating synthetic test scenarios...")
        scenarios = create_synthetic_scenarios()
        print(f"Created {len(scenarios)} synthetic scenarios")
        print()

    # Initialize results
    results = ValidationResults()

    # Try to load hybrid engine
    print("Initializing hybrid engine...")
    try:
        from decision import create_hybrid_engine
        engine = create_hybrid_engine(
            enable_cache=True,
            enable_rules=True,
            enable_llm=False,  # Disable LLM for validation (no API key)
        )
        print("Hybrid engine initialized (LLM disabled)")
        print()
    except Exception as e:
        print(f"Failed to initialize hybrid engine: {e}")
        print("Exiting...")
        return

    # Decision types to test
    decision_types = [
        "elderly_mobility_risk",
        "toddler_pacing_risk",
        "composition_risk",
        "visa_timeline_risk",
        "budget_feasibility",
    ]

    # Process each scenario
    print("Processing scenarios...")
    print("-" * 60)

    for scenario in scenarios:
        scenario_id = scenario.get("fixture_id", "unknown")
        results.total_scenarios += 1

        print(f"\n[{scenario_id}]")

        try:
            packet, message = create_test_packet(scenario)

            # Run each decision type
            for decision_type in decision_types:
                try:
                    result = engine.decide(decision_type, packet)
                    results.record_decision(result, decision_type)

                    # Print brief result
                    source = result.source if hasattr(result, "source") else "unknown"
                    confidence = getattr(result, "confidence", 0)
                    print(f"  {decision_type}: {source} (confidence: {confidence:.2f})")

                    # Check for edge cases
                    if source == "default":
                        results.add_edge_case(
                            scenario_id,
                            f"{decision_type} fell through to default"
                        )

                except Exception as e:
                    error_msg = str(e)
                    results.add_error(scenario_id, error_msg, decision_type)
                    print(f"  {decision_type}: ERROR - {error_msg[:50]}")

        except Exception as e:
            results.add_error(scenario_id, f"Packet creation failed: {e}")
            print(f"  ERROR: {e}")

    # Print summary
    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    summary = results.get_summary()

    print(f"\nDuration: {summary['duration_seconds']:.2f} seconds")
    print(f"Scenarios processed: {summary['total_scenarios']}")
    print(f"Total decisions made: {summary['total_decisions']}")
    print()
    print("Decision Sources:")
    print(f"  Cache hits:   {summary['cache_hits']} ({summary['cache_hit_rate']:.1%})")
    print(f"  Rule hits:    {summary['rule_hits']} ({summary['rule_hit_rate']:.1%})")
    print(f"  LLM calls:    {summary['llm_calls']} ({summary['llm_call_rate']:.1%})")
    print(f"  Defaults:     {summary['default_fallbacks']}")
    print()
    print("Cost Analysis:")
    print(f"  Free decisions: {summary['free_decision_rate']:.1%}")
    print(f"  Total cost: ₹{summary['total_cost_inr']}")
    print(f"  Avg cost per decision: ₹{summary['avg_cost_per_decision']}")
    print()

    if summary['errors'] > 0:
        print(f"Errors encountered: {summary['errors']}")
        for error in results.errors[:5]:
            print(f"  - {error['scenario_id']}: {error['error'][:60]}")
        print()

    if summary['edge_cases_found'] > 0:
        print(f"Edge cases found: {summary['edge_cases_found']}")
        for edge_case in results.edge_cases[:5]:
            print(f"  - {edge_case['scenario_id']}: {edge_case['description']}")
        print()

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    results_file = results_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(results_file, "w") as f:
        json.dump({
            "summary": summary,
            "errors": results.errors,
            "edge_cases": results.edge_cases,
            "decisions": results.decision_results,
        }, f, indent=2)

    print(f"Results saved to: {results_file.relative_to(Path.cwd())}")

    return summary


def create_synthetic_scenarios() -> List[Dict[str, Any]]:
    """Create synthetic test scenarios for validation."""
    scenarios = []

    # Scenario 1: Elderly travelers to Maldives
    scenarios.append({
        "fixture_id": "VAL-001",
        "stage": "discovery",
        "messages": [
            {
                "role": "user",
                "content": "We are 2 elderly travelers planning a trip to Maldives for 5 nights in June."
            }
        ],
    })

    # Scenario 2: Family with toddlers
    scenarios.append({
        "fixture_id": "VAL-002",
        "stage": "discovery",
        "messages": [
            {
                "role": "user",
                "content": "Family of 4 with 2 kids (ages 2 and 6) wanting to visit Goa for a week."
            }
        ],
    })

    # Scenario 3: Budget-conscious group
    scenarios.append({
        "fixture_id": "VAL-003",
        "stage": "discovery",
        "messages": [
            {
                "role": "user",
                "content": "Group of 6 friends planning a trip to Singapore with budget of 2 lakh total."
            }
        ],
    })

    # Scenario 4: Multi-generational family
    scenarios.append({
        "fixture_id": "VAL-004",
        "stage": "discovery",
        "messages": [
            {
                "role": "user",
                "content": "Family vacation - grandparents, parents, and 3 kids (ages 3, 8, 12) to Kerala."
            }
        ],
    })

    # Scenario 5: Urgent international travel
    scenarios.append({
        "fixture_id": "VAL-005",
        "stage": "booking",
        "messages": [
            {
                "role": "user",
                "content": "Need to travel to Paris in 5 days. Have passport, no visa yet."
            }
        ],
    })

    return scenarios


if __name__ == "__main__":
    run_validation()
