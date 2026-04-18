# Rule Expansion TODO

**Last Updated:** 2026-04-18

## Active Tasks

### 1. LLM Integration Testing (Pending)

**Goal:** Validate end-to-end LLM integration for hybrid decision engine.

**Test Areas:**
- Gemini API connectivity and decision quality
- Local LLM (phi-3-mini) integration
- Fallback behavior when LLMs fail
- Cache-fill from LLM decisions
- Telemetry and cost tracking accuracy

**Acceptance Criteria:**
- LLM client tests pass with mock responses
- Real API calls work (with valid key)
- Fallback to safe defaults on errors
- Cached LLM decisions return on subsequent calls
- Cost tracking matches actual usage

---

## Current State (60% Rule Hit Rate Achieved)

## Current State (60% Rule Hit Rate Achieved)

As of 2026-04-18, the hybrid decision engine achieves:
- **60% rule hit rate** (60 of 100 decisions via rules)
- **100% free decisions** (rules + cache, 0 LLM calls needed)
- **0 defaults** (all decisions handled explicitly)

### Rule Coverage by Decision Type

| Decision Type | Rule Hit % | Notes |
|---------------|------------|-------|
| budget_feasibility | 75% | Strong coverage |
| composition_risk | 70% | Strong coverage |
| visa_timeline_risk | 55% | Moderate coverage |
| elderly_mobility_risk | 50% | Moderate coverage |
| toddler_pacing_risk | 50% | Moderate coverage |

## Future Exploration Opportunities

### 1. Push Rule Hit Rate to 70%+

**Target Areas for Improvement:**
- **elderly_mobility_risk** (50% → 70%): Add rules for specific destinations with known accessibility
- **toddler_pacing_risk** (50% → 70%): Add rules for common destination + duration combinations
- **visa_timeline_risk** (55% → 75%): Add more country-specific visa timeline rules

**Approaches:**
- Add destination-specific accessibility data (e.g., "Singapore has excellent wheelchair access")
- Add toddler-friendly destination patterns (e.g., "Beach resorts with kids clubs")
- Expand visa requirement database with more countries and processing times

### 2. Learn from Real Traffic

**Data Collection:**
- Log all LLM decisions to a learning dataset
- Analyze patterns in high-frequency LLM calls
- Compile new rules from repeated LLM decision patterns

**Implementation:**
```python
# Track which decision types are falling through to LLM
# Priority: Add rules for the most common LLM decision patterns
```

### 3. Dynamic Rule Compilation

**Long-term Vision:**
- Automatically extract rules from cached LLM decisions
- Validate new rules against existing test suite
- Promote validated rules to built-in rule set

### 4. Edge Case Coverage

**Current Gaps:**
- Complex multi-destination itineraries
- Special needs beyond elderly/toddler (mobility aids, dietary restrictions)
- Seasonal considerations (monsoon, peak travel periods)
- Event-based travel (festivals, conferences, weddings)

## Related Documentation

- [How to Add a Decision Rule](how_to_add_a_decision_rule.md)
- [Hybrid Engine Validation Report](../validation/hybrid_engine_validation_report.md)
- [Hybrid Engine Operational Runbook](../operations/hybrid_engine_operational_runbook.md)
