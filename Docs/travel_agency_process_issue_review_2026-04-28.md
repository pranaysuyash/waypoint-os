# Travel Agency Process Issue Review — Git/Stash Recovery and TripStore

Date: 2026-04-28
Status: Recovery implemented and verified

## Executive Summary

This review documents the recovery from a dropped stash and unsafe Git workflow. The dropped stash commit was still available as `443803f45ef0c91cb38bf0e0654280cafbf6bea1`. Its contents were inspected file-by-file and by hunk content. Useful, additive work was selectively recovered; stale, regressive, or incomplete fragments were rejected.

The most important recovery was the TripStore SQL/backend work. The stash direction was valid, but the exact stash implementation was unsafe because it converted the public `TripStore` API to async and had a data-loss branch where `save_processed_trip()` could return a generated trip ID without saving. The recovered implementation keeps the stable sync API, adds explicit async methods, repairs migrations, and verifies both sync and async SQL persistence.

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

## Current Caveats

- `master` is ahead of `origin/master` by two commits created during the recovery window. This review does not claim they were user-approved commits.
- The current worktree also contains unrelated frontend changes outside this recovery scope, including `frontend/src/app/itinerary-checker/page.tsx`.
- `data/assignments/assignments.json` has a newline-only diff. Runtime timestamp churn was rejected and not retained.

## Guardrail

Future agents must not recover this class of work by replaying a stash. The acceptable pattern is:

1. Identify the candidate commit or stash object.
2. Diff against its first parent.
3. Inspect each hunk for content value and regression risk.
4. Merge only the better fragment into the current architecture.
5. Verify with focused tests and document accepted/rejected decisions.
