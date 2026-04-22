# Frontend Suitability Presentation Contract

> **SUPERSEDED**: This early draft has been replaced by **SUITABILITY_PRESENTATION_CONTRACT_2026-04-22.md**, which provides the complete SuitabilityProfile schema, Shadow Field integration strategy, SuitabilityCard component spec, and 4-phase implementation plan.
>
> This file is retained for historical reference only.

**Status**: Living Draft (Phase: Definition)
**Purpose**: Define the schema for structured suitability signals emitted by the backend to be consumed by the UI. This contract bridges the gap between generic risk-flag rendering and context-specific suitability presentation.

---

## 1. Schema Definitions

The backend should provide suitability data in a structured format rather than flat strings. The frontend will consume this via the `risk_flags` (or new `suitability_signals`) array.

### Suitability Signal Schema
```typescript
interface SuitabilitySignal {
  id: string;              // e.g., "suitability_age_001"
  category: "age" | "mobility" | "toddler" | "elderly" | "custom";
  severity: "low" | "medium" | "high" | "critical";
  displayLabel: string;    // e.g., "Age-related risk"
  reason: string;          // e.g., "This activity involves steep hiking trails."
  evidenceRef: string;     // ID for linking to the Provenance Sidebar
  actionPath: string;      // e.g., "/workspace/[tripId]/strategy#safety"
}
```

---

## 2. Frontend Rendering Strategy

Based on the schema, the UI implementation will follow these patterns:

| Severity | Color (Design Tokens) | Icon Mapping |
| :--- | :--- | :--- |
| `critical` | `var(--color-critical)` (Red) | `AlertOctagon` |
| `high` | `var(--color-danger)` (Orange-Red) | `AlertTriangle` |
| `medium` | `var(--color-warning)` (Amber) | `Info` |
| `low` | `var(--color-info)` (Blue) | `Sparkles` |

---

## 3. Implementation Evolution

### Phase 1: Classification (Current Gap)
- Backend: Tag existing `risk_flags` with the `SuitabilitySignal` structure.
- Frontend: `DecisionPanel.tsx` updates to conditionally render based on `category` instead of just mapping the string value.

### Phase 2: Iconography & Interaction
- Frontend: Introduce a `SuitabilityIcon` component that maps `category` to visual indicators.
- Frontend: Enable `onClick` on these components to trigger the **Provenance Sidebar** (linking the `evidenceRef` to the source evidence).

### Phase 3: Action Pathways
- Frontend: Render "Action Pathways" (buttons like "Review Activity" or "Override Warning") directly inside the suitability component, rather than forcing the user to find them in the main workbench flow.

---

## 4. Operational Invariants
1. **Never suppress critical signals**: `critical` severity signals must always be rendered at the top of the Suitability/Risk section.
2. **Context Preservation**: Every signal MUST provide an `evidenceRef`. If the backend cannot justify the flag, the UI must provide a "Request Explanation" fallback.
3. **Consistency**: The `displayLabel` and `reason` provided by the backend are treated as final for display, but the frontend maintains control over icon/color mapping to ensure design consistency.
