# Architecture Decision Record: Scenario Handling System

**ADR Number:** 001  
**Date:** 2026-04-15  
**Status:** Proposed  
**Author:** Architecture Team  

---

## Context

The current NB02 decision engine (`src/intake/decision.py`) has limited scenario handling capabilities. Based on code review (reference: [investigation findings](../../)), the system detects:

- ✅ Budget feasibility
- ✅ Elderly mobility risk  
- ✅ Toddler pacing/transfer risk (basic)
- ✅ Visa/document risks
- ❌ Weather/seasonal risks
- ❌ Multi-leg transfer fatigue
- ❌ Route complexity scoring
- ❌ Activity suitability matching

The frontend (`DecisionTab.tsx`, `SafetyTab.tsx`) displays risks as simple strings, limiting the ability to provide rich context and actionable guidance.

### Relevant Code References

- [`src/intake/decision.py:459-595`](../../src/intake/decision.py#L459-L595) - Current `generate_risk_flags()` implementation
- [`src/intake/decision.py:317-347`](../../src/intake/decision.py#L317-L347) - `BUDGET_FEASIBILITY_TABLE`
- [`frontend/src/app/workbench/DecisionTab.tsx:192-206`](../../frontend/src/app/workbench/DecisionTab.tsx#L192-L206) - Risk flags display

---

## Decision

We will implement an **enhanced scenario handling system** with the following key decisions:

### Decision 1: Structured Risk Format

**Decision:** Replace string-only `risk_flags` with `StructuredRisk` dataclass while maintaining backward compatibility.

**Rationale:**
- Current `risk_flags: List[str]` is insufficient for rich UI rendering
- Need category, severity, mitigation suggestions, and affected parties
- Must maintain backward compatibility for existing integrations

**Implementation:**
```python
@dataclass
class StructuredRisk:
    flag: str
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal["budget", "document", "weather", "routing", "activity", "composition"]
    title: str
    message: str
    details: Dict[str, Any]
    mitigation_suggestions: List[str]
    alternative_recommendations: List[str]
    # ... etc
```

**Consequences:**
- ✅ Rich, contextual risk information
- ✅ Enables detailed risk cards in UI
- ✅ Supports category-based filtering
- ⚠️ Slightly larger payload size
- ⚠️ Requires frontend type updates

---

### Decision 2: Modular Risk Detection

**Decision:** Create separate modules for each risk category that feed into `generate_risk_flags()`.

**Modules:**
1. **`route_analysis.py`** - Parse itinerary, calculate complexity, detect transfer risks
2. **`weather_risk.py`** - Seasonal risk database, destination + month → risk assessment
3. **`activity_matcher.py`** - Activity profiles, suitability scoring for party composition

**Rationale:**
- Each module can be developed, tested, and deployed independently
- Allows feature-flagging specific risk types
- Easier to extend with new risk categories later

**Consequences:**
- ✅ Clear separation of concerns
- ✅ Independent testing and versioning
- ✅ Can disable modules that aren't ready
- ⚠️ Need to define clear interfaces between modules
- ⚠️ Potential for module initialization overhead

---

### Decision 3: Route Parser Strategy

**Decision:** Implement hybrid route parsing: regex/rules-based first, LLM-based as fallback.

**Approach:**
1. **Primary:** Pattern matching on `itinerary_text` using known destinations and transport keywords
2. **Secondary:** If parsing confidence < threshold, use LLM to extract route structure
3. **Validation:** Cross-check against `destination_candidates` from packet

**Rationale:**
- Rule-based is fast and deterministic for common patterns
- LLM provides robust fallback for complex/natural language itineraries
- Need to balance accuracy with latency

**Consequences:**
- ✅ Handles both structured and unstructured itinerary inputs
- ✅ LLM fallback ensures coverage
- ⚠️ LLM adds latency (~500ms-2s)
- ⚠️ Need to cache LLM results
- ⚠️ Cost considerations for LLM usage

---

### Decision 4: Weather Data Strategy

**Decision:** Use static seasonal database initially, with optional API integration later.

**Initial Implementation:**
```python
SEASONAL_RISK_DB: Dict[str, List[SeasonalConditions]] = {
    "Bali": [
        SeasonalConditions(month=1, risk_level="high", risk_type="monsoon", ...),
        # ... 12 months
    ],
    # ... supported destinations
}
```

**Future Enhancement:** Optional integration with weather APIs for real-time adjustments.

**Rationale:**
- Static DB sufficient for 80% of use cases
- Predictable, no external dependencies
- Can be curated by travel experts
- APIs add complexity, cost, and latency

**Consequences:**
- ✅ No external API dependencies
- ✅ Fast lookups
- ✅ Expert-curated data
- ⚠️ Requires manual maintenance
- ⚠️ Won't account for year-to-year variations

---

### Decision 5: Frontend Component Strategy

**Decision:** Create new `scenario/` component directory with specialized viewers.

**Components:**
1. **`RouteVisualizer`** - Timeline visualization of journey segments
2. **`RiskDetailCard`** - Expandable risk cards with full context
3. **`WeatherRiskPanel`** - Calendar-based weather risk view
4. **`ActivitySuitabilityGrid`** - Activity × party compatibility matrix

**Rationale:**
- Current `DecisionTab` is already crowded
- Scenario analysis deserves dedicated visual treatment
- Can be conditionally rendered based on available data

**Consequences:**
- ✅ Clean separation from existing decision view
- ✅ Can iterate on UX independently
- ✅ Users can focus on relevant risks
- ⚠️ More components to maintain
- ⚠️ Need to integrate into existing tab structure

---

### Decision 6: Data Model Evolution

**Decision:** Add new structured fields to `DecisionResult` while keeping legacy fields.

```python
@dataclass
class DecisionResult:
    # Legacy (maintained for compatibility)
    risk_flags: List[str] = field(default_factory=list)
    
    # New structured data
    structured_risks: List[StructuredRisk] = field(default_factory=list)
    route_analysis: Optional[RouteAnalysis] = None
    weather_assessment: Optional[WeatherRiskAssessment] = None
    activity_assessment: Optional[PartyActivityAssessment] = None
```

**Rationale:**
- Avoids breaking changes to existing consumers
- Allows gradual migration
- Frontend can choose which data to use

**Consequences:**
- ✅ Zero breaking changes
- ✅ Gradual adoption path
- ⚠️ Duplicate data in payload (strings + structured)
- ⚠️ Need to keep both in sync

---

### Decision 7: Risk Severity Classification

**Decision:** Standardize severity levels: `low` | `medium` | `high` | `critical`

**Mapping:**

| Severity | Criteria | Action |
|----------|----------|--------|
| `critical` | Blocks progression, requires immediate attention | Decision: STOP_NEEDS_REVIEW |
| `high` | Strong warning, may block in strict mode | Decision: ASK_FOLLOWUP |
| `medium` | Advisory, traveler should be informed | Include in risk_flags |
| `low` | Minor concern, informational only | Include in details |

**Rationale:**
- Aligns with existing decision states (STOP_NEEDS_REVIEW, ASK_FOLLOWUP)
- Clear guidance for UI rendering (colors, icons)
- Consistent with security/vulnerability severity patterns

**Consequences:**
- ✅ Clear decision boundaries
- ✅ Consistent UI treatment
- ⚠️ Requires careful categorization during implementation

---

## Alternatives Considered

### Alternative 1: Monolithic Enhancement

**Approach:** Add all scenario logic directly to `decision.py`

**Rejected because:**
- Would make `decision.py` unmanageably large (>1500 lines)
- Tight coupling makes testing difficult
- Can't feature-flag specific capabilities

### Alternative 2: External Microservice

**Approach:** Deploy scenario analysis as separate service

**Rejected because:**
- Adds operational complexity
- Network latency for synchronous decision calls
- Current scale doesn't justify microservice overhead

### Alternative 3: LLM-Only Risk Detection

**Approach:** Use LLM to analyze scenarios and generate risks

**Rejected because:**
- Non-deterministic results
- Higher cost
- Slower than rule-based
- Better to use LLM for edge cases only

---

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Foundation | 1 week | StructuredRisk dataclass, type updates |
| 2. Route Analysis | 2 weeks | route_analysis.py, RouteVisualizer component |
| 3. Weather Risk | 1 week | weather_risk.py, WeatherRiskPanel component |
| 4. Activity Matching | 1 week | activity_matcher.py, ActivitySuitabilityGrid component |
| 5. Integration | 1 week | Wire into decision.py, testing, documentation |

**Total: 6 weeks**

---

## Related Decisions

- [decision_policy.md](../../specs/decision_policy.md) - NB02 decision rules
- [NB02_V02_IMPLEMENTATION.md](../NB02_V02_IMPLEMENTATION.md) - Current implementation

---

## Notes

### Performance Considerations
- Route parsing should complete in <200ms for simple itineraries
- Weather lookup is O(1) from dictionary
- Activity matching is O(n) where n = activities × party segments
- Total scenario analysis budget: <500ms additional latency

### Security Considerations
- No PII in scenario analysis (uses destination names, activity types only)
- Weather DB is public seasonal data
- Route analysis doesn't store actual flight details

### Monitoring
- Track scenario detection rates by category
- Monitor false positive rates (risks flagged but traveler proceeds anyway)
- Measure time spent in scenario analysis

---

*Approved by:* TBD  
*Last Updated:* 2026-04-15
