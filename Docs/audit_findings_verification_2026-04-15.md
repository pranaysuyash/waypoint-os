# Audit Findings Verification Report

**Date**: 2026-04-15  
**Auditor**: Code Review  
**Scope**: Verify all issues identified in previous comprehensive audit and identify any new issues

---

## Executive Summary

| Finding | Severity | Status | Notes |
|---------|----------|--------|-------|
| Secondary dataset license (ODbL-1.0 vs MIT) | HIGH | ✅ **FIXED** | README correctly documents ODbL-1.0 |
| strict_leakage wiring in Next.js path | HIGH | ✅ **FIXED** | Fully wired through spine_api FastAPI service |
| Frontend/backend payload shape mismatches | HIGH | ⚠️ **PARTIAL** | Core response shape matches; UI expects some fields that differ from backend |
| Python subprocess per spine run | HIGH | ✅ **FIXED** | Now uses persistent FastAPI spine_api service |
| Scenario loader drops stage/mode | MEDIUM | ⚠️ **CONFIRMED** | Issue exists as documented |
| Blacklist casing inconsistent | MEDIUM | ⚠️ **CONFIRMED** | Mixed case checks exist |
| Record seen city JSON corruption risk | MEDIUM | ✅ **ACKNOWLEDGED** | Documented limitation |

---

## Detailed Verification

### 1. Licensing Risk (HIGH) — ✅ FIXED

**Location**: `data/fixtures/README.md` lines 48-60

**Finding**: The audit claimed the secondary city dataset was incorrectly documented as MIT when upstream is ODbL-1.0.

**Verification Result**: ✅ **CORRECTLY DOCUMENTED**

```markdown
### cities.json (world-cities.json)

**Source**: https://github.com/dr5hn/countries-states-cities-database
**License**: ODbL-1.0 (Open Database License) — share-alike obligations apply
**Size**: ~150,000 cities
**Format**: JSON array

**Usage**: Supplemental city database, fills gaps in GeoNames coverage

**⚠️ License Note**: This dataset is ODbL-1.0, not MIT as previously documented.
ODbL-1.0 requires share-alike for derivative databases, which conflicts with proprietary licensing.
If proprietary licensing is required, replace with an MIT/CC0-licensed alternative.
```

**Conclusion**: The documentation now correctly identifies ODbL-1.0 license with appropriate warnings. This issue has been resolved.

---

### 2. Strict Leakage Mode Wiring (HIGH) — ✅ FIXED

**Location**: `spine_api/server.py`, `frontend/src/lib/spine-wrapper.py`

**Finding**: Audit claimed `strict_leakage` accepted by API but Python wrapper ignored it.

**Verification Result**: ✅ **FULLY WIRED**

In `spine_api/server.py` (lines 225-228, 265-269, 290-318):
```python
# Set strict mode for this request
if request.strict_leakage:
    set_strict_mode(True)

# ... leakage detection ...
safety = SafetyResult(
    strict_leakage=request.strict_leakage,
    leakage_passed=is_safe,
    leakage_errors=all_leaks,
)

# Strict mode failure handling (lines 290-318)
except ValueError as e:
    # Strict leakage violation — suppress traveler_bundle, return ok=False
    return SpineRunResponse(
        ok=False,
        run_id=run_id,
        packet=None,
        validation=None,
        decision=None,
        strategy=None,
        traveler_bundle=None,  # suppressed on strict failure
        internal_bundle=None,
        safety=SafetyResult(
            strict_leakage=True,
            leakage_passed=False,
            leakage_errors=[error_message],
        ),
        meta=meta,
    )
```

In `frontend/src/lib/spine-wrapper.py` (lines 102-107):
```python
strict_leakage = data.get("strict_leakage", False)

# Set strict leakage mode in the safety module before running spine
if strict_leakage:
    from src.intake.safety import set_strict_mode
    set_strict_mode(True)
```

**Conclusion**: Strict mode is properly wired end-to-end. The API accepts `strict_leakage`, sets the mode via `set_strict_mode()`, and handles ValueError from `enforce_no_leakage()` by returning `ok=False` with suppressed bundles.

---

### 3. Next.js Integration Shape Compatibility (HIGH) — ⚠️ PARTIAL

