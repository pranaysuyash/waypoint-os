# Workbench / Trip Workspace Architecture — Implementation Plan
**Date:** 2026-05-14  
**Status:** AWAITING USER APPROVAL — no code changes until approved  
**Branch:** master  
**Related:** `PHASE4F_OPS_UX_DESIGN_2026-05-08.md`, `PHASE5A_BOOKING_EXECUTION_DESIGN_2026-05-09.md`  
**Brainstorm artifact:** `Docs/brainstorm/BRAINSTORM_WORKBENCH_TRIP_WORKSPACE_2026-05-14.md`  
**Design doc:** `~/.gstack/projects/travel_agency_agent/pranay-master-design-20260514.md`

> **Updated 2026-05-14 after wide-open brainstorm (9 roles).** Key corrections from brainstorm incorporated below.

---

## Problem Statement

Two surfaces claim the same UX jobs:

| Job | Workbench | Trip Workspace |
|-----|-----------|----------------|
| New inquiry creation | ✅ Primary | — |
| AI processing (Spine) | ✅ Primary | — |
| Trip Details view | ✅ (PacketTab) | ✅ (Trip Details tab) |
| Risk Review | ✅ (SafetyTab) | ✅ (Risk Review tab) |
| Booking Ops execution | ✅ (OpsPanel) | ❌ **not present** |

This causes:
- Operators complete AI processing in Workbench → routed to Trip Workspace → need to return to Workbench to do Ops
- Trip Workspace cannot be a durable record if operational execution lives elsewhere
- Dead code accumulating (DecisionTab, StrategyTab never rendered)
- Architectural smell: Trip Workspace layout reads transient workbench store state (`result_run_ts`)

---

## Recommended Approach: Option B — Disciplined Clarification

**Workbench = creation + AI processing only**  
**Trip Workspace = durable record for all trip-level work**

This implements Feature #7 "Booking Execution Master Record" (documented in `PHASE5A_BOOKING_EXECUTION_DESIGN_2026-05-09.md`) and aligns with the nav-modules architecture intent.

Option C (redirect existing trips from Workbench) is deferred until a re-run affordance is built in Trip Workspace.

---

## Brainstorm Corrections (Critical — Read Before Implementing)

**1. The `result_validation` coupling is already handled. Risk reduced from "moderate" to "low".**

Executioner role verified from code: `OpsPanel.tsx` lines 182–184 already have a working fallback:
```typescript
const readiness = 
  (result_validation as {...})?.readiness ??
  (trip?.validation as {...})?.readiness;  // ← already works
```
`spine_api/server.py` (lines 1148, 2068, 2309) already passes `trip.get("validation")` into the API response. Step 5 is low-risk, not moderate-risk.

**2. Step 2.5 is missing from the plan — add it.**

The post-Spine "View Trip" button currently routes to `/trips/${completedTripId}/intake`. For proposal-stage trips, it should route to `/trips/${completedTripId}/ops`. This is the single most important operator workflow fix and was not in the original plan.

**3. DecisionTab.tsx is 446 lines of real business logic. Do NOT silently delete.**

Skeptic verified: `DecisionTab.tsx` has a full `STATE_BADGE_CLASS` lookup table, suitability flag acknowledgment, budget breakdown rendering, and follow-up question handling. It was built and then removed from the tab list. Before removing the import, open a tracked issue documenting what this file was for. Replace "zero risk cleanup" characterization with "low render risk, preserve intent via issue".

**4. Add power-user migration signal.**

Operators who have built muscle memory on Workbench → Ops will be the most affected. Add a first-visit tooltip or banner in the Trip Workspace Ops tab: "Booking operations have moved here from Workbench." Remove after 30 days.

**5. Workbench Ops deprecation must be scoped, not deferred indefinitely.**

Executioner #2 identified that Option B without a deprecation commitment creates permanent parallelism — two valid execution paths, doubled maintenance surface. Fix: Step 7 (remove Ops from Workbench) must be scoped to ship in the same or immediately following release as Steps 1–6. It should not be "deferred indefinitely."

---

## Pre-Implementation Verification Checklist

Before writing any code, confirm:

