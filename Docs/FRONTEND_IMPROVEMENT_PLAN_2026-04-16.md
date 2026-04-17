# Waypoint OS — Frontend Improvement Plan
**Date**: 2026-04-16  
**Scope**: Targeted improvement pass — no redesign. Fixing information architecture, wiring live data paths, and promoting reusable panels without breaking any working screen.  
**Companion doc**: `FRONTEND_COMPREHENSIVE_AUDIT_2026-04-16.md` (prior strategic audit)

---

## 1. True Current State (Code-Verified)

The prior audit was based on route/file inspection without running the app. After reading every key source file directly, the actual status differs in important ways:

| Screen | Route | Real Status | Actual Issue |
|---|---|---|---|
| Overview / Dashboard | `/` | ✅ Working | Real API via `useTrips`, `useTripStats`, `usePipeline` |
| Inbox | `/inbox` | ⚠️ Partial | Real trips from API, but **assignment/SLA/priority driven by `Math.random()`** (`inbox/page.tsx` L340–341) |
| Workbench | `/workbench` | ⚠️ Partial | Form UI works; **"Process Trip" button sets a local boolean and calls nothing** — `useSpineRun` hook and BFF `/api/spine/run` route both exist and are implemented, they are just not wired together |
| PacketTab | `/workbench?tab=packet` | ✅ Best screen | Feature-complete; renders facts, derived signals, ambiguities, unknowns, contradictions with raw JSON toggle |
| DecisionTab | `/workbench?tab=decision` | ✅ + 1 bug | Good; silent typo bug at L9: `PROCEED_TRAVERER_SAFE` (double-r) — wrong CSS class applied for that state key |
| StrategyTab | `/workbench?tab=strategy` | ✅ Good | Internal vs traveller-safe split view works correctly |
| Owner Reviews | `/owner/reviews` | ⚠️ Partial | Visual is good; entirely backed by `MOCK_REVIEWS` local array + `setTimeout` — `useReviews()` hook in `hooks/useGovernance.ts` exists but is not used |
| Owner Insights | `/owner/insights` | ⚠️ Partial | Visual is good; backed by `MOCK_INSIGHTS_SUMMARY` constants — analytics hooks exist but are bypassed |
| All workspace pages | `/workspace/[tripId]/*` | ❌ Stubs | All 6 stage pages are 8-line placeholder stubs (`<h1>New Inquiry</h1><p>...</p>`) |
| Traveller surface | — | ❌ Missing | Not started |
| Public audit funnel | — | ❌ Missing | Not started |

### The Core Routing Misalignment

**Inbox cards, Overview activity rows, and Owner Reviews "View Details" all link to `/workbench?trip=<id>`.**  
The trip workspace routes at `/workspace/[tripId]/intake` (etc.) go nowhere — they are stubs.  
This is why the `/workbench` feels like "the app" when it is supposed to be a power tool.

---

## 2. The One Change That Unlocks Everything

**Current**: Every trip click → `/workbench?trip=<id>` → shared global Zustand store  
**Target**: Every trip click → `/workspace/<tripId>/intake` → trip-scoped workspace with shared layout

This single routing fix:
- Repositions `/workbench` as an audit/power-tool surface (correct role)
- Makes the trip workspace the primary operator surface (correct role)
- Allows a shared workspace `layout.tsx` to load trip context once and share it across all stage tabs

---

## 3. Improvement Waves

### Wave 1 — Routing & Navigation Fix
**Effort**: Very low (4 line changes + 1 NAV array update)  
**Impact**: High — every inbox card goes somewhere meaningful

#### 1a. Fix link targets in 3 files

| File | Line | Current | Target |
|---|---|---|---|
| `app/inbox/page.tsx` | L177 | `/workbench?trip=${trip.id}` | `/workspace/${trip.id}/intake` |
| `app/page.tsx` | L258 | `/workbench?trip=${item.id}` | `/workspace/${item.id}/intake` |
| `app/owner/reviews/page.tsx` | L287 | `/workbench?trip=${review.tripId}` | `/workspace/${review.tripId}/intake` |

#### 1b. Update Shell NAV (`components/layouts/Shell.tsx` L18–59)

```
Current                          →   Proposed
─────────────────────────────────────────────────────
[OPERATE]                             [OPERATE]
  Overview (/)                          Inbox (/inbox)         ← default landing
  New Leads (/inbox)                    Trips (/workspace)     ← new
  Trip Workspace (/workbench)           Overview (/)           ← secondary

[GOVERN]                              [GOVERN]
  Pending Reviews (/owner/reviews)      Pending Reviews
  Analytics (/owner/insights)           Analytics
                                        ─────────────
                                        [TOOLS]                ← new group
                                          Audit Workbench (/workbench)
```

