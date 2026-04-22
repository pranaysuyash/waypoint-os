# D5 Override Learning Plan — Design Document

**Date**: 2026-04-22
**ADR Reference**: `Docs/ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`
**Purpose**: Design the feedback bus connecting D1 judgment → human override → policy improvement, without implementing it

---

## 1. The Problem

From the D1 handoff:
> "No explicit override event capture loop for D1 exists yet."

From the governing principle:
> "Every repeated LLM judgment should be considered a candidate for graduation into a deterministic rule."

The D5 problem: **how does the system learn when owners/agents disagree with its recommendations?**

When NB02 says `PROCEED_TRAVELER_SAFE` but the owner thinks it should be `STOP_NEEDS_REVIEW`, that's an override. The system should remember that and adjust future behavior — but only in narrow, safe ways.

---

## 2. Override Taxonomy

Three categories of override, each requiring different learning strategies:

| Category | Definition | Example | Frequency | Learning Approach |
|----------|-----------|---------|-----------|-----------------|
| **Decision Override** | D1 autonomy gate disagreed with | System said `auto`, owner changed to `review` | Medium | Per-state policy adjustment |
| **Suitability Override** | Activity recommendation rejected | System suggested paragliding, owner rejected due to age | Low-medium | Per-activity tag weight adjustment |
| **Sourcing Override** | Supplier match rejected | System suggested Supplier A, owner prefers Supplier B | High | Per-agency supplier preference learning |

---

## 3. Event Schema Design

### OverrideEvent

```python
@dataclass
class OverrideEvent:
    """Structured record of a human override."""
    
    # Identity
    event_id: str  # UUID
    event_timestamp: str  # ISO 8601
    
    # Actor
    actor_type: Literal["owner", "agent", "junior_agent", "system"]
    actor_id: str  # Clerk user ID
    agency_id: str  # Multi-tenant key (future)
    
    # What was overridden
    override_category: Literal["decision", "suitability", "sourcing"]
    
    # D1-specific fields
    original_state: str  # NB02 decision_state
    original_autonomy_action: str  # what D1 recommended (auto/review/block)
    overridden_state: str  # what the human chose
    overridden_autonomy_action: str  # what the human required
    
    # Suitability-specific fields
    activity_id: Optional[str]
    original_suitability_score: Optional[float]
    overridden_suitability_score: Optional[float]
    
    # Sourcing-specific fields
    original_supplier_id: Optional[str]
    overridden_supplier_id: Optional[str]
    
    # Learning fields
    rationale: str  # Required: why the human overrode
    rationale_tags: List[str]  # structured tags
    
    # Context (anonymized)
    packet_context_hash: str  # hash of packet, not full packet (privacy)
    decision_type: Optional[str]  # for hybrid engine correlation
    trip_type: Optional[str]  # family, solo, couple, group
    destination_region: Optional[str]  # SEA, Europe, Domestic, etc.
    budget_tier: Optional[str]  # economy, premium, luxury
    
    # Derived (computed later)
    outcome: Optional[Literal["confirmed_correct", "confirmed_wrong", "unknown"]] = None
    outcome_timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]: ...
```

### Rationale Tag Taxonomy

| Tag | Meaning | Used By |
|-----|---------|---------|
| `too_conservative` | System blocked when it should have auto'd | D1 policy |
| `too_permissive` | System auto'd when it should have blocked | D1 policy |
| `wrong_activity` | Activity was unsuitable for this traveler | D4 suitability |
| `supplier_preference` | Agency has preferred supplier | D3 sourcing |
| `margin_conflict` | Suggested supplier has wrong margin | D3 sourcing |
| `quality_issue` | Past bad experience with suggestion | D3 sourcing |
| `traveler_specific` | Unique traveler constraint not in data | D4 suitability |
| `seasonal` | Seasonal factor not captured | D4 suitability |

---

## 4. Capture Loop Architecture

### Where Overrides Happen

**D1 Override Capture Points:**

1. **Workbench override button** — Agent clicks "Override" on a `PROCEED_TRAVELER_SAFE` decision, changes autonomy to `review`
2. **Settings policy change** — Owner updates `approval_gates` after seeing a pattern of bad auto-decisions
3. **Review queue action** — Owner in `/owner/reviews` approves/rejects an autonomous decision

**D4 Override Capture Points:**

1. **Activity removal** — Agent removes an auto-suggested activity from itinerary
2. **Tag correction** — Agent changes suitability tags (e.g. removes "adventure" from elderly traveler)

**D3 Override Capture Points:**

1. **Supplier swap** — Agent replaces auto-suggested supplier
2. **Margin override** — Owner adjusts margin floor after realizing suggestion was unprofitable

### Capture Flow

```
Human Override Action
    ↓
[Override Capture Middleware] — intercepts the action
    ↓
[Prompt for Rationale] — "Why are you overriding?" (required, not optional)
    ↓
[Tag Classification] — auto-suggest tags based on rationale text
    ↓
[Anonymization] — strip PII, keep trip type / region / budget tier
    ↓
[Event Storage] — `OverrideEvent` persisted to Event Store
    ↓
[Immediate Feedback] — update CachedDecision.success_rate if applicable
    ↓
[Queue for Batch Learning] — daily/weekly batch job
```

---

## 5. Learning Phases

### Phase 1: Frequency-Based Signals (No ML)

No model. Simple frequency counting.

```python
class FrequencyBasedPolicyAdjuster:
    """Count overrides and suggest policy changes."""
    
    def analyze(self, events: List[OverrideEvent]) -> PolicySuggestions:
        # For each decision_state + override_type
        for state in DECISION_STATES:
            total = events.count(state=state)
            too_conservative = events.count(state=state, tag="too_conservative")
            too_permissive = events.count(state=state, tag="too_permissive")
            
            if too_permissive / total > 0.3:
                # Suggest: tighten gate for this state
                yield Suggestion(
                    target=f"approval_gates.{state}",
                    current="auto",
                    proposed="review",
                    confidence=too_permissive / total,
                    reason=f"{too_permissive}/{total} overrides were 'too permissive'"
                )
```

