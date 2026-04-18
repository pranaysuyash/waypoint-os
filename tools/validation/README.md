# Validation Tools

Tools for validating and testing the Hybrid Decision Engine.

## Overview

The validation tools measure:
- **Rule hit rate** - Percentage of decisions handled by deterministic rules
- **Cache hit rate** - Percentage of decisions served from cache
- **Accuracy** - Correctness of decisions against expected outcomes
- **Cost savings** - Money saved by avoiding LLM calls

## Tools

### structured_validator.py

Comprehensive validation with properly structured CanonicalPackets.

**Usage:**
```bash
python tools/validation/structured_validator.py
```

**What it tests:**
- 20 test scenarios covering all 5 decision types
- Elderly mobility risk (destination-based)
- Toddler pacing risk (duration-based)
- Budget feasibility (per-person thresholds)
- Visa timeline risk (urgency-aware)
- Composition risk (multi-generational, large groups)

**Output:**
- Console summary with pass/fail indicators
- JSON results file saved to `tools/validation/results/`
- Accuracy percentage and cost analysis

### hybrid_engine_validator.py

Original validator using scenario fixtures.

**Usage:**
```bash
python tools/validation/hybrid_engine_validator.py
```

**What it tests:**
- Loads scenario fixtures from `data/fixtures/scenarios/`
- Creates synthetic scenarios if none found
- Tests all 5 decision types
- Tracks edge cases and errors

**Output:**
- Validation summary with rates
- Cost analysis
- Edge cases discovered
- JSON results file

## Adding New Test Cases

To add a new test case to `structured_validator.py`:

```python
from intake.packet_models import CanonicalPacket, Slot

test_cases.append({
    "name": "Descriptive Test Name",
    "packet": CanonicalPacket(
        packet_id="TEST-XXX",
        stage="discovery",  # or "booking", "shortlist", "proposal"
        operating_mode="normal_intake",
        facts={
            # Required fields with Slot objects
            "field_name": Slot(value=<value>, authority_level="explicit_user"),
        },
        derived_signals={
            # Optional derived signals
            "signal_name": Slot(value=<value>, authority_level="derived_signal"),
        },
    ),
    "expected": {
        "decision_type": "expected_value",
        # Add more expectations as needed
    },
})
```

## Decision Types

### elderly_mobility_risk
**Risk factors:**
- Elderly travelers going to destinations with poor mobility infrastructure
- High-risk destinations: Maldives, Andaman, Bhutan, Nepal

**Risk levels:**
- `low`: Safe destinations or no elderly travelers
- `high`: Elderly + high-risk destination

### toddler_pacing_risk
**Risk factors:**
- Toddlers (age < 4) on long trips (>7 days)
- Toddlers on multi-destination trips
- International travel with toddlers

**Risk levels:**
- `low`: No toddlers, or short domestic trips
- `medium`: Toddlers + 5-7 day trips
- `high`: Toddlers + >7 days OR multiple destinations

### budget_feasibility
**Risk factors:**
- Budget per person vs destination cost
- Domestic vs international costs

**Risk levels:**
- `feasible`: Budget meets minimum per-person requirement
- `infeasible`: Budget below threshold

**Cost thresholds (examples):**
- Singapore: ₹60,000/person
- Goa: ₹15,000/person (domestic)
- International: ₹80,000+/person

### visa_timeline_risk
**Risk factors:**
- Destination visa lead time
- Trip urgency

**Risk levels:**
- `low`: Domestic, visa on arrival, or low urgency + standard processing
- `high`: High urgency + long processing time (>14 days)

### composition_risk
**Risk factors:**
- Multi-generational groups (elderly + children)
- Large party size (>8)
- Single adult managing many dependents
- Multiple toddlers

**Risk levels:**
- `low`: Simple adult groups
- `medium`: 1-2 concerns
- `high`: 3+ concerns

## Understanding Results

### Rule Hit Rate

Percentage of decisions handled by rules (not LLM or default). Higher is better - means more decisions are deterministic and free.

- **34%** in current validation (good baseline)
- Target: **60%+** with more rule development

### Cache Hit Rate

Percentage of decisions served from cache. In production, this grows over time as the system "learns."

- **9%** in validation (artificially low - cache cleared for testing)
- Target: **40%+** in production after cache fills

### Accuracy

Percentage of expected outcomes that match actual decisions.

- **100%** in current validation
- Target: **95%+** minimum

## Debugging Failed Tests

If a test fails:

1. **Check the packet structure** - Ensure all required fields are present with correct authority levels
2. **Verify the rule logic** - Read the rule file in `src/decision/rules/`
3. **Test the rule directly:**
   ```python
   from decision.rules.<rule_name> import rule_<decision_type>
   result = rule_<decision_type>(packet)
   print(result)
   ```
4. **Check cache key collisions** - Different packets should generate different keys
5. **Verify expected value** - Ensure the expected value matches what the rule should return

## Results Storage

Validation results are stored as JSON in `tools/validation/results/`:

```
structured_validation_YYYYMMDD_HHMMSS.json
validation_YYYYMMDD_HHMMSS.json
```

Each results file contains:
- Summary statistics (counts, rates)
- Cost analysis
- Test case details
- Errors and edge cases discovered

## Continuous Validation

Add to CI/CD pipeline:

```yaml
- name: Run hybrid engine validation
  run: python tools/validation/structured_validator.py

- name: Upload validation results
  uses: actions/upload-artifact@v3
  with:
    name: validation-results
    path: tools/validation/results/
```

## Related Documentation

- [Hybrid Decision Engine](../../docs/decision_engine.md)
- [Validation Report](../../docs/validation/hybrid_engine_validation_report.md)
- [Test Suite](../../tests/README.md)