- [ ] **Verified by brainstorm:** `trip.validation` is already in API response (`spine_api/server.py` passes `trip.get("validation")`). Confirm it's populated for trips at `proposal` and `booking` stage before Step 5.
- [ ] `spine_api/contract.py` — confirm `spine_updated_at` or `last_processed_at` field exists on trip response, or confirm `updated_at` is acceptable proxy for "last processed" display.
- [ ] Deep-link audit: are there any bookmarked or shared URLs pointing to `/workbench?tab=ops`? (Slack, Notion SOPs, onboarding docs) — check with Pranay before removing Workbench Ops tab.
- [ ] `routes.ts` Phase 1L redirect comments — is Phase 2 cleanup safe alongside this work?
- [ ] Open a tracked issue for DecisionTab.tsx / StrategyTab.tsx before removing imports — document what they were for.

---

## Implementation Steps

### Step 1 — Archive dead imports (low risk, preserve intent)

> **Brainstorm correction:** DecisionTab.tsx is 446 lines of real business logic. "Zero risk" was wrong. Correct characterization: zero render risk, but the file's intent must be preserved before removing the import.

**File:** `frontend/src/app/(agency)/workbench/PageClient.tsx`

Before removing lines 46–47, open a Linear/GitHub issue documenting: what `DecisionTab` and `StrategyTab` were built for, when they were removed from the tab list, and whether the logic is already replicated elsewhere (PacketTab, SafetyTab). Then remove the imports:
```typescript
// REMOVE (after issue filed):
const DecisionTab = dynamic(() => import('./DecisionTab'))
const StrategyTab = dynamic(() => import('./StrategyTab'))
```

Do NOT delete `DecisionTab.tsx` or `StrategyTab.tsx` files until the issue is resolved — the files contain non-trivial logic.

**Verification:** `bun run build` passes; no render change. Issue filed with file inventory.

---

### Step 2 — Add `'ops'` to WorkspaceStage type

**File:** `frontend/src/lib/routes.ts`

Change:
```typescript
export type WorkspaceStage = 'intake' | 'packet' | 'decision' | 'strategy' | 'output' | 'safety' | 'suitability' | 'timeline';
```

To:
```typescript
export type WorkspaceStage = 'intake' | 'packet' | 'decision' | 'strategy' | 'output' | 'safety' | 'suitability' | 'timeline' | 'ops';
```

**Verification:** TypeScript compiles. No behavior change — the type now covers the new route.

---

### Step 3 — Add Ops tab to Trip Workspace layout

**File:** `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`

Add to `STAGE_TABS` array (after `timeline`):
```typescript
{ id: "ops", label: "Ops" },
```

The tab should only be visible when `trip.stage === 'proposal' || trip.stage === 'booking'` — same gate as the current Workbench `showOps` logic. Implement this by adding a `hidden` condition in the tab render loop (consistent with how other tabs use `canAccessPlanningStage`).

**Verification:** Navigate to a trip in `proposal` stage → Ops tab appears. Navigate to a trip in `intake` stage → Ops tab hidden.

---

### Step 2.5 — Fix post-Spine navigation ⬅ NEW (from brainstorm)

> **This step was missing from the original plan. It is the single most important operator workflow fix.**

**File:** `frontend/src/app/(agency)/workbench/PageClient.tsx`

The "View Trip" button after a Spine run currently navigates to:
```typescript
push(`/trips/${completedTripId}/intake`)
```

For trips at `proposal` or `booking` stage, it should navigate to:
```typescript
const targetTab = trip?.stage === 'proposal' || trip?.stage === 'booking' ? 'ops' : 'intake';
push(`/trips/${completedTripId}/${targetTab}`)
```

This ensures operators land directly in the Ops surface after completing an AI run for a trip that's ready for booking execution, rather than having to hunt for the Ops tab.

**Verification:** Run Spine on a trip in `proposal` stage → click "View Trip" → lands on `/trips/[id]/ops`, not `/intake`.

---

### Step 4 — Create `/trips/[tripId]/ops/` page

Create two new files:

**`frontend/src/app/(agency)/trips/[tripId]/ops/page.tsx`:**
```typescript
export { default } from './PageClient';
```

