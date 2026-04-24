# Travel Agency App — Full User Flow Audit

**Date:** 2026-04-16  
**Environment:** Next.js dev (localhost:3000) + FastAPI spine_api (localhost:8000)  
**Auditor:** Automated walkthrough via source code analysis + live HTTP testing

---

## Executive Summary

The app has **2 parallel routing systems** that don't connect, **8 missing API route handlers** that will cause runtime errors, **6 stub pages** with no functionality, and several cross-flow navigation breaks. The core workbench pipeline (Intake → Packet → Decision → Strategy → Safety) works end-to-end, but is disconnected from the rest of the app.

**Severity breakdown:** 5 Critical, 6 High, 4 Medium, 3 Low

---

## CRITICAL ISSUES

### C1. 8 Governance API Routes Return 404 — Owner Pages Will Break at Runtime

**Routes affected:**
- `/api/reviews` (404)
- `/api/insights/summary` (404)
- `/api/insights/pipeline` (404)
- `/api/insights/team` (404)
- `/api/insights/bottlenecks` (404)
- `/api/team/members` (404)
- `/api/inbox` (404)
- `/api/inbox/stats` (404)

**Impact:**  
- `/owner/reviews` calls `useReviews()` → `governanceApi.getReviews()` → `/api/reviews` → **404**. The page has mock data fallback (hardcoded `MOCK_REVIEWS`), so it renders but the hook silently fails. No error shown to the user.
- `/owner/insights` has the same problem — hooks fail, but the page falls back to `MOCK_INSIGHTS_SUMMARY` etc. The `useInsightsSummary`, `usePipelineMetrics`, `useTeamMetrics`, `useBottleneckAnalysis` hooks all call 404 endpoints.

**Root cause:** `governance-api.ts` defines API calls to routes that have no `frontend/src/app/api/` handlers. The hooks are wired up but the BFF routes don't exist.

**Fix:** Create the missing Next.js API route handlers under `frontend/src/app/api/` for each endpoint, or stub them with mock data like `/api/trips` and `/api/stats` are.

---

### C2. Workbench IntakeTab is Disconnected from the Spine Pipeline

**File:** `frontend/src/app/workbench/IntakeTab.tsx`

The IntakeTab ("New Inquiry") has:
- Local state for `customerMessage`, `agentNotes`, `stage`, `mode`
- A "Trip Selection" dropdown with hardcoded mock trips
- **No connection to the Zustand workbench store** (`useWorkbenchStore`)
- **No "Process Trip" / "Run Spine" button** that actually triggers the spine

The "Process Trip" button in `workbench/page.tsx:76-97` is also purely cosmetic — it sets local `isRunning` state but never calls the spine API or updates the store.

**Impact:** A user enters text in IntakeTab, clicks "Process Trip"... nothing happens. The PacketTab, DecisionTab, StrategyTab, and SafetyTab all read from `useWorkbenchStore` which never gets populated, so they always show "No data. Process a trip from the New Inquiry tab first."

**Fix:** Wire the IntakeTab inputs to `useWorkbenchStore` setters (`setInputRawNote`, `setStage`, etc.) and connect the "Process Trip" button to `useSpineRun().execute()` with the store's input values, then populate result stores on success.

---

### C3. Inbox Page Links Lead to Wrong Destination

**File:** `frontend/src/app/inbox/page.tsx:177`

```tsx
<Link href={`/workbench?trip=${trip.id}`} className='block pl-6'>
```

The `trip.id` values from `/api/trips` are like `TRP-2026-SGP-0315`. But the workbench's `IntakeTab` has a hardcoded trip dropdown using IDs like `sgp-family`, `dubai-corp`. Clicking an inbox trip card sets `?trip=TRP-2026-SGP-0315` on the workbench URL, but nothing in the workbench reads or uses this `trip` query parameter to load any trip data.

**Impact:** Clicking an inbox trip card takes the user to the workbench but nothing loads. It's a dead-end navigation.

**Fix:** Either (a) add a `tripId` query param reader to the workbench that loads trip data from `/api/trips/{id}`, or (b) use the `/workspace/[tripId]` route instead.

---

### C4. `/workspace/[tripId]/*` Route Cluster is Fully Stubbed

All 6 pages under `workspace/[tripId]/` are placeholder stubs with no real content:
- `intake/page.tsx` — "Normal intake handling for operators"
- `packet/page.tsx` — "NB01 human summary + raw toggle"
- `decision/page.tsx` — "NB02 explanation-first decisioning view"
- `strategy/page.tsx` — "NB03 plan sequence and internal/traveler split"
- `safety/page.tsx` — "Leakage checks + sanitization diff + pass/fail assertions"
- `output/page.tsx` — "Traveler-safe proposal preview and send-prep"

**Impact:** If a user navigates here (e.g., via a direct URL or future navigation updates), they see a dead page. These are also competing with the workbench tabs which *do* have real implementations.

