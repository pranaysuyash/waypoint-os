# Waypoint OS — Workbench vs. Trip Workspace Architecture Decision
**Date:** 2026-05-14  
**Branch:** master  
**Status:** Pre-implementation — awaiting user approval before any code changes

---

## Executive Summary

Two surfaces in Waypoint OS — **Workbench** (`/workbench`) and **Trip Workspace** (`/trips/[tripId]/...`) — currently overlap in ownership of the same UX jobs. The strategist audit identifies this as a "competing app models" problem. This document: verifies each premise against real code, documents what the parallel analysis found, presents three alternatives, and recommends the path forward.

**Recommendation: Option B (Disciplined Clarification)** — Move ops access to Trip Workspace, strip workbench back to New Inquiry only, remove dead code, and clean the cross-boundary store read. This delivers the full strategic vision without the irreversibility risk of Option C.

---

## Background — What the Strategist Said

The strategist audit (~10,000 words) argued:

1. Workbench currently serves two jobs: **creation tool** (new inquiry → run Spine → see results) and **trip workspace** (review packet, assess risk, execute ops). These are different user needs with different cadences.
2. Trip Workspace should be the **single durable source of truth** for all trip work once a trip exists.
3. Ops (booking execution, document management, payments) is **operational execution** — it belongs in Trip Workspace, not a transient processing tool.
4. Workbench should become **"New Inquiry" only** — a creation funnel that routes to Trip Workspace on completion.

---

## Premises — Verified Against Code

### P1: Workbench and Trip Workspace have competing ownership of the same UX jobs
**VERIFIED.**

Workbench has four tabs:
```
[{id:'intake', label:'New Inquiry'}, {id:'packet', label:'Trip Details'}, 
 {id:'safety', label:'Risk Review'}, {id:'ops', label:'Ops'}]
```

Trip Workspace has seven tabs: Intake, Trip Details, Options, Quote Assessment, Output, Risk Review, Timeline.

The "Trip Details" and "Risk Review" jobs are claimed by both. The shell's `getPageLabel()` call already acknowledges this tension — it hides the word "Workbench" entirely and labels the route "New Inquiry" in the breadcrumb (`Shell.tsx:141`). The nav doc (`nav-modules.ts`) explicitly states `/workbench` is not a durable module name.

**Evidence:**
- `frontend/src/components/layouts/Shell.tsx:141` — `if (pathname === '/workbench') return 'New Inquiry';`
- `frontend/src/lib/nav-modules.ts` — "Actions like 'New Inquiry' do not belong in NAV_SECTIONS; they should live as shell CTAs."
- `frontend/src/app/(agency)/workbench/PageClient.tsx:69-74` — workspaceTabs includes packet + safety

### P2: Ops belongs in Trip Workspace because it's operational execution
**PARTIALLY VERIFIED — disputed by architecture docs, resolved by Feature #7.**

The strategist argument is architecturally correct: booking execution, document management, and payment tracking are long-running operational tasks tied to a trip record. They have nothing to do with the ephemeral Spine processing session.

However, architecture docs (Phase 4F, 5A) explicitly placed Ops in Workbench as the "individual operator analysis tool." The design rationale: Workbench = single-operator, ephemeral; Trip Workspace = collaborative, durable.

The resolution is Feature #7 "Booking Execution Master Record" — documented in existing project docs as the future path for bringing Ops-like functionality into Trip Workspace as a trip-level panel aggregating booking tasks, confirmations, documents, and extraction status. **Moving Ops to Trip Workspace is not a rogue idea — it is the documented future state, and implementing it now accelerates the roadmap rather than contradicting it.**

The key practical gap: `OpsPanel.tsx` (1404 lines) reads `result_validation` from `useWorkbenchStore` to assess trip readiness. That's a workbench-coupling that must be severed or replaced before the panel can live in Trip Workspace cleanly.

### P3: DecisionTab and StrategyTab are dead code safe to remove
**VERIFIED.**

`frontend/src/app/(agency)/workbench/PageClient.tsx:46-47`:
```typescript
const DecisionTab = dynamic(() => import('./DecisionTab'))
const StrategyTab = dynamic(() => import('./StrategyTab'))
```

Neither is rendered anywhere in the JSX (confirmed by searching the full 1148-line file). The render switch only handles: OpsPanel, SafetyTab, PacketTab, IntakeTab. These are dead imports that increase bundle parse overhead and cause confusion for future readers.

### P4: The cross-boundary `useWorkbenchStore` read in `layout.tsx` is an architectural smell
**VERIFIED.**

`frontend/src/app/(agency)/trips/[tripId]/layout.tsx:103`:
```typescript
const { result_run_ts } = useWorkbenchStore();
```

