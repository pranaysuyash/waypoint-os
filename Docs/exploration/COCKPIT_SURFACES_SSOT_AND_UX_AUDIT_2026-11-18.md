# Trip Workspace Cockpit (`/trips/[tripId]/*`) — SSOT, Routing & UX Audit

- **Date:** 2026-11-18
- **Scope:** All 10 per-trip workspace cockpit routes under `frontend/src/app/(agency)/trips/[tripId]/` (`layout.tsx`, `intake`, `packet`, `strategy`, `suitability`, `decision`, `output`, `safety`, `ops`, `timeline`, `followups`) and their backing workspace panels (`IntakePanel`, `PacketPanel`, `StrategyPanel`, `SuitabilityPanel`, `DecisionPanel`, `SafetyPanel`, `OutputPanel`, `IrropsReportSection`).
- **Baseline Verification:** Live Chrome DevTools inspection against `http://localhost:3005/trips/trip_f0ed923537e2/{intake,packet,timeline,followups}` (backed by live FastAPI/Postgres on `:8000`) + `6/6` Vitest suites (`41/41` tests passing) in `frontend/src/app/(agency)/trips/[tripId]/`.

---

## Findings Register

### COCKPIT-01 (P1 Architecture / Navigation Bug): `suitability` and `followups` sub-routes are orphaned from `STAGE_TABS`
- **Observation:** `frontend/src/app/(agency)/trips/[tripId]/layout.tsx` defines `STAGE_TABS` with 8 tabs (`intake`, `packet`, `strategy`, `decision`, `output`, `safety`, `ops`, `timeline`), while the filesystem contains 10 sub-routes (`suitability` and `followups` are omitted). `getActiveStage(pathname)` falls back to `"intake"`, causing **Intake** to be highlighted as `aria-current="page"` whenever an operator visits `/trips/[tripId]/suitability` or `/trips/[tripId]/followups`.
- **Additional Defect in `suitability/PageClient.tsx`:** Manually re-fetches `/api/trips/${tripId}` in `useEffect` instead of reading from `useTripContext()`, uses inline `/trips/${tripId}/packet` instead of `getTripRoute(tripId, 'packet')`, and uses unstyled `<div>` loading/error states instead of `InlineLoading`/`InlineError`.
- **First-Principles Fix:**
  1. Add `'followups'` to `WorkspaceStage` in `frontend/src/lib/routes.ts` and include `followups` in `STAGE_TABS` in `layout.tsx` (label: `"Follow-ups"`), and handle `'suitability'` cleanly in `getActiveStage` (or map it to `decision`/`suitability`) so `Intake` is never falsely highlighted.
  2. Refactor `suitability/PageClient.tsx` to read `trip` from `useTripContext()`, navigate with `getTripRoute(tripId, 'packet')`, and use `InlineLoading`/`InlineError`.

### COCKPIT-02 (P0 Functional Bug): `/trips/[tripId]/followups` hits 404 `/api/followups/dashboard` with malformed query string
- **Observation:** `frontend/src/app/(agency)/trips/[tripId]/followups/PageClient.tsx:50-51` calls `` `/api/followups/dashboard?${filterParam}${statusParam}` `` where `filterParam` starts with `&` (producing `?&filter=...`), and no `/api/followups/dashboard/route.ts` exists in Next.js BFF (the canonical BFF route is `frontend/src/app/api/followups/route.ts` at `/api/followups`, which proxies to backend `/followups/dashboard`).
- **First-Principles Fix:** Construct clean `URLSearchParams` and call `/api/followups${qs ? `?${qs}` : ''}` so live filtering/loading works without 404s.

### COCKPIT-03 (P0 Functional Bug): `SafetyPanel.tsx` reads only transient `useWorkbenchStore()` and ignores persisted `trip.safety`
- **Observation:** `frontend/src/components/workspace/panels/SafetyPanel.tsx:19-30` reads `result_safety`, `result_traveler_bundle`, and `result_internal_bundle` solely from `useWorkbenchStore()`. Navigating directly to `/trips/[tripId]/safety` or reloading the browser always shows `"Safety review not ready yet"`, even when `trip.safety` is persisted in PostgreSQL.
- **First-Principles Fix:** Wire `SafetyPanel.tsx` to `useTripContext({ optional: true })` and read `result_safety || context?.trip?.safety || null`, `result_traveler_bundle || context?.trip?.traveler_bundle || null`, and `result_internal_bundle || context?.trip?.internal_bundle || null`, matching `DecisionPanel` and `OutputPanel`.