**Finding**: Audit claimed UI expects different field shapes than backend produces.

**Verification Result**: ⚠️ **MOSTLY COMPATIBLE WITH MINOR MISMATCHES**

#### Response Shape Comparison:

| Field | Backend (orchestration.py) | Frontend (types/spine.ts) | Status |
|-------|---------------------------|---------------------------|--------|
| `packet` | `CanonicalPacket` object | `unknown` | ✅ Compatible (dynamic) |
| `decision` | `DecisionResult` object | `unknown` | ⚠️ UI expects different key names (see below) |
| `strategy` | `SessionStrategy` object | `unknown` | ✅ Compatible |
| `traveler_bundle` | `PromptBundle` object | `unknown` | ✅ Compatible |
| `internal_bundle` | `PromptBundle` object | `unknown` | ✅ Compatible |
| `safety` | `{strict_leakage, leakage_passed, leakage_errors}` | `SafetyResult` | ✅ Compatible |

#### Specific Field Mismatches Found:

**Decision Tab (`DecisionTab.tsx`)** expects:
- `follow_up_questions` — Backend provides this ✅
- `risk_flags` as array of strings — Backend provides array of dicts with `message` field ⚠️
- `contradictions` as array of strings — Backend provides array of dicts with `field_name`, `values`, `sources` ⚠️

**Strategy Tab (`StrategyTab.tsx`)** expects:
- `tone_indicator` — Backend provides `suggested_tone` ⚠️
- `constraints` on strategy — Not present in `SessionStrategy` ⚠️
- `internalBundle.traveler_safe` — Not a field in `PromptBundle` ⚠️

**Safety Tab (`SafetyTab.tsx`)** expects:
- `travelerBundle.message` — Backend provides `user_message` ⚠️
- `travelerBundle.itinerary` — Backend provides `system_context` + sequences ⚠️

**Conclusion**: While the high-level response structure is compatible, several UI components expect field names that differ from what the backend produces. The UI uses type casting which may mask these issues at compile time but could cause runtime display problems.

---

### 4. Python Subprocess Per Request (HIGH) — ✅ FIXED

**Finding**: Audit claimed spine spawns Python subprocess per request, causing cold-start issues with geography.

**Verification Result**: ✅ **NOW USES PERSISTENT FASTAPI SERVICE**

Current architecture (from `spine_api/server.py`):
```python
# FastAPI service with persistent Python process
app = FastAPI(...)

# Pre-loaded modules at startup
from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.safety import set_strict_mode
```

The `spine-client.ts` now calls HTTP endpoint instead of spawning subprocess:
```typescript
const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

export async function runSpine(request: SpineRunRequest): Promise<SpineRunResponse> {
  const response = await fetch(`${SPINE_API_URL}/run`, {...});
  // ...
}
```

**Conclusion**: The subprocess model has been replaced with a persistent FastAPI service. Cold-start geography loading happens once at service startup, not per request.

---

### 5. Scenario Loader Drops Stage/Mode (MEDIUM) — ⚠️ CONFIRMED

**Location**: `frontend/src/lib/scenario-loader.ts` lines 47-51

**Finding**: Audit claimed scenario loader returns only inputs and expected, dropping mode and stage.

**Verification Result**: ⚠️ **CONFIRMED ISSUE EXISTS**

```typescript
export interface ScenarioDetail {
  id: string;
  input: ScenarioInputs;
  expected: ScenarioExpected;
  // NOTE: mode and stage are MISSING here
}

export function loadScenarioById(id: string): ScenarioDetail | null {
  // ...
  return {
    id,
    input: scenario.inputs,
    expected: scenario.expected,
    // mode and stage NOT included!
  };
}
```

However, `ScenarioFixture` interface includes `mode` and `stage`:
```typescript
export interface ScenarioFixture {
  scenario_id: string;
  title: string;
  description: string;
  mode: string;  // Present in fixture
  stage: string; // Present in fixture
  inputs: ScenarioInputs;
  expected: ScenarioExpected;
}
```

**Impact**: `IntakeTab.tsx` tries to access `data.input.stage` and `data.input.mode` (lines 73-74), but these won't be present because they're at the root level, not inside `input`.

**Conclusion**: Issue confirmed. The scenario loader needs to include mode/stage in the returned detail object.

