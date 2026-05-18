# Issue Review: "Add Dates" Button Not Functional

**Status**: RESOLVED ✓  
**Date**: 2026-05-16  
**Investigation Method**: Full stack analysis + end-to-end testing

---

## Summary

The "Add dates" button in the Travel Window section was reported as non-functional. After comprehensive investigation and testing, the root cause has been identified and **fixed in commit e9c31aa** (May 1, 2026).

---

## Root Cause Analysis

### The Bug

When a user clicked "Add dates" and entered a travel window value, the field appeared to save but immediately reverted on page reload, creating an infinite loop where the button kept reappearing.

### Architecture Mismatch

The backend stored the dateWindow value in the nested `extracted.facts.date_window` structure (with confidence/authority metadata) but **did not** expose it at the top level of the Trip response. Meanwhile, the frontend adapters only read from the nested extracted field, missing the top-level canonical field entirely.

**Data Flow Failure**:
1. Frontend PATCH: `{"dateWindow": "June 15-22, 2026"}`
2. Backend: Stored in `extracted.facts.date_window` with authority_level="explicit_user"
3. Backend response: Included ONLY in `extracted.facts`, NOT at top level
4. Frontend adapter: Only read from `extracted.facts.date_window.value`, never checked top-level `dateWindow`
5. Frontend logic: `trip.dateWindow` was still undefined → "Add dates" button reappeared

### Adapter-Level Issue

The function `dateWindowValue()` in `frontend/src/lib/bff-trip-adapters.ts` (line ~35) was the critical point of failure:

```javascript
// BEFORE (broken)
function dateWindowValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.date_window.value", undefined),
    extractedValue(spineTrip, "date_window", undefined),
    "TBD"
  );
}

// AFTER (fixed)
function dateWindowValue(spineTrip: unknown): unknown {
  return firstPresent(
    getNestedValue(spineTrip, "extracted.facts.date_window.value", undefined),
    extractedValue(spineTrip, "date_window", undefined),
    getNestedValue(spineTrip, "dateWindow", undefined),  // ← Added
    "TBD"
  );
}
```

---

## The Fix (Commit e9c31aa)

**Author**: Pranay Suyash  
**Date**: May 1, 2026  
**Files Changed**: 25 files (+1624/-280 lines)

### Backend Changes

**spine_api/server.py** (+74 lines):
- Added `_sync_manual_trip_fields()` function that syncs manual field updates into the `extracted.facts` structure AND clears matching validation warnings
- Ensures the response is internally consistent when a user manually updates fields like dateWindow

### Frontend Adapter Fixes

**frontend/src/lib/bff-trip-adapters.ts**:
- **dateWindowValue**: Added fallback to check top-level `dateWindow` field before defaulting to "TBD"
- **destinationValue**: Added fallback to check top-level `destination` field before "Unknown"
- **budget**: Now reads `budget_raw_text.value` first (user-provided text) before falling back to parsed budget

### Frontend State Management

**frontend/src/components/workspace/panels/IntakePanel.tsx** (+185/-48):
- Added 'dates' to the PlanningDetailId type
- Added Travel Window to the Missing Customer Details panel
- Added deep-link support via `?field=dateWindow` URL parameter
- Unified editor state management for all field types

---

## Verification

### Testing Performed (2026-05-16)

**Environment**: Localhost instance running current master branch  
**Test Case**: Add travel window to existing trip (trip_5c823c0cb6a3)

**Steps**:
1. Navigated to `/trips/trip_5c823c0cb6a3/intake`
2. Clicked "Add dates" button
3. Entered "June 15-22, 2026"
4. Clicked save button
5. Observed PATCH request: `{"dateWindow":"June 15-22, 2026"}`
6. Verified API response included date at top level
7. Reloaded page
8. Confirmed "June 15-22" displayed on trip card and in Trip Details panel
9. Confirmed "Add dates" button is NO LONGER visible (field treated as complete)

**Result**: ✅ PASS - The fix works correctly

### Network Evidence

**PATCH Request**:
```json
{"dateWindow":"June 15-22, 2026"}
```

**Response** (relevant fields):
```json
{
  "id": "trip_5c823c0cb6a3",
  "dateWindow": "June 15-22, 2026",
  "packet": {
    "facts": {
      "date_window": {
        "value": "June 15-22, 2026",
        "confidence": 1,
        "authority_level": "explicit_user"
      }
    }
  },
  ...
}
```

---

## Implementation Details

### Field Reconstruction Pattern

The fix implements a three-tier fallback pattern for all manual-edit-prone fields:

```javascript
function fieldValue(trip: unknown): unknown {
  return firstPresent(
    getNestedValue(trip, "extracted.facts.field_name.value", undefined),  // AI extraction
    extractedValue(trip, "field_name", undefined),                         // Legacy format
    getNestedValue(trip, "fieldName", undefined),                          // Top-level canonical
    defaultValue                                                           // Fallback
  );
}
```

This ensures that:
1. AI-extracted values are prioritized
2. Legacy formats are respected
3. Manual user edits (stored at top level) are never lost
4. No field disappears due to missing adapter logic

### Related Fields Fixed

The same pattern was applied to:
- **destinationValue**: Resolves to top-level `destination` if no extraction
- **budget**: Resolves to top-level parsed budget or raw_text if no extraction  
- **originCityValue**: Resolves to top-level `origin` if no extraction

---

## Impact

### Before the Fix
- Users could not persist manual trip details through the intake form
- The "Add dates", "Add origin", "Add budget" buttons appeared to work but data didn't stick
- Users experienced infinite loops where buttons kept reappearing
- Trust in the system degraded due to apparent data loss

### After the Fix
- All manual field edits persist correctly
- Button states accurately reflect saved data
- Intake workflow is reliable and predictable
- Proper separation of AI extraction (extracted.facts) from manual edits (top-level fields)

---

## Related Artifacts

- **Commit**: e9c31aa (May 1, 2026)
- **Tests**: frontend/src/components/workspace/panels/__tests__/IntakePanel.test.tsx (+106 lines)
- **Documentation**: Multiple planning-status functions updated with detailed comments
- **Regression Tests**: tests/test_call_capture_phase2.py (+76 lines for PATCH sync tests)

---

## Recommendations

1. ✅ **Deployment**: Commit e9c31aa is already on master and tested
2. ✅ **Verification**: No further action needed — the bug is fixed
3. **Documentation**: If this issue recurs, refer to this review for the architectural pattern
4. **Pattern**: Use the three-tier fallback pattern for any other manual edit fields

---

## Notes for Future Work

If additional manual-edit fields need to be added to the system, follow this pattern:
1. Store the user-provided value at the top level of the trip object
2. Also store structured metadata in extracted.facts with confidence/authority
3. In the adapter layer, check: extracted.facts → legacy format → top-level → default
4. Add regression tests to ensure the PATCH/GET round-trip preserves manual edits
