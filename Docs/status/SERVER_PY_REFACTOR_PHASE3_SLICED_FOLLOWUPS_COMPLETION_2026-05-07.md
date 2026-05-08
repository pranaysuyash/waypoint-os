# SERVER_PY_REFACTOR_PHASE3_SLICED_FOLLOWUPS_COMPLETION_2026-05-07

Status: COMPLETE (Slice D only)
Date: 2026-05-08
Scope boundary respected: no Slice E work started.

## 1) Implemented Slice D route movement

Moved routes (and only these routes) out of `spine_api/server.py`:
- `GET /followups/dashboard`
- `PATCH /followups/{trip_id}/mark-complete`
- `PATCH /followups/{trip_id}/snooze`
- `PATCH /followups/{trip_id}/reschedule`

New router module:
- `spine_api/routers/followups.py`

Router shape verification:
- `router = APIRouter()` present (no prefix, no tags, no router-level dependencies)
- Endpoint-level dependency preserved: `Depends(get_current_agency)`

## 2) Behavior parity details preserved

Preserved semantics from in-file handlers:
- same query parameters and defaults
- same HTTP status/detail strings for error branches
- same audit event types/actor/payload keys
- same update payload keys for TripStore updates

Critical filesystem path semantic preserved for dashboard:
- route now resolves using `Path(__file__).resolve().parents[2] / "data" / "trips"`
- this preserves repo-root `data/trips` target after module move

## 3) server.py wiring updates

`spine_api/server.py` changes:
- Normal import path added: `from routers import followups as followups_router` (line ~288)
- Fallback importlib path added:
  - `_followups_spec = importlib.util.spec_from_file_location(...)` (line ~332)
  - module exec + assignment to `followups_router`
- Router include added: `app.include_router(followups_router.router)` (line ~579)
- Removed the 4 original in-file followups handlers from `server.py`

## 4) Added router behavior tests

Created:
- `tests/test_followups_router_behavior.py`

Coverage included:
- dashboard: agency filtering + due-date sort + malformed JSON fail-soft handling
- mark-complete: success, 404 not found, 400 no scheduled follow-up
- snooze: success, invalid days, invalid due-date format
- reschedule: success, invalid date format
- audit assertions for success paths

## 5) Required verification matrix + legacy followup tests

Executed command:

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_server_route_parity.py \
  tests/test_server_openapi_path_parity.py \
  tests/test_server_startup_invariants.py \
  tests/test_followups_router_behavior.py \
  tests/test_phase5_followup_api.py -q
```

Result:
- `48 passed in 4.74s`

Legacy test status:
- `tests/test_phase5_followup_api.py`: PASSED in this matrix run
- No classification needed (no failures to classify)

## 6) Snapshot and import safety checks

Route/OpenAPI snapshot check executed:

```bash
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py
```

Result:
- `route_count = 129`
- `openapi_path_count = 113`

Forbidden import check executed:

```bash
grep -n "from spine_api.server\|import server" spine_api/routers/followups.py || true
```

Result:
- no matches

## 7) Scope guard confirmation

Not changed in this slice:
- public checker
- agent runtime
- team routes
- `/trips`
- analytics core
- drafts/settings/documents/booking collection
- `/run`, `/runs`
- startup/lifespan/app factory/middleware

Slice D complete. Stopped before Slice E.
