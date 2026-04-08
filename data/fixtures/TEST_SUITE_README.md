# Notebook 02 Test Suite - Complete Documentation

**Version**: 1.0  
**Date**: 2026-04-09  
**Total Scenarios**: 30  
**Pass Rate**: 100%

---

## Quick Start

```bash
# Run all tests
cd data/fixtures
python3 run_all_tests.py

# Import specific scenarios in your code
from test_scenarios import TestScenarios

# Get a specific scenario
packet = TestScenarios.basic_empty()

# Get all scenarios
all_scenarios = TestScenarios.get_all()

# Get by category
contradictions = TestScenarios.get_by_category("contradiction")
```

---

## Test Suite Architecture

```
data/fixtures/
├── test_scenarios_catalog.md       # Human-readable scenario documentation
├── test_scenarios.py               # 30 CanonicalPacket factory functions
├── run_all_tests.py                # Comprehensive test runner
├── test_results.json               # Generated test results
└── TEST_SUITE_README.md           # This file
```

---

## Scenario Categories

### 🔹 Basic Flows (6 scenarios)

| ID | Scenario | Purpose | Expected Decision |
|----|----------|---------|-------------------|
| A1 | `basic_empty` | Baseline empty packet | ASK_FOLLOWUP |
| A2 | `basic_complete_discovery` | All discovery fields filled | PROCEED_TRAVELER_SAFE |
| A3 | `basic_hypothesis_only` | Hypotheses don't fill blockers | ASK_FOLLOWUP |
| A4 | `basic_derived_fills` | Derived signals CAN fill blockers | PROCEED_INTERNAL_DRAFT |
| A5 | `basic_soft_only` | Soft blockers only | PROCEED_INTERNAL_DRAFT |
| A6 | `basic_minimal_safe` | Edge of confidence threshold | PROCEED_TRAVELER_SAFE |

### ⚡ Contradictions (5 scenarios)

| ID | Scenario | Conflict Type | Expected Decision |
|----|----------|---------------|-------------------|
| B1 | `contradiction_date_critical` | Date mismatch | STOP_NEEDS_REVIEW |
| B2 | `contradiction_budget_branch` | Budget ambiguity | BRANCH_OPTIONS |
| B3 | `contradiction_destination_ask` | Destination conflict | ASK_FOLLOWUP |
| B4 | `contradiction_count_ask` | Traveler count mismatch | ASK_FOLLOWUP |
| B5 | `contradiction_origin_ask` | Origin conflict | ASK_FOLLOWUP |

### 🔐 Authority Tests (5 scenarios)

| ID | Scenario | Authority Test | Expected Decision |
|----|----------|----------------|-------------------|
| C1 | `authority_manual_override` | Highest authority | PROCEED_TRAVELER_SAFE |
| C2 | `authority_owner_vs_imported` | imported > owner | ASK_FOLLOWUP |
| C3 | `authority_derived_vs_hypothesis` | derived fills, hypothesis doesn't | ASK_FOLLOWUP |
| C4 | `authority_explicit_user_high` | Near-highest authority | PROCEED_TRAVELER_SAFE |
| C5 | `authority_unknown_rejected` | Unknown doesn't fill | ASK_FOLLOWUP |

### 📈 Stage Progression (4 scenarios)

| ID | Scenario | Stage | Missing Fields | Expected Decision |
|----|----------|-------|----------------|-------------------|
| D1 | `stage_discovery_to_shortlist` | shortlist | selected_destinations | ASK_FOLLOWUP |
| D2 | `stage_shortlist_to_proposal` | proposal | selected_itinerary | ASK_FOLLOWUP |
| D3 | `stage_proposal_to_booking` | booking | traveler_details, payment | ASK_FOLLOWUP |
| D4 | `stage_booking_complete` | booking | None | PROCEED_TRAVELER_SAFE |

### 🔪 Edge Cases (5 scenarios)

| ID | Scenario | Edge Case | Expected Decision |
|----|----------|-----------|-------------------|
| E1 | `edge_null_values` | None values | ASK_FOLLOWUP |
| E2 | `edge_empty_strings` | Empty strings | ASK_FOLLOWUP |
| E3 | `edge_zero_confidence` | Zero confidence | PROCEED_INTERNAL_DRAFT |
| E4 | `edge_duplicate_layers` | Same field in all layers | PROCEED_INTERNAL_DRAFT |
| E5 | `edge_unknown_stage` | Invalid stage | ASK_FOLLOWUP |

### 🔀 Complex Hybrid (5 scenarios)

| ID | Scenario | Complexity | Expected Decision |
|----|----------|------------|-------------------|
| F1 | `hybrid_multi_source` | Multi-envelope evidence | PROCEED_INTERNAL_DRAFT |
| F2 | `hybrid_normalized` | City code normalization | PROCEED_TRAVELER_SAFE |
| F3 | `hybrid_cross_layer` | Fact vs derived conflict | PROCEED_TRAVELER_SAFE |
| F4 | `hybrid_confidence_boundary` | Exact threshold | PROCEED_INTERNAL_DRAFT |
| F5 | `hybrid_all_layers` | Facts + derived + hypotheses | ASK_FOLLOWUP |

