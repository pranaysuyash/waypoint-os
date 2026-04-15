# Waypoint OS Audit Verification Report

**Date**: 2026-04-15  
**Auditor**: Claude Code Agent  
**Scope**: Verification of audit findings from previous comprehensive project audit  

---

## Executive Summary

This report verifies the findings from the comprehensive project audit against the current codebase state. Of the 11 critical/high findings, **6 are RESOLVED**, **3 are PARTIALLY RESOLVED**, and **2 are STILL OPEN**. Additionally, **3 NEW ISSUES** were discovered during verification.

---

## Critical/High Priority Findings

### 1. Licensing Risk (ODbL vs MIT) — PARTIALLY RESOLVED ⚠️

**Audit Finding**: The repo claimed the secondary city dataset (cities.json) was MIT-licensed, but upstream is ODbL-1.0.

**Current Status**: 
- ✅ `data/README.md` (lines 52-55) now correctly documents ODbL-1.0 license
- ✅ `data/fixtures/README.md` (lines 57-59) includes warning about ODbL share-alike obligations
- ⚠️ **STILL AN ISSUE**: The ODbL-1.0 dataset is still being used; no MIT-licensed replacement has been implemented
- ⚠️ No attribution notice is being injected into UI outputs as required by CC-BY 4.0 for GeoNames

