# How to Add a New Decision Rule

**Target**: Increase rule hit rate from 34% to 60%+ by adding more decision rules.

## Overview

The Hybrid Decision Engine uses a cascading decision flow:
```
Cache → Rules → LLM → Default
```

Each rule added increases the free decision rate (₹0 cost) and reduces latency.

## When to Add a Rule

Add a rule when a decision pattern is:
1. **Deterministic** - Can be expressed as clear if-then logic
2. **Common** - Occurs frequently in real scenarios
3. **Stable** - Won't change often (business logic, not preferences)
4. **Testable** - Has clear inputs and expected outputs

## Rule vs LLM Decision Guide

| Use a Rule When | Use LLM When |
|-----------------|--------------|
| Lookup tables (visa requirements, costs) | Ambiguity resolution |
| Threshold checks (age, duration, budget) | Preference inference |
| Data validation (dates, documents) | Contextual trade-offs |
| Domain rules (seasonal closures) | Complex composition balancing |

## Step-by-Step: Adding a New Rule

### Step 1: Identify the Decision Type

First, check if this is a new decision type or extending an existing one:

**Existing decision types:**
- `elderly_mobility_risk` - Mobility challenges for elderly travelers
- `toddler_pacing_risk` - Trip intensity for families with toddlers
- `budget_feasibility` - Budget sufficiency for destination/party size
- `visa_timeline_risk` - Visa processing time vs trip urgency
- `composition_risk` - Party composition complexity

**If extending existing type:** Skip to Step 3.

### Step 2: Define New Decision Type

Add to `src/decision/hybrid_engine.py`:

```python
class HybridDecisionEngine:
    SCHEMAS = {
        # ... existing types ...
        "your_decision_type": {
            "type": "object",
            "properties": {
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"]
                },
                "reasoning": {"type": "string"},
                # Add decision-specific fields
            },
            "required": ["risk_level"],
        },
    }
    
    DEFAULT_DECISIONS = {
        # ... existing defaults ...
        "your_decision_type": {
            "risk_level": "medium",
            "reasoning": "Default decision - insufficient data",
        },
    }
```

### Step 3: Create the Rule File

Create `src/decision/rules/your_decision_type.py`:

```python
"""
decision.rules.your_decision_type — Your decision description.

Assesses [what this rule does].
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from intake.packet_models import CanonicalPacket


def _extract_relevant_data(packet: CanonicalPacket) -> Optional[Any]:
    """Extract data needed for this decision."""
    # Extract from facts
    fact_value = packet.facts.get("your_fact")
    if fact_value and fact_value.value:
        return fact_value.value
    
    # Extract from derived signals
    signal_value = packet.derived_signals.get("your_signal")
    if signal_value and signal_value.value:
        return signal_value.value
    
    return None


def rule_your_decision_type(packet: CanonicalPacket) -> Optional[Dict[str, Any]]:
    """
    Assess [what this rule assesses].
    
    Returns None if:
    - Required data not available
    - Situation too complex for rules (delegate to LLM)
    
    Returns decision dict with risk assessment.
    
    Args:
        packet: CanonicalPacket with travel information
    
    Returns:
        Decision dict or None
    """
    # 1. Check if we have required data
    data = _extract_relevant_data(packet)
    if data is None:
        return None
    
    # 2. Apply deterministic logic
    if _condition_for_low_risk(data):
        return {
            "risk_level": "low",
            "reasoning": "Explanation for low risk",
            # Add decision-specific fields
        }
    
    if _condition_for_medium_risk(data):
        return {
            "risk_level": "medium",
            "reasoning": "Explanation for medium risk",
        }
    
    if _condition_for_high_risk(data):
        return {
            "risk_level": "high",
            "reasoning": "Explanation for high risk",
            "recommendations": ["Action 1", "Action 2"],
        }
    
    # 3. If we can't decide, return None (LLM will handle)
    return None


def _condition_for_low_risk(data: Any) -> bool:
    """Check if risk level is low."""
    # Your logic here
    return False


def _condition_for_medium_risk(data: Any) -> bool:
    """Check if risk level is medium."""
    # Your logic here
    return False


def _condition_for_high_risk(data: Any) -> bool:
    """Check if risk level is high."""
    # Your logic here
    return False
```

### Step 4: Register the Rule

Add to `src/decision/rules/__init__.py`:

```python
from .elderly_mobility import rule_elderly_mobility_risk
from .toddler_pacing import rule_toddler_pacing_risk
from .budget_feasibility import rule_budget_feasibility
from .visa_timeline import rule_visa_timeline_risk
from .composition_risk import rule_composition_risk
from .your_decision_type import rule_your_decision_type

# Rule registry maps decision types to their rule functions
RULE_REGISTRY = {
    "elderly_mobility_risk": [rule_elderly_mobility_risk],
    "toddler_pacing_risk": [rule_toddler_pacing_risk],
    "budget_feasibility": [rule_budget_feasibility],
    "visa_timeline_risk": [rule_visa_timeline_risk],
    "composition_risk": [rule_composition_risk],
    "your_decision_type": [rule_your_decision_type],
}
```

