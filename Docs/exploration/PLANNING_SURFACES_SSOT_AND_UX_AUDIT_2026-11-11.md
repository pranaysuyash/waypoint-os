# Exploration & Council Audit: Planning Surfaces SSOT, Discovery & UX Overhaul (`/trips`, `/quotes`, `/bookings`)

- **Date:** 2026-11-11
- **Status:** Verified (Implementation, Automated Suites & Live Browser Verification Complete)
- **Scope:** All three `PLANNING` sidebar modules (`Trips in Planning` `/trips`, `Quotes` `/quotes`, `Bookings` `/bookings`), canonical trip listing/search/filter API (`GET /trips` -> `/api/trips`), shared trip card (`PlanningTripCard`), and global breadcrumb capitalization (`Shell`).
- **Predecessor Audit:** `Docs/exploration/COMMAND_CENTER_SSOT_AND_UX_AUDIT_2026-11-11.md` (`COMMAND` section: `/overview`, `/inbox`, `/reviews`, committed at `607e5025`).

---

## 1. Ground-Truth Observations & Root-Cause Evidence

Live runtime inspection (`:8000` + `:3005`, test agency `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b`, `48,767` total trips / `44,274` workspace planning trips) and PostgreSQL queries revealed four systemic defects across the `PLANNING` section:

### 1.1 Trips in Planning (`/trips`) — Silent 100-Row Cap & Card Noise
1. **SSOT Header Contradiction:** `/overview` displays `44,274 trips in planning` (from SQL `statusCounts`), whereas `/trips` displays `⚠ 100 needs details · 100 in planning` and `Showing 26 grouped cards from 100 trips` because `WorkspacesPageWithSearchParams` (`frontend/src/app/(agency)/trips/PageClient.tsx`) renders `workspaceTrips.length` (`100`, the implicit `limit=100` cap of `GET /trips`) rather than server `total` / `statusCounts`.
2. **No Search, Filter, or Pagination:** `GET /trips` (`spine_api/server.py`) supports only `status` and `limit`, lacking `offset`, text search `q`, and domain scopes. Advisors cannot reach trips beyond row 100 out of `44,274`.
3. **Card & Breadcrumb Slop:**
   - `Shell.tsx` line 442 applies Tailwind CSS `capitalize` onto `getPageLabel(pathname)`, mutating `"Trips in Planning"` into `"Trips In Planning"`.
   - `PlanningTripCard.tsx` (`variant='workspace'`) repeats `"Stage: Intake · Details · Options · Quote Review · Output"` identically on all 26 cards and prefixes every footer with lowercase `"Next: confirm ..."`, even though `variant='overview'` already strips `"Next:"` and capitalizes sentence case.

### 1.2 Quotes (`/quotes`) — Blind `trips[0]` Selection & Leaked Schema Paths
1. **Dead-End Default Selection:** `QuotesPageClient` (`frontend/src/app/(agency)/quotes/PageClient.tsx`) calls `useTrips({ view: 'workspace', limit: 100 })` and picks `trips[0]` (`trip_4f8887968b0f`, an incomplete checker lead with no strategy), ignoring persisted trips that actually have quote/strategy data (PostgreSQL verified real modeled quotes such as `Emirates` `$3,000`, `Lufthansa` `$3,000`, `Tokyo Autumn Discovery` `$6,400`, `Original Supplier` `$3,000` plus budget-breakdown trips).
2. **Leaked Schema Paths & Engineering Prose:**
   - Subtitle reads: `"Quotes from persisted spine data. Nothing on this page is invented."`
   - When a trip lacks modeled quote inputs, raw backend paths are shown verbatim to the travel advisor: `strategy.recommended_option (run the spine to produce a recommended itinerary)` and `decision.budget_breakdown (cost bucket estimates)`. Note: `tests/test_quotes_read_model.py` asserts `"strategy.recommended_option" in data["missing"]`, so backend API field preservation with frontend display translation preserves API backwards compatibility while fixing the advisor UX.
3. **CTA Hierarchy Imbalance:** `Generate Output Artifacts` (primary blue button) and `Quote Review Queue` dominate the header even when no quote is loaded on the screen.

### 1.3 Bookings (`/bookings`) — Duplicate Picker Leaking Test IDs & Encrypted-Blob Blindness
1. **Duplicate `formatTripPickerLabel`:** Unlike `/quotes`, `/suppliers`, and `/documents` (which all share `@/lib/trip-picker-label`), `BookingsPageClient` defines a local `formatTripPickerLabel` that appends raw internal IDs (`(tc_roundtrip_...)`, `(tc_dbg_e898dac9)`, `(trip_budget_probe_1)`, `(trip_conc_24)`).
2. **Active Dossiers Buried Past `limit=100`:** PostgreSQL inspection confirmed real populated dossiers (e.g., `trip_39d4c7308976`: `John Doe` & `Jane Doe`, `INR 120,000` agreed / `INR 50,000` paid / `INR 70,000` due), pending customer submissions (`trip_913ad37c860f`), and `1,457` `booking_collection_tokens` — yet `/bookings` loads only newest-100 workspace trips and defaults to empty `trip_4f8887968b0f`.
3. **Note on Encryption & Column Types:** `booking_data` and `pending_booking_data` are Fernet-encrypted at rest (`_PRIVATE_BLOB_FIELDS` in `SQLTripStore`) and stored in `json` (not `jsonb`) columns, and empty `{travelers: []}` stubs encrypt to ~172-byte ciphertexts while populated dossiers are ~536–1607 bytes. Discovering real dossiers cleanly requires candidate filtering + batched decryption without exposing raw PII in generic `GET /trips` list payloads.

---

## 2. Supersession & Preservation Matrix

