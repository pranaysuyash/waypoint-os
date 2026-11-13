# Intelligence Surfaces SSOT, Performance & UX Audit

- **Date:** 2026-11-12
- **Scope:** Sidebar **INTELLIGENCE** section:
  1. `Insights` (`/insights` — `frontend/src/app/(agency)/insights/PageClient.tsx`, `spine_api/routers/analytics.py`, `product_b_analytics.py`)
  2. `Destination Intel` (`/destination-intelligence` — `frontend/src/app/(agency)/destination-intelligence/PageClient.tsx`, `spine_api/routers/destination_intelligence.py`)
  3. `Audit` (`/audit` — `frontend/src/app/(agency)/audit/PageClient.tsx`, `spine_api/routers/audit.py`, `spine_api/routers/legacy_ops.py`)
  4. `Knowledge Base` (`/knowledge` & `/knowledge-base` redirect — `frontend/src/app/(agency)/knowledge/PageClient.tsx`, `frontend/src/app/(agency)/knowledge-base/page.tsx`, `spine_api/routers/rag.py`, `src/rag/store.py`)
- **Doctrine Alignment:** `OPERATING_DOCTRINE.md` v8.2, `FND-0182` / `FND-0398` (zero fake AI / fabricated data), `FND-0345` (no silent truncation), `FND-0402` (evidence-backed revenue honesty), `PA-19` (execution hash-chain verification), BFF `route-map.ts` parity.

---

## 1. Live Runtime & Code Audit Findings

### A. `/insights` (`Insights & Analytics`)
1. **P0 — 15s+ Stall & Request Aborts (`ERR_ABORTED`) on 48k-Trip Agencies:**
   - **Evidence:** Live Chrome DevTools network trace showed all 11 requests pending >12s, with `/api/insights/bottlenecks` and `/api/insights/revenue` aborting (`net::ERR_ABORTED`) and retrying, leaving the dashboard stuck on `"Calculating latest dashboard telemetry…"`.
   - **Root Cause:** `spine_api/routers/analytics.py` executes `_all_agency_records(TripStore.list_trips, agency.id)` independently across 5 concurrent endpoints (`/analytics/summary`, `/pipeline`, `/team`, `/bottlenecks`, `/revenue` — which scans BOTH `list_trips` AND `list_trip_payment_records_for_agency`). On a 48,767-trip workspace (`d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`), this triggers ~500 sequential paged queries and ~243,835 trip deserializations, plus `async def get_analytics_team` runs sync `_all_agency_records` directly on the asyncio event loop.
   - **Fix:** Add an in-flight singleflight lock + short-TTL (15s) per-agency snapshot cache in `analytics.py` for `_all_agency_records` (automatically bypassed when `TripStore.list_trips` / readers are monkeypatched in tests, and invalidated cleanly via helper if needed), and offload sync DB paging in `async def get_analytics_team` via `starlette.concurrency.run_in_threadpool`.
2. **P1 — All-or-Nothing Loading/Error Gate (`PageClient.tsx:426-427`):**
   - `isLoading = isSummaryLoading || isPipelineLoading || isTeamLoading || isBottlenecksLoading || isRevenueLoading;` blocks the entire dashboard behind one spinner if any single card's query is slow or fails.
   - **Fix:** Render sections progressively (Summary & Commercial Evidence, Pipeline & Funnel, Revenue, Team Performance, Bottlenecks) with per-section loading/error cards and retry buttons so one slow/failing endpoint never blanks out healthy metrics.
3. **P1 — SSOT Scope Mismatch on `Total Inquiries` StatCard (`PageClient.tsx:521-522`):**
   - Mixes `unifiedState?.canonical_total` (all-time agency trip count) as the headline value with `summary.conversionRate` (scoped to `timeRange` e.g. `30d`) as its subtext.
   - **Fix:** Use `summary.totalInquiries` (window-scoped to the selected `timeRange`) on the `Total Inquiries` card so numerator, denominator, and `conversionRate` share the same time window, and show `unifiedState?.canonical_total` in its own clearly labeled `"All-Time Workspace Trips"` StatCard (plus `"Active Team Members"` / `"Open Bottlenecks"` so the 4/5-column grid is balanced instead of leaving 3 empty columns).