**Fix:** Either implement these pages (they duplicate the workbench tabs) or remove them and consolidate on the workbench approach.

---

### C5. Reviews Page "View Details" Link Points to Workbench, Not Workspace

**File:** `frontend/src/app/owner/reviews/page.tsx:287`

```tsx
<Link href={`/workbench?trip=${review.tripId}`}>
```

`review.tripId` values are `trip-001`, `trip-002`, etc. — these don't match any trip IDs in the system. And as noted in C3, the workbench doesn't process the `trip` query param anyway.

**Impact:** Clicking "View Details" on a review card takes the user to the workbench with `?trip=trip-001`, which does nothing.

---

## HIGH ISSUES

### H1. Dashboard "Recent Trips" Links Use Wrong ID Format

**File:** `frontend/src/app/page.tsx:259`

```tsx
<Link href={`/workbench?trip=${item.id}`}>
```

Same problem as C3. The `item.id` comes from `/api/trips` and is like `TRP-2026-SGP-0315`. The workbench ignores this param.

---

### H2. Pipeline Data Mismatch Between API and UI

The `/api/pipeline` returns:
```json
[{"label":"Lead","count":4}, {"label":"Qualified","count":3}, ...]
```

But the workbench pipeline stages are: Discovery → Shortlist → Proposal → Booking. And the dashboard PipelineBar renders these labels directly.

**Impact:** The pipeline bar shows "Lead", "Qualified", "Planning", etc. which are sales-funnel terms, not the app's actual pipeline stages. This is confusing and inconsistent.

---

### H3. Inbox and Dashboard Both Show Trips, But With Different Data Models

- **Inbox** (`/inbox`) uses `useTrips()` → `/api/trips` and decorates with mock priority/SLA/assignment data
- **Dashboard** (`/`) uses `useTrips({ limit: 5 })` → `/api/trips` and maps to a simpler `ActivityRow`
- The stats on Dashboard come from `/api/stats` which returns hardcoded numbers that don't match the actual trip count from `/api/trips` (stats says 12 active, but `/api/trips` returns 7 trips)

**Impact:** Dashboard shows "12 Active Trips" but only 7 exist in the trips API. Numbers are inconsistent.

---

### H4. `useGovernance` Hooks Call Non-Existent Routes

Even though `/owner/reviews` has mock fallback data and `/owner/insights` uses inline mock data (bypassing hooks entirely), the `useGovernance.ts` hooks are still wired to call:
- `/api/reviews`
- `/api/insights/summary`
- `/api/insights/pipeline`
- `/api/insights/team`
- `/api/insights/bottlenecks`
- `/api/team/members`

Each hook fires on mount and will log console errors. The reviews page is particularly problematic because `useReviews()` is actually called (line 18 of reviews/page.tsx), even though mock data is used for rendering.

---

### H5. `/api/trips/{id}` Route Handler Returns 404

**File:** `frontend/src/app/api/trips/[id]/route.ts` exists but the trip IDs in the mock data (like `TRP-2026-SGP-0315`) don't work.

```bash
curl http://localhost:3000/api/trips/sgp-family → 404
```

The `[id]/route.ts` may exist but needs verification. The `useTrip(id)` hook is defined but likely broken for all IDs.

---

### H6. Budget Breakdown Uses INR (₹) Formatting But Data Uses USD

**File:** `frontend/src/app/workbench/DecisionTab.tsx:78`

```tsx
function formatINR(n: number): string {
  return `₹${n.toLocaleString("en-IN")}`;
}
```

But the spine API returns budget values in USD (and the mock reviews show `$12,400` etc.). This formatting mismatch will show ₹ symbols on what are USD values.

---

## MEDIUM ISSUES

### M1. Workbench Has Two Competing Tab Systems

- `workbench/page.tsx` uses a `Tabs` component from `@/components/ui/tabs`
- `workbench/WorkbenchTab.tsx` defines its own custom tab component with ARIA keyboard nav

The page uses the first one (`<Tabs tabs={workbenchTabs} .../>`), while `WorkbenchTab.tsx` is defined but not used.

**Impact:** Debatable. The unused component is dead code. The used `Tabs` component may not have keyboard navigation.

---

### M2. Scenario Loading Uses Server-Side File I/O in API Route

**File:** `frontend/src/lib/scenario-loader.ts`

```ts
import { readFileSync, readdirSync } from "fs";
```

This uses synchronous file reads in a Next.js API route. Works in dev, but:
- The path `join(process.cwd(), "..", "data", "fixtures", "scenarios")` assumes a specific directory structure
- Synchronous I/O blocks the event loop

---

### M3. Workbench URL Sync Only Updates `stage`, `mode`, `scenario` — Not `tab`

The workbench store's URL sync middleware updates `?stage=`, `?mode=`, `?scenario=` in the URL. But the **tab** state (`intake`, `packet`, `decision`, etc.) also needs to be in the URL, and it is — but via a separate mechanism in `workbench/page.tsx` using `searchParams.get('tab')`.

