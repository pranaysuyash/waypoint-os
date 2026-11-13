# Exploration & Audit: OPERATIONS Sidebar Surfaces (`/documents`, `/payments`, `/suppliers`)

**Date:** 2026-11-11  
**Scope:** End-to-end SSOT, latency, honesty, and operator-UX audit of the three `OPERATIONS` routes:
- `Documents` (`frontend/src/app/(agency)/documents/PageClient.tsx` -> `/trips/{id}/documents`)
- `Payments` (`frontend/src/app/(agency)/payments/PageClient.tsx` -> `GET /payments` / `spine_api/services/payment_queue_service.py`)
- `Suppliers` (`frontend/src/app/(agency)/suppliers/PageClient.tsx` -> `spine_api/routers/supplier.py`)

---

## 1. Empirical Ground Truth (Live Chrome DevTools + PostgreSQL + Backend Profiling)

Measured against agency `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b` on `2026-11-11`:

### 1.1 Documents (`/documents`)
- **Live PostgreSQL truth:** `booking_documents` holds **17,823 total rows** (**16,858 active**, non-deleted) across **17,798 distinct trips** in this agency (e.g., `trip_fe7032b8205d`, `trip_bbb6b10d7d00`, `trip_5edb388bc631`, `trip_45f8693cafee` with 2 active documents).
- **Pre-change browser behavior (`documents_before.png`):**
  1. `DocumentsPage` calls `useTrips({ view: 'workspace', limit: 100 })` with no `scope` and no `q` search query, then defaults blindly to `trips[0]` (`trip_4f8887968b0f`, in `discovery` stage with `0` uploaded documents).
  2. `OpsPanel` (`frontend/src/app/(agency)/workbench/OpsPanel.tsx`) sets `canUpload = stage === 'proposal' || stage === 'booking'`. Because the default trip is in `discovery` stage, `DocumentsZone` hides its Upload controls and shows only `"No documents uploaded yet."` with no explanation of why upload is disabled and no way to filter to trips that have documents or are ready for upload.
  3. Subtitle exposes internal engineering jargon: `"Route-level shell over canonical document contracts. No parallel document workflow."`.
  4. Selecting any of the 16,858+ active document trips requires blind scrolling in an unsearchable `<select>` capped at the newest 100 workspace trips.

### 1.2 Payments (`/payments`)
- **Live PostgreSQL & service profiling:**
  - Agency has **48,767** total trips (`31,720` with null/empty `booking_data`, `17,047` with non-null encrypted `booking_data` payloads).
  - Queue summary across full tenant scope:
    - `total`: `48,767`
    - `overdue_count`: **232**
    - `due_soon_count`: **0**
    - `due_later`: **1,398**
    - `not_configured_count`: **47,137**
    - `paid_complete_count`: **0**
    - `refund_in_progress_count`: **0**
  - **Latency measurement:** `build_payment_queue_response_for_agency(...)` took **14.39s–16.409s** (`TripStore.list_trip_payment_records_for_agency` loop across 49 batches of 1,000 rows, decrypting all 17,047 `booking_data` blobs sequentially via `_run_async_blocking`). By contrast, a single SQL query over non-null `booking_data` rows returned in **0.427s**.
- **Pre-change browser behavior (`payments_before.png`):**
  1. `GET /api/payments?limit=25&offset=0` showed `"Loading…"` during initial render because of the 14–16s backend scan.
  2. When settled, Page 1 (`Showing 25 of 48767`) displayed **25 consecutive `"Not Configured | Unknown | — | — | Not Applicable"` rows** (`Trip details incomplete · 0CB4`, etc.), burying all **232 Overdue** and **1,398 Due Later** configured payment records beyond unconfigured discovery trips.
  3. Configured overdue trips (`trip_b8324fda4304`, `INR 120,000` agreed / `INR 50,000` paid / `INR 70,000` due) showed `'destination': None` and `'trip_name': 'Trip details incomplete · 4304'` because `list_trip_payment_records_for_agency` did not project `Trip.destination` / `Trip.extracted` / `Trip.strategy` and frontend `renderTripLabel` fell back directly to raw `item.trip_id` when `trip_name`/`destination` were empty.
  4. KPI cards were static displays rather than quick filter triggers, and there was no search box (`q`) for trip name, destination, or reference, nor a toggle between **Actionable / Configured** vs **All trips (including not configured)**.

