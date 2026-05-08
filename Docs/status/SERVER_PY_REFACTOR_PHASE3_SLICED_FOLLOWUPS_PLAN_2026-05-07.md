# Server.py Refactor Phase 3 — Slice D Followups Plan (Plan Only)

Date: 2026-05-07
Status: Plan-only checkpoint
Implementation starts only after approval.

Hold before next slice: enabled.

## Objective
Move only the followup route group out of `spine_api/server.py` into a dedicated router module while preserving behavior exactly.

Target routes:
- GET /followups/dashboard
- PATCH /followups/{trip_id}/mark-complete
- PATCH /followups/{trip_id}/snooze
- PATCH /followups/{trip_id}/reschedule

## Planned router module
- New file: `spine_api/routers/followups.py`
- Router shape:
  - `router = APIRouter()`
  - no prefix
  - no tags
  - no router-level dependencies
  - preserve endpoint-level `Depends(get_current_agency)` on all four handlers

## 1) Exact routes to move
1. `GET /followups/dashboard`
2. `PATCH /followups/{trip_id}/mark-complete`
3. `PATCH /followups/{trip_id}/snooze`
4. `PATCH /followups/{trip_id}/reschedule`

No other route movement is in scope.

## 2) Current behavior to preserve per route

### A. GET /followups/dashboard
Current behavior:
- Reads trip JSON files directly from filesystem path computed from server file location:
  - `Path(__file__).parent.parent / "data" / "trips"`
- Iterates `*.json`, best-effort reads, and silently skips malformed/unreadable files.
- Filters trips by `trip.get("agency_id") == agency.id`.
- Includes only records with `follow_up_due_date`.
- Parses due date via `datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))`; skips invalid values.
- Optional query filters:
  - `status` (pending|completed|snoozed, or any exact string currently present)
  - `filter` values: `due_today`, `overdue`, `upcoming`
- Computes `days_until_due` as `(due_date.date() - now.date()).days`.
- Sorts ascending by `due_date` string key.
- Returns:
  - `{ "items": [...], "total": len(items) }`

HTTPException behavior:
- No explicit HTTPException branch in this route today.
- Preserve current fail-soft behavior (skip bad files/records, return aggregate list).

### B. PATCH /followups/{trip_id}/mark-complete
Current behavior:
- Loads trip from `TripStore.get_trip(trip_id)`.
- 404 if missing trip or agency mismatch.
  - detail: `"Trip not found"`
- 400 if no followup scheduled.
  - detail: `"Trip has no follow-up scheduled"`
- Updates trip via `TripStore.update_trip` with:
  - `follow_up_status = "completed"`
  - `follow_up_completed_at = datetime.now(timezone.utc).isoformat()`
- Emits audit event:
  - name: `followup_completed`
  - actor: `operator`
  - payload contains `trip_id`, original `due_date`, `completed_at`
- Returns updated trip object.

### C. PATCH /followups/{trip_id}/snooze
Current behavior:
- Inputs:
  - `trip_id` path param
  - `days: int = 1` query param
- 404 if missing trip or agency mismatch.
  - detail: `"Trip not found"`
- 400 if no followup scheduled.
  - detail: `"Trip has no follow-up scheduled"`
- 400 if days not in allowed set `{1, 3, 7}`.
  - detail: `"days must be 1, 3, or 7"`
- Parses existing due date:
  - `datetime.fromisoformat(trip["follow_up_due_date"].replace('Z', '+00:00'))`
- 400 on parse failure.
  - detail: `"Invalid follow_up_due_date format"`
- Computes `new_due_date = current_due + timedelta(days=days)`.
- Updates trip via `TripStore.update_trip` with:
  - `follow_up_due_date = new_due_date`
  - `follow_up_status = "snoozed"`
- Emits audit event:
  - name: `followup_snoozed`
  - actor: `operator`
  - payload contains `trip_id`, `original_due_date`, `new_due_date`, `snooze_days`
- Returns updated trip object.

