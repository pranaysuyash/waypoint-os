# Worklog: Planning Surfaces SSOT, Discovery & UX Overhaul (`/trips`, `/quotes`, `/bookings`)

- **Date:** 2026-11-11
- **Status:** Verified & Complete (pending git commit upon operator confirmation)
- **Exploration & Council Record:** `Docs/exploration/PLANNING_SURFACES_SSOT_AND_UX_AUDIT_2026-11-11.md`
- **Visual Proof Artifact:** `PLANNING_PRE_POST_VISUAL_PROOF.md` (before/after PNGs captured from Chrome DevTools against live `:8000` + `:3005` + PostgreSQL)

---

## 1. Problems Solved

1. **`/trips` (`Trips in Planning`) SSOT Contradiction & Scale Cliff:**
   - Replaced silent `limit=100` client-side totals with canonical server `total` and `statusCounts` from `GET /trips` (`44,274 in planning` matching `/overview` identically instead of `100 in planning`).
   - Added server-backed search (`q`), SQL-aggregated status tabs (`All (44,274)`, `Assigned (42,218)`, `In progress (1,849)`, `Blocked (5)`, `In trip (202)`), and `offset` pagination (`PAGE_SIZE = 24`).
   - Fixed scoped missing-details summary copy (`24 of 24 on page need details`), removed duplicated `"Next:"` prefixes and multi-stop stage clutter from `PlanningTripCard`, and fixed `Shell.tsx` breadcrumb CSS `capitalize` mutating `"Trips in Planning"` into `"Trips In Planning"`.
2. **`/quotes` (`Quotes & Commercial Proposals`) Dead-End Default & Schema Leaks:**
   - Added `scope="quotes"` filtering & ranking on `GET /trips` so `/quotes` opens immediately onto trips that actually have persisted itinerary/quote data (`Emirates · $3,570` / `16` quote-capable trips) with clean `With Quote Data` / `All Planning Trips` toggle, live search filter, and automatic empty-scope fallback.
   - Kept backend `GET /api/v1/trips/{id}/quotes` `missing` keys backward-compatible for `tests/test_quotes_read_model.py` while translating raw paths (`strategy.recommended_option`, `decision.budget_breakdown`, `commercial_pricing`) into operator guidance in `QuotesPageClient`, removing developer meta-prose (`"Nothing on this page is invented."`), and balancing header CTA hierarchy.
3. **`/bookings` (`Bookings`) Raw Test-ID Leaks & Empty Default State:**
   - Removed duplicate local `formatTripPickerLabel` in `bookings/PageClient.tsx` and unified onto canonical `@/lib/trip-picker-label` (`formatTripPickerLabel`, enhanced to surface `strategy.recommended_option.name` when incomplete and strip raw `tc_roundtrip_*` / `_c` test prefixes).
   - Added `scope="bookings"` ranking (populated `booking_data` dossiers > pending customer submissions > stage/collection-link candidates, strictly excluding `booking_data` / `pending_booking_data` PII blobs from generic list payloads), opening `/bookings` directly onto populated dossier records (`John Doe`, `Jane Doe`, `INR 120,000` agreed / `INR 50,000` paid / `INR 70,000` balance due).

---

## 2. Files Modified / Added

### Backend
- `spine_api/persistence.py` — `_trip_search_matches`, `_quote_scope_rank`, `_has_booking_dossier_payload`, `_booking_dossier_rank`, `_trip_matches_scope`; `offset`, `q`, `scope`, and `count_trips_by_status` on `FileTripStore`, `SQLTripStore`, and `TripStore`; stripped `booking_data`/`pending_booking_data` from `FileTripStore.list_trips` return dicts for SQL parity.
- `spine_api/server.py` — Extended `GET /trips` with `offset`, `q`, `scope`, `limit <= 500`, and `statusCounts`.
- `tests/test_planning_surfaces_regressions.py` — Added HTTP `GET /trips` pagination/search/scope/PII-exclusion tests + live Postgres `SQLTripStore` test.

### Frontend & BFF
- `frontend/src/app/api/trips/route.ts` — Preserves valid caller `status` subsets on `view=workspace`, forwards `q`, `scope`, `offset`, `statusCounts`.
- `frontend/src/lib/api-client.ts` & `frontend/src/hooks/useTrips.ts` — Added `q`, `scope`, `offset`, optional `statusCounts` return typing, and `UseTripsParams`.
- `frontend/src/lib/trip-picker-label.ts` — Strategy option fallback naming & test-ID reference normalization.
- `frontend/src/components/layouts/Shell.tsx` — Removed CSS `capitalize` on canonical section labels & exported `getPageLabel`.
- `frontend/src/components/workspace/PlanningTripCard.tsx` — Stripped `"Next:"` prefixes and simplified workspace stage badge row.
- `frontend/src/app/(agency)/trips/PageClient.tsx` — SSOT total/statusCounts header, search, status tabs, and URL pagination.
- `frontend/src/app/(agency)/quotes/PageClient.tsx` — `scope: 'quotes'` default + toggle/search + humanized missing-input translation.
- `frontend/src/app/(agency)/bookings/PageClient.tsx` — Canonical `formatTripPickerLabel` + `scope: 'bookings'` default + toggle/search.
- Updated/extended tests: `frontend/src/app/(agency)/trips/__tests__/page.test.tsx`, `quotes/__tests__/page.test.tsx`, `bookings/__tests__/page.test.tsx`, `app/api/trips/__tests__/route.test.ts`, `components/layouts/__tests__/Shell.test.tsx`.

---

## 3. Verification Summary

- **Frontend:** `npx tsc --noEmit` (0 errors); `npx eslint` on all touched files (0 errors, 1 pre-existing warning on `quotes/PageClient.tsx` L188 `fetch`); `npx vitest run` across all 8 related test suites — **8 test files, 53/53 tests passed**.
- **Backend:** `uv run ruff check spine_api/persistence.py spine_api/server.py tests/test_planning_surfaces_regressions.py` (All checks passed); `uv run pytest tests/test_planning_surfaces_regressions.py tests/test_quotes_read_model.py tests/test_booking_data.py tests/test_booking_collection.py` against live PostgreSQL — **137 passed**.
- **Live Browser E2E (Chrome DevTools `:3005` + `:8000`):** Verified `/trips` (`44,274 in planning`, `Blocked (5)`, `?q=Paris`, 0 console errors), `/quotes` (`With Quote Data (16)` default `$3,570` / `Emirates` + humanized toggle check, 0 console errors), and `/bookings` (`Active Dossiers (13,906)` default `John Doe` / `INR 120,000`, 2 pre-existing 404 console logs from absent `/pending-booking-data` probe).