### 1.3 Suppliers (`/suppliers`)
- **Architectural & honesty context (preserving `FND-0182`, `FND-0340`, `FND-0398`):**
  - `FND-0398` (closed `2026-11-06`) added explicit `SimulatedBadge label='Sample data'`, amber `Local preview only` banner, and `"(illustrative)"` record labels on `/suppliers` because no live producer feed (`DP-04a`, owner-gated) or persisted agency supplier read-model was wired yet.
  - Meanwhile, `spine_api/routers/supplier.py` already implements `POST /api/v1/supplier/contracts/upload` and `POST /api/v1/supplier/inventory/soft-hold` with agency scoping and `TierMetadata(tier="manual"/"simulated")`, but:
    1. Only held contracts/holds in process memory (`CONTRACTS_STORE`, `HOLDS_STORE`), losing data on restart.
    2. Exposed **no `GET /contracts` or `GET /inventory/holds` listing endpoints**.
    3. Had **zero entries in `frontend/src/lib/route-map.ts`** (`FND-0340` BFF deny-by-default blocked browser calls).
  - **Pre-change browser behavior (`suppliers_before.png`):**
    1. `SuppliersPage` called `useTrips({ view: 'workspace', limit: 100 })` and defaulted blindly to `trips[0]` (`Trip details incomplete · Updated 1w · 4F88`) with no search or scope filtering.
    2. Clicking `Preview Rate-Sheet Intake` opened a non-submitting dead modal (`Close Preview` without invoking `/api/v1/supplier/contracts/upload` or allowing real operator-recorded contract & 48h soft-hold tracking).
    3. Illustrative sample directory fixtures mixed at top level without an honest persisted "Operator-Recorded Contracts & Soft-Holds" workspace alongside clearly separated "Illustrative Directory Fixtures".

---

## 2. Multi-Persona Council Review & Decisions

| Persona | Core Concern | Adopted Design Decision |
|---|---|---|
| **Agency Operations Director (Elena)** | Operators landing on `/documents` see an empty discovery trip with no upload button despite 16,858 uploaded documents in the agency; `/suppliers` can't actually store a negotiated DMC rate sheet. | Add canonical `scope="documents"` (trips with active `booking_documents` ranked first, then `proposal`/`booking` stage) + `scope="suppliers"` (trips with `supplier_intelligence_snapshot` / post-intake stage) to `GET /trips`; add persistent SQLite-backed `GET/POST` contracts & soft-holds on `/api/v1/supplier/*` mapped in `route-map.ts`. |
| **Travel Finance Controller (Marcus)** | `/payments` takes 14–16s per request and fills Page 1 with unconfigured `Not Configured` discovery rows instead of the 232 overdue payments. | Optimize `payment_queue_service.py` + `TripStore`: pre-count/skip null `booking_data` rows when `payment_status`/`due_bucket`/`queue_status` or default actionable sorting allows, sort actionable & overdue configured payments ahead of `not_configured` (while preserving 100% existing filter/summary semantics & `tests/test_payments_queue_api.py` monkeypatch contract!), project `Trip.destination` / `Trip.extracted` / `Trip.strategy` into `_build_item`, add short TTL cache invalidated on booking updates, and support `q` search + actionable view toggle (`Configured & urgent` vs `All trips`). |
| **Operator UX & Design Architect (Maya)** | Internal developer copy (`"Route-level shell over canonical document contracts..."`), raw ID fallbacks, unsearchable `<select>` dropdowns, non-interactive KPI cards. | Replace jargon subtitle with plain operator copy; add live debounced trip search + scope selector on `/documents` & `/suppliers` using shared `formatTripPickerLabel`; explain clearly when upload requires `proposal`/`booking` stage with link to trip workbench; make `/payments` KPI cards clickable filter pills + clean tabular currency/status badges + ref-normalized fallback labels (`Trip details incomplete · <REF>`). |
| **Red-Team Honesty Reviewer (Devon)** | Guard against `FND-0182`, `FND-0340`, `FND-0398`, `FND-0333`: never claim live supplier feeds (DP-04a), live SLA monitoring, or carrier verification when persisting operator-entered contracts. | Preserve `SimulatedBadge`, explicit `DP-04a` / `"Operator-recorded (not live provider feed)"` boundary banner, and `"(illustrative)"` fixture labeling in a dedicated "Illustrative Reference Fixtures" tab/section; map all new `GET`/`POST` supplier endpoints in `frontend/src/lib/route-map.ts` so `test_bff_parity_gate.py` passes cleanly; preserve existing unit/API contracts. |