### Step 5: Update Cache Key Generation

Add to `src/decision/cache_key.py` if your decision needs specific fields:

```python
def _get_relevant_fields(decision_type: str, packet: CanonicalPacket) -> Dict[str, Any]:
    # ... existing code ...
    
    elif decision_type == "your_decision_type":
        return {
            "field1": _extract_value(packet, "field1"),
            "field2": _extract_value(packet, "field2"),
            "signal1": _extract_value(packet.derived_signals, "signal1"),
        }
```

### Step 6: Write Tests

Add to `tests/test_hybrid_engine.py` or create a new test file:

```python
class TestYourDecisionRule:
    """Tests for your_decision_type rule."""
    
    def test_low_risk_scenario(self):
        """Test rule returns low risk for safe inputs."""
        from src.decision.rules.your_decision_type import rule_your_decision_type
        from src.intake.packet_models import CanonicalPacket, Slot
        
        packet = CanonicalPacket(
            packet_id="test-low-risk",
            facts={
                "your_fact": Slot(value="safe_value", authority_level="explicit_user"),
            },
            derived_signals={}
        )
        
        result = rule_your_decision_type(packet)
        assert result is not None
        assert result["risk_level"] == "low"
    
    def test_high_risk_scenario(self):
        """Test rule returns high risk for risky inputs."""
        # Similar to above but with risky inputs
        
    def test_returns_none_for_complex_cases(self):
        """Test rule delegates to LLM for complex cases."""
        # Test that rule returns None when it can't decide
```

### Step 7: Add Validation Test Cases

Add to `tools/validation/structured_validator.py`:

```python
def create_test_packets() -> List[Dict[str, Any]]:
    test_cases = []
    
    # Your new test case
    test_cases.append({
        "name": "Your Test Case Name",
        "packet": CanonicalPacket(
            packet_id="TEST-XXX",
            stage="discovery",
            operating_mode="normal_intake",
            facts={
                "field1": Slot(value=<value>, authority_level="explicit_user"),
            },
            derived_signals={
                "signal1": Slot(value=<value>, authority_level="derived_signal"),
            },
        ),
        "expected": {
            "your_decision_type": "expected_value",
        },
    })
    
    return test_cases
```

### Step 8: Run Validation

```bash
# Run your specific test
uv run python -m pytest tests/test_hybrid_engine.py::TestYourDecisionRule -v

# Run full validation
python tools/validation/structured_validator.py

# Run all tests
uv run python -m pytest tests/ -v
```

## Rule Writing Best Practices

### 1. Return None for Edge Cases

If the situation is complex or ambiguous, return `None` to let the LLM handle it:

```python
# Don't try to handle every case
if _has_unusual_combination(data):
    return None  # Let LLM figure it out
```

### 2. Use Lookup Tables for Reference Data

```python
# Good: Maintainable lookup table
VISA_LEAD_TIMES = {
    "USA": 60,
    "Singapore": 7,
    "Goa": 0,  # Domestic
}

lead_time = VISA_LEAD_TIMES.get(destination, 30)
```

### 3. Provide Reasoning

Always explain why the decision was made:

```python
return {
    "risk_level": "high",
    "reasoning": f"Destination {dest} requires {days}-day visa processing, "
                 f"but trip is in {trip_days} days",
}
```

### 4. Include Actionable Recommendations

For medium/high risk decisions:

```python
return {
    "risk_level": "high",
    "recommendations": [
        "Start visa application immediately",
        "Consider expedited processing",
        "Have backup destination ready",
    ],
}
```

## Examples

See existing rules for reference:
- `src/decision/rules/elderly_mobility.py` - Destination-based lookup
- `src/decision/rules/toddler_pacing.py` - Duration threshold checks
- `src/decision/rules/budget_feasibility.py` - Per-person cost calculations
- `src/decision/rules/visa_timeline.py` - Urgency-aware logic
- `src/decision/rules/composition_risk.py` - Multi-concern aggregation

## Measuring Impact

After adding a rule, run validation to measure impact:

```bash
python tools/validation/structured_validator.py
```

Look for:
- **Rule hit rate increase** - More decisions handled by rules
- **Accuracy maintained** - Still 100% on expected values
- **Cache fill rate** - New patterns being cached

Target: **60%+ rule hit rate** for production.

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Rule too complex | Break into smaller rules or use LLM |
| Magic numbers | Use named constants or lookup tables |
| No fallback for edge cases | Return None for complex/ambiguous inputs |
| Missing reasoning | Always explain the decision |
| Not testing | Add test cases for all risk levels |

## Next Steps

After adding your rule:
1. ✅ Run validation and verify accuracy
2. ✅ Update this guide with your learnings
3. ✅ Monitor production hit rates
4. ✅ Iterate based on real-world patterns

---

For questions, refer to:
- [Validation Report](validation/hybrid_engine_validation_report.md)
- [Hybrid Decision Architecture](HYBRID_DECISION_ARCHITECTURE_2026-04-16.md)
- [Tools Guide](../../tools/validation/README.md)
