# Research: Internal Data Integration with Pipeline

**Status**: 🟡 Exploration — Integration Architecture  
**Topic ID**: 16b (Extension of AGENCY_INTERNAL_DATA)  
**Parent**: [AGENCY_INTERNAL_DATA.md](AGENCY_INTERNAL_DATA.md)  
**Last Updated**: 2026-04-09

---

## The Question

> How does preferred hotel data interact with the Gap & Decision system?

**Short answer**: Internal data doesn't just affect the *output* — it can change the *decision* itself, enable new decision states, and provide richer signals for existing logic.

---

## Current Pipeline (Without Internal Data)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   NB01       │────▶│   NB02       │────▶│   NB03           │
│  Intake      │     │  Gap &       │     │  Session         │
│              │     │  Decision    │     │  Strategy        │
└──────────────┘     └──────────────┘     └──────────────────┘
                                                          │
                                                          ▼
                                               ┌──────────────────┐
                                               │  Ask traveler /  │
                                               │  Draft proposal  │
                                               └──────────────────┘
```

**NB02 logic**:
1. Check contradictions → STOP_NEEDS_REVIEW
2. Check hard blockers → ASK_FOLLOWUP
3. Check budget contradictions → BRANCH_OPTIONS
4. Check confidence threshold → PROCEED

**NB03 logic**:
1. Decision state drives strategy
2. Format questions/prompts based on tone
3. Present branches or draft output

**What's missing**: No knowledge of:
- What hotels the agency prefers
- What packages work for similar customers
- Which vendors are reliable
- What margins exist

---

## Integration Points

### 1. Preferred Supplier Filtering (NB02 Enhancement)

**Current**: NB02 decides based on field completeness alone.

**With Internal Data**: NB02 can check if constraints match *available* preferred options.

```python
# New: Preferred supplier compatibility check
def check_preferred_compatibility(packet: CanonicalPacket, preferred_data: dict) -> dict:
    """
    Check if customer constraints are compatible with preferred suppliers.
    Returns compatibility issues that may trigger special handling.
    """
    destination = packet.facts.get("destination_city")
    budget = packet.facts.get("budget_range")
    composition = packet.facts.get("traveler_composition")
    
    issues = []
    
    # Check 1: Do we have preferred hotels for this destination?
    if destination and destination.value:
        dest_hotels = preferred_data.get("hotels", {}).get(destination.value, [])
        if not dest_hotels:
            issues.append({
                "type": "no_preferred_hotels",
                "field": "destination_city",
                "value": destination.value,
                "impact": "Will need to source from open market (higher risk)",
                "suggestion": "Consider suggesting alternative destinations where we have preferred hotels"
            })
    
    # Check 2: Does budget align with preferred hotel tiers?
    if budget and destination:
        dest_hotels = preferred_data.get("hotels", {}).get(destination.value, [])
        affordable = [h for h in dest_hotels if h.get("min_budget", 0) <= budget.value]
        if not affordable:
            issues.append({
                "type": "budget_mismatch_preferred",
                "field": "budget_range",
                "value": budget.value,
                "impact": "Preferred hotels start at ₹12K/night, budget allows ₹8K/night",
                "suggestion": "Recommend budget adjustment OR use open-market hotels"
            })
    
    # Check 3: Is traveler composition suitable for preferred options?
    if composition and destination:
        # e.g., "family_with_toddler" - do we have toddler-friendly preferred hotels?
        pass
    
    return issues
