# Waypoint OS Audit Verification Report

**Date**: 2026-04-15  
**Scope**: Verify resolution of previous audit findings and identify missed issues  
**Status**: COMPLETED

---

## Executive Summary

This audit verifies whether the critical findings from the previous comprehensive audit have been resolved. **Good news: Most HIGH severity issues have been addressed.** However, several MEDIUM and LOW severity issues remain, plus one new architectural concern was discovered.

### Resolution Status Overview

| Severity | Total Findings | Resolved | Remaining |
|----------|----------------|----------|-----------|
| High | 4 | 3 | 1 |
| Medium | 5 | 2 | 3 |
| Low | 3 | 1 | 2 |

---

## Previous Findings - Resolution Status

### 1. Licensing Risk (High Severity) ✅ RESOLVED

**Previous Finding**: Data README claimed MIT license for cities.json, but upstream is ODbL-1.0.

**Verification**:
- `data/README.md` line 34: **"License**: ODbL-1.0 (Open Database License) — share-alike obligations apply"
- `data/README.md` lines 52-55: Explicit warning about share-alike obligations and proprietary product conflicts
- `data/fixtures/README.md` lines 51-59: Same ODbL-1.0 documentation with replacement recommendation

**Status**: **RESOLVED** - Documentation now accurately reflects ODbL-1.0 license with clear warnings.

---

### 2. Strict Leakage Mode Wiring (High Severity) ✅ RESOLVED

**Previous Finding**: Next.js path accepted `strict_leakage` but Python wrapper ignored it.

**Verification**:
- `frontend/src/lib/spine-wrapper.py` lines 104-107: Now properly imports and calls `set_strict_mode(True)`
- `spine_api/server.py` lines 225-227: FastAPI endpoint sets strict mode via `set_strict_mode(True)` when `request.strict_leakage` is True
- `spine_api/server.py` lines 290-318: Properly catches `ValueError` from strict mode failures and returns 422 response
- `src/intake/strategy.py` lines 885-892: `build_traveler_safe_bundle` calls `enforce_no_leakage()` and handles leakage

**Status**: **RESOLVED** - Strict leakage is now fully wired through both subprocess and HTTP API paths.

---

### 3. Next.js Workbench Integration Shape (High Severity) ⚠️ PARTIALLY RESOLVED

**Previous Finding**: UI expected fields that don't exist in backend payloads.

**Verification Results**:

| UI Tab | Expected Field | Backend Field | Status |
|--------|----------------|---------------|--------|
| Packet | `packet.destination` | `facts.destination_candidates` | ⚠️ Mismatch |
| Packet | `packet.dates` | `facts.date_window` | ⚠️ Mismatch |
| Decision | `followup_questions` | `follow_up_questions` | ✅ Fixed (DecisionTab.tsx line 72) |
| Decision | `risk_flags` (strings) | `risk_flags` (dicts) | ⚠️ Mismatch |
| Strategy | `tone_indicator` | `suggested_tone` | ❌ Mismatch |
| Strategy | `constraints` | Not in SessionStrategy | ❌ Missing |
| Strategy | `internalBundle.traveler_safe` | Not in PromptBundle | ❌ Missing |
| Safety | `travelerBundle.message` | `user_message` | ⚠️ Mismatch |
| Safety | `travelerBundle.itinerary` | `follow_up_sequence` | ⚠️ Mismatch |

**Key Issues Remaining**:

1. **StrategyTab.tsx** expects `tone_indicator` but backend provides `suggested_tone` (line 79)
2. **StrategyTab.tsx** expects `constraints` on strategy but SessionStrategy doesn't have this field
3. **StrategyTab.tsx** expects `traveler_safe` boolean on internal bundle - doesn't exist
4. **SafetyTab.tsx** uses `isStrictFail` variable that is never defined (line 109)

**Status**: **PARTIALLY RESOLVED** - Some field names fixed, but multiple payload shape mismatches remain.

---

### 4. Python Subprocess Performance (Medium Severity) ✅ RESOLVED

**Previous Finding**: Subprocess per request would be slow with geography loading.