### D. PATCH /followups/{trip_id}/reschedule
Current behavior:
- Inputs:
  - `trip_id` path param
  - `new_date: str` query param (keep current contract unchanged)
- 404 if missing trip or agency mismatch.
  - detail: `"Trip not found"`
- 400 if no followup scheduled.
  - detail: `"Trip has no follow-up scheduled"`
- Validates `new_date` via `datetime.fromisoformat(new_date.replace('Z', '+00:00'))`.
- 400 on parse failure.
  - detail: `"Invalid date format. Use ISO-8601"`
- Updates trip via `TripStore.update_trip` with:
  - `follow_up_due_date = new_date`
  - `follow_up_status = "pending"`
- Emits audit event:
  - name: `followup_rescheduled`
  - actor: `operator`
  - payload contains `trip_id`, `old_due_date`, `new_due_date`
- Returns updated trip object.

## 3) Dependencies required in new router
The router plan must include/import only what these routes need:
- `TripStore`
- `AuditStore`
- `Agency`
- `get_current_agency`
- `datetime`
- `timezone`
- `timedelta`
- `json`
- `Path`
- `Optional`
- `HTTPException`

FastAPI helpers required for signatures:
- `APIRouter`
- `Depends`

## 4) Dashboard filesystem behavior preservation plan
Critical invariant:
- Preserve direct filesystem read behavior in dashboard route exactly for Slice D.

Preservation rules:
- Keep path derivation and glob semantics (`data/trips/*.json`) behavior-equivalent.
- Keep fail-soft `try/except` behavior on file decode/read errors.
- Keep agency filtering, due-date parsing, status/filter query logic, sorting, and return shape unchanged.
- Do not refactor dashboard to use `TripStore` in Slice D.

## 5) server.py changes (after approval only)
Planned changes only (do not execute in this plan phase):
1. Add normal import path wiring for new router:
   - `from routers import followups as followups_router`
2. Add fallback importlib wiring analogous to existing router fallback pattern for:
   - `spine_api/routers/followups.py`
3. Add router registration:
   - `app.include_router(followups_router.router)`
4. Remove only these four in-file handlers from `server.py`:
   - `get_followups_dashboard`
   - `mark_followup_complete`
   - `snooze_followup`
   - `reschedule_followup`

No other server.py behavior changes permitted.

## 6) Tests to add
New file:
- `tests/test_followups_router_behavior.py`

Planned cases:
1. dashboard agency filtering
2. mark-complete:
   - success
   - no-followup -> 400
   - missing trip -> 404
3. snooze:
   - success
   - invalid days -> 400
   - invalid date (bad existing due date format) -> 400
4. reschedule:
   - success
   - invalid date -> 400
5. audit event emitted for all mutating routes:
   - mark-complete
   - snooze
   - reschedule

## 7) Verification matrix (post-implementation phase)
Run after implementation approval:
- `tests/test_server_route_parity.py`
- `tests/test_server_openapi_path_parity.py`
- `tests/test_server_startup_invariants.py`
- `tests/test_followups_router_behavior.py`

## 8) Snapshot expectations (post-implementation phase)
- `scripts/snapshot_server_routes.py`
- expected `route_count=129`
- expected `openapi_path_count=113`

## 9) Forbidden server-import check
After router creation (implementation phase), run:
- `grep -n "from spine_api.server\|import server" spine_api/routers/followups.py`

Expected:
- no matches

## 10) Non-goals / must-not-change
- no public checker movement
- no agent runtime movement
- no team routes movement
- no `/trips` movement
- no core analytics movement
- no drafts/settings/documents/booking collection movement
- no `/run` or `/runs` movement
- no startup/lifespan/app-factory/middleware changes
- no auth/rate-limit behavior changes beyond preserving existing endpoint behavior
- no cleanup-only refactors

## Delivery confidence precheck for this plan artifact
- Filename/path exactness must match request:
  - `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICED_FOLLOWUPS_PLAN_2026-05-07.md`
- Scope must remain plan-only.
- Stop condition must be explicit.

## Stop condition
Stop after writing this plan. Await approval before implementation.