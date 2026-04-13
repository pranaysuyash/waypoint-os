# NB01 v0.2 Patch Implementation Summary

**Date**: 2026-04-12
**Tests**: 22/22 passed
**Status**: PATCH COMPLETE — honest enough to proceed to NB02

---

## Fixes Applied (All 7)

### Fix 1: Schema drift resolved
- Added `maturity` field to `FieldSlot` in `specs/canonical_packet.schema.json`
- Enum: `stub | heuristic | verified` (nullable)
- Python model and schema now aligned

### Fix 2: Validation made truthful
- Rewrote `src/intake/validation.py` with `ValidationIssue` severity classes
- `is_valid` is now `False` for structural errors:
  - derived-only field in facts
  - fact with non-fact authority
  - derived signal with wrong authority
  - missing/invalid maturity on derived signals
  - legacy v0.1 field names
- Warnings remain informational (low confidence facts, high ambiguity count, many stubs)

### Fix 3: Package path corrected
- Renamed `src/travel_agent/` → `src/intake/`
- Updated all imports in tests, notebook, and __init__.py
- Package name aligns with NB01's role (intake & normalization)

### Fix 4: Regex correctness fixed
- All `[-–—to]+` character class misuse replaced with `(?:-|–|—|\bto\b)` alternation
- Applied in both normalizer.py and extractors.py
- 0 remaining character class misuse patterns

### Fix 5: Tests strengthened
- Removed all conditional assertions ("if present" style)
- Owner constraint scenarios now mandatory
- Urgency scenarios now mandatory
- Added schema roundtrip test (extract → serialize → validate)
- Updated all test assertions for new validation API

### Fix 6: Structured field drift patched
- `passport_status` now extracts as per-traveler structured map
- Format: `{"all": {"status": "expired", "expired_date": "Jan 2025"}}`
- Per-traveler extraction: `{"adult_1": {"status": "valid", "valid_until": "March 2029"}}`

### Fix 7: Notebook discipline maintained
- All 6 code cells verified: no embedded class/function definitions
- Imports from `intake.*` modules
- Notebook is purely import + demo wrapper

---

## Changed Files

### New (0) — all files existed from previous round
### Modified (6)

| File | Changes |
|------|---------|
| `specs/canonical_packet.schema.json` | Added `maturity` to FieldSlot |
| `src/intake/validation.py` | Complete rewrite with severity classes |
| `src/intake/extractors.py` | Regex fixes, Andaman→DOMESTIC, passport_status structured |
| `src/intake/normalizer.py` | Regex fixes |
| `tests/test_nb01_v02.py` | Removed conditionals, added roundtrip test, fixed imports |
| `notebooks/01_intake_and_normalization.ipynb` | Updated imports, verified thin wrapper |

---

## Test Results

| Metric | Value |
|--------|-------|
| Total tests | 22 |
| Passed | 22 |
| Failed | 0 |
| Time | 0.13s |

### Test Coverage Map

| # | Test | What It Proves |
|---|------|---------------|
| 1 | Freeform + ambiguity | "Andaman or Sri Lanka" → candidates list + ambiguity detected |
| 2 | Structured budget | "4-5L" → `budget_min=400000`, `budget_max=500000` |
| 3 | Structured dates | ISO range → `date_start`, `date_end`, `date_confidence="exact"` |
| 4 | Party composition | Full composition dict + `child_ages=[8,12]` |
| 5 | Owner constraints (internal) | "never book X" → `OwnerConstraint(visibility="internal_only")` |
| 6 | Owner constraints (transformable) | "prefers X" → `visibility="traveler_safe_transformable"` |
| 7 | Repeat customer split | `customer_id` in facts, `is_repeat_customer` ONLY in derived |
| 8 | Multi-party structure | `SubGroup` objects with typed fields |
| 9 | Emergency mode (top-level) | `packet.operating_mode="emergency"` |
| 10 | Normal intake default | `packet.operating_mode="normal_intake"` |
| 11 | Urgency high | `date_end = today+5d` → `urgency="high"`, `maturity="verified"` |
| 12 | Urgency medium | `date_end = today+14d` → `urgency="medium"` |
| 13 | Schema validation (missing) | Missing MVB → errors reported |
| 14 | Schema validation (valid) | All MVB present → `is_valid=True` |
| 15 | Legacy field rejection | `destination_city` in facts → validation error |
| 16 | Derived-only not in facts | No derived-only field in `packet.facts` |
| 17 | No resolved_destination | NB01 never sets `resolved_destination` |
| 18 | Owner fields with visibility | All constraints have valid `visibility` enum |
| 19 | All derived have maturity | Every derived signal has `maturity ∈ {stub, heuristic, verified}` |
| 20 | Stub signals marked | `sourcing_path.maturity="stub"` |
| 21 | Verified signals marked | `urgency.maturity="verified"` |
| 22 | Schema roundtrip | Extract → serialize → validate: all derived have maturity, no errors |