**Timeline**: Can implement immediately after override capture exists.

### Phase 2: Context-Aware Rules (Rule-Based, Not ML)

Still no ML. Structured rules based on trip context.

Example learned rule:
```python
if trip_type == "family" and destination_region == "SEA" and budget_tier == "economy":
    # Historical data: 80% of PROCEED_TRAVELER_SAFE auto-detected for this pattern
    # were overridden to review due to "underbudgeted child activities"
    suggestion = {
        "gate": "PROCEED_TRAVELER_SAFE",
        "condition": "family + SEA + economy",
        "recommended_action": "review",
        "historical_override_rate": 0.80,
        "sample_size": 45,
    }
```

**Timeline**: Needs ~50+ labeled overrides per category.

### Phase 3: Statistical Classification (Lightweight ML)

A lightweight classifier (logistic regression or small decision tree) that predicts override likelihood based on trip context.

**Inputs**: trip_type, destination_region, budget_tier, party_composition, season
**Output**: override_probability for each decision_state
**Action**: If P(override) > 0.7, downgrade to `review`

**Constraints**:
- Model must be interpretable (no black box)
- Model must not auto-promote (only downgrade)
- Model must be versioned and rollback-able
- Model must be evaluated on held-out data before deployment

**Timeline**: Needs ~500+ labeled overrides. This is months away.

---

## 6. Policy Change Approval

The system NEVER auto-adjusts policy. It only **suggests** changes.

### Suggestion Flow

```
Learning system generates suggestion
    ↓
Suggestion queued in owner dashboard
    ↓
Owner sees: "Based on 12 recent overrides, consider changing PROCEED_TRAVELER_SAFE for family + SEA trips from 'auto' to 'review'"
    ↓
Owner clicks "Review Details" — sees specific overrides with context
    ↓
Owner chooses:
    - "Apply" → policy updated, event logged
    - "Dismiss" → suggestion archived, learning notes dismissal
    - "Modify" → owner edits proposed gate before applying
```

### Approval Record
Every policy change is recorded:
- Who approved it
- What data supported it
- What the previous value was
- When it was applied

This is the **audit trail for autonomy**.

---

## 7. Event Storage

### Storage Options (until Gap #02 is resolved)

| Option | Pros | Cons |
|--------|------|------|
| **JSONL file** (current) | Simple, works today | No queryability, no aggregation |
| **SQLite** (interim) | Queryable, no external deps | Single-file, no multi-tenancy |
| **Postgres table** (post-Gap-#02) | Full relational power | Blocked on persistence |

**Recommendation**: Start with JSONL files, migrate to SQLite when volume demands it, switch to Postgres when Gap #02 closes.

### JSONL Schema
```jsonl
{"event_id": "...", "event_timestamp": "...", /* all OverrideEvent fields */}
{"event_id": "...", "event_timestamp": "...", /* all OverrideEvent fields */}
```

---

## 8. D5/D2/D6 Integration

### How D5 Feeds D2

Consumer surface (D2) should be **over-cautious** by default. The D5 learning loop helps identify which consumer-facing outputs are trustworthy:

```
D2 generates consumer output
    ↓
Consumer uses output / books consultation
    ↓
Agency owner reviews the lead trip
    ↓
If owner disagrees with D2 assessment → OverrideEvent captured
    ↓
D5 learning suggests tightening D2 gates for that pattern
    ↓
D2 becomes more accurate over time
```

### How D5 Feeds D6

Override events are evidence for eval:

```
D6 golden path fixture passes
    ↓
Production traffic includes override
    ↓
D5 records: "packet X was overriden from auto to review"
    ↓
D6 analysis: "Golden path said PROCEED_TRAVELER_SAFE, but 80% of similar real packets were overriden"
    ↓
Fixture updated to reflect real-world complexity
```

---

## 9. Implementation Order

1. **Phase 0 — Event Schema** (this doc) — Define `OverrideEvent` dataclass + rationale taxonomy
2. **Phase 1 — Capture Infrastructure** — Add `emit_override_event()` to key action points (override button, settings change, review action)
3. **Phase 2 — Frequency Dashboard** — Show owner: "You overrode 12 decisions this week. Here's the pattern."
4. **Phase 3 — Suggestion Engine** — Generate concrete policy suggestions from frequency data
5. **Phase 4 — Statistical Classification** — Build override predictor (requires ~500 events)

---

## 10. Verification

Success criteria:

1. ✅ OverrideEvent schema captures all three categories
2. ✅ Rationale is required (not optional)
3. ✅ Policy changes are suggestions, not auto-applied
4. ✅ Audit trail records every change
5. ✅ PII is stripped before storage

```python
# Conceptual test
from src.learning.override_event import OverrideEvent
event = OverrideEvent(
    override_category="decision",
    original_state="PROCEED_TRAVELER_SAFE",
    overridden_state="STOP_NEEDS_REVIEW",
    rationale="Budget was too low for Maldives in peak season",
    rationale_tags=["too_permissive", "seasonal"],
)
assert event.rationale  # Required field
assert "too_permissive" in event.rationale_tags
```

---

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
References:
- `Docs/ARCHITECTURE_DECISION_D5_OVERRIDE_LEARNING_2026-04-18.md`
- `Docs/D1_IMPLEMENTATION_SUMMARY_2026-04-22.md`
- `Docs/D2_CONSUMER_SURFACE_CONTRACT_DESIGN_2026-04-22.md`
- `Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md`
