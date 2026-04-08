# Decision Policy v0.1

## Purpose
Convert the current `CanonicalPacket` state into exactly one explicit next-action decision.

---

## The Decision Matrix
The system evaluates the packet and chooses one of the following outputs:

### 1. `ASK_FOLLOWUP`
**Trigger**: 
- Any `hard blocker` for the current stage is missing.
- A stage-critical field has confidence below the required threshold.
- A `blocking` contradiction is unresolved.
- The next most valuable information requires a direct user answer.

**Output**: Ordered list of targeted questions + Rationale.

### 2. `PROCEED_INTERNAL_DRAFT`
**Trigger**: 
- Enough information exists to build a rough working draft for the agency.
- Some hard blockers may be missing, but assumptions are explicit.
- **Constraint**: The output MUST be marked as "Internal Only" and not shared with the traveler.

**Output**: Internal-only itinerary + List of explicit assumptions.

### 3. `PROCEED_TRAVELER_SAFE`
**Trigger**: 
- The stage-specific `MVB` (Minimum Viable Brief) is fully satisfied.
- No unresolved `blocking` contradictions exist.
- Confidence thresholds for all critical fields are met.

**Output**: Traveler-ready proposal + Rationale grounded in facts.

### 4. `BRANCH_OPTIONS`
**Trigger**: 
- Two or more plausible, materially different directions exist.
- Forcing a single path would be misleading or risk a "bad fit."
- Example: "Luxury-leaning" vs "Budget-conscious" contradictory signals.

**Output**: Multiple versioned paths + The specific contradiction driving the branch.

### 5. `STOP_NEEDS_REVIEW`
**Trigger**: 
- Data corruption or severe contradictions that prevent any safe path.
- Edge cases requiring human agency-owner judgment (e.g., complex legal/visa issues).

**Output**: Stop reason + Human review note.

---

## Precedence & Gating Logic

The system checks for the decision in this order:
1. **Stop Check**: Is there a fatal error or severe contradiction? $\rightarrow$ `STOP_NEEDS_REVIEW`.
2. **Blocker Check**: Is a hard blocker missing? $\rightarrow$ `ASK_FOLLOWUP`.
3. **Contradiction Check**: Is there a blocking contradiction? $\rightarrow$ `ASK_FOLLOWUP` or `BRANCH_OPTIONS`.
4. **Safety Check**: Is the MVB satisfied and confidence high? $\rightarrow$ `PROCEED_TRAVELER_SAFE`.
5. **Internal Utility Check**: Can we at least provide a draft for the owner? $\rightarrow$ `PROCEED_INTERNAL_DRAFT`.

---

## Contradiction Resolution Rules
- **Auto-Resolve**: Allowed only if the `authority_level` of one source is significantly higher than the other.
- **Branch**: Used when both contradictory values are plausible and result in different sourcing strategies.
- **Ask**: Used when the contradiction is a "blocking" field (e.g., 2 adults vs 4 adults).