**`frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx`:**
- Import `OpsPanel` from `../../workbench/OpsPanel` (or move to shared location — see Step 6)
- Use `TripContext` to get `tripId` and `trip`
- Pass `tripId` and `trip` to `OpsPanel`
- Wrap with `PlanningStageGate` if consistent with other gated pages

Minimal shell:
```typescript
'use client';
import { use } from 'react';
import { TripContext } from '@/contexts/TripContext';
import OpsPanel from '../../../workbench/OpsPanel';

export default function OpsPageClient() {
  const { trip, tripId } = use(TripContext);
  if (!trip || !tripId) return null;
  return <OpsPanel tripId={tripId} trip={trip} mode="full" />;
}
```

**Verification:** Navigate to `/trips/[real-tripId]/ops` → OpsPanel renders with correct trip data. All booking, documents, payments functionality works.

---

### Step 5 — Verify and clean OpsPanel store coupling

> **Brainstorm correction:** The coupling is ALREADY handled by a working fallback. Risk is LOW, not moderate. The `useWorkbenchStore` import may be removable with minimal code change.

**File:** `frontend/src/app/(agency)/workbench/OpsPanel.tsx`

The Executioner role verified from code:
- Lines 182–184: `result_validation` already falls back to `trip?.validation` which is populated by the API
- `spine_api/server.py` passes `trip.get("validation")` in lines 1148, 2068, 2309

Audit remaining `useWorkbenchStore` calls:

| Store field used | Current purpose | Status |
|-----------------|-----------------|--------|
| `result_validation` | Readiness assessment + BLOCKED/ESCALATED banner | Fallback `trip?.validation` already works — remove store read |
| Any other result fields | Confirm via `rg "useWorkbenchStore" OpsPanel.tsx` | Likely removable; confirm each |

The goal: remove the `useWorkbenchStore` import from OpsPanel entirely. The `trip` and `tripId` props + direct API calls should be sufficient.

**Verification:** Remove `useWorkbenchStore` import from OpsPanel → TypeScript finds remaining usages → fix each → compile passes → verify BLOCKED/ESCALATED banner still renders correctly via `trip.validation` → test with direct URL navigation (no prior Spine run in session).

---

### Step 6 — Fix cross-boundary store read in Trip Workspace layout

**File:** `frontend/src/app/(agency)/trips/[tripId]/layout.tsx`

Line 103:
```typescript
const { result_run_ts } = useWorkbenchStore();  // DELETE THIS
```

**Replacement options (pick one, verify during pre-implementation checklist):**

Option A — Use `trip.spine_updated_at` (if it exists in API response):
```typescript
const lastProcessed = trip?.spine_updated_at;
```

Option B — Use `trip.updated_at` as proxy (less precise but always available):
```typescript
const lastProcessed = trip?.updated_at;
```

