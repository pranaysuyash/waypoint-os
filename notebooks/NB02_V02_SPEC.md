# Notebook 02 v0.2: Gap and Decision — Agency Judgment Engine

**Date**: 2026-04-12
**Co-locked with**: `specs/canonical_packet.schema.json` v0.2, NB03 v0.2 contract
**Input**: `CanonicalPacket` v0.2 from NB01
**Output**: `DecisionResult` — the judgment layer for NB03

---

## Purpose

NB02 answers: **"Given what we know (and don't know), and given the context we're in, what should we do next?"**

It is the agency judgment engine. It does NOT:
- Extract facts from raw text (NB01)
- Generate prompts or session strategy (NB03)
- Execute external lookups (pricing, suppliers, Timatic)
- Run the conversation loop

---

## Input Contract

NB02 receives:

| Field | Type | Source | v0.2 Changes |
|-------|------|--------|-------------|
| `packet` | CanonicalPacket v0.2 | NB01 | — |
| `current_stage` | str | NB01 (`packet.stage`) | — |
| `operating_mode` | str | NB01 (`packet.operating_mode`) | **New** — top-level, not in facts |
| `mvb_config` | dict | Internal config | Updated field names below |
| `budget_feasibility_table` | dict | External (stub for now) | **New** — min-cost per destination tier |

### Legacy Alias Layer (NB02 only)

For backward compatibility with existing fixtures:

```python
LEGACY_ALIASES = {
    "destination_city": "destination_candidates",
    "travel_dates": "date_window",
    "budget_range": "budget_min",       # was "budget_total" — now maps to numeric
    "traveler_count": "party_size",
    "traveler_details": "passport_status",
    "traveler_preferences": "soft_preferences",
}
```

> **Correction from v0.1 draft**: `budget_range` → `budget_min` (not `budget_total`, which no longer exists). The alias points to the numeric field NB02 actually uses for feasibility logic.

---

## Output Contract: DecisionResult

```python
@dataclass
class DecisionResult:
    packet_id: str
    current_stage: str                           # discovery | shortlist | proposal | booking
    operating_mode: str                          # normal_intake | audit | emergency | ...
    decision_state: str                          # ASK_FOLLOWUP | PROCEED_INTERNAL_DRAFT | ...
    hard_blockers: List[str]                     # Required fields missing/ambiguous/contradictory
    soft_blockers: List[str]                     # Fields that could be inferred or deferred
    ambiguities: List[AmbiguityRef]              # New: filled-but-unresolved fields
    contradictions: List[dict]                   # Active conflicts
    follow_up_questions: List[dict]              # Ordered questions
    branch_options: List[dict]                   # Alternative paths
    rationale: dict                              # Why this decision
    confidence: ConfidenceScorecard               # Multi-axis scorecard (D1)
    risk_flags: List[dict]                       # Computed risks (suitability, documents, etc.)
```

@dataclass
class ConfidenceScorecard:
    data_quality: float          # [0.0-1.0] Field presence + authority check
    judgment_confidence: float   # [0.0-1.0] Contradiction + ambiguity severity
    commercial_confidence: float # [0.0-1.0] Budget feasibility check
    overall: float               # Weighted average for gating

@dataclass
class AmbiguityRef:
    field_name: str
    ambiguity_type: str          # matches packet.ambiguities[].ambiguity_type
    raw_value: str
    severity: str                # "blocking" | "advisory"
```

---

## MVB (Minimum Viable Blockers) v0.2

### Discovery Stage

```python
DISCOVERY_HARD_BLOCKERS = [
    "destination_candidates",    # Where? (may be a list — that's okay)
    "origin_city",               # From where?
    "date_window",               # When? (raw text accepted at discovery)
    "party_size",                # How many?
]

DISCOVERY_SOFT_BLOCKERS = [
    "budget_raw_text",           # Can infer from context
    "budget_min",                # Numeric preferred but not blocking at discovery
    "trip_purpose",              # Can infer or ask
    "soft_preferences",          # Can refine later
]
```

### Shortlist Stage

```python
SHORTLIST_HARD_BLOCKERS = DISCOVERY_HARD_BLOCKERS + [
    "destination_candidates",    # Must exist
]
# Note: At shortlist, destination_candidates should have been narrowed.
# If still "open" or "undecided", this becomes a hard blocker.

SHORTLIST_SOFT_BLOCKERS = [
    "budget_min",                # Numeric budget preferred for sourcing
    "trip_style",                # Helps rank options
]
```

### Proposal Stage

```python
PROPOSAL_HARD_BLOCKERS = SHORTLIST_HARD_BLOCKERS + [
    "selected_itinerary",        # Chosen from shortlist
]

