# Agency Command Center SSOT & UX Overhaul (`/overview`, `/inbox`, `/reviews`)

- **Date:** 2026-11-11
- **Exploration / Council Record:** [COMMAND_CENTER_SSOT_AND_UX_AUDIT_2026-11-11.md](../exploration/COMMAND_CENTER_SSOT_AND_UX_AUDIT_2026-11-11.md)
- **Evidence Tier & Sensitivity:** Tier 2 / `S2` (real FastAPI/SQL/BFF unit & contract regressions) + `S3` (live Postgres `48,767`-trip tenant `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b` & Chrome DevTools live UI verification across `:8000` / `:3005`).

## 1. Outcome Summary

Eliminated systematic cross-page counter contradictions (caused by hardcoded `10,000` / `5,000` / `1,000` pagination caps and incomplete status sets), fixed `$ ₹0 INR` multi-currency prefix corruption and leaked internal flags (`STOP_NEEDS_REVIEW`, `details_unclear`), flattened `PlanningTripCard` nested box clutter, and reclaimed `/inbox` above-the-fold triage capacity by collapsing `ChannelMessagesPanel` behind a compact single-row live preview strip.

| Surface Metric | Before | After (Live Postgres SSOT) |
| --- | --- | --- |
| Workspace Planning Total (`/overview`, `/api/pipeline`) | Contradictory `9,188` vs `10,000` | Unified **`44,274`** (`42,218 + 1,849 + 5 + 202`) |
| Pipeline `'active'` Stage Label (`PipelineBar`) | Raw `'active · 45'` | **`In trip · 202`** |
| False Orphan Count (`System Check`) | `46` false orphans (`blocked`/`active` unrecognized) | **`0`** (`consistent: true`) |
| Quote Review Queue (`/reviews` vs `/overview`) | `All 25` vs `127` mismatch warning | Unified **`402`** (`All 402 \| Pending 402`, paginated by 25) |
| Quote Value & Currency Display (`/reviews`) | `$ ₹0 INR` / hardcoded `$0.0k` | `<Wallet /> Budget to confirm` & **`To confirm`** KPI + currency-aware rollups |
| Review Hold Jargon | `STOP_NEEDS_REVIEW` | **`Policy hold: requires owner review`** |
| Lead Inbox Viewport (`/inbox`) | 48-row `Channel Messages` pushed all leads off-screen; clipped search placeholder; `details_unclear`; `INTAKE` | Compact 1-row `Channel Messages · 48 recent` preview bar (`Show feed (48)` toggle); unclipped search; **`Details unclear`**; calm sentence-case pills; **`4,478 leads total`** |

## 2. Files Changed

### Backend & SSOT Data Truth
- `spine_api/persistence.py` — Added SQL `count_trips_by_status`, selective `list_unified_state_projections` (`~0.657s` across 48,767 rows), and `list_pending_review_trips`; lifted `FileTripStore.count_trips` 10k cap; fixed `TripStore.list_trip_summaries` `offset` forwarding and `SQLTripStore.list_trip_summaries` RLS scoping.
- `src/services/dashboard_aggregator.py` — Preserved `VALID_STAGES` compatibility while splitting lifecycle classification into `INBOX_LIFECYCLE_STATUSES`, `WORKSPACE_LIFECYCLE_STATUSES`, `TERMINAL_AND_REVIEW_STATUSES`, and `KNOWN_LIFECYCLE_STATUSES`; loaded untruncated projections without mock-signature breakage; added `pending_review_value_by_currency` and `primary_review_currency`.
- `spine_api/routers/analytics.py` & `src/analytics/review.py` — Removed the 1,000-row pending review cap, added `_humanize_review_reason`, and added `extracted.budget` fallback in `trip_to_review`.
- `spine_api/server.py` & `spine_api/routers/inbox.py` — Exposed SQL `statusCounts` on `GET /trips` and lifted the `5,000`-row inbox cap.

