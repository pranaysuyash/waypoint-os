# Agentic Eval Maturity — VNext (2026-07-01)

**Date:** 2026-07-01  
**Owner context:** Travel Agency Agent product loop + operator reality checks  
**Source:** Built from unresolved items in `Docs/EXPLORATION_TOPICS.md#18` and `Docs/research/AGENTIC_EVAL_CANONICAL_ROADMAP_2026-06-20.md`

## Will (in-scope this pass)

- Extend `src/evals/audit/snapshot.py` routing health block from status-only to complete gate evidence:
  - add `alerts` (warning/critical threshold hits with metric + severity)
  - add deterministic `metrics_snapshot` used for regression checks
  - preserve JSON-serialisable stable view
- Improve D6 snapshot confidence surface by persisting the above in `build_gate_snapshot()`.
- Expand canonical eval evidence for operator traceability:
  - include `review_workflow_unit_id` in canonical evidence rows
  - include `owner` inferred from failure layer via existing recommendation profiles
- Export operator-facing review-cascade timeline in `/api/trips/{trip_id}/agentic-eval` so review outcomes can be read as execution → review-action → closure chains
- Expose routing-health envelope in `/api/trips/{trip_id}/agentic-eval` responses:
  - include `routing_health` with status, alert summary, checked timestamp, and metrics snapshot
  - include public routing authority context from `resolve_routing_health_authority()`
- Add regression-safe tests for new D6 snapshot fields and evidence traceability.
- Add operator-facing live-refresh controls in `/(agency)/audit` for routing-health paging and alert visibility (manual refresh, pause/resume polling).

## Should (next milestone, 1–2 weeks)

- Add unit-level test fixtures for non-`activity` D6 categories that currently have no rule runners (`pacing`, `logistics`, `documents`, `weather`, `safety`, plus any newly aligned manifest additions).
- Replace placeholder `status: planned/shadow` category outcomes with explicit fixture-backed rule execution (even if no findings) so gates can report measured precision/recall status instead of missing-metric inference.
- Add routing-health alert publication path from CI/gate job artifacts into operator runbooks:
  - hook for `status == warning|critical`
  - alert payload includes `metric`, `actual_value`, `threshold`, `status`.
- Add API client documentation for `routing_health` semantics and operator action expectations.

## Can (incremental opportunities)

- Cross-agent conflict evaluator to detect duplicate/overlapping agent writes before they become trip-state conflicts.
- Per-category trend detection (`p50/p95`, fallback and escalation rates over rolling windows) with control-chart style drift alarms.
- Cost attribution by workflow category and per-agent segment for budget-aware gating.
- Per-step latency decomposition (ingestion/extraction/model/routing/review) instead of aggregate latency.
- Real shadow replay path for candidate fixes (LLM re-run) with acceptance/reject rollup and rollback policy.

## Open items carried forward with ownership

- **Data drift monitoring (owner: closed_loop_learning):** add rolling-window trend logic and runbook thresholds for routing health.
- **Category completion (owner: agents-runtime):** add real D6 rule runners for non-activity categories listed in `src/evals/audit/manifest.yaml`.
- **Conflict governance (owner: operators):** define duplicate-action contract between agents and add audit for conflicting field edits.
- **Decision support (owner: product):** decide whether `routing`/`feasibility`/`document_readiness`/`destination_intelligence` category names in roadmap docs should be merged with existing manifest categories or expanded to dedicated manifest entries.

## Completion proof (2026-07-01)

- `tests/evals/test_d6_gate_snapshot.py` updated for `routing_health.alerts` + `routing_health.metrics_snapshot`.
- `tests/evals/test_agentic_feedback.py` updated for review-workflow and owner inference in `canonical_evidence_records`.
- `src/evals/audit/snapshot.py` and `src/evals/agentic_feedback.py` updated with traceability fields, plus review-cascade timeline output in `aggregate_eval_records`.
- `tests/evals/test_agentic_feedback.py` now covers timeline export shape and action/closure linkage.
- `spine_api/routers/confirmations.py` now returns `routing_health` in `/api/trips/{trip_id}/agentic-eval`.
- `tests/evals/test_agentic_eval_endpoint.py` now verifies routing_health contract and authority surfacing on eval endpoint responses.
- `tests/evals/test_agentic_eval_endpoint.py` now verifies routing_health alert-contract fields and critical severity behavior for operator actions.
- `Docs/research/AGENTIC_EVAL_ROUTING_HEALTH_OPERATOR_CONTRACT_2026-07-01.md` added as the operator-facing contract/reference.
- `Docs/EXPLORATION_TOPICS.md` updated to mark this tranche as implemented and point to this VNext plan.
- `frontend/src/app/(agency)/audit/PageClient.tsx` updated with manual + scheduled refresh controls.
- `frontend/src/app/(agency)/audit/__tests__/PageClient.test.tsx` updated with control-level coverage for pause/resume and manual refresh.
