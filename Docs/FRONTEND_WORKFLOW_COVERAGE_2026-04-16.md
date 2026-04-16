# Frontend Workflow Coverage Baseline

**Date:** 2026-04-16
**Status:** Baseline documented (read-only analysis; no implementation changes in this document)
**Purpose:** Capture current frontend workflow coverage vs `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md` and identify gaps by product surface.

---

## Scope and Evidence Sources

This baseline is derived from direct route/component inspection in `frontend/src/app/**` and `frontend/src/components/**`, plus comparison with the full frontend product spec.

Primary references:
- `Docs/FRONTEND_PRODUCT_SPEC_FULL_2026-04-15.md`
- `frontend/src/components/layouts/Shell.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/inbox/page.tsx`
- `frontend/src/app/workbench/page.tsx`
- `frontend/src/app/workbench/IntakeTab.tsx`
- `frontend/src/app/workbench/PacketTab.tsx`
- `frontend/src/app/workbench/DecisionTab.tsx`
- `frontend/src/app/owner/reviews/page.tsx`
- `frontend/src/app/owner/insights/page.tsx`
- `frontend/src/app/workspace/[tripId]/*/page.tsx`
- `frontend/src/app/api/**/route.ts`

---

## What Exists (Route Map)

| Route | Component | Depth |
|---|---|---|
| `/` | `page.tsx` (Dashboard) | ✅ Full — stat cards, pipeline summary, activity/recent trips |
| `/inbox` | `inbox/page.tsx` | ✅ Full — trip cards, state badges, filters |
| `/workbench` | `workbench/page.tsx` + tab components | ✅ Substantial — tabs, stage flow, process action, store-backed tab content |
| `/owner/reviews` | `owner/reviews/page.tsx` | ⚠️ Stub — placeholder view only |
| `/owner/insights` | `owner/insights/page.tsx` | ⚠️ Stub — placeholder view only |
| `/workspace/[tripId]/intake` | `workspace/.../intake/page.tsx` | ⚠️ Stub — placeholder only |
| `/workspace/[tripId]/packet` | `workspace/.../packet/page.tsx` | ⚠️ Stub — placeholder only |
| `/workspace/[tripId]/decision` | `workspace/.../decision/page.tsx` | ⚠️ Stub — placeholder only |
| `/workspace/[tripId]/strategy` | `workspace/.../strategy/page.tsx` | ⚠️ Stub — placeholder only |
| `/workspace/[tripId]/safety` | `workspace/.../safety/page.tsx` | ⚠️ Stub — placeholder only |
| `/workspace/[tripId]/output` | `workspace/.../output/page.tsx` | ⚠️ Stub — placeholder only |

Also present (BFF layer): API routes for `/api/trips`, `/api/scenarios`, `/api/spine/run`, `/api/pipeline`, `/api/stats` (plus trip/scenario detail routes).

---

## Coverage by Spec Surface

### Surface A — Internal Intelligence Workbench
**Status:** ✅ ~60% implemented

Implemented:
- Workbench route and tab architecture
- Intake tab with scenario/stage/mode controls + note capture
- Packet tab with facts/signals/ambiguities/unknowns/contradictions and raw JSON toggle
- Decision tab with state, rationale, blockers, and follow-up structures
- Stage flow visualization and processing action

Not yet implemented:
- Flow Simulation mode (explicit)
- Fixture compare workflow
- Scenario replay against persisted outputs

---

### Surface B — Agency Operator App
**Status:** ⚠️ ~20% implemented

Implemented:
- Lead Inbox (`/inbox`) with triage UX

Missing or incomplete:
- Intake Workspace (`/workspace/[tripId]/intake`) is placeholder only
- Decision & Clarification route exists but placeholder only
- Quote/Option Builder route not present
- Booking Readiness route not present
- Change Requests & Recovery route not present
- Conversation Timeline route not present

Critical gap:
- Inbox cards currently route into `/workbench` (not trip-scoped workspace flow).
- No `/workspace/[tripId]` shell/layout route orchestration is currently established.

---

### Surface C — Agency Owner Console
**Status:** ⚠️ ~10% implemented

Implemented:
- Route scaffolding for reviews and insights

Missing or incomplete:
- `/owner/reviews` is placeholder only
- `/owner/insights` is placeholder only
- Margin policy governance module not implemented
- Team productivity/SLA module not implemented
- Exception/escalation center not implemented

---

### Surface D — Traveler-Facing Experience
**Status:** ❌ ~5% implemented

Implemented:
- `/workspace/[tripId]/output` route exists as placeholder

Missing:
- Clarification response view
- Trip plan timeline
- Change request flow
- Status/confidence communication views

---

### Surface E — Public Acquisition Layer
**Status:** ❌ 0% implemented

Missing:
- Itinerary checker funnel route(s)
- SEO landing routes
- “Fix this plan” conversion flow

---

## Navigation Coverage Gap

`frontend/src/components/layouts/Shell.tsx` currently exposes 5 internal destinations:
- Overview
- New Leads (Inbox)
- Trip Pipeline (Workbench)
- Pending Reviews
- Analytics

Spec top-level IA calls for broader internal nav including:
- Inbox
- Workspaces
- Proposals
- Trips in Progress
- Insights
- Settings

Gap summary:
- Workspaces/Proposals/Trips in Progress/Settings are not represented in shell nav.
- Secondary workspace context nav (Intake/Packet/Decision/Strategy/Output/Activity/Safety) is not exposed at shell level.

---

## Summary Judgment

| Surface | Built | Gap Type |
|---|---|---|
| A: Internal Workbench | ✅ ~60% | Flow simulation + replay/compare workflows missing |
| B: Operator App | ⚠️ ~20% | Trip-scoped workspace remains mostly scaffold |
| C: Owner Console | ⚠️ ~10% | Routes exist but content is mostly placeholder |
| D: Traveler-Facing | ❌ ~5% | Output placeholder only |
| E: Public Layer | ❌ 0% | Entirely unimplemented |

Overall baseline:
- The strongest implemented area is the internal workbench + API/BFF foundation.
- The largest product risk is incomplete trip-scoped operator workflow and absent traveler/public surfaces.

---

## Recommended Sequencing (Documentation-Only Recommendation)

1. Wire Inbox → trip-scoped workspace shell (`/workspace/[tripId]/*`).
2. Build trip intake workspace (left/center/right operational layout).
3. Reuse/adapt workbench tab logic into trip-scoped pages.
4. Flesh out owner review and insight screens.
5. Implement public acquisition surface after internal ops workflow is stable.

---

## Notes

This file intentionally documents coverage status only. It does not modify implementation scope, code ownership boundaries, or release commitments.
