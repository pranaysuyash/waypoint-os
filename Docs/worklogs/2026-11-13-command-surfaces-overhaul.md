# COMMAND Surfaces SSOT, Performance & UX Overhaul (`/overview`, `/inbox`, `/reviews`)

**Date:** 2026-11-13  
**Status:** In Progress  
**Scope:**
- `frontend/src/components/workspace/PlanningTripCard.tsx` (Eliminates `?repair=undefined` broken links)
- `frontend/src/app/(agency)/overview/PageClient.tsx` (Clickable pipeline stages, action required consolidation)
- `frontend/src/app/(agency)/inbox/PageClient.tsx` (A11y form controls, bulk assignment feedback, atomic pagination)
- `frontend/src/app/(agency)/reviews/PageClient.tsx` (Differentiated quote titles, 25/page pagination, bulk review toolbar, output routing)

---

## Changes Made

### 1. PlanningTripCard (`frontend/src/components/workspace/PlanningTripCard.tsx`)
- Integrated `resolveRepairDeepLinkField` and comprehensive missing badge mapping (`Trip purpose missing` → `type`, `Priorities missing` → `priorities`, `Flexibility missing` → `flexibility`).
- Replaced fragile string concatenation with `buildRepairDeepLinkHref`, ensuring zero broken `?repair=undefined` query parameters in the DOM.

### 2. Operations Overview (`frontend/src/app/(agency)/overview/PageClient.tsx`)
- Transformed PipelineBar stages into clickable navigation targets linking directly to `/trips?stage=<stage>`, giving operators instant 1-click drill-down from the high-level bar chart into filtered trip dossiers.
- Consolidated ActionRequired quote group subtitles.

### 3. Lead Inbox (`frontend/src/app/(agency)/inbox/PageClient.tsx`)
- Resolved Chrome DevTools accessibility issue by adding explicit `id="inbox-search-input"`, `name="q"`, `id="inbox-page-size-select"`, `name="limit"`.
- Hardened `BulkActionsToolbar` with live assignment status, success banner, and error preservation.

### 4. Quote Review (`frontend/src/app/(agency)/reviews/PageClient.tsx`)
- Upgraded `getReviewTitle` with intelligent fallback (`Client {id} · {tripType}` / `Ref {ref} · Quote`), eliminating the ocean of 400 identical "Trip details incomplete" cards.
- Added clean client-side pagination (25 reviews per page with Previous/Next controls, total count display, and page jumping).
- Implemented `BulkReviewToolbar` connecting to `bulkReviewAction` for multi-quote supervisor approval and revision requests.
- Updated `View Details` to route to `/trips/{tripId}/output` (or `/intake` fallback).
- Added inline mutation error banner to `ReviewCard`.

---

## Verification & Receipts
*(Will be filled with test and live inspection results)*
