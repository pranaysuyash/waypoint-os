# Agency Command Center SSOT & UX Unslop Audit (`/overview`, `/inbox`, `/reviews`)

- **Date:** 2026-11-11
- **Status:** Implemented & Verified (Backend + Frontend + Live Postgres/Browser E2E)
- **Governing Doctrines:** `AGENTS.md`, `OPERATING_DOCTRINE.md` (v8.2), `REVIEW_DOCTRINE.md` (v1.3), `EXPLORATION_DOCTRINE.md` (v1.1), `ARCHITECTURE_DOCTRINE.md` (v1.1), `TESTING_DOCTRINE.md` (v1.1), `DOCUMENTATION_DOCTRINE.md` (v1.1)
- **Canonical Prior Anchors Checked (Supersession & Intent):** `FND-0120` (workspace `"active"` in-trip status), `FND-0270` (review action history), `FND-0302` (required rejection/revision reasons), `FND-0305` (real webhook `ChannelMessagesPanel`), `FND-0402` (overview react-query migration), `FND-0406` (channel feed refresh)

---

## 1. Council Orchestrator Manifest & Coverage Analysis

- **Orchestrator Protocol:** `$council-orchestrator` (`/Users/pranay/Projects/skills/council-orchestrator/SKILL.md`)
- **Lead Persona:** **Elena Rostova (`P2-OWNER-01`)** — Agency Owner (`Docs/personas/PERSONA_AGENCY_OWNER_ELENA.md`)
- **Participating Core Seats:**
  1. **Marcus Chen (`P3-JUNIOR-01`)** — Junior Agent (`Docs/personas/PERSONA_JUNIOR_AGENT_MARCUS.md`): daily triage speed across `/overview`, `/inbox`, and `PlanningTripCard`.
  2. **Siddharth Mehta (`P9-PLATFORM-01`)** — Platform Reliability (`Docs/personas/PERSONA_PLATFORM_RELIABILITY_SIDDHARTH.md`): SSOT counts, truncation bugs, Postgres query scaling, cache/consistency invariants.
  3. **Clara Sterling (`P13-LEGAL-01`)** — Legal & Audit Compliance (`Docs/personas/PERSONA_LEGAL_COMPLIANCE_CLARA.md`): escalation policy integrity, `STOP_NEEDS_REVIEW` / `FND-0302` audit preservation, honest incomplete-data display.
  4. **Mateo Rossi (`P8-ARBITRAGE-01`)** — Yield & Multi-Currency Accuracy (`Docs/personas/PERSONA_REVENUE_ARBITRAGE_MATEO.md`): multi-currency budget rendering and quote value rollups.
- **Bounded Specialist Seats:**
  5. **UI Craft & Unslop Auditor** (`unslop` skill + `signs.md`): nested cards, redundant navigation, unformatted numbers, screaming uppercase pills, viewport hogging.
  6. **Regression & Contract Skeptic** (`TESTING_DOCTRINE.md` + `REVIEW_DOCTRINE.md` §1A + `systematic-debugging`): fixture parity (`tests/test_integrity.py` `VALID_STAGES`), BFF route tests, Vitest component contracts.
- **Coverage Gaps & Unknowns Recorded:**
  - *Currency Exchange Normalization:* For `Total Value in Progress` when multiple currencies exist in the pending queue, live FX rate conversion is out of scope for static aggregation; display single-currency totals cleanly or multi-currency breakdown without fabricating FX conversion or prepending `$`.
  - *Full Tenant Scale Ceiling:* Verified on live Postgres tenant `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b` (`Test`, `48,767` trips). Tenants growing to `100k+` encrypted rows will eventually benefit from SQL-indexed computed summary columns for `requires_review`, though selective projection currently executes in `~0.66s`.

---

## 2. Live Runtime Ground Truth (2026-11-11 Evidence)

Direct inspection against Postgres (`trips` for `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`) + running `:8000`/`:3005` services + Chrome DevTools screenshots:

| Metric / Surface | Postgres Ground Truth (`Test`, `48,767` trips) | Current Live API / UI Displayed | Root Cause |
| --- | --- | --- | --- |
| Total Trips | `48,767` (`assigned: 42,218`, `new: 3,896`, `in_progress: 1,849`, `incomplete: 582`, `active: 202`, `completed: 13`, `blocked: 5`, `cancelled: 2`) | `canonical_total: 10,000` | `DashboardAggregator.get_unified_state` hardcodes `TripStore.list_trip_summaries(limit=10000)` (`src/services/dashboard_aggregator.py:84`). |
| Workspace / Planning Count | `44,274` (`assigned + in_progress + ready_to_quote + ready_to_book + blocked + active`) | `9,188` on StatCard & `Planning Progress` header vs `10,000` inside `Planning Progress` bullets (`9867 + 83 + 5 + 45`) | 1) `DashboardAggregator` truncates at 10k AND only sums `assigned + in_progress` (`:184`). 2) `/api/pipeline/route.ts:14` fetches `/trips?limit=10000` and counts only newest 10k items. |
| Lead Inbox Count | `4,478` (`3,896 new + 582 incomplete`) | `599` on `/overview` vs `4478` on `/inbox` | `DashboardAggregator` sets `inbox_lead_count = stages.get("new", 0)` on the truncated 10k sample instead of `_INBOX_STATUSES` over all trips. |
| False Orphans (`System Check`) | `0` true unknown-status rows (`202 active` + `5 blocked` are valid lifecycle statuses per `FND-0120`) | `46` false routing issues (`orphan_count: 46`) | `VALID_STAGES` only lists 6 legacy statuses (`dashboard_aggregator.py:11`), classifying valid `active` / `blocked` workspace rows into `orphans`. |
| Pending Quote Reviews | `402` trips with `analytics.requires_review == True` | `127` on `/overview` & `/reviews` summary vs `All 25` loaded tabs & warning banner | `get_pending_reviews` (`spine_api/routers/analytics.py:198`) calls `TripStore.list_trips(limit=1000)` -> misses 377 pending reviews; `unifiedState` stops at `10,000` -> reports `127` instead of `402`. |

