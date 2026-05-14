# Workbench Deferred Tabs Inventory
**Date:** 2026-05-14  
**Status:** Imports removed from PageClient.tsx — files retained pending product decision

---

## DecisionTab.tsx

**Path:** `frontend/src/app/(agency)/workbench/DecisionTab.tsx`  
**Lines:** 446  
**Last commit:** `1644c4d` — "Commit remaining frontend, backend, docs, and service router updates after targeted data tracking review"  

### What logic exists inside

- Full `STATE_BADGE_CLASS` lookup table mapping trip/result state values to visual badge classes
- Suitability flag acknowledgment UI — operators confirm they have reviewed AI-flagged suitability issues before proceeding
- Budget breakdown rendering — itemized cost display with fee calculation results
- Follow-up question handling — display and capture of AI-generated follow-up questions from the Spine pipeline
- Decision output rendering — structured display of AI decision rationale

### Is logic duplicated elsewhere

Partially. The suitability acknowledgment concept appears in `ReviewControls` and the workbench store (`acknowledged_suitability_flags`). Budget/fee display appears in parts of PacketTab. However, the full composition in DecisionTab is not fully replicated in any current rendered path.

### Why the import was removed

The tab is imported in `PageClient.tsx` but never appears in the `workspaceTabs` array or the render switch. It was built during an earlier iteration of the Workbench tab model and removed from the tab list without deleting the file. The dynamic import adds bundle overhead without providing any rendered output.

### Action taken

Import `const DecisionTab = dynamic(() => import('./DecisionTab'))` removed from Workbench `PageClient.tsx`.  
**File retained.**

### Follow-up decision required

- Does the budget breakdown / decision rationale logic belong in Trip Workspace Quote Assessment tab?
- Does the suitability acknowledgment flow need to be surfaced elsewhere in Trip Workspace?
- Can this file be archived (moved to `_archived/`) or should it be reintegrated?

---

## StrategyTab.tsx

**Path:** `frontend/src/app/(agency)/workbench/StrategyTab.tsx`  
**Lines:** 106  
**Last commit:** `1644c4d` — "Commit remaining frontend, backend, docs, and service router updates after targeted data tracking review"  
Also: `c8a0095` — "fix: remove Build Options -> Intake loop on StrategyPage, replace with honest disabled state"

### What logic exists inside

- Options/strategy display component (106 lines)
- Was the "Build Options" / strategy generation panel
- `c8a0095` commit removed a feedback loop (Build Options → Intake) and replaced with a disabled state — this was explicitly fixed, suggesting the component was actively maintained before being removed from the tab list

### Is logic duplicated elsewhere

The Trip Workspace has a `/trips/[tripId]/strategy` page (Options tab). Some of StrategyTab's logic may overlap. Needs review before any reintegration.

### Action taken

Import `const StrategyTab = dynamic(() => import('./StrategyTab'))` removed from Workbench `PageClient.tsx`.  
**File retained.**

### Follow-up decision required

- Does this overlap entirely with the Trip Workspace `/strategy` (Options) tab?
- Is any logic here unique or needed?
- If fully superseded, mark for archive.
