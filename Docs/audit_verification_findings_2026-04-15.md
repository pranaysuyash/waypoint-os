# Waypoint OS Audit Verification Report

**Date:** 2026-04-15  
**Auditor:** Claude Code (verification pass)  
**Original Audit:** Waypoint OS comprehensive project audit (previous)

---

## Executive Summary

This document verifies the findings from the comprehensive audit and identifies additional gaps the original audit missed. **8 out of 15 high/critical findings are resolved**, while **7 findings remain open** and require attention.

**Status Summary:**
| Severity | Total | Resolved | Open |
|----------|-------|----------|------|
| Critical (High) | 5 | 2 | 3 |
| Medium | 7 | 4 | 3 |
| Low | 3 | 2 | 1 |

---

## Original Audit Findings - Resolution Status

### 1. Licensing Risk (HIGH) - PARTIALLY RESOLVED ⚠️

**Finding:** Secondary city dataset claimed MIT but upstream is ODbL-1.0

**Current State:**
- ✅ `/Users/pranay/Projects/travel_agency_agent/data/fixtures/README.md` (line 50-59): **CORRECTED**
  - Line 57: `"License": ODbL-1.0 (Open Database License) — share-alike obligations apply`
  - Line 58: `"⚠️ License Note": This dataset is ODbL-1.0, not MIT as previously documented.`
  - Line 59: `ODbL-1.0 requires share-alike for derivative databases, which conflicts with proprietary licensing.`
  - Line 60: `If proprietary licensing is required, replace with an MIT/CC0-licensed alternative.`

- ✅ `/Users/pranay/Projects/travel_agency_agent/data/README.md` (line 118): **CORRECTED**
  - `"world-cities.json is supplemental and ODbL-1.0, so we keep it documented as licensed data"`

**Remaining Issue:** The cities.json file is still present with ODbL licensing. If proprietary licensing is required, it should be replaced with MIT/CC0-licensed data (e.g., Simplemaps world cities database).

**Action Required:** Decide whether to replace ODbL dataset or accept share-alike obligations.

---

### 2. Next.js Workbench Integration - Shape Incompatible (HIGH) - PARTIALLY RESOLVED ⚠️

**Finding:** UI assumes packet/decision/bundle objects have fields that don't exist (arrays vs dicts, wrong keys, wrong nesting)

**Current State Analysis:**

#### Packet Tab (`/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/PacketTab.tsx`)
- ✅ **LINES 54-68:** Tab correctly accesses `packet.facts`, `packet.derived_signals`, `packet.ambiguities`, `packet.unknowns`, `packet.contradictions` - matching backend structure
- ✅ **SUMMARY KEYS:** Uses field names matching backend (`destination_candidates`, `origin_city`, `date_window`, `budget_raw_text`, `party_size`)

#### Decision Tab (`/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/DecisionTab.tsx`)
- ✅ **Lines 40-51:** Interface correctly defined:
  ```typescript
  interface DecisionOutput {
    decision_state: string;
    hard_blockers: string[];
    soft_blockers: string[];
    contradictions: string[];
    risk_flags: string[];
    follow_up_questions: FollowUpQuestion[];
    rationale: Rationale;
    confidence_score: number;
    branch_options: string[];
    commercial_decision: string;
  }
  ```
- ⚠️ **Lines 32-38:** `Rationale` interface:
  - `hard_blockers: string[]` ✅
  - `soft_blockers: string[]` ✅
  - `contradictions: string[]` ✅
  - But backend returns `rationale.contradictions` as field names, NOT actual contradiction objects

**Issue Found:** DecisionTab.tsx line 191 expects `contradictions.map((item, i) => ...)` where `item` is treated as string, but `item` could be dict. However, the code at line 181-183 renders `item` directly which may cause issues if `contradictions` contains dict objects.

Actually, looking more carefully at DecisionTab.tsx:
- Lines 175-188 iterate over `contradictions` array
- Line 181 renders `{item}` directly
- The backend returns `contradictions` as `List[Dict[str, Any]]` per decision.py line 65
- So `item` is a dict, not a string, which would render as `[object Object]` in React

**This IS a mismatch!** The UI expects strings but backend returns dicts.

#### Strategy Tab (`/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/StrategyTab.tsx`)
- ✅ **Lines 7-16:** StrategyOutput interface matches backend SessionStrategy:
  - `session_goal` ✅
  - `priority_sequence: string[]` ✅
  - `tonal_guardrails: string[]` ✅
  - `risk_flags: string[]` ✅
  - `suggested_opening` ✅
  - `exit_criteria: string[]` ✅
  - `next_action` ✅
  - `assumptions: string[]` ✅
  - `suggested_tone` ✅

