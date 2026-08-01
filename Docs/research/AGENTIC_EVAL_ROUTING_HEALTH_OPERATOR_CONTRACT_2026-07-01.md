# Agentic Eval Routing Health Operator Contract (2026-07-01)

## Purpose
Define how operators should interpret `routing_health` in
`GET /api/trips/{trip_id}/agentic-eval` and what actions to take for each severity.

## Source contract
The endpoint returns:
- `routing_health.status` (`healthy` | `warning` | `critical`)
- `routing_health.alert_count`
- `routing_health.alerts[]` entries with:
  - `metric`
  - `severity` (`warning` | `critical`)
  - `actual_value`
  - `threshold`
  - `message`
- `routing_health.checked_at`
- `routing_health.metrics_snapshot`
- `routing_health.authority`:
  - `status`
  - `blocks_ci`
  - `source` (`eval_snapshot` | `manifest_fallback`)
  - `thresholds`

## Operational interpretation
- `healthy`: no operator action required solely for routing health.
- `warning`: route for inspection.
  - review `alerts` and confirm no correlated incidents in trip agent events.
  - file triage note if trend repeats in `window_minutes`.
  - do not block trip workflows immediately.
- `critical`: escalate to operator handling.
  - `routing_health.alerts` should include at least one `severity: critical` alert.
  - if `routing_health.authority.blocks_ci` is true, route as a CI-gate issue in the owning team.
  - verify trip timeline/review outcomes before any assumptions are considered resolved.

## Alert payload semantics (required for each entry)
- `actual_value` must be the metric value from evaluation snapshot/rules at check time.
- `threshold` must be the active threshold used for the classification.
- `metric` must resolve to one of:
  - `fallback_trigger_rate`
  - `false_escalation_rate`
  - `missed_escalation_rate`
  - `review_correction_rate`
  - `latency_p50_ms`
  - `latency_p95_ms`
- `severity` MUST map to the threshold tier crossed for that metric.

## CI/runtime observability linkage
- CI-facing consumers should treat `routing_health.status == critical` and
  `routing_health.authority.blocks_ci == true` as a blocking operator notice.
- Operators should keep snapshots or exports for each escalation so follow-up work can reference:
  - endpoint payload
  - trip id and window
- `routing_health.authority.source`/`thresholds`

## Alert eventing behavior (logger policy)
- `TripEventLogger.log_routing_health_alert` suppresses duplicate warning/critical writes when the same alert condition reappears in a short burst.
- Duplicate suppression compares normalized fingerprint fields:
  - `trip_id`
  - `status`
  - `workflow`
  - `workflow_unit_id`
  - `window_minutes`
  - `min_occurrences`
  - alert metric/signature (`metric`, `severity`, rounded `actual_value`, rounded `threshold`)
  - authority context (`source`, `blocks_ci`)
- Controls:
  - `ROUTING_HEALTH_ALERT_DEDUPE_WINDOW_SECONDS` (default `900`)
  - `ROUTING_HEALTH_ALERT_DEDUPE_LOOKBACK_LIMIT` (default `250`)
- Re-logging occurs when the signature changes, status changes, or workflow/window params change.

### Sustained paging/notification guard
- A new event is emitted when warning/critical alerts persist for the same trip context across a sustained window.
- Event type: `routing_health_paging_alert`.
- Event details include:
  - `trip_id`
  - `status`
  - `occurrence_index` (current sustained sequence number)
  - `window_minutes`, `min_occurrences`, `workflow`, `workflow_unit_id`
  - `sustained_window_seconds`
  - `paging_cooldown_seconds`
  - `alert_signature` (hash over sustained context)
- Duplicate paging is suppressed per signature for the cooldown window so operators are not re-paged from repeated checks.
- Controls:
  - `ROUTING_HEALTH_ALERT_SUSTAINED_WARNING_THRESHOLD` (default `3`)
  - `ROUTING_HEALTH_ALERT_SUSTAINED_WINDOW_SECONDS` (default `3600`)
  - `ROUTING_HEALTH_ALERT_PAGING_COOLDOWN_SECONDS` (default `3600`)

## Implemented observability/export path
- Warning/critical trips from `GET /api/trips/{trip_id}/agentic-eval` now emit an
  `AuditStore` event with `type == "routing_health_alert"`.
- Event details currently include:
  - `trip_id`
  - `status`
  - `alert_count`
  - `alerts`
  - `checked_at`
  - `metrics_snapshot`
  - `authority`
  - `workflow`
  - `workflow_unit_id`
  - `min_occurrences`
  - `window_minutes`
- Operators can inspect the emitted signals via:
  - `GET /legacy_ops/audit?event_type=routing_health_alert`
  - optional `trip_id=<trip_id>`
  - optional `trip_status=<warning|critical>`

  These server-side filters return only matching events without requiring client-side
  post-processing.

## Implementation evidence in-repo
- Endpoint payload contract tests:
  - `tests/evals/test_agentic_eval_endpoint.py`
- Snapshot/routing health computation:
  - `spine_api/routers/confirmations.py`
  - `src/evals/agentic_feedback.py`
  - `src/evals/audit/public_authority.py`

## What can and should still be done
- Done (2026-07-01): expose a dedicated operator UI panel in `/(agency)/audit` that normalizes `routing_health_alert` and `routing_health_paging_alert` with status/context metadata and raw event payload.
- Done (2026-07-02): add alert triage UX support in `/(agency)/audit` for `routing_health_alert` with acknowledgement/closure/escalate controls and persistent notes.
- Done (2026-07-02): route triage actions to auditable events via `POST /legacy_ops/audit/{event_id}/triage` and `routing_health_alert_triage` log entries.
- Can / Should: batch triage actions and paging suppression controls for sustained warning loops.
  - Implemented: `POST /legacy_ops/audit/routing-health/batch-triage` for multi-alert triage.
  - Implemented: `POST /legacy_ops/audit/{event_id}/suppress-routing-health-paging` for explicit paging suppression.
- Can / Should: automated evidence export for warning/critical trips into operator bundles.
  - Implemented: `GET /legacy_ops/audit/routing-health/export` for JSON and CSV exports with optional paging inclusion.
- Done (2026-07-01): add scheduled paging/notification guard when repeated warning/critical `routing_health_alert` states persist for the same `trip_id` and context.