PROPOSAL_SOFT_BLOCKERS = [
    "special_requests",
    "dietary_restrictions",
]
```

### Booking Stage

```python
BOOKING_HARD_BLOCKERS = PROPOSAL_HARD_BLOCKERS + [
    "passport_status",           # Per-traveler document status
    "visa_status",               # Visa requirements met
    "traveler_details",          # Names, DOB (legacy compat)
    "payment_method",
]

BOOKING_SOFT_BLOCKERS = []
```

---

## Decision Logic v0.2

### Phase 1: Operating Mode Routing

The `operating_mode` determines which judgment rules apply:

| Mode | Effect on Decision Logic |
|------|------------------------|
| `normal_intake` | Standard MVB + contradiction + feasibility checks |
| `audit` | Add `value_gap` check; flag self-booked vs agency-fit mismatches |
| `emergency` | Suppress all soft blockers; prioritize document/timeline checks; if critical contradiction → STOP_NEEDS_REVIEW with emergency_options |
| `follow_up` | Check response gap (days since last contact); if no response > 72h → LEAD_FOLLOWUP (via branch) |
| `cancellation` | Run policy engine: refund eligibility, insurance check, alternative paths |
| `post_trip` | Skip blocker logic; generate review/feedback strategy |
| `coordinator_group` | Run per-sub-group blocker checks; aggregate readiness |
| `owner_review` | Run commercial/suitability audit; flag margin risks |

### Phase 2: Ambiguity-Aware Blocker Evaluation

```python
def field_fills_blocker(field_name: str, slot: Slot, ambiguities: List[Ambiguity]) -> bool:
    """
    A field fills a blocker ONLY if:
    1. It exists as a fact or derived_signal
    2. It has fact-level authority (manual_override, explicit_user, imported_structured, explicit_owner, derived_signal)
    3. It is NOT ambiguous with "blocking" severity
    
    Ambiguities with "advisory" severity do NOT block.
    Ambiguities with "blocking" severity DO block.
    """
    if not slot or slot.value is None:
        return False
    if not is_fact(slot.authority_level) and slot.authority_level != "derived_signal":
        return False
    # Check for blocking ambiguities
    for amb in ambiguities:
        if amb.field_name == field_name and amb.severity == "blocking":
            return False
    return True
```

**Ambiguity severity rules**:
| Ambiguity Type | Severity | Rationale |
|---------------|----------|-----------|
| `unresolved_alternatives` on destination | **blocking** | Cannot source without resolved destination |
| `destination_open` | **blocking** | "somewhere with beaches" is too vague |
| `value_vague` on party_size | **blocking** | "big family" — need actual count |
| `composition_unclear` | **advisory** | Can proceed with estimate, refine later |
| `budget_stretch_present` | **advisory** | Budget exists, stretch is extra signal |
| `budget_unclear_scope` | **advisory** | Budget exists, scope can be clarified |
| `date_window_only` | **advisory** | Window is enough for discovery |

### Phase 3: Urgency-Aware Blocker Suppression

```python
def apply_urgency(urgency: str, soft_blockers: List[str]) -> List[str]:
    """
    If urgency is "high" (travel < 7 days), suppress low-value soft blockers.
    If urgency is "medium" (< 21 days), downgrade soft blockers to advisory.
    """
    if urgency == "high":
        # Suppress everything except budget confirmation
        return [b for b in soft_blockers if b in ("budget_min",)]
    elif urgency == "medium":
        # All soft blockers become advisory (do not block PROCEED_TRAVELER_SAFE)
        return []
    return soft_blockers
```

### Phase 4: Budget Feasibility Enforcement

```python
def check_budget_feasibility(packet: CanonicalPacket, feasibility_table: dict) -> Dict:
    """
    Compare stated budget against minimum viable cost for destination + party.
    Returns: {"status": "feasible"|"tight"|"infeasible"|"unknown", "gap": int|None}
    """
    budget_min = get_numeric_budget(packet)  # from budget_min fact
    if budget_min is None:
        return {"status": "unknown", "gap": None}

    dest_candidates = packet.facts.get("destination_candidates", {}).value
    if not dest_candidates:
        return {"status": "unknown", "gap": None}

    party_size = packet.facts.get("party_size", {}).value
    if not party_size:
        return {"status": "unknown", "gap": None}

    # Lookup minimum cost (stub — will use real table later)
    min_per_person = feasibility_table.get(dest_candidates[0], {}).get("min_per_person", 0)
    estimated_minimum = min_per_person * party_size

    gap = budget_min - estimated_minimum
    if gap < -0.3 * estimated_minimum:  # >30% under budget
        return {"status": "infeasible", "gap": gap}
    elif gap < 0:
        return {"status": "tight", "gap": gap}
    return {"status": "feasible", "gap": gap}
