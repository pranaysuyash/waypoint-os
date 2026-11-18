# COMMAND Surfaces SSOT, Performance & UX Audit (`/overview`, `/inbox`, `/reviews`)

**Date:** 2026-11-13  
**Status:** In Progress / Implementation Wave  
**Scope:** The daily operational command surfaces of Waypoint OS:
1. `/overview` (`frontend/src/app/(agency)/overview/PageClient.tsx`, `useOverviewSummary.ts`, `buildActionRequiredItems.ts`)
2. `/inbox` (`frontend/src/app/(agency)/inbox/PageClient.tsx`, `frontend/src/components/inbox/*`)
3. `/reviews` (`frontend/src/app/(agency)/reviews/PageClient.tsx`, `frontend/src/components/reviews/*`)

---

## 1. Executive Summary & First-Principles Assessment

The **COMMAND** cluster represents the daily operational command cockpit for travel agency founders, managers, and designers. In a high-volume boutique or enterprise travel agency:
- **`/overview`** is the executive bird's-eye view: it aggregates queue depths, action-required priority items, pipeline velocity, and urgent watchdog alerts.
- **`/inbox`** is the front-door triage engine: incoming customer inquiries from email, web, WhatsApp, and concierge channels must be scored, ranked, filtered, assigned, or converted into active trips.
- **`/reviews`** is the supervisor quality control gate: every AI-crafted or designer-drafted quote requiring approval (due to margin thresholds, complex itineraries, high value, or policy holds) is evaluated, annotated, and signed off.

Our exhaustive codebase and live browser audit of these three surfaces reveals solid foundational models but several critical architectural gaps, broken deep links, missing bulk controls, accessibility defects, and unhandled mutation states.

---

## 2. Comprehensive Findings Register

### Area A: `/overview` (Operations Overview)

| ID | Severity | Finding | First-Principles Analysis & Long-Term Solution |
|---|---|---|---|
| **OV-01** | **P1 (Bug)** | Broken `?repair=undefined` deep links in `PlanningTripCard.tsx` | `PlanningTripCard.tsx` uses a static `fieldParam` dictionary mapping string badges (`'Budget missing' -> 'budget'`). When a trip has `'Trip purpose missing'`, `'Priorities missing'`, or other fields, `fieldParam[badge]` evaluates to `undefined`, generating `/trips/${trip.id}/intake?repair=undefined`. <br><br>**Fix:** Wire `buildRepairDeepLinkHref` from `@/lib/repair-deep-link` with complete field coverage (`'type'`, `'priorities'`, `'flexibility'`) and fallback to clean `/trips/${trip.id}/intake` without broken query parameters. |
| **OV-02** | **P2 (UX)** | Non-clickable Pipeline Bar stages | The PipelineBar displays planning stages (`Waiting for options`, `Planning in progress`, `Ready for quote review`, `Ready for booking`), but clicking them does nothing. Operators expect to click any stage bar or label to navigate directly to `/trips?stage=<stage>`. <br><br>**Fix:** Make each stage segment and label an interactive link/button that navigates to `/trips` with the corresponding stage filter applied. |
| **OV-03** | **P2 (A11y/Feedback)** | ActionRequired list priority contrast and key sanitation | `ActionRequiredList.tsx` renders priority tags and sanitized reasons, but lacks clean keyboard focus styles on group links and can render redundant duplicate subtitles when multiple quotes share the same owner review hold. <br><br>**Fix:** Deduplicate and consolidate grouped quote reasons cleanly; ensure explicit `focus-visible` ring on all action links. |
| **OV-04** | **P3 (Telemetry)** | StatCard metric number formatting & loading consistency | `displayCount` formats with `toLocaleString('en-IN')`, but if `unifiedState` has counts while domain queries are fetching, counts can momentarily jump between filtered limit totals and SSOT counts. <br><br>**Fix:** Anchor `useOverviewSummary` counts consistently on `useUnifiedState` with instant progressive rendering and zero flicker. |

---

### Area B: `/inbox` (Lead Inbox)

| ID | Severity | Finding | First-Principles Analysis & Long-Term Solution |
|---|---|---|---|
| **IN-01** | **P1 (A11y)** | Browser accessibility issue: Form field missing `id` or `name` | Chrome DevTools flags: `[issue] A form field element should have an id or name attribute (count: 1)`. In `inbox/PageClient.tsx`, the search input and row selector select box lack explicit `id` and `name` attributes. <br><br>**Fix:** Add `id="inbox-search-input"`, `name="q"`, `id="inbox-page-size-select"`, `name="limit"` and associate with explicit aria labels. |
| **IN-02** | **P1 (Resilience)** | Bulk assignment lacks mutation feedback & unhandled error recovery | When selecting multiple trips and clicking `Assign to...`, the UI immediately calls `assignTrips` and clears selection synchronously. If the network drops or backend fails, the operator receives no error banner or toast, and their selection state is wiped out. <br><br>**Fix:** Keep selection during mutation, show pending state ("Assigning X trips..."), display success feedback with count, and preserve selection on error with inline retry. |
| **IN-03** | **P2 (UX)** | Unclear View Profile preset impacts | The ViewProfile radio buttons (`Operations`, `Team Lead`, `Finance`, `Fulfillment`) persist to URL `?role=`, but the user has no clue what columns or prioritization rules each profile triggers. <br><br>**Fix:** Add subtle descriptive metadata tags or tooltips to each profile pill so the operator understands the operational lens (e.g. "Operations: SLA & unassigned triage", "Finance: Value & margin", "Team Lead: Workload distribution"). |
| **IN-04** | **P2 (Navigation)** | Filter changes cause redundant page push | In `InboxPageWithSearchParams`, changing filters resets `page=1` in `handleFiltersChange`, but a secondary `useEffect` also detects `page !== currentPage` and fires a redundant `updateParams`. <br><br>**Fix:** Simplify pagination state alignment to avoid duplicate history pushes. |

