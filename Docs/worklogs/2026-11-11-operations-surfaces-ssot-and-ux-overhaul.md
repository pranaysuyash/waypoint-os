# Operations Surfaces SSOT, Latency & UX Overhaul (`/documents`, `/payments`, `/suppliers`) — 2026-11-11

**Date:** 2026-11-11  
**Companion Audit:** [Operations Surfaces SSOT & UX Audit](file:///Users/pranay/Projects/travel_agency_agent/Docs/exploration/OPERATIONS_SURFACES_SSOT_AND_UX_AUDIT_2026-11-11.md)

---

## Executive Summary

Overhauled all three `OPERATIONS` navigation surfaces from first principles with canonical SSOT contracts, sub-second read performance, honesty preservation (`FND-0182` / `FND-0398`), and zero regression failures:

1. **`/documents` ([PageClient.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/documents/PageClient.tsx), [DocumentsZone.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/DocumentsZone.tsx))**:
   - Replaced internal implementation jargon (`"Route-level shell over canonical document contracts. No parallel document workflow."`) with clear operator guidance.
   - Extended canonical `GET /trips` (`scope="documents"`) in [persistence.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/persistence.py) and [server.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/server.py) to prioritize trips with active `booking_documents` first, followed by upload-ready stages (`proposal`, `booking`, `booked`), with `q` search across `23,702` scoped trips and explicit stage-eligibility notices when viewing `intake` trips.
   - Fixed legacy `NaNKB` display when `doc.size_bytes` is null/missing and added accessible `id`/`name`/`aria-label` on the document-type `<select>`.

2. **`/payments` ([PageClient.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/payments/PageClient.tsx), [payment_queue_service.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/services/payment_queue_service.py))**:
   - Eliminated the 14.39s–16.41s multi-batch sequential scan over `48,767` trips using a single selective SQL projection (`SQLTripStore.load_all_trip_payment_records_for_agency`, skipping decryption on empty `booking_data`) backed by a write-versioned 60s snapshot cache (`_load_agency_payment_items_cached`). Measured cold load at **0.765s**, warm service call at **0.0098s**, and live BFF `GET /api/payments?limit=25&offset=0&sort=urgent` fetch in Chrome at **28ms**.
   - Preserved backward-compatible default `sort="recent"` in `GET /payments` while adding `sort="urgent"`, `configured_only`, and `q` query params. Defaulted `/payments` UI to `Urgency priority` (`Overdue` `232` first), added interactive KPI filter cards, `Hide unconfigured` toggle, debounced search bar, INR/USD currency formatting, accessible `<select>` `id`/`name` pairs, and reference-normalized fallback labels (`Trip details incomplete · <REF>`).

3. **`/suppliers` ([PageClient.tsx](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/suppliers/PageClient.tsx), [supplier.py](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/supplier.py), [route-map.ts](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts))**:
   - Added SQLite persistence (`data/suppliers/supplier_ledger.db`, disabled during `PYTEST_CURRENT_TEST`) + `GET /api/v1/supplier/contracts` & `GET /api/v1/supplier/inventory/holds` + BFF mappings in `route-map.ts`.
   - Wired real **Upload Rate Sheet** (`POST /api/v1/supplier/contracts/upload`) and **Reserve 48h Soft-Hold** (`POST /api/v1/supplier/inventory/soft-hold`) workflows in an explicit **Operator-Recorded Contracts & 48h Soft-Holds** section, cleanly separated from **Illustrative Sample Directory (`Sample data`)** fixtures preserving `<SimulatedBadge label='Sample data' />`, `suppliers-preview-banner`, and `DP-04a` live-feed disclosure.
   - Added searchable `scope="suppliers"` trip supplier context via shared [`ScopedTripPickerBar`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/ScopedTripPickerBar.tsx).

---

## Verification Ledger

- **Backend Lint:** `uv run ruff check ...` — all checks passed (0 errors).
- **Backend Regression Suite (Post-Final Edit):** `uv run pytest tests/test_bff_parity_gate.py tests/test_supplier_real.py tests/test_supplier_contract_suite.py tests/test_payments_queue_api.py tests/test_planning_surfaces_regressions.py -q` — **25 passed, 0 failed**.
- **Frontend Static & Unit Checks (Post-Final Edit):**
  - `cd frontend && npx tsc --noEmit` — passed (0 errors).
  - `npx eslint` on all modified/created frontend files — passed (0 errors, 0 warnings).
  - `npx vitest run` (`documents`, `payments`, `suppliers`, `workflows`, `ScopedTripPickerBar`) — **5 files passed, 10 tests passed**.
- **Live Browser E2E (Chrome DevTools on `:3005` + live uvicorn `:8000`):**
  - `/documents`, `/payments`, and `/suppliers` verified visually and via console inspection: **0 console errors, 0 form issues**.
  - Before/after PNGs captured and visually verified in session artifact directory.

### Diff Audit & Feature Parity Verification (Follow-Up Check)

Audited full `git diff HEAD` across all 6 Planning + Operations pages (`/trips`, `/quotes`, `/bookings`, `/documents`, `/payments`, `/suppliers`) and shared components (`PlanningTripCard`, `DocumentsZone`, `ScopedTripPickerBar`):
- **Planning (`/trips`, `/quotes`, `/bookings`):** Zero features dropped; condensed `PlanningTripCard` inline step chain into `Stage: <X> · Step N of 5` while retaining all workspace/intake/ops actions and routes.
- **Operations restorations from diff audit:**
  1. [`suppliers/PageClient.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/suppliers/PageClient.tsx): Restored `useTrip(selectedTripId || null)` so dynamic `agentOperations.supplierRiskLevel` and `agentOperations.supplierIntelligenceSnapshot` determine `"Trip-derived supplier risk"` and `"Snapshot provenance"` honestly per trip (`Unknown (no supplier evidence)` / `no stored supplier snapshot` when absent).
  2. [`payments/PageClient.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/payments/PageClient.tsx): Restored explicit `Refresh` button calling `refetch()`.
  3. [`documents/PageClient.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/documents/PageClient.tsx): Restored `useTrip(selectedTripId || null)`, URL `?tripId=` persistence when switching trips, and the `Open Trip Workspace` (`/trips/<id>/intake`) link.
- Re-ran `tsc --noEmit`, `eslint`, and all **10/10** Planning + Operations Vitest suites (**37/37 tests passed**).

### Follow-Up First-Principles Taxonomy Unification (`/suppliers`, 2026-11-12)
- Unified `/suppliers` (`frontend/src/app/(agency)/suppliers/PageClient.tsx`, `spine_api/routers/supplier.py`, `frontend/src/lib/api-client.ts`) onto a single canonical 7-category agency supplier taxonomy (`dmc`, `hotel`, `airline`, `rail_charter`, `transfer`, `safari`, `insurance` + `all`) shared across:
  1. `ContractUploadRequest.supplier_category` (persisted in SQLite, backward-compatible default `"dmc"`),
  2. **Operator-Recorded Contracts** category filter bar and contract card badges, and
  3. **Illustrative Sample Directory** (9 fixtures restoring `Airlines`, `Transfers`, and `Insurance` alongside `DMCs & Inbound`, `Hotels & Resorts`, `Rail & Charter`, and `Safari & Camps`, all clearly marked `Sample data` / `(illustrative)`).