4. **P1 — Dead `Export` & `suggestedAction` Buttons (`PageClient.tsx:479, 296`):**
   - Header `Export` button has no `onClick` handler (even though `governanceApi.exportInsights` exists, and client-side JSON/CSV snapshot download works immediately from loaded metrics). Bottleneck `suggestedAction` is rendered as a dead `<button>`.
   - **Fix:** Wire `Export` to download a structured JSON report of the live telemetry (and call `governanceApi.exportInsights` / fallback cleanly), and render `suggestedAction` as an actionable recommendation chip or scroll/navigate trigger rather than a dead button.
5. **P2 — Hardcoded `/ 20` Width Denominator (`PageClient.tsx:609`) & Form A11y (`PageClient.tsx:462`):**
   - Stage breakdown bar uses `(stage.tripCount / 20) * 100` (overflowing past 100% whenever `tripCount > 20`). Fix to `Math.min(100, (stage.tripCount / maxStageTripCount) * 100)`.
   - `<select>` time-range picker lacks `id`, `name`, and `aria-label` (triggers Chrome DevTools form-field issue).

### B. `/destination-intelligence` (`Destination Intelligence`)
1. **Honesty Baseline (Preserve):** Already strictly `FND`-compliant — every safety verdict, weather grade, and anonymous rating displays source provenance, coverage gaps, and `"No data"` / `"Gap"` rather than fabricating values.
2. **P1 — Form Accessibility Issues (6 violations in Chrome DevTools):**
   - All 6 `<input>`/`<select>` elements (`country`, `lat`, `lng`, `start`, `end`, `activity`) lack `id`/`name`/`aria-label` (and visible or `sr-only` `<label htmlFor>`).
3. **P2 — Operator Ergonomics (Raw Coordinates & Country Slugs):**
   - Operators must manually type decimal `lat`/`lng` (defaulting to Bangkok `13.7563, 100.5018`) and lowercase country slugs (`japan`, `russia`) with no quick-pick destination presets or URL query hydration (`?country=...`).
   - **Fix:** Add quick-pick destination presets (e.g., Tokyo, Bangkok, Bali, Paris, London, Cape Town, Dubai, Maldives) that populate BOTH the country slug and coordinates in one click while keeping full custom country/lat/lng input support, plus default sensible upcoming trip dates if empty, and optional `?country=` URL param initialization.

### C. `/audit` (`Trip Fit & Compliance Audit`)
1. **P0 — Page Completely Broken (`Error: HTTP 404`, 8 Failed Requests):**
   - **Evidence:** Live browser rendered `"Error: HTTP 404"` and Chrome DevTools logged 8× `404` on `GET /legacy_ops/audit?...`.
   - **Root Cause:** `PageClient.tsx` calls `/legacy_ops/audit`, `/legacy_ops/audit/{id}/triage`, `/legacy_ops/audit/routing-health/batch-triage`, `/legacy_ops/audit/{id}/suppress-routing-health-paging`, and `/legacy_ops/audit/routing-health/export`. Next.js (`next.config.mjs`) has no `/legacy_ops/*` rewrite and BFF only proxies `/api/*` via `frontend/src/lib/route-map.ts`. Meanwhile backend `legacy_ops.py` mounts those exact endpoints at `/audit`, `/audit/{event_id}/triage`, `/audit/routing-health/batch-triage`, `/audit/{event_id}/suppress-routing-health-paging`, `/audit/routing-health/export`.
   - **Fix:** Add explicit BFF entries in `frontend/src/lib/route-map.ts` under `audit/...` (`audit/{event_id}/triage`, `audit/routing-health/batch-triage`, `audit/{event_id}/suppress-routing-health-paging`, `audit/routing-health/export`, plus `audit/logs` -> `api/audit` and `audit/chain-verify` -> `api/audit/chain-verify`). Update `audit/PageClient.tsx` and `audit/__tests__/PageClient.test.tsx` to use `/api/audit/...`.
