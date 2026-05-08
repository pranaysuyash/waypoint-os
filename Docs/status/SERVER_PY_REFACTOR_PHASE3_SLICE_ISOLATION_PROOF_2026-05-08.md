# Server.py Refactor Phase 3 — Slice Isolation Proof (A–F)

Date: 2026-05-08
Mode: Read-only inspection only
Scope: Isolation proof for accepted slices A–F before any Slice G planning

## Evidence commands used (read-only)
1) `git status --short`
2) `git diff --unified=0 -- spine_api/server.py`
3) `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`
4) `TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py`
5) `rg -n "from spine_api\.server|\bimport server\b" spine_api/routers/{run_status,health,system_dashboard,followups,team,product_b_analytics}.py`
6) `search/read` inspection of `spine_api/server.py` router imports/includes and route decorators

---

## Slice A (Run status)

### 1) Files that belong to Slice A
- `spine_api/routers/run_status.py`
- `tests/test_run_status_router_behavior.py`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEA_COMPLETION_2026-05-07.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import run_status as run_status_router` (present at line ~285)
- fallback importlib load: `spec_from_file_location("routers.run_status", ...)` (present at line ~319)
- include_router: `app.include_router(run_status_router.router)` (present at line ~588)
- removed in-file handlers:
  - `GET /runs`
  - `GET /runs/{run_id}`
  - `GET /runs/{run_id}/steps/{step_name}`
  - `GET /runs/{run_id}/events`

### 3) Exact routes moved
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/steps/{step_name}`
- `GET /runs/{run_id}/events`

### 4) No unrelated route handlers removed/modified (for this slice)
- Current `server.py` contains no in-file `/runs*` handlers (expected after extraction).
- No contrary evidence found in current read-only inspection.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware change evidence tied to Slice A in current inspection.

### 6) /run and /runs boundary
- `/runs*` moved per Slice A scope.
- `/run` remains in `server.py` (`@app.post("/run", response_model=RunAcceptedResponse)` present).

### 7) Forbidden router import check
- `spine_api/routers/run_status.py`: no `spine_api.server` / `import server` matches.

---

## Slice B (Health)

### 1) Files that belong to Slice B
- `spine_api/routers/health.py`
- `tests/test_health_router_behavior.py`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEB_HEALTH_COMPLETION_2026-05-07.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import health as health_router` (line ~286)
- fallback importlib load: `spec_from_file_location("routers.health", ...)` (line ~324)
- include_router: `app.include_router(health_router.router)` (line ~589)
- removed in-file handler:
  - `GET /health`

### 3) Exact routes moved
- `GET /health`

### 4) No unrelated route handlers removed/modified (for this slice)
- Current `server.py` has no in-file `GET /health` handler (expected).
- No contrary evidence found in current read-only inspection.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware change evidence tied to Slice B in current inspection.

### 6) /run and /runs boundary
- No /run or /runs changes attributable to Slice B.

### 7) Forbidden router import check
- `spine_api/routers/health.py`: no `spine_api.server` / `import server` matches.

---

## Slice C (System + Dashboard)

### 1) Files that belong to Slice C
- `spine_api/routers/system_dashboard.py`
- `tests/test_system_dashboard_router_behavior.py`
- `tests/test_integrity.py` (patch target update documented in completion)
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEC_SYSTEM_DASHBOARD_COMPLETION_2026-05-07.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import system_dashboard as system_dashboard_router` (line ~287)
- fallback importlib load: `spec_from_file_location("routers.system_dashboard", ...)` (line ~329)
- include_router: `app.include_router(system_dashboard_router.router)` (line ~590)
- removed in-file handlers:
  - `GET /api/system/unified-state`
  - `GET /api/system/integrity/issues`
  - `GET /api/dashboard/stats`

### 3) Exact routes moved
- `GET /api/system/unified-state`
- `GET /api/system/integrity/issues`
- `GET /api/dashboard/stats`

