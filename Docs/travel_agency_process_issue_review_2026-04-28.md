# Travel Agency Process Issue Review — Git/Stash Recovery and TripStore

Date: 2026-04-28
Status: Recovery implemented and verified

## Executive Summary

This review documents the recovery from a dropped stash and unsafe Git workflow. The dropped stash commit was still available as `443803f45ef0c91cb38bf0e0654280cafbf6bea1`. Its contents were inspected file-by-file and by hunk content. Useful, additive work was selectively recovered; stale, regressive, or incomplete fragments were rejected.

The most important recovery was the TripStore SQL/backend work. The stash direction was valid, but the exact stash implementation was unsafe because it converted the public `TripStore` API to async and had a data-loss branch where `save_processed_trip()` could return a generated trip ID without saving. The recovered implementation keeps the stable sync API, adds explicit async methods, repairs migrations, and verifies both sync and async SQL persistence.

This document is also the ledger for changes made during the recovery pass: code, migrations, docs, guardrails, and verification.

## Recovery Rules Applied

- No wholesale stash apply.
- No reset, checkout, restore, clean, stash pop, or stash apply workflow.
- Inspect candidate content before deciding.
- Recover only content that is missing, better, additive, and compatible with the current architecture.
- Reject deleted documentation, stale async rewrites, duplicate route behavior, and unsafe persistence paths.
- Keep documentation of accepted and rejected fragments.

## Stash Content Decision Log

| Area | Decision | Reason |
| --- | --- | --- |
| `spine_api/contract.py` intake metadata | Merged | `follow_up_due_date`, `pace_preference`, `lead_source`, `activity_provenance`, and `date_year_confidence` were referenced elsewhere but forbidden by the request contract. |
| Frontend generated spine types | Merged | Kept frontend request contract aligned with backend `SpineRunRequest`. |
| `spine_api/server.py` envelope metadata | Merged | Structured intake metadata now reaches the canonical envelope path instead of being dropped. |
| `src/intake/extractors.py` raw destination matches | Merged | Prevents returning raw matches from rejected origin/label tokens. |
| `src/analytics/metrics.py` empty-data analytics | Merged | Avoids fake nonzero velocity and response-time metrics when there are no trips. |
| `spine_api/models/__init__.py` Trip import | Merged | Ensures Alembic model discovery includes `Trip`. |
| `pyproject.toml` / `uv.lock` cryptography dependency | Merged | Required by the existing encryption utility and SQL TripStore path. |
| Stash async TripStore rewrite | Rejected as-is | It converted the public API to async, left many sync call sites behind, and could return unsaved trip IDs. |
| Stash feedback/dashboard stubs | Rejected | Partial endpoints with placeholder bodies; not comprehensive. |
| Assignment timestamp churn | Rejected | Runtime seed timestamp change, not semantic work. |
| `/api/trips` mock-to-run rewrite | Deferred | Valuable direction, but route ownership must be resolved against canonical `/run` and `/api/spine/run` paths before changing. |

## Changes and Improvements Implemented

### Contract and Intake Metadata

- Added intake metadata fields to `SpineRunRequest`: `follow_up_due_date`, `pace_preference`, `lead_source`, `activity_provenance`, and `date_year_confidence`.
- Updated generated frontend spine types so frontend calls can send those fields without type drift.
- Added structured envelope propagation for those metadata fields in `build_envelopes()`.
- Added intake extractor field mappings so imported structured payloads preserve the same metadata.

### Extraction and Analytics Correctness

- Fixed destination extraction raw-match reporting so rejected origin/label tokens are not returned as the raw destination match.
- Recovered empty-data analytics handling so zero trips produce zero velocity, zero response time, and zero pipeline value instead of fake nonzero metrics.
- The broader analytics recovery in the current branch computes pipeline velocity from trip timestamps where possible.

### TripStore and Persistence

- Added SQL-backed `SQLTripStore` while preserving the existing synchronous `TripStore` facade.
- Added explicit async methods: `asave_trip`, `aget_trip`, `alist_trips`, and `aupdate_trip`.
- Added `save_processed_trip_async()` for future async call sites.
- Made SQL mode explicit with `TRIPSTORE_BACKEND=sql`; file/JSON mode remains the default.
- Kept the shared app database engine pooled for normal app traffic.
- Added a TripStore-specific SQL engine using `NullPool` so sync facade calls do not reuse asyncpg connections across event loops.
- Added SQL field-level encryption/decryption for common and travel-specific PII fields.
- Preserved dogfood privacy guard checks on the file store path.

### Alembic and Database

- Fixed `alembic/env.py` so Alembic imports from the project root and uses `spine_api.models.Base`.
- Registered `Trip` in `spine_api/models/__init__.py` for Alembic discovery.
- Fixed `create_trips_table_v1.py` syntax and migration ordering.
- Made the membership migration idempotent because the live database already had some columns while Alembic's version table lagged.
- Made the follow-up migration idempotent when the column already exists.
- Ran the live database to Alembic head: `add_follow_up_due_date`.

### Audit Store Recovery

- Hardened `AuditStore._load_events()` so corrupt `data/audit/events.json` no longer breaks trip persistence.
- Corrupt audit files are archived with a `.corrupt-YYYYMMDDTHHMMSSZ.json` suffix.
- Audit writes now use the existing `file_lock()` helper.

### Documentation and Guardrails

- Added this issue review at `Docs/travel_agency_process_issue_review_2026-04-28.md`.
- Updated `Docs/P1_VERIFICATION_COMPLETE_2026-04-28.md` to remove stale `asyncio.run()` guidance and point to this recovery record.
- Updated repo-local `AGENTS.md` with the user's work-quality preference:
  - current compatibility is necessary but not sufficient;
  - solutions should be elegant, first-principles, scalable, long-term, better, comprehensive, architecturally correct, vision-oriented, and open to updates.