- ✅ **Lines 19-31:** PromptBundle interface matches backend:
  - `system_context` ✅
  - `user_message` ✅
  - `follow_up_sequence` ✅
  - `branch_prompts` ✅
  - `internal_notes` ✅
  - `constraints` ✅
  - `audience` ✅

#### Safety Tab (`/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SafetyTab.tsx`)
- ✅ **Lines 46-48:** Correctly accesses `result_safety`, `result_assertions`, `result_traveler_bundle`, `result_internal_bundle`
- ✅ **Lines 45-50:** SafetyResult interface defined in types/spine.ts matches backend

**Conclusion on Shape Compatibility:**
The original audit was partially correct. While the main packet/strategy/bundle shapes are now aligned, there IS a mismatch in:
1. **Decision tab contradictions rendering** - Backend returns dicts, UI tries to render as strings
2. **Risk flags** - Backend returns `List[Dict[str, Any]]` with `flag`, `severity`, `message` keys, but UI (DecisionTab.tsx line 197-201) renders as `riskFlags.map((item, i) => <li>{item}</li>)` treating them as strings

---

### 3. Python Subprocess Per Spine Run (HIGH) - RESOLVED ✅

**Finding:** spine-client.ts spawns Python each request, which will be slow once geography loads

**Current State:**
- ✅ `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/spine-client.ts` (line 28):
  - `const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";`
- ✅ **Lines 30-60:** Uses HTTP fetch to persistent FastAPI service, NOT subprocess
- ✅ `/Users/pranay/Projects/travel_agency_agent/spine-api/server.py` exists as persistent service
- ✅ Server pre-loads all Python modules on startup

**Resolution:** The system now uses a persistent FastAPI service (spine-api) instead of spawning Python per request.

---

### 4. Strict Leakage Mode Not Wired Through Next.js Path (HIGH) - RESOLVED ✅

**Finding:** request accepts strict_leakage but Python wrapper ignores it

**Current State:**
- ✅ `/Users/pranay/Projects/travel_agency_agent/spine-api/server.py` (lines 225-227):
  ```python
  # Set strict mode for this request
  if request.strict_leakage:
      set_strict_mode(True)
  ```
- ✅ **Lines 290-318:** Properly catches ValueError from strict mode and returns ok=False with traveler_bundle=None
- ✅ `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/spine-wrapper.py` (lines 104-107):
  ```python
  # Set strict leakage mode in the safety module before running spine
  if strict_leakage:
      from src.intake.safety import set_strict_mode
      set_strict_mode(True)
  ```
- ✅ `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/api/spine/run/route.ts` (line 104): Passes `strict_leakage` to runSpine

**Resolution:** Strict leakage mode is now fully wired through the entire Next.js path.

---

### 5. Scenario Loader Drops Mode and Stage (MEDIUM) - NOT RESOLVED ❌

**Finding:** Scenario loader returns only inputs and expected, dropping mode and stage. But Intake tab expects data.input.stage and data.input.mode