### 4) No unrelated route handlers removed/modified (for this slice)
- Current `server.py` no longer hosts these three in-file handlers (expected).
- No contrary evidence found in current read-only inspection.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware change evidence tied to Slice C in current inspection.

### 6) /run and /runs boundary
- No /run or /runs changes attributable to Slice C.

### 7) Forbidden router import check
- `spine_api/routers/system_dashboard.py`: no `spine_api.server` / `import server` matches.

---

## Slice D (Followups)

### 1) Files that belong to Slice D
- `spine_api/routers/followups.py`
- `tests/test_followups_router_behavior.py`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICED_FOLLOWUPS_COMPLETION_2026-05-07.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import followups as followups_router` (line ~288)
- fallback importlib load: `spec_from_file_location("routers.followups", ...)` (line ~334)
- include_router: `app.include_router(followups_router.router)` (line ~591)
- removed in-file handlers:
  - `GET /followups/dashboard`
  - `PATCH /followups/{trip_id}/mark-complete`
  - `PATCH /followups/{trip_id}/snooze`
  - `PATCH /followups/{trip_id}/reschedule`

### 3) Exact routes moved
- `GET /followups/dashboard`
- `PATCH /followups/{trip_id}/mark-complete`
- `PATCH /followups/{trip_id}/snooze`
- `PATCH /followups/{trip_id}/reschedule`

### 4) No unrelated route handlers removed/modified (for this slice)
- Target followups handlers are removed from in-file `server.py` as expected.
- However, current `server.py` diff includes unrelated non-Slice-D modifications (extraction and inbox changes). This prevents isolated-merge proof.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware changes shown in current `server.py` diff.

### 6) /run and /runs boundary
- No /run or /runs diff lines in current `server.py` patch.

### 7) Forbidden router import check
- `spine_api/routers/followups.py`: no `spine_api.server` / `import server` matches.

---

## Slice E (Team)

### 1) Files that belong to Slice E
- `spine_api/routers/team.py`
- `tests/test_team_router_behavior.py`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEE_TEAM_COMPLETION_2026-05-08.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import team as team_router` (line ~289)
- fallback importlib load: `spec_from_file_location("routers.team", ...)` (line ~339)
- include_router: `app.include_router(team_router.router)` (line ~592)
- removed in-file handlers:
  - `GET /api/team/members`
  - `GET /api/team/members/{member_id}`
  - `POST /api/team/invite`
  - `PATCH /api/team/members/{member_id}`
  - `DELETE /api/team/members/{member_id}`
  - `GET /api/team/workload`

### 3) Exact routes moved
- `GET /api/team/members`
- `GET /api/team/members/{member_id}`
- `POST /api/team/invite`
- `PATCH /api/team/members/{member_id}`
- `DELETE /api/team/members/{member_id}`
- `GET /api/team/workload`

### 4) No unrelated route handlers removed/modified (for this slice)
- Target team handlers are removed from in-file `server.py` as expected.
- However, current `server.py` diff includes unrelated non-Slice-E modifications (extraction and inbox changes). This prevents isolated-merge proof.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware changes shown in current `server.py` diff.

### 6) /run and /runs boundary
- No /run or /runs diff lines in current `server.py` patch.

### 7) Forbidden router import check
- `spine_api/routers/team.py`: no `spine_api.server` / `import server` matches.

---

## Slice F (Product-B KPI)