### COCKPIT-04 (P1 Operator UX / Developer Jargon Leak): `NEXT_PUBLIC_ALLOW_DEBUG_JSON=true` amber warning & disabled button rendered in 5 cockpit panels
- **Observation:** `PacketPanel.tsx`, `StrategyPanel.tsx`, `DecisionPanel.tsx`, `SafetyPanel.tsx`, and `OutputPanel.tsx` all render an amber warning banner instructing travel agents to `"Set NEXT_PUBLIC_ALLOW_DEBUG_JSON=true in a secure environment to enable"` alongside a permanently disabled `Show Technical Data` button.
- **First-Principles Fix:** When `!debugJsonAllowed`, omit both the developer env-var notice and the disabled debug toggle completely. Render the toggle only when `debugJsonAllowed` is `true`.

### COCKPIT-05 (P1 Operator UX / Machine Token Leaks): Raw internal enums, JSON strings, and snake_case tokens displayed to operators
- **Evidence (observed live in Chrome DevTools):**
  - `IntakePanel.tsx:1337`: renders `hardBlockers[0]` raw (`"extraction_quality"`).
  - `PacketPanel.tsx`: renders `{"adults":2,"children":2}` via `JSON.stringify`, raw authority tokens (`explicit_user`, `derived_signal`), raw enum values (`semi_open`, `nothing_booked`, `open_market`), and internal system flag `Internal Data Present: true (100%)`.
  - `IrropsReportSection.tsx:64`: renders `"Delay reports need delay_minutes."`.
- **First-Principles Fix:** Introduce canonical humanization helpers (`formatBlockerLabel`, `formatPacketAuthority`, `formatPacketValue`) in `frontend/src/lib/label-maps.ts`, suppress internal-only `internal_data_present` signal from operator-facing `Inferred Details`, format plain objects as readable key-value summaries, and rewrite the IRROPS validation message to `"Delay reports require a delay duration in minutes."`.

### COCKPIT-06 (P1 Accessibility): 2 form-field accessibility issues on `/trips/[tripId]/intake`
- **Observation (Chrome DevTools Issues):** `IntakePanel.tsx:1544` (`textarea` for Suggested Follow-up) and `IntakePanel.tsx:1554` (`input` for Recipient) lack `id`, `name`, and `aria-label`/`htmlFor`.
- **First-Principles Fix:** Add `id`, `name`, and `aria-label`/`htmlFor` attributes to both controls.

### COCKPIT-07 (P2 Test Hygiene): `IrropsReportSection.tsx` emits React `act(...)` warnings in `ops/__tests__/page.test.tsx`
- **Observation:** `vitest` logs `Warning: An update to IrropsReportSection inside a test was not wrapped in act(...)` across all 9 tests because async `loadState()` updates state after unmount/without cancellation guard.
- **First-Principles Fix:** Add an `isMounted` / cancellation guard in `IrropsReportSection.tsx` `useEffect` and keep `loadState` clean.

---

## Implementation Plan (Dependency-Aware)

1. **Shared Label & Humanization Helpers (`frontend/src/lib/label-maps.ts`):**
   - Add `formatBlockerLabel(code: string)`, `formatPacketAuthority(authority?: string | null)`, and `formatPacketValue(value: unknown)` with clean fallback formatting.
2. **Routing & Layout SSOT (`frontend/src/lib/routes.ts`, `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`):**
   - Add `'followups'` to `WorkspaceStage` and `STAGE_TABS`; fix `getActiveStage` so `suitability` and `followups` never fall back to highlighting `intake`.
3. **Sub-Page & Panel Fixes:**
   - `followups/PageClient.tsx`: fix `/api/followups` BFF URL + `URLSearchParams`.
   - `suitability/PageClient.tsx`: use `useTripContext()`, `getTripRoute()`, `InlineLoading`/`InlineError`.
   - `SafetyPanel.tsx`: fall back to `useTripContext()?.trip?.safety`, `traveler_bundle`, `internal_bundle`; remove `!debugJsonAllowed` developer leak.
   - `PacketPanel.tsx`: use `formatPacketValue` & `formatPacketAuthority`, filter internal-only `internal_data_present`, remove `!debugJsonAllowed` developer leak.
   - `StrategyPanel.tsx`, `DecisionPanel.tsx`, `OutputPanel.tsx`: remove `!debugJsonAllowed` developer leak.
   - `IntakePanel.tsx`: humanize `hardBlockers[0]` via `formatBlockerLabel`, add `id`/`name`/`aria-label`/`htmlFor` to Suggested Follow-up textarea & Recipient input.
   - `IrropsReportSection.tsx`: humanize `delay_minutes` error copy and add cancellation guard.
4. **Verification:**
   - Update/add Vitest unit tests covering `SafetyPanel` `TripContext` persistence, `PacketPanel` humanization, `layout.tsx` `followups` tab activation, and `followups` `/api/followups` URL.
   - Run `npx tsc --noEmit`, `npx eslint`, and full `trips/[tripId]` + panel Vitest suites.
   - Perform live Chrome DevTools verification on `/trips/trip_f0ed923537e2/{intake,packet,safety,followups}` confirming 0 console errors, 0 form-field issues, and 0 404s.