```

**New Decision State**: `BRANCH_DESTINATION` — when preferred suppliers don't exist for the chosen destination.

```python
# Example: Customer wants "Vietnam", agency only has preferred suppliers for "Singapore", "Thailand"
{
    "decision_state": "BRANCH_DESTINATION",
    "rationale": "No preferred hotels in Vietnam. Can proceed with open market (risk) or suggest destinations where we have preferred suppliers.",
    "branch_options": [
        {
            "label": "Proceed with Vietnam (Open Market)",
            "description": "Source hotels outside preferred network",
            "trade_offs": ["Less familiar properties", "Higher research time", "Unknown reliability"],
            "risk_level": "medium"
        },
        {
            "label": "Consider Thailand instead",
            "description": "Similar beaches, we have 8 preferred hotels",
            "trade_offs": ["Different country", "Better value through preferred suppliers", "Proven track record"],
            "risk_level": "low"
        }
    ]
}
```

---

### 2. Historical Pattern Confidence Boost (NB02 Enhancement)

**Current**: Confidence is computed from authority weights only.

```python
AUTHORITY_WEIGHTS = {
    "manual_override": 1.0, "explicit_user": 0.95, ...
}
```

**With Internal Data**: Historical patterns can provide "soft confirmation" that boosts confidence.

```python
def compute_historical_confidence_boost(packet: CanonicalPacket, historical_data: dict) -> float:
    """
    Check if this booking pattern matches historical success patterns.
    Returns confidence boost (0.0 - 0.15).
    """
    destination = packet.facts.get("destination_city", {}).value
    composition = packet.facts.get("traveler_composition", {}).value
    budget = packet.facts.get("budget_range", {}).value
    
    boost = 0.0
    
    # Pattern 1: "Families like this loved Singapore"
    if destination and composition:
        similar_bookings = historical_data.get_bookings(
            destination=destination,
            composition=composition,
            satisfaction_min=4.5
        )
        if len(similar_bookings) >= 10:
            boost += 0.10
            # Store signal for NB03
            packet.derived_signals["historical_pattern_match"] = {
                "value": f"{len(similar_bookings)} similar bookings, avg satisfaction {avg(similar_bookings.satisfaction)}",
                "confidence": 0.9,
                "authority_level": "derived_signal"
            }
    
    # Pattern 2: "This budget is typical for this destination"
    if destination and budget:
        avg_budget = historical_data.get_avg_budget(destination)
        if abs(budget - avg_budget) / avg_budget < 0.2:  # Within 20%
            boost += 0.05
    
    return min(boost, 0.15)  # Cap at 0.15
```

**Impact on NB02**:
- Confidence 0.75 → 0.85 (crosses threshold to PROCEED_TRAVELER_SAFE)
- Historical pattern signal becomes part of the rationale

---

### 3. Wasted Spend Detection (New Blocker Type)

**Current**: Blockers are just missing fields.

**With Internal Data**: Can detect "high wasted spend risk" even when all fields are filled.

```python
def detect_wasted_spend_risk(packet: CanonicalPacket, tribal_knowledge: dict) -> List[dict]:
    """
    Use tribal knowledge to detect bookings where traveler won't get value.
    Returns 'advisory blockers' — not hard stops, but warnings.
    """
    risks = []
    
    # Example: Universal Studios with toddlers and elderly
    destination = packet.facts.get("destination_city", {}).value
    activities = packet.facts.get("requested_activities", {}).value  # e.g., ["Universal Studios"]
    composition = packet.facts.get("traveler_composition", {}).value  # e.g., "2 adults, 2 elderly, 1 toddler"
    
    if destination == "Singapore" and "Universal_Studios" in (activities or []):
        # Check tribal knowledge
        activity_reality = tribal_knowledge.get("activities", {}).get("Universal_Studios_Singapore", {})
        suitability = activity_reality.get("suitability", {})
        
        # Parse composition
        has_toddler = "toddler" in composition.lower() if composition else False
        has_elderly = "elderly" in composition.lower() if composition else False
        
        if has_toddler and has_elderly:
            risks.append({
                "type": "wasted_spend_risk",
                "severity": "high",
                "field": "requested_activities",
                "value": "Universal Studios",
                "reason": "Tribal knowledge: toddlers can ride 2-3 attractions, elderly struggle with walking. 3/5 travelers won't enjoy.",
                "suggested_alternatives": ["Gardens_by_the_Bay", "Singapore_Zoo"],
                "estimated_wasted_spend": "₹15,000"
            })
    
    return risks
```

**New Decision State**: `ADVISORY_BRANCH` — not a blocker, but a "are you sure?" moment.

```python
{
    "decision_state": "ADVISORY_BRANCH",
    "hard_blockers": [],  # All fields filled
    "advisory_flags": [{
        "type": "wasted_spend_risk",
        "message": "Universal Studios may not be suitable for your group composition"
    }],
    "branch_options": [
        {
            "label": "Keep Universal Studios",
            "description": "Proceed with USS booking",
            "trade_offs": ["₹15K potentially wasted", "Some travelers may not participate"]
        },
        {
            "label": "Consider alternatives",
            "description": "Gardens by the Bay + Zoo (better for mixed ages)",
            "trade_offs": ["No roller coasters", "Free/much cheaper", "All ages enjoy"]
        }
    ]
}
```

---

### 4. Supplier Reliability Risk Flags (NB03 Enhancement)

**Current**: NB03 risk flags are generic ("urgent", "ambiguous").

**With Internal Data**: Risk flags include vendor-specific concerns.

```python
def build_reliability_risk_flags(packet: CanonicalPacket, vendor_scores: dict) -> List[str]:
    """
    Generate risk flags based on vendor reliability scores.
    """
    risks = []
    
    # Check if selected hotel has reliability issues
    hotel = packet.facts.get("selected_hotel", {}).value
    if hotel:
        score = vendor_scores.get("hotels", {}).get(hotel, {}).get("reliability_score", 5.0)
        if score < 7.0:
            risks.append(f"RELIABILITY WARNING: {hotel} has score {score}/10. 15% booking change rate.")
        if score < 5.0:
            risks.append(f"HIGH RISK: {hotel} blacklisted by agency. Find alternative.")
    
    # Check if dates are during high-risk period for destination
    dates = packet.facts.get("travel_dates", {}).value
    destination = packet.facts.get("destination_city", {}).value
    if destination and dates:
        # e.g., "Avoid Singapore in December — peak prices, availability issues"
        pass
    
    return risks
