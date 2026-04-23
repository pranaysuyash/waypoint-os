# Implementation Directive: Assemble Decision Timeline Rail (P0-02)

**Status**: Active / Priority: Critical
**To**: Implementation Agent
**Objective**: Final assembly of the "Decision Cockpit"—inject `TimelinePanel` into the workspace Right Rail.

---

## 1. Scope of Work
- **Target File**: `frontend/src/app/workspace/[tripId]/layout.tsx`
- **Task**: 
  - Remove the placeholder text "AI Copilot Panel" inside the `aside` tag.
  - Import `TimelinePanel` from `@/components/workspace/panels/TimelinePanel`.
  - Mount `<TimelinePanel tripId={tripId as string} />` inside the aside.

## 2. Technical Requirements
- **Independent Scrolling**: Ensure the `aside` container has `h-full overflow-y-auto`. It must not be part of the main page scroll.
- **Error Boundaries**: Wrap the `TimelinePanel` in the existing `<ErrorBoundary />`.
- **Layout Alignment**: Maintain the `grid` structure in `layout.tsx` (ensure the Aside stays to the right of the main content).

## 3. Verification Protocol
1. **Functional**: Verify the timeline appears in the right rail after clicking "Show AI rail".
2. **Scrolling**: Verify the timeline scrolls independently of the main content.
3. **Data Integrity**: Confirm timeline events pull and render correctly.

---

**Directive**: Proceed with assembly. Do not modify global layout logic, just the component injection. Report status immediately upon successful mounting.