Option C — Remove the "Last processed" display entirely from Trip Workspace header (if it's not critical UX).

Remove the `useWorkbenchStore` import from the layout file entirely.

**Verification:** Navigate to a trip via direct URL (simulating fresh session, no workbench store). "Last processed" date shows correct value (not undefined). No console errors about store hydration.

---

### Step 6.5 — Add power-user migration signal ⬅ NEW (from brainstorm)

> Operators who have muscle memory on Workbench → Ops will be the most affected and are the highest-value users. A silent move will create support tickets from your best operators.

**File:** `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx`

Add a first-visit tooltip or dismissible banner on initial render:
```
"Booking operations have moved here from Workbench. [Dismiss]"
```

Store dismissal in localStorage keyed by user. Auto-remove after 30 days or after first dismissal.

**Verification:** Visit Trip Workspace Ops tab for first time → banner appears → dismiss → does not reappear.

---

### Step 7 — Remove Ops from Workbench

> **Brainstorm requirement:** This step must ship in the same or immediately following release as Steps 1–6. It must NOT be deferred indefinitely. Indefinite parallelism (two valid Ops paths) is worse than either the old or new model.

**File:** `frontend/src/app/(agency)/workbench/PageClient.tsx`

Only after Steps 4+5 are verified working AND Step 6.5 migration signal is live:

1. Remove `ops` from `workspaceTabs` array (lines 69–74)
2. Remove `showOps` derived state (line 198)
3. Remove OpsPanel render in the tab switch (lines 1095–1104 area)
4. Remove OpsPanel import if no longer used

**Verification:** Workbench shows three tabs: New Inquiry, Trip Details, Risk Review. After running Spine on a trip in proposal stage, "View Trip" navigates to Trip Workspace and the Ops tab is visible there. No 404 or missing functionality.

---

## Files Changed Summary

| File | Change Type | Step |
|------|-------------|------|
| `frontend/src/app/(agency)/workbench/PageClient.tsx` | Remove dead imports (issue first); fix post-Spine nav; remove Ops tab | 1, 2.5, 7 |
| `frontend/src/lib/routes.ts` | Add `'ops'` to WorkspaceStage | 2 |
| `frontend/src/app/(agency)/trips/[tripId]/layout.tsx` | Add ops tab with stage gate; fix store read | 3, 6 |
| `frontend/src/app/(agency)/trips/[tripId]/ops/page.tsx` | Create new | 4 |
| `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx` | Create new + migration signal | 4, 6.5 |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Remove workbench store coupling (fallback already works) | 5 |
| `spine_api/contract.py` | Confirm `spine_updated_at` field or add it | 6 (verify) |
| [tracked issue] | Document DecisionTab.tsx / StrategyTab.tsx intent | 1 |

---

## Testing Protocol

For each step, after the change:

1. `cd frontend && npm test -- --run` — all tests pass (no new failures)
2. Start dev server: `cd frontend && npm run dev`
3. Golden path: create new inquiry → run Spine → "View Trip" → navigate to Ops tab → verify booking panel loads
4. Direct URL navigation: go directly to `/trips/[tripId]/ops` without visiting Workbench first → panel loads correctly
5. Stage gate: trip in `intake` stage → Ops tab hidden; trip in `proposal` stage → Ops tab visible
6. Fresh session: close and reopen browser → navigate to trip → "Last processed" shows correct date (not undefined)

---

## What NOT to do in this implementation

- Do not add a redirect from Workbench to Trip Workspace for existing trips — this is Option C and deferred.
- Do not move OpsPanel to a shared `components/` directory unless the component's internal imports already assume it (check first).
- Do not change the Spine run flow, draft lifecycle, or `completedTripId` handoff — those work correctly.
- Do not remove the `acknowledged_suitability_flags` session state from workbench store — it is intentionally ephemeral per-run, not per-trip.
- Do not touch Phase 1L redirect cleanup in the same PR unless explicitly scoped in.

---

## Longer-Term Roadmap (From Brainstorm — Not This Sprint)

**Phase 3 (next major feature sprint):**
- Workbench becomes a modal/gesture, not a nav location. "New Inquiry" is a verb — open a creation sheet, close when done, deposit trip into pipeline. Remove Workbench from sidebar nav entirely.
- Phase-adaptive tabs in Trip Workspace: Quoting phase shows Intake/Options/Quote Assessment; Executing phase shows Booking Record/Documents/Payments/Tasks.
- Pipeline triage view: counts by stage in sidebar (`Needs AI (3) / Needs Ops (7) / Active (12)`) before individual trip names.

**12-month leapfrog:**
- Client-facing trip URL (read-only first): agencies send a link, not a PDF. The trip workspace is the deliverable. This 3×s close rate in every comparable product.
- AI Guardian mode: nightly scan of confirmed bookings for disruptions (flight changes, hotel flags, visa advisories). Highest-retention feature by far.

## Open Questions (Resolve Before Starting Step 5+6)

1. **`spine_api/contract.py`** — does `TripResponse` include `spine_updated_at` or `last_processed_at`? Run: `rg "spine_updated_at|last_processed_at|updated_at" spine_api/contract.py`
2. **OpsPanel store usage audit** — run `rg "useWorkbenchStore" frontend/src/app/\(agency\)/workbench/OpsPanel.tsx` to list every field used beyond `result_validation`
3. **`PHASE5A_BOOKING_EXECUTION_DESIGN_2026-05-09.md`** — confirm the intended data shape for Trip Workspace ops panel before implementing Step 4/5.
4. **DecisionTab.tsx intent** — run `git log --oneline frontend/src/app/\(agency\)/workbench/DecisionTab.tsx` to see when it was last touched and by what commit message, before filing the tracking issue.