### Frontend BFF, Lower `/overview`, `/reviews`, and `/inbox`
- `frontend/src/app/api/pipeline/route.ts` — Consumes `statusCounts` directly via `limit=1` (preserving legacy `items` fallback for route tests).
- `frontend/src/hooks/useUnifiedState.ts` — Typed `pending_review_value_by_currency` and `primary_review_currency`.
- `frontend/src/app/(agency)/overview/PageClient.tsx` & `useOverviewSummary.ts` — Locale-formatted all counters (`en-IN`), mapped `active` → `In trip`, and synchronized `PipelineBar` header/bullet totals.
- `frontend/src/components/workspace/PlanningTripCard.tsx` — Flattened nested sub-cards/heavy shadows to hairline `var(--bg-surface)` rows, capitalized `nextAction`, and calmed micro-headers while retaining all inline fix links.
- `frontend/src/app/(agency)/reviews/PageClient.tsx` — Fixed `$ ₹0 INR` via `<Wallet />` and `'Budget to confirm'`, formatted currency-aware rollups (`To confirm` when budgets are pending entry), humanized `STOP_NEEDS_REVIEW`, calibrated severity borders, and added 25-row incremental pagination (`Show N more` / `Show all`).
- `frontend/src/lib/inbox-helpers.ts`, `frontend/src/components/inbox/TripCard.tsx`, `frontend/src/components/inbox/ChannelMessagesPanel.tsx`, `frontend/src/components/inbox/ComposableFilterBar.tsx`, and `frontend/src/app/(agency)/inbox/PageClient.tsx` — Added `formatFlagLabel` (`details_unclear` → `Details unclear`), calmed SLA/Stage pills, added `defaultCollapsed` toggle mode on `ChannelMessagesPanel` preserving `FND-0305` / `FND-0406` intake handoff, widened search input (`Search customer, destination, ref…`), and formatted `All (4,478)` / `4,478 leads total`.

### Regression Tests Added
- `tests/test_command_center_ssot_regressions.py`
- `frontend/src/app/api/pipeline/__tests__/status-counts.test.ts`
- `frontend/src/app/(agency)/reviews/__tests__/ReviewsOverhaul.test.tsx`
- `frontend/src/components/inbox/__tests__/CommandCenterInboxOverhaul.test.tsx`

## 3. Verification Receipts

1. **Backend Lint (`BypassSandbox: false`):**
   - `uv run ruff check spine_api/persistence.py src/services/dashboard_aggregator.py spine_api/routers/analytics.py src/analytics/review.py spine_api/routers/inbox.py spine_api/server.py tests/test_command_center_ssot_regressions.py` → `All checks passed!`
2. **Backend Tests (`BypassSandbox: true` for Postgres localhost socket):**
   - `uv run pytest tests/test_integrity.py tests/test_system_dashboard_router_behavior.py tests/test_analytics_router_contract.py tests/test_review_logic.py tests/test_review_policy_escalation.py tests/test_command_center_ssot_regressions.py -q` → `51 passed, 1 warning in 11.17s`.
3. **Frontend Typecheck & ESLint (`BypassSandbox: false`):**
   - `cd frontend && npx tsc --noEmit` → exit `0`.
   - `./node_modules/.bin/eslint -c eslint.config.mjs ...` (all 14 modified/new frontend files) → `0 errors` (`1` pre-existing `no-restricted-globals` warning on bare `fetch` in `ChannelMessagesPanel.tsx`).
4. **Frontend Tests (`BypassSandbox: false`):**
   - `npm test --prefix frontend -- "src/app/(agency)/overview" "src/app/(agency)/reviews" "src/app/(agency)/inbox" "src/components/inbox" "src/app/api/pipeline" "src/lib/__tests__/inbox-helpers.test.ts" --run` → `17 test files, 161/161 passed`.
   - Re-ran inbox subset (`ChannelMessagesPanel.test.tsx`, `CommandCenterInboxOverhaul.test.tsx`, `inbox/__tests__/page.test.tsx`) after final `ChannelMessagesPanel.tsx` ESLint fix → `3 test files, 11/11 passed`.
5. **Live Browser Verification (Chrome DevTools MCP against `:8000` & `:3005`, Console clean with 0 errors):**
   - `/overview` top & lower fold verified (`44,274`, `4,478`, `402`, `0` System Check, `In trip · 202`, flattened `PlanningTripCard`).
   - `/inbox` verified (`Channel Messages · 48 recent` collapsed strip, interactive `Show feed (48)` toggle expands to `48` rows, leads immediately visible above the fold, `Details unclear`, unclipped search placeholder, `4,478 leads total`).
   - `/reviews` verified (`402` matching `All 402 | Pending 402`, `To confirm`, `<Wallet /> Budget to confirm`, zero `$ ₹0 INR`).
