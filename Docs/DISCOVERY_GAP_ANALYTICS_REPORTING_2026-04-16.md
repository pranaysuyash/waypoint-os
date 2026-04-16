# Discovery Gap Analysis: Analytics/Reporting Pipeline

**Date**: 2026-04-16
**Gap Register**: #12 (P2 — owner visibility)
**Scope**: Owner dashboard, conversion funnel, agent performance metrics, KPI tracking, revenue tracking. NOT: audit trail logging (#13), customer lifecycle scoring (#06).

---

## 1. Executive Summary

The frontend has a fully designed analytics page (`/owner/insights`) with TypeScript types, API clients, and mock data. The backend has **zero analytics endpoints** — every `/api/insights/*`, `/api/pipeline/*`, `/api/team/*`, `/api/revenue/*` call returns 404. The 9 KPIs defined in `LEAD_LIFECYCLE_AND_RETENTION.md` have zero computation. The owner has no visibility into pipeline performance, agent productivity, revenue, or conversion rates.

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L179-189 | 7 missing KPIs: repeat customer rate, lead-to-booking conversion, quote-to-close rate, CSAT, cancellation rate, avg turnaround, margin adherence | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L81-96, L260-262 | Owner needs: quote quality review, agent dashboard, cross-trip analytics — all missing or stubs | Docs/ |
| `LEAD_LIFECYCLE_AND_RETENTION.md` L193-202 | 9 KPIs: quote-to-reply rate, quote-to-book rate, silent-after-quote rate, avg revisions, planning-fee conversion, repeat booking rate, reactivation conversion, churn rate, loss-reason distribution | Docs/ |
| `DISCOVERY_GAP_CUSTOMER_LIFECYCLE` | Phase 4: Track 9 KPIs | #06 deep-dive |
| `DISCOVERY_GAP_DATA_PERSISTENCE` L99 | PC-04: "Cross-trip analytics: Impossible — no trip history persisted" | #02 deep-dive |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `frontend/src/app/owner/insights/page.tsx` | Full analytics page with mock data (`MOCK_PIPELINE_METRICS`, `MOCK_TEAM_METRICS`) | **Mock only** — no real data |
| `frontend/src/hooks/useGovernance.ts` L143-161 | `usePipelineMetrics(timeRange)` — calls API, returns empty | **Hook only** |
| `frontend/src/hooks/useGovernance.ts` L206-251 | `useTeamMetrics`, `useBottleneckAnalysis`, `useRevenueMetrics` | **Hooks only** |
| `frontend/src/lib/governance-api.ts` L72-114 | 7 analytics endpoints defined | **API client only** — backend 404 |
| `frontend/src/types/governance.ts` L65-126 | `InsightsSummary`, `StageMetrics`, `TeamMemberMetrics`, `RevenueMetrics`, `BottleneckAnalysis` TypeScript types | **Types only** |
| `frontend/src/app/inbox/page.tsx` | Inbox with "Needs Review" filter | **Hardcoded data** |

### What's NOT Implemented

- No backend analytics computation (0 of 9 KPIs)
- No backend analytics endpoints (all 404)
- No conversion funnel tracking
- No agent performance metrics
- No revenue tracking or margin reporting
- No historical trend data
- No cohort analysis

---

## 3-4. Gap Taxonomy & Data Model

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **AN-01** | KPI computation engine | None | All owner visibility |
| **AN-02** | Analytics API endpoints | Frontend types only, backend 404 | Dashboard rendering |
| **AN-03** | Conversion funnel tracking | None — no quote-to-book pipeline data | Conversion optimization |
| **AN-04** | Agent performance metrics | None — no trip assignment, no CSAT data | Owner team management |
| **AN-05** | Revenue/margin reporting | None — no financial state (#04) | Financial visibility |

```python
@dataclass
class KPIs:
    # From LEAD_LIFECYCLE_AND_RETENTION.md
    quote_to_reply_rate: float      # % of quotes that get a reply
    quote_to_book_rate: float       # % of quotes that convert to bookings
    silent_after_quote_rate: float  # % of quotes with no response after N days
    avg_revisions_per_trip: float   # average number of quote revisions
    planning_fee_conversion: float  # % of token requests that convert
    repeat_booking_rate: float      # % of customers who book again
    reactivation_conversion: float  # % of dormant customers who return
    churn_rate: float               # % of active customers who churn
    loss_reason_distribution: dict  # {"price": 0.4, "timing": 0.3, ...}
```

---

## 5-8. Phase-In, Decisions, Risks, Out of Scope

### Phase 1: Core KPI Endpoints (P2, ~2-3 days, blocked by #02, #06)

1. Implement 4 core KPI endpoints: pipeline metrics, team metrics, conversion funnel, revenue summary
2. Wire frontend analytics page to real data
3. Add daily/weekly/monthly time range support

**Acceptance**: Owner `/insights` page shows real conversion rates, agent productivity, and revenue numbers instead of mock data.

### Phase 2: Conversion Funnel + Agent Dashboard (P2, ~2-3 days, blocked by #06, #08)

1. Track pipeline stage transitions (NEW_LEAD → QUOTE_SENT → WON → BOOKED → COMPLETED)
2. Compute per-agent metrics from trip assignments
3. Add loss reason categorization from cancelled/lost trips

**Acceptance**: Owner can see "42 leads this month, 18 quoted, 8 booked, 5 completed. Conversion rate: 12%."

### Phase 3: Historical Trends + Export (P3, ~1-2 days)

1. Store KPI snapshots daily for trend analysis
2. Add CSV/PDF export for reports
3. Add cohort analysis (customers acquired in month X, retention over 6 months)

**Acceptance**: Owner can see lead conversion trend over 6 months and export a PDF report.

| Decision | Options | Recommendation |
|----------|---------|----------------|
| KPI storage | (a) Compute on demand from events, (b) Pre-compute daily snapshots, (c) Hybrid | **(c) Hybrid** — snapshots for trends, compute on demand for current |
| Analytics engine | (a) Custom SQL, (b) Metabase, (c) Custom API + frontend charts | **(a) Custom SQL for MVP** — add Metabase later for self-serve |

**Out of Scope**: Real-time streaming analytics, machine learning predictions, A/B test analytics, multi-agency benchmarking, financial reconciliation reports.