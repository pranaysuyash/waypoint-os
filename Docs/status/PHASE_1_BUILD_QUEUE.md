# PHASE_1_BUILD_QUEUE (Additive Foundation, 2026-04-15)

This queue is **phase-ordered implementation**, not scope reduction.
Goal: establish hard contracts and evidence so large multi-agent orchestration can expand safely.

## P1.1 Canonical State Contract Hardening
- [ ] Add/confirm field-level authority metadata:
  - `source_type`, `source_id`, `captured_at`, `authority_level`, `verified_by_human`
- [ ] Add/confirm overwrite and freshness semantics:
  - `overwrite_policy`, `staleness_window`, `resolution_status`
- [ ] Add fixture cases for stale/high-authority conflict resolution.

Acceptance:
- Deterministic conflict resolution in tests.
- Provenance and freshness present on critical fields.

## P1.2 Stage-Aware Decision State Machine
- [ ] Finalize stage transitions: discovery, shortlist, proposal, booking, ops, post-trip.
- [ ] Add per-stage blocker lists and clarification budgets.
- [ ] Add loop detection and contradiction severity thresholds.
- [ ] Add “brief freeze” behavior before quote/proposal generation.

Acceptance:
- State transitions testable with deterministic expected outcomes.
- No repeated follow-up loops past configured threshold.

## P1.3 Prompt Registry + Composer Contracts
- [ ] Lock modular prompt block interfaces.
- [ ] Ensure composed prompts carry provenance/confidence flags.
- [ ] Add verifier checks for required policy blocks in composed outputs.

Acceptance:
- Prompt assembly reproducible from registry and state.
- Missing mandatory blocks fail verifier tests.

## P1.4 Lifecycle Intelligence in Runtime
- [ ] Integrate lifecycle state in decision path (repeat, ghost-risk, window-shopper, churn-risk).
- [ ] Ensure interventions are surfaced as policy outputs, not hidden heuristics.
- [ ] Add regression tests for lifecycle-to-policy mapping.

Acceptance:
- Lifecycle transitions are deterministic and auditable.
- Policy outputs include intervention hints where required.

## P1.5 Evaluation and Evidence Gate
- [ ] Define scorecards for:
  - extraction integrity
  - contradiction detection
  - decision correctness
  - commercial policy compliance
- [ ] Add gold case pack from personas/scenarios docs.
- [ ] Add red-team cases: authority inversion, stale memory, contradiction blindness.

Acceptance:
- Gate metrics documented and enforced before orchestration expansion.

## P1.6 Audit Trail and Documentation Discipline
- [ ] Log each implemented decision in `Docs/DISCUSSION_LOG.md`.
- [ ] Log ingestion updates in `Docs/context/CONTEXT_INGESTION_LOG_2026-04-14.md` addenda.
- [ ] Keep `Docs/INDEX.md` current with new control docs.

Acceptance:
- Every major design/implementation decision is traceable by path and date.

## Expansion Note
After this phase, activate additional specialist agents in waves using measured error clusters and ops pain.
This preserves the comprehensive architecture while maintaining runtime reliability.

