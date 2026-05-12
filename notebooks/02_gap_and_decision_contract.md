# DEPRECATION NOTICE (2026-05-12)

This file is retained for history only. It contains legacy contract language and legacy field names (`destination_city`, `travel_dates`, `budget_range`, `traveler_count`) that are NOT canonical in current runtime.

## Canonical sources (current)
- `/Users/pranay/Projects/travel_agency_agent/src/intake/decision.py`
- `/Users/pranay/Projects/travel_agency_agent/specs/decision_policy.md`
- `/Users/pranay/Projects/travel_agency_agent/notebooks/NB02_V02_SPEC.md`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py`

## Current contract notes
- Runtime packet model in code is `CanonicalPacket` v0.3 (`packet_models.py`), while some specs still reference v0.2.
- Decision states are constrained to:
  - `ASK_FOLLOWUP`
  - `PROCEED_INTERNAL_DRAFT`
  - `PROCEED_TRAVELER_SAFE`
  - `BRANCH_OPTIONS`
  - `STOP_NEEDS_REVIEW`

---

# Notebook 02: Gap and Decision - Contract Definition

## Environment

- **Package manager**: `uv` — run tests with `uv run python <script>` or `.venv/bin/python`
- **Python**: 3.13, venv at `.venv/`

## Purpose

Transform a `CanonicalPacket` into a `DecisionState` by identifying blockers, contradictions, and determining the next action.

---

## Inputs

| Input                  | Type            | Description                                             |
| ---------------------- | --------------- | ------------------------------------------------------- |
| `packet`               | CanonicalPacket | The state object from Notebook 01                       |
| `current_stage`        | str             | One of: `discovery`, `shortlist`, `proposal`, `booking` |
| `mvb_config`           | dict            | Minimum Viable Blockers per stage                       |
| `contradiction_policy` | dict            | How to handle conflicting values                        |
| `confidence_threshold` | float           | Minimum confidence to consider a field "filled"         |

---

## Outputs

| Output                | Type       | Description                              |
| --------------------- | ---------- | ---------------------------------------- |
| `hard_blockers`       | List[str]  | Required fields that are missing/unknown |
| `soft_blockers`       | List[str]  | Fields that could be inferred or asked   |
| `contradictions`      | List[dict] | Active conflicts that need resolution    |
| `decision_state`      | str        | One of 5 states (see below)              |
| `follow_up_questions` | List[dict] | Ordered questions to ask                 |
| `branch_options`      | List[dict] | Optional alternative paths               |
| `rationale`           | dict       | Summary of why this decision was made    |

---

## Decision States

| State                    | When                                         | Description                             |
| ------------------------ | -------------------------------------------- | --------------------------------------- |
| `ASK_FOLLOWUP`           | Hard blockers exist or critical info missing | Need more information before proceeding |
| `PROCEED_INTERNAL_DRAFT` | No hard blockers, confidence sufficient      | Can draft options for internal review   |
| `PROCEED_TRAVELER_SAFE`  | All critical fields filled, high confidence  | Safe to present to traveler             |
| `BRANCH_OPTIONS`         | Multiple valid paths exist                   | Present alternatives to decision maker  |
| `STOP_NEEDS_REVIEW`      | Contradictions or anomalies detected         | Human review required                   |

---

## MVB (Minimum Viable Blockers) by Stage

### Discovery Stage

```python
HARD_BLOCKERS = [
    "destination_city",      # Where are they going?
    "origin_city",           # Where are they starting?
    "travel_dates",          # When?
    "traveler_count",        # How many people?
]

SOFT_BLOCKERS = [
    "budget_range",          # Can infer or ask
    "trip_purpose",          # Can infer or ask
    "traveler_preferences",   # Can refine later
]
```

### Shortlist Stage

```python
HARD_BLOCKERS = DISCOVERY_HARD_BLOCKERS + [
    "selected_destinations",  # Narrowed down options
]

SOFT_BLOCKERS = [
    "activity_preferences",
    "accommodation_type",
]
```

### Proposal Stage

```python
HARD_BLOCKERS = SHORTLIST_HARD_BLOCKERS + [
    "selected_itinerary",     # Chosen from shortlist
]

SOFT_BLOCKERS = [
    "special_requests",
    "dietary_restrictions",
]
```

### Booking Stage

```python
HARD_BLOCKERS = PROPOSAL_HARD_BLOCKERS + [
    "traveler_details",       # Names, DOB, passport info
    "payment_method",
]