| Finding / Commit Precedent | Original Intent | Disposition in This Overhaul |
|---|---|---|
| **FND-0120** (`WORKSPACE_TRIP_STATUSES`, `active` = `in_trip`) | Ensure `active` and in-flight trips appear in workspace totals instead of vanishing | **Preserved** — `/trips` uses the exact same `WORKSPACE_TRIP_STATUSES` total (`44,274`) as `/overview` via `statusCounts` + `total` |
| **FND-0260 → FND-0303 (T4 Quotes Read Model)** | Delete fabricated tier matrix (`Essential Saver`, `Signature Curator`, `Ultra Prestige Suite`) and never invent prices | **Preserved & Strengthened** — No prices or quotes are ever fabricated; `GET /trips?scope=quotes` surfaces trips with *real* persisted strategy/budget records instead of defaulting blindly to `trips[0]`, and raw JSON paths in `missing[]` are translated into clear operator guidance on the frontend while keeping API contract intact |
| **E1 Honest Bookings Dossier** | Delete sample traveler/payment tables and render real `booking_data`, `pending_booking_data`, and `collection-link` state | **Preserved & Strengthened** — Uses real tenant-scoped endpoints only, preserves empty-state honesty when choosing an unbooked trip, and adds `scope=bookings` discovery so advisors land on genuine dossiers first |
| **Register N-4 Escalated Filter** (`trips/PageClient.tsx`) | Allow filtering escalated trips in `/trips` | **Preserved & Upgraded** — Kept URL `filter` persistence alongside server-backed status pills (`All`, `Ready to Quote`, `Ready to Book`, `In Progress`, `Blocked`, `In Trip`, `Assigned`), search `q`, and pagination |

---

## 3. Persona Council Deliberation & Architectural Decisions

- **Elena (Luxury Agency Owner):** Advisors click `Planning -> Trips in Planning` expecting the same pipeline numbers as `Overview`, quick destination/client lookup across the whole book (`44,274`), and clean quote/booking queues that open real work rather than blank error screens.
- **Marcus (Systems & Database Architect):** Extend **one canonical endpoint (`GET /trips`)** rather than adding parallel `/api/v1/quotes/trips` or `/api/v1/bookings/trips` shadows. Support `offset`, `q` (search), and `scope` (`quotes` | `bookings` | `all`), forwarding them cleanly through `/api/trips` BFF (`statusCounts` + `total` + `items`). Keep SQL portable across PostgreSQL (`CAST(... AS TEXT)` / `booking_collection_tokens` join/subquery + ciphertext-size candidate ranking + decryption check for non-empty dossiers), SQLite test DBs, and `FileTripStore`. Maintain the privacy boundary (`booking_data` / `pending_booking_data` NEVER leaked into generic `GET /trips` JSON payloads — only used server-side for `scope=bookings` membership & ordering).
- **Siddharth (SSOT Lead):** `/trips` header count binds strictly to server `total` (`44,274`), per-status filter pills bind to SQL `statusCounts`, and grouped card banners clearly state page/filter scope (`Page 1 of X` / `Showing Y grouped cards from Z trips on this page`).
- **Clara (Epistemic Honesty):** Translate raw code paths (`strategy.recommended_option`, `decision.budget_breakdown`) cleanly in the frontend UI (`QuotesPageClient`) while preserving `tests/test_quotes_read_model.py` backend assertion compatibility. Replace developer defensive prose (`"Nothing on this page is invented."`) with commercial domain clarity.
- **Mateo (Pricing & Margin Integrity):** Preserve policy provenance (`applied_rule_id`), statutory TCS disclaimers, unpriced decision branches, and `INR` (`en-IN`) locale formatting across both `/quotes` and `/bookings`.
- **UI Craft / Unslop Auditor:**
  1. Remove CSS `capitalize` bug in `Shell.tsx` breadcrumb (`Trips In Planning` -> `Trips in Planning`).
  2. Strip `Next:` lowercase prefix consistently across `PlanningTripCard` variants, and collapse the repetitive 5-stage dot chain on workspace cards to a clean single stage pill (`Intake`, `Options`, etc.) + concise completed count.
  3. On `/quotes` and `/bookings`, provide a clean scope segmented control (`With Quotes (N)` / `All Planning Trips` and `Active Booking Dossiers (N)` / `All Planning Trips`), filterable/searchable selector using canonical `@/lib/trip-picker-label` without raw ID leakage, and balanced action button hierarchy.

---

## 4. Owner Decisions Required
None — all changes stay strictly within existing authorization boundaries, preserve privacy boundaries (`booking_data` remains excluded from generic `/trips` responses), require no destructive database mutations, and keep existing public contracts intact.

---

## 5. Verification Plan
1. **Backend:** Targeted `pytest` regression suite covering `GET /trips` (`offset`, `q`, `scope=quotes`, `scope=bookings`, `statusCounts`, privacy boundary ensuring `booking_data` PII never leaks in list output) + existing `tests/test_quotes_read_model.py`, `tests/test_booking_data.py`, `tests/test_booking_collection.py`, `ruff check`, `mypy`.
2. **Frontend:** Targeted `vitest` suites (`/trips`, `/quotes`, `/bookings`, `/api/trips`, `PlanningTripCard`, `Shell` breadcrumb) + `tsc --noEmit` + `eslint`.
3. **Browser E2E & Visual Proof:** Restart uvicorn `:8000`, verify `/trips`, `/quotes`, and `/bookings` in Chrome DevTools against live PostgreSQL (`44,274` SSOT match, search & pagination, `/quotes` defaulting to real persisted quote without schema leaks, `/bookings` defaulting to real populated dossier without raw `tc_*` IDs, `0` console errors), and capture pre/post visual proof artifact.
