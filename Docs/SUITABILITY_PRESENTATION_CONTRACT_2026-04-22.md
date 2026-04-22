# Suitability Presentation Contract

**Date**: 2026-04-22
**Status**: Draft
**Depends On**: Frontend_SUITABILITY_DISPLAY_STRATEGY_2026-04-22.md
**Companion**: AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md

---

## 0. Purpose

Define the exact data shape the frontend must consume for suitability display, independent of the generic `risk_flags` list. This is the contract between backend scoring output and frontend rendering logic.

---

## 1. Current Data Shape (Verified 2026-04-22)

Backend emits risk flags via `generate_risk_flags()` as `List[Dict[str, Any]]`:

```python
{
    "flag": "elderly_mobility_risk",       # String identifier
    "severity": "high",                    # String: low|medium|high|critical
    "message": "Elderly travelers + Maldives — verify medical access"  # Human text
}
```

**Verdict**: Structure exists. Sufficient for Shadow Field strategy. Frontend can start immediately.

**Limitation**: No `type` field to distinguish suitability from compliance. The `flag` string encodes category implicitly (prefix convention).

---

## 2. Target Data Shape: SuitabilityProfile

This is the NEW field to be added alongside (not replacing) `risk_flags`.

```typescript
interface SuitabilityProfile {
  // --- Top-level summary ---
  summary: {
    status: "suitable" | "caution" | "unsuitable";
    primaryReason: string;          // One-line explanation
    overallScore: number;           // 0-100 (from Tier1+Tier2 scoring)
  };

  // --- Per-dimension breakdown ---
  dimensions: Array<{
    type: "age" | "mobility" | "weight" | "intensity" | "climate" | "recovery" | "other";
    severity: "low" | "medium" | "high";
    score: number;                  // Dimension-specific score
    reason: string;                 // Why this dimension flagged
    evidence_id?: string;           // Link to source data / catalog entry
  }>;

  // --- Actionability ---
  overrides: Array<{
    flag: string;                   // Which risk flag this relates to
    overridden: boolean;
    override_action?: "suppress" | "downgrade" | "acknowledge";
    override_reason?: string;
    overridden_by?: string;
    overridden_at?: string;         // ISO timestamp
  }>;
}
```

### Field-by-field rationale

| Field | Why it exists | Frontend use |
|-------|--------------|-------------|
| `summary.status` | Operators need triage at a glance | Card border color / badge |
| `summary.primaryReason` | Scanning, not reading | Card header text |
| `summary.overallScore` | Trend tracking over time | Score bar / sparkline |
| `dimensions[].type` | Different iconography per risk type | Icon selection |
| `dimensions[].severity` | Severity ≠ type; both matter independently | Color coding within type |
| `dimensions[].reason` | Drill-down context | Expandable detail text |
| `dimensions[].evidence_id` | Traceability to source catalog | Click-through to catalog entry |
| `overrides[]` | Feedback loop (see AGENT_FEEDBACK_LOOP_SPEC) | Accept/Override buttons |

---

## 3. Shadow Field Integration

### Backend side

In `decision.py`, the decision object currently returns:

```python
decision.risk_flags: List[Dict[str, Any]]
```

Add:

```python
decision.suitability_profile: Optional[SuitabilityProfile] = None
```

Population logic:
1. If any flag in `risk_flags` starts with a suitability prefix (`elderly_`, `toddler_`, `mobility_`, `intensity_`, `climate_`, `recovery_`), construct a `SuitabilityProfile`.
2. Map the flat flag structure to the dimensioned structure.
3. Calculate `summary.status` from the highest severity dimension.
4. Calculate `summary.overallScore` from the Tier1+Tier2 score.

### Frontend side

In `DecisionPanel.tsx`:

```typescript
// Render priority:
// 1. If decision.suitability_profile exists → render <SuitabilityCard profile={...} />
// 2. Else → render generic risk_flags list (current behavior)

{decision.suitability_profile ? (
  <SuitabilityCard profile={decision.suitability_profile} />
) : (
  <GenericRiskFlags flags={decision.risk_flags} />
)}
```

**Fallback guarantee**: If backend hasn't been updated, `suitability_profile` is undefined, and the UI renders exactly as it does today. Zero breakage.

---

## 4. Frontend Component Specification

### 4.1 SuitabilityCard

**Location**: `src/frontend/src/components/SuitabilityCard.tsx` (new file)

**Props**:
```typescript
interface SuitabilityCardProps {
  profile: SuitabilityProfile;
  onOverride?: (flag: string, action: OverrideAction, reason: string) => void;
  compact?: boolean;  // Collapse dimensions by default
}
```