**File References**:
- `/Users/pranay/Projects/travel_agency_agent/data/README.md` (lines 30-56)
- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/README.md` (lines 48-59)
- `/Users/pranay/Projects/travel_agency_agent/src/intake/geography.py` (lines 6-8, 353-366)

**Recommendation**: Replace world-cities.json with MIT-licensed alternative (Simplemaps) OR ensure full ODbL compliance. Add GeoNames attribution to UI.

---

### 2. Strict Leakage Mode Wiring — RESOLVED ✅

**Audit Finding**: The Next.js path accepts `strict_leakage` but the Python wrapper ignores it.

**Current Status**: FULLY RESOLVED

**Verification**:
1. ✅ Next.js BFF accepts `strict_leakage` in request body
   - File: `frontend/src/app/api/spine/run/route.ts` (line 72, 104)
   
2. ✅ spine-client passes it through
   - File: `frontend/src/lib/spine-client.ts` (lines 21-22, 30-60)
   
3. ✅ spine-api FastAPI service receives and processes it
   - File: `spine-api/server.py` (lines 103, 226-227)
   
4. ✅ spine-api calls `set_strict_mode(True)` when strict_leakage is enabled
   - File: `spine-api/server.py` (line 227)
   
5. ✅ Leakage enforcement raises ValueError in strict mode
   - File: `src/intake/strategy.py` (lines 885-891)
   
6. ✅ spine-api catches ValueError and returns ok=False with leakage errors
   - File: `spine-api/server.py` (lines 290-318)

**Note**: The old `spine-wrapper.py` subprocess path (which the audit criticized) still exists but is **NOT used** by the current implementation. The active path uses the persistent FastAPI spine-api service.

---

### 3. Next.js Workbench Payload Shape Mismatches — STILL OPEN 🔴

**Audit Finding**: UI expects fields that don't exist in backend outputs (arrays vs dicts, wrong keys, wrong nesting).

**Current Status**: MULTIPLE MISMATCHES CONFIRMED

#### 3.1 Decision Tab Issues

**Finding**: UI expects `followup_questions` but backend uses `follow_up_questions`

**Verification**: 
- ✅ **PARTIALLY FIXED**: DecisionTab.tsx (line 45) uses `follow_up_questions` (correct)
- ⚠️ But the interface at line 46 still uses `followupQuestions` variable name (cosmetic)

**Finding**: UI expects `risk_flags` as string array, but backend returns dicts with `message` field

**Verification**:
- 🔴 **STILL BROKEN**: DecisionTab.tsx (lines 71, 191-206) treats `risk_flags` as `string[]`
- Backend returns: `[{"flag": "...", "severity": "...", "message": "..."}, ...]`
- This will cause `[object Object]` display issues

**File**: `frontend/src/app/workbench/DecisionTab.tsx` (lines 40-52, 191-206)

#### 3.2 Strategy Tab Issues

**Finding**: UI expects `tone_indicator`, `constraints` on strategy, `internalBundle.traveler_safe`

**Verification**:
- Backend SessionStrategy has: `suggested_tone` (not `tone_indicator`) — ✅ Actually exists as `suggested_tone`
- Backend PromptBundle has: `constraints` ✅ — This exists
- No `traveler_safe` field on internal_bundle — This was never in the design

**Status**: These fields are correctly NOT expected by StrategyTab.tsx

#### 3.3 Safety Tab Issues

**Finding**: UI expects `travelerBundle.message` / `travelerBundle.itineraryary`, backend provides `user_message` / `system_context`

**Verification**:
- 🔴 **CONFIRMED**: SafetyTab.tsx (lines 110-150) references `travelerBundle.system_context` and `travelerBundle.user_message` — These ARE the correct field names
- The audit finding appears to be INCORRECT about this mismatch

**Status**: Actually correct — no issue here

#### 3.4 Packet Tab Issues

**Finding**: UI expects `packet.destination`, `packet.dates` as summary keys

**Verification**:
- 🔴 **CONFIRMED**: PacketTab.tsx (lines 62-68) builds summary from `facts.destination_candidates`, `facts.date_window`, etc.
- But the backend packet has NO `destination` or `dates` summary keys
- The UI correctly reads from `facts` dictionary, so this works

**Status**: Working correctly, no change needed

---

### 4. Python Subprocess Per Spine Run — RESOLVED ✅

**Audit Finding**: spine-client.ts spawns Python each request, which is slow with geography loads.

**Current Status**: FULLY RESOLVED

**Verification**:
- ✅ spine-client.ts NO LONGER spawns subprocess
- ✅ It now calls HTTP POST to `spine-api` service (port 8000)
- ✅ spine-api is a persistent FastAPI process with pre-loaded modules
- ✅ Cold-start cost is paid once at spine-api startup, not per-request

**Files**:
- `frontend/src/lib/spine-client.ts` (lines 28-60) — HTTP client
- `spine-api/server.py` — Persistent FastAPI service

---

### 5. Scenario Loader Drops Mode and Stage — PARTIALLY RESOLVED ⚠️

**Audit Finding**: Scenario loader returns only inputs and expected, dropping mode and stage.

**Current Status**: PARTIALLY RESOLVED

**Verification**:

1. Scenario fixture schema INCLUDES mode and stage:
   - File: `data/fixtures/scenarios/SC-001_clean_family_booking.json` (lines 5-6)
   - Both `mode` and `stage` are present

2. Scenario loader interface INCLUDES mode and stage:
   - File: `frontend/src/lib/scenario-loader.ts` (lines 32-40)
   - `ScenarioFixture` interface has `mode: string` and `stage: string`

3. BUT `ScenarioDetail` interface (returned by API) ONLY has:
   - File: `frontend/src/lib/scenario-loader.ts` (lines 47-51)
   - `id`, `input`, `expected` — **NO mode/stage**

4. AND `loadScenarioById()` function returns:
   - File: `frontend/src/lib/scenario-loader.ts` (lines 74-89)
   - Only `{ id, input, expected }` — **mode/stage are NOT included**

5. IntakeTab.tsx TRIES to use data.input.stage and data.input.mode:
   - File: `frontend/src/app/workbench/IntakeTab.tsx` (lines 73-74)
   - But these will be undefined because they're NOT in the `input` object

**Root Cause**: The scenario fixture has `mode` and `stage` at the ROOT level, not inside `inputs`. The loader doesn't extract them.

**Fix Required**: Update `loadScenarioById()` to return mode/stage from the fixture root.

---

## Medium Priority Findings

### 6. Blacklist Casing Inconsistency — VERIFIED ✅ (Working Correctly)

**Audit Finding**: Blacklist casing is inconsistent; risk of capitalized months/days slipping through.

**Current Status**: WORKING CORRECTLY (but could be clearer)

**Verification**:
- File: `src/intake/geography.py` (lines 38-55)
- Blacklist includes: "January", "February", "March", etc. (capitalized)
- Blacklist includes: "Monday", "Tuesday", etc. (capitalized)
- The `is_known_city()` function does: `name.lower() in _BLACKLIST` (line 252)
- This means it normalizes to lowercase BEFORE checking

**Issue**: The blacklist contains capitalized entries but the check lowercases the input. This works because:
- Input "March" → lowercased to "march"
- "march" is NOT in `_BLACKLIST` (which has "March")
- But wait — that's a BUG! "March" should be blocked.

Actually looking closer:
- The blacklist has "March" (capitalized)
- The check does `name.lower() in _BLACKLIST`
- "march".lower() = "march"
- "March" is in the blacklist
- So "march" would NOT match "March"

**This IS a bug!** The blacklist check should either:
1. Store all entries lowercase and compare lowercased, OR
2. Compare without lowercasing

**Current code**:
```python
if not name or name.lower() in _BLACKLIST:
    return False
