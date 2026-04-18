# Session Writeup: Frontend Trip Workspace Fix

**Date**: 2026-04-17
**Status**: Completed
**Scope**: Fix broken trip loading, populate all tabs with mock data, wire Process Trip button

---

## Problem Statement

Two issues reported:

1. **Clicking recent trips opened a blank workspace** — navigating to `/workbench?trip=<id>` rendered an empty page because the workbench never read the `?trip=` URL parameter
2. **"Workbench" wording everywhere** — UI still said "workbench", "Open workbench" etc. despite previous claims of wording fixes

### Root Cause Analysis

| Issue | Root Cause | Evidence |
|-------|-----------|----------|
| Blank workspace on trip click | `workbench/page.tsx` read `?tab=` param but never read `?trip=` param. `useTrip(id)` hook existed but wasn't used. | `page.tsx:40` only read `searchParams.get('tab')` |
| Empty tabs | Tabs (Packet, Decision, Strategy, Safety) all depend on `useWorkbenchStore` results which were never populated from trip data | Each tab checked `if (!result_packet)` and showed empty state |
| Hardcoded dropdown | `IntakeTab` had a static array of 4 fake trips (`sgp-family`, `dubai-corp`) unrelated to real trip IDs | `IntakeTab.tsx:22-27` |
| Sparse mock data | Trip detail API (`/api/trips/[id]`) only had 2 of 7 trips, with no pipeline data | Only `TRP-2026-SGP-0315` and `TRP-2026-DXB-0418` existed |
| Dead Process Trip button | Had `isRunning` state but no `onClick` handler | Button rendered but did nothing |
| "Workbench" wording | 305+ references across source files; user-facing strings in `page.tsx`, `Shell.tsx`, `design-system.ts` | grep: `Open workbench`, `href='/workbench'` labels |

---

## Changes Made

### 1. Trip Detail API Enrichment

**File**: `frontend/src/app/api/trips/[id]/route.ts`

Expanded from 2 trips with basic fields to **7 trips** with full pipeline data:

| Trip ID | Destination | Packet | Decision | Strategy | Safety |
|---------|------------|--------|----------|----------|--------|
| `TRP-2026-SGP-0315` | Singapore (Family) | Facts, derived signals, ambiguities | PROCEED_SAFE + budget breakdown | Warm professional tone + agent/customer split views | Pass |
| `TRP-2026-DXB-0418` | Dubai (Corporate) | Facts, visa signals | ASK_FOLLOWUP + follow-up questions | Professional + visa urgency | Pass |
| `TRP-2026-AND-0420` | Andaman (Honeymoon) | Facts, scuba unknowns | BRANCH_OPTIONS + 2 branch options | Warm romantic + monsoon backup | Pass |
| `TRP-2026-MSC-0422` | Moscow (Solo) | Facts, geopolitical risk | STOP_NEEDS_REVIEW + hard blockers | Honest professional + escalation | Pass |
| `TRP-2026-BKK-0401` | Bangkok (Group) | Facts, dietary signals | PROCEED_SAFE + group questions | Fun enthusiastic + group deals | Pass |
| `TRP-2026-PAR-0430` | Paris (Anniversary) | Facts, luxury signals | ASK_FOLLOWUP + visa urgency | Luxury concierge tone | Pass |
| `TRP-2026-NYC-0512` | New York (Family) | Facts, peak pricing | ASK_FOLLOWUP + budget clarification | Warm helpful + Xmas pricing reality | Pass |

Each trip now returns:
- `customerMessage` — the original inquiry text
- `agentNotes` — owner/agent context
- `packet` — extracted facts, derived signals, ambiguities, unknowns, contradictions
- `validation` — is_valid + errors/warnings
- `decision` — decision_state, blockers, risk flags, follow-up questions, rationale, confidence score, budget breakdown
- `strategy` — session goal, priority sequence, tonal guardrails, suggested opening, assumptions
- `safety` — leakage check results
- `internal_bundle` — agent-only system context, user message, internal notes, constraints
- `traveler_bundle` — customer-safe message, follow-up sequence

### 2. Workbench Page: Store Hydration

**File**: `frontend/src/app/workbench/page.tsx`

Added `useHydrateStoreFromTrip()` hook that:
1. Reads `?trip=<id>` from URL params
2. Fetches trip via `useTrip(tripId)` (existing hook, was unused)
3. On load, pushes all pipeline data into Zustand store:
   - `setResultPacket(trip.packet)`
   - `setResultValidation(trip.validation)`
   - `setResultDecision(trip.decision)`
   - `setResultStrategy(trip.strategy)`
   - `setResultInternalBundle(trip.internal_bundle)`
   - `setResultTravelerBundle(trip.traveler_bundle)`
   - `setResultSafety(trip.safety)`
   - `setInputRawNote(trip.customerMessage)`
   - `setInputOwnerNote(trip.agentNotes)`
4. Uses `hydratedRef` to prevent re-hydration on re-renders (only hydrates once per trip ID)

**Result**: All 5 tabs (New Inquiry, Trip Details, Ready to Quote?, Build Options, Final Review) now render with populated data when any trip is opened.

### 3. IntakeTab: Rich Trip Display

