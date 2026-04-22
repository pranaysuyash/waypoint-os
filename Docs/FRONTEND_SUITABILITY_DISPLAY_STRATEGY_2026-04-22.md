# Frontend Suitability Display Strategy

**Date**: 2026-04-22
**Status**: Draft Strategy
**Related Issues**: Suitability Module Implementation (Backend Complete, Frontend Gap Identified)

---

## Executive Summary

The backend suitability module is complete (Tier 1/Tier 2 scoring, 18+ activity catalog, risk flag generation). However, the frontend is currently "deaf" to the nuance of this data.

**Current State**: Frontend treats suitability warnings as generic string bullets, losing critical metadata (severity, type, evidence).
**Goal**: Transform suitability from a "hidden feature" into a distinct, operable decision component.

---

## 1. Operational Implications: The Transparency Gap

### The Problem
The backend computes nuanced risks (e.g., "Unsuitable for elderly due to steep inclines"), but the operator sees a flat list of indistinguishable warnings.

### Operational Risks
1. **Prioritization Failure**: Operators cannot distinguish between hard compliance blockers ("Missing Insurance") and suitability warnings ("Steep inclines").
2. **Scanning vs. Reading**: In a fast-paced environment, operators scan. If suitability looks like just another generic error, critical warnings may be missed.
3. **Lack of Context**: A flag saying "High age risk" doesn't tell the operator *why* or provide evidence to override the decision safely.

---

## 2. Production Implications: The Hidden Feature

### Current Reality
The feature is "dark" — technically in production (if flags are emitted), but invisible to the user as a distinct suitability element.

### Maintenance Burden
- **Visual Stagnation**: Backend updates (e.g., new "Mobility" category) are injected as raw text into a generic list without visual hierarchy.
- **Zero UI Leverage**: We are paying the engineering cost for complex scoring but getting zero UX value from it.

### Deployment Safety
- **Safe to Ship**: New backend rules won't break the UI (it just renders strings).
- **Failure to Ship Value**: We fail to leverage the intelligence we built to help the operator make better decisions.

---

## 3. Agent-Wise Implications: The Missing Feedback Loop

### The Problem
The agent emits flags, but it has no signal that the operator saw, understood, or acted on them.

### The Gap
- **No Dialogue**: The agent shouts into the void. It cannot ask, "I flagged this as unsuitable because [X]; operator, do you disagree?"
- **No Learning**: If an operator overrides a suitability warning, the agent doesn't learn from that human judgment.

### Desired State
The UI should allow operators to "Accept" or "Override" warnings, creating a training signal for the agent.

---

## 4. Strategic Recommendations (The 5 Takes)

### Take 1: Stop Destroying Data Fidelity
**Issue**: Converting structured backend data `{ type, severity, score, reason }` into a simple string list destroys critical information.
**Action**: Frontend must consume structured objects, not flattened strings.

### Take 2: Distinguish Suitability from Compliance
**Issue**: Compliance is binary (blocker); Suitability is a spectrum (risk but maybe doable).
**Action**: Visually separate these concepts. Use different iconography and color coding.

### Take 3: Use the "Shadow Field" Strategy (Safe Path)
**Issue**: We cannot break the existing generic `risk_flags` display.
**Action**:
- Keep emitting to `decision.risk_flags` (generic list).
- Add a NEW field: `decision.suitability_profile`.
- Frontend logic: If `suitability_profile` exists, render the dedicated Suitability Card. Else, fall back to generic list.
**Benefit**: Zero downtime, progressive rollout.

### Take 4: Implement the "Accordion" MVP
**Issue**: Full dashboard redesign is heavy.
**Action**: Start small. Wrap any flag starting with `suitability_` in a component that:
1. Shows a warning icon.
2. Hides long text by default.
3. Expands on click to show the "Why".
**Effort**: ~2 hours frontend change.

### Take 5: Define the Presentation Contract
Before implementation, we must define the data shape.

**Proposed Schema (Frontend Suitability Presentation Contract)**:

```typescript
interface SuitabilityProfile {
  summary: {
    status: "suitable" | "caution" | "unsuitable";
    primaryReason: string;
    overallScore: number; // 0-100
  };
  dimensions: Array<{
    type: "age" | "mobility" | "weight" | "intensity" | "climate" | "other";
    severity: "low" | "medium" | "high";
    score: number;
    reason: string;
    evidence_id?: string; // Link to source data
  }>;
}
```

**Frontend Mapping**:
- **Icons**: ♿ (Mobility), 👶 (Age), 🛡️ (Safety), ⚖️ (Weight)
- **Colors**: Green (Suitable), Yellow (Caution), Red (Unsuitable)

---

## 5. Immediate Next Steps

1. [x] **Verify Data Shape** (COMPLETED 2026-04-22):
   - **Finding**: Backend (`src/intake/decision.py`, line 1180) returns `List[Dict[str, Any]]`.
   - **Structure**: Each dict has `flag`, `severity`, and `message` keys.
     ```python
     {
         "flag": "elderly_mobility_risk",
         "severity": "high",
         "message": "Elderly travelers + Maldives — verify medical access"
     }
     ```
   - **Conclusion**: Frontend can change immediately. The data structure exists and is sufficient for the "Shadow Field" strategy.

2. [ ] **Draft UI Spec**: Create a simple markdown spec defining:
   - The Suitability Card layout.
   - Color coding rules.
   - Interaction states (hover, expand, override).

3. [ ] **Backend Audit**: Ensure `generate_risk_flags()` in the suitability module emits the structured schema defined above.

4. [ ] **Frontend Implementation**: Implement the "Accordion" MVP as a proof-of-concept.

---

## Appendix: Status Check

**Implemented**:
- [x] Backend Tier 1/Tier 2 scoring
- [x] Static activity catalog (18+ activities)
- [x] Suitability integration via `generate_risk_flags()`
- [x] Frontend generic `risk_flags` rendering (`DecisionPanel.tsx`)

**Not Implemented**:
- [ ] Dedicated activity suitability display UI
- [ ] Explicit suitability iconography
- [ ] Per-activity suitability warnings/confidence view
- [ ] Operator override/feedback mechanism
- [ ] Structured `suitability_profile` data contract

---

## Cross-References

| Document | Purpose |
|----------|---------|
| `SUITABILITY_PRESENTATION_CONTRACT_2026-04-22.md` | Exact data shapes, component spec, implementation phases |
| `AGENT_FEEDBACK_LOOP_SPEC_2026-04-22.md` | Override API, persistence, agent learning loop |

**Status**: The strategy (this doc) defines *why* and *what direction*. The Presentation Contract defines *exactly how*. The Feedback Loop Spec defines *the override path*.
