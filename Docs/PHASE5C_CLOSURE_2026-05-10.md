# Phase 5C Closure — 2026-05-10

## What changed

Phase 5C backfills document and extraction lifecycle events into the execution event ledger established in Phase 5B. The `execution_events` table already existed; Phase 5C adds the emission code.

### Files modified

| File | Change |
|------|--------|
| `spine_api/models/tenant.py` | Added `DOCUMENT_EVENT_TYPES`, `EXTRACTION_EVENT_TYPES`, `ALLOWED_SUBJECT_TYPES`, `ALLOWED_EVENT_SOURCES`. Expanded `ALLOWED_EVENT_METADATA_KEYS` (18 new keys). Added `filename_hash`, `sha256`, `error_summary`, `confidence_scores`, `raw_error` to `FORBIDDEN_METADATA_PATTERNS`. |
| `spine_api/services/execution_event_service.py` | Added `emit_event_best_effort()` using `db.begin_nested()` savepoint for session isolation. Strengthened `_validate_metadata()` to enforce allowlist (unknown keys rejected) in addition to denylist. |
| `spine_api/services/document_service.py` | 4 emission points: upload, accept, reject, soft_delete. Customer upload mapped to `actor_type=system, source=customer_submission`. |
| `spine_api/services/extraction_service.py` | 7 emission points: run_started, run_completed, run_failed, attempt_completed, attempt_failed, applied, rejected. Fixed extractor initialization order. |
| `frontend/.../ExecutionTimelinePanel.tsx` | 14 new event type labels, 8 new status icons/colors, subject type label cleanup. |
| `frontend/.../IntakeFieldComponents.test.tsx` | Added `value: null` to PlanningDetailRow mocks (pre-existing TS error). |

### Files created

| File | Tests |
|------|-------|
| `tests/test_document_events.py` | 15 tests: constants, actor mapping (5 integration), PII boundaries (2), best-effort isolation (4), category validation |
| `tests/test_extraction_events.py` | 38 tests: constants (7), actor mapping (3 integration), PII boundaries (15), subject types (2), metadata structure (5), best-effort (2), allowlist enforcement (5), PII sentinel (1) |

## Blockers found during review

### Blocker 1: `emit_event_best_effort` poisoned the DB session

**Problem**: Initial implementation used `try/except + db.rollback()`. After a failed event insert, `rollback()` undid the session state including previously committed document rows. Calling code then hit `DetachedInstanceError`.

**Fix**: Changed to `async with db.begin_nested()` (SQLAlchemy savepoint). Event insert failure rolls back only the savepoint, leaving the caller's session intact.

### Blocker 2: `_validate_metadata` only checked denylist, not allowlist

**Problem**: Unknown metadata keys (e.g., `customer_email`) were not rejected. Only keys matching `FORBIDDEN_METADATA_PATTERNS` were blocked.

**Fix**: Added allowlist enforcement — every metadata key must be in `ALLOWED_EVENT_METADATA_KEYS`. Unknown keys are rejected before the forbidden-pattern check.

### Blocker 3: `run_extraction` referenced `extractor` before assignment

**Problem**: `extraction_run_started` event emission called `_get_model_chain(extractor)` before `extractor = get_extractor()` was assigned. Runtime `NameError`.

**Fix**: Moved extractor initialization and model chain resolution before the event emission.

### Blocker 4: Placeholder tests with `assert True` and `pass`

**Problem**: `test_run_started_uses_system_actor` contained `assert True` placeholder. `test_accept_succeeds_when_event_emission_fails` had a `pass` path instead of testing real behavior.

**Fix**: Replaced with real integration tests using proper mocks for `begin_nested()` savepoint.

### Blocker 5: TypeScript PlanningDetailRow missing `value`

**Problem**: `IntakeFieldComponents.test.tsx` had mock objects missing the `value` property required by `PlanningDetailRow` type.

**Fix**: Added `value: null` to budget and origin rows.

## Fixes applied

1. `emit_event_best_effort`: savepoint isolation via `db.begin_nested()`
2. `_validate_metadata`: allowlist enforcement before denylist check
3. `extraction_service.py`: extractor initialization moved before `extraction_run_started` emission
4. `tenant.py`: added `filename_hash` and `sha256` to `FORBIDDEN_METADATA_PATTERNS`
5. Test files: replaced placeholders with real integration tests
6. `IntakeFieldComponents.test.tsx`: added `value: null`

## Final test outputs

### Backend

```
tests/test_document_events.py          15 passed
tests/test_extraction_events.py        38 passed
tests/test_confirmation_service.py     30 passed
tests/test_execution_event_service.py  26 passed
tests/test_vision_extraction.py        18 passed
tests/test_extraction_attempts.py      17 passed
──────────────────────────────────────────────────
Total backend                         149 passed
```

### Frontend

```
TypeScript: 0 errors
Test Files: 87 passed (87)
Tests:      790 passed (790)
```

## Privacy invariants

These values must never appear in `execution_events.event_metadata`:

- `filename` — original filename not stored anywhere in the system
- `filename_hash` — could identify documents
- `sha256` — file fingerprint
- `storage_key` — internal storage path
- `signed_url` — temporary access URL
- `extracted_fields` — encrypted PII (names, passport numbers, DOB)
- `confidence_scores` — per-field confidence dict (field names reveal document content categories)
- `error_summary` — may contain provider error details with PII context
- `raw_error` — uncontrolled provider error text
- Field names from `fields_to_apply` — reveal what was extracted

Enforcement: dual-layer validation in `_validate_metadata()`:
1. Allowlist: key must be in `ALLOWED_EVENT_METADATA_KEYS`
2. Denylist: key must not match any pattern in `FORBIDDEN_METADATA_PATTERNS` (exact + substring)

## Historical backfill note

Events start from Phase 5C forward. No historical backfill. Documents and extractions created before Phase 5C deployment will not have execution events in the timeline.