---

## 3. Supersession & Preservation Matrix

| Element | Original Intent | Decision | Rationale |
| --- | --- | --- | --- |
| `VALID_STAGES` (`src/services/dashboard_aggregator.py:11`) | 6-key histogram for `scenario_alpha` (`tests/test_integrity.py:83`) | **KEEP legacy constant + extend known lifecycle recognition** | `test_alpha_stage_distribution` asserts exact 6-key dict from `VALID_STAGES`. Keeping `VALID_STAGES` untouched while classifying `WORKSPACE_TRIP_STATUS_LIST`, `_INBOX_STATUSES`, and terminal/review statuses as known lifecycle states prevents false orphans while preserving 100% fixture test compatibility. |
| `"active"` stage (`FND-0120`, `trip-domain.ts`) | Canonical `in_trip` alias in workspace pipeline | **PRESERVE + label properly** | Never drop `"active"`; map `"active": "In trip"` in `PipelineBar.getStageLabel` (`overview/PageClient.tsx`). |
| `ChannelMessagesPanel` (`FND-0305`, `FND-0406`) | Live webhook message feed + `"Use for intake ->"` prefill + refresh | **PRESERVE + collapse by default in `/inbox`** | Currently renders 48 test email rows above all lead cards, pushing the actual Lead Inbox off-screen. Adding `defaultCollapsed` (default `false` for standalone tests, `true` in `/inbox/PageClient.tsx`) keeps live latest-message preview + one-click intake handoff + `Expand (N)` while putting lead cards above the fold. |
| `Jump To` + `Latest Trips Status` (`overview/PageClient.tsx`) | Right-rail shortcuts & recent-sample status breakdown | **RETAIN routes/test contracts cleanly + format numbers + label honestly** | Removing `Jump To` or changing `'Latest Trips Status · showing X of Y'` blindly would break `overview/__tests__/page.test.tsx` assertions on links/labels. Reconciling counts to exact DB truth, adding `.toLocaleString('en-IN')`, and refining card weight avoids visual repetition cleanly. |
| `FND-0270` & `FND-0302` (`src/analytics/review.py`) | Owner approval history & mandatory written reason on reject/revision | **PRESERVE strictly** | Compliance invariant (`Clara`). Only humanize display copy (`STOP_NEEDS_REVIEW`) cleanly. |

---

## 4. Defect & Unslop Resolution Design by Surface

1. **Backend & BFF SSOT (`src/services/dashboard_aggregator.py`, `spine_api/persistence.py`, `spine_api/server.py`, `spine_api/routers/analytics.py`, `src/analytics/review.py`, `frontend/src/app/api/pipeline/route.ts`):**
   - Add `SQLTripStore.list_unified_state_projections(agency_id)` (and non-truncated `count_trips_by_status(agency_id)`) + fast filtered pending-review loader so `DashboardAggregator.get_unified_state` aggregates ALL trips (zero `limit=10000` cap) in `<1s` while respecting existing `TripStore.list_trip_summaries` test mocks!
   - Expose `statusCounts` in `GET /trips` via SQL `GROUP BY status` (`count_trips_by_status`) and consume `statusCounts` in `/api/pipeline/route.ts` (keeping `transformSpineTripsResponseToTrips` fallback for existing route unit tests) -> eliminates `10,000`-trip truncation & HTTP payload bloat.
   - Fix `get_pending_reviews` (`spine_api/routers/analytics.py`) to load all pending-review trips without the `limit=1000` cap -> `All` matches `Pending` (`402 == 402`), eliminating the mismatch warning banner.
   - Compute `pending_review_value_by_currency` and `primary_review_currency` in `DashboardAggregator.get_unified_state`.
   - Humanize `STOP_NEEDS_REVIEW` reason in `trip_to_review` (`src/analytics/review.py`) and UI (`humanizeReviewReason` in `reviews/PageClient.tsx`).

