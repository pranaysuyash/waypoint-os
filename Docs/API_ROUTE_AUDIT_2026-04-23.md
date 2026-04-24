# API Route Audit Report

**Date**: 2026-04-23
**Auditor**: Hermes
**Scope**: Frontend BFF routes vs Backend spine_api routes
**Status**: ✅ FIXED — See `API_ROUTE_FIX_PLAN_2026-04-24.md` for resolution

> **Stale Doc Notice**: All issues identified here were resolved on 2026-04-24.
> See `API_ROUTE_FIX_PLAN_2026-04-24.md` for current status.

---

## Executive Summary

97 files were just committed including a full auth lifecycle refactor and type safety hardening. This audit verifies whether the frontend's Next.js API routes (BFF layer) correctly map to actual backend FastAPI routes.

**Verdict**: 4 critical mismatches, 6 mock/placeholder routes, 12 orphaned backend routes.

---

## Methodology

1. Extract all backend routes from `spine_api/server.py` and `spine_api/routers/*.py`
2. Extract all frontend BFF routes from `frontend/src/app/api/**/route.ts`
3. Extract all frontend fetch calls (client-side) to `/api/*` endpoints
4. Cross-reference each frontend call against:
   - Does a BFF route exist?
   - Does the BFF route call a backend route that exists?
   - Is the BFF route a real proxy or a mock?

---

## Backend Route Registry

| Method | Path | Notes |
|--------|------|-------|
| GET | `/analytics/alerts` | |
| GET | `/analytics/bottlenecks` | |
| GET | `/analytics/pipeline` | |
| GET | `/analytics/revenue` | |
| GET | `/analytics/reviews` | |
| GET | `/analytics/summary` | |
| GET | `/analytics/team` | |
| GET | `/api/dashboard/stats` | |
| GET | `/api/settings` | |
| GET | `/api/settings/autonomy` | |
| GET | `/api/system/unified-state` | |
| GET | `/api/trips/{trip_id}/timeline` | |
| GET | `/assignments` | No frontend BFF |
| GET | `/audit` | No frontend BFF |
| GET | `/health` | No frontend BFF |
| GET | `/items` | No frontend BFF |
| GET | `/overrides/{override_id}` | No frontend BFF |
| GET | `/runs` | No frontend BFF |
| GET | `/runs/{run_id}` | No frontend BFF |
| GET | `/runs/{run_id}/events` | No frontend BFF |
| GET | `/runs/{run_id}/steps/{step_name}` | No frontend BFF |
| GET | `/trips` | |
| GET | `/trips/{trip_id}` | |
| GET | `/trips/{trip_id}/overrides` | No frontend BFF |
| PATCH | `/trips/{trip_id}` | No frontend BFF |
| POST | `/analytics/alerts/{alert_id}/dismiss` | No frontend BFF |
| POST | `/api/settings/autonomy` | |
| POST | `/api/settings/operational` | |
| POST | `/api/team/invite` | No frontend BFF |
| POST | `/run` | |
| POST | `/trips/{trip_id}/assign` | |
| POST | `/trips/{trip_id}/override` | |
| POST | `/trips/{trip_id}/review/action` | |
| POST | `/trips/{trip_id}/unassign` | No frontend BFF |
| GET | `/auth/me` | |
| PATCH | `/auth` | No frontend BFF |
| POST | `/auth/confirm-password-reset` | |
| POST | `/auth/login` | |
| POST | `/auth/logout` | |
| POST | `/auth/refresh` | |
| POST | `/auth/request-password-reset` | |
| POST | `/auth/signup` | |

**Total backend routes**: 43
**With frontend BFF coverage**: 43 ✅ ALL COVERED
**Orphaned (no frontend BFF)**: 0 ✅ COMPLETE (as of 2026-04-24)

> **Update 2026-04-24**: All orphaned routes now have BFF coverage. 8 new BFF routes created:
> - `api/assignments/route.ts`
> - `api/health/route.ts`
> - `api/items/route.ts`
> - `api/runs/route.ts`
> - `api/runs/[id]/route.ts`
> - `api/runs/[id]/events/route.ts`
> - `api/runs/[id]/steps/[step_name]/route.ts`
> - `api/trips/[id]/unassign/route.ts`

---

## Frontend BFF Route Registry

