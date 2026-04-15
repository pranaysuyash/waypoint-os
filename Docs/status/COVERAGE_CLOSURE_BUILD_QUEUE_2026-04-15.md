# COVERAGE_CLOSURE_BUILD_QUEUE (2026-04-15)

Purpose: convert the P0/P1 gaps from `Docs/COVERAGE_MATRIX_2026-04-15.md` into a dependency-ordered implementation queue aligned to concrete repo areas.

This is a **build queue**, not a reduction of scope.
It exists to close the highest-value gap between:

- what is already documented,
- what is scenario-covered,
- and what is actually enforced in runtime behavior.

## Operating Rules

- Preserve additive scope; do not delete broader capability docs.
- Close **trust-critical** gaps before expansion-layer capabilities.
- Prefer deterministic enforcement over prose-only policy.
- Every phase must end with a testable acceptance signal.
- New behavior must be reflected in docs, tests, and runtime contracts together.

## Phase 0 — Protect the Existing Baseline

### Phase 0 Goal

Keep the current discovery / intake golden path stable while higher-risk controls are added.

### Phase 0 Repo Areas

- `src/intake/*`
- `tests/*`
- existing scenario fixtures and contract tests

### Phase 0 Tasks

- [ ] Confirm the current green baseline for `tests/` remains the non-negotiable regression floor.
- [ ] Identify which existing tests cover the current intake / decision happy path and tag them as the baseline pack for future changes.
- [ ] Ensure every subsequent phase references at least one existing passing baseline test plus one new gap-closing test.

### Phase 0 Acceptance

- Existing core `tests/` suite remains green.
- Gap-closing work is additive rather than replacing baseline behavior.

### Why Phase 0 Comes First

Without a protected baseline, the project can improve edge-case thinking while accidentally degrading the only path that currently works well.

---

## Phase 1 — Canonical Blocker and Boundary Hardening (P0)

### Phase 1 Goal

Close the highest-trust gaps that can cause the system to proceed confidently while still being wrong.

### Phase 1 Repo Areas