No pages need to be created for this wave — `/workspace` can redirect to `/inbox` temporarily.

---

### Wave 2 — Workspace Shell Layout
**Effort**: Medium  
**Files to create**: `app/workspace/[tripId]/layout.tsx`, `contexts/TripContext.tsx`

Shared layout that wraps all trip stage pages:

1. Loads the canonical trip record once via `useTrip(tripId)`
2. Renders a persistent trip header: `destination | stage badge | assigned agent`
3. Renders stage tab navigation: **Intake | Packet | Decision | Strategy | Output | Safety**
4. Makes trip context available to child pages via React Context
5. Right-rail AI panel — collapsed by default, drawer on mobile

Tab navigation maps directly to the existing `/workspace/[tripId]/[stage]` folder structure — no new directories needed, the folders already exist.

**Layout wireframe:**
```
┌─ Waypoint › Inbox › TRP-2026-AND-0420 ─────────────── Awaiting Info ─┐
│ Intake │ Packet │ Decision │ Strategy │ Output │ Safety                │
├──────────────────────────────────────────────────────┬────────────────┤
│               Stage page content                     │ AI Assist (→)  │
│                                                      │                │
└──────────────────────────────────────────────────────┴────────────────┘
```

---

### Wave 3 — Wire the Workspace Stage Pages
**Effort**: Medium-high  
**Approach**: Extract workbench tabs into shared panel components; reuse in workspace pages

Replace the 6 placeholder stubs with real content:

| Workspace page | Source to reuse | Extraction needed |
|---|---|---|
| `/workspace/[tripId]/intake` | Adapt `workbench/IntakeTab.tsx` | Scope to tripId route param |
| `/workspace/[tripId]/packet` | `workbench/PacketTab.tsx` | Extract as `PacketPanel` (props instead of store) |
| `/workspace/[tripId]/decision` | `workbench/DecisionTab.tsx` | Extract as `DecisionPanel` |
| `/workspace/[tripId]/strategy` | `workbench/StrategyTab.tsx` | Extract as `StrategyPanel` |
| `/workspace/[tripId]/output` | New | Render `result_traveler_bundle` data |
| `/workspace/[tripId]/safety` | `workbench/SafetyTab.tsx` | Extract as `SafetyPanel` |

**Extraction pattern**: Each panel becomes a standalone component accepting data as props. The workbench tabs continue working unchanged by passing store data as props. Zero breaking changes to `/workbench`.

---

### Wave 4 — Wire "Process Trip" Button
**Effort**: Low (plumbing exists, just needs connecting)  
**File**: `app/workbench/IntakeTab.tsx`

Current state (`workbench/page.tsx` L75–97): button sets a local `isRunning` boolean and nothing else.

All the pieces exist:
- `hooks/useSpineRun.ts` — hook is implemented and correct
- `lib/api-client.ts` — `runSpine()` function is implemented
- `app/api/spine/run/route.ts` — BFF route is implemented and validates stage/mode contracts

Fix: In `IntakeTab.tsx`, import `useSpineRun` and call `execute(...)` on form submit. On success, call the workbench store setters (`setResultPacket`, `setResultDecision`, `setResultStrategy`, etc.) and advance to the Packet tab.

---

### Wave 5 — Remove Simulations from Production Code
**Effort**: Low per item  

**5a. Inbox random SLA** (`inbox/page.tsx` L340–341):
```diff
- const daysInStage = Math.floor(Math.random() * 5) + 1;
- const slaStatus: SLAStatus = daysInStage > 3 ? 'breached' : daysInStage > 2 ? 'at_risk' : 'on_track';
```
Replace with `trip.age` string parsing (e.g. "3d" → 3), or add `days_in_stage` field to the BFF trips response.

**5b. Inbox random assignment** (`inbox/page.tsx` L331–333):
```diff
- const assignments = ['agent-001', 'agent-002', 'agent-003', undefined];
- const assignedTo = assignments[index % 4];
```
Add `assigned_to` field to trip API response, or leave as unassigned if not yet in backend.

**5c. Owner Reviews mock data** (`owner/reviews/page.tsx` L305):
```diff
- const [reviews, setReviews] = useState(MOCK_REVIEWS);
+ const { data: reviews, isLoading, error } = useReviews();
```
`useReviews()` exists in `hooks/useGovernance.ts` — wire it. Replace `setTimeout` approve/reject/escalate handlers with real governance API calls from `lib/governance-api.ts`.

