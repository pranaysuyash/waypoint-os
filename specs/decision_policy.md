# Decision Policy v0.2 (Runtime Contract)

Last updated: 2026-04-14 (Asia/Kolkata)
Source of truth: `src/intake/decision.py` (`run_gap_and_decision`)

## Purpose
Map a `CanonicalPacket` to exactly one `decision_state` with explicit blocker, contradiction, ambiguity, and risk reasoning.

## Allowed Decision States
Runtime allows only:
- `ASK_FOLLOWUP`
- `PROCEED_INTERNAL_DRAFT`
- `PROCEED_TRAVELER_SAFE`
- `BRANCH_OPTIONS`
- `STOP_NEEDS_REVIEW`

## Core Inputs Used by Policy
- Stage MVB hard/soft blockers (`MVB_BY_STAGE`)
- Ambiguity severity (`blocking` vs `advisory`)
- Contradictions (including budget feasibility injected contradiction)
- Operating mode routing (`normal_intake`, `emergency`, `audit`, `owner_review`, `post_trip`, etc.)
- Confidence score

## Precedence (As Implemented)
Decision is computed in this order:

1. `forced_decision` from `apply_operating_mode` (if any).
2. Critical contradiction handling:
   - Any critical contradiction yields follow-up questions.
   - If contradiction type includes `date_conflict` or `document_conflict` => `STOP_NEEDS_REVIEW`.
   - Else critical contradictions => `ASK_FOLLOWUP`.
3. Hard blockers present => `ASK_FOLLOWUP`.
4. Budget contradictions (non-critical path) => `BRANCH_OPTIONS`.
5. If none above:
   - No blocking ambiguities and no soft blockers => `PROCEED_TRAVELER_SAFE`.
   - Soft blockers present => `PROCEED_INTERNAL_DRAFT`.
   - Blocking ambiguities only => `ASK_FOLLOWUP`.
   - Else fallback by confidence (<0.6 => `PROCEED_INTERNAL_DRAFT`, otherwise `PROCEED_TRAVELER_SAFE`).
6. `post_trip` mode override sets `PROCEED_TRAVELER_SAFE` and clears blockers/questions.
7. Final invariant guards may still downgrade:
   - If blocking ambiguities exist and state is `PROCEED_TRAVELER_SAFE` => force `ASK_FOLLOWUP`.
   - If feasibility is `infeasible` and state is `PROCEED_TRAVELER_SAFE` => force `ASK_FOLLOWUP`.

## Policy Invariants (Must Hold)

1. Hard blockers cannot proceed:
   - If `hard_blockers` is non-empty, state must be `ASK_FOLLOWUP`.

2. Critical date/document contradictions are stop-level:
   - Any critical contradiction with type `date_conflict` or `document_conflict` must result in `STOP_NEEDS_REVIEW`.

3. Blocking ambiguity cannot be traveler-safe:
   - `decision_state == PROCEED_TRAVELER_SAFE` is forbidden when any ambiguity is classified as `blocking`.

4. Decision enum safety:
   - `decision_state` must be a member of the allowed state set listed above.

## Notes on Current Behavior
- Hard blockers are evaluated before soft blockers and before confidence-based fallback.
- Soft blockers produce `PROCEED_INTERNAL_DRAFT` (with follow-up prompts), not `ASK_FOLLOWUP`.
- Budget infeasibility is converted into:
  - hard blocker `budget_feasibility`
  - contradiction `budget_feasibility`
  and therefore cannot result in traveler-safe output.
- `post_trip` mode bypasses normal blocker flow but is still subject to final invariant checks.