```

**Impact on SessionStrategy**:

```python
SessionStrategy(
    session_goal="Generate proposal for Singapore family trip",
    risk_flags=[
        "RELIABILITY WARNING: Hotel Y has score 6/10",
        "URGENT: Booking within 7 days",
    ],
    # ...
)
```

---

### 5. Margin-Aware Branch Ranking (NB02 Enhancement)

**Current**: Branches are presented neutrally.

**With Internal Data**: Branches can be ranked by margin potential without biasing presentation.

```python
def rank_branches_by_margin(branch_options: List[dict], margin_data: dict) -> List[dict]:
    """
    Sort branches by margin potential (highest first) without changing neutral presentation.
    Internal use only — traveler still sees neutral options.
    """
    def branch_margin(branch):
        # Compute estimated margin for this branch
        total = 0
        for component in branch.get("components", []):
            supplier = component.get("supplier")
            margin_pct = margin_data.get("suppliers", {}).get(supplier, {}).get("margin", 0)
            cost = component.get("cost", 0)
            total += cost * margin_pct
        return total
    
    # Sort but keep neutral presentation
    ranked = sorted(branch_options, key=branch_margin, reverse=True)
    
    # Add internal note about ranking
    for i, branch in enumerate(ranked):
        branch["_internal_margin_rank"] = i + 1
        branch["_estimated_margin"] = branch_margin(branch)
    
    return ranked
```

**Impact on NB03**:

```python
# In PromptBundle.internal_notes
internal_notes = """
Branch ranking (by margin):
1. Option A (Hard Rock): ₹18K margin — RECOMMENDED
2. Option B (MBS): ₹12K margin
3. Option C (Hotel X): ₹8K margin

Customer-facing presentation: All options shown neutrally.
"""
```

---

### 6. Customer Memory Integration (NB02 + NB03)

**Current**: Each session starts fresh.

**With Internal Data**: Past preferences affect current decision.

```python
def apply_customer_memory(packet: CanonicalPacket, customer_profile: dict) -> CanonicalPacket:
    """
    Enrich packet with learned customer preferences.
    """
    # Example: Customer always prefers pool hotels (learned from 8/10 bookings)
    preferred_amenities = customer_profile.get("learned_preferences", {}).get("amenities", [])
    if "pool" in preferred_amenities and "hotel_amenities" not in packet.facts:
        # Add as derived signal — not fact (never stated), but strong pattern
        packet.derived_signals["likely_prefers_pool"] = {
            "value": True,
            "confidence": 0.85,
            "authority_level": "derived_signal",
            "source": "historical_booking_pattern",
            "evidence": "8/10 previous bookings had pool"
        }
    
    # Example: Customer had bad experience with long layovers
    pain_points = customer_profile.get("pain_points", [])
    for point in pain_points:
        if point.get("issue") == "long_layover":
            # Add constraint to packet
            packet.derived_signals["avoid_long_layovers"] = {
                "value": True,
                "confidence": 0.95,
                "authority_level": "derived_signal",
                "source": "stated_pain_point"
            }
    
    return packet