---

## Remaining Contract Mismatches

| Item | Status | Priority |
|------|--------|----------|
| Schema doesn't strongly-type `owner_constraints` value | Schema says `FieldSlot` (generic), code uses `List[OwnerConstraint]` | Medium — Python type enforces |
| Schema doesn't strongly-type `sub_groups` value | Schema says `FieldSlot`, code uses `Dict[str, SubGroup]` | Medium — Python type enforces |
| Schema doesn't strongly-type `passport_status` value | Schema says `FieldSlot`, code uses `Dict[str, Dict]` | Medium — Python type enforces |
| No JSON schema validator in tests | We validate with our Python layer, not against the JSON schema file itself | Low — can add `jsonschema` package later |

These are acceptable for now. The Python dataclasses enforce the actual shape. The JSON schema serves as the contract document for downstream consumers.

---

## Stubbed Signals (honest)

| Signal | Maturity | Status |
|--------|----------|--------|
| `sourcing_path` | stub | Not yet implemented — no real supplier data |
| `estimated_minimum_cost` | not yet computed | Needs per-destination min-cost table |
| `budget_feasibility` | not yet computed | Depends on estimated_minimum_cost |
| `preferred_supplier_available` | not yet computed | Needs supplier database |
| `booking_readiness` | not yet computed | Composite signal |
| `composition_risk` | not yet computed | Needs suitability rules |
| `document_risk` | not yet computed | Needs Timatic integration |
| `operational_complexity` | not yet computed | Needs difficulty heuristics |
| `value_gap` | not yet computed | Depends on estimated_minimum_cost |

All tagged. None treated as authoritative by NB01 logic.

---

## Self-Review

### Did I implement the contract honestly, or did I create the appearance of capability?

**Mostly honest.** The 22 tests exercise real extraction paths through the pipeline. Every field that's populated comes from regex/pattern parsing. Maturity tags are structural — they're on every derived signal.

### Where appearance exceeded reality:

1. **~47 known destinations** — won't catch "Europe" generically, "Caribbean", or obscure locations. Documented limitation.
2. **INR-only budget parsing** — assumes ₹/L/K. `budget_currency` defaults to "INR" — stub.
3. **Basic owner constraint patterns** — will miss nuanced owner knowledge. Honest extraction, not NLP.
4. **Medical constraint detection** — only matches specific keywords. Won't catch "dad has mobility issues".
5. **Multi-party extraction partial** — only detects rigid "Family A: N people, budget X" patterns.

### What's actually strong:
- Schema/code alignment on `maturity` (was the biggest contract break)
- Validation is now truthful (structural errors → `is_valid=False`)
- Tests don't have conditional assertions anymore
- Passport status is per-traveler structured
- No v0.1 field names emitted
- No embedded logic in notebook

### Verdict: Honest enough to proceed to NB02

The remaining gaps are extraction coverage limitations (which need better patterns/LLM), not contract dishonesty. The NB02 spec can be implemented against the current contract with confidence.
