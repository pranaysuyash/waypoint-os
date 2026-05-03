# Test Isolation Fix - Phase 2 Call-Capture Structured Fields

**Date**: 2026-05-03
**File**: `tests/test_call_capture_phase2.py`
**Status**: Fixed

---

## Problem

`test_call_capture_phase2.py` was flaky - it failed intermittently when run as part of the full
pytest suite (`pytest tests/ -x`) but passed reliably in isolation.

### Root cause

The test creates trips with **hardcoded IDs** (`trip_patch_canonical_sync`) via
`TripStore.save_trip()`. Since the project uses a `FileTripStore` backend by default
(persisting to `data/trips/`), those hardcoded IDs collide with stale state from previous
runs or other tests in the full suite.

The `conftest.py` `reset_global_singletons` fixture resets in-memory singletons, but
**does not clean up on-disk trip JSON files**. Other test files (e.g. `test_call_capture_e2e.py`)
work around this by monkeypatching `TRIPS_DIR` to a temp directory, but `test_call_capture_phase2.py`
did not.

### Failure pattern

```python
trip_id = "trip_patch_canonical_sync"
TripStore.save_trip({...}, agency_id=AGENCY_ID)
# Later in the same or another test:
TripStore.get_trip("trip_patch_canonical_sync")
# May return stale data from a previous run or a different test
```

## Fix

Added an `autouse` fixture `_cleanup_phase2_trips` that:

1. Sets `DATA_PRIVACY_MODE=test` so `check_trip_data` doesn't reject the test data
2. Deletes the specific trip JSON files after each test

```python
_TEST_TRIP_IDS = frozenset({
    "trip_patch_canonical_sync",
    "trip_patch_priorities_flex",
    "trip_patch_clear_warnings",
})

@pytest.fixture(autouse=True)
def _cleanup_phase2_trips():
    original_mode = os.environ.get("DATA_PRIVACY_MODE", "dogfood")
    os.environ["DATA_PRIVACY_MODE"] = "test"
    yield
    os.environ["DATA_PRIVACY_MODE"] = original_mode
    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    for trip_id in _TEST_TRIP_IDS:
        trip_file = TRIPS_DIR / f"{trip_id}.json"
        if trip_file.exists():
            try:
                trip_file.unlink()
            except OSError:
                pass
```

## Why not monkeypatch TRIPS_DIR?

Monkeypatching `TRIPS_DIR` at the module level would change the path for all tests in
the file, but `FileTripStore` methods are called via the `TripStore` facade which
reads the global `TRIPS_DIR` at runtime. Since the `session_client` fixture creates
a single FastAPI app for the whole session, and some tests call the app directly while
others call `TripStore` methods directly, a simple monkeypatch inside a test function
would be inconsistent. The cleanup approach is safer.

## Future prevention

- Prefer `monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path / "trips")` for tests
  that create persistent trip data
- Or use `_cleanup_phase2_trips` pattern for tests with hardcoded IDs
- Consider adding a session-scoped `tmp_path` TRIPS_DIR fixture to `conftest.py`
  (but this would require monkeypatching the module before any `server.py` import)

## Verification

```bash
# Before fix: intermittent failure at ~test #1380
# After fix:  1402 passed, 9 skipped in full suite
```
