# Audit Findings Verification Report

**Date:** 2026-04-15
**Status:** Comprehensive verification of audit findings

---

## Executive Summary

The audit identified several critical issues. This report verifies which issues are resolved, which remain, and any additional issues discovered.

---

## 1. CRITICAL ISSUES

### 1.1 Licensing Risk (ODbL vs MIT) - **RESOLVED** ✅

**Audit Finding:** The repo claimed the secondary city dataset (cities.json) was MIT-licensed, but the upstream repository (countries-states-cities-database) is ODbL-1.0.

**Current Status:**
- `data/README.md` (lines 34-55): **Correctly documents ODbL-1.0 license**
- `data/fixtures/README.md` (lines 57-59): **Correctly documents ODbL-1.0 license with warning**

**Verdict:** Documentation has been corrected. The licensing issue is properly documented.

---

### 1.2 Next.js Workbench Integration Shape-Incompatible - **PARTIALLY RESOLVED** ⚠️

**Audit Finding:** The UI assumes packet/decision/bundle objects have fields that don't exist (arrays instead of dicts, wrong keys, wrong nesting).

**Current Status Analysis:**

| Component | Status | Notes |
|-----------|--------|-------|
| PacketTab.tsx | ✅ Compatible | Uses `packet.facts`, `packet.derived_signals` dict structures |
| DecisionTab.tsx | ⚠️ Partially Compatible | Uses `follow_up_questions` (correct) but `contradictions` as strings instead of dicts |
| StrategyTab.tsx | ✅ Compatible | Uses correct `PromptBundle` fields |
| SafetyTab.tsx | ⚠️ Issues | References `isStrictFail` variable that doesn't exist (line 109, 148) |

**Specific Issues Found:**

#### SafetyTab.tsx - Undefined Variable
```typescript
// Line 109, 148 - 'isStrictFail' is used but never defined
{travelerBundle && !isStrictFail ? (  // ERROR: isStrictFail not defined
```

#### DecisionTab.tsx - Contradictions Type Mismatch
```typescript
// DecisionTab expects contradictions as strings[]
interface DecisionOutput {
  contradictions: string[];  // UI expects strings
}

// But backend returns Dict[str, Any][]
// decision.py line 65: contradictions: List[Dict[str, Any]]
```

**Verdict:** Partial compatibility. SafetyTab has a runtime error (undefined variable). DecisionTab expects wrong contradiction type.

---

### 1.3 Strict Leakage Mode Wiring - **RESOLVED** ✅

**Audit Finding:** Strict leakage mode accepted by API but ignored in Python wrapper.

**Current Status:**

1. **spine-wrapper.py** (lines 102-107): ✅ **CORRECTLY WIRED**
```python
strict_leakage = data.get("strict_leakage", False)
if strict_leakage:
    from src.intake.safety import set_strict_mode
    set_strict_mode(True)
```

2. **spine-client.ts**: ✅ Uses HTTP API (not subprocess) - calls spine-api

3. **spine-api/server.py** (lines 226-227): ✅ **CORRECTLY WIRED**
```python
if request.strict_leakage:
    set_strict_mode(True)
```

4. **route.ts**: ✅ Passes strict_leakage to runSpine()

**Verdict:** Strict leakage is properly wired through the entire path.

---

### 1.4 Python Subprocess Per Spine Run - **MISLEADING** ⚠️

**Audit Finding:** spine-client.ts spawns Python each request causing performance issues.

**Current Status:**
- **spine-client.ts** does NOT spawn subprocesses anymore
- It calls a **persistent FastAPI service** (spine-api) via HTTP

```typescript
// spine-client.ts lines 28-60
const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
export async function runSpine(request: SpineRunRequest): Promise<SpineRunResponse> {
  const response = await fetch(`${SPINE_API_URL}/run`, {...});
}
```

**However:** The old spine-wrapper.py still exists and is documented as "the ONLY entrypoint" but is no longer used by the actual client.

**Verdict:** The subprocess issue is resolved (uses HTTP API now), but legacy wrapper.py remains with outdated documentation.

---

## 2. MEDIUM PRIORITY ISSUES

### 2.1 Scenario Loader Drops Mode/Stage - **OPEN** ⚠️

**Audit Finding:** Scenario loader returns only inputs and expected, dropping mode and stage.

**Current Status:**

1. **Scenario Fixture Schema** (SC-001_clean_family_booking.json):
```json
{
  "mode": "normal_intake",
  "stage": "discovery",
  "inputs": {...},
  "expected": {...}
}
```

2. **scenario-loader.ts** `loadScenarioById()` (lines 74-90):
```typescript
return {
  id,
  input: scenario.inputs,
  expected: scenario.expected,
  // Note: mode and stage are NOT returned
};
```

**Issue Confirmed:** The loader does drop mode/stage, but looking at the IntakeTab expectations:

The audit said: "Intake tab expects data.input.stage and data.input.mode"

But the scenario structure has mode/stage at root level, not under inputs:
```json
{
  "mode": "normal_intake",  // At root
  "stage": "discovery",     // At root
  "inputs": {...}           // No mode/stage here
}
```

**Verdict:** The scenario loader should return mode/stage. This is a valid issue.

---

### 2.2 Blacklist Casing Inconsistent - **RESOLVED** ✅

**Audit Finding:** Blacklist casing inconsistent - months/days could slip through.

**Current Status:**

