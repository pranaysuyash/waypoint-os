# Frontend Suitability Display Specification

> **SUPERSEDED**: This early draft has been replaced by a comprehensive three-document set dated 2026-04-22:
> - **FRONTEND_SUITABILITY_DISPLAY_STRATEGY_2026-04-22.md** — Full operational/production/agent analysis + 5 strategic takes
> - **SUITABILITY_PRESENTATION_CONTRACT_2026-04-22.md** — Exact data shapes, component spec, implementation phases
> - **AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md** — Override API, persistence, agent learning loop
>
> This file is retained for historical reference only.

## Purpose

This document defines the intended frontend behavior for surfacing activity suitability information in the travel agency workbench.

The goal is to make suitability signals understandable, actionable, and visible to end users without requiring them to parse raw decision risk flags.

## Current implemented state

- Backend suitability scoring exists in `src/suitability/`.
- Suitability integration can emit risk flags through `generate_risk_flags()` in the decision pipeline.
- The frontend currently renders generic `decision.risk_flags` in `frontend/src/components/workspace/panels/DecisionPanel.tsx`.

## What is missing

- No dedicated frontend section explicitly labeled as `Suitability`.
- No activity-level suitability feedback in itinerary or activity cards.
- No dedicated icons, badges, or summary prose for suitability-specific warnings.
- No standardized label mapping for `suitability_*` backend flags.
- No user-facing explanation of why an activity may be unsuitable.

## Frontend contract

### Primary user visible surface

The frontend should expose suitability information in the decision or itinerary review flow with the following elements:

1. **Suitability Summary Card**
   - Location: `DecisionPanel` or a dedicated `SuitabilityPanel` within the workbench.
   - Content:
     - overall suitability verdict (e.g. `Good`, `Caution`, `Risky`)
     - number of suitability warnings
     - key categories (elderly, toddler, mobility, pacing, age restrictions)
     - guidance on next action

2. **Suitability Risk List**
   - Show the actual suitability warnings in a human-friendly format.
   - Prefer label text like:
     - `Activity may be too strenuous for elderly travelers`
     - `Child-friendly activity recommended`
     - `Mobility access not confirmed`
     - `Scheduling may cause fatigue`

3. **Activity-level callouts**
   - If possible, surface suitability warnings near the itinerary or activity item they apply to.
   - This may be a later extension after the dedicated summary card is implemented.

4. **Confidence / diagnostics**
   - Show an optional confidence indicator if the backend includes it.
   - Do not overwhelm the user; keep diagnostic detail collapsible.

### Data expectations

The frontend should be able to consume either:

- `decision.risk_flags` containing `suitability_*` entries, or
- a dedicated `decision.suitability` object with:
  - `summary` string
  - `warnings: string[]`
  - `confidence: number`
  - `details?: { activity_id: string; message: string; severity: string }[]`

For the current implementation, the existing `risk_flags` path is acceptable, but the UI should treat suitability entries as a distinct category where possible.

## Recommended frontend behavior

1. Keep the existing generic `Risk Flags` list in `DecisionPanel` as a fallback.
2. Add a new `Suitability` section directly above or below `Risk Flags`.
3. If a risk flag starts with `suitability_`, render it in the new section rather than in the generic list.
4. If no suitability items are present, do not render the dedicated section.

## Suggested label mapping

The backend should emit flags in a consistent form, for example:

- `suitability_overload_elderly`
- `suitability_pacing_toddler`
- `suitability_accessibility_limit`
- `suitability_age_restriction`
- `suitability_climate_fatigue`

Frontend label examples:

- `This activity is likely too much for elderly travelers.`
- `This activity may be too demanding for toddlers.`
- `Mobility access is uncertain for this activity.`
- `Age restrictions may limit participation.`
- `The itinerary may be too tiring given current pacing.`

## What to explore next

- Should suitability warnings be grouped into `Travelers`, `Accessibility`, and `Pacing` categories?
- Should the UI show activity-level suitability badges inside itinerary cards?
- Should the frontend display a dedicated `Looks good for this group` indicator when no suitability warnings exist?
- Should we add a lightweight `More details` / `Explain why` toggle for each suitability warning?
- How should suitability display interact with owner review flows and the broader decision state?

## Acceptance criteria

- A dedicated suitability display section exists in the workbench UI.
- Suitability-specific backend flags are surfaced separately from generic risk flags.
- The UI uses clear, non-technical language for warnings.
- The design supports future activity-level callouts.
- The corresponding docs are linked from `Docs/INDEX.md` and referenced in the suitability implementation handoff.