---

## 3. Canonical Architecture Plan (Zero Duplication)

1. **Extend canonical `GET /trips` scopes (`spine_api/persistence.py`, `spine_api/server.py`, `frontend/src/hooks/useTrips.ts`):**
   - `scope: Optional[Literal["all", "quotes", "bookings", "documents", "suppliers"]]`
   - `documents` scope ranks trips with active rows in `booking_documents` highest (`tier=2`), then `stage in ('proposal', 'booking', 'booked')` (`tier=1`), preserving fast SQL/Postgres predicate (`exists(BookingDocument)` + stage check) + SQLite/File fallback.
   - `suppliers` scope ranks trips with stored supplier intelligence / risk signals (`supplier_intelligence_snapshot` / `supplier_risk_level`) highest (`tier=2`), then `stage in ('shortlist', 'proposal', 'booking', 'booked')` (`tier=1`).
2. **Optimize & enrich `GET /payments` (`spine_api/persistence.py`, `spine_api/services/payment_queue_service.py`, `spine_api/server.py`):**
   - Add optional `q: Optional[str]` search and `configured_only: bool = False` (or prioritize actionable configured items `overdue -> due_soon -> refund_in_progress -> due_later -> unknown -> paid_complete -> not_configured` cleanly via urgent priority order). Wait: verify `test_full_tenant_scope_not_limited_to_initial_5000` & `test_pagination_after_filtering_and_filtered_summary` pass unchanged — note both preserve exact `TripStore.list_trip_payment_records_for_agency` signature & call contract when monkeypatched!
   - When running unpatched against real `SQLTripStore`, split `count` of null/empty `booking_data` trips vs fetching & decrypting ONLY non-empty `booking_data` rows (using cached agency queue snapshot with short TTL / invalidation hook or single-pass async fetch without 49 `_run_async_blocking` hops) — reducing 16.4s to ~<1s while producing identical summary & pagination totals!
   - Also fetch `Trip.destination`, `Trip.extracted`, `Trip.strategy` cleanly (truncated/summary projection without extra decryption bloat!) so trip names & destinations populate accurately.
3. **Wire Real Persistent Supplier Workspace + Honest Sample Separation (`spine_api/routers/supplier.py`, `frontend/src/lib/route-map.ts`, `frontend/src/lib/api-client.ts`, `frontend/src/app/(agency)/suppliers/PageClient.tsx`):**
   - Persist `supplier_contracts` and `supplier_holds` in agency-scoped SQLite (`src/intake/data/suppliers/supplier_ledger.db`) alongside keeping `CONTRACTS_STORE` & `HOLDS_STORE` test hooks compatible (`setup_method` `.clear()` works identically!).
   - Add `GET /api/v1/supplier/contracts` & `GET /api/v1/supplier/inventory/holds` (agency-scoped) and map `v1/supplier/contracts`, `v1/supplier/contracts/upload`, `v1/supplier/inventory/holds`, `v1/supplier/inventory/soft-hold` in `frontend/src/lib/route-map.ts`.
   - Upgrade `/suppliers` UI cleanly: two clear tabs (**Recorded Contracts & Soft-Holds** backed by real API vs **Illustrative Fixtures (`Sample data`)** preserving all FND-0182/FND-0398 honesty markers), working rate-sheet upload & 48h soft-hold reservation dialogs, and scoped/searchable Trip Supplier Intelligence bar.