```

**Impact on NB02**:
- "avoid_long_layovers" becomes a soft blocker for flights with >2 hour layovers
- Confidence boosted if selected hotel has pool

**Impact on NB03**:

```python
PromptBundle(
    system_context="""
    Customer context:
    - Repeat customer (3 previous bookings)
    - Strong preference for hotels with pools (8/10 bookings)
    - Previous issue: Long layover in Dubai 2024 (avoid)
    
    Use this context to tailor recommendations.
    """,
    # ...
)
```

---

## Full Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INTERNAL DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  PREFERRED   │  │  TRIBAL      │  │  HISTORICAL  │  │  CUSTOMER    │        │
│  │  SUPPLIERS   │  │  KNOWLEDGE   │  │  PATTERNS    │  │  MEMORY      │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                 │                │
│         ▼                 ▼                  ▼                 ▼                │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                    DATA ENRICHMENT FUNCTIONS                         │       │
│  │  - check_preferred_compatibility()   - detect_wasted_spend_risk()    │       │
│  │  - compute_historical_confidence()   - apply_customer_memory()       │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         NB02: GAP & DECISION (Enhanced)                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INPUT: CanonicalPacket ─────────────────────────────────────┐                  │
│                                                              │                  │
│  ┌────────────────────────────────────────────────────────┐  │                  │
│  │  ENRICHMENT STAGE (New)                                │  │                  │
│  │  1. Apply customer memory → derived_signals            │  │                  │
│  │  2. Check preferred compatibility → compatibility_issues│  │                  │
│  │  3. Detect wasted spend risk → advisory_flags          │  │                  │
│  │  4. Compute historical confidence boost                │  │                  │
│  └────────────────────────────────────────────────────────┘  │                  │
│                              │                               │                  │
│                              ▼                               │                  │
│  ┌────────────────────────────────────────────────────────┐  │                  │
│  │  DECISION LOGIC (Existing + New States)                │  │                  │
│  │                                                        │  │                  │
│  │  IF contradictions → STOP_NEEDS_REVIEW                 │  │                  │
│  │  IF hard_blockers → ASK_FOLLOWUP                       │  │                  │
│  │  IF compatibility_issues → BRANCH_DESTINATION (NEW)    │  │                  │
│  │  IF advisory_flags → ADVISORY_BRANCH (NEW)             │  │                  │
│  │  IF budget_contradictions → BRANCH_OPTIONS             │  │                  │
│  │  IF confidence >= threshold → PROCEED_*                │  │                  │
│  └────────────────────────────────────────────────────────┘  │                  │
│                              │                               │                  │
│                              ▼                               │                  │
│  OUTPUT: DecisionResult (with internal_data_refs) ◀──────────┘                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      NB03: SESSION STRATEGY (Enhanced)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INPUT: DecisionResult + Internal Data ────────────────────┐                    │
│                                                            │                    │
│  Strategy Builder Enhancements:                            │                    │
│  - build_reliability_risk_flags() → risk_flags            │                    │
│  - rank_branches_by_margin() → internal ranking           │                    │
│  - generate_supplier_context() → system_context           │                    │
│                                                            │                    │
│  OUTPUT: SessionStrategy + PromptBundle                    │                    │
│  - Includes vendor reliability warnings                   │                    │
│  - Includes margin-aware internal notes                   │                    │
│  - Includes customer preference context                   │                    │                    │
│                                                            │                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Read-Only Integration (Week 1-2)
- Internal data is read-only reference
- NB02 checks preferred compatibility (adds advisory, doesn't block)
- NB03 includes supplier reliability in risk flags
- No new decision states yet

### Phase 2: Advisory States (Week 3-4)
- Add ADVISORY_BRANCH decision state
- Wasted spend detection triggers advisory
- Customer memory enriches prompts

### Phase 3: Active Routing (Month 2)
- Add BRANCH_DESTINATION decision state
- Preferred supplier gaps trigger alternative suggestions
- Margin-aware branch ranking

### Phase 4: Learning Loop (Month 3)
- Post-trip feedback updates tribal knowledge
- Booking outcomes update reliability scores
- Customer preferences learned from choices

---

## New Decision States Summary

| State | Trigger | Internal Data Used |
|-------|---------|-------------------|
| `ASK_FOLLOWUP` | Missing required fields | Customer memory (what they usually prefer) |
| `BRANCH_OPTIONS` | Contradictory signals | Historical patterns (what similar customers chose) |
| `BRANCH_DESTINATION` | No preferred suppliers for destination | Preferred supplier network |
| `ADVISORY_BRANCH` | Wasted spend risk detected | Tribal knowledge |
| `PROCEED_INTERNAL_DRAFT` | Low confidence, soft blockers | Margin data (prioritize high-margin options) |
| `PROCEED_TRAVELER_SAFE` | High confidence, all clear | Customer memory, reliability scores |
| `STOP_NEEDS_REVIEW` | Critical contradictions | All data for human context |

---

## Key Design Principles

1. **Internal data enriches, doesn't override** — Still need explicit user signals
2. **Advisory, not prescriptive** — Suggest based on data, let user decide
3. **Internal notes for agents** — Margin rankings, reliability warnings (not shown to travelers)
4. **Learn from outcomes** — Every booking updates internal data
5. **Graceful degradation** — Works without internal data, better with it

---

## Related Topics

- [AGENCY_INTERNAL_DATA.md](AGENCY_INTERNAL_DATA.md) — What data exists
- [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) — Master index
- Notebook 02 contract — Base decision logic
- Notebook 03 contract — Session strategy logic

---

*This is an integration architecture doc. Implementation pending.*
