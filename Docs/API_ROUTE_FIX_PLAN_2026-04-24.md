# API Route Fix Plan

**Date**: 2026-04-24
**Scope**: Close all P0/P1 gaps from API_ROUTE_AUDIT_2026-04-23.md
**Status**: ALL PHASES ✅ COMPLETED + ORPHANED ROUTES ✅ COMPLETED 2026-04-24

---

## Execution Order

### Phase 1: Quick Wins (Hardcoded URLs + Real Proxies) ✅ COMPLETED 2026-04-24

1. ~~**Fix `pipeline/route.ts`** — replace `http://localhost:8000` with `process.env.SPINE_API_URL || "http://127.0.0.1:8000"`~~ ✅ Already had env var
2. ~~**Fix `reviews/route.ts`** — same~~ ✅ Verified real proxy (already fixed)
3. **Fix `trips/[id]/route.ts`** — same (GET and PATCH) ✅ COMPLETED
4. **Fix `insights/revenue/route.ts`** — proxy to backend `/analytics/revenue` instead of hardcoded JSON ✅ Verified real proxy
5. **Fix `reviews/action/route.ts`** — proxy to backend `/trips/{trip_id}/review/action` ✅ Already had partial fix, completed
6. **Fix `inbox/route.ts`** — hardcoded URL ✅ COMPLETED
7. **Fix `system/unified-state/route.ts`** — hardcoded URL ✅ COMPLETED
8. **Fix `trips/route.ts`** — hardcoded URL ✅ COMPLETED
9. **Fix `trips/[id]/review/action/route.ts`** — hardcoded URL ✅ COMPLETED
10. **Fix `stats/route.ts`** — hardcoded URL ✅ COMPLETED

### Phase 2: Inbox Routes ✅ COMPLETED 2026-04-24

11. **Fix `inbox/stats/route.ts`** — computes from `/trips` backend data ✅ Already working
12. **Fix `inbox/assign/route.ts`** — proxies to backend `/trips/{trip_id}/assign` ✅ Already working
13. **Fix `inbox/[tripId]/snooze/route.ts`** — proxies to backend ✅ Already working

### Phase 3: Suitability Acknowledge ✅ COMPLETED 2026-04-24

14. ~~**Add backend endpoint** `POST /trips/{trip_id}/suitability/acknowledge` in `server.py`~~ ✅ Already existed (line 843)
15. **Add BFF route** `frontend/src/app/api/trips/[id]/suitability/acknowledge/route.ts` ✅ COMPLETED

### Phase 4: Agent Drill-Down ✅ COMPLETED 2026-04-24

16. ~~**Add backend endpoint** `GET /analytics/agent/{agent_id}/drill-down` in `server.py`~~ ✅ Already exists (line 936)
17. **Fix BFF** `insights/agent-trips/route.ts` to call real backend endpoint ✅ COMPLETED
18. **Fix ANALYTICS_SERVICE_URL** in 6 insight routes → `SPINE_API_URL` ✅ COMPLETED

### Phase 5: Orphaned Routes ✅ COMPLETED 2026-04-24

19. **BFF** `api/assignments/route.ts` → proxy to `GET /assignments` ✅ COMPLETED
20. **BFF** `api/health/route.ts` → proxy to `GET /health` ✅ COMPLETED
21. **BFF** `api/items/route.ts` → proxy to `GET /items` ✅ COMPLETED
22. **BFF** `api/runs/route.ts` → proxy to `GET /runs` ✅ COMPLETED
23. **BFF** `api/runs/[id]/route.ts` → proxy to `GET /runs/{run_id}` ✅ COMPLETED
24. **BFF** `api/runs/[id]/events/route.ts` → proxy to `GET /runs/{run_id}/events` ✅ COMPLETED
25. **BFF** `api/runs/[id]/steps/[step_name]/route.ts` → proxy to `GET /runs/{run_id}/steps/{step_name}` ✅ COMPLETED
26. **BFF** `api/trips/[id]/unassign/route.ts` → proxy to `POST /trips/{trip_id}/unassign` ✅ COMPLETED

---

## Verification

- ✅ Build passes: `npm run build` (Next.js 16.2.4)
- ✅ Tests pass: 670 passed, 13 skipped (backend)
- ✅ Frontend build includes new route `/api/trips/[id]/suitability/acknowledge`
- ✅ No hardcoded `localhost:8000` URLs remain (verified via grep)
