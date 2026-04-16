# Component Adaptation Spec — Design

**Feature Name:** component-adaptation  
**Version:** 1.0.0  
**Date:** 2026-04-16  
**Status:** Design Phase

---

## 1. Component Analysis

### 1.1 Component Inventory

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| IntakeTab | `IntakeTab.tsx` | ~150 | INPUT: Trip selector, message textarea, agent notes, stage/mode dropdowns |
| PacketTab | `PacketTab.tsx` | ~200 | DISPLAY: Shows packet data, facts, ambiguities, contradictions |
| DecisionTab | `DecisionTab.tsx` | ~250 | DISPLAY: Shows decision state, blockers, budget breakdown |
| StrategyTab | `StrategyTab.tsx` | ~180 | DISPLAY: Shows strategy, internal vs traveler bundles |
| SafetyTab | `SafetyTab.tsx` | ~150 | DISPLAY: Shows leakage status, traveler-safe bundle |
| PipelineFlow | `PipelineFlow.tsx` | ~100 | DISPLAY: Visual pipeline representation |
| WorkbenchTab | `WorkbenchTab.tsx` | ~50 | Wrapper component |

### 1.2 Component Classification

| Component | Current Type | Workspace Type | Strategy |
|-----------|-------------|----------------|----------|
| IntakeTab | INPUT | DISPLAY | **Rebuild** - Needs new component without input forms |
| PacketTab | DISPLAY | DISPLAY | **Reuse** - Already display-only |
| DecisionTab | DISPLAY | DISPLAY | **Reuse** - Already display-only |
| StrategyTab | DISPLAY | DISPLAY | **Reuse** - Already display-only |
| SafetyTab | DISPLAY | DISPLAY | **Reuse** - Already display-only |
| PipelineFlow | DISPLAY | DISPLAY | **Reuse** - Already display-only |

### 1.3 Key Differences: IntakeTab

**Workbench IntakeTab (INPUT):**
- Trip selector dropdown with `useState`
- Customer message textarea with `useState`
- Agent notes textarea with `useState`
- Stage/mode dropdowns with `useState`
- No `spineResult` prop
- Purpose: Collect input and trigger spine

**Workspace IntakeTab (DISPLAY):**
- No trip selector (trip ID from URL)
- No input textareas
- No stage/mode dropdowns
- Accepts `spineResult` as prop
- Purpose: Display processed intake data

---

## 2. Component Reuse Strategy

### 2.1 Criteria for Reuse

**Reuse as-is:**
- Component is already display-only
- Component accepts data via props
- Component doesn't have input forms
- Component doesn't trigger spine execution

**Rebuild needed:**
- Component has input forms (textareas, dropdowns)
- Component has "Run Spine" button
- Component manages its own state for input
- Component triggers spine execution

### 2.2 Component Mapping

| Workbench Component | Workspace Counterpart | Action | Reason |
|---------------------|----------------------|--------|--------|
| IntakeTab | DisplayIntakeTab | **Rebuild** | INPUT → DISPLAY conversion needed |
| PacketTab | DisplayPacketTab | **Reuse** | Already DISPLAY |
| DecisionTab | DisplayDecisionTab | **Reuse** | Already DISPLAY |
| StrategyTab | DisplayStrategyTab | **Reuse** | Already DISPLAY |
| SafetyTab | DisplaySafetyTab | **Reuse** | Already DISPLAY |

### 2.3 New Component: DisplayIntakeTab

**Location:** `frontend/src/app/workspace/[tripId]/DisplayIntakeTab.tsx`

**Props:**
```typescript
interface DisplayIntakeTabProps {
  spineResult: SpineResult;
  tripId: string;
}
```

**Display Content:**
- Extracted facts with confidence scores
- Validation report (errors/warnings)
- Ambiguities and contradictions
- Derived signals
- Evidence references

**No Input:**
- No trip selector
- No message textareas
- No stage/mode dropdowns
- No "Run Spine" button

---

## 3. Implementation Plan

### 3.1 Phase 1: Component Analysis ✅ COMPLETE
- [x] Analyze all workbench components
- [x] Classify each as INPUT/DISPLAY
- [x] Document component reuse strategy

### 3.2 Phase 2: Component Creation

#### Task 3.2.1: Create DisplayIntakeTab
**File:** `frontend/src/app/workspace/[tripId]/DisplayIntakeTab.tsx`

**Structure:**
```typescript
export function DisplayIntakeTab({ spineResult, tripId }: DisplayIntakeTabProps) {
  const packet = spineResult.packet;
  const validation = spineResult.validation;
  
  return (
    <div className="space-y-6">
      {/* Extracted Facts */}
      <FactsSection facts={packet.facts} />
      
      {/* Validation Report */}
      <ValidationSection validation={validation} />
      
      {/* Ambiguities */}
      <AmbiguitiesSection ambiguities={packet.ambiguities} />
      
      {/* Contradictions */}
      <ContradictionsSection contradictions={packet.contradictions} />
    </div>
  );
}
```

#### Task 3.2.2: Update Workspace Routing
**File:** `frontend/src/app/workspace/[tripId]/page.tsx`