- Updated `/Users/pranay/Projects/AGENTS.md` with the same working-style rule at Projects level.

## Files Touched by Recovery

Code and migrations:

- `spine_api/contract.py`
- `spine_api/server.py`
- `spine_api/persistence.py`
- `spine_api/core/database.py`
- `spine_api/models/__init__.py`
- `src/analytics/metrics.py`
- `src/intake/extractors.py`
- `frontend/src/types/generated/spine-api.ts`
- `frontend/src/types/generated/spine_api.ts`
- `pyproject.toml`
- `uv.lock`
- `alembic/env.py`
- `alembic/versions/a1b2c3d4e5f6_add_capacity_specializations_status_to_memberships.py`
- `alembic/versions/add_follow_up_due_date_to_trips.py`
- `alembic/versions/create_trips_table_v1.py`
- `tests/test_call_capture_e2e.py`

Documentation and instruction files:

- `Docs/travel_agency_process_issue_review_2026-04-28.md`
- `Docs/P1_VERIFICATION_COMPLETE_2026-04-28.md`
- `AGENTS.md`
- `/Users/pranay/Projects/AGENTS.md`

## TripStore Recovery Architecture

The recovered TripStore implementation keeps a compatibility facade:

- `TripStore.save_trip`, `get_trip`, `list_trips`, and `update_trip` remain synchronous for existing file-mode callers and tests.
- `TripStore.asave_trip`, `aget_trip`, `alist_trips`, and `aupdate_trip` provide explicit async entry points for SQL-backed async callers.
- `save_processed_trip()` remains the sync convenience function.
- `save_processed_trip_async()` is available for FastAPI/background paths that are already async.
- SQL mode is explicit via `TRIPSTORE_BACKEND=sql`; file/JSON remains the default dogfood mode.

The SQL TripStore uses a dedicated async engine with `NullPool`. This isolates the sync facade's `asyncio.run()` calls from asyncpg loop-bound connection reuse. The shared app database engine keeps normal pooling in `spine_api/core/database.py`, so the fix does not degrade unrelated database traffic.

## Migration Recovery

The database should have a `trips` table for SQL TripStore mode. It was missing because the migration chain was broken:

- `alembic/env.py` inserted the `spine_api` directory into `sys.path`, which broke `spine_api` imports under Alembic.
- `alembic/versions/create_trips_table_v1.py` had escaped triple quotes, making it syntactically invalid.
- The migration graph had competing children after `10a6e1336ba4`.
- The memberships migration was not idempotent, but the database already had those columns.

Recovered state:

- Alembic imports `Base` from `spine_api.models`.
- `Trip` is registered in the model registry.
- The migration graph has one head: `add_follow_up_due_date`.
- `uv run alembic upgrade head` completed.
- `uv run alembic current` reports `add_follow_up_due_date (head)`.

## Privacy and Audit Hardening

TripStore SQL encryption coverage was expanded beyond generic field names. Protected keys now include travel-specific fields such as `traveler_name`, `traveler_email`, `traveler_phone`, `passport_number`, `medical_notes`, `dietary_restrictions`, and `special_requests`.

`AuditStore` now treats corrupt `data/audit/events.json` as recoverable. If JSON decoding fails, the corrupt file is archived with a timestamped `.corrupt-YYYYMMDDTHHMMSSZ.json` suffix and a fresh log starts. Audit writes now use the repo's file-lock helper.

## Verification Evidence

Commands run:

```bash
python -m py_compile spine_api/core/database.py spine_api/persistence.py spine_api/server.py tests/test_call_capture_e2e.py
git diff --check
uv run pytest -q tests/test_call_capture_e2e.py tests/test_privacy_guard.py tests/test_review_policy_escalation.py
uv run alembic heads
uv run alembic current
```

Results:

- Focused tests: `45 passed`
- Alembic head: `add_follow_up_due_date (head)`
- SQL sync probe: persisted and read back a trip with `follow_up_due_date`.
- SQL async probe: persisted and read back a trip with `follow_up_due_date`.

Additional verification during the pass:

- `python -m py_compile spine_api/contract.py spine_api/server.py src/analytics/metrics.py src/intake/extractors.py spine_api/models/__init__.py`
- `python -m py_compile spine_api/core/database.py spine_api/persistence.py spine_api/server.py tests/test_call_capture_e2e.py`
- `uv run pytest -q tests/test_call_capture_e2e.py tests/test_privacy_guard.py tests/test_review_policy_escalation.py`
- `TRIPSTORE_BACKEND=sql DATA_PRIVACY_MODE=beta` sync probe persisted and read back SQL trips.
- `TRIPSTORE_BACKEND=sql DATA_PRIVACY_MODE=beta` async probe persisted and read back SQL trips.
- `git diff --check` passed after the recovery edits.

## Current Caveats

- At the latest read-only check, `master` was ahead of `origin/master` by four commits. This review does not claim those commits were user-approved by this assistant.
- The current worktree contains unrelated dirty files outside this recovery scope. Examples observed during the pass included frontend/design files and `spine_api/models/frontier.py`.
- `data/assignments/assignments.json` had only a newline-only diff after runtime timestamp churn was rejected.
- The remaining stash `stash@{0}: pre-design-review-wip` was not dropped or applied by this assistant.

## Guardrail

Future agents must not recover this class of work by replaying a stash. The acceptable pattern is:

1. Identify the candidate commit or stash object.
2. Diff against its first parent.
3. Inspect each hunk for content value and regression risk.
4. Merge only the better fragment into the current architecture.
5. Verify with focused tests and document accepted/rejected decisions.
