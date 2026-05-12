# App Performance Review — 2026-05-12

## Scope

Investigated local app slowness across the running Waypoint OS frontend (`:3000`) and backend (`:8000`) using authenticated runtime checks and targeted backend timing probes.

## Findings

1. Missing local OpenTelemetry collectors were creating request-time backpressure.
   - Backend defaulted `OTEL_EXPORTER_OTLP_ENDPOINT` to `http://localhost:4317`.
   - Frontend defaulted `OTEL_EXPORTER_OTLP_ENDPOINT` to `http://localhost:4318/v1/traces`.
   - Local logs repeatedly showed OTLP export failures and deadline exceeded errors.

2. TripStore SQL reads used `NullPool`, forcing new database connections for repeated TripStore calls.
   - Earlier architecture notes used `NullPool` to prevent asyncpg connection reuse across event loops.
   - Current TripStore implementation already creates one engine/sessionmaker per event loop, so normal pooling can be safely scoped per loop.

3. Summary endpoints were reading full trip records, including encrypted/private blobs not needed by list views.
   - `/inbox`, `/inbox/stats`, `/analytics/summary`, and `/analytics/pipeline` only need projection/list fields.
   - Full detail reads remain available through existing `TripStore.list_trips()` and `TripStore.get_trip()`.

## Changes

- Made OpenTelemetry export opt-in for backend and frontend; traces are enabled only when `OTEL_EXPORTER_OTLP_ENDPOINT` is explicitly set.
- Changed the TripStore SQL engine from `NullPool` to per-event-loop pooled connections (`pool_size=10`, `max_overflow=5`).
- Added `TripStore.list_trip_summaries()` for projection/list views.
- Routed inbox and analytics summary/pipeline reads through the summary path.

## Measurement Evidence

Baseline before fixes:

- Backend `/health`: ~34ms.
- Frontend root: ~603ms on first probe.
- `/api/inbox?page=1&limit=1`: ~403ms average.
- `/api/pipeline`: ~627ms average, max ~1508ms.
- `TripStore.list_trips(... inbox statuses, limit=5000)`: ~786ms average for 1648 rows.

After fixes and server restart:

- `/overview`: ~54ms average.
- `/trips`: ~48ms average.
- `/workbench?draft=new&tab=safety`: ~47ms average.
- `/api/inbox?page=1&limit=1`: ~319ms average for ~1678 rows.
- `/api/inbox/stats`: ~125ms average.
- `/api/pipeline`: ~227ms average.
- `TripStore.list_trips(... inbox statuses, limit=5000)`: ~204ms average.
- `TripStore.list_trip_summaries(... inbox statuses, limit=5000)`: ~128ms average.

## Verification

- `python tools/runtime_smoke_matrix.py --preflight-local-stack` passed.
- `uv run pytest tests/test_call_capture_phase2.py tests/test_drafts_router_contract.py tests/test_settings_router_contract.py tests/test_server_startup_invariants.py -q` passed: 38 tests.
- `npm run typecheck` passed in `frontend/`.

## Remaining Hotspot

`/api/inbox?page=1&limit=1` still computes projection, sorting, and filter counts across the full inbox dataset so tab counts stay correct. At ~1.7k inbox rows this remains the slowest measured user-facing API. The next durable improvement is to split count computation from page projection:

- use SQL aggregate counts for stable tab/status counts,
- project only the requested page when no computed-field filters require full projection,
- keep full projection only for search/sort modes that cannot yet be pushed into SQL.