This is imported inside the Trip Workspace layout — a durable per-trip surface — to display "Last processed" timestamp. This is wrong because:
1. `result_run_ts` is transient Workbench session state that survives only in browser memory until the store resets.
2. If the user navigates directly to a trip URL (bookmark, shared link, fresh session), `result_run_ts` is undefined.
3. It creates a hard module dependency: Trip Workspace cannot be extracted or independently rendered without pulling in the entire workbench store.

The correct fix: store `last_processed_at` on the Trip record itself (it likely already exists as a `spine_updated_at` or similar field on the API response). If not, add it to the trip API response and read from `TripContext`.

### P5: Workbench should be scoped to "New Inquiry" creation only
**PARTIALLY SUPPORTED — requires intent verification.**

The shell nav and breadcrumb system already treats Workbench as "New Inquiry." The sidebar CTA links to `/workbench?draft=new&tab=intake`, not just `/workbench`. The nav doc says workbench is not a durable module name.

However, the current `useHydrateStoreFromTrip()` hook allows any existing trip to be re-opened in Workbench (e.g., to re-run Spine on existing data). This is a legitimate workflow — an operator may want to re-process a trip through the AI pipeline without losing the existing trip record. Restricting Workbench to truly new drafts only would break this workflow.

**Modified P5:** Workbench should be scoped to "creation and AI processing" — creating new inquiries AND re-running Spine on existing trips. Post-completion navigation should always route to Trip Workspace. The "Ops" and "Trip Details (read-only view)" tabs should not exist in Workbench.

---

## Findings from Parallel Agent Analysis

### Agent 1: Architecture & State Analysis
Key findings:
- **Store coupling is the primary risk.** `OpsPanel.tsx` has direct `useWorkbenchStore` calls for `result_validation` (readiness check). Moving the panel requires either: (a) replacing the validation read with a trip-API-derived readiness signal, or (b) passing it as a prop.
- **`acknowledged_suitability_flags`** is session-local in workbench store — it tracks per-run acknowledgment of AI-flagged suitability issues. This state is ephemeral by design and should NOT be moved to Trip Workspace store.
- **Phase 1L migration comments** in `routes.ts` indicate redirects from trip stage pages to workbench are intended to be removed in Phase 2+. The cleanup is overdue.
- **`completedTripId` flow** is clean — after a run, `push(\`/trips/${completedTripId}/intake\`)` routes correctly to Trip Workspace. The handoff already works; it's just that Ops never got its own Trip Workspace home.

### Agent 2: UI/UX Navigation Analysis
Key findings:
- **No user-visible entry point to `/trips/[tripId]/ops/`** exists because the page doesn't exist. Users who've completed a Spine run see "View Trip" → `/trips/.../intake` then have to go back to Workbench to do Ops work.
- **The Ops tab in Workbench shows based on trip stage** (`showOps` = `trip?.stage === 'proposal' || trip?.stage === 'booking'`). This is correct stage-gating logic that should be preserved when the tab moves.
- **Trip Workspace stage tabs are already gated** via `canAccessPlanningStage()`. Adding an "Ops" tab that's only shown when `trip.stage === 'proposal' || 'booking'` is consistent with existing patterns.
- **Dead imports (P3)** confirmed by two independent reads of PageClient.tsx.

---

## Three Alternatives

### Option A — Minimal Safe Fix
**Scope:** Add Ops tab to Trip Workspace; remove dead imports. Workbench keeps its Ops tab.

Changes:
1. Add `{id: "ops", label: "Ops"}` to `STAGE_TABS` in `trips/[tripId]/layout.tsx`
2. Create `frontend/src/app/(agency)/trips/[tripId]/ops/page.tsx` + `PageClient.tsx` rendering `OpsPanel`
3. Add stage-gate: only show ops tab when `trip.stage === 'proposal' || 'booking'`
4. Remove `DecisionTab` and `StrategyTab` dead imports from Workbench `PageClient.tsx`

**Pros:** Lowest risk, non-breaking, additive only.  
**Cons:** Leaves workbench with competing Ops tab; doesn't resolve dual ownership; doesn't clean cross-boundary store read.

---

### Option B — Disciplined Clarification (RECOMMENDED)
**Scope:** Option A + remove Ops from Workbench + clean cross-boundary store read.

Changes (beyond Option A):
5. Remove `ops` from `workspaceTabs` in Workbench `PageClient.tsx`; remove `showOps` logic and OpsPanel render in Workbench
6. Fix `trips/[tripId]/layout.tsx:103` — replace `useWorkbenchStore` read of `result_run_ts` with trip API field (add `last_processed_at` to trip response if needed, or read from `trip.updated_at` as proxy)
7. Update OpsPanel to not read `result_validation` from workbench store — either accept it as a prop (from trip-level API readiness data) or remove the workbench-coupled readiness check and replace with trip-stage-based logic