**5d. Owner Insights mock data** (`owner/insights/page.tsx`):
Same pattern — analytics hooks exist in `hooks/useGovernance.ts`, page needs to use them instead of `MOCK_INSIGHTS_SUMMARY` constants.

---

### Wave 6 — Bug Fix: DecisionTab Typo
**Effort**: 1 line  
**File**: `app/workbench/DecisionTab.tsx` L9

```diff
- PROCEED_TRAVERER_SAFE: styles.stateGreen,   // typo: double-r — silent CSS class bug
  PROCEED_TRAVELER_SAFE: styles.stateGreen,   // correct (L10)
```

The API returns `PROCEED_TRAVELER_SAFE`. The typo key on L9 silently applies no CSS class (falls through to default) for any response that uses the typo spelling. Remove it.

---

### Wave 7 — State Model Cleanup
**Effort**: Medium  
**File**: `stores/workbench.ts`

**Problem**: The store contains 4 conceptually separate concerns:
1. Draft input text (`input_raw_note`, `input_owner_note`, etc.)
2. Run config (`operating_mode`, `stage`, `scenario_id`, etc.)
3. Result state (`result_packet`, `result_decision`, etc.)
4. URL sync state (`url_stage`, `url_mode`, `url_scenario`) — a duplicate of config

The `urlSyncMiddleware` (L75–143) overrides setters to write to URL, then watches the store and writes URL again — a potential double-write. Meanwhile, `workbench/page.tsx` L38–44 already reads from `useSearchParams` directly.

**Non-breaking fix**:
1. Remove `UrlSyncState` interface and `urlSyncMiddleware`
2. Let the workbench page manage URL state via `useSearchParams` + `useRouter` (already done at L46–53)
3. Workspace pages will bypass the workbench store entirely — they use `useTrip(tripId)` for server state loaded by the workspace layout

---

## 4. Target Navigation (v1)

```
OPERATE
  Inbox         /inbox          ← default landing (urgency-sorted queue)
  Trips         /workspace      ← listing of active trip workspaces
  Overview      /               ← stats dashboard (secondary)

GOVERN
  Reviews       /owner/reviews
  Insights      /owner/insights

TOOLS
  Audit Bench   /workbench      ← power tool for fixture runs, QA, inspection
```

---

## 5. What to Keep Exactly As-Is

| Item | Why keep |
|---|---|
| Shell visual design | Excellent dark theme, token usage correct, keyboard accessible, mobile nav works |
| `globals.css` token system | Comprehensive, WCAG-aware, well-named state/accent/bg tokens |
| `PacketTab.tsx` | Best component in the codebase — clear, feature-complete, good empty state |
| `DecisionTab.tsx` | Good after the typo fix |
| `StrategyTab.tsx` | Internal vs traveller-safe split view is the right UI concept |
| Inbox card grammar | Dense but readable; priority badge + SLA badge pattern is right |
| Review card in `owner/reviews` | Good urgency styling, action affordance with expand/collapse is clean |
| `useTrips` / `useTrip` hooks | Well-structured; 300ms loading delay prevents flicker correctly |
| `useSpineRun` hook | Implemented correctly — just needs to be called |
| All BFF API routes | Working: `/api/trips`, `/api/spine/run`, `/api/stats`, `/api/pipeline` |
| `PipelineFlow` component | Good visual for showing stage progression inside workbench |
| `components/ui/*` | All reusable UI primitives — keep |

---

## 6. What to Remove or Defer

| Item | Recommendation |
|---|---|
| `themeStore.ts` variant system | Not wired to any route or component. Annotate as deferred or remove. |
| `lib/url-state.ts` | Check if imported anywhere (grep confirms no consumers) — remove |
| `lib/design-system.ts` nav config | Duplicates Shell.tsx NAV definition. Remove duplicate or consolidate |
| `urlSyncMiddleware` in `workbench.ts` | Redundant with existing `useSearchParams` in page — remove |
| Traveller surface | Build only after workspace shell lands and Output stage is stable |
| Public itinerary-checker funnel | Build last — highest commercial risk, needs stable ops core first |

---

## 7. Work Sequencing