2. **P1 — Missing PA-19 Hash-Chain Verification & SQL Audit Log Surface:**
   - `spine_api/routers/audit.py` exposes `GET /api/audit` (SQL `AuditLog` entries) and `GET /api/audit/chain-verify` (`PA-19` cryptographic execution-event hash chain verifier), neither of which is surfaced on `/audit`.
   - **Fix:** Add a live **Execution Chain Integrity (PA-19)** verification card/action (`GET /api/audit/chain-verify`) and a clean filterable **Workspace Audit Logs** section (`GET /api/audit/logs`) alongside the preserved **Routing Health Alert Triage**, **Paging Suppression**, and **Evidence Export** workflows.
3. **P2 — Form A11y & `legacy_ops.py` Performance:**
   - Ensure all filter/triage inputs have `id`/`name`/`aria-label`. In `legacy_ops.py:get_audit_events`, replace `TripStore.list_trips(limit=10000)` with `TripStore.list_trip_summaries(agency_id=agency.id, limit=10000)` (or fallback to `list_trips`) to avoid full trip blob decryption on every audit poll.

### D. `/knowledge` & `/knowledge-base` (`Knowledge Base & Agency Memory`)
1. **P0 — Static Hardcoded Showcase Masquerading as Live AI Memory (`FND-0182` / `FND-0398` Violation):**
   - **Evidence:** `knowledge/PageClient.tsx` makes **zero** API calls, hardcodes 5 static strings (`kb_01..kb_05`), contains a template-stripped typo (`"Quotes exceeding ,000"`), claims `"Learned Customer Memory... 150+ completed luxury trips"` from `"Autonomous Customer Memory Engine"` and `"Synced with RAG Vector Store"`, and its `"+ Create New Playbook"` modal `"Save & Index into Agency Brain"` button does nothing except close the modal.
   - **Root Cause:** Real backend RAG (`spine_api/routers/rag.py`: `GET /api/v1/rag/status`, `GET /api/v1/rag/documents`, `POST /api/v1/rag/documents/index`, `POST /api/v1/rag/query`) and BFF `route-map.ts` entries (`v1/rag/*`) already exist, and `src/rag/store.py` already has `delete_chunks_by_document`, but `/knowledge` was never wired to them.
   - **Fix:**
     - Wire `/knowledge` directly to the real agency-scoped RAG backend:
       - `GET /api/v1/rag/status` -> live RAG status banner (indexed chunk count, embedding provider/model, lexical/semantic availability, honest degraded/offline state).
       - `GET /api/v1/rag/documents` -> live list of indexed agency documents/playbooks (`title`, `source_type`, `license_class`, `chunk_count`, `embedding_model`), with honest empty state when zero documents are indexed.
       - `POST /api/v1/rag/documents/index` -> working **Index Playbook / Document** modal that actually persists and indexes into `SQLiteRAGStore`, refreshes the document list, and displays chunk count / status.
       - `POST /api/v1/rag/query` -> real hybrid search & grounded answer panel with citations (explicitly grounded in indexed chunks, never fabricated).
       - Add `DELETE /api/v1/rag/documents/{document_id}` in `spine_api/routers/rag.py` + `route-map.ts` so operators can also remove obsolete/test playbooks cleanly.
       - Add a clear, non-deceptive **Reference Starter Templates** drawer/toggle (explicitly marked `SimulatedBadge` / `Starter Template — Not Yet Indexed` with 1-click **"Index into Agency Knowledge Base"** button!) so operators can either start clean or load curated starter playbooks (fixing the `",000"` typo to `"$25,000"` and removing fake `"150+ completed luxury trips"` claims!) into the real RAG store.
     - Fix search input & modal `<input>`/`<select>`/`<textarea>` `id`/`name`/`htmlFor` accessibility.
     - Keep `/knowledge-base` -> `/knowledge` redirect intact.

---

## 2. Multi-Persona First-Principles Review

