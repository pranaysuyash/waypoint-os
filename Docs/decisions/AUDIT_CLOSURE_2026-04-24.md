# Audit Closure Report — 2026-04-24

**Date**: 2026-04-24  
**Auditor**: AI assistant (automated static review)  
**Scope**: `src/intake/decision.py`, `src/intake/strategy.py`, `spine_api/server.py`, `src/decision/rules/budget_feasibility.py`, `src/services/dashboard_aggregator.py`, `src/decision/hybrid_engine.py`  
**Status**: Audit closure complete

---

## 1) Verified Findings

### P0-2: Import Fragility

**File**: `src/intake/decision.py:44`  
**Status**: Fixed  
**Detail**: Changed bare `from decision import create_hybrid_engine` to `from src.decision.hybrid_engine import create_hybrid_engine`.  
**Remaining issues**: Bare `from decision` imports existed in `src/decision/hybrid_engine.py` and `src/services/dashboard_aggregator.py`. These have also been corrected.

### P1-3: `internal_notes` Leakage on Traveler-Safe Bundle

**File**: `src/intake/strategy.py:938`  
**Status**: Fixed  
**Detail**: `to_traveler_dict()` correctly excluded `internal_notes`, but `spine_api/server.py:355` (now `serialize_bundle`) called `_to_dict()` which read `__dict__` and included `internal_notes`. Added `to_traveler_dict()` precedence in `serialize_bundle()` when `traveler_safe=True`.

### P2-5: Duplicate `BUDGET_FEASIBILITY_TABLE`

**Files**: `src/intake/decision.py:503` and `src/decision/rules/budget_feasibility.py:17`  
**Status**: Fixed  
**Detail**: Removed the table from `src/intake/decision.py`. Now imports from canonical source `src.decision.rules`. This prevents silent divergence.

---

## 2) Changes Made

| File | Change | Lines |
|---|---|---|
| `spine_api/server.py` | `serialize_bundle()` now prefers `to_traveler_dict()` for traveler-safe bundles | 355–361 |
| `src/decision/hybrid_engine.py` | Fixed bare `from decision` imports to `from src.decision` | 243, 250, 258, 685 |
| `src/services/dashboard_aggregator.py` | Removed `sys.path` fallback; uses clean absolute import | 25–35, 106–113 |
| `src/intake/decision.py` | Removed duplicate `BUDGET_FEASIBILITY_TABLE`; imports from `src.decision.rules` | 499–506 |
| `src/decision/rules/__init__.py` | Exported `BUDGET_FEASIBILITY_TABLE` for canonical import | 12, 26 |
| `tests/test_audit_closure_2026_04_24.py` | New regression tests for serialization safety and table deduplication | New file |
| `tests/test_spine_api_contract.py` | Added assertion: `traveler_bundle` must not contain `internal_notes` | 237–239 |

---

## 3) Test Results

- **Regression tests**: 6 new tests added (`test_audit_closure_2026_04_24.py`), all passing.
- **Full backend suite**: 685 passed, 13 skipped, 0 failed, 0 errors.
- **Coverage**: All modified code paths exercised by existing + new tests.

---

## 4) Remaining Risks

- **P0-1**: `PROJECT_ROOT` NameError in `spine_api/server.py:259` — Not addressed in this closure. Will be handled separately if still present.
- **P1-1**: Duplicate `_PAST_TRIP_INDICATORS` in `src/intake/extractors.py` — Not addressed in this closure.
- **P1-2**: Dead code in `generate_risk_flags` — Already handled in previous session.
- **P1-4**: Race condition in persistence stores — Not addressed; requires concurrency audit.
- **P2-P5**: Various code quality items — Not part of this closure scope.
- **P2-3**: Import fragility in `spine_api/server.py` — Partially mitigated by `dashboard_aggregator.py` cleanup, but server startup path still relies on `sys.path` manipulation.

---

## 5) Recommended Next Steps

1. **Backend output contract stabilization** — Freeze `run_gap_and_decision` return shape.
2. **Frontend suitability panel** — Surface backend suitability output to operators (after contract is stable).
3. **Tier 3 LLM scorer** — Deferred until real borderline/override cases are observed.
4. **Full Agency Suite** — Treat as roadmap; do not implement until core is hardened.

---

*Checklist applied: AGENTS.md 11-dimension audit / Fix & Verify / Review & Iterate discipline.*
