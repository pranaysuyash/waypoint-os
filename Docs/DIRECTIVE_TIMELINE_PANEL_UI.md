# Implementation Directive: Decision Timeline Rail (P0-02) - UPDATED

**Status**: Active / Priority: Critical
**To**: Implementation Agent
**Objective**: Final assembly of the "Decision Cockpit"—replace the static placeholder in the Right Rail with the new `TimelinePanel`.

---

## 1. Technical Requirements

### A. API Integration
- **Source**: `GET /api/trips/{tripId}/timeline`
- **Polling Strategy**: Initialize fetch on mount. Implement basic polling or socket integration (if available) for real-time updates.

### B. UI Component (Right Rail)
- **Component**: `frontend/src/components/workspace/panels/TimelinePanel.tsx`
- **Design Pattern**: Vertical Event Stream.
- **Scroll Behavior (CRITICAL)**: The panel MUST be height-constrained (`overflow-y-auto`, `h-full`) so that it scrolls independently of the main workspace. Do not let the timeline scroll the entire page.
- **Visuals**:
  - **Color-Coding**: 
    - `System` (e.g., `INTAKE`, `PACKET`, `DECISION`) = Blue badge.
    - `Operator` (Overrides) = Green badge.
    - `Anomaly` (Suitability flags) = Red badge.
  - **Density**: Compact mode by default.
  - **Interaction**: Clicking an event must log intent to update the main workspace view to the packet state at that timestamp.
- **Resizability**: If possible, add a subtle resizer handle/boundary to allow the user to expand the Right Rail for better readability of JSON state.

### C. Data Mapping
- Map the schema from `src/intake/orchestration.py` (`stage`, `state`, `reason`, `confidence`) into a readable timeline card.
- **Evidence Linkage**: If `decision_type` exists, render a link to open the `Provenance Sidebar` (to be built next).

---

## 2. Success Criteria (Verification)
1. **Functional Audit**: Load the "Elderly Pilgrimage" scenario. The `TimelinePanel` must display the Intake transition, the Decision stage, and the Suitability warning.
2. **Operational Verification**: An operator can identify *exactly when* a trip transitioned from "Intake" to "Packet" and *why* the decision engine arrived at its verdict.
3. **No Modal Fatigue**: Ensure this panel is an "Opt-in" right rail; it must not steal focus from the primary workspace.
4. **Independent Scrolling**: Verify the Right Rail scrolls while the main Workbench stays fixed.

---

## 3. Implementation Constraints
- **Additive Only**: Do not modify existing `Workspace` layout logic unless necessary to render the right-rail side-by-side.
- **Error Handling**: Fail gracefully if the API returns an empty timeline (show "No history available").
- **Styling**: Must match the current `[#0f1115]` workspace background and design system tokens.
- **Architecture**: The component must be ready to trigger a `WorkbenchStore` state rehydration in the next iteration.