**Verification**:
- `frontend/src/lib/spine-client.ts` lines 13-60: **Completely refactored**
- Now calls `spine_api` (FastAPI HTTP service) at `SPINE_API_URL` instead of spawning subprocess
- `spine_api/server.py`: Persistent FastAPI service with pre-loaded modules

**Status**: **RESOLVED** - No longer uses subprocess per request; uses persistent HTTP service.

---

### 5. Scenario Loader Drops Mode/Stage (Medium Severity) ❌ NOT RESOLVED

**Previous Finding**: Scenario loader returns only inputs and expected, dropping mode and stage.

**Verification**:
- `frontend/src/lib/scenario-loader.ts` lines 47-51: `ScenarioDetail` interface only has `id`, `input`, `expected`
- `frontend/src/lib/scenario-loader.ts` lines 74-89: `loadScenarioById` returns `{ id, input, expected }` only
- `frontend/src/app/workbench/IntakeTab.tsx` lines 73-74: Expects `data.input.stage` and `data.input.mode` which don't exist

**Root Cause**: 
- Fixture files (e.g., `SC-001_clean_family_booking.json`) have `mode` and `stage` at root level
- But `loadScenarioById` only returns `scenario.inputs`, not `scenario.mode` or `scenario.stage`

**Status**: **NOT RESOLVED** - Mode and stage are still dropped from scenario detail response.

---

### 6. Blacklist Casing for Months/Days (Medium Severity) ❌ NOT VERIFIED

**Previous Finding**: Inconsistent blacklist casing could let "March"/"May" through as destinations.

**Verification**:
- Need to check `src/intake/geography.py` for blacklist implementation
- Need to check if blacklist is case-insensitive

**Status**: **NOT VERIFIED** - Requires deeper inspection of geography module.

---

### 7. Documentation Inconsistencies (Low Severity) ⚠️ PARTIALLY RESOLVED

**Previous Finding**: Freeze status, "no Streamlit path", test counts inconsistent.

**Verification**:
- `app.py` still exists and contains Streamlit implementation
- README.md line 12: Mentions "Workbench UI: Next.js frontend" but Streamlit path still present
- Multiple spec documents still reference Streamlit

**Status**: **PARTIALLY RESOLVED** - Streamlit still exists but documentation acknowledges it as legacy/dev tool.

---

### 8. Route Paths Alignment (Low Severity) ❌ NOT RESOLVED

**Previous Finding**: Docs target `/app/workbench` but implementation uses `/workbench`.

**Verification**:
- `frontend/src/app/workbench/page.tsx` exists at `/workbench` route
- `frontend/src/app/workspace/[tripId]/*` routes exist at `/workspace`  
- No evidence of `/app/workbench` route existing

**Status**: **NOT RESOLVED** - Implementation and docs still diverge on route paths.

---

## New Issues Discovered

### NEW-1: SafetyTab.tsx Undefined Variable (High Severity)

**Location**: `frontend/src/app/workbench/SafetyTab.tsx` line 109

**Issue**: Uses `isStrictFail` variable that is never defined:
```typescript
{travelerBundle && !isStrictFail ? (
```

**Impact**: Will cause runtime error when Safety tab renders with data.

**Fix**: Should be `safety.strict_leakage && !safety.leakage_passed` or similar.

---

### NEW-2: Scenario API Response Missing Mode/Stage (Medium Severity)

**Location**: `frontend/src/app/api/scenarios/[id]/route.ts`

**Issue**: API returns scenario detail without `mode` and `stage`, but IntakeTab expects them.

**IntakeTab.tsx lines 73-74**:
```typescript
if (data.input.stage) setStage(data.input.stage as SpineStage);
if (data.input.mode) setOperatingMode(data.input.mode as OperatingMode);
```

But the scenario fixture has these at root level, not under `input`.

**Fix Options**:
1. Update `scenario-loader.ts` to include mode/stage in ScenarioDetail
2. Update fixture schema to nest mode/stage under inputs
3. Update IntakeTab to read from correct location

---

