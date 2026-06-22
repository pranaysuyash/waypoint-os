# Agentic Eval Canonical Roadmap — 2026-06-19

## What we shipped in this slice

- Added a canonical evidence builder in `src/evals/agentic_feedback.py` that emits
  one stable record per evaluable execution event.
- Canonical fields now included in the eval summary include:
  - `workflow_unit_id`, `workflow_type`, `input_artifact_id`
  - `provider`, `model`
  - `prompt_version`, `prompt_hash`
  - `schema_version`, `routing_version`, `dictionary_version`, `normalization_version`
  - `fallback_trigger_reason`, `fallback_result`
  - `review_trigger_reason`, `review_outcome`, `escalation_outcome`
  - `failure_signature`, `failure_layer`, `next_fix_layer`
  - `final_acceptance_status`, `latency_ms`, `cost_usd`
  - `created_at`
- Added canonical records to `/api/trips/{trip_id}/agentic-eval` response via `aggregate_eval_records`:
  - new key: `canonical_evidence_records`
- Kept routing metrics and repeated-failure work-item surface compatible while expanding
  each work item with action-ready fields:
  - `severity`, `proposed_change`, `expected_improvement`, `regression_risk`,
    `rerun_subset`, `keep_if`, `revert_if`, `owner`
- Added workflow-unit linkage for review escalations:
  - `ReviewActionRequest.review_workflow_unit_id` is now accepted by the trip-review API.
  - Review audit events persist `review_workflow_unit_id` and `escalation_outcome`.
  - Agentic eval aggregation joins `review_action` events to matching execution workflow units.
- Added provider-retry provenance to extraction attempt events:
  - `provider_retry` and `max_provider_retries` are now part of the canonical event metadata allowlist.
  - Retry failures stay internal to the logical provider attempt while still surfacing the retry path.
- Added optional `workflow_unit_id` query parameter to `/api/trips/{trip_id}/agentic-eval` to pull unit-level summaries.

## Tests added

- `tests/evals/test_agentic_feedback.py`
  - `test_aggregate_eval_records_includes_canonical_evidence_records`
  - `test_build_canonical_evidence_records_limits_output`
  - `test_build_repeated_failure_signal_severity_increases_with_repetition`
  - `test_build_canonical_evidence_records_maps_non_extraction_events`
  - `test_build_canonical_evidence_records_uses_review_escalation_outcome_by_workflow_unit`
  - `test_build_routing_metrics_scopes_escalation_outcomes_to_candidate_unit_ids`
  - `test_build_routing_metrics_uses_legacy_outcomes_without_unit_links`
- `tests/evals/test_agentic_eval_endpoint.py`
  - assertion that endpoint response includes `canonical_evidence_records`
  - endpoint coverage for `workflow_unit_id` propagation
- `frontend/src/lib/__tests__/api-client-contract-surface.test.ts`
  - `passes workflow unit id through the trip review action client`

## Immediate value against user’s request

- Inputs (`trip/subject`, prompt/schema/routing versions), outputs (final acceptance)
  and intermediate path signals are now emitted in one shape that can be fed by
  dashboards, schedulers, and repeat-failure reducers without joining ad-hoc across
  multiple systems.
- Route-level evaluation is now traceable end-to-end:
  - **Input:** workflow unit metadata (`workflow_unit_id`, `workflow_type`, artifact/context ids)
  - **Prompt layer:** `prompt_version`, `prompt_hash`, `schema_version`, routing/dictionary/normalization versions
  - **Output/action layer:** `fallback_result`, `review_outcome`, `escalation_outcome`, `final_acceptance_status`
  - **Cost/latency layer:** `latency_ms`, `cost_usd`
  - **Decision layer:** repeated-work-item severity, owner, keep/revert gates.

## What remains (next recommended slice)

1. Add missing `input_artifact_id` emission on all extractors and any non-extraction
   AI workflow events so `canonical_evidence_records` is complete across the whole
   product.
2. Add a read-side page in the operator dashboard that surfaces:
   - current routing quality
   - repeated work items
   - false/missed escalation distribution
3. Add a first-pass backlog action API for operators to claim a work item and create a ticket.
4. Add guardrails/tests for mixed legacy audit trails when review events predate
   workflow-unit linkage in active systems.

## Practical I/P/O Map for this repo

- Inputs now in use:
  - execution events (`ExecutionEvent`) with workflow metadata
  - review/audit events (`AuditStore.get_events_for_trip`) for escalation outcome
  - request-level constraints (`workflow`, `workflow_unit_id`, `min_occurrences`, `window_minutes`)
  - path metadata (`prompt_version`, `schema_version`, `routing_version`,
    `dictionary_version`, `normalization_version`, `provider`, `model`, etc.)

- Prompt/decision surface:
  - prompt version/hash are preserved in event metadata when producers emit them
  - fallback trigger and fallback result are preserved
  - review trigger/review outcome and escalation outcome are now joined into canonical evidence

- Outputs now in use:
  - `/api/trips/{trip_id}/agentic-eval` returns:
    - `canonical_evidence_records[]` (path-preserving evidence)
    - repeated failure `work_items[]` (with severity, keep/revert gates, owner)
    - routing metrics (`fallback` and `review` quality signals, p50/p95 latency/cost)

- Where not yet covered:
  - no single cross-workflow eval export view (still strongest in extraction/confirmation path)
  - no universal escalation-fidelity metrics for every workflow yet (false/missed escalation coverage is growing)
  - no persisted work-item backlog API yet (currently contract/test-visible only)
