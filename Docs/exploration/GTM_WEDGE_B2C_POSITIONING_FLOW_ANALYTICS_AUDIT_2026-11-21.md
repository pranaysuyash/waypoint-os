# GTM Wedge (`/itinerary-checker` & `/check/[agencySlug]`) — Comprehensive Council Audit, Supersession Review & Implementation Plan

**Date:** 2026-11-21
**Scope:** Full-stack audit of the public GTM wedge (`frontend/src/app/(traveler)/itinerary-checker/`, `frontend/src/app/(traveler)/check/[agencySlug]/`, `frontend/src/components/traveler/WedgeVisualShowcase.tsx`, `frontend/src/lib/proxy-core.ts`, `spine_api/routers/public_checker.py`, `spine_api/services/public_checker_service.py`, `spine_api/services/public_checker_access.py`, `spine_api/services/agency_marketplace.py`, `spine_api/services/work_intake.py`, `spine_api/product_b_events.py`, `src/intake/extractors.py`, `src/intake/orchestration.py`, `data/agency_marketplace/profiles.json`).
**Baseline Commit:** `46917980` (`refactor(itinerary-checker): unslop GTM wedge, eliminate CLS, tighten live results`).
**Method:** Operating Doctrine v8.2 (§0–§6.1), 3-Seat Persona Council (B2C Growth Strategist, Systems & Security Architect, Extraction/Telemetry/UX Engineer), live web competitor research (closing Open Work Roadmap B9), and direct code verification.

---

## 1. Executive Verdict

Visually and layout-wise, `/itinerary-checker` is clean and CLS-free (`46917980`). Structurally, however, **a 3-seat Persona Council uncovered three P0 live defects and five P1 architectural/telemetry/extraction gaps**:

1. **P0 — BFF Proxy Strips Capability Tokens (`frontend/src/lib/proxy-core.ts:88-108`):** `forwardAuthHeaders` intentionally drops `Authorization`. Because Next.js has no custom `/api/public-checker/trip/*` route handler, every browser `GET`, `/export`, and `DELETE` on `/api/public-checker/trip/{trip_id}` returns **403 Forbidden** in live Next.js sessions.
2. **P0 — B2C Exit Sends Travelers to B2B Agency Signup (`PageClient.tsx:2707-2711`):** `Find an advisor →` links to `/signup` (`frontend/src/app/(auth)/signup/page.tsx`), which is the B2B travel agency workspace signup (`agencyName`, redirects to `/workbench`).
3. **P0 — Synthetic Fabrication in Live `WedgeVisualShowcase` (`WedgeVisualShowcase.tsx:1525-1605`):** `resolveDynamicWedgeScenario` silently falls back to `amalfi_rome`, fabricates `7h 40m` / `4h 15m` / `50m tight transit hub` legs, hardcodes `$640` Virtuoso perks (`$260` breakfast, `$100` credit, etc.) for any `entityChecks`, and still embeds emojis (`🥐`, `💳`, `⬆️`, `⏰`).
4. **P1 — Agency Lead Black-Hole & False Copy (`PageClient.tsx:2580`, `route_leads.jsonl`, `work_intake.py`, `WorkQueuePanel.tsx`):** `RouteRequestPanel` claims `"The matched agency will reach out in-product"`, but travelers have no account/inbox, `route_leads.jsonl` has zero agency UI/API endpoints, `WorkQueuePanel` only sees a hashed `identity_key`, and clicking `"Open trip"` 404s cross-tenant against `PUBLIC_CHECKER_AGENCY_ID`.
5. **P1 — Empty Marketplace Supply (`data/agency_marketplace/profiles.json`):** Contains 1 placeholder (`Waypoint Trips Desk` with empty `places_covered`, `customer_types`, `services`), forcing 100% of `/itinerary-checker` users into the waitlist.
6. **P1 — Live Extraction Noise & Generic `incomplete_intake` (`src/intake/extractors.py`, `orchestration.py`, `PageClient.tsx`):** Natural-language Dubai test (`"Atlantis The Royal... Al Maha... Gold Souk... Flying via Istanbul"`) extracts `['Dubai', 'Atlantis', 'Al', 'Gold', 'Istanbul']` due to hospitality span slicing + missing transit guard + frontend `KNOWN_DESTINATION_PATTERNS` pollution. `formatTravelerBlockerItem` overwrites full-sentence `live_checks` blockers with generic `"needs a human eye"` copy.
7. **P1 — Telemetry Blind Spots (`product_b_events.py`, `public_checker_service.py`, `PageClient.tsx`):** `product_a_interest_signal` has 0 callers; `finding_evidence_opened` misfires on JSON export; `intake_started` logs all `false` when `retentionConsent === false`; pre-result and conversion funnel steps are uninstrumented.
8. **P1 — Cross-Tenant IDOR on Legacy Routes (`public_checker.py:409-449`):** Superseded `/api/public-checker/{trip_id}` routes allow any authenticated agency JWT to read/export/delete anonymous public-checker trips.

