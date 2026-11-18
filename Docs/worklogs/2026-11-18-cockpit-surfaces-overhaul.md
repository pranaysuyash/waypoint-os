# Worklog: Trip Workspace Cockpit (`/trips/[tripId]/*`) SSOT, Routing & UX Overhaul

- **Date:** 2026-11-18
- **Audit Reference:** [COCKPIT_SURFACES_SSOT_AND_UX_AUDIT_2026-11-18.md](../exploration/COCKPIT_SURFACES_SSOT_AND_UX_AUDIT_2026-11-18.md)

## Summary of Changes

1. **Workspace Cockpit Navigation & Stage Routing (`layout.tsx`, `routes.ts`, `planning-status.ts`, `suitability/PageClient.tsx`):**
   - Added `'followups'` to `WorkspaceStage` in `frontend/src/lib/routes.ts`, `BLOCKED_PLANNING_ALLOWED_STAGES` in `frontend/src/lib/planning-status.ts`, and `STAGE_TABS` in `frontend/src/app/(agency)/trips/[tripId]/layout.tsx` (`Follow-ups`).
   - Updated `getActiveStage(pathname)` in `layout.tsx` so `suitability` maps to `decision` instead of falsely highlighting `Intake`, and removed unused `timelineEvents`.
   - Refactored `frontend/src/app/(agency)/trips/[tripId]/suitability/PageClient.tsx` to read `trip` from `useTripContext()` (eliminating redundant `/api/trips/${tripId}` fetch), navigate via `getTripRoute(tripId, 'packet')`, and render `InlineLoading` / `InlineError`.

2. **Follow-ups BFF Endpoint & Query Hygiene (`followups/PageClient.tsx`):**
   - Fixed the broken `/api/followups/dashboard?${filterParam}${statusParam}` call (404 + malformed `?&...`) to use clean `URLSearchParams` against canonical `/api/followups`.

3. **SafetyPanel Persistence Wiring (`SafetyPanel.tsx`):**
   - Wired `SafetyPanel.tsx` to `useTripContext({ optional: true })` so it falls back to persisted `trip.safety`, `trip.traveler_bundle`, and `trip.internal_bundle` when accessed directly via `/trips/[tripId]/safety` or after page reload.

4. **Operator UX & Developer Jargon Cleanup (`label-maps.ts`, `IntakePanel.tsx`, `PacketPanel.tsx`, `StrategyPanel.tsx`, `DecisionPanel.tsx`, `OutputPanel.tsx`, `SafetyPanel.tsx`, `IrropsReportSection.tsx`):**
   - Added `BLOCKER_LABELS`, `AUTHORITY_LABELS`, `formatBlockerLabel`, `formatPacketAuthority`, and `formatPacketValue` in `frontend/src/lib/label-maps.ts`.
   - Humanized `hardBlockers[0]` (`extraction_quality` → `"Required trip details are still incomplete"`) in `IntakePanel.tsx`.
   - Humanized `PacketPanel.tsx` table authorities (`Client stated`, `System inferred`), values (`Semi-open`, `Flexible`, `Total trip`, `Nothing booked yet`, `Open market`), and plain objects (`2 adults, 2 children` instead of raw `JSON.stringify`), and suppressed internal-only `internal_data_present` signal.
   - Removed the amber `Set NEXT_PUBLIC_ALLOW_DEBUG_JSON=true` developer banner and disabled button from `PacketPanel.tsx`, `StrategyPanel.tsx`, `DecisionPanel.tsx`, `SafetyPanel.tsx`, and `OutputPanel.tsx` when `!debugJsonAllowed`.
   - Rewrote `IrropsReportSection.tsx` validation error `"Delay reports need delay_minutes."` → `"Delay reports require a delay duration in minutes."` and added an unmount cancellation guard in `useEffect`.

5. **Accessibility (`IntakePanel.tsx`):**
   - Added `id`, `name`, `aria-label`, and `<label htmlFor="followup-recipient">` to the Suggested Follow-up draft `<textarea>` and Recipient `<input>` in `IntakePanel.tsx`.

## Verification Receipts

- **TypeScript:** `cd frontend && npx tsc --noEmit` → **0 errors**.
- **ESLint:** `npx eslint` on all 14 modified/added frontend files → **0 errors**.
- **Vitest:** `9/9` test files, `56/56` tests passing (`cockpit-overhaul.test.tsx`, `layout.test.tsx`, `layout-stale-link.test.tsx`, `gated-stage-pages.test.tsx`, `packet-page.test.tsx`, `followups/__tests__/page.test.tsx`, `ops/__tests__/page.test.tsx`, `SafetyPanel.test.tsx`, `OutputPanel.test.tsx`).
- **Live Browser (Chrome DevTools MCP against `:3005` + `:8000`):** Verified `/trips/trip_f0ed923537e2/intake`, `/packet`, and `/followups` render cleanly with 0 console errors, 0 form-field accessibility issues, and 200 OK on `/api/followups`.