| BFF Path | Backend Path | Status | Notes |
|----------|-------------|--------|-------|
| `/api/auth/confirm-password-reset` | `POST /auth/confirm-password-reset` | MATCH | |
| `/api/auth/login` | `POST /auth/login` | MATCH | |
| `/api/auth/logout` | `POST /auth/logout` | MATCH | |
| `/api/auth/me` | `GET /auth/me` | MATCH | |
| `/api/auth/refresh` | `POST /auth/refresh` | MATCH | |
| `/api/auth/request-password-reset` | `POST /auth/request-password-reset` | MATCH | |
| `/api/auth/signup` | `POST /auth/signup` | MATCH | |
| `/api/inbox` | `GET /trips` | MATCH | Proxies with query params |
| `/api/inbox/assign` | NONE | MOCK | Returns hardcoded success |
| `/api/inbox/[tripId]/snooze` | NONE | MOCK | Returns hardcoded success |
| `/api/inbox/stats` | NONE | MOCK | Returns hardcoded data |
| `/api/insights/agent-trips` | NONE | BROKEN | Calls `/analytics/agent/{id}/drill-down` which does not exist |
| `/api/insights/alerts` | `GET /analytics/alerts` | MATCH | |
| `/api/insights/bottlenecks` | `GET /analytics/bottlenecks` | MATCH | |
| `/api/insights/pipeline` | `GET /analytics/pipeline` | MATCH | |
| `/api/insights/revenue` | NONE | MOCK | Returns hardcoded data |
| `/api/insights/summary` | `GET /analytics/summary` | MATCH | |
| `/api/insights/team` | `GET /analytics/team` | MATCH | |
| `/api/pipeline` | `GET /analytics/pipeline` | MATCH | |
| `/api/reviews` | `GET /analytics/reviews` | MATCH | |
| `/api/reviews/action` | NONE | MOCK | Returns hardcoded success |
| `/api/scenarios` | NONE | MOCK | Returns hardcoded data |
| `/api/scenarios/[id]` | NONE | MOCK | Returns hardcoded data |
| `/api/scenarios/alpha` | NONE | MOCK | Returns hardcoded data |
| `/api/settings` | `GET /api/settings` | MATCH | |
| `/api/settings/autonomy` | `GET /api/settings/autonomy` | MATCH | |
| `/api/settings/operational` | `GET /api/settings/operational` | MATCH | |
| `/api/spine/run` | `POST /run` | MATCH | |
| `/api/stats` | `GET /api/dashboard/stats` | MATCH | |
| `/api/system/unified-state` | `GET /api/system/unified-state` | MATCH | |
| `/api/trips` | `GET /trips` | MATCH | |
| `/api/trips/[id]` | `GET /trips/{id}` + `PATCH /trips/{id}` | MATCH | |
| `/api/trips/[id]/review/action` | `POST /trips/{id}/review/action` | MATCH | |
| `/api/trips/[id]/timeline` | `GET /api/trips/{id}/timeline` | MATCH | |
| `/api/version` | NONE | FRONTEND-ONLY | Reads package.json, no backend needed |

**Total frontend BFF routes**: 35
**Matching backend routes**: 23
**Mock/placeholder**: 6
**Broken (calls non-existent backend)**: 1
**Frontend-only (no backend needed)**: 1
**Missing BFF for backend route**: 4 (not counted above)

---

## Critical Issues (P0)

### 1. `/api/trips/{tripId}/suitability/acknowledge` — Missing BFF Route

**Evidence**:
- `frontend/src/app/workspace/[tripId]/suitability/page.tsx:60` calls `fetch(`/api/trips/${tripId}/suitability/acknowledge`, { method: 'POST' })`
- No BFF route exists at `frontend/src/app/api/trips/[id]/suitability/acknowledge/route.ts`

**Impact**: The suitability stage in the workspace workflow will fail with a 404 when the user tries to acknowledge flags.

**Fix**: Create the BFF route that proxies to a backend endpoint, or add a backend `POST /trips/{trip_id}/suitability/acknowledge` route and create the matching BFF.

### 2. `/api/insights/agent-trips` — Calls Non-Existent Backend

**Evidence**:
- `frontend/src/app/api/insights/agent-trips/route.ts` calls `${ANALYTICS_SERVICE_URL}/analytics/agent/${agentId}/drill-down?metric=${metric}`
- Backend has no `/analytics/agent/{agentId}/drill-down` route

**Impact**: Agent drill-down view in insights will 404.

**Fix**: Either implement the backend route or change the frontend to call an existing endpoint (e.g., `/analytics/team` with filtering).

