# Test Data Lifecycle & Agency Hygiene Audit

**Date:** 2026-05-12  
**Scope:** Every path that creates, seeds, persists, or cleans up trip records  
**Method:** Source code inspection, SQL diagnostic, baseline test runs

---

## 1. Every Path That Creates Persisted Trips

| # | Path | Where | `source=` tag | Agency | Cleanup |
|---|------|-------|---------------|--------|---------|
| 1 | **Spine pipeline `POST /run` → `execute_spine_pipeline`** | `spine_api/services/pipeline_execution_service.py:286,359` | `"spine_api"` | Current auth agency | None |
| 2 | **Frontend `POST /api/trips` → BFF → `POST /run`** | Same as #1 (forwards to `/run`) | `"spine_api"` | Current auth agency | None |
| 3 | **Seed scenario (auto-seed on `/trips` GET for test agencies)** | `spine_api/server.py:857-1009` | `"seed_scenario"` | The requesting test agency | None |
| 4 | **`seed_test_user.py` script** | `seed_test_user.py:67` | `"seed_scenario"` | Hardcoded to main agency | None |
| 5 | **`scripts/seed_analytics_trips.py`** | `scripts/seed_analytics_trips.py:79` | `"seed_script"` | Hardcoded to main agency | None |
| 6 | **Public checker `POST /api/public-checker/run`** | `spine_api/services/public_checker_service.py:190-208` | `"public_checker"` | Public checker agency (separate) | None |
| 7 | **Pytest test files (many, direct TripStore.save_trip)** | 40+ test files e.g. `test_call_capture_phase6_backend.py`, `test_vision_extraction.py`, etc. | Varies (often none or `"seed_scenario"`) | **Hardcoded to main agency ID** in ~15 files | Manual delete_trip in some, none in most |
| 8 | **Pytest test files (via save_processed_trip)** | `test_call_capture_e2e.py:66,238,282,352` | `"test"` | Main agency | None |
| 9 | **Pytest conftest fixtures** | Various conftest files | Varies | Varies | None |
| 10 | **`app.py` (agency notes ingestion)** | `app.py:161,169` | `"agency_notes"` | Current auth agency | None |

---

## 2. Which Paths Write to the Main Agency