```
NOW  (Wave 1)   Fix 4 href links · Update Shell NAV · 2 files, minimal risk
                → Every inbox card goes somewhere meaningful immediately

WEEK 1  (Wave 2)  Build workspace/[tripId]/layout.tsx + TripContext
                  → Operators can navigate between trip stages with persistent header

WEEK 1-2  (Wave 3)  Extract workbench panels to shared components
                    → Inbox → Trip → Packet/Decision/Strategy all work end-to-end

WEEK 2  (Wave 4)  Wire "Process Trip" via useSpineRun in IntakeTab
                  → Core AI loop is triggerable from the workspace

WEEK 2  (Wave 5-6)  Remove Math.random() · Wire governance hooks · Fix typo
                    → Screens stop lying about data

WEEK 3  (Wave 7)  State model cleanup
                  → Zustand store simplified, workspace uses trip-scoped server state

FUTURE  Traveller surface (/trip/[shareToken]) · Public audit funnel (/itinerary-checker)
```

---

## 8. Complete File Inventory

### Files that change

| File | What changes | Wave |
|---|---|---|
| `components/layouts/Shell.tsx` | NAV array: reorder sections + add TOOLS group | 1 |
| `app/inbox/page.tsx` | L177: href change; L340: remove Math.random() | 1, 5 |
| `app/page.tsx` | L258: href change | 1 |
| `app/owner/reviews/page.tsx` | L287 href; L305 replace MOCK with `useReviews()` | 1, 5 |
| `app/owner/insights/page.tsx` | Replace mock constants with analytics hook calls | 5 |
| `app/workbench/IntakeTab.tsx` | Wire `useSpineRun` to submit handler | 4 |
| `app/workbench/DecisionTab.tsx` | Remove typo key L9 | 6 |
| `stores/workbench.ts` | Remove `UrlSyncState` and `urlSyncMiddleware` | 7 |
| `lib/url-state.ts` | Delete if unused | 7 |
| `lib/design-system.ts` | Consolidate or delete duplicate NAV config | 7 |
| `stores/themeStore.ts` | Annotate as deferred or delete | 7 |

### Files to create

| File | Purpose | Wave |
|---|---|---|
| `app/workspace/[tripId]/layout.tsx` | Shared trip workspace shell | 2 |
| `contexts/TripContext.tsx` | Trip data context for workspace children | 2 |
| `app/workspace/page.tsx` | Trip listing page at `/workspace` | 1 |
| `components/panels/PacketPanel.tsx` | Extracted from PacketTab | 3 |
| `components/panels/DecisionPanel.tsx` | Extracted from DecisionTab | 3 |
| `components/panels/StrategyPanel.tsx` | Extracted from StrategyTab | 3 |
| `components/panels/SafetyPanel.tsx` | Extracted from SafetyTab | 3 |
| `app/workspace/[tripId]/intake/page.tsx` | Replace stub | 3 |
| `app/workspace/[tripId]/packet/page.tsx` | Replace stub using PacketPanel | 3 |
| `app/workspace/[tripId]/decision/page.tsx` | Replace stub using DecisionPanel | 3 |
| `app/workspace/[tripId]/strategy/page.tsx` | Replace stub using StrategyPanel | 3 |
| `app/workspace/[tripId]/output/page.tsx` | Replace stub; render traveller bundle | 3 |
| `app/workspace/[tripId]/safety/page.tsx` | Replace stub using SafetyPanel | 3 |

### Files that stay untouched

- `globals.css` — token system is solid
- `app/layout.tsx` — root layout fine for now
- `hooks/useTrips.ts` — correct
- `hooks/useSpineRun.ts` — correct, just needs usage  
- `hooks/useGovernance.ts` — correct
- `lib/api-client.ts` — stable
- `lib/governance-api.ts` — stable
- `app/workbench/PacketTab.tsx` — best screen, keep
- `app/workbench/StrategyTab.tsx` — good, keep
- `app/workbench/SafetyTab.tsx` — keep
- `app/workbench/WorkbenchTab.tsx` — keep
- `app/workbench/PipelineFlow.tsx` — keep
- `app/workbench/page.tsx` — keep (becomes audit surface)
- `components/ui/*` — keep all
- All BFF routes under `app/api/` — keep all

---

## 9. Open Questions

1. **Auth / role model**: Should Shell nav differ by role (owner vs. agent vs. solo), or is v1 flat — everyone sees the same nav with different defaults?

2. **`/workspace` listing page**: Should it show only trips that have been processed (have a packet/decision), or all trips from the inbox? Or redirect to `/inbox` temporarily?

3. **`/workbench` URL**: Rename to `/audit` in the URL, or keep `/workbench` and just relabel it "Audit Workbench" in the nav?

4. **Right-rail AI panel**: Freeform Q&A only, or structured modes (Explain · Draft · Diff)? Affects how much context needs to be passed.

---

*Document written 2026-04-16. Next review after Wave 2 (workspace layout) is complete.*