| Persona | Verdict & Key Guardrails Applied |
| :--- | :--- |
| **Travel OS Architect** | Consolidate `/audit` onto `/api/audit/*` via `route-map.ts` instead of exposing raw `/legacy_ops/*` paths; keep `analytics.py` endpoint shapes intact while adding singleflight + short-TTL snapshot caching. |
| **Security & Privacy Engineer** | Preserve `agency.id` scoping on all RAG, Audit, and Analytics reads/writes; never bypass `route-map.ts` allowlist; keep `PA-19` hash-chain verification accessible via `audit:read`. |
| **Performance Engineer** | Eliminate the 5×48,767-trip concurrent scan storm in `analytics.py` using singleflight lock + 15s TTL cache + `run_in_threadpool`; use `list_trip_summaries` in `legacy_ops.py:get_audit_events`. |
| **Operator UX Lead** | Replace raw lat/lng guesswork with 1-click destination presets on `/destination-intelligence`; prevent full-page spinner deadlock on `/insights`; make Knowledge Base Create/Search/Delete actually work. |
| **Honesty / Eval Reviewer** | Remove fake `"Autonomous Customer Memory Engine (150+ trips)"` and `"Synced with RAG Vector Store"` lies; ground `/knowledge` in real `SQLiteRAGStore` responses and label starter templates honestly until indexed. |

**Owner Decisions Required:** None — all fixes implement existing documented doctrine (`FND-0182`, `FND-0345`, `FND-0398`, `FND-0402`, `PA-19`) without destructive schema drops or breaking API contracts.

---

## 3. Dependency-Aware Implementation Plan

1. **Backend (`spine_api`):**
   - `spine_api/routers/analytics.py`: Add singleflight + 15s TTL cache for `_all_agency_records` (bypassed when reader is monkeypatched in tests) and `run_in_threadpool` in `get_analytics_team`.
   - `spine_api/routers/legacy_ops.py`: Prefer `TripStore.list_trip_summaries` in `get_audit_events` for fast agency trip ID lookup.
   - `spine_api/routers/rag.py`: Add `DELETE /api/v1/rag/documents/{document_id}` scoped to `agency.id`.
2. **BFF Route Map (`frontend/src/lib/route-map.ts`):**
   - Add `audit/{event_id}/triage`, `audit/routing-health/batch-triage`, `audit/{event_id}/suppress-routing-health-paging`, `audit/routing-health/export`, `audit/logs`, `audit/chain-verify`, and `v1/rag/documents/{document_id}`.
3. **Frontend Overhaul (4 Pages):**
   - `/insights`: Progressive section loading/error isolation, SSOT-aligned `Total Inquiries` vs `All-Time Workspace Trips`, working `Export` JSON download, clamped `Stage Breakdown` bar, accessible `<select>` attributes.
   - `/destination-intelligence`: Quick-pick destination presets, sensible default trip dates, `?country=` hydration, `htmlFor`/`id`/`name` on all 6 form controls.
   - `/audit`: Switch all `/legacy_ops/audit/*` calls to `/api/audit/*`, add `PA-19` Execution Chain Integrity verifier card + SQL Audit Logs section while preserving 100% of routing-health triage, batch triage, paging suppression, and export.
   - `/knowledge`: Wire to `/api/v1/rag/status`, `/api/v1/rag/documents`, `/api/v1/rag/documents/index`, `/api/v1/rag/query`, and `DELETE /api/v1/rag/documents/{document_id}`; honest empty state + 1-click starter playbook templates; fix `",000"` typo and all form `id`/`name`/`htmlFor` attributes.
4. **Tests & Live Verification:**
   - Update & expand `insights/__tests__/PageClient.test.tsx`, `audit/__tests__/PageClient.test.tsx`, `knowledge/__tests__/page.test.tsx`, plus backend pytest for `analytics` caching and `rag` delete.
   - Run `uv run ruff check`, `uv run pytest` on touched routers, `npx tsc --noEmit`, `npx eslint`, `npx vitest run`.
   - Restart backend `:8000`, verify all 4 routes live in Chrome DevTools (0 console errors, 0 form issues, 0 404s, fast load), capture & inspect all 4 AFTER PNGs, write worklog + `INTELLIGENCE_PRE_POST_VISUAL_PROOF.md`, update `Docs/INDEX.md`.