---

## 2. External Competitor Research (Roadmap B9 Refresh, 2026-11-21)

Live web search (`2026-11-21`) across `"AI itinerary checker"`, `"travel plan risk checker"`, `"Spotinga"`, and `"Fortrip"`:
- **Spotinga (`spotinga.com`):** Free, no-login Itinerary Checker for ChatGPT/Claude/Gemini plans; scores realism & routing efficiency using map travel times, flags overpacked days and backtracking.
- **Fortrip (`fortrip.ai`):** Itinerary Validator + multi-city transport/stay optimizers; stress-tests pacing, sequencing, and venue closures.
- **Mindtrip / Stippl / Wanderlog / Layla:** Planners with live mapping/hours or hybrid AI+human concierge.

**First-Principles Positioning Verdict:** Competing on *"clearer trip map"* (`PageClient.tsx:1069`) puts Waypoint head-to-head with Spotinga/Wanderlog on map routing. Waypoint's structural moat is **pre-booking reality & protection**: (1) Ghost-hotel/entity verification, (2) airport connection & seasonal/visa risk checks, (3) Virtuoso/partner hotel perks economics, and (4) optional warm handoff to a vetted human travel advisor.

---

## 3. Operating Doctrine §6.1 Supersession & Original-Intent Verdicts

| Artifact / Seam | Original Intent (Observed) | Live Usage & Defects | §6.1 Verdict |
| --- | --- | --- | --- |
| `GET/DELETE /api/public-checker/{trip_id}` (`public_checker.py:409-449`) | Pre-EX-04 endpoints kept as `"fallback for authed contexts"` (`WOBS` Part 3.6) | 0 workbench callers; 401 on anonymous fallback; cross-tenant IDOR (any agency JWT can read/delete public-checker trips). | **GENUINELY SUPERSEDED -> DELETE** (Owner decision + test migration) |
| `POST /api/public-checker/re-verify` (`public_checker.py:267-327`) | WOBS P3 v0 on-demand read-only climate/entity recheck (`WOBS` Part 3.5) | Wired in `middleware.py:39` + `route-map.ts:106`, 0 FE callers; passes `""` to `run_entity_checks` (no-op) & `_extract_month_year` (defaults to today); lacks capability-token check. | **LAST-MILE MISSING -> COMPLETE** (Fix date/entity continuity, gate or wire UI `"Re-check live signals"`) |
| `product_a_interest_signal` (`product_b_events.py:59, 129-133`) | KPI #7 in `PRODUCTB_EVENT_SCHEMA_V1` (pull-through into Product A) | 0 callers in FE or BE. | **LAST-MILE MISSING -> COMPLETE** (Server-seal on `/route-request` + client beacon on B2B CTA) |

---

## 4. Complete Findings & Resulting Tasks Register (Explicit, Implicit & Inferred)

### Implementation Tasks (Unambiguous — Execute Now)
- **T1 (P0 Security/BFF):** Add `frontend/src/app/api/public-checker/trip/[...slug]/route.ts` to forward `Authorization` + `Content-Type` to FastAPI for `/api/public-checker/trip/*` capability-token read/export/delete without weakening `proxy-core.ts` cookie-only rules.
- **T2 (P0 UX/Copy):** Remove `<Link href='/signup'>Find an advisor →</Link>` from `ResultsConversionSection` (`PageClient.tsx:2707-2711`); replace `"will reach out in-product"` (`PageClient.tsx:2580`) with contact-accurate copy.
- **T3 (P0 Honesty/UI):** Stop `WedgeVisualShowcase.tsx:1525-1605` from fabricating `7h 40m` / `50m` legs and `$640` Virtuoso perk dollar breakdowns on live runs; remove emojis (`🥐`, `💳`, `⬆️`, `⏰`).
- **T4 (P1 Extraction):**
  - Remove hospitality/POI tokens from `KNOWN_DESTINATION_PATTERNS` (`PageClient.tsx:612-644`) and stop sending heuristic `destination_candidates` in `structured_json`.
  - Add transit/layover guard (`via/layover in/connecting in/transit through/stopover in`) and lodging/landmark span masking in `src/intake/extractors.py` so `"Atlantis"`, `"Al"`, `"Gold"`, `"Istanbul"` do not pollute `destination_candidates`.
