# Traceability Implementation Plan: The Decision Timeline

**Date**: Wednesday, April 22, 2026
**Priority**: Critical (P0-02)
**Goal**: Connect the "Black Box" (AuditStore) to the "Cockpit" (Frontend Workspace) to enable operational auditability.

---

## 1. Backend: The Event Stream (API)

### Step 1: Create Timeline Endpoint
We need a unified view that merges historical audit logs with current state transitions.
- **File**: `spine-api/server.py`
- **Logic**: 
  - `GET /api/trips/{tripId}/timeline`
  - Merge: `AuditStore.get_events(tripId)` + Current `Spine` execution state.
  - Returns: `{ "events": [ { "timestamp", "stage", "description", "actor", "deltas" }, ... ] }`

### Step 2: Instrument the Spine
- **File**: `src/intake/orchestration.py`
- **Logic**: Inject `AuditStore.log_event` calls inside `run_spine_once`.
- **Trigger**: Every stage transition (`Intake` -> `Packet` -> `Decision` -> `Strategy` -> `Output`).
- **Data**: Log the `CanonicalPacket` delta at each stage.

---

## 2. Frontend: The Visual Timeline

### Step 3: UI Component (Right Rail)
- **File**: `frontend/src/components/workspace/panels/TimelinePanel.tsx`
- **Logic**: 
  - `fetch('/api/trips/[id]/timeline')`
  - Render a vertical "Event Stream" (a common pattern for audit logs).
  - Use color-coding: `System` (Blue), `Operator` (Green), `Anomaly/Warning` (Red).

---

## 3. Implementation Workflow

1.  **Orchestration Logging**: Modify the spine to ensure every run is an "event" in the timeline.
2.  **API Expansion**: Expose the timeline via the server.
3.  **Visualization**: Build the `TimelinePanel` and attach it to the `Workspace` Right Rail.

---

## 4. Verification & Testing

- **Scenario Test**: Run the "Elderly Pilgrimage" fixture via `test_02_comprehensive.py`.
- **Validation**: Verify that the generated log contains the `medical_needs` capture event.
- **Visual Audit**: Verify that the `TimelinePanel` correctly renders this event in the UI (or API JSON response, before the UI is built).

---

## 5. Next Action
I will now start by implementing the **Timeline Endpoint** and the **Orchestrator Logging** logic.

**Does this sequence—Backend Logging -> API Exposure -> Frontend Visualization—make sense as our roadmap to fixing the "State Blindness"?**