**Visual layout**:
```
┌──────────────────────────────────────────┐
│ ⚠ CAUTION                    Score: 67/100│
│ Elderly mobility risk for steep terrain    │
├──────────────────────────────────────────┤
│ ♿ Mobility  HIGH    │ Steep inclines...   │
│ 👶 Age      MEDIUM  │ Verify fitness...   │
│   [expand for details]                     │
├──────────────────────────────────────────┤
│ [Override ▼]  [Acknowledge]  [Suppress]   │
└──────────────────────────────────────────┘
```

**Color rules**:
- `suitable` → green border (#22c55e)
- `caution` → yellow border (#eab308)
- `unsuitable` → red border (#ef4444)

**Icon mapping**:
```typescript
const TYPE_ICONS: Record<string, string> = {
  age: "👶",
  mobility: "♿",
  weight: "⚖️",
  intensity: "⚡",
  climate: "🌡️",
  recovery: "🩹",
  other: "⚠️",
};
```

### 4.2 Accordion MVP (Phase 0)

Before building the full `SuitabilityCard`, implement a lightweight wrapper:

**What**: Any `risk_flags` entry whose `flag` field starts with a suitability prefix gets wrapped in an expandable accordion.

**File**: Modify `DecisionPanel.tsx` inline (no new component yet).

**Logic**:
```typescript
const SUITABILITY_PREFIXES = ["elderly_", "toddler_", "mobility_", "intensity_", "climate_", "recovery_"];

function isSuitabilityFlag(flag: string): boolean {
  return SUITABILITY_PREFIXES.some(p => flag.startsWith(p));
}
```

**Rendering**: Suitability flags show a different icon and are collapsible. Non-suitability flags render as before.

**Effort**: ~2 hours.

---

## 5. Suitability Prefix Registry

All suitability-related flags MUST use one of these prefixes:

| Prefix | Category | Example Flag |
|--------|----------|-------------|
| `elderly_` | Age-related (elderly) | `elderly_mobility_risk` |
| `toddler_` | Age-related (toddler) | `toddler_pacing_risk` |
| `mobility_` | Physical mobility | `mobility_stairs_risk` |
| `intensity_` | Activity exertion | `intensity_strenuous_risk` |
| `climate_` | Weather/climate | `climate_heat_risk` |
| `recovery_` | Rest/recovery | `recovery_fatigue_risk` |

Non-suitability flags (compliance, margin, etc.) MUST NOT use these prefixes.

---

## 6. Implementation Phases

### Phase 0: Accordion MVP (Week 1)
- [ ] Add `isSuitabilityFlag()` helper to DecisionPanel
- [ ] Wrap suitability flags in expandable accordion
- [ ] Add type-specific icons
- **Backend**: No changes needed.
- **Risk**: None. Pure additive UI change.

### Phase 1: Shadow Field + SuitabilityCard (Week 2-3)
- [ ] Backend: Add `suitability_profile` to decision output
- [ ] Backend: Construct `SuitabilityProfile` from existing suitability flags
- [ ] Frontend: Create `SuitabilityCard` component
- [ ] Frontend: Wire Shadow Field logic in DecisionPanel
- **Fallback**: If `suitability_profile` undefined, render generic list.

### Phase 2: Override Integration (Week 3-4)
- [ ] Frontend: Add Override/Acknowledge/Suppress buttons to SuitabilityCard
- [ ] Backend: Implement `POST /trips/{trip_id}/override` (see AGENT_FEEDBACK_LOOP_SPEC)
- [ ] Backend: Persist overrides in decision cache
- [ ] Agent: Use override history to adjust future flag generation
- **Depends on**: AGENT_FEEDBACK_LOOP_SPEC implementation.

### Phase 3: Confidence Display (Future)
- [ ] Show per-dimension confidence scores
- [ ] Trend sparklines for suitability over multiple trips
- [ ] Agent learning from override patterns

---

## 7. Verification Checklist

Before declaring any phase complete:
- [ ] Backend test: `generate_risk_flags()` emits structured flags with `flag`, `severity`, `message`
- [ ] Backend test: `suitability_profile` populated when suitability flags exist
- [ ] Frontend test: DecisionPanel renders generic list when `suitability_profile` absent
- [ ] Frontend test: SuitabilityCard renders with structured profile
- [ ] Visual test: Color coding matches severity
- [ ] Visual test: Icons match dimension types
- [ ] Override test: Clicking "Override" calls handler with correct flag and action
- [ ] Fallback test: Removing `suitability_profile` from API response causes generic list to render

---

## Cross-References

- **Strategy**: Frontend_SUITABILITY_DISPLAY_STRATEGY_2026-04-22.md
- **Feedback Loop API**: AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md
- **Backend Suitability Module**: src/suitability/
- **Frontend Decision Panel**: src/frontend/src/components/DecisionPanel.tsx
- **Backend Decision Engine**: src/intake/decision.py (line ~1180)