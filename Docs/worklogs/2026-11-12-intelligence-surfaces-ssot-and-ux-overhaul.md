# Worklog — Intelligence Surfaces SSOT, Performance & UX Overhaul (2026-11-12)

- **Scope:** Sidebar **INTELLIGENCE** section:
  - `/insights` (`Insights & Analytics`)
  - `/destination-intelligence` (`Destination Intel`)
  - `/audit` (`Trip Fit & Compliance Audit`)
  - `/knowledge` & `/knowledge-base` (`Knowledge Base`)
- **Audit & Plan Doc:** [INTELLIGENCE_SURFACES_SSOT_AND_UX_AUDIT_2026-11-12.md](file:///Users/pranay/Projects/travel_agency_agent/Docs/exploration/INTELLIGENCE_SURFACES_SSOT_AND_UX_AUDIT_2026-11-12.md)

## Changes Implemented

### Backend (`spine_api`)
1. `spine_api/routers/analytics.py`:
   - Added singleflight lock + 15s TTL per-agency snapshot cache in `_all_agency_records` (automatically bypassed when readers are monkeypatched in tests) + `clear_analytics_snapshot_cache()` so the 5 concurrent `/insights` requests share one DB scan instead of 5 parallel 48k-row scans (~500 paged queries).
   - Offloaded `get_analytics_team`'s sync `_all_agency_records` call via `starlette.concurrency.run_in_threadpool` so it no longer blocks the asyncio event loop.
2. `spine_api/routers/legacy_ops.py`:
   - Updated `get_audit_events` to prefer `TripStore.list_trip_summaries(agency_id=agency.id, limit=10000)` when available instead of decrypting 10,000 full trip blobs.
3. `spine_api/routers/rag.py`:
   - Added `DELETE /api/v1/rag/documents/{document_id}` scoped to `agency.id` using `rag.store.delete_chunks_by_document`.

### BFF Allowlist (`frontend/src/lib/route-map.ts`)
- Added explicit proxy entries: `audit/logs`, `audit/chain-verify`, `audit/routing-health/batch-triage`, `audit/routing-health/export`, `audit/{id}/triage`, `audit/{id}/suppress-routing-health-paging`, and `v1/rag/documents/{id}`.

### Frontend (`frontend/src/app/(agency)/`)
1. `insights/PageClient.tsx`:
   - Replaced the all-or-nothing loading/error gate with progressive per-section loading, error isolation, and retry buttons.
   - Fixed the SSOT mismatch on `Total Inquiries` (now strictly window-scoped `summary.totalInquiries` matching `summary.conversionRate`) and added dedicated `All-Time Workspace Trips` (`unifiedState.canonical_total`) and `Open Bottlenecks` StatCards in a balanced 4-column grid.
   - Wired header `Export` button to download a JSON telemetry snapshot, fixed the hardcoded `/ 20` width denominator in `Stage Breakdown`, replaced dead `suggestedAction` `<button>` with a non-dead action badge, and added accessible `id`/`name`/`aria-label` on the time-range `<select>`.
2. `destination-intelligence/PageClient.tsx`:
   - Added 8 quick-pick destination presets (Bangkok, Tokyo, Bali, Paris, London, Cape Town, Dubai, Malé), sensible default upcoming trip dates, and `?country=` URL parameter hydration while preserving 100% of strict `FND` provenance, coverage/gaps, weather grading, and anonymized ratings.
   - Fixed all 6 Chrome DevTools form-field accessibility issues (`htmlFor`/`id`/`name`/`aria-label`).
3. `audit/PageClient.tsx`:
   - Fixed the live `Error: HTTP 404` failure by migrating `/legacy_ops/audit*` requests onto the BFF-proxied `/api/audit*` routes.
   - Added an **Execution Chain Integrity (PA-19)** verification card (`GET /api/audit/chain-verify`) and dark-theme styling while preserving 100% of routing-health alert triage, batch triage, paging suppression, and evidence export.
4. `knowledge/PageClient.tsx`:
   - Replaced the hardcoded 5-item mock showcase (including the `",000"` typo and fake `"Autonomous Customer Memory Engine — 150+ completed luxury trips"`) and dead modal with real agency-scoped RAG wiring (`GET /api/v1/rag/status`, `GET /api/v1/rag/documents`, `POST /api/v1/rag/documents/index`, `POST /api/v1/rag/query`, `DELETE /api/v1/rag/documents/{id}`).
   - Added honestly badged `Starter Templates` with 1-click `Index` buttons and accessible `htmlFor`/`id`/`name` form controls.

## Verification
- `uv run ruff check spine_api/routers/analytics.py spine_api/routers/legacy_ops.py spine_api/routers/rag.py tests/test_intelligence_overhaul_api.py` -> passed (`All checks passed!`).
- `uv run pytest tests/test_intelligence_overhaul_api.py -q` -> `3 passed`.
- `cd frontend && npx tsc --noEmit` -> `0 errors`.
- `cd frontend && npx eslint ...` -> `0 errors` (`17 warnings` on pre-existing `no-restricted-globals` `fetch` usage in `audit` & `knowledge`).
- `cd frontend && npx vitest run ...` -> `4 test files passed, 16 tests passed`.
- **Verification:** `tsc --noEmit` (0 errors), `eslint` (0 errors), `vitest` (4 files / 16 tests passed), and live Chrome DevTools inspection across all 4 routes.

### Follow-Up First-Principles Contract Alignment (`/knowledge` & `/destination-intelligence`, 2026-11-12)
1. **`/knowledge` (`frontend/src/app/(agency)/knowledge/PageClient.tsx`):**
   - Preserved both the curated operator category pills (`All Intelligence`, `Playbooks & Cheatsheets`, `Visa & Regulatory`, `Customer Memory`, `Agency Rules` mapped via `CURATED_CATEGORIES`) and the granular backend `Source type:` filter pills across all 8 `DocumentSourceType` values.
2. **`/destination-intelligence` (`frontend/src/app/(agency)/destination-intelligence/PageClient.tsx`):**
   - Fixed 5 silent frontend/backend contract mismatches uncovered during contract verification:
     - `BAND_STYLES`: keyed on `"1" | "2" | "3" | "4"` (`safety_band.py` `BAND_LABELS`) instead of `"no_advisory" | ...`.
     - `activity`: aligned strictly to `weather_suitability.py` `THRESHOLDS` (`city`, `beach`, `hiking`), fixing the `Cape Town, ZA` preset (`hiking` instead of `outdoor` which caused HTTP 422).
     - Weather display: aligned `WEATHER_VERDICT_STYLES` to `green | yellow | red | unverifiable`, rendered forecast `summary` counts + `days[]` breakdown (`date`, `verdict`, `tmax_c`, `precip_mm`, `uv_note`), and aligned `climate_baseline` `normals` (`mean_tmax_c`, `mean_precip_mm`, `rain_day_fraction`, `years_used`).
     - `DIMENSION_LABELS` & `TRV-DP-07` consent: aligned to all 6 canonical `federated_intelligence.RATING_DIMENSIONS` (`safety`, `value`, `family_fit`, `food`, `transport`, `connectivity`) and replaced implicit 1-click `consent: true` with an explicit consented submission form (`dimension`, `score`, optional `trip_month`, optional contact-scrubbed `note`, required `consent` checkbox).
     - Hydration: moved `?country=` URL parameter hydration into `useEffect` so SSR and initial client render match cleanly with 0 React hydration warnings.
   - Added `frontend/src/app/(agency)/destination-intelligence/__tests__/PageClient.test.tsx` (2 tests).