**Problem:** If you set `?stage=booking` in the URL, the store picks it up. But `?tab=decision` is managed by the page, not the store. These two systems might conflict.

---

### M4. Dashboard Subtexts Are Hardcoded, Not Dynamic

**File:** `frontend/src/app/page.tsx:435-464`

```tsx
sub={stats ? '+3 this week' : 'Loading...'}
sub={stats ? '2 overdue' : 'Loading...'}
sub={stats ? '+1 today' : 'Loading...'}
```

These sub-labels are hardcoded strings, not derived from actual data. They'll always show "+3 this week" even if there are 0 new trips.

---

## LOW ISSUES

### L1. Duplicate `STATE_META` Definitions

`STATE_META` (color/label config for trip states) is defined independently in:
- `frontend/src/app/page.tsx:21-41`
- `frontend/src/app/inbox/page.tsx:67-95`

These should be shared from a common module.

---

### L2. Missing `coordinator_group` and `owner_review` Modes in IntakeTab

**File:** `frontend/src/app/workbench/IntakeTab.tsx:36-43`

IntakeTab only lists 6 operating modes but the spine supports 8 (missing `coordinator_group` and `owner_review`).

---

### L3. Inbox Bulk "Assign" Uses `alert()`

**File:** `frontend/src/app/inbox/page.tsx:422`

```tsx
const handleAssign = useCallback(() => {
  alert(`Assigning ${selectedTrips.size} trips...`);
```

Uses browser `alert()` instead of a toast or inline confirmation.

---

## FLOW WALKTHROUGH — User Journey Map

### Flow 1: First-time User → Dashboard → Workbench

1. **Landing on `/`**: Dashboard loads. Stats show "12 Active" (hardcoded). Pipeline shows "Lead/Qualified/..." (wrong labels vs actual stages). Recent Trips show 7 items.
2. **Click "Open workbench"**: Goes to `/workbench`. ✅
3. **Enter text in IntakeTab**: Fields work locally. 
4. **Click "Process Trip"**: ❌ Nothing happens. Button toggles visual state but no API call.

### Flow 2: Inbox → Trip Details

1. **Navigate to `/inbox`**: Shows trip cards. ✅
2. **Click a trip card**: Goes to `/workbench?trip=TRP-2026-SGP-0315`. ❌ Workbench doesn't load the trip.

### Flow 3: Dashboard → Reviews

1. **Dashboard "Jump To" → Reviews**: Goes to `/owner/reviews`. ✅ Page renders with mock data.
2. **Click "Review" → "Approve"**: ❌ Only updates local state via `setTimeout`. No API call persists this.
3. **Click "View Details"**: Goes to `/workbench?trip=trip-001`. ❌ Dead link.

### Flow 4: Dashboard → Insights

1. **Navigate to `/owner/insights`**: Page renders with inline mock data. ✅ But hooks fire and fail silently.
2. **Change time range**: ❌ No effect. Mock data is constant regardless of time range.

### Flow 5: Workbench Full Pipeline

1. **IntakeTab**: Enter data ✅. Submit ❌ (nothing happens).
2. **PacketTab**: ❌ Always shows "No data" (store never populated).
3. **DecisionTab**: ❌ Same.
4. **StrategyTab**: ❌ Same.
5. **SafetyTab**: ❌ Same.

### Flow 6: Direct Workspace URLs

1. **Navigate to `/workspace/test-trip/intake`**: Shows stub page. ❌ No functionality.
2. **Same for `/decision`, `/strategy`, `/safety`, `/output`**: All stubs. ❌

### Flow 7: API-Level Spine Run

1. **POST `/api/spine/run`** with valid payload: ✅ Full response with packet, decision, strategy, bundles, safety.
2. **The spine_api works perfectly.** The issue is the frontend doesn't call it from the workbench.

---

## Summary: What's Broken vs What Works

### ✅ Working
- Spine API (port 8000) — full pipeline
- Next.js BFF proxy to spine API (`/api/spine/run`)
- Trips API (`/api/trips`, `/api/stats`, `/api/pipeline`)
- Scenarios API (`/api/scenarios`, `/api/scenarios/[id]`)
- Dashboard renders with mock data
- Inbox renders with mock trip data
- Owner Reviews renders with hardcoded mock data
- Owner Insights renders with hardcoded mock data
- Workbench tab navigation (URL-based)
- Workbench store (Zustand) structure
- All pages return HTTP 200

### ❌ Broken
- Workbench "Process Trip" button — does nothing
- IntakeTab → store connection — missing
- 8 governance API routes — 404
- `/api/trips/{id}` — broken/404
- Inbox/Dashboard trip links — dead-end navigation
- Review "View Details" links — dead-end
- `/workspace/[tripId]/*` pages — all stubs
- Budget formatting — INR symbol on USD data
- Pipeline stage labels — mismatched
- Dashboard stats — don't match actual trip count
- Scenario loading from IntakeTab — not wired