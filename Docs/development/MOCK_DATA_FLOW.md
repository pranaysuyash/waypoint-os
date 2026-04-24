# Mock Data Flow: End-to-End Reference

**Last verified:** 2026-04-22
**Status:** All mock routes return 200, all pages render correctly.

## Architecture

```
[Next.js App Router]          [React Hooks]           [Page Components]
  /api/* routes  ──────────►  useGovernance.ts  ────►  owner/reviews/page.tsx
  (mock data or               useTrips.ts             owner/insights/page.tsx
   spine_api proxy)                                   page.tsx (dashboard)
                                                     inbox/page.tsx
                                                     workspace/page.tsx
                                                     workbench/page.tsx
```

Two data sources:
1. **Mock routes** — hardcoded in `frontend/src/app/api/*/route.ts`, return static JSON
2. **Spine-api proxy** — forward to FastAPI backend at `localhost:8000`

## API Routes Inventory

### Mock Routes (static data, no backend dependency)

| Route | File | Returns | Used By |
|-------|------|---------|---------|
| `GET /api/trips` | `api/trips/route.ts` | 7 trips (SGP, BKK, PAR, TYO, NYC, DEL, DXB) | `useTrips` → dashboard, workspace |
| `GET /api/stats` | `api/stats/route.ts` | `{active:7, pendingReview:2, readyToBook:2, needsAttention:1}` derived from trips | dashboard |
| `GET /api/pipeline` | `api/pipeline/route.ts` | 5 pipeline stages | dashboard |
| `GET /api/reviews` | `api/reviews/route.ts` | 3 reviews (2 pending, 1 escalated) | `useReviews` → owner/reviews |
| `POST /api/reviews/action` | `api/reviews/action/route.ts` | `{success: true}` | owner/reviews approve/reject |
| `GET /api/inbox` | `api/inbox/route.ts` | 7 inbox trips with priority/SLA/assignments | `useInboxTrips` → inbox |
| `GET /api/inbox/stats` | `api/inbox/stats/route.ts` | `{total:7, unassigned:1, critical:1, atRisk:2}` | `useInboxStats` |
| `POST /api/inbox/assign` | `api/inbox/assign/route.ts` | `{success: true, assigned: N}` | inbox bulk assign |
| `POST /api/inbox/[tripId]/snooze` | `api/inbox/[tripId]/snooze/route.ts` | `{success: true}` | inbox snooze |
| `GET /api/insights/revenue` | `api/insights/revenue/route.ts` | Revenue metrics ($52k pipeline, $18k booked) | `useRevenueMetrics` → owner/insights |
| `GET /api/insights/alerts` | `api/insights/alerts/route.ts` | `[]` (empty — no alerts) | `useOperationalAlerts` → owner/insights |

### Spine-API Proxy Routes (require FastAPI on :8000)

| Route | Proxies To | Returns | Used By |
|-------|-----------|---------|---------|
| `GET /api/insights/summary` | `localhost:8000/analytics/summary` | 305 inquiries, 2% conv | `useInsightsSummary` → owner/insights |
| `GET /api/insights/pipeline` | `localhost:8000/analytics/pipeline` | 6 pipeline stages | `usePipelineMetrics` → owner/insights |
| `GET /api/insights/team` | `localhost:8000/analytics/team` | 2 agents (Alice, Bob) | `useTeamMetrics` → owner/insights |
| `GET /api/insights/bottlenecks` | `localhost:8000/analytics/bottlenecks` | 1 bottleneck (Feasibility) | `useBottleneckAnalysis` → owner/insights |

### Routes That Exist But Are Broken/Unused

| Route | Issue |
|-------|-------|
| `GET /api/insights/escalations` | Empty directory, no route.ts |
| `GET /api/insights/funnel` | Empty directory, no route.ts |
| `GET /api/team/*` | No route handlers exist (intentionally deferred) |
| `GET /api/audit/*` | No route handlers exist |

## Data Flow by Page

### Dashboard (`/` aka `page.tsx`)
- `useTrips()` → `GET /api/trips` → 7 trips → recent trips list
- `getTripStats()` → `GET /api/stats` → stats cards (7/2/2/1)
- `getPipeline()` → `GET /api/pipeline` → pipeline visualization