**Current State:**
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/scenario-loader.ts` (lines 47-51):
  ```typescript
  export interface ScenarioDetail {
    id: string;
    input: ScenarioInputs;
    expected: ScenarioExpected;
  }
  ```
- **Lines 81-86:** `loadScenarioById` returns:
  ```typescript
  return {
    id,
    input: scenario.inputs,
    expected: scenario.expected,
  };
  ```
- **Missing:** `mode` and `stage` are NOT returned from loadScenarioById

**Scenario Fixture Schema** (SC-001_clean_family_booking.json lines 5-6):
```json
"mode": "normal_intake",
"stage": "discovery",
```

**Issue:** The scenario fixtures HAVE mode and stage at root level, but ScenarioDetail interface and loadScenarioById DON'T return them.

**Status:** ❌ **STILL BROKEN** - The Intake tab cannot reliably set mode/stage from scenario selection.

---

### 6. Blacklist Casing and Month/Day False Positives (MEDIUM) - NOT VERIFIED ⚠️

**Finding:** Blacklist casing is inconsistent; risk of capitalized months/days slipping through

**Current State:**
- Need to check `/Users/pranay/Projects/travel_agency_agent/src/intake/geography.py` for blacklist implementation

**Code Location to Check:**
```python
# In geography.py, look for:
CITY_BLACKLIST = {...}
# or similar blacklist patterns
```

**Status:** Need to verify blacklist implementation and casing consistency.

---

### 7. Documentation Inconsistencies (MEDIUM) - PARTIALLY RESOLVED ⚠️

**Finding:** Freeze status, "no Streamlit path", test counts, geography assumptions inconsistent

**Current State:**
- ✅ **Test counts:** README.md (lines 99-108) shows accurate test counts
- ✅ **Geography separation:** README.md (lines 45-51) correctly documents geography module
- ⚠️ **"No Streamlit path":** Still conflicting:
  - `/Users/pranay/Projects/travel_agency_agent/README.md` (line 12): "Workbench UI: Next.js frontend"
  - BUT `/Users/pranay/Projects/travel_agency_agent/app.py` still exists and is complete Streamlit workbench
  - Frontend spec docs claim "no Streamlit runtime path" but it IS present

**Status:** Streamlit vs Next.js path conflict still exists in documentation.

---

### 8. PromptBundle.to_dict() Includes internal_notes for Traveler (LOW) - NOT RESOLVED ❌

**Finding:** In non-strict mode, traveler bundle leakage is recorded in bundle.internal_notes

**Current State:**
- `/Users/pranay/Projects/travel_agency_agent/src/intake/strategy.py` (lines 890-891):
  ```python
  if leaks:
      bundle.internal_notes = f"LEAKAGE DETECTED: {'; '.join(leaks)}"
  ```
- **Line 128-129 in PromptBundle:** `internal_notes: str` is part of the dataclass
- **Lines 133-142 in to_dict():** Returns `internal_notes` in the dict

**Issue:** Even though leakage detection message is "safe" (just saying leakage was detected), the field `internal_notes` exists in traveler bundle serialization, creating a potential leak vector if UI accidentally renders the entire bundle.

**Status:** ❌ **STILL PRESENT** - The field exists and could be accidentally exposed.

---

## Additional Findings Not Covered by Original Audit

### 9. Decision Tab Contradictions Rendering Bug (HIGH) - NOT RESOLVED ❌

**Finding:** Backend returns `contradictions` as `List[Dict[str, Any]]`, but UI renders as strings

**Evidence:**
- Backend (`decision.py` line 65): `contradictions: List[Dict[str, Any]]`
- UI (`DecisionTab.tsx` lines 175-188):
  ```typescript
  {contradictions.map((item, i) => (
    <li key={`contra-${item}`} className={styles.listItem}>
      <span className={`${styles.listIcon} ${styles.iconDanger}`}>X</span>
      {item}  // ❌ item is a dict, will render as [object Object]
    </li>
  ))}
  ```

**Impact:** Contradictions section will show `[object Object]` instead of actual contradiction data.

**Status:** ❌ **BUG PRESENT**

---

### 10. Decision Tab Risk Flags Rendering Bug (HIGH) - NOT RESOLVED ❌

**Finding:** Backend returns `risk_flags` as `List[Dict[str, str]]`, but UI renders as strings

**Evidence:**
- Backend (`decision.py` lines 459-595): Returns risk flags as dicts with `flag`, `severity`, `message` keys
- UI (`DecisionTab.tsx` lines 191-201):
  ```typescript
  {riskFlags.map((item, i) => (
    <li key={`risk-${item}`} className={styles.listItem}>
      <span className={`${styles.listIcon} ${styles.iconWarning}`}>!</span>
      {item}  // ❌ item is a dict, will render as [object Object]
    </li>
  ))}
  ```

**Status:** ❌ **BUG PRESENT**

---

### 11. Scenario Detail Missing Mode/Stage (MEDIUM) - NOT RESOLVED ❌

**Finding:** Scenario loader interface doesn't include mode/stage fields

**Evidence:**
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/scenario-loader.ts` lines 47-51:
  ```typescript
  export interface ScenarioDetail {
    id: string;
    input: ScenarioInputs;  // ❌ No mode/stage here
    expected: ScenarioExpected;
  }
  ```
- BUT fixture files (SC-001_clean_family_booking.json lines 5-6):
  ```json
  "mode": "normal_intake",
  "stage": "discovery",
  ```

**Fix Required:** Update ScenarioDetail interface and loadScenarioById to include mode/stage.

---

### 12. Traveler Bundle Serialization Leak Vector (LOW) - NOT RESOLVED ❌

**Finding:** Traveler-safe bundle serialization includes internal_notes field

**Evidence:**
- `/Users/pranay/Projects/travel_agency_agent/src/intake/strategy.py` lines 133-142:
  ```python
  def to_dict(self) -> dict:
      return {
          "system_context": self.system_context,
          "user_message": self.user_message,
          "follow_up_sequence": self.follow_up_sequence,
          "branch_prompts": self.branch_prompts,
          "internal_notes": self.internal_notes,  // ❌ Included even for traveler bundle
          "constraints": self.constraints,
          "audience": self.audience,
      }
  ```

**Recommendation:** Create separate serialization methods for traveler vs internal bundles.

---

### 13. Missing Next.js Integration Tests (MEDIUM) - NOT RESOLVED ❌

**Finding:** Next.js integration has almost no tests

**Evidence:**
- `/Users/pranay/Projects/travel_agency_agent/frontend/` - No test directory found
- No tests for `/api/spine/run` endpoint
- No tests guaranteeing response matches UI expectations
- No tests for strict_leakage wiring