---

### Area C: `/reviews` (Quote Review)

| ID | Severity | Finding | First-Principles Analysis & Long-Term Solution |
|---|---|---|---|
| **RV-01** | **P1 (UX/Clarity)** | Identical "Trip details incomplete" titles across 400+ quotes | In `reviews/PageClient.tsx`, `getReviewTitle(review)` returns `'Trip details incomplete'` whenever `destination` is unknown or empty. Because 377+ quotes have unconfirmed destinations, the supervisor queue displays an ocean of identical card titles with no client or inquiry context. <br><br>**Fix:** Elevate title generation to incorporate trip reference, client name, or trip type (e.g. `Client 1DF96A · Leisure Quote` or `Ref TRIP-1C4679 · Custom Itinerary`) so cards are immediately identifiable at a glance. |
| **RV-02** | **P1 (Scalability)** | No pagination or virtualization for 402+ reviews | `getPendingReviews` returns all 402 reviews in an unpaginated array, which are rendered simultaneously in the DOM. This causes slow initial render and heavy DOM tree weight. <br><br>**Fix:** Implement client-side or server-side pagination (e.g., 20 or 25 reviews per page) with page size selection (`20`, `50`, `All`) and standard page navigation buttons (`Previous`, `Next`, page counter), identical to `/inbox` and `/trips`. |
| **RV-03** | **P1 (Feature Parity)** | Missing Bulk Review Action UI | `spine_api` provides `POST /analytics/reviews/bulk-action` and `governance-api.ts` provides `bulkReviewAction(requests)`, but `reviews/PageClient.tsx` has NO bulk selection or bulk approval toolbar! A supervisor with dozens of standard reviews must approve them one by one. <br><br>**Fix:** Add multi-select checkboxes, "Select All", and a `BulkReviewToolbar` enabling one-click bulk approval or revision requests with shared supervisor audit notes. |
| **RV-04** | **P2 (Routing)** | `View Details` links to raw `/intake` instead of Quote / Packet | In `ReviewCard`, the `View Details` button links to `/trips/${review.tripId}/intake`. But this is Quote Review! The reviewer needs to see the quote output, proposal, or packet decision details. <br><br>**Fix:** Route `View Details` to `/trips/${review.tripId}/output` (or `/decision` / `/packet`), with fallback to `/intake` if no quote is generated yet. |
| **RV-05** | **P2 (Resilience)** | Review Action error suppression | If `submitReviewAction` fails (e.g. network failure, permission error, or 400 validation error), the form closes immediately without showing an error message on the card. <br><br>**Fix:** Add error state tracking to `ReviewCard` and surface an inline error notice if the review action mutation rejects. |

---

## 3. Dependency-Aware Implementation Plan

### Phase 1: Shared Core & Deep-Link Resolution (Foundation)
1. Update `frontend/src/components/workspace/PlanningTripCard.tsx`:
   - Import `buildRepairDeepLinkHref` and `resolveRepairDeepLinkField` from `@/lib/repair-deep-link`.
   - Expand fieldParam map to include all missing badge variants (`Trip purpose missing`, `Priorities missing`, `Flexibility missing`, etc.).
   - Ensure clean fallback to `/trips/${trip.id}/intake` without broken `?repair=undefined`.

### Phase 2: `/overview` Operations Cockpit Elevation
1. Update `frontend/src/app/(agency)/overview/PageClient.tsx`:
   - Make PipelineBar stages interactive links to `/trips?stage=<stage>`.
   - Ensure StatCard counts remain rock-solid without layout shifts.
   - Improve ActionRequired grouped quote summaries.

### Phase 3: `/inbox` Lead Triage Hardening
1. Update `frontend/src/app/(agency)/inbox/PageClient.tsx`:
   - Fix all form control accessibility issues (`id` and `name` attributes on search and combobox).
   - Harden bulk assignment with pending spinner, error boundary, and success notification banner.
   - Clean up pagination state sync to eliminate redundant history pushes.

### Phase 4: `/reviews` Supervisor Approval Suite
1. Update `frontend/src/app/(agency)/reviews/PageClient.tsx`:
   - Enhance `getReviewTitle` with client / reference fallback for incomplete destinations.
   - Implement pagination (25 reviews per page with responsive page selector).
   - Add multi-select checkboxes and `BulkReviewToolbar` powered by `bulkReviewAction`.
   - Route `View Details` intelligently to `/trips/${review.tripId}/output`.
   - Add inline error banners on failed review actions.

### Phase 5: Verification & Regression Testing
1. Run `vitest` across all overview, inbox, and review test suites.
2. Run `tsc` and `eslint`.
3. Inspect live pages with Chrome DevTools MCP and take verification snapshots.
4. Document all receipts in `Docs/worklogs/2026-11-13-command-surfaces-overhaul.md` and update `Docs/INDEX.md`.