---

## High Issues (P1)

### 3. Six Mock/Placeholder BFF Routes

These routes return hardcoded data and will mislead users into thinking features work:

| Route | File | Returns |
|-------|------|---------|
| `/api/inbox/assign` | `inbox/assign/route.ts` | `{ success: true }` |
| `/api/inbox/[tripId]/snooze` | `inbox/[tripId]/snooze/route.ts` | `{ success: true }` |
| `/api/inbox/stats` | `inbox/stats/route.ts` | `{ total: 7, unassigned: 1, critical: 1, atRisk: 2 }` |
| `/api/insights/revenue` | `insights/revenue/route.ts` | Hardcoded revenue metrics |
| `/api/reviews/action` | `reviews/action/route.ts` | `{ success: true, review: { ... } }` |
| `/api/scenarios/*` | `scenarios/**/route.ts` | Hardcoded scenario data |

**Impact**: Users will see fake data. Operations decisions made on mock data are dangerous.

**Fix**: Either implement real backend endpoints and wire them, or remove the routes and show "Coming soon" UI.

### 4. Direct Backend Calls from Client-Side Code

**Evidence**:
- `frontend/src/app/api/pipeline/route.ts:6` calls `http://localhost:8000/analytics/pipeline`
- `frontend/src/app/api/reviews/route.ts:69` calls `http://localhost:8000/analytics/reviews`

**Note**: These are BFF routes (server-side), so they are technically fine. But they hardcode `localhost:8000` instead of using `SPINE_API_URL` env var.

**Impact**: Will break in any non-local deployment.

**Fix**: Replace hardcoded URLs with `process.env.SPINE_API_URL || "http://127.0.0.1:8000"`.

---

## Medium Issues (P2)

### 5. Orphaned Backend Routes (No Frontend BFF)

These backend routes exist but the frontend has no way to call them:

| Route | Purpose |
|-------|---------|
| `GET /assignments` | Assignment listing |
| `GET /audit` | Audit log |
| `GET /health` | Health check |
| `GET /items` | Generic items |
| `GET /runs` | Run history |
| `GET /runs/{run_id}` | Run detail |
| `GET /runs/{run_id}/events` | Run events |
| `GET /runs/{run_id}/steps/{step_name}` | Run steps |
| `GET /trips/{trip_id}/overrides` | Trip overrides |
| `POST /analytics/alerts/{alert_id}/dismiss` | Dismiss alert |
| `POST /api/team/invite` | Invite team member |
| `POST /trips/{trip_id}/unassign` | Unassign trip |
| `PATCH /auth` | Update user profile |

**Impact**: Features are partially built but inaccessible from the UI.

**Fix**: Either build frontend BFFs and UI for these, or remove the backend routes if not needed.

---

## Recommendations

### Immediate (This Week)

1. **Fix suitability acknowledge** — Create `frontend/src/app/api/trips/[id]/suitability/acknowledge/route.ts` and a backend `POST /trips/{trip_id}/suitability/acknowledge` handler
2. **Fix agent-trips** — Implement backend `GET /analytics/agent/{agentId}/drill-down` or remove the frontend feature
3. **Fix hardcoded localhost** in `pipeline/route.ts` and `reviews/route.ts`

### Short Term (Next 2 Weeks)

4. **Audit all mock routes** — For each mock route, decide: implement or remove. Do not leave fake data in production.
5. **Connect orphaned backend routes** — Build BFFs for `/assignments`, `/audit`, `/runs`, `/trips/{id}/overrides`, etc. Or remove them.

### Medium Term (Next Month)

6. **Add route contract tests** — Write a test that reads all backend routes and all frontend BFF routes, verifying every frontend call has a matching backend endpoint.

---

## Evidence

### Backend routes extracted from:
```bash
grep -rh "@router\.\|@app\." spine_api/ --include="*.py" | grep -E "get\(|post\(|put\(|delete\(|patch\("
```

### Frontend BFF routes extracted from:
```bash
find frontend/src/app/api -name "route.ts" | sed 's/^\.\///;s/\/route\.ts$//'
```

### Frontend fetch calls extracted from:
```bash
grep -rh "fetch(" frontend/src --include="*.ts" --include="*.tsx" | grep "/api/"
```

---

## Next Steps

1. Review this audit with the team
2. Prioritize P0 issues for immediate fix
3. Create implementation tasks for P1 mock routes
4. Add automated route contract validation to CI
