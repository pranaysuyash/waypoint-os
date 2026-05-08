# Server.py Refactor Phase 3 — A–F Server Hunk Manifest (Read-only)

Date: 2026-05-08
Mode: Read-only inspection only
Goal: Identify accepted Slice A–F `spine_api/server.py` patch content, separate from unrelated parallel drift.

## Source artifacts
- Isolation proof doc:
  - `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICE_ISOLATION_PROOF_2026-05-08.md`
- Read-only inspection used:
  - `git diff --unified=0 -- spine_api/server.py`
  - `read/search` inspection of `spine_api/server.py`

---

## 1) Accepted A–F server.py hunks only

### A. Router imports added (accepted A–F)
- `from routers import run_status as run_status_router`
- `from routers import health as health_router`
- `from routers import system_dashboard as system_dashboard_router`
- `from routers import followups as followups_router`
- `from routers import team as team_router`
- `from routers import product_b_analytics as product_b_analytics_router`

### B. Fallback importlib blocks added (accepted A–F)
- `spec_from_file_location("routers.run_status", _base / "routers" / "run_status.py")`
- `spec_from_file_location("routers.health", _base / "routers" / "health.py")`
- `spec_from_file_location("routers.system_dashboard", _base / "routers" / "system_dashboard.py")`
- `spec_from_file_location("routers.followups", _base / "routers" / "followups.py")`
- `spec_from_file_location("routers.team", _base / "routers" / "team.py")`
- `spec_from_file_location("routers.product_b_analytics", _base / "routers" / "product_b_analytics.py")`

### C. include_router additions (accepted A–F)
- `app.include_router(run_status_router.router)`
- `app.include_router(health_router.router)`
- `app.include_router(system_dashboard_router.router)`
- `app.include_router(followups_router.router)`
- `app.include_router(team_router.router)`
- `app.include_router(product_b_analytics_router.router)`

### D. In-file handlers removed (accepted A–F)
- Slice A (`/runs*`)
  - `GET /runs`
  - `GET /runs/{run_id}`
  - `GET /runs/{run_id}/steps/{step_name}`
  - `GET /runs/{run_id}/events`
- Slice B
  - `GET /health`
- Slice C
  - `GET /api/system/unified-state`
  - `GET /api/system/integrity/issues`
  - `GET /api/dashboard/stats`
- Slice D (`/followups/*`)
  - `GET /followups/dashboard`
  - `PATCH /followups/{trip_id}/mark-complete`
  - `PATCH /followups/{trip_id}/snooze`
  - `PATCH /followups/{trip_id}/reschedule`
- Slice E (`/api/team/*`)
  - `GET /api/team/members`
  - `GET /api/team/members/{member_id}`
  - `POST /api/team/invite`
  - `PATCH /api/team/members/{member_id}`
  - `DELETE /api/team/members/{member_id}`
  - `GET /api/team/workload`
- Slice F
  - `GET /analytics/product-b/kpis`

---

## 2) Routes moved by accepted slices (A–F)
- Slice A: `/runs*`
- Slice B: `/health`
- Slice C: `/api/system/unified-state`, `/api/system/integrity/issues`, `/api/dashboard/stats`
- Slice D: `/followups/*`
- Slice E: `/api/team/*`
- Slice F: `/analytics/product-b/kpis`

---

## 3) Router files belonging to accepted slices
- `spine_api/routers/run_status.py`
- `spine_api/routers/health.py`
- `spine_api/routers/system_dashboard.py`
- `spine_api/routers/followups.py`
- `spine_api/routers/team.py`
- `spine_api/routers/product_b_analytics.py`

---

## 4) Test files belonging to accepted slices
- `tests/test_run_status_router_behavior.py`
- `tests/test_health_router_behavior.py`
- `tests/test_system_dashboard_router_behavior.py`
- `tests/test_followups_router_behavior.py`
- `tests/test_team_router_behavior.py`
- `tests/test_product_b_analytics_router_behavior.py`

---

## 5) Docs belonging to accepted slices (completion + plan docs only)

### Completion docs
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEA_COMPLETION_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEB_HEALTH_COMPLETION_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEC_SYSTEM_DASHBOARD_COMPLETION_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICED_FOLLOWUPS_COMPLETION_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEE_TEAM_COMPLETION_2026-05-08.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEF_PRODUCTB_KPI_COMPLETION_2026-05-08.md`

### Plan docs
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_ROUTER_DECOMPOSITION_PLAN_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEB_HEALTH_PLAN_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEC_SYSTEM_DASHBOARD_PLAN_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICED_FOLLOWUPS_PLAN_2026-05-07.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEE_TEAM_PLAN_2026-05-08.md`
- `Docs/status/SERVER_PY_REFACTOR_PHASE3_SLICEF_PRODUCTB_KPI_PLAN_2026-05-08.md`

---

## 6) Non-slice examples to ignore (outside A–F manifest scope)
These may exist due to parallel agents. They are outside this manifest and should not be interpreted as A–F slice failures:
- inbox priority/filter changes (e.g., `minUrgency`, `minImportance`)
- extraction attempt/retry routes/models
- `AttemptSummaryResponse`
- `ExtractionResponse` attempt metadata fields
- extraction MIME/attempt behavior changes
- vision/extraction file changes
- frontend file changes
- scoring file changes
- unrelated docs
- snapshot fixture changes unless explicitly approved for slice evidence

---

## Current server.py mixed non-slice hunk breakdown (read-only)

### Non-slice hunk A: inbox query/doc surface expansion
- Area: `get_inbox(...)`
- What changed:
  - added query params: `minUrgency`, `minImportance`
  - updated endpoint docstring filter/sort descriptions accordingly
- Why unrelated to A–F:
  - A–F scope is router extraction of `/runs*`, `/health`, system/dashboard trio, `/followups/*`, `/api/team/*`, `/analytics/product-b/kpis` only.
  - Inbox filtering is separate feature work.

### Non-slice hunk B: extraction response schema expansion
- Area: `class ExtractionResponse`
- What changed:
  - added attempt-tracking fields: `attempt_count`, `run_count`, `current_attempt_id`, `page_count`
- Why unrelated to A–F:
  - extraction schema evolution is independent from route extraction slices.

### Non-slice hunk C: new extraction attempt summary model
- Area: `class AttemptSummaryResponse`
- What changed:
  - added new response model for extraction attempts list endpoint
- Why unrelated to A–F:
  - not part of accepted route extraction slices.

### Non-slice hunk D: extraction execution behavior updates
- Area: `extract_document(...)` and `_extraction_to_response(...)`
- What changed:
  - MIME prevalidation set includes PDF
  - import/exception flow changes with `ExtractionValidationError`
  - response mapping now includes attempt-tracking fields
- Why unrelated to A–F:
  - extraction behavior and document-processing pipeline are not in A–F route-move scope.

### Non-slice hunk E: new extraction retry/attempts routes
- Areas:
  - `POST /trips/{trip_id}/documents/{document_id}/extraction/retry`
  - `GET /trips/{trip_id}/documents/{document_id}/extraction/attempts`
- What changed:
  - new route handlers added with DB/service flow and response shaping
- Why unrelated to A–F:
  - these are net-new extraction endpoints, not A–F extracted endpoints.

---

## Manual patch construction checklist
1. Build patch from accepted `server.py` hunks only (Section 1 above).
2. Include router files A–F only.
3. Include test files A–F only.
4. Include docs A–F (completion + plan docs only).
5. Exclude all non-slice hunks listed above (outside A–F manifest scope).
6. Exclude snapshot fixture changes unless separately approved.
7. After manual patch construction, run parity/startup verification matrices before merge review.

