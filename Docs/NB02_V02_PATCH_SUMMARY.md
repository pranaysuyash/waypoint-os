# NB02 v0.2 Patch Summary

**Date**: 2026-04-12
**Tests**: 41/41 passed (22 NB01 + 19 NB02)
**Status**: PATCH COMPLETE — honest enough to proceed to NB03

---

## Changed Files

### Modified (2)
| File | Changes |
|------|---------|
| `src/intake/decision.py` | 3 fixes: stage semantics, feasibility under ambiguity, leakage risk |
| `tests/test_nb02_v02.py` | 19 tests (up from 14) — all strengthened, new tests added |

---

## Exact Decision Logic Changes

### Fix 1: Stage semantics — `resolved_destination` in downstream stages

**MVB_BY_STAGE updated:**

| Stage | Before | After |
|-------|--------|-------|
| Discovery | `destination_candidates` | `destination_candidates` (unchanged) |
| Shortlist | `destination_candidates` (duplicate) | `destination_candidates` + `resolved_destination` |
| Proposal | `destination_candidates` | `resolved_destination` only |
| Booking | `destination_candidates` | `resolved_destination` only |

Discovery uses plural candidates. Shortlist requires both candidates AND a resolved single target. Proposal and booking require only the resolved target — no more relying on unresolved candidate lists.

### Fix 3: Feasibility conservative under unresolved destination

`check_budget_feasibility()` now:
1. Checks `resolved_destination` first — if present, uses it
2. Falls back to `destination_candidates` only if no resolved destination
3. If multiple candidates exist → returns `"unknown"` with reason `"Destination unresolved — feasibility cannot be determined"`
4. Never guesses from the first candidate when destination is ambiguous

### Fix 4: Leakage risk includes ambiguities and internal-only owner fields

`generate_risk_flags()` now triggers `traveler_safe_leakage_risk` when ANY of:
- Hypotheses present
- Contradictions present
- Blocking ambiguities (`unresolved_alternatives`, `destination_open`, `value_vague`)
- Internal-only owner constraints (`visibility="internal_only"`)

Reports specific reasons in the message: `"Internal data present (3 hypotheses, blocking ambiguities, internal-only owner constraints) — ensure traveler-safe boundary"`

---

## Exact Test Additions (5 new tests)

| # | Test | What It Proves |
|---|------|---------------|
| 13a | Shortlist without resolved_destination blocks | `resolved_destination` is a hard blocker in shortlist stage |
| 13b | Shortlist with resolved_destination proceeds | Having `resolved_destination` removes it from blockers |
| 14 | Stage progression (discovery→shortlist→proposal→booking) | Proves engine changes behavior by stage: shortlist blocks without resolved, proposal blocks without itinerary, booking blocks without docs/payment |
| 15a | Multi-candidate destination → unknown feasibility | Feasibility stays conservative when destination is unresolved |
| 15b | Resolved destination enables feasibility | Feasibility computed when single destination is resolved |

### Tests strengthened (existing tests tightened):
- **Urgency suppression**: Now explicitly checks that `trip_purpose` and `soft_preferences` are NOT in soft_blockers under high urgency
- **Infeasible budget**: Now requires `"infeasible"` or `"tight"` (not `"unknown"` fallback)
- **Audit mode**: Now checks that audit adds `budget_feasibility` contradiction when feasibility is infeasible/tight
- **Coordinator group**: Now checks subgroup extraction alongside mode detection

---

## NB01 Patches Required

**None.** No changes to NB01 were needed for NB02 integration.

---

## Remaining Stubbed Logic

| Signal/Feature | Maturity | Why Stubbed |
|----------------|----------|-------------|
| `sourcing_path` | stub | No real supplier/internal package database |
| `estimated_minimum_cost` | heuristic | Coarse per-destination min-cost table |
| `budget_feasibility` | heuristic | Depends on estimated_minimum_cost |
| `preferred_supplier_available` | not yet computed | Needs supplier database |
| `booking_readiness` | not yet computed | Composite of docs + payment + supplier |
| `composition_risk` | partial | Has elderly/toddler detection, missing full suitability rules |
| `document_risk` | partial | Has booking-stage checks, missing Timatic |
| `operational_complexity` | not yet computed | Needs multi-stop heuristics |
| `value_gap` | not yet computed | Depends on estimated_minimum_cost |
| Per-group readiness | not yet computed | Sub-group structure exists, readiness check not implemented |

All stubbed. All tagged. None treated as authoritative.

---

## Self-Review

### Did I use the real NB01 packet?
**Yes.** All 19 NB02 tests exercise `ExtractionPipeline().extract() → run_gap_and_decision()`. The stage progression test constructs packets manually but only to test stage-specific blocker logic — which is the correct approach for testing downstream stages that NB01 hasn't reached yet.

### Did I keep the decision logic honest under weak signals?
**Yes.**
- Feasibility returns `"unknown"` under multi-candidate destination (not guessing)
- Stub `sourcing_path` doesn't affect routing
- Blocking ambiguities prevent PROCEED_TRAVELER_SAFE (invariant enforced + tested)
- Infeasible budget never produces PROCEED_TRAVELER_SAFE (invariant enforced + tested)
- Hypotheses never fill hard blockers (authority check in `field_fills_blocker`)
- Shortlist/proposal/booking require `resolved_destination` — not just candidate lists

### Did I accidentally let notebook code diverge from shared modules?
**No.** The notebook is thin import/demo wrapper. Zero embedded logic.

### Did I create any fake-green path to PROCEED_TRAVELER_SAFE?
**No.** The stage progression test proves that each stage has its own blocker requirements and the engine correctly blocks/advances. The decision state machine enforces the full chain.

---

## Verdict: Honest enough to proceed to NB03

The NB02 decision engine is honest. Key improvements from the patch:

1. **Stage semantics fixed**: Downstream stages (shortlist/proposal/booking) require `resolved_destination` — no more relying on unresolved candidate lists
2. **Feasibility conservative**: Multi-candidate destination → `"unknown"` feasibility — no guessing from first candidate
3. **Leakage risk comprehensive**: Triggers on hypotheses, contradictions, blocking ambiguities, AND internal-only owner constraints
4. **Tests strengthened**: 19 tests (up from 14) — urgency suppression explicitly checks remaining blockers, infeasible budget must be truly infeasible, stage progression proves per-stage behavior, feasibility under ambiguity is tested directly

Ready for NB03 v0.2 implementation.