**geography.py** (lines 252, 267, 303, 434):
```python
# Line 252: Uses .lower() for check
if not name or name.lower() in _BLACKLIST:

# Line 267: Uses .lower() for check  
if name_lower in _BLACKLIST:

# Line 303: Uses .lower() for check
if not city or city.lower() in _BLACKLIST:

# Line 433-434: Explicit case-insensitive check
if name.lower() in {b.lower() for b in _BLACKLIST}:
```

**Verdict:** The blacklist is checked case-insensitively. Months/days will be caught regardless of casing.

---

### 2.3 Streamlit Still Present vs Docs - **ACKNOWLEDGED** ⚠️

**Audit Finding:** Docs claim "no Streamlit runtime path" but app.py still exists.

**Current Status:**
- `app.py` exists and is runnable (21,022 bytes)
- `Docs/status/NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md` (line 11): "No Streamlit runtime path is active for this build track"

**Verdict:** Streamlit app exists but is marked as not the active path. This is acceptable for development but should be clarified.

---

## 3. ADDITIONAL ISSUES DISCOVERED

### 3.1 SafetyTab Runtime Error - **NEW CRITICAL** 🔴

**File:** `frontend/src/app/workbench/SafetyTab.tsx`

**Issue:** Variable `isStrictFail` used but never defined.

**Lines affected:** 109, 148
```typescript
// Line 109
{travelerBundle && !isStrictFail ? (

// Line 148
{isStrictFail ? "Invalidated due to strict mode failure" : "No traveler bundle available"}
```

**Impact:** Will cause runtime error when Safety tab is rendered.

**Fix needed:** Define `isStrictFail` based on safety result:
```typescript
const isStrictFail = safety?.strict_leakage && !safety?.leakage_passed;
```

---

### 3.2 spine-wrapper.py Documentation Mismatch - **NEW MEDIUM** 🟡

**File:** `frontend/src/lib/spine-wrapper.py`

**Issue:** Documentation claims "The ONLY entrypoint the Next.js BFF should use" but the actual spine-client.ts uses HTTP API.

**Impact:** Confusing for developers. Legacy code with misleading docs.

**Recommendation:** Update docstring or remove if no longer used.

---

### 3.3 DecisionTab Contradiction Type Mismatch - **NEW MEDIUM** 🟡

**File:** `frontend/src/app/workbench/DecisionTab.tsx`

**Issue:** UI expects `contradictions: string[]` but backend returns `List[Dict[str, Any]]`.

**Backend (decision.py line 65):**
```python
contradictions: List[Dict[str, Any]] = field(default_factory=list)
```

**Frontend (DecisionTab.tsx lines 39-47):**
```typescript
interface DecisionOutput {
  contradictions: string[];  // Wrong type!
}
```

**Impact:** Contradictions won't render correctly.

---

### 3.4 Risk Flags Type Mismatch - **NEW MEDIUM** 🟡

**File:** `frontend/src/app/workbench/DecisionTab.tsx`

**Issue:** UI expects `risk_flags: string[]` but backend returns `List[Dict[str, Any]]`.

**Backend (decision.py line 70):**
```python
risk_flags: List[Dict[str, Any]] = field(default_factory=list)
```

**Frontend (DecisionTab.tsx line 45):**
```typescript
risk_flags: string[];  // Wrong type!
```

---

### 3.5 No FROZEN_SPINE_STATUS.md File - **NEW LOW** 🟢

**Audit Finding:** "Update Docs/FROZEN_SPINE_STATUS.md to reflect geography separation"

**Current Status:** File does not exist at `Docs/status/FROZEN_SPINE_STATUS.md`

**Impact:** Missing documentation.

---

## 4. SUMMARY TABLE

| Issue | Audit Status | Current Status | Priority |
|-------|-------------|----------------|----------|
| Licensing (ODbL vs MIT) | Open | **RESOLVED** | High |
| UI Payload Shape | Open | **PARTIALLY RESOLVED** | High |
| Strict Leakage Wiring | Open | **RESOLVED** | High |
| Python Subprocess | Open | **MISLEADING/RESOLVED** | Medium |
| Scenario Loader Mode/Stage | Open | **OPEN** | Medium |
| Blacklist Casing | Open | **RESOLVED** | Low |
| Streamlit vs Docs | Open | **ACKNOWLEDGED** | Low |
| **SafetyTab Runtime Error** | **Missed** | **NEW CRITICAL** | **Critical** |
| **DecisionTab Type Mismatches** | **Partial** | **NEW MEDIUM** | **Medium** |
| **FROZEN_SPINE_STATUS Missing** | **Noted** | **MISSING** | **Low** |

---

## 5. RECOMMENDED ACTIONS

### Immediate (Before Using Workbench):
1. **Fix SafetyTab.tsx** - Define `isStrictFail` variable
2. **Fix DecisionTab.tsx** - Update contradiction and risk_flags types

### Short Term:
3. **Update scenario-loader.ts** - Return mode and stage
4. **Remove or update spine-wrapper.py** - Clarify it's legacy
5. **Create FROZEN_SPINE_STATUS.md** - Document freeze status

### Documentation:
6. **Clarify Streamlit status** - Note it exists but is not the active path

---

## 6. AUDIT ACCURACY ASSESSMENT

**What the audit got right:**
- ✅ Licensing issue existed (now fixed)
- ✅ Scenario loader drops mode/stage (still true)
- ✅ Streamlit exists despite docs (still true)

**What the audit missed:**
- ❌ SafetyTab has runtime error (undefined variable)
- ❌ DecisionTab has type mismatches (contradictions, risk_flags)

**What the audit overstated:**
- ⚠️ "Python subprocess per spine run" - Already uses HTTP API
- ⚠️ "Strict leakage not wired" - Actually is wired correctly