2. **Lower `/overview` (`frontend/src/app/(agency)/overview/PageClient.tsx`, `frontend/src/components/workspace/PlanningTripCard.tsx`):**
   - Format all KPI counters, `PipelineBar`, `Jump To`, and `Latest Trips Status` numbers with `.toLocaleString('en-IN')`.
   - Map `active` -> `'In trip'` in `PipelineBar.getStageLabel` and unify bar/header totals (`stageTotal == planningTripsTotal`).
   - Flatten `PlanningTripCard`: remove heavy gradient/shadow wrapper (`linear-gradient`, `0 18px 44px`), flatten nested `CONTACT DETAILS` / `MISSING TRIP DETAILS` / `Next step` bordered sub-cards into crisp hairline rows & inline links, capitalize next-action sentence (`Confirm budget range...`), and replace screaming uppercase micro-headers (`MISSING CUSTOMER DETAILS`, `5 MATCHING TRIPS`) with refined mixed case.

3. **Quote Review (`/reviews` — `frontend/src/app/(agency)/reviews/PageClient.tsx`):**
   - Remove hardcoded `<DollarSign />` before currency-formatted budgets (`$ ₹0 INR` defect) -> use neutral `<Wallet />` icon and show `'Budget to confirm'` when `value <= 0`.
   - Format `Total Value in Progress` using `primary_review_currency` / `pending_review_value_by_currency` (`formatMoneyCompact`) + locale-formatted integer counts (`127` / `402`).
   - Calibrate `ReviewCard` visual severity (stop painting every >2d item in uniform red border/tint; reserve red for escalated / SLA-breached / flagged risk items).
   - Add responsive pagination (`25` per page with `Show more` / pager) so loading 402 real reviews stays instant in DOM.

4. **Lead Inbox (`/inbox` — `PageClient.tsx`, `ChannelMessagesPanel.tsx`, `TripCard.tsx`, `ComposableFilterBar.tsx`, `inbox-helpers.ts`):**
   - Pass `defaultCollapsed={true}` to `<ChannelMessagesPanel />` in `inbox/PageClient.tsx`, rendering a compact summary strip with latest inbound preview, `"Use for intake ->"`, and `"Show messages (N)"` expand button.
   - Add `formatFlagLabel(flag)` in `inbox-helpers.ts` and use it unconditionally in `TripCard` `FlagBadge` so `details_unclear` -> `Details unclear` and `incomplete` -> `Incomplete details`.
   - Remove screaming `uppercase` utility on `TripCardSLA` & `TripCardStageBadge`, widen search input (`Search customer, destination, ref…`) so placeholder never truncates, and locale-format total counts (`4,478 leads total`, `All (4,478)`).

---

## 5. Genuine Decisions / Questions for Owner

- **None blocking this execution pass:** Every defect above is an objective data-truth discrepancy (`9,188 vs 10,000 vs 44,274`; `25 vs 127 vs 402`), currency symbol corruption (`$ ₹0 INR`), leaked internal enum (`STOP_NEEDS_REVIEW`, `details_unclear`), or layout obstruction (`ChannelMessagesPanel` pushing leads below the fold).
- **Deferred Strategic Question (for future backlog, non-blocking):** Confirm whether `Test` agency's `~48,767` historical seeded/synthetic trips should retain all legacy `incomplete` / `new` rows for stress benchmarking or introduce a workspace-level archive filter (`archived_at` / age cutoff). No records are altered or deleted in this pass.

---

## 6. Post-Implementation Verification Receipts (2026-11-11)

- **Backend Static & Tests:** `uv run ruff check ...` passed with zero issues; `uv run pytest tests/test_integrity.py tests/test_system_dashboard_router_behavior.py tests/test_analytics_router_contract.py tests/test_review_logic.py tests/test_review_policy_escalation.py tests/test_command_center_ssot_regressions.py -q` passed `51 passed, 1 warning in 11.17s`.
- **Frontend Static & Tests:** `npx tsc --noEmit` exited `0`; ESLint exited `0` (`0` errors, `1` pre-existing `no-restricted-globals` warning on bare `fetch` in `ChannelMessagesPanel.tsx`); Vitest passed `17` files / `161` tests (`CommandCenterInboxOverhaul.test.tsx`, `ChannelMessagesPanel.test.tsx`, `inbox/__tests__/page.test.tsx` re-verified `11/11` after final edit).
- **Live Browser & Postgres Parity (`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`, `48,767` rows):**
  - `/overview`: `44,274` trips in planning (`42,218` waiting for options + `1,849` planning in progress + `5` needs attention + `202` in trip), `4,478` enquiries, `402` quotes to review, `0` System Check items, flattened `PlanningTripCard`.
  - `/inbox`: `4,478 leads total`, `All (4,478)`, collapsed `Channel Messages · 48 recent` preview bar (expands cleanly on click), unclipped search placeholder, humanized `Details unclear` / `Incomplete details`, natural-case SLA & stage pills.
  - `/reviews`: `402` pending matching `All 402 | Pending 402` (mismatch alert eliminated), `To confirm` KPI (`Budgets awaiting entry`), `<Wallet /> Budget to confirm` (no `$ ₹0 INR`), humanized `Policy hold: requires owner review`, 25-row incremental pagination.
