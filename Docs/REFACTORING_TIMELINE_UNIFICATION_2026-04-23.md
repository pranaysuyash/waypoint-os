# Timeline Refactoring: Unified AuditStore Architecture

**Date**: 2026-04-23  
**Status**: ✅ COMPLETE  
**Impact**: High (architectural correctness, eliminated duplicate systems)

---

## Executive Summary

The initial P0-02 implementation created a **parallel timeline logging system** instead of integrating with the existing **AuditStore**. This refactoring unified both systems into a single source of truth, eliminating architectural fragmentation.

### What Changed

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| Event logging | Custom JSONL in `data/logs/trips/{id}.jsonl` | Unified AuditStore | ✅ Integrated |
| Backend emitter | `_emit_timeline_event()` | `_emit_audit_event()` with AuditStore call | ✅ Refactored |
| REST endpoint | Reads from custom JSONL | Reads from AuditStore via unified endpoint | ✅ Updated |
| Frontend | Already called correct endpoint | No changes needed | ✅ Compatible |
| Test suite | JSONL-based tests | AuditStore-based tests | ✅ Updated |

---

## Architectural Problem (Identified by External Review)

### The Gap

1. **Fragmentation**: Auditing logic was scattered across two systems:
   - `src/analytics/review.py` + `AuditStore` (backend audit trail for review actions)
   - Custom `data/logs/trips/` (separate JSONL for spine stage transitions)

2. **Black Box Recorder, No Cockpit**: 
   - AuditStore existed but was never called by the Spine (orchestration)
   - Frontend couldn't see AuditStore events—it pulled from a separate system
   - Result: Spine lifecycle was stateless ("black box"), events were lost

3. **No Unified Timeline API**:
   - No single source of truth for trip history
   - No way to merge operator review events with spine stage transitions
   - Event federation needed, but never implemented

### The Fix

**Single Source of Truth**: Wire Spine to AuditStore + create unified endpoint

1. **Backend Integration** (`src/intake/orchestration.py`):
   - Removed `_emit_timeline_event()` (custom JSONL logging)
   - Added `_emit_audit_event()` → calls `AuditStore.log_event()`
   - All 5 stage transitions now call AuditStore

2. **Unified Endpoint** (`spine_api/server.py`):
   - Updated `GET /api/trips/{trip_id}/timeline`
   - Merged all AuditStore events for the trip
   - Sorted by timestamp, supports `?stage=<stage>` filter

3. **Frontend** (no changes needed):
   - Already calling correct endpoint
   - Compatible with new AuditStore-based response

4. **Tests** (refactored to new model):
   - Unit tests now validate AuditStore integration
   - E2E tests verify Spine emits audit events
   - REST endpoint tests work with unified response

5. **Cleanup**:
   - Removed `data/logs/` directory (old JSONL logs)
   - Removed unused imports and pathlib references

---

## Implementation Details

### Changed Files

| File | Changes | Lines |
|------|---------|-------|
| `src/intake/orchestration.py` | Rewrote event logging function, updated all 5 stage calls | -pathlib, +sys.path |
| `spine_api/server.py` | Updated `/api/trips/{trip_id}/timeline` to use AuditStore | +40 (merged logic) |
| `tests/test_timeline_P0_02.py` | Rewrote all unit tests for AuditStore | 273 → 260 (refactored) |
| `tests/test_timeline_e2e.py` | Rewrote E2E tests to validate audit events | 191 → 150 (simplified) |
| `tests/test_timeline_rest_endpoint.py` | No changes (already generic) | — |

### New Event Structure

Events logged via AuditStore now:

```json
{
  "id": "evt_xyz",
  "type": "spine_stage_transition",
  "user_id": "system",
  "timestamp": "2026-04-23T10:02:49.870+05:30",
  "details": {
    "trip_id": "pkt_abc123",
    "stage": "intake|packet|decision|strategy|safety",
    "state": "extracted|validated|...",
    "decision_type": "gap_and_decision",
    "reason": "Extraction pipeline completed"
  }
}
```

Frontend consumes via REST endpoint:
```json
{
  "trip_id": "pkt_abc123",
  "events": [
    {
      "timestamp": "2026-04-23T...",
      "stage": "intake",
      "state": "extracted",
      "version": "1.0",
      "decision_type": "gap_and_decision",
      "reason": "..."
    }
  ]
}
```

---

## Verification

### Test Results

```
564 tests passing
13 tests skipped
0 test failures
0 regressions
```

**Timeline tests** (14/14 passing):
- ✅ AuditStore append-only semantics
- ✅ Event schema validation
- ✅ Event ordering by timestamp
- ✅ Stage filtering
- ✅ ISO8601 timestamps
- ✅ Spine run emits audit events
- ✅ REST endpoint returns unified response

### Build Status

```
✅ src/intake/orchestration.py — syntax OK
✅ spine_api/server.py — syntax OK
✅ Full test suite — 564 passed
✅ No import errors
✅ No circular dependencies
```

---

## Path Handling Insight

One technical challenge: When `orchestration.py` imports AuditStore, it needs the `spine_api/` directory in sys.path. Solution implemented:

```python
# In _emit_audit_event()
import sys
from pathlib import Path

spine_api_path = str(Path(__file__).resolve().parent.parent.parent / "spine_api")
if spine_api_path not in sys.path:
    sys.path.insert(0, spine_api_path)

from persistence import AuditStore
```

This handles both:
- Running from project root (tests, app)
- Running from subdirectory context

---

## Key Design Decisions

1. **Error Resilience**: Audit failures don't block Spine execution (logged as warning, continue)
2. **Append-Only**: AuditStore already enforces immutability, Spine just appends
3. **Lazy Import**: Import AuditStore only when needed to avoid circular deps at module load
4. **Backward Compatible**: REST endpoint response structure unchanged
5. **Frontend Agnostic**: TimelinePanel doesn't care about backend implementation, works with both

---

## What This Enables

Now that Spine emits events to AuditStore:

✅ **Unified History**: All trip events (stage transitions + operator actions) in one place  
✅ **Compliance**: Complete audit trail, immutable by design  
✅ **Learning**: D1 can now see "what system decided" + "what operator did" together  
✅ **Debugging**: Full lifecycle visible, no stateless black boxes  
✅ **Future Integration**: E2E can replay or inject scenarios into the audit trail  

---

## Outstanding Notes

- **Activity Metadata Accuracy**: Suitability scoring depends on accurate catalog (noted in P0-01 review, deferred to Gap #01)
- **Database Persistence**: P2-01 is a hard blocker for commercial launch, but doesn't affect P0-02/P0-01/P1-02
- **Multi-Tenant Schema**: P2-02 deferred post-Wave A

---

## Checklist

- ✅ Unified event logging (Spine → AuditStore)
- ✅ Updated REST endpoint (AuditStore source)
- ✅ Updated test suite (AuditStore model)
- ✅ Removed custom JSONL system (data/logs/)
- ✅ All tests passing (564/564)
- ✅ No regressions
- ✅ Frontend compatible (no changes needed)
- ✅ Documentation updated (this file)

---

## Files to Preserve

- `Docs/REFACTORING_TIMELINE_UNIFICATION_2026-04-23.md` (this document)
- Updated `src/intake/orchestration.py`
- Updated `spine_api/server.py`
- Updated test files (timeline tests)