---

## Key Test Validations

### 1. Hypothesis vs Derived Signal Distinction

```python
# Test A3: Hypothesis-only
hypotheses = {
    "destination_city": Slot(authority_level="soft_hypothesis"),
    "travel_dates": Slot(authority_level="soft_hypothesis"),
}
# Expected: ASK_FOLLOWUP (hypotheses don't fill blockers)

# Test A4: Derived fills
facts = {"origin_city": ..., "traveler_count": ..., "travel_dates": ...}
derived_signals = {"destination_city": Slot(authority_level="derived_signal")}
# Expected: PROCEED_INTERNAL_DRAFT (derived fills blocker)
```

### 2. Contradiction Routing

```python
# Date conflict → STOP_NEEDS_REVIEW (critical)
# Budget conflict → BRANCH_OPTIONS (medium)
# Other conflicts → ASK_FOLLOWUP
```

### 3. Authority Precedence

```python
manual_override (1.0) > explicit_user (0.95) > imported_structured (0.85) > 
explicit_owner (0.80) > derived_signal (0.60) > soft_hypothesis (0.0) > unknown (0.0)
```

### 4. Stage-Based MVB

| Stage | Hard Blockers Added |
|-------|---------------------|
| discovery | 4 (destination, origin, dates, count) |
| shortlist | +1 (selected_destinations) |
| proposal | +1 (selected_itinerary) |
| booking | +2 (traveler_details, payment_method) |

---

## Usage Examples

### Running Specific Categories

```python
from test_scenarios import TestScenarios

# Test only contradiction scenarios
contradictions = TestScenarios.get_by_category("contradiction")
for name, packet in contradictions.items():
    result = run_gap_and_decision(packet)
    print(f"{name}: {result.decision_state}")
```

### Validating Expected Results

```python
expected = TestScenarios.get_expected_results()

for name, packet in TestScenarios.get_all().items():
    result = run_gap_and_decision(packet)
    exp = expected[name]
    
    assert result.decision_state == exp["decision_state"], \
        f"{name}: expected {exp['decision_state']}, got {result.decision_state}"
    
    if "hard_blockers" in exp:
        assert len(result.hard_blockers) == exp["hard_blockers"], \
            f"{name}: expected {exp['hard_blockers']} blockers, got {len(result.hard_blockers)}"
```

### Creating Custom Fixtures

```python
custom_packet = CanonicalPacket(
    packet_id="my_test",
    created_at=datetime.now().isoformat(),
    last_updated=datetime.now().isoformat(),
    stage="discovery",
    facts={
        "destination_city": Slot(
            value="Japan",
            confidence=0.95,
            authority_level="explicit_user"
        ),
    },
    # ... other fields
)
```

---

## Test Results Format

Generated `test_results.json`:

```json
{
  "summary": {
    "total": 30,
    "passed": 30,
    "failed": 0,
    "errors": 0,
    "success_rate": 100.0
  },
  "category_stats": {
    "basic": {"total": 6, "passed": 6},
    "contradiction": {"total": 5, "passed": 5},
    "authority": {"total": 5, "passed": 5},
    "stage": {"total": 4, "passed": 4},
    "edge": {"total": 5, "passed": 5},
    "hybrid": {"total": 5, "passed": 5}
  },
  "results": {
    "passed": [...],
    "failed": [],
    "errors": []
  }
}
```

---

## Integration with Notebook 02

To use these fixtures with the actual Notebook 02 pipeline:

```python
# In Notebook 02 test cell
from data.fixtures.test_scenarios import TestScenarios

# Run all scenarios through pipeline
results = []
for name, packet in TestScenarios.get_all().items():
    result = run_gap_and_decision(packet)
    results.append({
        "scenario": name,
        "decision": result.decision_state,
        "hard_blockers": result.hard_blockers,
        "soft_blockers": result.soft_blockers,
    })

# Display results
import pandas as pd
df = pd.DataFrame(results)
df.to_csv("notebook_02_test_results.csv", index=False)
```

---

## Maintenance Notes

### Adding New Scenarios

1. Add factory method to `TestScenarios` class
2. Add entry to `get_all()` method
3. Add expected results to `get_expected_results()`
4. Update this documentation
5. Run `python3 run_all_tests.py` to validate

### Scenario Naming Convention

```
{category}_{descriptive_name}

Categories:
- basic_ : Basic flows
- contradiction_ : Contradiction handling
- authority_ : Authority/priority tests
- stage_ : Stage progression
- edge_ : Edge cases
- hybrid_ : Complex hybrid scenarios
```

---

## Validation Checklist

- [x] 30 scenarios defined
- [x] All 6 categories covered
- [x] Expected results documented
- [x] Test runner validates all scenarios
- [x] 100% pass rate
- [x] Integration examples provided
- [x] Documentation complete

---

**Status**: ✅ Ready for production use
