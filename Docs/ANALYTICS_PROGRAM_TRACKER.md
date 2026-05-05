# ANALYTICS PROGRAM TRACKER

Last updated: 2026-05-05 (Asia/Kolkata)
Owner: Analytics program (canonical Insights surface)

## 1) Program Charter

Objective:
- Establish truthful, evidence-backed analytics for owner and trip-level insights on the existing Insights surface.

Non-parallel-path rule:
- No new analytics routes/pages/dashboards.
- Existing canonical surface remains `frontend/src/app/(agency)/insights/page.tsx` backed by existing `/analytics/*` endpoints.

Success criteria:
- No fabricated KPI outputs presented as authoritative.
- Weak/estimated/unavailable metrics explicitly labeled in API and UI.
- Baseline and post-change verification recorded with pre-existing vs new regressions separation.

Scope boundaries:
- In scope (Phase A): truth hardening of current Insights outputs.
- Out of scope (Phase A): net-new KPI families requiring new event schema/foundation (agent ranking fairness, advanced response-time SLA decomposition).

## 2) Current State Inventory

Backend analytics endpoints in use:
- `/analytics/summary` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3110))
- `/analytics/pipeline` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3120))
- `/analytics/team` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3130))
- `/analytics/bottlenecks` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3141))
- `/analytics/revenue` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3150))
- `/analytics/alerts` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3180))
- `/analytics/alerts/{alert_id}/dismiss` ([spine_api/server.py](/Users/pranay/Projects/travel_agency_agent/spine_api/server.py:3187))

BFF/proxy mappings in use:
- `/api/insights/summary -> analytics/summary` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:32))
- `/api/insights/pipeline -> analytics/pipeline` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:33))
- `/api/insights/team -> analytics/team` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:34))
- `/api/insights/revenue -> analytics/revenue` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:35))
- `/api/insights/bottlenecks -> analytics/bottlenecks` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:36))
- `/api/insights/alerts -> analytics/alerts` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:39))
- `/api/insights/alerts/{id}/dismiss -> analytics/alerts/{id}/dismiss` ([frontend/src/lib/route-map.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/route-map.ts:136))

Insights UI sections currently rendered:
- Summary stat cards ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:380))
- Pipeline velocity bars ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:424))
- Stage breakdown ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:461))
- Pipeline funnel ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:493))
- Revenue chart ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:507))
- Team performance chart/table ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:522))
- Bottleneck analysis ([frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:587))

Current KPI list with status:

| KPI | Status | Notes |
| --- | --- | --- |
| Total inquiries | tracked | Count from trip list. |
| Converted to booked / conversion rate | partial | Mixes `status == booked` with quality-score heuristic. |
| Avg response time | partial | Explicitly marked unavailable until real response-time events exist. |
| Pipeline value | tracked | Summary now derives active pipeline budget evidence when available; otherwise marked unavailable. |
| Pipeline velocity stage timings | partial | Uses coarse created/updated evidence and marked estimated/unavailable. |
| Stage trip counts | tracked | Status-based counts from trips. |
| Stage avg time / exit metrics | partial | Stage timing uses coarse evidence with status; exit metrics marked unavailable. |
| Team active/completed/conversion/workload | tracked | Derived from assignee and trip status. |
| Team CSAT | partial | Real when ratings exist; otherwise marked unavailable (no imputed 4.5 default). |
| Bottleneck analysis | partial | Derived from observed stage durations when evidence exists; otherwise explicit unavailable state. |
| Revenue metrics (booked/projected/pipeline/near-close) | tracked | Derived from budget value + stage probabilities. |
| Operational alerts | partial | Derived from analytics flags; requires ongoing signal validation. |

## 3) Evidence & Quality Matrix

| KPI | Formula | Source fields | Source path | Confidence | Owner |
| --- | --- | --- | --- | --- | --- |
| Total inquiries | `len(trips)` | trip records | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:32) | evidence-backed | Analytics backend |
| Conversion rate | `(converted/total)*100` | `status`, `analytics.quality_score` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:33) | estimated | Analytics backend |
| Avg response time | fixed `0.0` + explicit status | none (no event timestamps) | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:102) | unavailable | Analytics backend |
| Summary pipeline value | sum active budgets | `packet/extracted.budget.value` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:97) | evidence-backed/unavailable | Analytics backend |
| Revenue pipeline value | sum active trip budget | `packet/extracted.budget.value`, stage/status | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:233) | evidence-backed | Analytics backend |
| Pipeline velocity | coarse duration heuristic (no defaults) | `created_at`, `updated_at` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:73) | estimated/unavailable | Analytics backend |
| Stage avg time/exit | stage timing from coarse durations; exit unavailable | `status`, `created_at`, `updated_at` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:117) | estimated/unavailable | Analytics backend |
| Team conversion/workload | status counts per assignee | `assigned_to`, `status` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:174) | evidence-backed | Analytics backend |
| Team CSAT | mean(feedback.rating) else unavailable | `extracted.feedback.rating` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:195) | evidence-backed/unavailable | Analytics backend |
| Bottleneck stage + causes | max observed stage duration; no fabricated causes | `status`, `created_at`, `updated_at` | [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:222) | estimated/unavailable | Analytics backend |

Explicit weak metrics to harden in Phase A:
- Hardcoded bottleneck output.
- Defaulted/imputed values (`customerSatisfaction=4.5`, stage timings/exit, summary pipeline/response-time heuristics).
- Unavailable response-time path (no reliable event-level response timestamps yet).

## 4) Findings Register

1. Hardcoded bottleneck output removed; now evidence-derived or unavailable.
   - Evidence: [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:222)
