# Frontend Wave 1L + 6H — Implementation Notes
**Date**: 2026-04-18  
**Branch**: feature/wave-1l-6h (merge to main after review)  
**Parent doc**: `FRONTEND_IMPROVEMENT_PLAN_2026-04-16.md`

---

## What Was Shipped

### Wave 1L — Long-term-safe routing migration

**Not Wave 1 exact** (which would have been a functional downgrade — routing users into stub pages).  
Instead: canonical URLs are locked in now; workbench remains fully functional via a server-side redirect layer.

#### `frontend/src/lib/routes.ts` — NEW
Single source of truth for trip navigation. Two exported functions:
- `getTripRoute(tripId, stage?)` — canonical URL; use everywhere in UI code
- `_getWorkbenchCompatRoute(tripId, stage?)` — internal, used only by compat redirects; prefixed `_` to signal intent

Also exports `WorkspaceStage`, `WorkbenchTab` types and `WORKSPACE_TO_WORKBENCH_TAB` mapping.

**Rule going forward**: no inline `/workspace/${id}/...` or `/workbench?trip=...` strings in UI code. All routing through `getTripRoute`.

#### `frontend/src/components/layouts/Shell.tsx` — MODIFIED
NAV restructured:
- `[OPERATE]`: Inbox (default) → Workspaces (`/workspace`) → Overview
- `[GOVERN]`: unchanged
- `[TOOLS]` (new group): Workbench (power tool / audit surface)

Added `Layers`, `Wrench` imports from lucide-react. Removed `Briefcase` from OPERATE (Workbench no longer top-level work destination).

#### `frontend/src/app/inbox/page.tsx` — MODIFIED
- L177: `href={getTripRoute(trip.id)}` (was `/workbench?trip=${trip.id}`)

#### `frontend/src/app/page.tsx` — MODIFIED
- L259: `href={getTripRoute(item.id)}` (was `/workbench?trip=${item.id}`)

#### `frontend/src/app/owner/reviews/page.tsx` — MODIFIED
- L288: `href={getTripRoute(review.tripId)}` (was `/workbench?trip=${review.tripId}`)

#### `frontend/src/app/workspace/[tripId]/*/page.tsx` — ALL 6 REPLACED
All 6 stage pages (intake, packet, decision, strategy, output, safety) now server-redirect to the workbench compat layer via `_getWorkbenchCompatRoute`. Users get the full workbench functionality immediately at the canonical URL.

**When to remove these redirects**: After Wave 2 (workspace layout) + Wave 3 (panel extraction) are complete. Each file has a doc comment marking the removal condition.

`output` stage → maps to workbench `strategy` tab (closest pre-Wave-3 equivalent).

#### `frontend/src/app/workspace/page.tsx` — NEW
Workspace listing page at `/workspace`. Key design choices:
- Domain boundary is an **explicit constant**, not ad-hoc inline filter:
  ```ts
  const IN_WORKSPACE_STATES = new Set(['green', 'amber', 'red']);
  ```
- Empty state cross-links to Inbox with clear explanation of the domain split
- Blocked trip count surfaced in header
- All cards link via `getTripRoute`

---

### Wave 6H — DecisionTab state normalization (hardened)

**Not a one-line deletion** (which would have been risky if old API responses still emit the typo).  
Instead: proper alias layer + unknown-state fallback.

#### `frontend/src/app/workbench/DecisionTab.tsx` — MODIFIED

Three changes:

1. **`STATE_BADGE_CLASS`** — cleaned to canonical spellings only (no typo keys)

2. **`STATE_ALIASES`** — new map of known typo/variant → canonical
   ```ts
   const STATE_ALIASES = {
     PROCEED_TRAVERER_SAFE: 'PROCEED_TRAVELER_SAFE', // double-r (pre-hardening)
   };
   ```
   Add here when new variants are discovered. Never add to `STATE_BADGE_CLASS` directly.

3. **`normalizeDecisionState(raw)`** — normalizes before lookup; returns original string if no alias, so unknown states hit the `?? styles.stateBlue` fallback visibly (not silently unstyled)

Badge render now uses pre-computed `badgeClass` variable:
```tsx
const badgeClass = STATE_BADGE_CLASS[decisionState] ?? styles.stateBlue;
// ...
<span className={`${styles.badge} ${badgeClass}`}>
```

---

## What Was Not Changed

- `globals.css` — untouched
- `app/layout.tsx` — untouched
- All `hooks/` — untouched
- All `lib/api-client.ts`, `governance-api.ts` — untouched  
- All `app/api/` BFF routes — untouched
- All `app/workbench/` panels (PacketTab, StrategyTab, SafetyTab, WorkbenchTab, PipelineFlow) — untouched
- `app/workbench/page.tsx` — untouched (becomes audit surface)
- `components/ui/*` — untouched

---

## Zero Functional Downgrade Verification

| User action | Before | After |
|---|---|---|
| Click inbox card | → `/workbench?trip=X` (workbench) | → `/workspace/X/intake` → redirect → `/workbench?trip=X&tab=intake` (workbench) |
| Click overview activity row | → `/workbench?trip=X` | → same redirect chain |
| Click "View Details" in reviews | → `/workbench?trip=X` | → same redirect chain |
| Navigate to Workbench in nav | → `/workbench` (OPERATE section) | → `/workbench` (TOOLS section) |
| Navigate to "Inbox" | same | same |
| Visit `/workspace` | 404 | New listing page |

End user lands in the same workbench screen in all cases. URL changes, capability does not.

---

## Next Steps (Wave 2)

Open questions to resolve before Wave 2 starts:
1. Right-rail AI panel in workspace layout — toggleable collapsed default, or skip for Wave 2?
2. Role-based nav (owner vs. agent) — flat for v1 or differentiated?

Wave 2 work:
- `app/workspace/[tripId]/layout.tsx` — shared trip header, stage tabs, optional right-rail
- `contexts/TripContext.tsx` — trip data context shared across stage children
- Once layout is done: remove compat redirects from stage pages, replace with real panels (Wave 3)
