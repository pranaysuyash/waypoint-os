# Server.py Refactor Phase 3 — Slice E Team Completion

Date: 2026-05-08
Status: Implemented and verified (stopped at Slice E)

## Scope implemented
Moved only these six routes from `spine_api/server.py` to `spine_api/routers/team.py`:
1. GET /api/team/members
2. GET /api/team/members/{member_id}
3. POST /api/team/invite
4. PATCH /api/team/members/{member_id}
5. DELETE /api/team/members/{member_id}
6. GET /api/team/workload

## Files changed
- `spine_api/routers/team.py` (new)
- `spine_api/server.py` (router import/wiring + removal of six in-file team handlers)
- `tests/test_team_router_behavior.py` (new)

## Preservation checks
- Preserved unscoped behavior of `GET /api/team/members/{member_id}`:
  - Handler signature remains `member_id, db` (no agency dependency introduced).
- No auth hardening/security changes were added in this extraction slice.
- No startup/lifespan/app-factory/middleware changes.
- No /run or /runs movement.
- No public-checker, agent-runtime, or settings movement.

## Verification executed

### Required matrix
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py tests/test_team_router_behavior.py -q`

Result:
- `12 passed in 10.36s`

### Snapshot command
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py`

Observed:
- `route_count = 131`
- `openapi_path_count = 115`

Note:
- Current repository snapshot fixtures are also `131/115` (`tests/fixtures/server_route_snapshot.json`, `tests/fixtures/server_openapi_paths_snapshot.json`).
- Parity tests passed, confirming no route/openapi drift versus current baseline.

### Forbidden import check
Command:
`grep -n "from spine_api.server\|import server" spine_api/routers/team.py`

Result:
- No matches (empty output).

## Additional correction carried forward
- `POST /run` is excluded from Phase 3 router movement and is not part of the agent-runtime candidate scope.

## Stop condition
Stopped after Slice E implementation and verification. No further slice work started.

## Addendum — Acceptance update (2026-05-08)
External review verdict updated to:
- Phase 3 Slice E Team extraction: ACCEPTED

Acceptance basis:
- Required matrix passing: 12 passed.
- Route/OpenAPI parity vs current fixtures: 131/115 equals 131/115.
- Live-vs-fixture route/path set diff: zero added, zero removed.
- Forbidden router->server import check in `spine_api/routers/team.py`: clean.
- Unscoped behavior for `GET /api/team/members/{member_id}` preserved.

Remaining merge condition:
- Merge only a Slice E-isolated patch. Do not include unrelated workspace drift.
- Intended Slice E patch scope:
  1. `spine_api/routers/team.py`
  2. `spine_api/server.py` (Team import/include/removal hunks only)
  3. `tests/test_team_router_behavior.py`
  4. This completion document
  5. Snapshot files only if baseline update is intentional and explicitly explained