### Inbox (`/inbox`)
- `useInboxTrips()` → `GET /api/inbox` → 7 trips with server-computed priority/SLA/assignments
- Assignment action → `POST /api/inbox/assign` → mock success
- Export action → client-side CSV generation from inbox data

### Workspace (`/workspace`)
- `useTrips()` → `GET /api/trips` → 7 trips → active workspace cards

### Workbench (`/workbench`)
- `useWorkbenchStore()` → local state + `GET /api/trips/{id}` → trip processing

### Reviews (`/owner/reviews`)
- `useReviews()` → `GET /api/reviews` → 3 reviews → review cards
- `submitAction()` → `POST /api/reviews/action` → approve/reject

### Insights (`/owner/insights`)
- `useInsightsSummary()` → `GET /api/insights/summary` → summary stats (proxied)
- `usePipelineMetrics()` → `GET /api/insights/pipeline` → velocity bars (proxied)
- `useTeamMetrics()` → `GET /api/insights/team` → team table (proxied)
- `useBottleneckAnalysis()` → `GET /api/insights/bottlenecks` → bottleneck cards (proxied)
- `useRevenueMetrics()` → `GET /api/insights/revenue` → revenue chart (mock)
- `useOperationalAlerts()` → `GET /api/insights/alerts` → alert banner (mock, empty)

## Hook → API → Data Chain

```
useGovernance.ts hooks
  ├── useReviews(filters?)     → governance-api.getReviews()    → GET /api/reviews
  ├── useInsightsSummary(range) → governance-api.getInsightsSummary() → GET /api/insights/summary?range=30d
  ├── usePipelineMetrics(range) → governance-api.getPipelineMetrics() → GET /api/insights/pipeline?range=30d
  ├── useTeamMetrics(range)     → governance-api.getTeamMetrics()     → GET /api/insights/team?range=30d
  ├── useBottleneckAnalysis(range) → governance-api.getBottleneckAnalysis() → GET /api/insights/bottlenecks?range=30d
  ├── useRevenueMetrics(range)  → governance-api.getRevenueMetrics()  → GET /api/insights/revenue?range=30d
  ├── useOperationalAlerts()    → governance-api.getOperationalAlerts() → GET /api/insights/alerts
  ├── useTeamMembers()          → governance-api.getTeamMembers()      → GET /api/team/members (DEFERRED — no auth yet)
  ├── useWorkloadDistribution() → governance-api.getWorkloadDistribution() → GET /api/team/workload (DEFERRED — no auth yet)
  └── useInboxTrips(filters,page,limit) → governance-api.getInboxTrips() → GET /api/inbox (MOCK)

useTrips.ts hooks
  └── useTrips(params)          → api-client.getTrips()              → GET /api/trips

All governance hooks use the delayed-loading pattern:
  - 300ms delay before showing spinner (prevents flicker)
  - Ref-based timeout management
  - useCallback/useEffect lifecycle
```

## Spine-API Endpoints (FastAPI :8000)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/health` | GET | Working |
| `/run` | POST | Working (spine execution) |
| `/runs` | GET | Working (run history) |
| `/trips` | GET | Working (trip list) |
| `/assignments` | GET | Working |
| `/audit` | GET | Working |
| `/analytics/summary` | GET | Working |
| `/analytics/pipeline` | GET | Working |
| `/analytics/team` | GET | Working |
| `/analytics/bottlenecks` | GET | Working |

**Missing from spine_api** (would need mock fallbacks or implementation):
- `/analytics/revenue`
- `/analytics/reviews`
- `/analytics/escalations`
- `/analytics/funnel`
- Alert-related endpoints

## Real API Integration Plan

When switching from mock to real data:

1. **Replace mock routes with spine_api proxy** — the pattern already exists in `insights/summary/route.ts` etc.
2. **Implement missing spine_api endpoints** — revenue, reviews, alerts
3. **Add missing route handlers** — inbox, team, audit
4. **Ensure data shapes match TypeScript types** — `governance.ts` defines the contracts
5. **Remove hardcoded mock data** — each mock route has a `MOCK_*` constant at the top