2. Non-evidence summary approximations removed; explicit status metadata added.
   - Evidence: [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:102)
3. Stage random placeholders removed; timing marked estimated/unavailable and exit marked unavailable.
   - Evidence: [src/analytics/metrics.py](/Users/pranay/Projects/travel_agency_agent/src/analytics/metrics.py:130)
4. UI bottleneck empty state updated to insufficient-data wording (no “all smooth” claim).
   - Evidence: [frontend/src/app/(agency)/insights/page.tsx](/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/insights/page.tsx:617)
5. FE generated contract synced with new additive fields.
   - Evidence: [frontend/src/types/generated/spine-api.ts](/Users/pranay/Projects/travel_agency_agent/frontend/src/types/generated/spine-api.ts:65)

## 5) Decision Log (Append-Only)

| Timestamp (IST) | Decision | Rationale | Alternatives considered | Impact |
| --- | --- | --- | --- | --- |
| 2026-05-05 | Keep existing Insights surface canonical; harden truth in-place. | Avoid drift and duplicate analytics surfaces. | Create `/analytics-v2` page/route (rejected). | Preserves route/UI continuity and avoids parallel paths. |
| 2026-05-05 | Introduce additive quality metadata (`confidence`/`data_status` class) without breaking endpoint paths. | Needed to mark estimated/unavailable metrics explicitly. | Remove metrics entirely until perfect data (rejected for operational visibility loss). | Enables honest display while preserving API compatibility. |
| 2026-05-05 | Remove all random/fabricated analytics generation in current Insights computations. | Deterministic truthfulness is required for owner decisions. | Keep placeholders with hidden defaults (rejected). | Some KPIs now explicitly unavailable, reducing false confidence. |
| 2026-05-05 | Keep bottleneck causes empty when root-cause evidence is missing. | Suggested actions without causal evidence are fabricated. | Keep static cause text (rejected). | Forces event-foundation work before prescriptive recommendations. |

## 6) Work Queue

### P0
- Remove fabricated bottleneck output or mark unavailable with explicit insufficient-data behavior.
  - Acceptance:
    - [x] No fixed/static bottleneck causes returned.
    - [x] API differentiates evidence-backed vs unavailable bottleneck state.
    - [x] UI empty state text no longer asserts healthy flow without evidence.
- Label default/imputed metrics as estimated/unavailable in API + UI.
  - Acceptance:
    - [x] Summary/stage/team fields carrying fallback values include status metadata.
    - [x] UI renders non-authoritative labels for estimated/unavailable data.

### P1
- Contract sync for frontend generated types to include new additive metadata fields.
  - Acceptance:
    - [x] `frontend/src/types/generated/spine-api.ts` includes new fields.
    - [x] Typecheck/tests pass.

### P2
- Replace conversion heuristic coupling (`quality_score > 80`) with explicit booked-state policy after product decision.

### P3
- Phase B/C/D roadmap execution (stabilized stage event contracts, KPI breadth, task-event foundation).

Dependency order:
1. P0 truth hardening
2. P1 type/contract sync
3. P2 conversion policy decision
4. P3 roadmap phases

## 7) Verification Ledger

Baseline snapshots (before Phase A code changes):
- Backend full suite:
  - Command: `uv run pytest -q`
  - Result: `4 failed, 1595 passed, 9 skipped`
  - Pre-existing failures:
    - `tests/test_rate_limiter.py::TestRateLimitMiddlewareRegistration::test_auth_router_has_7_routes`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_file_tripstore_write_blocked_in_dogfood_when_pii_present`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_file_tripstore_update_blocked_in_dogfood_for_existing_real_pii`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_file_tripstore_allows_empty_analytics_updates`
- Frontend targeted analytics/drilldown/workload:
  - Command: `npm test -- --run src/lib/__tests__/workload-normalization.test.ts src/components/visual/__tests__/TeamPerformanceChart.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/app/__tests__/e2e_metric_drilldown.test.tsx`
  - Result: `4 files passed, 25 tests passed`

Post-change snapshots:
- Backend targeted analytics tests:
  - Command: `uv run pytest -q tests/test_analytics_truth_hardening.py tests/test_team_metrics_contract.py tests/test_revenue_analytics.py`
  - Result: `17 passed`
- Frontend targeted analytics/drilldown/workload:
  - Command: `npm test -- --run src/lib/__tests__/workload-normalization.test.ts src/components/visual/__tests__/TeamPerformanceChart.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/app/__tests__/e2e_metric_drilldown.test.tsx`
  - Result: `4 files passed, 25 tests passed`
- Backend full suite (post-change):
  - Command: `uv run pytest -q`
  - Result: `4 failed, 1601 passed, 9 skipped`
  - New regressions vs baseline: `none`
  - Pre-existing failures unchanged (same 4):
    - `tests/test_rate_limiter.py::TestRateLimitMiddlewareRegistration::test_auth_router_has_7_routes`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_round_trip_preserves_all_compartments`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_file_store_preserves_frontier_result`
    - `tests/test_state_contract_parity.py::TestFileTripStoreParity::test_file_store_preserves_fees`

## 8) Future Roadmap

Phase B — Contract stabilization:
- Align generated FE/BE analytics contracts with explicit metric quality semantics.
- Remove drift between model additions and generated frontend types.

Phase C — KPI expansion:
- Add owner/trip-level KPIs once evidence paths exist (response-time decomposition, stage SLA variance, owner intervention outcomes).
- Explicit KPI governance for `tracked / partial / missing / placeholder`.

Phase D — Task-event foundation:
- Add durable event model for response and lifecycle timing to support unbiased throughput/latency metrics.
- Gate agent ranking/scorecards on fairness policy + complete event capture.
