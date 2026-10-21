# Decision Policy v0.3 (Runtime Contract)

Last updated: 2026-09-18 (Asia/Kolkata)
Source of truth: `src/intake/decision.py` (`run_gap_and_decision`)
Conformance harness: `tests/test_decision_policy_conformance.py`
Version history: v0.2 (2026-04-14) → v0.3 (2026-09-18). v0.2→v0.3 changes are
listed at the bottom; this matrix is also recorded in
`specs/runtime_contract_version_matrix_2026-05-12.md`.

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
- Contradictions (including the stage-gated budget feasibility contradiction)
- Operating mode routing (`normal_intake`, `emergency`, `audit`, `owner_review`, `post_trip`, etc.)
- Confidence scorecard (computed and reported; **not** a decision gate — see v0.3 change 1)
- Budget feasibility, including season-tier adjustment of the destination minimum (see v0.3 change 4)

## Precedence (As Implemented, v0.3)
Decision is computed in this order inside `run_gap_and_decision`:

1. `forced_decision` from `apply_operating_mode` (if any).
2. Budget feasibility stage gating (Phase 5):
   - feasibility `infeasible` in stage `proposal`/`booking` → **hard blocker** `budget_feasibility`;
   - infeasible in `discovery`/`shortlist` → **soft blocker** `budget_feasibility`;
   - either way a `budget_feasibility` contradiction is appended.
3. Urgency suppression for `normal_intake` (soft-blocker set only).
4. Contradiction evaluation (Phase 7). A contradiction is *actionable* iff its
   table action is:
   - `STOP_NEEDS_REVIEW` (any priority), or
   - priority `critical`, or
   - decision `ASK_FOLLOWUP` with priority `high` **and** type in
     `HIGH_PRIORITY_ESCALATION_TYPES = {"party_conflict", "origin_conflict"}`.
   `budget_feasibility` is deliberately excluded from the escalation set — its
   action is stage-gated in step 2 and expressed as a blocker, not an
   escalation.
5. Decision state machine (Phase 9, only when no forced decision):
   - Any actionable contradictions → follow-up questions for all of them;
     state is `STOP_NEEDS_REVIEW` if any actionable action is STOP, else
     `ASK_FOLLOWUP`. **STOP wins over ASK when multiple independent conflicts
     coexist.**
   - elif hard blockers present → `ASK_FOLLOWUP` (questions ordered by
     operation impact, TS-07).
   - elif a `budget_conflict` contradiction exists → `BRANCH_OPTIONS` with the
     budget-tier options entry.
   - else (no blocking ambiguities, no soft blockers) → `PROCEED_TRAVELER_SAFE`;
     soft blockers only → `PROCEED_INTERNAL_DRAFT` (with follow-up questions);
     blocking ambiguities → `ASK_FOLLOWUP`.
   - **There is no confidence-based fallback.** A separate
     `overall_confidence < 0.6 → PROCEED_INTERNAL_DRAFT` floor previously
     existed here and was removed as unreachable dead code (N01 triage,
     2026-09-02 §2.2). Fully populated low-confidence packets are
     traveler-safe by corpus contract (`basic_minimal_safe` asserts
     `PROCEED_TRAVELER_SAFE` at confidence 0.496).
6. Risk flags, override-learning adjustments, and suitability profile are
   computed after the state machine and do not change `decision_state`.
7. `post_trip` mode override sets `PROCEED_TRAVELER_SAFE` and clears
   blockers/questions (still subject to the final invariant checks below).
8. Final invariant guards may still downgrade:
   - If blocking ambiguities exist and state is `PROCEED_TRAVELER_SAFE` → force `ASK_FOLLOWUP`.
   - If feasibility is `infeasible` and state is `PROCEED_TRAVELER_SAFE` → force `ASK_FOLLOWUP`.

## Policy Invariants (Must Hold)

1. Hard blockers cannot proceed:
   - If `hard_blockers` is non-empty, state must be `ASK_FOLLOWUP`.

2. Critical date/document contradictions are stop-level:
   - Any critical contradiction with type `date_conflict` or `document_conflict` must result in `STOP_NEEDS_REVIEW`.

3. Blocking ambiguity cannot be traveler-safe:
   - `decision_state == PROCEED_TRAVELER_SAFE` is forbidden when any ambiguity is classified as `blocking`.

4. Decision enum safety:
   - `decision_state` must be a member of the allowed state set listed above.

5. Low confidence cannot force a downgrade (v0.3):
   - No branch may key off `overall_confidence` alone; confidence is reported,
     never a standalone gate.

6. Budget infeasibility is stage-gated (v0.3):
   - `budget_feasibility` is a hard blocker only in `proposal`/`booking`;
     elsewhere it is a soft blocker. In all stages an infeasible packet can
     never surface as `PROCEED_TRAVELER_SAFE` (guard 8, second bullet).

## Notes on Current Behavior
- Hard blockers are evaluated before soft blockers and before any fallback.
- Soft blockers produce `PROCEED_INTERNAL_DRAFT` (with follow-up prompts), not `ASK_FOLLOWUP`.
- Budget infeasibility is converted into a stage-gated blocker plus a
  `budget_feasibility` contradiction, and therefore cannot result in
  traveler-safe output in any stage.
- `post_trip` mode bypasses normal blocker flow but is still subject to final
  invariant checks.
- `general_conflict` (medium) is not in the escalation set; its user-facing
  question behavior is specified alongside the contradiction→question mapping
  tests (`tests/test_decision_policy_conformance.py`).

## v0.2 → v0.3 Changes (2026-09-18)
1. **Removed the documented confidence fallback.** v0.2 §"Precedence" step 5
   ("fallback by confidence <0.6 → `PROCEED_INTERNAL_DRAFT`") no longer exists
   in runtime; it was removed as unreachable dead code in the N01 triage
   (2026-09-02 §2.2). The spec previously documented a behavior the runtime
   deliberately does not have.
2. **Stage-gated budget feasibility documented.** v0.2 stated budget
   infeasibility unconditionally becomes a hard blocker
   (`budget_feasibility`); runtime has stage-gated it since Phase 5 gating
   landed — hard blocker only in `proposal`/`booking`, soft blocker in
   `discovery`/`shortlist`.
3. **High-priority escalation documented.** `party_conflict` and
   `origin_conflict` escalate to `ASK_FOLLOWUP` via
   `HIGH_PRIORITY_ESCALATION_TYPES`; v0.2 did not mention this path.
4. **STOP-over-ASK precedence documented.** When multiple independent policy
   conflicts coexist, `STOP_NEEDS_REVIEW` wins over `ASK_FOLLOWUP`; v0.2 did
   not state this.
5. **Season-tier feasibility input documented** (see Core Inputs): the
   destination minimum in `check_budget_feasibility` is multiplied by a
   per-destination season tier (`peak` 1.30 / `shoulder` 1.15 / `off` 1.0)
   resolved from the packet's structured travel dates; unknown destinations or
   unresolvable dates keep multiplier 1.0. This supersedes the two unused flat
   `_SEASON_MULTIPLIER_*` constants and closes the gap recorded in
   `Docs/CORE_INSIGHT_AND_HARDCODED_INVENTORY_2026-04-16.md` ("No seasonality
   factor… multipliers don't vary by destination").