```

If feasibility returns `"infeasible"`:
- Add `budget_feasibility` to hard_blockers
- Add contradiction: `budget_range` vs `estimated_minimum_cost`
- Decision: `ASK_FOLLOWUP` (not STOP — still solvable with alternatives)

### Phase 5: Contradiction Classification

```python
CONTRADICTION_ACTIONS = {
    "date_conflict":        {"decision": "STOP_NEEDS_REVIEW",  "priority": "critical"},
    "destination_conflict": {"decision": "ASK_FOLLOWUP",       "priority": "critical"},
    "budget_conflict":      {"decision": "BRANCH_OPTIONS",     "priority": "medium"},
    "budget_feasibility":   {"decision": "ASK_FOLLOWUP",       "priority": "critical"},
    "party_conflict":       {"decision": "ASK_FOLLOWUP",       "priority": "high"},
    "origin_conflict":      {"decision": "ASK_FOLLOWUP",       "priority": "high"},
}
```

### Phase 6: Decision State Machine

```
1. Classify operating_mode → apply mode-specific rules
2. Check ambiguities → mark blocking vs advisory
3. Apply urgency → suppress soft blockers if high
4. Check budget feasibility → hard blocker if infeasible
5. Check hard blockers (MVB for stage)
6. Check soft blockers (MVB for stage, after urgency suppression)
7. Check contradictions → classify per policy
8. Compute confidence
9. Determine decision_state:
   a. Critical contradiction → STOP_NEEDS_REVIEW
   b. Hard blockers exist → ASK_FOLLOWUP
   c. Budget infeasible → ASK_FOLLOWUP
   d. Multiple valid paths → BRANCH_OPTIONS
   e. All blockers filled + no blocking ambiguities → PROCEED_TRAVELER_SAFE
   f. Soft blockers only → PROCEED_INTERNAL_DRAFT
10. Generate follow_up_questions (ordered by constraint-first rule)
11. Compute risk_flags (composition, document, sourcing, urgency)
12. Return DecisionResult
```

---

## Invariants (Hard Assertions)

These must NEVER be violated:

1. **Decision state is determined by blockers/contradictions/feasibility/mode, never by confidence alone**
2. **Traveler-safe can never proceed if blocking ambiguities remain unresolved**
3. **Hypotheses never fill hard blockers** — only facts and derived_signals
4. **Derived signals can influence routing but never silently override explicit facts**
5. **`operating_mode` affects which blockers matter but never removes hard blockers**
6. **Budget feasibility infeasible → always ASK_FOLLOWUP or STOP, never PROCEED_TRAVELER_SAFE**

---

## Risk Flags Computed by NB02

| Risk Flag | Computed From | Severity |
|-----------|--------------|----------|
| `composition_risk` | `party_composition` + `destination_candidates` + `date_window` | advisory |
| `document_risk` | `passport_status` + `visa_status` + `date_end` | critical if booking stage |
| `margin_risk` | `budget_min` vs `estimated_minimum_cost` | advisory |
| `urgency` | `date_end` parsed → days until travel | advisory/medium/high |
| `coordination_risk` | `sub_groups` + per-group budget/payment spread | advisory |
| `traveler_safe_leakage_risk` | hypotheses + contradictions + internal_data_present | critical |

---

## Known Limitations Resolved in v0.2

| v0.1 Limitation | v0.2 Resolution |
|-----------------|-----------------|
| Ambiguous values not detected | Phase 2: ambiguity-aware blocker evaluation |
| No urgency handling | Phase 3: urgency-aware soft blocker suppression |
| Budget stretch not structured | Phase 4: numeric budget feasibility enforcement |
| Sourcing path not computed | Derived signal `sourcing_path` from destination + budget + owner context |
| Suitability not computed | Risk flag `composition_risk` from party composition + destination |
| Visa/passport not modeled | Booking-stage hard blockers: `passport_status`, `visa_status` |
| No operating mode | Top-level `operating_mode` routes to mode-specific judgment |

---

## Legacy Compatibility

NB02 accepts both v0.1 and v0.2 field names via `LEGACY_ALIASES`. NB01 emits v0.2 names only. This compatibility layer will be removed after all fixtures migrate.

```python
def normalize_fields(facts: dict) -> dict:
    """Apply legacy aliases so NB02 logic works with either vocabulary."""
    normalized = {}
    for key, value in facts.items():
        canonical = LEGACY_ALIASES.get(key, key)
        normalized[canonical] = value
    return normalized
```
