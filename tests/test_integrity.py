import pytest
import json
from pathlib import Path
from src.services.dashboard_aggregator import DashboardAggregator

def test_aggregator_logic():
    """
    Directly test the aggregator logic.
    """
    state = DashboardAggregator.get_unified_state()
    
    canonical_total = state.get("canonical_total")
    stages = state.get("stages", {})
    orphan_count = state.get("integrity_meta", {}).get("orphan_count", 0)
    
    sum_stages = sum(stages.values())
    
    print(f"\nAggregator Audit Result:")
    print(f"  Canonical Total: {canonical_total}")
    print(f"  Sum of Stages:   {sum_stages}")
    print(f"  Orphans Count:   {orphan_count}")
    
    assert sum_stages + orphan_count == canonical_total, "Mathematical inconsistency in aggregator!"
    assert state.get("integrity_meta", {}).get("consistent") == True

if __name__ == "__main__":
    try:
        test_aggregator_logic()
        print("Aggregator Logic Test Passed!")
    except Exception as e:
        print(f"Aggregator Logic Test Failed: {e}")
        import traceback
        traceback.print_exc()