**File**: `frontend/src/app/workbench/IntakeTab.tsx`

- Removed hardcoded mock trip dropdown (4 fake trips)
- Added trip detail card showing: destination, type, party size, dates, budget, reference ID
- Customer message and agent notes textareas now read from/write to Zustand store (pre-filled from trip data via hydration)
- Shows "No trip loaded" empty state when no trip is selected

### 4. Process Trip Button: Wired to Real Pipeline

**File**: `frontend/src/app/workbench/page.tsx`

The Process Trip button now:
- **Reads** intake inputs from Zustand store (`input_raw_note`, `input_owner_note`, stage, mode, etc.)
- **Calls** `POST /api/spine/run` via `useSpineRun` hook
- **Populates** store with results on success (packet, decision, strategy, safety, bundles)
- **Shows** green "Processed successfully" toast on success
- **Shows** red error banner on failure (with helpful message about spine API availability)
- **Disabled** when both customer message and agent notes are empty

The Reset button clears all store state (inputs + results).

### 5. Wording Cleanup

| File | Before | After |
|------|--------|-------|
| `page.tsx:426` | "Open workbench" | "Open Trip Workspace" |
| `Shell.tsx:39` | "Process trips through the workspace stages" | "Process trips through the analysis pipeline" |
| `design-system.ts:84` | `return "Workspace"` | `return "Trip Workspace"` |

Note: Route paths (`/workbench`) were intentionally kept as-is to avoid breaking existing navigation. Only user-facing labels were changed.

---

## Data Flow (Current State)

```
User clicks trip in Dashboard/Inbox/Reviews
  → Link: /workbench?trip=TRP-2026-SGP-0315
    → WorkbenchContent reads ?trip= param
      → useTrip("TRP-2026-SGP-0315") → GET /api/trips/TRP-2026-SGP-0315
        → Returns full trip with packet/decision/strategy/safety/bundles
      → useHydrateStoreFromTrip() pushes data into Zustand store
        → All 5 tabs render with data

User edits customer message / agent notes in IntakeTab
  → Zustand store updated in real-time

User clicks "Process Trip"
  → POST /api/spine/run with store inputs
    → BFF forwards to Python spine API (localhost:8000)
      → On success: store updated with new results, all tabs refresh
      → On failure: error banner shown

User clicks "Reset"
  → All store fields cleared, tabs show empty states
```

---

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/app/workbench/page.tsx` | Added trip loading, store hydration, Process Trip handler, Reset handler, success/error UI |
| `frontend/src/app/workbench/IntakeTab.tsx` | Removed hardcoded dropdown, added trip detail card, connected to Zustand store |
| `frontend/src/app/api/trips/[id]/route.ts` | Expanded from 2 to 7 trips with full pipeline mock data |
| `frontend/src/app/page.tsx` | "Open workbench" → "Open Trip Workspace" |
| `frontend/src/components/layouts/Shell.tsx` | Sidebar description updated |
| `frontend/src/lib/design-system.ts` | Fallback page title updated |

## Files NOT Modified (Intentional)

| File | Reason |
|------|--------|
| `frontend/src/stores/workbench.ts` | Store structure unchanged; only consumers changed |
| `frontend/src/hooks/useTrips.ts` | `useTrip(id)` hook already existed and worked correctly |
| `frontend/src/app/workbench/PacketTab.tsx` | Already reads from store correctly; now gets data |
| `frontend/src/app/workbench/DecisionTab.tsx` | Same — reads from store, now populated |
| `frontend/src/app/workbench/StrategyTab.tsx` | Same |
| `frontend/src/app/workbench/SafetyTab.tsx` | Same |
| Route paths (`/workbench`) | Kept as-is to avoid breaking navigation; wording only changed in labels |

---

## Verification

- Build: `npx next build` passes clean (no TypeScript errors, no warnings)
- All 7 trips in list API (`/api/trips`) have corresponding detail entries in `/api/trips/[id]`
- Store hydration uses `useRef` guard to prevent double-hydration on React strict mode

---

## Known Limitations (Deferred to Real API Stage)

1. **Mock data is static** — trip detail API returns hardcoded JSON. No real database.
2. **Process Trip requires Python spine** — the button calls `localhost:8000` which must be running. In mock-only mode, trips come pre-processed.
3. **No mutations** — editing intake fields and re-processing works, but changes aren't persisted (no PUT/PATCH endpoints).
4. **Budget breakdown in INR** — the `formatINR` function in DecisionTab formats as rupees, but mock data uses USD strings. Will need alignment.
5. **Store hydration is one-way** — navigating away and back re-hydrates from API (no local cache). The `hydratedRef` prevents re-hydration within the same mount.

---

## Next Stage: Real API Migration

When moving from mock to real APIs, the following needs to change:

1. **Trip detail API** → replace `MOCK_TRIPS` with database queries
2. **Trip list API** → replace `MOCK_TRIPS` array with paginated DB queries
3. **Process Trip** → ensure Python spine API is deployed and accessible
4. **IntakeTab inputs** → persisted to DB on change or on Process Trip
5. **Store hydration** → only hydrate if store is empty (don't overwrite user edits)
6. **Error handling** → add retry logic, loading states per tab, network error recovery
