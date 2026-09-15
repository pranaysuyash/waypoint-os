# E-D — Memory Read-Path Slot Spec (2026-09-08)

**Exploration package E-D (PER-0700)** — unblocks PA-18 wiring.
Status update 2026-09-15: **Slot 1 shadow-landed** (`src/memory/slot_candidates.py`,
default `MEMORY_SLOT_READ_MODE=shadow`, promotion-only, audited via
`memory_slot_promotion`; active flip is a deliberate operator act) and
**Slot 2 display-only landed end-to-end** — durable-store facts via
`memory_on_file_facts()` surfaced as "On file from <date>" chips with purge
affordance (`OnFileMemoryCard` on the trip decision page). The invariant
below is unchanged and enforced by import-containment tests: **nothing in
this spec authorizes memory → inventory influence.**

## 1. Problem

The traveler memory graph (`src/memory/`, `customer_memory` router) is write-only: facts are extracted and stored, but no read path consumes them (PA-18). The naive fix — "personalize everything" — is the exact failure the persona doctrine forbids: a stale stored preference ("never morning flights") silently de-scoring live inventory is shadow state with traveler-facing consequences.

## 2. The rule (invariant)

> Memory may rank **questions**. Memory may never select, score, filter, or reorder **inventory, prices, or booking options**.

Corollaries:
1. Memory output is **advisory context**, always labeled `source: memory, observed_at: <ts>`.
2. Stale facts (older than their `freshness horizon`) are dropped, not down-weighted.
3. Every memory-derived influence must be **visible in the decision rationale** ("asked about rail preference because stored note mentioned trains, 2026-08-02").
4. Traveler can inspect and purge; purge propagates (existing erasure prerequisites per X-14).

## 3. The two slots (wiring points)

### Slot 1 — Question generation (R3, deterministic)

**Site:** `src/intake/strategy.py` question-generation, after NB01/NB02 gates produce `unknowns`.

**Contract:** memory supplies *candidate priorities*, never questions directly.

```
input:  unknowns[] (from gates), memory_facts[] (typed, fresh)
output: reordered unknowns[] + rationale tags
rule:   a stored fact may PROMOTE an unknown it would answer
        ("allergic to shellfish" stored → promote "dietary_requirements" unknown)
        a stored fact may NEVER demote or answer an unknown by itself
```

Guard: promotion requires the stored fact to be **topical** (destination-scoped facts don't promote date questions) and **fresh**. The question is still asked — memory only changes its order.

### Slot 2 — FreshnessCard context (R3, display-only)

**Site:** `frontend` FreshnessCard / decision rationale.

**Contract:** memory facts render as "On file from <date>: <fact>" chips with a purge affordance. They never render as confirmed trip data, never enter `packet`, never satisfy a gate.

## 4. Non-slots (explicitly rejected)

- Suitability scoring (PA-36 Tier-3 stays PLANNED; memory would contaminate the deterministic tiers)
- Proposal compile inventory selection (PA-25 — simulated inventory stays order-independent)
- NBTA projection (AT-07 — actions derive from lifecycle + JDG + disruption, not preferences)
- Gate evaluation (NB01/NB02 cannot be satisfied by memory)

## 5. Data contract

```python
@dataclass(slots=True)
class MemorySlotCandidate:
    fact_type: str          # e.g. "preference", "constraint", "context"
    fact_value: str
    observed_at: datetime   # UTC; naive rejected
    freshness_horizon: timedelta  # per fact_type; expired → dropped
    topical_scope: str      # "trip" | "destination:<name>" | "global"
    rationale_tag: str      # rendered in decision rationale
```

Read API: one function, `memory_slot_candidates(agency_id, trip_id, unknowns) -> list[MemorySlotCandidate]`, consumed only by the two slots. No other module may import memory read paths (enforced by review + a lint-style test asserting import containment).

## 6. Sequencing

1. Ship Slot 2 (display-only) behind no flag — zero decision influence.
2. Ship Slot 1 with promotion-only reordering + rationale tags + tests proving: stale fact ignored, non-topical fact ignored, unknown never auto-answered.
3. Purge propagation test (X-14 prerequisite check) before enabling persistence of new fact types.

**Owner gates honored:** memory→inventory stays forbidden; ADR-008 §4.3 slot language matches this spec.
