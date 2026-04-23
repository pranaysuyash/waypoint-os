
> **Stale Doc Notice**: All issues resolved — see `API_ROUTE_FIX_PLAN_2026-04-24.md` for current status.
# API Route Fix Report

**Date**: 2026-04-24
**Status**: P0/P1 Complete — Build green, 312 tests passing

---

## Summary

Resolved all critical (P0) and high (P1) gaps from the API Route Audit. During implementation, discovered an additional class of missing BFF routes referenced by `frontend/src/lib/governance-api.ts` and `frontend/src/lib/api-client.ts` but never created. These have also been wired where backend support exists.

**Files changed**: 14 modified/created
**Build**: Zero TypeScript errors
**Tests**: 312/312 passing

---

## P0 Fixes

### 1. Suitability Acknowledge Workflow

**Problem**: `/api/trips/${tripId}/suitability/acknowledge` called from workspace but no BFF or backend route existed.

**Fix**:
- **Backend**: Added `POST /trips/{trip_id}/suitability/acknowledge` in `spine-api/server.py`
  - Stores acknowledged flags in `trip.analytics.acknowledged_flags`
  - Sets `suitability_acknowledged_at` timestamp
  - Logs audit event
- **Contract**: Added `SuitabilityAcknowledgeRequest` to `spine-api/contract.py`
- **BFF**: Created `frontend/src/app/api/trips/[id]/suitability/acknowledge/route.ts`

### 2. Agent Drill-Down

**Problem**: `/api/insights/agent-trips` called non-existent `/analytics/agent/{id}/drill-down`.

**Fix**:
- **Backend**: Added `GET /analytics/agent/{agent_id}/drill-down` in `spine-api/server.py`
  - Filters trips by `assigned_to` or `agent_id`
  - Returns trips array + count
- **BFF**: No changes needed — existing `insights/agent-trips/route.ts` already calls the correct URL pattern

---

## P1 Fixes

### 3. Hardcoded localhost:8000

**Problem**: Three BFF routes hardcoded `localhost:8000`, breaking on any non-local deploy.

**Fix**:
- `frontend/src/app/api/pipeline/route.ts`
- `frontend/src/app/api/reviews/route.ts`
- `frontend/src/app/api/trips/[id]/route.ts` (both GET and PATCH)

All now use:
```typescript
const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
```

### 4. Mock Routes Replaced with Real Proxies

| Route | Before | After |
|-------|--------|-------|
| `/api/insights/revenue` | Hardcoded JSON | Proxies to `GET /analytics/revenue` |
| `/api/reviews/action` | Hardcoded success | Proxies to `POST /trips/{trip_id}/review/action` |
| `/api/inbox/stats` | Hardcoded counts | Computes from `GET /trips` |
| `/api/inbox/assign` | Hardcoded success | Proxies to `POST /trips/{trip_id}/assign` per trip |
| `/api/inbox/[tripId]/snooze` | Hardcoded success | Proxies to `POST /trips/{trip_id}/snooze` |

**Backend snooze endpoint**: Added `POST /trips/{trip_id}/snooze` in `server.py`
- Stores `snooze_until` in `trip.analytics`
- Logs audit event

---

## Expanded Scope — API Client Orphaned Routes

During the fix, discovered that `governance-api.ts` and `api-client.ts` reference many BFF routes that were never created. The original audit only caught `fetch()` calls in page components, missing the centralized API client layer.

### Newly Created (Backend Exists)

| BFF Route | Backend Route | Purpose |
|-----------|--------------|---------|
| `/api/audit` | `GET /audit` | Audit log listing |
| `/api/audit/trip/[tripId]` | `GET /audit` (filtered) | Audit events for a trip |
| `/api/insights/alerts/[alertId]/dismiss` | `POST /analytics/alerts/{id}/dismiss` | Dismiss operational alert |
| `/api/overrides/[id]` | `GET /overrides/{id}` | Get override by ID |
| `/api/trips/[id]/overrides` | `GET /trips/{id}/overrides` | List overrides for a trip |

### Still Missing — No Backend Support

These endpoints are called by the frontend API client but have no backend implementation. They represent feature gaps, not routing gaps:

| Frontend Call | Status | Notes |
|---------------|--------|-------|
| `GET /api/reviews/${id}` | Missing | Get single review by ID |
| `POST /api/reviews/bulk-action` | Missing | Bulk review actions |
| `GET /api/insights/escalations` | Missing | Escalation heatmap |
| `GET /api/insights/funnel` | Missing | Conversion funnel |
| `GET /api/team/members` | Missing | Team listing |
| `GET /api/team/members/${id}` | Missing | Team member detail |
| `POST /api/team/invite` | Missing | Invite team member |
| `PATCH /api/team/members/${id}` | Missing | Update team member |
| `DELETE /api/team/members/${id}` | Missing | Deactivate team member |
| `GET /api/team/workload` | Missing | Workload distribution |
| `POST /api/inbox/reassign` | Missing | Reassign trip |
| `POST /api/inbox/bulk` | Missing | Bulk inbox actions |
| `GET /api/settings/pipeline` | Missing | Pipeline stage config |
| `PUT /api/settings/pipeline` | Missing | Update pipeline config |
| `GET /api/settings/approvals` | Missing | Approval thresholds |
| `PUT /api/settings/approvals` | Missing | Update thresholds |
| `POST /api/insights/export` | Missing | Export insights |

**Recommendation**: Each of these needs either:
1. Backend endpoint + BFF route, or
2. Frontend UI removal if the feature is deprioritized

Do not leave them as silent 404s — the API client will throw `ApiException` which the UI may not handle gracefully.

---

## Files Changed

### Backend
- `spine-api/server.py` — Added 3 new endpoints (snooze, suitability acknowledge, agent drill-down)
- `spine-api/contract.py` — Added `SuitabilityAcknowledgeRequest`, `SnoozeRequest`

### Frontend BFF
- `frontend/src/app/api/pipeline/route.ts` — Fixed hardcoded URL
- `frontend/src/app/api/reviews/route.ts` — Fixed hardcoded URL
- `frontend/src/app/api/trips/[id]/route.ts` — Fixed hardcoded URL (GET + PATCH)
- `frontend/src/app/api/insights/revenue/route.ts` — Replaced mock with proxy
- `frontend/src/app/api/reviews/action/route.ts` — Replaced mock with proxy
- `frontend/src/app/api/inbox/stats/route.ts` — Replaced mock with computed data
- `frontend/src/app/api/inbox/assign/route.ts` — Replaced mock with proxy
- `frontend/src/app/api/inbox/[tripId]/snooze/route.ts` — Replaced mock with proxy
- `frontend/src/app/api/trips/[id]/suitability/acknowledge/route.ts` — **Created**
- `frontend/src/app/api/audit/route.ts` — **Created**
- `frontend/src/app/api/audit/trip/[tripId]/route.ts` — **Created**
- `frontend/src/app/api/insights/alerts/[alertId]/dismiss/route.ts` — **Created**
- `frontend/src/app/api/overrides/[id]/route.ts` — **Created**
- `frontend/src/app/api/trips/[id]/overrides/route.ts` — **Created**

---

## Verification

```bash
cd frontend
npm run build      # zero errors
npm test -- --run  # 312/312 passing
```

---

## Next Steps

1. **Implement missing backend endpoints** for team management, pipeline config, and approvals (or remove frontend calls)
2. **Add route contract tests** to CI that fail when frontend calls a non-existent BFF or BFF calls a non-existent backend endpoint
3. **Audit `governance-api.ts`** systematically — every endpoint referenced there should have a corresponding BFF file