SOFT_BLOCKERS = []
```

---

## Contradiction Policy

```python
CONTRADICTION_HANDLING = {
    "destination_conflict": {
        "action": "ASK_FOLLOWUP",
        "priority": "critical",
        "message": "Multiple destinations mentioned. Please clarify."
    },
    "date_conflict": {
        "action": "STOP_NEEDS_REVIEW",
        "priority": "critical",
        "message": "Conflicting travel dates detected."
    },
    "budget_conflict": {
        "action": "BRANCH_OPTIONS",
        "priority": "medium",
        "message": "Budget range could indicate different trip tiers."
    }
}
```

---

## Follow-Up Question Generation

### Priority Ordering

1. Hard blockers first (most critical)
2. Soft blockers (can be inferred)
3. Refinements (optional improvements)

### Question Template

```python
{
    "field_name": str,
    "question": str,
    "priority": str,  # "critical", "high", "medium", "low"
    "can_infer": bool,
    "inference_confidence": float,
    "suggested_values": List[str],  # Optional
}
```

---

## Core Logic Flow

```
1. Load CanonicalPacket
2. Check contradictions → if critical, STOP_NEEDS_REVIEW
3. Identify hard blockers for current stage
4. Identify soft blockers for current stage
5. Calculate overall confidence score
6. Determine decision state:
   - Hard blockers > 0 → ASK_FOLLOWUP
   - Contradictions > 0 → evaluate per policy
   - Confidence >= threshold & no blockers → PROCEED_*
   - Multiple valid paths → BRANCH_OPTIONS
7. Generate ordered follow-up questions
8. Return decision packet
```

---

## Confidence Scoring

```python
def calculate_confidence(packet: CanonicalPacket) -> float:
    """
    Weighted confidence based on:
    - Fact confidence (authority-weighted)
    - Hypothesis confidence (discounted)
    - Unknown penalties
    """
    fact_weight = sum(
        slot.confidence * AUTHORITY_WEIGHTS[slot.authority_level]
        for slot in packet.facts.values()
    )
    hypothesis_weight = sum(
        slot.confidence * 0.5  # Discount hypotheses
        for slot in packet.hypotheses.values()
    )
    unknown_penalty = len(packet.unknowns) * 0.1

    return min(1.0, max(0.0, fact_weight + hypothesis_weight - unknown_penalty))
```

---

## Implementation Notes

1. **Hypotheses do NOT fill blockers** - Only facts count for blocker resolution
2. **Derived signals CAN fill blockers** - If authority is `derived_signal`
3. **Contradictions must be resolved** - Before proceeding to next stage
4. **Confidence threshold is configurable** - Per stage and per client
5. **Questions are ordered by impact** - Critical blockers first

---

## Test Cases

### Implemented (68 unit + 13 scenario tests — 100% pass)

See `notebooks/02_SCENARIO_TEST_RESULTS.md` for full results.

Core scenarios covered:

1. Empty packet → ASK_FOLLOWUP with all hard blockers
2. Complete packet → PROCEED_TRAVELER_SAFE
3. Packet with hypothesis only → Still ASK_FOLLOWUP (hypothesis doesn't fill blocker)
4. Packet with derived_signal → fills blocker (contract rule confirmed)
5. Date contradiction → STOP_NEEDS_REVIEW
6. Budget contradiction → BRANCH_OPTIONS (when no hard blockers)
7. Soft blockers only → PROCEED_INTERNAL_DRAFT
8. Stage progression (discovery → shortlist → proposal → booking)
9. Multi-source envelope merging
10. Urgency/last-minute (see Known Limitations below)

---

## Known Limitations (from Scenario Testing)

### 1. Ambiguous Values Not Detected

**Gap**: "Andaman or Sri Lanka" is treated as a valid destination value. The MVB checks field existence, not value specificity.
**Impact**: System may say PROCEED when the traveler hasn't actually decided.
**Where to fix**: NB01 should tag ambiguous values with a `destination_status` field (decided / semi-open / open). NB03 should detect "or" patterns during question generation.
**Priority**: Medium — NB01 extraction issue.

### 2. No Urgency Handling

**Gap**: "This weekend, flying Friday" → soft blockers still block PROCEED_TRAVELER_SAFE. System asks about trip_purpose when urgency is extreme.
**Impact**: Conservative but wasteful — agent asks unnecessary questions on last-minute trips.
**Where to fix**: Add `urgency` flag to packet. When set, suppress soft blocker questions.
**Priority**: Low — current behavior is safe, just annoying.

### 3. Budget Stretch Not Structured

**Gap**: "200000 (can stretch)" is a string. Numeric value and stretch signal not parsed separately.
**Impact**: Sourcing tier uses base budget. Stretch signal lost for NB03 question generation.
**Where to fix**: NB01 extraction should parse structured budget: `{base: 200000, stretch: true}`.
**Priority**: Low — current behavior correct, loses signal.

---

## NB03 Handoff Notes

NB03 (Session Strategy + Prompt Bundle) receives the DecisionResult from NB02 and should:

1. **Detect ambiguous values** — If destination contains "or" / "maybe", ask for clarification even if NB02 said PROCEED
2. **Handle urgency** — If dates within 7 days, suppress soft blocker questions
3. **Parse budget stretch** — Extract base vs stretch signal for better question generation
4. **Flag traveler-type risks** — Elderly + medical, toddler + pacing, corporate + logistics — these are NOT MVB blockers but should be in session strategy risk flags

See `notebooks/scenario_analysis.md` for the full first-principles analysis that produced these findings.
