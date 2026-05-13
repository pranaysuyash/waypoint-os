# Phase 5D Closure — 2026-05-13

## What changed

Phase 5D hardens the execution timeline for daily operator use after Phase 5C's event emission pipeline. Adds backend event integrity validation, corrects `emit_event_best_effort` semantics, adds actor-type filtering, date grouping, and a metadata detail drawer with frontend defense-in-depth.

### Files modified

| File | Change |
|------|--------|
| `spine_api/models/tenant.py` | Added `ALLOWED_ACTOR_TYPES = ("agent", "system")` |
| `spine_api/services/execution_event_service.py` | Added 5 validators (`_validate_subject_type`, `_validate_source`, `_validate_category`, `_validate_event_type_category`, `_validate_actor_type`), `_validate_all` convenience wrapper, extracted `_insert_event_row()` from `emit_event()`. Refactored `emit_event_best_effort()`: validates before savepoint, catches `SQLAlchemyError` only (not generic `Exception`). Fixed `review_notes_present` false positive in metadata substring denylist. Added `actor_type` filter to `get_timeline()`. |
| `spine_api/routers/confirmations.py` | Added `actor_type` and `category` query param validation (422 for invalid). Imports `EVENT_CATEGORIES` from tenant. |
| `spine_api/persistence.py` | Added `TEST_AGENCY_ID` export for test imports. |
| `frontend/src/lib/api-client.ts` | `getExecutionTimeline` accepts optional `actorType` param. |
| `frontend/src/components/workspace/panels/ExecutionTimelinePanel.tsx` | Date grouping, actor filter chips, expandable metadata drawer with `SAFE_METADATA_KEYS` allowlist and `formatMetadataValue` helper. |
| `tests/test_document_events.py` | Updated best-effort test to use `OperationalError` (SQLAlchemyError) instead of generic `Exception`. |
| `tests/test_extraction_events.py` | Updated best-effort test to use `OperationalError` instead of generic `Exception`. |
| `tests/test_booking_documents.py` | Added `flush`, `add`, `begin_nested` mocks for `emit_event_best_effort` savepoint. Updated to import `TEST_AGENCY_ID`. |

### Files created

| File | Tests |
|------|-------|
| `tests/test_event_integrity.py` | 19 tests: subject_type/source/category/actor_type validation (2 each), event_type/category pairing (6 including unknown type and unknown category), `_validate_all` integration (2), best-effort semantics (3 — invalid subject_type raises, invalid metadata raises, DB failure swallowed) |
| `frontend/.../ExecutionTimelinePanel.phase5d.test.tsx` | 11 tests: date grouping (2), actor filter (2), detail drawer (4 — expand, labels, allowlist filtering, PII redaction), empty/error states (2), redaction sentinel (1) |

### Pre-existing TypeScript fixes

| File | Fix |
|------|-----|
| `frontend/src/app/(agency)/workbench/ScenarioLab.tsx` | `setScenarioLabStatus(...)` → `dispatchOp({ type: 'set-status', status: ... })` |
| `frontend/src/components/auth/AuthProvider.tsx` | `setPassword` → `patchLoginForm({ password })`, `setShowPassword` → `patchLoginForm({ showPassword })` |
| `frontend/src/app/api/pipeline/__tests__/route.test.ts` | Mock Trip objects completed with all required fields |

## Key design decisions

### 1. Best-effort semantics: validate before DB, catch DB errors only

Previous code caught generic `Exception` in `emit_event_best_effort`, which swallowed programmer bugs (ValueError from validation). Refactored to:

1. Run all validation BEFORE the savepoint/try block (pure Python, no DB access)
2. Use `begin_nested()` savepoint for DB write isolation
3. Catch `SQLAlchemyError` only — covers OperationalError, IntegrityError, DBAPIError
4. Validation `ValueError` is never caught — it raises to the caller

### 2. `_insert_event_row()` extracted from `emit_event()`

Separate function with no validation, called after validation completes. Used by both `emit_event()` (validate + insert) and `emit_event_best_effort()` (validate + try/savepoint/insert). Avoids double validation and makes the two-step semantics obvious.

### 3. `review_notes_present` metadata allowlist fix

`review_notes_present` is in the allowlist but contains the substring `notes` which is in `FORBIDDEN_METADATA_PATTERNS`. Previous code ran substring check on all keys, causing false positives. Fixed: allowlisted keys skip the substring denylist check — the allowlist represents intentional inclusion of safe boolean indicators.

### 4. Frontend defense-in-depth

Backend enforces metadata allowlist at write time. Frontend adds a second layer: only keys in `SAFE_METADATA_KEYS` (derived from `METADATA_LABELS`) are rendered in the detail drawer. Unknown keys from old rows, test fixtures, or future bugs are silently filtered.

### 5. Router validates query params

Timeline endpoint validates both `actor_type` and `category` query params, returning 422 for invalid values instead of silently returning empty results.

## Final test outputs

### Backend

```
tests/test_event_integrity.py                              19 passed
tests/test_execution_event_service.py                      28 passed
tests/test_document_events.py                              15 passed
tests/test_extraction_events.py                            38 passed
tests/test_confirmation_service.py                         30 passed
────────────────────────────────────────────────────────────────────
Total backend                                            2132 passed, 7 skipped, 1 xfailed
```

### Frontend

```
TypeScript: 0 errors
Test Files: 114 passed (114)
Tests:      896 passed (896)
```

## xfail explanation

```
tests/test_rls_live_postgres.py::test_trips_rls_hides_cross_tenant_rows_for_runtime_role
Reason: "Live runtime role can bypass tenant RLS" — when the configured DB role owns
the tables and FORCE RLS is not enabled, PostgreSQL bypasses row-level security for
the table owner. Dynamically marks xfail via pytest.xfail() when the condition is
detected. Known architecture gap, unrelated to Phase 5D.
```

## Privacy invariants (unchanged from Phase 5C)

These values must never appear in `execution_events.event_metadata`:

- `filename`, `filename_hash`, `sha256`, `storage_key`, `signed_url`
- `extracted_fields`, `confidence_scores`, `error_summary`, `raw_error`
- `supplier_name`, `confirmation_number`, `notes`
- `traveler_name`, `dob`, `passport_number`
- Field names from `fields_to_apply`

Enforcement: dual-layer validation in `_validate_metadata()`:
1. Allowlist: key must be in `ALLOWED_EVENT_METADATA_KEYS`
2. Exact match denylist: key must not be in `FORBIDDEN_METADATA_PATTERNS`
3. Allowlisted keys skip substring denylist (safe booleans like `review_notes_present`)

Frontend adds: `SAFE_METADATA_KEYS` set filters metadata keys before rendering.

## Non-goals preserved

- No new business workflow
- No supplier API, payments, messaging, or customer portal
- No historical data migration
- No changes to event emission logic in document/extraction/confirmation services
- No run grouping within date groups (deferred)