- `src/intake/packet_models.py`
- `src/intake/extractors.py`
- `src/intake/decision.py`
- `tests/`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`

### Phase 1 Tasks

- [ ] Add or confirm canonical fields for passport / visa / document readiness in the packet model.
- [ ] Ensure booking-stage proceed states depend on canonical document-readiness checks, not only loosely related fields.
- [ ] Add explicit ambiguity handling rules so ambiguous values do not satisfy hard blockers.
- [ ] Add urgency-aware decision behavior so last-minute trips do not get trapped by the wrong soft blockers.
- [ ] Add explicit traveler-safe boundary enforcement tests for internal-only vs traveler-facing output.

### Phase 1 Acceptance

- Ambiguous values fail hard-blocker satisfaction in tests.
- Booking-stage proceed decisions require canonical document readiness.
- Urgent scenarios produce stage-appropriate behavior in decision tests.
- Traveler-facing outputs fail tests if internal-only leakage appears.

### Phase 1 Suggested Tests

- ambiguity-at-decision-time regression test
- booking-readiness passport/visa hard-blocker test
- urgent-trip soft-blocker suppression test
- traveler-safe boundary enforcement test

### Why Phase 1 Precedes Phase 2

If these controls are missing, richer memory, lifecycle, or commercial logic can amplify wrong outputs instead of improving them.

---

## Phase 2 — Budget Realism and Quote Safety (P0/P1 bridge)

### Phase 2 Goal

Stop mathematically unrealistic trips from flowing through as if they were merely incomplete but otherwise acceptable.

### Phase 2 Repo Areas

- budget-related logic in `src/intake/*`
- `tests/test_budget_decomposition.py`
- scenario fixtures covering budget realism
- proposal / decision acceptance tests

### Phase 2 Tasks

- [ ] Add explicit budget-feasibility checks based on structured assumptions rather than raw value presence.
- [ ] Distinguish between:

  - budget missing,
  - budget contradictory,
  - budget unrealistic,
  - budget stretch but still potentially viable.

- [ ] Parse stretch/flex signals into structured state rather than leaving them buried in free text.
- [ ] Add quote-safety acceptance rules so obviously unrealistic budgets cannot reach the wrong proceed states.

### Phase 2 Acceptance

- Unrealistic budgets trigger deterministic realism outcomes in tests.
- Stretch/flex signals are represented structurally in state or derived signals.
- Proposal/decision tests can distinguish impossible from merely incomplete.

### Phase 2 Suggested Tests

- unrealistic-budget-per-destination test
- budget-stretch structural parsing test
- quote-safety regression test

### Phase 2 Dependency

Phase 1 blocker semantics must be stable first.

---

## Phase 3 — Repeat Customer Memory and Multi-Party State (P1)

### Phase 3 Goal

Close two major operating-leverage gaps: unnecessary re-asking for known customers and manual coordination for group/subgroup trips.

### Phase 3 Repo Areas

- `src/intake/packet_models.py`
- lifecycle / memory-related runtime modules
- `tests/`
- scenario fixtures for repeat customer and family/group trips

### Phase 3 Tasks

- [ ] Add customer identity and memory hooks needed to represent repeat-customer context safely.
- [ ] Define rules for what prior facts may be reused automatically vs what must be reconfirmed.
- [ ] Add subgroup / multi-party packet structures for family or split-party coordination.
- [ ] Add readiness logic at subgroup level instead of only whole-trip level.

### Phase 3 Acceptance

- Repeat-customer scenarios reduce unnecessary re-asking in tests.
- Multi-party scenarios show subgroup-aware blockers/readiness in tests.
- Memory reuse does not bypass safety-critical reconfirmation.

### Phase 3 Suggested Tests

- repeat-customer known-facts reuse test
- repeat-customer safety-reconfirmation test
- subgroup readiness / mixed-readiness group test

### Phase 3 Dependency

Phase 1 and Phase 2 must be stable first, otherwise memory and group logic will compound incorrect decisions.

---

## Phase 4 — Lifecycle Policy Deepening (P1)

### Phase 4 Goal

Move lifecycle intelligence from useful documented policy into stronger runtime behavior.

### Phase 4 Repo Areas

- lifecycle runtime logic
- decision / policy outputs
- `tests/`
- `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`

### Phase 4 Tasks

- [ ] Ensure ghost-risk, churn-risk, repeat-customer, and window-shopper signals materially influence policy outputs.
- [ ] Make interventions explicit in outputs rather than leaving them as hidden heuristics.
- [ ] Add acceptance tests that prove lifecycle state changes downstream actions.

### Phase 4 Acceptance

- Lifecycle states trigger distinct policy outputs in regression tests.
- Lifecycle interventions are auditable from state to output.

### Phase 4 Suggested Tests

- ghost-risk intervention mapping test
- churn-risk commercial policy test
- repeat-customer lifecycle interaction test

### Phase 4 Dependency

Repeat-customer identity and stable baseline policy behavior from earlier phases.

---

## Phase 5 — Commercial Governance Layer (P1)

### Phase 5 Goal

Start turning commercial logic from strategic documentation into explicit runtime constraints.

### Phase 5 Repo Areas

- decision policy and future commercial-policy modules
- owner-facing/frontend specs
- `tests/`
- sourcing and pricing docs

### Phase 5 Tasks

- [ ] Add margin-risk or quote-quality signals where they can influence decisions or review routing.
- [ ] Define when commercial concerns trigger owner review, internal draft, or follow-up rather than silent proceed behavior.
- [ ] Add first-pass sourcing hierarchy hooks so sourcing path can later become a runtime input instead of only a strategy concept.

### Phase 5 Acceptance

- Margin / quote-quality concerns are test-visible and policy-visible.
- At least one owner-review or commercial-escalation path exists in tests/specs.

### Phase 5 Suggested Tests

- margin-risk review-routing test
- quote-completeness acceptance test
- sourcing-path placeholder contract test

### Phase 5 Dependency

Budget realism and owner-facing policy definitions must exist first.

---

## Phase 6 — Expansion-Layer Coverage (P2)

### Phase 6 Goal

Address important but non-blocking expansions only after core trust and leverage gaps are closed.

### Phase 6 Candidate Areas

- audit mode / wasted-spend comparison
- cancellation and refund policy engine
- in-trip disruption protocols
- post-trip review and referral loops
- additional market-segment specialization

### Phase 6 Rule

Do not start this phase until the acceptance signals in Phases 1–5 are materially complete.

---

## Ordered Implementation Summary

1. Protect current passing baseline.
2. Harden blocker semantics and traveler-safe boundary.
3. Enforce budget realism and quote safety.
4. Add repeat-customer memory and multi-party state.
5. Deepen lifecycle policy outputs.
6. Add commercial governance and review logic.
7. Expand into audit/disruption/post-trip layers.

---

## Immediate Next Coding Targets

If implementation begins immediately, the highest-signal starting surfaces are:

1. `src/intake/decision.py`
2. `src/intake/packet_models.py`
3. `src/intake/extractors.py`
4. `tests/` for new acceptance/regression coverage

These surfaces align most directly to the P0 trust gaps and should move before broader workflow expansion.

---

## Related Documents

- `Docs/COVERAGE_MATRIX_2026-04-15.md`
- `Docs/COVERAGE_ASSESSMENT_2026-04-15.md`
- `Docs/status/PHASE_1_BUILD_QUEUE.md`
- `Docs/status/STATUS_MATRIX.md`
- `Docs/LEAD_LIFECYCLE_AND_RETENTION.md`
- `Docs/personas_scenarios/SCENARIO_COVERAGE_GAPS.md`