- **T5 (P1 Blocker & Follow-up Copy):**
  - Pass `analysis` into `formatTravelerBlockerItem` (`PageClient.tsx:1552-1564`) so `incomplete_intake` names only actually missing fields, and full-sentence `live_checks` blockers pass through verbatim instead of hitting generic fallback copy.
  - Humanize `follow_up_questions` labels in `src/intake/orchestration.py:414-418`.
- **T6 (P1 Telemetry):**
  - Emit server-sealed `product_a_interest_signal` in `post_public_checker_route_request` (`public_checker.py`).
  - Fix `intake_started` in `public_checker_service.py` so non-consented runs still log accurate `has_destination` / `has_dates` / `has_budget_band` / `has_traveler_profile` booleans.
  - Move `finding_evidence_opened` off JSON export; add `report_exported`, `checker_page_viewed`, `sample_plan_selected`, `showcase_tab_selected`, `matches_requested` to `ProductBEventStore.ALLOWED_EVENT_NAMES` with KPI-isolation so pre-intake events never inflate `inquiries_total`.
- **T7 (P1 `/re-verify` Completion):** Fix `post_public_checker_re_verify` (`public_checker.py:267-327`) to use `packet.facts.date_window` / `date_start` and stored `public_checker_entity_checks` names (instead of `""`), and wire a `"Re-check live signals"` button in `ResultsView`.
- **T8 (P1 Hardening):** Add `persistence.file_lock` to `public_checker_access.py` (`access_tokens.json`) and `agency_marketplace.py` (`route_leads.jsonl`), and centralize `get_public_checker_agency_id()` in `public_checker.py` (fail-closed `503` if `"__UNSET__"`).

### Testing & Verification Tasks
- **V1:** BFF capability-token proxy test / verification (`GET/export/DELETE /api/public-checker/trip/{id}` returning 200 with token, 403 without).
- **V2:** Python unit tests for Dubai/lodging/transit destination extraction (`tests/test_destination_extraction.py` or intake extractor tests), `re-verify` date/entity continuity (`tests/test_public_checker_reverify_and_fingerprint.py`), `product_a_interest_signal` + funnel KPI isolation (`tests/test_product_b_events.py`), and `file_lock` concurrency on `public_checker_access.py`.
- **V3:** Frontend Vitest tests (`blocker-copy.test.tsx`, `honesty-sweep.test.tsx`, `WedgeVisualShowcase` live-run no-fabrication test) + `tsc --noEmit` + `ruff check .`.

### Owner Decisions Required (Do Not Arbitrarily Choose)
1. **D1 — Marketplace Supply Policy (`data/agency_marketplace/profiles.json`):** Operate a staffed house/founding concierge desk for unmatched B2C leads, or sync opt-in B2B SaaS agencies into `profiles.json` and frame `/itinerary-checker` explicitly as concierge-assisted waitlist until regional supply is onboarded?
2. **D2 — Primary B2C Hero Positioning (`PageClient.tsx:1069`):** Shift Fold 1 headline from `"clearer trip map"` (collides with Spotinga) to **"Second-Opinion Audit for AI & DIY Itineraries"** (safety/entity/layover) vs. **"Luxury Perks & Advisor Rescue"**?
3. **D3 — Approve Deletion of Superseded Legacy `/api/public-checker/{trip_id}` (`public_checker.py:409-449`):** Approve deleting these routes and migrating `test_call_capture_e2e.py` / `test_product_b_events.py` onto `/api/public-checker/trip/{trip_id}*` to close the cross-tenant IDOR hole (per §6.1.4).
4. **D4 — Agency Lead Inbox & Brief Handoff Architecture:** Upon consented `route-request`, should we clone a redacted brief into the matched agency's `TripStore` + expose `GET /api/v1/leads` so `"Open trip"` and contact reply work in `/overview`, or notify agencies via email/webhook first?
5. **D5 — Persistent Shareable Report URLs (`/report/[tripId]#token=...`):** Approve moving beyond `sessionStorage`-only tokens so travelers can bookmark/share live reports with companions or external advisors.