**Pros:** Resolves dual ownership cleanly; Workbench = creation + AI processing; Trip Workspace = durable trip record; clean module boundary; no dead code.  
**Cons:** Requires touching OpsPanel's store reads (moderate risk); requires trip API change for `last_processed_at`.

---

### Option C — Full Strategist Vision
**Scope:** Option B + redirect any existing-trip Workbench session to Trip Workspace; extract shared processing controller hook.

Changes (beyond Option B):
8. When `useHydrateStoreFromTrip` loads an existing trip in Workbench, detect completed trips (`trip.stage !== 'draft'`) and redirect to `/trips/${tripId}/intake`
9. Extract a `useSpineProcessing` controller hook that can be used from Trip Workspace to re-run Spine without requiring the user to navigate back to Workbench
10. Phase out the Workbench Spine trigger as a standalone route (long-term; keep as fallback)

**Pros:** Purest architecture; complete strategic vision.  
**Cons:** Operators currently use Workbench to re-process trips — hard redirect would break that workflow until the re-run affordance exists in Trip Workspace. High risk of regression without thorough QA. This is a Phase 3+ item.

---

## Recommendation

**Implement Option B.** It delivers the strategic goal (single durable source of truth = Trip Workspace) without the re-run workflow regression risk of Option C. Option C's "redirect existing trips" work should be deferred until a Trip Workspace re-run affordance is built.

**Implementation order within Option B:**

1. **Remove dead imports** (P3) — zero-risk cleanup, ship first.
2. **Add Ops to Trip Workspace** — additive, low risk.
3. **Fix cross-boundary store read** (P4) — moderate complexity; need to confirm `last_processed_at` field availability on trip API response.
4. **Fix OpsPanel store coupling** — de-couple `result_validation` read; use trip-stage or trip-API readiness.
5. **Remove Ops from Workbench** — once Trip Workspace Ops is confirmed working.

Each step is independently releasable and verifiable. Do not do steps 4+5 in the same deploy as step 2 until OpsPanel is verified working in Trip Workspace.

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|-----------|
| OpsPanel breaks when decoupled from workbench store | High | Verify `result_validation` usage; replace with trip-stage gate before removing |
| `last_processed_at` not in trip API response | Medium | Check `spine_api/contract.py`; add field or use `updated_at` as proxy |
| Operators lose Ops access mid-session if redirect added prematurely | High | Do NOT add redirect (Option C) until re-run affordance exists in Trip Workspace |
| Phase 1L redirect cleanup breaks navigation | Medium | Test with direct URL navigation to each trip stage after cleanup |
| `acknowledged_suitability_flags` session state lost | Low | This is intentionally ephemeral; confirm with UX that re-acknowledgment per session is acceptable |

---

## Files Affected (Option B)

| File | Change |
|------|--------|
| `frontend/src/app/(agency)/workbench/PageClient.tsx` | Remove `DecisionTab`/`StrategyTab` dead imports; remove `showOps`, OpsPanel render; remove `ops` from `workspaceTabs` |
| `frontend/src/app/(agency)/trips/[tripId]/layout.tsx` | Add `ops` to STAGE_TABS with stage-gate visibility; fix `useWorkbenchStore` import → trip API field |
| `frontend/src/app/(agency)/trips/[tripId]/ops/page.tsx` | Create new page (Next.js shell) |
| `frontend/src/app/(agency)/trips/[tripId]/ops/PageClient.tsx` | Create; renders OpsPanel with trip context |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | De-couple `result_validation` read from workbench store |
| `frontend/src/lib/routes.ts` | Add `'ops'` to `WorkspaceStage` type |
| `spine_api/contract.py` | Confirm / add `last_processed_at` field to trip response (if missing) |

---

## Open Questions (Require Verification Before Implementation)

1. Does `spine_api/contract.py` expose `last_processed_at` or equivalent on the trip response? If not, what field should the Trip Workspace layout display for "last processed"?
2. Does OpsPanel's `result_validation` use (for readiness assessment) gate any user-visible UI that operators depend on? What happens if we replace it with `trip.stage >= 'proposal'`?
3. Are there any deep-link URLs in use (emails, shared links) that point to `/workbench?tab=ops&tripId=...`? These would break if Workbench drops the ops tab.
4. Phase 1L redirect comments in `routes.ts` — is the Phase 2 cleanup now safe to do alongside this work?