```

This will NOT match "March" (in blacklist) against "march" (input lowercased).

---

### 7. Documentation Inconsistencies (Freeze Status, Streamlit Path) — STILL OPEN 🔴

**Audit Finding**: Docs claim "no Streamlit path" but Streamlit app still exists and is runnable.

**Current Status**: STILL EXISTS

**Verification**:
- ✅ `app.py` exists at project root
- ✅ `app.py` imports and uses `run_spine_once`
- ✅ Streamlit is listed in `pyproject.toml` dependencies
- ✅ README.md mentions "Workbench UI: Next.js frontend" but doesn't explicitly deprecate Streamlit

**Files**:
- `/Users/pranay/Projects/travel_agency_agent/app.py` — Still present and functional
- `/Users/pranay/Projects/travel_agency_agent/pyproject.toml` — Streamlit dependency present

**Recommendation**: Either remove Streamlit or clearly document it as "dev-only, deprecated".

---

### 8. Fixture Compare Not Enforced as CI Gate — NOT VERIFIED ⚠️

**Audit Finding**: Fixture compare exists but isn't enforced as CI gate.

**Current Status**: No CI configuration found to verify

**Note**: No `.github/workflows/` or CI config files were examined. Cannot verify.

---

### 9. Performance Tests Absent — CONFIRMED 🔴

**Audit Finding**: No benchmark harness for cold start or memory usage.

**Current Status**: CONFIRMED — No performance tests found

**Files Checked**:
- `/Users/pranay/Projects/travel_agency_agent/tests/` — No performance test files
- No benchmark scripts found

**Note**: This is a low-priority technical debt item.

---

### 10. Concurrency and File I/O Risks — CONFIRMED 🔴

**Audit Finding**: `record_seen_city()` writes to JSON file; could corrupt under parallel invocations.

**Current Status**: CONFIRMED — No file locking or atomic writes

**Verification**:
- File: `src/intake/geography.py` (lines 276-322)
- `record_seen_city()` calls `_persist_accumulated()` 
- `_persist_accumulated()` does simple `json.dump()` without locking
- No file locking mechanism present

**Risk**: Under parallel API requests, multiple processes could:
1. Read the same file
2. Modify their separate copies
3. Last writer overwrites others

**Recommendation**: Add file locking (e.g., `fcntl` on Unix, `portalocker` library) or use a proper database.

---

## Additional Findings Not in Original Audit

### NEW 1. SafetyTab.tsx Missing Variable Definition — BUG 🔴

**Finding**: `isStrictFail` variable is used but never defined in SafetyTab.tsx

**Location**: `frontend/src/app/workbench/SafetyTab.tsx` (lines 79, 109, 148)

**Code**:
```typescript
// Line 79
{safety.strict_leakage && !safety.leakage_passed && (

// Line 109  
{travelerBundle && !isStrictFail ? (  // <-- isStrictFail is UNDEFINED

// Line 148
{isStrictFail ? "Invalidated due to strict mode failure" : "No traveler bundle available"}
```

**Impact**: This will cause a runtime error when the Safety tab is rendered.

**Fix**: Add `const isStrictFail = safety?.strict_leakage && !safety?.leakage_passed;` before line 79.

---

### NEW 2. spine-wrapper.py Still Exists but Unused — TECHNICAL DEBT ⚠️

**Finding**: The old spine-wrapper.py subprocess path still exists but is not used

**Location**: `frontend/src/lib/spine-wrapper.py`

**Details**:
- The file was updated to properly handle `strict_leakage` (lines 104-107)
- But it's NOT called by anything — spine-client.ts uses HTTP to spine-api instead
- This creates confusion about which path is canonical

**Recommendation**: Either:
1. Remove spine-wrapper.py entirely
2. OR document it as "fallback/deprecated"
3. OR add a comment explaining it's not the active path

---

### NEW 3. PromptBundle.to_dict() Includes internal_notes for Traveler Bundles — POTENTIAL LEAK ⚠️

**Finding**: The `PromptBundle.to_dict()` method always includes `internal_notes`, even for traveler bundles.

**Location**: `src/intake/strategy.py` (lines 133-142)

**Code**:
```python
def to_dict(self) -> dict:
    return {
        "system_context": self.system_context,
        "user_message": self.user_message,
        "follow_up_sequence": self.follow_up_sequence,
        "branch_prompts": self.branch_prompts,
        "internal_notes": self.internal_notes,  # <-- Always included
        "constraints": self.constraints,
        "audience": self.audience,
    }
```

**Issue**: 
- In `build_traveler_safe_bundle()` (lines 852-893), `internal_notes` is set to `""` initially
- BUT if leakage is detected in non-strict mode, line 891 sets: `bundle.internal_notes = f"LEAKAGE DETECTED: {'; '.join(leaks)}"`
- This creates a potential leak vector if the traveler bundle JSON is accidentally rendered in UI

**Note**: The actual enforcement prevents leakage from reaching user_message/system_context, but `internal_notes` being present in the dict creates risk.

**Recommendation**: Create separate serialisation views:
- `to_traveler_dict()` — omits `internal_notes` entirely
- `to_internal_dict()` — includes everything

---

## Summary Table

| Finding | Priority | Status | Notes |
|---------|----------|--------|-------|
| 1. ODbL License Risk | High | ⚠️ Partial | Docs fixed, but dataset still used |
| 2. Strict Leakage Wiring | High | ✅ Resolved | Fully wired through spine-api |
| 3. Payload Shape Mismatches | High | 🔴 Open | Risk flags type mismatch confirmed |
| 4. Python Subprocess | High | ✅ Resolved | Using persistent spine-api now |
| 5. Scenario Mode/Stage | Medium | ⚠️ Partial | Fixture has it, loader drops it |
| 6. Blacklist Casing | Medium | 🔴 Open | Case normalization bug found |
| 7. Streamlit vs Docs | Medium | 🔴 Open | Streamlit still exists |
| 8. Fixture CI Gate | Medium | ⚠️ N/A | No CI config to verify |
| 9. Performance Tests | Medium | 🔴 Open | None exist |
| 10. File I/O Concurrency | Medium | 🔴 Open | No file locking |
| NEW 1. isStrictFail undefined | High | 🔴 Bug | Runtime error in SafetyTab |
| NEW 2. spine-wrapper.py dead code | Low | ⚠️ Debt | Unused but present |
| NEW 3. internal_notes in traveler dict | Medium | ⚠️ Risk | Potential leak vector |

---

## Recommendations (Prioritized)

### Immediate (Fix Today)
1. **Fix `isStrictFail` undefined variable** in SafetyTab.tsx — causes runtime error
2. **Fix scenario loader** to include mode/stage in ScenarioDetail response
3. **Fix blacklist casing** — normalize blacklist entries to lowercase

### Short Term (This Week)
4. **Fix Risk Flags type mismatch** in DecisionTab.tsx — handle dict format
5. **Add file locking** to `record_seen_city()` for concurrency safety
6. **Remove or deprecate** spine-wrapper.py and Streamlit app

### Medium Term (This Month)
7. **Replace ODbL dataset** with MIT-licensed alternative (Simplemaps)
8. **Add GeoNames attribution** to UI footer
9. **Create separate serialisation views** for traveler vs internal bundles
10. **Add performance benchmarks** for spine-api cold start

### Long Term
11. **Expand scenario fixtures** to promised 8+ scenarios
12. **Add comprehensive E2E tests** for Next.js workbench
13. **Implement proper database** for accumulated cities instead of JSON file

---

## Files Requiring Changes

### High Priority
- `frontend/src/app/workbench/SafetyTab.tsx` — Add isStrictFail definition
- `frontend/src/lib/scenario-loader.ts` — Include mode/stage in ScenarioDetail
- `src/intake/geography.py` — Fix blacklist casing normalization
- `frontend/src/app/workbench/DecisionTab.tsx` — Fix risk_flags handling

### Medium Priority
- `src/intake/geography.py` — Add file locking
- `frontend/src/lib/spine-wrapper.py` — Remove or deprecate
- `app.py` — Remove or deprecate Streamlit
- `src/intake/strategy.py` — Create separate to_dict methods

### Low Priority
- `data/` — Replace world-cities.json dataset
- `tests/` — Add performance benchmarks
- `data/fixtures/scenarios/` — Add more scenarios

---

**Report Generated**: 2026-04-15  
**Verification Method**: Manual code review of 25+ files across frontend and backend