### 1) Files that belong to Slice F
- `spine_api/routers/product_b_analytics.py`
- `tests/test_product_b_analytics_router_behavior.py`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEF_PRODUCTB_KPI_COMPLETION_2026-05-08.md`
- `spine_api/server.py` (wiring + in-file handler removal)

### 2) Exact server.py hunk categories
- normal router import: `from routers import product_b_analytics as product_b_analytics_router` (line ~290)
- fallback importlib load: `spec_from_file_location("routers.product_b_analytics", ...)` (line ~344)
- include_router: `app.include_router(product_b_analytics_router.router)` (line ~593)
- removed in-file handler:
  - `GET /analytics/product-b/kpis`

### 3) Exact routes moved
- `GET /analytics/product-b/kpis`

### 4) No unrelated route handlers removed/modified (for this slice)
- Target Product-B KPI handler is removed from in-file `server.py` as expected.
- However, current `server.py` diff includes unrelated non-Slice-F modifications (extraction and inbox changes). This prevents isolated-merge proof.

### 5) Startup/lifespan/app factory/middleware unchanged (for this slice)
- No startup/lifespan/app factory/middleware changes shown in current `server.py` diff.

### 6) /run and /runs boundary
- No /run or /runs diff lines in current `server.py` patch.

### 7) Forbidden router import check
- `spine_api/routers/product_b_analytics.py`: no `spine_api.server` / `import server` matches.

---

## 8) Current parity status (live verification in this run)

### Route/OpenAPI/startup parity tests
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_server_route_parity.py tests/test_server_openapi_path_parity.py tests/test_server_startup_invariants.py -q`

Result:
- `7 passed in 5.83s`

### Snapshot status
Command:
`TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/snapshot_server_routes.py`

Observed:
- `route_count = 131`
- `openapi_path_count = 115`

---

## 9) Unrelated modified/untracked files that must be excluded from slice merge

From `git status --short`, unrelated drift exists outside A–F slice artifacts.

### Blocking unrelated modified files
- `AGENTS.md`
- `Docs/EXPLORATION_TOPICS.md`
- `Docs/PHASE4E_EXTRACTION_PLAN_2026-05-07.md`
- `Docs/context/agent-start/SESSION_CONTEXT.md`
- `frontend/docs/context/agent-start/SESSION_CONTEXT.md`
- `frontend/src/components/inbox/TripCard.tsx`
- `frontend/src/components/inbox/__tests__/TripCard.test.tsx`
- `frontend/src/lib/inbox-helpers.ts`
- `frontend/src/types/governance.ts`
- `spine_api/contract.py`
- `spine_api/models/tenant.py`
- `spine_api/services/extraction_service.py`
- `spine_api/services/inbox_projection.py`
- `src/extraction/openai_vision_extractor.py`
- `src/extraction/vision_client.py`
- `tests/fixtures/server_openapi_paths_snapshot.json`
- `tests/fixtures/server_route_snapshot.json`
- `tests/test_vision_extraction.py`

### Blocking unrelated untracked files/directories
- `Docs/DESIGN_2D_PRIORITY_MODEL_2026-05-08.md`
- `Docs/PHASE4F_OPS_UX_DESIGN_2026-05-08.md`
- `Docs/PRIORITY_SIGNAL_MODEL_ANALYSIS_2026-05-08.md`
- `Docs/PRODUCTB_AGENT_ARCH_LAUNCH_NOW_2026-05-08.md`
- `alembic/versions/add_extraction_attempts_and_pdf.py`
- `frontend/src/components/ui/PriorityIndicator.tsx`
- `frontend/src/components/ui/__tests__/PriorityIndicator.test.tsx`
- `spine_api/scoring/`
- `src/extraction/exceptions.py`
- `src/extraction/gemini_vision_client.py`
- `src/extraction/gemini_vision_extractor.py`
- `src/extraction/model_chain.py`
- `src/extraction/pdf_utils.py`
- `src/extraction/pricing.py`
- `tests/test_extraction_attempts.py`
- `tests/test_extraction_fallback.py`
- `tests/test_scoring_priority.py`
- `tools/benchmarks/`

Additionally, `spine_api/server.py` currently contains unrelated non-A–F hunks (inbox filter/query changes and extraction attempt/retry route/model additions), so server.py itself is not currently slice-isolated.

---

## Final recommendation
Merge gate: BLOCKED

Blocking reasons:
1) `spine_api/server.py` includes unrelated non-A–F changes mixed with slice extraction hunks.
2) Numerous unrelated modified/untracked files are present in the working tree and must be excluded from any slice merge bundle.

Stop here. No Slice G planning started.