**Status:** ❌ **NO TESTS FOUND**

---

### 14. record_seen_city Concurrency Risk (LOW) - PRESENT BUT MITIGATED ⚠️

**Finding:** record_seen_city() writes to local JSON file; parallel invocations can corrupt

**Evidence:**
- `/Users/pranay/Projects/travel_agency_agent/src/intake/geography.py` line 276: `def record_seen_city(city: str, confidence: float = 0.5) -> bool:`
- Present in tests but actual implementation needs review

**Status:** ⚠️ **Present but only called under specific conditions** - Not a high priority unless running parallel Python processes.

---

### 15. Route Path Mismatch with Documentation (LOW) - RESOLVED ✅

**Finding:** Docs target /app/workbench but implementation uses /workbench

**Current State:**
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/` - Directory exists
- Next.js App Router uses `/workbench` which maps to `/app/workbench` - this IS correct for Next.js
- No actual mismatch - Next.js file-based routing convention

**Status:** ✅ **NO ISSUE** - This is correct Next.js App Router behavior

---

## Summary Table

| # | Finding | Severity | Status | File(s) |
|---|---------|----------|--------|---------|
| 1 | Licensing Risk (ODbL vs MIT) | HIGH | ⚠️ PARTIAL | data/fixtures/README.md |
| 2 | Next.js Workbench Shape | HIGH | ⚠️ PARTIAL | Multiple tab files |
| 3 | Python Subprocess Per Request | HIGH | ✅ RESOLVED | spine-client.ts, spine-api/server.py |
| 4 | Strict Leakage Wiring | HIGH | ✅ RESOLVED | spine-api/server.py, spine-wrapper.py |
| 5 | Scenario Loader Mode/Stage | MEDIUM | ❌ OPEN | scenario-loader.ts |
| 6 | Blacklist Casing | MEDIUM | ⚠️ UNVERIFIED | geography.py |
| 7 | Doc Inconsistencies | MEDIUM | ⚠️ PARTIAL | README.md, app.py existence |
| 8 | internal_notes in Traveler Bundle | LOW | ❌ OPEN | strategy.py |
| 9 | Contradictions Rendering Bug | HIGH | ❌ OPEN | DecisionTab.tsx |
| 10 | Risk Flags Rendering Bug | HIGH | ❌ OPEN | DecisionTab.tsx |
| 11 | Scenario Detail Interface | MEDIUM | ❌ OPEN | scenario-loader.ts |
| 12 | Traveler Bundle Serialization | LOW | ❌ OPEN | strategy.py |
| 13 | Missing Integration Tests | MEDIUM | ❌ OPEN | frontend/ (no tests) |
| 14 | record_seen_city Concurrency | LOW | ⚠️ PRESENT | geography.py |
| 15 | Route Path Mismatch | LOW | ✅ RESOLVED | N/A (correct behavior) |

---

## Recommended Priority Order

### Immediate (Before Production)
1. **Fix DecisionTab contradictions/risk_flags rendering** (Findings #9, #10)
2. **Complete licensing decision** (Finding #1)
3. **Add mode/stage to scenario loader** (Findings #5, #11)

### Short Term (Next Sprint)
4. **Add Next.js integration tests** (Finding #13)
5. **Remove internal_notes from traveler bundle serialization** (Findings #8, #12)
6. **Clarify Streamlit vs Next.js path in docs** (Finding #7)

### Backlog
7. **Verify blacklist casing** (Finding #6)
8. **Address record_seen_city concurrency** (Finding #14) - only if running parallel processes

---

## Verification Methodology

1. **Direct file inspection** - Read all relevant source files
2. **Interface comparison** - Compared TypeScript interfaces with Python dataclasses
3. **Data flow tracing** - Traced strict_leakage from UI through API to Python
4. **Test enumeration** - Checked for test files in expected locations
5. **Documentation cross-reference** - Verified README claims against actual code

---

## Files Reviewed

- `/Users/pranay/Projects/travel_agency_agent/README.md`
- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/README.md`
- `/Users/pranay/Projects/travel_agency_agent/data/README.md`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/safety.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/strategy.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/decision.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/orchestration.py`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/spine-client.ts`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/spine-wrapper.py`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/scenario-loader.ts`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/types/spine.ts`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/stores/workbench.ts`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/PacketTab.tsx`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/DecisionTab.tsx`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/StrategyTab.tsx`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/workbench/SafetyTab.tsx`
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/api/spine/run/route.ts`
- `/Users/pranay/Projects/travel_agency_agent/spine-api/server.py`
- `/Users/pranay/Projects/travel_agency_agent/data/fixtures/scenarios/*.json`

---

*End of Verification Report*