**Changes:**
```typescript
// Import new display components
import { DisplayIntakeTab } from "./DisplayIntakeTab";
import { PacketTab } from "../workbench/PacketTab"; // Reuse
import { DecisionTab } from "../workbench/DecisionTab"; // Reuse
import { StrategyTab } from "../workbench/StrategyTab"; // Reuse
import { SafetyTab } from "../workbench/SafetyTab"; // Reuse

// Use display components in workspace
<DisplayIntakeTab spineResult={spineResult} tripId={tripId} />
<PacketTab spineResult={spineResult} /> // Adapt prop signature
```

### 3.3 Phase 3: Testing
- [ ] Test DisplayIntakeTab displays data correctly
- [ ] Test PacketTab still works in workbench
- [ ] Test DecisionTab still works in workbench
- [ ] Verify no cross-contamination

---

## 4. Component Architecture

### 4.1 Display Component Pattern

```typescript
interface DisplayComponentProps {
  spineResult: SpineResult;
  tripId?: string; // Optional, for context
}

export function DisplayComponent({ spineResult, tripId }: DisplayComponentProps) {
  // Extract data from spineResult
  const { packet, validation, decision, strategy, traveler_bundle } = spineResult;
  
  // Render display-only content
  return (
    <div>
      {/* Display content */}
    </div>
  );
}
```

### 4.2 Input Component Pattern (Unchanged)

```typescript
export function InputComponent() {
  const [inputData, setInputData] = useState('');
  
  const handleRunSpine = () => {
    // Trigger spine execution
  };
  
  return (
    <div>
      {/* Input forms */}
      <button onClick={handleRunSpine}>Run Spine</button>
    </div>
  );
}
```

---

## 5. File Structure

```
frontend/src/app/
├── workbench/                    # INPUT components (unchanged)
│   ├── IntakeTab.tsx            # INPUT: Trip selector + forms
│   ├── PacketTab.tsx            # DISPLAY: Shows packet data
│   ├── DecisionTab.tsx          # DISPLAY: Shows decision data
│   ├── StrategyTab.tsx          # DISPLAY: Shows strategy
│   ├── SafetyTab.tsx            # DISPLAY: Shows safety analysis
│   └── page.tsx                 # Workbench shell
│
└── workspace/                    # DISPLAY components (new)
    ├── [tripId]/
    │   ├── page.tsx             # Workspace shell
    │   ├── layout.tsx           # Tab navigation
    │   ├── DisplayIntakeTab.tsx # NEW: Display-only intake
    │   ├── DisplayPacketTab.tsx # Reuse PacketTab
    │   ├── DisplayDecisionTab.tsx # Reuse DecisionTab
    │   ├── DisplayStrategyTab.tsx # Reuse StrategyTab
    │   └── DisplaySafetyTab.tsx # Reuse SafetyTab
    └── lib/
        └── workspaceStore.ts    # Zustand store
```

---

## 6. State Management

### 6.1 Workspace Store

**Location:** `frontend/src/app/workspace/[tripId]/lib/workspaceStore.ts`

```typescript
interface WorkspaceState {
  currentTripId: string | null;
  spineResults: Record<string, SpineResult>;
  isLoading: boolean;
  error: string | null;
}

interface WorkspaceActions {
  setTripId: (tripId: string) => void;
  loadSpineResult: (tripId: string) => Promise<void>;
  getCachedResult: (tripId: string) => SpineResult | undefined;
  clearTrip: () => void;
}
```

### 6.2 Component State Flow

```
Workspace Shell
    │
    ├─► Load trip context
    │   ├─ Check cache
    │   └─ Call /api/spine/run if needed
    │
    ▼
DisplayIntakeTab (prop: spineResult)
    │
    ├─ Extract packet data
    ├─ Extract validation data
    └─ Render display-only content
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**DisplayIntakeTab:**
- Renders facts section correctly
- Shows validation errors/warnings
- Displays ambiguities and contradictions
- Handles empty state

**PacketTab (reused):**
- Still works in workbench
- Still shows data correctly

### 7.2 Integration Tests

**Workspace Routing:**
- Navigate to workspace loads data
- All tabs display data correctly
- No input forms visible

**Component Isolation:**
- Input components unchanged
- Display components work independently

---

## 8. Rollback Plan

### 8.1 If DisplayIntakeTab Fails

**Option A:** Revert to workbench pattern
- Keep workspace using workbench IntakeTab
- Accept input forms in workspace (not ideal)

**Option B:** Simplified display
- Create minimal DisplayIntakeTab
- Show only key facts without details

### 8.2 If Component Reuse Breaks

**Option A:** Fork components
- Create workspace-specific versions
- Accept code duplication temporarily

**Option B:** Feature flag
- Keep workspace behind `/workspace` route
- Keep workbench at `/workbench`
- Test both in parallel

---

## 9. Success Criteria

### 9.1 Code Quality
- [ ] No INPUT components in workspace
- [ ] All workspace components are DISPLAY-only
- [ ] Workbench components unchanged
- [ ] Test coverage >80%

### 9.2 Functionality
- [ ] Workspace displays data correctly
- [ ] No input forms in workspace
- [ ] "Run Spine" only in workspace shell
- [ ] All tabs work correctly

### 9.3 Developer Experience
- [ ] Component purpose clear from name
- [ ] Documentation explains reuse strategy
- [ ] Tests cover all scenarios

---

## 10. Future Enhancements

### 10.1 Component Library
- Extract common display components
- Create shared UI library
- Standardize component patterns

### 10.2 Dynamic Adaptation
- Auto-generate DISPLAY variants from INPUT
- Component composition system
- Template-based component generation