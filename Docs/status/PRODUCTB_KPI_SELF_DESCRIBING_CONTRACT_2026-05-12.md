# Product B KPI Self-Describing Contract

Date: 2026-05-12  
Status: Complete for backend KPI response contract  
Scope: Product B KPI endpoint payload semantics, no frontend changes

## Context

The next-feature prioritization review selected Product B action-packet and KPI closure as the highest-leverage next work. Fresh code review showed much of Product B Phase 0 was already implemented:

- `spine_api/product_b_events.py` validates and stores the v1 Product B event schema.
- `spine_api/routers/product_b_analytics.py` serves `GET /analytics/product-b/kpis`.
- `tests/test_product_b_events.py` already covered event validation, deduplication, qualified filtering, public-checker event ingestion, KPI auth failures, and observed/inferred/unknown outcome buckets.
- `Docs/status/PRODUCT_B_WEDGE_AND_SERVER_PHASE0_COMPLETION_2026-05-07.md` records the earlier Phase 0 completion sweep.

Remaining gap from `Docs/NEXT_STEPS_PRODUCTB_WEDGE_EXECUTION_2026-05-07.md`: KPI definitions needed to be unambiguous and tied to numerator, denominator, window, and data source. Before this change, `compute_kpis()` returned metric values but the formula contract lived only in docs and code.

## Decision

Add a `definitions` block to `ProductBEventStore.compute_kpis()` output.

The block includes:

- `qualified_sample_rule`
  - required events
  - excluded traffic categories
  - current enforcement status
- `kpis`
  - description
  - numerator
  - denominator
  - aggregation
  - selected `window_days`
  - data source label

This keeps `/analytics/product-b/kpis` self-describing without creating a second analytics route or parallel metric system.

## Why This Is Long-Term Safe

- It is additive to the existing response payload.
- Existing KPI values and event math are unchanged.
- The data source label remains logical (`data/product_b_events/events_normalized.jsonl`) even when tests monkeypatch the store into a temp directory.
- It supports future frontend/admin reporting surfaces without requiring each consumer to re-encode formula meanings.

## Files Changed

- `spine_api/product_b_events.py`
  - Added `NORMALIZED_DATA_SOURCE_LABEL`.
  - Added `_kpi_definitions(window_days=...)`.
  - Included `definitions` in `compute_kpis()` output.
- `tests/test_product_b_events.py`
  - Added a regression test that verifies KPI definitions and the qualified sample rule.

## Verification

TDD red/green:

```bash
uv run pytest -q tests/test_product_b_events.py::test_compute_kpis_returns_formula_definitions_and_sample_rule
# Red before implementation: KeyError: 'definitions'
# Green after implementation: 1 passed
```

Targeted Product B/public-checker regression:

```bash
uv run pytest -q tests/test_product_b_events.py tests/test_product_b_analytics_router_behavior.py tests/test_public_checker_agency_config.py tests/test_public_checker_path_safety.py
# 23 passed in 3.11s
```

## Follow-Up

- Wire frontend/Product B reporting surfaces to display definitions alongside values when useful.
- Add explicit `response_model` for `/analytics/product-b/kpis` if/when the analytics contract becomes public-facing.
- Enforce richer qualified-sample exclusions (`internal_test_traffic`, insufficient input quality, missing real trip intent) once those signals are recorded in events instead of only documented.

## Additional Same-Day Hardening (API Contract)

Queued TODO #2 from `Docs/NEXT_STEPS_PRODUCTB_WEDGE_EXECUTION_2026-05-07.md` called out API-level tests for `/api/public-checker/run`.
This pass added malformed payload coverage for that route to ensure request-shape validation stays explicit:

- rejects non-object JSON body payloads
- rejects `structured_json` when it is not an object
- rejects non-string `raw_note`
- rejects non-boolean `retention_consent`

Files updated:

- `tests/test_product_b_events.py`

Verification refresh:

```bash
uv run pytest -q tests/test_product_b_events.py tests/test_product_b_analytics_router_behavior.py tests/test_public_checker_agency_config.py tests/test_public_checker_path_safety.py
# 27 passed in 4.05s
```

Cross-slice verification (with legacy-ops extraction behavior guardrails):

```bash
uv run pytest -q \
  tests/test_legacy_ops_router_behavior.py \
  tests/test_product_b_events.py \
  tests/test_product_b_analytics_router_behavior.py \
  tests/test_public_checker_agency_config.py \
  tests/test_public_checker_path_safety.py
# 30 passed in 7.86s
```

## Additional Same-Day Hardening (Failure And Consent Boundaries)

The next Product B/public-checker backlog item was runtime failure behavior and consent-boundary persistence for `/api/public-checker/run`.

Changes:

- `spine_api/services/public_checker_service.py`
  - Preserves missing `decision_state` as `None` instead of serializing it to the invalid enum string `"None"`.
- `tests/test_product_b_events.py`
  - Added HTTP-level coverage that internal runtime failures return the generic `500` detail and do not leak sensitive exception text.
  - Added service-level coverage that `retention_consent=false` redacts `raw_note`, `owner_note`, `itinerary_text`, and `structured_json` from the persisted `meta.submission`.
- `tests/test_live_checker_service.py`
  - Isolated the manifest-fallback authority test from the generated D6 snapshot by setting `D6_AUDIT_GATE_SNAPSHOT_PATH` to a missing file.

Why the service fix matters:

- The public checker may receive a valid run result without a decision state in mocked, partial, or degraded paths.
- `RunStatusResponse.decision_state` is optional, so absence should remain `None`.
- Serializing absence as `"None"` caused response-model validation to fail and masked the successful run as a generic `500`.

Verification:

```bash
uv run pytest -q \
  tests/test_product_b_events.py \
  tests/test_product_b_analytics_router_behavior.py \
  tests/test_public_checker_agency_config.py \
  tests/test_public_checker_path_safety.py \
  tests/test_live_checker_service.py \
  tests/test_public_checker_contract_authority.py
# 38 passed in 19.00s
```

## Additional Same-Day Hardening (Qualified Sample Enforcement)

Task 0.3 from `Docs/NEXT_STEPS_PRODUCTB_WEDGE_EXECUTION_2026-05-07.md` requires kill tests to use qualified samples only. Before this pass, the backend only required event presence (`intake_started` plus `first_credible_finding_shown`) and did not enforce the documented exclusions.

Changes:

- `spine_api/product_b_events.py`
  - Added explicit exclusion handling for `intake_started.properties.internal_test_traffic=true`.
  - Added explicit exclusion handling for `intake_started.properties.sufficient_input_quality=false`.
  - Added explicit exclusion handling for `intake_started.properties.real_trip_intent=false`.
  - Added `sample.excluded_inquiries` counters to KPI output.
  - Updated KPI definitions to report `current_enforcement=event_presence_plus_explicit_exclusions`.
- `tests/test_product_b_events.py`
  - Added coverage proving qualified-only KPIs exclude internal test traffic, insufficient input quality, and missing real trip intent while preserving backwards compatibility for events without those optional signals.

Verification:

```bash
uv run pytest -q \
  tests/test_product_b_events.py \
  tests/test_product_b_analytics_router_behavior.py \
  tests/test_public_checker_agency_config.py \
  tests/test_public_checker_path_safety.py \
  tests/test_live_checker_service.py \
  tests/test_public_checker_contract_authority.py
# 39 passed in 15.87s
```