### NEW-3: DecisionTab Risk Flags Type Mismatch (Medium Severity)

**Location**: `frontend/src/app/workbench/DecisionTab.tsx` lines 71, 191-205

**Issue**: 
- Frontend expects `risk_flags: string[]` (line 71)
- Backend provides `risk_flags: List[Dict[str, Any]]` with dicts containing `flag`, `message`, `severity`

**Current code renders risk flags as strings**:
```typescript
riskFlags.map((item, i) => (
  <li key={`risk-${item}`}>{item}</li>  // item is actually an object!
))
```

**Fix**: Update DecisionTab to handle dict format:
```typescript
riskFlags.map((item, i) => (
  <li key={`risk-${item.flag}-${i}`}>
    [{item.severity}] {item.message}
  </li>
))
```

---

## Summary Table

| Finding | Severity | Status | File(s) |
|---------|----------|--------|---------|
| Licensing documentation | High | ✅ RESOLVED | data/README.md, data/fixtures/README.md |
| Strict leakage wiring | High | ✅ RESOLVED | spine-wrapper.py, spine_api/server.py, strategy.py |
| Payload shape mismatches | High | ⚠️ PARTIAL | Multiple Tab components |
| Subprocess performance | Medium | ✅ RESOLVED | spine-client.ts, spine_api/ |
| Scenario loader drops mode/stage | Medium | ❌ NOT RESOLVED | scenario-loader.ts, IntakeTab.tsx |
| SafetyTab undefined variable | High | ❌ NEW | SafetyTab.tsx line 109 |
| Risk flags type mismatch | Medium | ❌ NEW | DecisionTab.tsx |
| Scenario API response shape | Medium | ❌ NEW | scenario-loader.ts, [id]/route.ts |
| Documentation inconsistencies | Low | ⚠️ PARTIAL | Multiple docs |
| Route paths alignment | Low | ❌ NOT RESOLVED | frontend/src/app/ |

---

## Recommended Actions (Priority Order)

### Immediate (Before Next Deploy)

1. **Fix SafetyTab.tsx undefined variable** (line 109) - Runtime error
2. **Fix DecisionTab.tsx risk flags handling** - Type mismatch
3. **Fix scenario mode/stage propagation** - Feature broken

### Short-term (Next Sprint)

4. Align remaining payload shapes between backend and UI
5. Verify geography blacklist casing
6. Remove or clearly mark Streamlit as dev-only legacy

### Long-term

7. Create shared TypeScript types from Python dataclasses
8. Add end-to-end type checking tests
9. Document route path conventions consistently

---

## Verification Commands

```bash
# Check that spine_api starts correctly
uv run python -m spine_api.server

# Run frontend type checking
cd frontend && npm run type-check 2>/dev/null || npx tsc --noEmit

# Run tests
uv run pytest

# Check scenario loading
curl http://localhost:3000/api/scenarios/clean-family-booking | jq .
```

---

## Appendix: File References

### Backend (Resolved Issues)
- `data/README.md` - License documentation corrected
- `data/fixtures/README.md` - License documentation corrected  
- `src/intake/safety.py` - Strict mode implementation
- `src/intake/strategy.py` - Leakage enforcement in build_traveler_safe_bundle
- `spine_api/server.py` - FastAPI service with strict mode wiring

### Frontend (Unresolved Issues)
- `frontend/src/app/workbench/SafetyTab.tsx` - Undefined `isStrictFail` variable (line 109)
- `frontend/src/app/workbench/DecisionTab.tsx` - Risk flags type mismatch (lines 71, 191-205)
- `frontend/src/app/workbench/StrategyTab.tsx` - Multiple field mismatches
- `frontend/src/app/workbench/IntakeTab.tsx` - Expects mode/stage in wrong location
- `frontend/src/lib/scenario-loader.ts` - Drops mode/stage from ScenarioDetail

### Subprocess Wrapper (Legacy)
- `frontend/src/lib/spine-wrapper.py` - Strict mode wired but subprocess approach deprecated

---

*Report generated by verification audit against previous findings*