---

### 6. Blacklist Casing Inconsistency (MEDIUM) — ⚠️ CONFIRMED

**Location**: `src/intake/geography.py`

**Finding**: Audit claimed blacklist casing is inconsistent (risk: capitalized months/days slip through).

**Verification Result**: ⚠️ **PARTIALLY ADDRESSED**

Current blacklist (lines 38-55):
```python
_BLACKLIST: Set[str] = {
    # ...
    # Month names (can be place names but should be excluded in travel context)
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    # Days of week
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    # ...
}
```

Check implementations:
1. Line 252: `name.lower() in _BLACKLIST` — ❌ Will never match capitalized entries
2. Line 267: `name_lower in _BLACKLIST` — ❌ Will never match capitalized entries
3. Line 303: `city.lower() in _BLACKLIST` — ❌ Will never match capitalized entries
4. Line 434: `name.lower() in {b.lower() for b in _BLACKLIST}` — ✅ Correctly case-insensitive

Only `is_known_destination()` (line 434) creates a proper case-insensitive check.

**Conclusion**: Issue partially exists. While `is_known_destination()` handles casing correctly, `is_known_city()` and `is_known_city_normalized()` do lowercase checks against a mixed-case set, which will never match capitalized entries.

---

### 7. Additional Issues Found

#### 7.1 PromptBundle.internal_notes Always Included (LOW)

**Location**: `src/intake/strategy.py` lines 133-142

The `PromptBundle.to_dict()` method includes `internal_notes` even for traveler bundles. While this is empty for traveler bundles (set on line 870), the field itself exists in the serialized output. This creates a potential future leak vector if UI code accidentally renders the full JSON.

**Recommendation**: Consider having traveler-safe bundles omit the `internal_notes` key entirely rather than setting it to an empty string.

#### 7.2 "both" Audience Path Attaches Internal Notes (LOW)

**Location**: `src/intake/strategy.py` lines 940-948

```python
if audience == "both":
    internal_bundle = build_internal_bundle(strategy, decision, packet)
    traveler_bundle = build_traveler_safe_bundle(strategy, decision)
    # Return combined bundle with traveler as primary, internal notes attached
    bundle = traveler_bundle
    bundle.internal_notes = internal_bundle.internal_notes  # ⚠️ Attaches internal to traveler
```

The "both" audience path explicitly attaches internal notes to the traveler bundle object. While the field is `internal_notes`, this makes the object structurally unsafe unless consumers are careful.

#### 7.3 Safety Tab Missing `isStrictFail` Variable (COSMETIC)

**Location**: `frontend/src/app/workbench/SafetyTab.tsx` line 109

```typescript
{travelerBundle && !isStrictFail ? (
```

The variable `isStrictFail` is used but never defined. This will cause a runtime ReferenceError when the Safety tab renders with a traveler bundle.

---

## Summary of All Issues

### Resolved Issues (✅)
1. ✅ Licensing documentation now correctly identifies ODbL-1.0
2. ✅ Strict leakage mode fully wired through FastAPI service
3. ✅ Python subprocess model replaced with persistent FastAPI service

### Confirmed Issues (⚠️)
1. ⚠️ Scenario loader drops mode/stage from detail response
2. ⚠️ Blacklist casing inconsistent in `is_known_city()` functions
3. ⚠️ UI expects some field names that differ from backend (may cause display issues)

### New Issues Found
1. ⚠️ SafetyTab uses undefined `isStrictFail` variable (will crash)
2. ⚠️ "both" audience path attaches internal notes to traveler bundle
3. ⚠️ PromptBundle always includes `internal_notes` field even for traveler bundles

---

## Recommendations

1. **Fix scenario loader**: Include `mode` and `stage` in `ScenarioDetail` interface and return them in `loadScenarioById()`

2. **Fix blacklist casing**: Make all blacklist checks consistently case-insensitive by converting the blacklist to lowercase at module load time

3. **Fix SafetyTab**: Define `isStrictFail` variable or remove the check

4. **Consider bundle serialization**: For traveler-safe bundles, consider omitting `internal_notes` key entirely rather than empty string

5. **Document field mapping**: Create explicit documentation of frontend/backend field mappings to prevent UI display issues