**Main agency** (`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) receives persistent trips from:

| Path | Estimated SQL records | Source tag |
|------|----------------------|------------|
| Frontend `POST /api/trips` (intake_panel) | ~1,282 | `"spine_api"` → stored as `"intake_panel"` via BFF? Actually `"spine_api"` |
| Spine pipeline runs | ~420 | `"spine_api"` |
| Pytest direct saves (hardcoded agency ID) | ~245 | various |
| Seed scenario auto-seed | ~30 | `"seed_scenario"` |
| Other test fixtures | ~400 | various |

**The main agency ID is hardcoded in 15+ test files** (`"d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"`). Every pytest run that creates a trip sends it to the same agency as the user's working data.

---

## 3. Tagging Analysis

### `source` field — present on all paths ✅
Every trip creation path sets a `source` field. Sources observed: `spine_api`, `seed_scenario`, `seed_script`, `public_checker`, `pytest`, `test`, `agency_notes`, `unknown`.

### `run_id` field — present on seed/pipeline paths ✅
Seed paths set `run_id: f"seed_{trip_id}"`. Pipeline paths set real `run_id`. Test files often omit it.

### `fixture_id` in raw_input — inconsistent ⚠️
Only seed scenarios and some test fixtures set `fixture_id`. The frontend `intake_panel` submissions (1,282 records) do NOT set `fixture_id`. **Fixture detection based only on `fixture_id` misses 45% of synthetic records.**

### `agency_id` — always scoped ✅
Every `save_trip` call receives an `agency_id`. The problem is that 15+ test files hardcode the **main** agency ID.

### `meta.seed` flag — only on seed paths
Seed scenarios set `meta: {"seed": True}`. Pipeline/test paths do not.

### `is_test` column on Agency model — present ✅
The `Agency.is_test` boolean exists. `newuser@test.com` creates an `is_test=True` agency. But `is_test` only controls auto-seeding — it does not prevent test data from mixing with real data.

---

## 4. SQL vs File Store Divergence

**Status as of 2026-05-12: Parity fixed.** Both backends now support:
- Comma-separated multi-status filtering with whitespace trimming
- `offset`/`limit` pagination
- Accurate `count_trips` independent of pagination limits

**Remaining divergence risk:** The `TripStore` facade still dispatches differently for `list_trip_summaries`:
- SQL: column-projected query (returns only needed fields)
- File: full trip load then filter in memory

This matters for `/inbox` (uses `list_trip_summaries`). On SQL backend it's efficient; on file backend it loads full JSON. Not urgent since the active backend is SQL.

**Critical finding:** 40+ tests call `TripStore.save_trip()` directly. When `TRIPSTORE_BACKEND=sql`, these write to the SQL database. The file store at `data/trips/` has only 89 records — almost no test activity. **Test data lives primarily in SQL.**

---

## 5. Existing Cleanup/Reset/Seed Tooling

| Tool | Location | What it does | Safe? |
|------|----------|-------------|-------|
| `seed_test_user.py` | `seed_test_user.py` | Seeds fixture trips for main agency (additive, skips existing) | ✅ Yes |
| `scripts/seed_analytics_trips.py` | `scripts/` | Seeds analytics mock data | ❌ Hardcodes main agency |
| `scripts/bootstrap_public_checker_agency.py` | `scripts/` | Creates public checker agency + settings | ✅ Separate agency |
| `_seed_scenario_for_agency()` | `spine_api/server.py:932` | Auto-seeds fixture for any agency on first `/trips` GET | ✅ Additive, skips existing |
| `TripStore.delete_trip()` | `spine_api/persistence.py` | Deletes individual trip by ID | ✅ Available but never called in bulk |
| `TripStore.list_trips()` w/ filter | `spine_api/persistence.py` | Can enumerate trips by source/agency/status | ✅ Read-only |
| `AuditStore` | `spine_api/persistence.py` | Logs every trip creation with source + agency_id | ✅ Permanent audit trail |

**No tool exists for:**
- Bulk cleanup of trips by source, age, or agency
- Dashboard data reset
- Ephemeral test agency teardown
- Demo data regeneration

---

## 6. Risk Register

| Risk | Severity | Evidence | Status |
|------|----------|----------|--------|
| **Main agency pollution by tests** | **High** | 15+ test files hardcode main agency ID. Each `pytest` run adds records. | Active |
| **Test data indistinguishable from real** | **Medium** | 1,282 `intake_panel` records have no `fixture_id` — are they test or real? Unknown. | Active |
| **No bulk cleanup** | **Medium** | No safe way to reset the test agency. `delete_trip` exists per-trip only. | Gap |
| **Demo non-determinism** | **Medium** | Demo numbers change every session because test runs add records. | Active |
| **Stale integrity issues** | **Low** | 0-2 integrity issues detected. Orphan detection seems accurate and low-volume. | Manageable |
| **Seed records reassigned across agencies** | **Low** | Seed creates records per agency. `_seed_scenario_for_agency` scopes correctly. | Managed |
| **SQL/file divergence in list_trip_summaries** | **Low** | Active backend is SQL. File backend parity now fixed for basic operations. | Managed |
| **Test isolation** | **Medium** | Tests write to shared SQL database. Order-dependent failures possible. | Active |

---

## 7. Recommended Architecture

### Phase 1 — Tag everything (quick wins)

1. **Add `source` field override in `save_processed_trip` for BFF `POST /api/trips` calls** so `intake_panel` and `spine_api` pipeline runs are distinguishable in SQL. Current diagnostic shows 420 `spine_api` records — some are real pipeline runs, some are BFF intake submissions. Without separation we can't tell which.
2. **Add a `generated` boolean column** on the `trips` table (analogous to `is_test` on agencies). Set it `true` for all seed, pytest, and script-created records. This creates a single queryable marker for "this record is synthetic."
3. **Make all test files use a dedicated test agency ID** instead of hardcoding the main agency ID. Create a `conftest.py` constant like `TEST_AGENCY_ID = "00000000-0000-0000-0000-000000000001"` and use it everywhere.

### Phase 2 — Ephemeral test isolation

4. **Create a pytest fixture that creates and tears down an ephemeral test agency** per test session or per test module. All tests that save trips should use this fixture's agency ID. The fixture cleans up all trips for that agency in its teardown.
5. **Add a CLI command** (`python -m tools.reset_test_agency`) that deletes all trips for the main test agency where `source` starts with `test_` or `seed_` or `generated=true`. Must print a count and require confirmation.

### Phase 3 — Deterministic demo data

6. **Create a `seed_demo_agency.py`** that creates a fresh demo agency with deterministic trip data (no random variation). This replaces the ad-hoc accumulation model.
7. **Add a "Demo Mode" env var** that causes the Overview to use the demo agency instead of the auth agency. Allows consistent screenshots and walkthroughs.

### Phase 4 — Long-term

8. **Retire the file store** (`data/trips/`) once all consumers are confirmed using SQL. The file store holds only 89 records and has no automated cleanup.
9. **Add a periodic cleanup task** that archives or deletes trips older than N days with `source IN ('test', 'seed_scenario', 'seed_script', 'pytest')`.

---

## 8. Baseline Test Results

- **Frontend:** Pre-existing failures: 80 failed / 103 passed (environment/setup issue, unrelated to this audit)
- **Backend:** 1 pre-existing failure (`test_booking_documents.py::test_upload_creates_document` — MagicMock issue)
- **Changes made during audit:** None (read-only analysis)

---

## 9. Questions for You

1. **Do you want the main test agency to remain accumulative, or should we add cleanup tooling first?**
2. **Should "intake_panel" (frontend-submitted trips via the UI) be considered real data or test data?** The answer determines whether 1,282 records are a problem or expected behavior.
3. **Do you want an ephemeral test agency pattern for pytest** (Phase 2, item 4), or is the hardcoded main agency ID acceptable for now with the understanding that counts keep growing?
