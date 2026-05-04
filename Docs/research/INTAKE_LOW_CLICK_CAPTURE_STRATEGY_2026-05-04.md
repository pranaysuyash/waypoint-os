# Intake Low-Click Capture Strategy (2026-05-04)

## Objective
Reduce agency-user clicks and mode switches required to capture a new enquiry, while keeping the existing Intake/Workbench surface canonical.

## What Exists Today (Code-Verified)
- `New Inquiry` is an action-level CTA in shell, with `/workbench` as temporary route label mapping (`frontend/src/lib/nav-modules.ts`, `frontend/src/components/layouts/Shell.tsx`).
- Intake has two capture paths:
  - Manual raw/owner note fields + `Process Trip` (`frontend/src/components/workspace/panels/IntakePanel.tsx`).
  - `Capture call notes` button that opens `CaptureCallPanel`, which creates a trip (`createTrip`) (`frontend/src/components/workspace/panels/CaptureCallPanel.tsx`).
- After call-capture save, navigation still takes user into trip flow; processing and planning progression are separate actions.

## Current Friction (Click Cost)
1. User clicks `New Inquiry`.
2. User clicks `Capture call notes`.
3. User fills form.
4. User clicks `Save`.
5. User returns to intake context and still needs to trigger next step (`Process Trip` or planning progression).

This is operationally safe, but not the minimum-step path for fast call capture.

## Proposed Low-Click Model

### Principle
Keep one canonical workflow and reduce interaction overhead by using entry-mode presets and progressive disclosure.

### Flow A (Primary): Phone/Call Fast Capture
1. Click `New Inquiry`.
2. Capture panel opens immediately in "Call" mode (no extra click).
3. Agent pastes/speaks notes + optional fields.
4. Click single primary CTA: `Save and Process`.

### Flow B: Message/Email Fast Capture
1. Click `New Inquiry`.
2. Entry chooser offers `Call`, `WhatsApp/Chat`, `Email`, `Itinerary/PDF`.
3. Selected mode preconfigures fields and prompt copy.
4. Single primary CTA: `Save and Process`.

## UX/Behavior Changes
- Convert hidden secondary action (`Capture call notes`) into default first screen for `New Inquiry`.
- Add "capture mode" at entry, not as deep nested option.
- Merge two actions where safe:
  - current: `Save` then `Process Trip`
  - target: `Save and Process` (with fallback to `Save Draft`).
- Keep optional fields collapsed by default; reveal only when needed.
- Preserve strong validation on mandatory capture text (`raw_note`).

## Implementation Plan (Frontend)

### Phase 1: Entry and Defaults (No Contract Risk)
- Route `New Inquiry` CTA to `/workbench?capture_mode=call&entry=new`.
- Auto-open `CaptureCallPanel` when `entry=new` and no active trip is selected.
- File targets:
  - `frontend/src/components/layouts/Shell.tsx`
  - `frontend/src/components/workspace/panels/IntakePanel.tsx`

### Phase 2: Action Compression
- Add primary CTA in `CaptureCallPanel`: `Save and Process`.
- On submit success:
  - create trip (`POST /api/trips`) then
  - trigger run with existing spine request path (same canonical run route; no duplicate API route).
- Keep secondary CTA: `Save only`.
- File targets:
  - `frontend/src/components/workspace/panels/CaptureCallPanel.tsx`
  - existing run trigger integration point in `IntakePanel.tsx` / `useSpineRun` flow.

### Phase 3: Multi-Channel Presets
- Add capture mode presets (`call`, `chat`, `email`, `itinerary`) that only alter UI hints/defaults and field emphasis.
- Do not fork backend contract by mode.

## Guardrails
- No duplicate route creation.
- No parallel policy/processing stacks.
- All capture modes must map to existing canonical trip creation + run flow.
- Preserve existing workbench/intake as the single operator surface.

## Success Metrics
- Time-to-first-processed-inquiry reduced.
- Clicks from `New Inquiry` to first AI output reduced (target: 5 -> 2/3 interaction steps).
- Lower drop-off between trip creation and first processing run.

## Not Doing (Explicit)
- Not creating a separate standalone "Call Capture app".
- Not replacing existing intake/workbench module.
- Not introducing new duplicate API routes for mode-specific capture.

## Recommended New Goal
Implement Phase 1 + Phase 2 as one cohesive slice: "`New Inquiry` opens fast capture by default and supports one-click `Save and Process` through the existing canonical trip + run pipeline."
