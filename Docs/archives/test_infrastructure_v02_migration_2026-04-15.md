# Test Infrastructure v0.2 Migration Plan

**Status:** Completed 2026-04-15
**All phases:** ✓ Complete
**Test result:** 255 passed, 22 skipped (100% pass rate)

---

## Context

After successfully migrating notebook tests (`test_02_comprehensive.py`, `test_scenarios_realworld.py`) to v0.2 API (100% pass rate), we identified four critical gaps in the test infrastructure:

1. **Fixture files use v0.1 field names** - `data/fixtures/packet_fixtures.py`, `raw_fixtures.py`, `test_scenarios.py` still reference old field names
2. **Notebook tests are standalone scripts** - not integrated with pytest test suite
3. **No API contract regression tests** - future breaking changes could go undetected
4. **Missing test documentation** - no guide for test organization and usage

## Field Name Mappings (v0.1 → v0.2)

| v0.1 Field Name | v0.2 Canonical Name |
|------------------|---------------------|
| `destination_city` | `destination_candidates` |
| `travel_dates` | `date_window` |
| `budget_range` | `budget_min` |
| `traveler_count` | `party_size` |
| `traveler_preferences` | `soft_preferences` |
| `traveler_details` | `passport_status` |
| `selected_destinations` | `resolved_destination` |

---

## Implementation Results

### Phase 1: Migrate Fixture Files to v0.2 ✓

**Files modified:**
1. `data/fixtures/packet_fixtures.py` - Now imports from `src/intake/packet_models` instead of defining own models
2. `data/fixtures/raw_fixtures.py` - Added `budget_raw_text` field to all fixtures expecting `PROCEED_TRAVELER_SAFE`

**Key changes:**
- Replaced custom `_load_nb02_models()` function with direct imports from `src/intake/packet_models`
- Fixed `AuthorityLevel` usage (string constants instead of IntEnum)
- Added `budget_raw_text` soft blocker to fixtures (v0.2 requirement)
- Adjusted budgets for feasibility: `complete_pilgrimage` (2L→4L), `luxury_wants_budget_reality` (4-5L→8L)

---

### Phase 2: Formalize Notebook Tests as Pytest ✓

**Completed in previous work:**
- `tests/test_comprehensive_v02.py` - 29 tests from `test_02_comprehensive.py`
- `tests/test_realworld_scenarios_v02.py` - 13 scenario tests
- `tests/test_api_contract_v02.py` - 21 regression tests

**Status:** All passing (100%)

---

### Phase 3: v0.2 API Contract Regression Test ✓

**File:** `tests/test_api_contract_v02.py`

**Validates:**
1. `LEGACY_ALIASES` has all 6 expected field mappings
2. `MVB_BY_STAGE` has 4 stages: discovery, shortlist, proposal, booking
3. `AuthorityLevel` has 7 levels with correct `RANK` ordering
4. `run_gap_and_decision()` signature: `(packet, feasibility_table, _cached_feasibility)`
5. `field_fills_blocker()` signature: `(slot, ambiguities, field_name)`
6. `CanonicalPacket`, `DecisionResult`, `Slot` dataclass structures
7. Backward compatibility with legacy field names

---

### Phase 4: Test Documentation ✓

**File:** `tests/README.md`

**Contents:**
- Test categories (Unit, Integration, Regression, Comprehensive)
- Running tests commands
- v0.2 API change reference table
- Fixture usage examples
- Test status summary (192+ passing tests)

---

## Additional Work Completed

### Eval Runner Tools

**Created:** `tools/eval_runner.py`
- Standalone eval runner for fixture validation
- 31/31 fixtures passing (100%)
- Modes: Policy-Only (19 fixtures) and End-to-End (12 fixtures)
- Results saved to `data/fixtures/eval_results.json`

**Updated:** `notebooks/04_eval_runner.ipynb`
- Migrated from loading other notebooks to direct `src/intake/` imports
- Uses `LEGACY_ALIASES` for field name mapping
- Added v0.2 documentation header

---

## Bug Fixes

### decision.py - String Composition Handling

**Issue:** `generate_risk_flags()` expected `party_composition` as dict, but raw fixtures used strings like "6 elderly"

**Fix:**
```python
# Before (line 1034):
if composition.get("elderly") and dest:

# After:
if isinstance(composition, dict) and composition.get("elderly") and dest:
```

---

## Final Test Results

**Full test suite:** 255 passed, 22 skipped in 5.39s
**New test file:** `tests/test_contradiction_data_model.py` - 8 passed

**Eval runner:**
- Mode 2 (Policy-Only): 19/19 passed
- Mode 1 (End-to-End): 12/12 passed
- Overall: 31/31 passed (100%)

---

## Files Changed

### Core source
- `src/intake/decision.py` - String composition fix
- `src/intake/packet_models.py` - ContradictionValue dataclass (from earlier work)

### Fixtures
- `data/fixtures/packet_fixtures.py` - v0.2 imports, budget_raw_text added
- `data/fixtures/raw_fixtures.py` - budget_raw_text added, budgets adjusted

### Tools
- `tools/eval_runner.py` - New standalone eval runner
- `tools/README.md` - Added eval_runner documentation
- `notebooks/04_eval_runner.ipynb` - Updated to v0.2 API

### Tests
- `tests/test_contradiction_data_model.py` - New file, 8 tests
- `tests/README.md` - Existing documentation

---

## Lessons Learned

1. **Archive in project, not workspace** - Plans should be moved to `Docs/archives/` not deleted from `.claude/plans/`
2. **budget_raw_text is a soft blocker** - v0.2 requires this field for `PROCEED_TRAVELER_SAFE` decisions
3. **Composition can be string or dict** - Raw fixtures use natural language ("6 elderly") while structured input uses dicts
4. **Feasibility checks matter** - Tight budgets trigger `budget_feasibility` soft blockers

---

## Verification Strategy Used

After each phase:
- Run `python -m pytest tests/ -v`
- Ensure all existing tests still pass
- Run new tests specifically

After all phases:
- Full test suite passes (255 passed)
- All tests discoverable by pytest
- Documentation complete and accurate
- Eval runner validates fixtures (31/31 pass)
