# Random Document Audit Report: Task Management Analytics

Date checked: 2026-05-04

Chosen document: `frontend/docs/TASK_MGMT_04_ANALYTICS.md`

Selection method: real random selection with `shuf -n 1` over 1,005 feature-adjacent repo documents from `Docs/product_features`, `frontend/docs`, `specs`, `Docs/architecture`, `Docs/design`, `.kiro/specs`, `data`, and `notebooks`.

No durable implementation was performed. This report is the durable discussion and handoff artifact.

## 1. Document Inventory

Inventory command:

```bash
find Docs/product_features frontend/docs specs Docs/architecture Docs/design .kiro/specs data notebooks -type f \( -iname '*.md' -o -iname 'README.md' -o -iname 'TODO*' -o -iname 'ROADMAP*' -o -iname 'ADR*' \) -print 2>/dev/null | sort
```

Candidate count: 1,005 feature-adjacent repository documents.

| Doc ID | Path | Type | Why it may matter |
| --- | --- | --- | --- |
| DOC-001 | `.kiro/specs/component-adaptation/design.md` | spec | Workspace/component implementation surface |
| DOC-002 | `Docs/architecture/adr/ADR-006-MULTI-AGENT-RUNTIME_2026-05-04.md` | ADR | Current multi-agent runtime architecture |
| DOC-003 | `Docs/product_features/AI_AGENT_TEAM_ORCHESTRATOR.md` | product feature | Agentic operations direction |
| DOC-004 | `Docs/product_features/CRISIS_ORCHESTRATION_DASHBOARD.md` | product feature | Operational command-center concept |
| DOC-005 | `data/fixtures/TEST_SUITE_README.md` | test docs | Fixture/test boundary |
| DOC-006 | `frontend/docs/TASK_MANAGEMENT_MASTER_INDEX.md` | feature docs | Task-management index and roadmap |
| DOC-007 | `frontend/docs/TASK_MGMT_01_TRACKING.md` | feature docs | Task data model and tracking assumptions |
| DOC-008 | `frontend/docs/TASK_MGMT_02_ASSIGNMENT.md` | feature docs | Assignment/routing assumptions |
| DOC-009 | `frontend/docs/TASK_MGMT_03_AUTOMATION.md` | feature docs | Automation/task generation assumptions |
| DOC-010 | `frontend/docs/TASK_MGMT_04_ANALYTICS.md` | feature docs | Selected task analytics and performance-measurement doc |

Code comment inventory command:

```bash
rg -n "TODO|FIXME|HACK|NOTE|XXX" --glob '!node_modules/**' --glob '!frontend/node_modules/**' --glob '!.venv/**' --glob '!tools/node_modules/**' .
```

Relevant hits included:

- `spine_api/server.py:2071` has a TODO to replace bounded inbox stats with DB-level aggregations.
- `frontend/src/app/(agency)/trips/page.tsx:13` has a TODO to move trip filtering to shared domain code.
- `Docs/CODE_QUALITY_AUDIT_2026-04-28.md:104` names prior TODOs around LLM health and spine pipeline calls.

## 2. Random Selection

```text
Chosen document: frontend/docs/TASK_MGMT_04_ANALYTICS.md
Selection method: real random method, `shuf -n 1`
Why this doc is worth auditing: it is feature-related, touches live analytics/workload/SLA surfaces, and has obvious product, privacy, fairness, and anti-gaming implications.
```

## 3. Chosen Document Deep Analysis

| Doc Item ID | Type | Short evidence | Location | Interpretation | Confidence |
| --- | --- | --- | --- | --- | --- |
| D-001 | Question | measure individual agent productivity fairly | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:7-14` | Fairness and anti-gaming are first-class product questions. | High |
| D-002 | Current/Intended-State Claim | `AgentPerformanceMetrics` includes productivity, quality, timeliness, customer, collaboration, growth | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:21-31` | Intended balanced scorecard contract. | High |
| D-003 | Intended-State Claim | productivity includes tasks, trips, revenue, completion time, tasks/day, active trips | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:33-42` | Requires task-native and trip-native facts. | High |
| D-004 | Intended-State Claim | quality metrics include revision rate, booking error rate, complaints, compliance, peer review | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:44-51` | Requires quality event taxonomy and review/complaint data. | High |
| D-005 | Intended-State Claim | timeliness includes on-time completion, overdue hours, SLA compliance, response times | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:53-59` | Requires timestamped task/message events. | High |
| D-006 | Privacy/PII/Data Claim | customer metrics include CSAT, NPS, retention, upsell conversion | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:61-67` | Touches customer feedback and commercial data. | High |
| D-007 | Architecture Claim | balanced scorecard, not single productivity target | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:69-76` | Metric integrity principle. | High |
| D-008 | Intended-State Claim | dashboard has utilization, active/overdue/at-risk tasks, workload, SLA, bottlenecks, trends | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:78-101` | Dashboard scope is broader than current trip insights. | High |
| D-009 | Intended-State Claim | `AgentWorkloadEntry` statuses available/at_capacity/overloaded | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:103-112` | Different contract than current workload API. | High |
| D-010 | Intended-State Claim | bottlenecks include visa, supplier, payment, overload, skill shortage, approval delay, document generation | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:114-130` | Requires causal classification not currently present. | High |
| D-011 | UX Claim | real-time, daily, weekly, monthly dashboard views | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:132-137` | Multi-granularity dashboard requirement. | High |
| D-012 | Architecture Claim | task analytics query union | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:139-152` | Requires query layer or typed analytics endpoint family. | High |
| D-013 | UX/Analytics Claim | examples for visa processing, booking errors, SLA trend, payment delays, agent comparison | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:154-160` | Concrete query expectations. | High |
| D-014 | Operational Safety Claim | anti-gaming: scorecard, peer review, customer validation, time tracking, anomaly detection | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:163-202` | Enforcement design needed before using metrics as performance controls. | High |
| D-015 | Explicit Task | design balanced scorecard | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Work candidate. | High |
| D-016 | Explicit Task | build operational dashboard | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Partially stale because an insights dashboard exists. | High |
| D-017 | Explicit Task | create task analytics query framework | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Missing as task-native framework. | High |
| D-018 | Explicit Task | design anti-gaming measures | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Missing as canonical guardrail. | High |
| D-019 | Explicit Task | study workforce analytics best practices | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Needs external research before scoring design. | High |
| D-020 | Question | metric fairness, attribution, leading indicators, seasonality, qualitative assessment | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:206-217` | Product/architecture decisions required before durable implementation. | High |
| D-021 | Stale/Unknown | `MetricPeriod`, `CollaborationMetrics`, `GrowthMetrics`, `MetricAudit` referenced but not defined | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:21-31`, `frontend/docs/TASK_MGMT_04_ANALYTICS.md:166-169` | Contract sample is not implementation-ready. | High |
| D-022 | Contradiction | `document_generation` union member comment contains the semicolon | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:123-130` | Sample type syntax is suspect. | Medium |

## 4. Extracted Task Candidates

| Task Candidate ID | Source Doc Item IDs | Task | Explicit or Implicit | Why this is a task | Expected repo area | Initial priority guess |
| --- | --- | --- | --- | --- | --- | --- |
| TC-001 | D-002, D-007, D-015, D-020 | Define a canonical balanced-scorecard contract and fairness policy. | Explicit | Current analytics have a partial team metric model but no scorecard policy. | `src/analytics`, `frontend/src/types`, `Docs/` | P1 |
| TC-002 | D-008, D-011, D-016 | Reconcile existing Insights page with task-management dashboard scope. | Explicit | Existing dashboard is trip/owner analytics, not task-native analytics. | `frontend/src/app/(agency)/insights`, backend analytics routes | P1 |
| TC-003 | D-012, D-013, D-017 | Create task analytics query framework or formal design contract. | Explicit | Doc has query examples, code has fixed endpoint family. | `src/analytics`, `spine_api/server.py`, `frontend/src/lib/governance-api.ts` | P2 |
| TC-004 | D-014, D-018 | Design and test metric-integrity/anti-gaming controls. | Explicit | Metrics can become harmful if used without integrity model. | analytics, audit, assignment, review systems | P1 |
| TC-005 | D-003, D-004, D-005, D-010 | Establish canonical task event schema before deriving metrics. | Implicit | Most proposed metrics need task events that are not present as a canonical model. | task management models/routes/events | P1 |
| TC-006 | D-006, D-020 | Define privacy/data classification for employee performance and customer metric data. | Implicit | Team performance and customer feedback are sensitive internal data. | Docs, auth/permissions, analytics payloads | P1 |
| TC-007 | D-008, D-009 | Align workload contracts across backend, frontend type, and tests. | Implicit | `/api/team/workload` returns snake_case rows, frontend type expects camelCase enriched rows. | `spine_api/server.py`, `frontend/src/types/governance.ts`, tests | P2 |
| TC-008 | D-010 | Replace fixed bottleneck output with evidence-derived bottlenecks or label as demo. | Implicit | Current bottleneck computation returns a hard-coded cause. | `src/analytics/metrics.py`, tests, UI labels | P1 |
| TC-009 | D-019 | Perform external best-practices research before scorecard design. | Explicit | Contact center/workforce analytics norms are external. | Docs/research | P2 |
| TC-010 | D-016 | Wire or remove/label export affordance in Insights page. | Implicit | Existing UI has export button with no observed handler. | `frontend/src/app/(agency)/insights/page.tsx`, export API | P3 |
| TC-011 | D-012 | Verify and protect metric drill-down routing. | Implicit | Drilldown is implemented as explicit BFF route, not catch-all route-map. | `frontend/src/app/api/insights/agent-trips/route.ts`, route-map tests | P3 |

## 5. Static Codebase Reality Check

| Task Candidate ID | Codebase Status | Evidence | What exists today | Gap | Actual Work Needed |
| --- | --- | --- | --- | --- | --- |
| TC-001 | Partially Done | `src/analytics/models.py:50-60`; `src/analytics/metrics.py:135-217`; `tests/test_team_metrics_contract.py:1-133` | Team metrics include active/completed trips, conversion, avg response unavailable, CSAT default, workload score. | No balanced scorecard, no fairness normalization, no collaboration/growth. | Design canonical scorecard policy and add model/test coverage before UI expansion. |
| TC-002 | Partially Done / Stale Doc | `frontend/src/app/(agency)/insights/page.tsx:296-315`, `frontend/src/app/(agency)/insights/page.tsx:335-620`; `spine_api/server.py:3110-3184` | Live Insights page and backend summary/pipeline/team/bottleneck/revenue/alert endpoints. | It is trip/owner analytics, not the task dashboard from the doc. | Reconcile doc with current implementation; avoid parallel dashboard. |
| TC-003 | Missing | Search: `rg -n "TaskAnalyticsQuery|average_time_to_complete|task_distribution|automation_effectiveness|cost_per_task"` found only docs. | Fixed API endpoints exist: summary, pipeline, team, bottlenecks, revenue, alerts. | No typed task query framework. | Start with design contract; implement only after task event schema exists. |
| TC-004 | Missing / Partial | `src/analytics/logger.py:301-312`; `spine_api/services/routing_service.py:57-78`; `frontend/docs/TASK_MGMT_04_ANALYTICS.md:177-202` | There is anomaly logging machinery and routing handoff history. | No metric-integrity audit model, peer review randomization, customer validation, or anti-gaming policy. | Design integrity layer tied to audit events and data provenance. |
| TC-005 | Missing / Duplicated Assignment Paths | `spine_api/routers/assignments.py:1-20`; `spine_api/services/routing_service.py:1-20`; `spine_api/persistence.py:887-960`; `spine_api/server.py:2036-2060`, `spine_api/server.py:3894-3923` | There is SQL routing state machine plus legacy JSON `AssignmentStore` and inbox assignment updating TripStore. | No single canonical task event store; assignment data is split across paths. | Define task event source of truth and bridge existing assignment paths without duplicating routes. |
| TC-006 | DataBoundaryRisk / Needs Product Decision | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:44-67`; `src/analytics/models.py:50-60`; `frontend/src/app/(agency)/insights/page.tsx:199-253` | Employee/team performance and customer satisfaction are rendered to owner insights. | No explicit privacy/data-classification policy for employee performance metrics in inspected code/docs. | Define access, retention, redaction, export, and fairness policy before richer metrics. |
| TC-007 | Contradictory Evidence | Backend: `spine_api/server.py:3894-3923`; frontend type: `frontend/src/types/governance.ts:111-120`; frontend test adapter: `frontend/src/lib/__tests__/workload-normalization.test.ts:1-143` | Backend emits `member_id`, no `loadPercentage/status`; type expects `memberId`, `loadPercentage`, `status`; test has local normalization helper only. | Normalization is not a shared production helper in the inspected files. | Move normalization into production code or change API/type contract. |
| TC-008 | FalsePositiveRisk / Partially Done | `src/analytics/metrics.py:220-237`; `frontend/src/app/(agency)/insights/page.tsx:258-289` | `compute_bottlenecks` always returns one fixed “Missing Budget Clarification” bottleneck. | UI presents it as live analysis. | Either compute from real stage/task evidence or label/demo-gate it. |
| TC-009 | Needs Research | `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226` | Research task exists in doc. | No current external research performed in this audit. | Run external workforce analytics research before designing scorecard thresholds. |
| TC-010 | Partially Done | Button: `frontend/src/app/(agency)/insights/page.tsx:365-367`; API: `spine_api/server.py:4318-4331`; client references in `frontend/src/lib/governance-api.ts` around export functions were observed by search. | Export backend/client surface appears to exist. | Button has no handler in inspected page. | Wire export safely or remove/disable with clear state. |
| TC-011 | Already Done / Minor Risk | BFF route: `frontend/src/app/api/insights/agent-trips/route.ts:23-64`; backend route: `spine_api/server.py:3159-3177`; route-map deny test: `frontend/src/lib/__tests__/route-map.test.ts:22-28` | Explicit Next API route proxies drilldown; route-map intentionally excludes it. | Backend returns raw trip dicts, while drawer expects mapped fields. Existing tests mock expected frontend shape. | If expanding drilldown, verify real response shape and add contract mapping tests. |

## 6. Dynamic Verification and Test Baseline

Baseline command:

```bash
uv run pytest -q
```

Baseline result:

```text
16 failed, 1575 passed, 9 skipped, 3 warnings in 182.95s
```

Pre-existing failures observed before any probe or implementation:

- `tests/test_booking_collection.py::TestPublicCustomerEndpoints::test_public_form_valid_token` and `test_public_form_no_pii_in_summary`: `NameError: _safe_fact_value is not defined` at `spine_api/server.py:2888`.
- `tests/test_call_capture_e2e.py::TestCallCaptureFollowUpDueDate::test_save_processed_trip_persists_public_checker_artifacts`: failure in public-checker artifact persistence path.
- Six `tests/test_phase3_suitability_api.py` failures.
- Two `tests/test_privacy_guard.py` failures, including `SQLTripStore requires agency_id`.
- `tests/test_rate_limiter.py::TestRateLimitMiddlewareRegistration::test_auth_router_has_7_routes`: expected 7 auth routes, got 9.
- Three `tests/test_review_logic.py` failures and one `tests/test_review_policy_escalation.py` failure: direct JSON test setup is invisible under current `TripStore` backend.

Targeted backend command:

```bash
uv run pytest -q tests/test_team_metrics_contract.py tests/test_revenue_analytics.py tests/test_routing_state_machine.py
```

Targeted backend result:

```text
29 passed in 6.04s
```

First frontend targeted command was incorrectly run from `frontend/` with repo-root paths and found no files. Corrected command:

```bash
npm test -- --run src/lib/__tests__/workload-normalization.test.ts src/components/visual/__tests__/TeamPerformanceChart.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/app/__tests__/e2e_metric_drilldown.test.tsx
```

Corrected frontend result:

```text
4 files passed, 25 tests passed
```

No proof-of-concept code changes were made, so there are no new regressions to compare against baseline.

## 7. Critical Implementation and Test Traps Checked

Environment/config loading:

- `TripStore._backend()` reads `TRIPSTORE_BACKEND` at call time, not import time: `spine_api/persistence.py:720-727`. This is good for runtime configurability but creates test contamination if tests assume file-backed direct JSON writes while `.env` or process env points to SQL.
- `frontend/src/app/api/insights/agent-trips/route.ts:4` stores `SPINE_API_URL` at module import time. This is typical for Next route modules but tests that mutate `process.env.SPINE_API_URL` after import need module reset.
- `spine_api/server.py:76-77`, `spine_api/server.py:246-247`, and `spine_api/server.py:311-323` have module-level environment reads for OTEL, agent work coordinator, host/port, and strict traveler-safe mode. These were not directly implicated by the chosen doc but are config-cache risks for tests.

State leakage/test isolation:

- Baseline failures show tests that write direct JSON trip files under `tmp_path` can fail when `TripStore` uses SQL backend. Evidence: `src/analytics/review.py:66` raises `KeyError` in review tests, and `spine_api/persistence.py:720-727` selects backend by `TRIPSTORE_BACKEND`.
- `AssignmentStore` is still file-backed and module-level: `spine_api/persistence.py:887-960`. `/api/team/workload` reads it directly at `spine_api/server.py:3901`, while SQL routing state exists separately in `spine_api/routers/assignments.py:1-20`.

Write paths:

- Assignment write paths are split:
  - Inbox assignment mutates `TripStore.update_trip`: `spine_api/server.py:2036-2060`.
  - SQL routing state machine mutates `TripRoutingState`: `spine_api/services/routing_service.py:97-293`.
  - Legacy `AssignmentStore.assign_trip` writes JSON assignments: `spine_api/persistence.py:912-932`.
- Any task analytics implementation that counts assignments, response time, SLA, or workload must define the canonical write path first.

Duplicate/parallel-route risk:

- The codebase has both `/api/assignments/...` router routes and older assignment surfaces in `spine_api/server.py`. This is not automatically wrong because they serve different current workflows, but task analytics must not build a third path.

## 8. Data, Privacy, and PII Boundary Checks

Relevant because the selected doc touches customer satisfaction, complaints, NPS, retention, revenue, peer review, time tracking, and individual employee performance.

Findings:

- Employee performance data is sensitive internal operational data. The doc proposes individual productivity, booking errors, peer review score, customer complaint rate, and time tracking at `frontend/docs/TASK_MGMT_04_ANALYTICS.md:33-67`.
- Current UI displays agent name, active trips, workload, conversion, response time, and CSAT in an owner insights page: `frontend/src/app/(agency)/insights/page.tsx:199-253` and `frontend/src/app/(agency)/insights/page.tsx:561-584`.
- Current `compute_team_metrics` defaults CSAT to `4.5` when no ratings exist: `src/analytics/metrics.py:187-215`. This can be misleading if shown as real performance.
- Export affordance exists in the UI at `frontend/src/app/(agency)/insights/page.tsx:365-367`. Exporting employee/customer metric data needs explicit data classification, access control, and retention rules.

Privacy checklist status:

- Save/update PII guard behavior is out of scope for this selected doc, but the full suite currently has privacy guard failures, so privacy guardrails are not globally green.
- For future metric implementation: classify employee performance metrics, customer feedback metrics, revenue metrics, and audit/time-tracking records before adding exports or broader views.
- Rollback/kill switch: no specific metric-enforcement kill switch exists because anti-gaming/enforcement is not implemented.

## 9. Deduped Issue / Task Register

## ISSUE-001: Task Analytics Needs a Canonical Event Model Before More Metrics

Category:
- architecture / data-boundary / reliability / tests

Origin:
- Implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:33-67`, `frontend/docs/TASK_MGMT_04_ANALYTICS.md:139-160`
- Related doc items: D-003, D-004, D-005, D-010, D-012, D-013

Codebase Evidence:
- `spine_api/server.py:2036-2060` - inbox assignment writes `assigned_to_id` and status into TripStore.
- `spine_api/services/routing_service.py:97-293` - routing state machine writes SQL `TripRoutingState` and handoff history.
- `spine_api/persistence.py:912-932` - legacy `AssignmentStore.assign_trip` writes JSON assignment records.
- `spine_api/server.py:3894-3923` - workload endpoint reads JSON `AssignmentStore`, not SQL routing state.

Static Verification:
- No canonical task event model was found for task completion timestamps, task type, revision events, booking error events, customer responses, or time tracking.

Dynamic Verification:
- Baseline command: `uv run pytest -q`
- Baseline result: 16 failed, 1575 passed, 9 skipped.
- Targeted command: `uv run pytest -q tests/test_team_metrics_contract.py tests/test_revenue_analytics.py tests/test_routing_state_machine.py`
- Targeted result: 29 passed.
- New failures vs baseline: none, no code changes.

Current Behavior:
- Analytics are mostly trip-level, roster-level, and assignment-adjacent.

Expected Behavior / Decision Needed:
- Decide whether task analytics are task-native, trip-native, or a layered model where task events roll up to trip and team metrics.

Gap:
- Metrics in the doc require source events that are not yet canonical.

Impact:
- Building scorecards or dashboards now risks false precision and duplicate data paths.

Risk:
- High architecture risk if implemented as a parallel analytics stack.

Confidence:
- High

Acceptance Criteria:
- [ ] A canonical task event schema exists and names source-of-truth write paths.
- [ ] Existing assignment/routing/inbox paths are mapped to that schema or explicitly out of scope.
- [ ] Tests cover save/update/assignment/reassignment/completion/revision event creation.

Test Plan:
- Automated: routing state tests, task event model tests, workload aggregation tests.
- Manual: create/assign/reassign/complete a trip and inspect task event rollup.

Rollback / Kill Switch:
- Keep new task analytics read-only until event capture is proven.

Open Questions:
- Should tasks be first-class persisted records or derived from trip/routing/audit events?

## ISSUE-002: Existing Insights Dashboard Is Partial, Not the Task Management Dashboard

Category:
- UX / architecture / docs

Origin:
- Explicit and stale/partial
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:78-137`, `frontend/docs/TASK_MGMT_04_ANALYTICS.md:220-226`
- Related doc items: D-008, D-011, D-016

Codebase Evidence:
- `frontend/src/app/(agency)/insights/page.tsx:296-315` - page fetches summary, pipeline, team, bottleneck, revenue, alerts.
- `frontend/src/app/(agency)/insights/page.tsx:335-620` - UI renders stat cards, velocity, stage breakdown, revenue, team performance, bottlenecks.
- `spine_api/server.py:3110-3184` - backend exposes analytics summary/pipeline/team/bottlenecks/revenue/alerts.

Static Verification:
- Dashboard exists, but its data model does not include `TaskDashboard` fields such as active tasks, overdue tasks, task volume trend, completion rate trend, and SLA compliance report.

Dynamic Verification:
- Frontend targeted tests: 25 passed.
- Backend targeted tests: 29 passed.

Current Behavior:
- Owner Insights page exists and is live against backend endpoints.

Expected Behavior / Decision Needed:
- Treat current page as owner/trip analytics and extend it only through canonical task-event data, or explicitly rename/scope it.

Gap:
- Doc next step “build dashboard” is stale unless scoped to task-native additions.

Impact:
- Without reconciliation, future agents may build a parallel dashboard.

Risk:
- Medium to high duplicate-product-surface risk.

Confidence:
- High

Acceptance Criteria:
- [ ] Update docs to state current Insights surface and remaining task-native gaps.
- [ ] No new dashboard route is created for the same owner/team analytics resource.
- [ ] Any new task analytics is an additive section fed by canonical data.

Test Plan:
- Automated: route-map/proxy tests and page component tests.
- Manual: inspect Insights page with backend running.

Rollback / Kill Switch:
- Feature-flag task-native sections until data quality is validated.

Open Questions:
- Should the existing Insights page become the single analytics command center?

## ISSUE-003: Bottleneck Analysis Is Hard-Coded But Presented as Live

Category:
- reliability / UX / analytics

Origin:
- Implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:114-130`
- Related doc items: D-010

Codebase Evidence:
- `src/analytics/metrics.py:220-237` - `compute_bottlenecks` returns a fixed decision-stage bottleneck with fixed cause and counts.
- `frontend/src/app/(agency)/insights/page.tsx:258-289` - bottleneck card renders the result as operational analysis.
- `spine_api/server.py:3141-3147` - endpoint returns `compute_bottlenecks(trips)`.

Static Verification:
- No evidence-derived bottleneck logic was found for visa, supplier, payment, overload, skill shortage, approval delay, or document generation.

Dynamic Verification:
- Targeted backend suite passed but does not include bottleneck tests.

Current Behavior:
- A fixed bottleneck can appear even if actual data does not support it.

Expected Behavior / Decision Needed:
- Either compute bottlenecks from real task/stage evidence or mark the section as unavailable/demo until data exists.

Gap:
- False-positive operational insight risk.

Impact:
- Operators may chase nonexistent causes.

Risk:
- Medium product trust risk.

Confidence:
- High

Acceptance Criteria:
- [ ] Empty/no-data trips produce no bottlenecks or an honest unavailable state.
- [ ] Bottlenecks cite source counts and stage/task evidence.
- [ ] Tests cover empty, no-bottleneck, and real-bottleneck cases.

Test Plan:
- Automated: unit tests for `compute_bottlenecks`.
- Manual: compare UI output against known seeded trips.

Rollback / Kill Switch:
- Hide or label the section if evidence thresholds are not met.

Open Questions:
- What minimum evidence threshold should be required before showing a bottleneck?

## ISSUE-004: Workload Contract Normalization Exists Only in Test Helper

Category:
- frontend / API contract / tests

Origin:
- Implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:103-112`
- Related doc items: D-009

Codebase Evidence:
- `spine_api/server.py:3894-3923` - backend returns `member_id`, `capacity`, `assigned`, `available`.
- `frontend/src/types/governance.ts:111-120` - frontend `WorkloadDistribution` expects `memberId`, `loadPercentage`, `status`.
- `frontend/src/lib/__tests__/workload-normalization.test.ts:1-143` - normalization helper exists inside test file only.

Static Verification:
- No production `normalizeWorkload` helper was found in inspected frontend code.

Dynamic Verification:
- Frontend targeted tests passed, but the workload-normalization test validates a local test helper rather than production code.

Current Behavior:
- Potential mismatch between real backend response and frontend type unless another uninspected layer handles normalization.

Expected Behavior / Decision Needed:
- Put normalization in production code or make backend return the frontend contract.

Gap:
- Tests can pass while production type assumptions drift.

Impact:
- Runtime UI bugs or silent missing fields in workload distribution.

Risk:
- Medium contract risk.

Confidence:
- Medium-high

Acceptance Criteria:
- [ ] Production API client or backend returns a single verified `WorkloadDistribution` shape.
- [ ] Test imports the production normalizer or validates real endpoint response shape.

Test Plan:
- Automated: frontend unit test imports production normalizer; backend contract test for `/api/team/workload`.
- Manual: call `/api/team/workload` through BFF and inspect actual JSON.

Rollback / Kill Switch:
- Keep existing UI unchanged until contract is verified.

Open Questions:
- Should normalization live in backend, BFF, or frontend client?

## ISSUE-005: Team Performance Metrics Need Data Classification and Fairness Policy

Category:
- privacy / data-boundary / product-decision / operational-safety

Origin:
- Explicit and implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:44-67`, `frontend/docs/TASK_MGMT_04_ANALYTICS.md:177-202`, `frontend/docs/TASK_MGMT_04_ANALYTICS.md:206-217`
- Related doc items: D-004, D-006, D-014, D-020

Codebase Evidence:
- `src/analytics/metrics.py:187-215` - CSAT defaults to 4.5 if no ratings exist.
- `frontend/src/app/(agency)/insights/page.tsx:199-253` - agent rows show workload, conversion, response, CSAT.
- `frontend/src/components/visual/TeamPerformanceChart.tsx:92-113` - UI labels metrics with “higher/lower is better.”

Static Verification:
- No explicit employee-performance data classification or fairness policy found in inspected implementation.

Dynamic Verification:
- Targeted UI tests pass, but they validate rendering and drilldown, not fairness/privacy policy.

Current Behavior:
- Performance metrics can be rendered even when some values are default or unavailable.

Expected Behavior / Decision Needed:
- Define how metrics may be used, who can see them, how defaults/unavailable values are labeled, and whether exports are allowed.

Gap:
- Risk of misleading or punitive metric use.

Impact:
- Trust, privacy, and management-quality risk.

Risk:
- High if expanded without policy.

Confidence:
- High

Acceptance Criteria:
- [ ] Employee performance metrics are classified and access-scoped.
- [ ] Default/imputed metrics are labeled as unavailable or estimated.
- [ ] Exports include only allowed fields and audit the export.
- [ ] Scorecards include fairness normalization before ranking agents.

Test Plan:
- Automated: permission tests for analytics endpoints; UI tests for unavailable/default labels.
- Manual: owner/admin/junior-agent role check.

Rollback / Kill Switch:
- Gate performance ranking/export behind a feature flag until policy is ratified.

Open Questions:
- Should individual performance metrics be visible only to owners/admins, or also to team leads?

## ISSUE-006: Metric Drilldown Is Functional, But Real Response Shape Needs Guarded Mapping

Category:
- API contract / frontend / reliability

Origin:
- Implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:148-160`
- Related doc items: D-012, D-013

Codebase Evidence:
- `frontend/src/app/api/insights/agent-trips/route.ts:23-64` - explicit BFF route proxies backend drilldown.
- `spine_api/server.py:3159-3177` - backend returns raw `agent_trips` from TripStore.
- `frontend/src/components/workspace/panels/MetricDrillDownDrawer.tsx:7-16`, `frontend/src/components/workspace/panels/MetricDrillDownDrawer.tsx:147-217` - drawer expects `tripId`, `destinationName`, `status`, response/suitability/decision fields.
- `frontend/src/app/__tests__/e2e_metric_drilldown.test.tsx:27-45` - test mocks expected frontend shape.

Static Verification:
- BFF route forwards `data.trips || []` without mapping raw backend trips into drawer shape.

Dynamic Verification:
- Mocked frontend drilldown tests pass.

Current Behavior:
- Works against mocked frontend shape, but real backend response may not match the drawer contract.

Expected Behavior / Decision Needed:
- BFF route should map backend trips into the drawer contract or drawer should consume real backend shape with guards.

Gap:
- Mock contract may hide runtime mismatch.

Impact:
- Drilldown can show fallback IDs/status or fail to render useful trip details.

Risk:
- Medium, narrower than core dashboard.

Confidence:
- Medium

Acceptance Criteria:
- [ ] Capture real backend drilldown JSON.
- [ ] Add BFF mapping test using raw backend-shaped trip.
- [ ] Drawer uses guarded optional access.

Test Plan:
- Automated: BFF route unit test and drawer test with raw/backend-shaped trip.
- Manual: click a real team metric in the Insights page.

Rollback / Kill Switch:
- Keep drilldown graceful-empty behavior.

Open Questions:
- Which fields are allowed in drilldown for privacy and operational usefulness?

## ISSUE-007: Insights Export Button Is Not Wired in the Inspected Page

Category:
- UX / product-polish / privacy

Origin:
- Implicit
- Source doc: `frontend/docs/TASK_MGMT_04_ANALYTICS.md:132-160`
- Related doc items: D-011, D-013

Codebase Evidence:
- `frontend/src/app/(agency)/insights/page.tsx:365-367` - export button renders with no observed handler.
- `spine_api/server.py:4318-4331` - export endpoint exists and returns a mock export URL.

Static Verification:
- No page-level export click handler found in inspected range.

Dynamic Verification:
- Not run manually; not needed for audit conclusion.

Current Behavior:
- Button appears actionable but likely does nothing.

Expected Behavior / Decision Needed:
- Wire export through policy-aware endpoint or disable/label as unavailable.

Gap:
- UX trust issue and potential future privacy issue if wired too broadly.

Impact:
- Low to medium.

Risk:
- Low now, higher if export is enabled without classification.

Confidence:
- Medium

Acceptance Criteria:
- [ ] Button either performs an audited, permissioned export or is visibly disabled.
- [ ] Export fields are explicitly classified.

Test Plan:
- Automated: button click test.
- Manual: export and inspect payload/URL.

Rollback / Kill Switch:
- Disable button.

Open Questions:
- Should exports include employee-level performance data?

## 10. Prioritization

| ID | Title | Severity | Blast Radius | Effort | Confidence | Priority | Why |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| ISSUE-001 | Canonical task event model | 4 | 4 | 4 | 5 | P1 | Foundation for every task metric; prevents parallel stack. |
| ISSUE-002 | Reconcile dashboard scope | 3 | 4 | 2 | 5 | P1 | Prevents duplicate dashboard/product drift. |
| ISSUE-003 | Hard-coded bottleneck analysis | 3 | 3 | 2 | 5 | P1 | Current UI can imply false operational insight. |
| ISSUE-005 | Performance data classification/fairness | 4 | 3 | 3 | 5 | P1 | Sensitive employee/customer metric risk. |
| ISSUE-004 | Workload contract normalization | 3 | 2 | 2 | 4 | P2 | Contract drift risk, smaller surface. |
| ISSUE-006 | Drilldown response mapping | 2 | 2 | 2 | 3 | P2 | Mocked tests may hide real-shape mismatch. |
| ISSUE-007 | Export button wiring | 2 | 2 | 1 | 3 | P3 | Smaller UX issue, but privacy-sensitive if expanded. |

## Priority Queues

### P0

- None from this selected document.

### P1

- ISSUE-001: Task analytics needs a canonical event model before more metrics.
- ISSUE-002: Existing Insights dashboard is partial, not the task management dashboard.
- ISSUE-003: Bottleneck analysis is hard-coded but presented as live.
- ISSUE-005: Team performance metrics need data classification and fairness policy.

### P2

- ISSUE-004: Workload contract normalization exists only in test helper.
- ISSUE-006: Metric drilldown is functional, but real response shape needs guarded mapping.

### P3

- ISSUE-007: Insights export button is not wired in the inspected page.

### Quick Wins

- Label or hide hard-coded bottleneck results when evidence is absent.
- Move workload normalization out of test helper into production code or backend.
- Disable/export button until policy is defined.

### Risky Changes

- Building a new task analytics dashboard route.
- Adding scorecards without canonical task events.
- Ranking agents without fairness/data classification.

### Needs Discussion Before Work

- Whether task events become first-class records or are derived from audit/routing/trip state.
- Who can see individual agent performance metrics.
- Whether CSAT defaults should be displayed at all.

### Not Worth Doing

- Building the full scorecard UI immediately. The data model and policy are not ready.
- Adding a new parallel analytics dashboard. Extend/reconcile the existing Insights surface instead.

## 11. Proof-of-Concept Validation

No proof-of-concept probe was needed. Static and existing dynamic evidence were sufficient.

No files were temporarily modified.

## 12. Assumptions Challenged by Implementation

| Assumption | Why it seemed true | What disproved it | Evidence | How recommendation changed |
| --- | --- | --- | --- | --- |
| “Build dashboard” is still wholly missing. | The selected doc has unchecked next step. | Live Insights UI and backend endpoints exist. | `frontend/src/app/(agency)/insights/page.tsx:296-620`; `spine_api/server.py:3110-3184` | Recommend reconciliation, not a new dashboard. |
| Team metrics are fully real. | UI says live telemetry and tests pass. | CSAT defaults to 4.5 and response time is explicitly unavailable. | `src/analytics/metrics.py:187-215`; `tests/test_team_metrics_contract.py:98-107` | Require data-quality labels and policy before scorecards. |
| Bottlenecks are analytics-derived. | UI labels section Bottleneck Analysis. | Backend returns fixed cause/counts. | `src/analytics/metrics.py:220-237` | Prioritize evidence-derived or hidden/unavailable state. |
| Targeted frontend tests prove real API contract. | Drilldown tests pass. | Tests mock BFF response shape; backend returns raw trip dicts. | `frontend/src/app/__tests__/e2e_metric_drilldown.test.tsx:27-45`; `spine_api/server.py:3159-3177` | Add real-shape mapping test before expanding drilldown. |
| Full suite is currently green enough. | Prior memory had a similar baseline with 14 failures. | Current run has 16 failures. | `uv run pytest -q` result in this report | Treat failures as pre-existing and separate from selected-doc findings. |

## 13. Parallel Agent / Multi-Model Findings

Used subagents deliberately:

- Document analyst subagent completed and confirmed explicit tasks, implicit tasks, undefined sample types, dashboard partial staleness, and Goodhart/fairness claims.
- Codebase verifier, test/runtime verifier, and security/privacy reviewer timed out and were shut down. Their output was not used as evidence.

Reconciliation:

- The completed document analyst’s findings matched direct local reads of the selected doc and current analytics surfaces.
- Final issue register relies on direct repo evidence and targeted tests, not subagent consensus.

No external model review was used.

## 14. Discussion Pack

## My Recommendation

I recommend working on:

1. ISSUE-003 - Hard-coded bottleneck analysis is presented as live.
2. ISSUE-002 - Reconcile current Insights page with task-management analytics scope.
3. ISSUE-001 - Define the canonical task event model before scorecards.

Reason:

- ISSUE-003 is the smallest real product-value fix: it reduces false operational guidance without changing architecture broadly.
- ISSUE-002 prevents future duplicate dashboard work.
- ISSUE-001 is the long-term foundation, but it should start as a design/contract work unit, not a broad implementation.

## Why These Matter Now

- The existing Insights page already ships analytics-like UI.
- Some displayed metrics are defaults or fixed outputs.
- The selected doc can mislead future agents into building a parallel dashboard instead of improving the canonical surface.

## What Breaks If Ignored

- Operators may trust hard-coded bottleneck output.
- Agents may build new dashboard routes for the same resource.
- Scorecards may be built from incomplete or unfair data.

## What I Would Not Work On Yet

- Full balanced scorecard UI.
- Ranking agents.
- Anti-gaming enforcement.
- External export of employee/customer performance metrics.

## What Is Ambiguous

- Whether task analytics should be first-class or derived.
- Whether team leads, senior agents, or only owners can see individual performance.
- Whether imputed/default values can be shown in production dashboards.

## Questions For You

1. Should current `Insights & Analytics` be the single canonical analytics command center, with task analytics added inside it, or should task analytics remain only a design track for now?
2. Should hard-coded/no-evidence bottlenecks be hidden entirely, or shown as “insufficient data” with no suggested action?
3. Should individual agent metrics be treated as owner/admin-only sensitive performance data by default?
4. Should task events be first-class persisted records, or derived from trip/routing/audit events until the system proves a need for first-class tasks?

## Needs Runtime Verification

- Real browser check of Insights page with backend and frontend servers.
- Real API shape check for `/api/insights/agent-trips`.
- Real API shape check for `/api/team/workload` through the BFF.

## Needs Online Research

- Workforce analytics best practices before designing balanced scorecard thresholds.
- Fair performance measurement and Goodhart mitigation patterns before agent ranking.

## Needs ChatGPT / External Review

- Not needed for this audit. The next uncertain decision is product/architecture intent, not external technical feasibility.

## 15. Online Research

No online research was needed for the codebase-reality audit. External research is useful before implementing ISSUE-001/ISSUE-005, but not required to prove the current repo gaps.

## 16. ChatGPT / External Review Escalation Writeup

Not needed now.

## 17. Recommended Next Work Unit

## Unit-1: Make Bottleneck Analytics Honest

Goal:

- Stop the Insights page from presenting hard-coded bottleneck output as real operational analysis.

Issues covered:

- ISSUE-003
- Supports ISSUE-002 by keeping the existing Insights surface canonical and truthful.

Scope:

- In:
  - Audit `compute_bottlenecks` behavior for empty/no-evidence trips.
  - Change behavior to return no bottleneck, or add explicit insufficient-data metadata, rather than fixed operational causes.
  - Add focused tests for empty/no-evidence and real-evidence cases if real evidence fields already exist.
  - Update docs to record that bottleneck analytics are evidence-gated.
- Out:
  - New dashboard routes.
  - Full task event schema.
  - Balanced scorecard implementation.
  - Anti-gaming enforcement.

Likely files touched:

- `src/analytics/metrics.py`
- `src/analytics/models.py` only if an explicit unavailable-state model is needed.
- `tests/test_*analytics*.py` or a new focused backend test.
- `frontend/src/app/(agency)/insights/page.tsx` only if the frontend needs an honest unavailable state.
- `Docs/random_document_audit_task_mgmt_analytics_2026-05-04.md` or a follow-up status doc.

Acceptance criteria:

- [ ] Empty/no-evidence datasets do not show a fabricated bottleneck.
- [ ] Any displayed bottleneck is backed by counted source evidence.
- [ ] UI copy does not imply smooth flow or bottlenecks without evidence.
- [ ] Targeted backend analytics tests pass.
- [ ] Relevant frontend tests pass if UI changes.
- [ ] Full suite result is recorded and pre-existing failures remain separated.

Tests to run:

- Baseline:
  - `uv run pytest -q`
- Targeted:
  - `uv run pytest -q tests/test_team_metrics_contract.py tests/test_revenue_analytics.py <new-or-existing-bottleneck-test>`
  - If UI changes: `npm test -- --run src/components/visual/__tests__/TeamPerformanceChart.test.tsx src/app/__tests__/e2e_metric_drilldown.test.tsx`
- Full suite:
  - `uv run pytest -q`
  - Frontend relevant suite if UI changes.

Manual verification:

- Start backend and frontend.
- Load Insights page.
- Confirm bottleneck section is hidden or honest when no evidence exists.

Docs to update:

- Follow-up note in `Docs/` with baseline, targeted tests, and current limitations.

Operational safety:

- Kill switch / rollback:
  - Returning an empty bottleneck list is reversible and safer than showing fabricated causes.

Risks:

- If users relied on the hard-coded card as a placeholder, hiding it may make the dashboard look emptier. That is acceptable because it is more truthful.

Rollback plan:

- Revert the bottleneck function/UI change if targeted tests expose hidden coupling, but do not reintroduce fabricated operational claims as final behavior.

## 18. Appendix: Searches Performed

```bash
/Users/pranay/Projects/agent-start
sed -n '1,220p' Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt
sed -n '1,220p' Docs/context/agent-start/SESSION_CONTEXT.md
find README.md TODO.md Docs frontend/docs docs specs audits plans architecture design qa tests .kiro data notebooks -path '*/node_modules/*' -prune -o -path '*/.venv/*' -prune -o -type f \( -iname '*.md' -o -iname 'CHANGELOG*' -o -iname 'TODO*' -o -iname 'ROADMAP*' -o -iname 'ADR*' \) -print
find Docs/product_features frontend/docs specs Docs/architecture Docs/design .kiro/specs data notebooks -type f \( -iname '*.md' -o -iname 'README.md' -o -iname 'TODO*' -o -iname 'ROADMAP*' -o -iname 'ADR*' \) -print | sort | wc -l
find Docs/product_features frontend/docs specs Docs/architecture Docs/design .kiro/specs data notebooks -type f \( -iname '*.md' -o -iname 'README.md' -o -iname 'TODO*' -o -iname 'ROADMAP*' -o -iname 'ADR*' \) -print | sort | shuf -n 1
rg -n "TODO|FIXME|HACK|NOTE|XXX" --glob '!node_modules/**' --glob '!frontend/node_modules/**' --glob '!.venv/**' --glob '!tools/node_modules/**' .
nl -ba frontend/docs/TASK_MGMT_04_ANALYTICS.md | sed -n '1,260p'
find frontend/src spine_api src tests frontend/src -type f \( -iname '*.ts' -o -iname '*.tsx' -o -iname '*.py' -o -iname '*.md' \) | rg -i 'task|analytics|productivity|sla|workload|assignment|dashboard'
find frontend/docs -maxdepth 1 -type f -iname 'TASK_MGMT*.md' -o -iname 'TASK_MANAGEMENT*.md' | sort
nl -ba src/analytics/models.py | sed -n '1,260p'
nl -ba src/analytics/metrics.py | sed -n '1,430p'
nl -ba src/services/dashboard_aggregator.py | sed -n '1,260p'
nl -ba spine_api/routers/assignments.py | sed -n '1,260p'
nl -ba spine_api/services/sla_service.py | sed -n '1,260p'
nl -ba spine_api/services/routing_service.py | sed -n '1,340p'
nl -ba frontend/src/lib/__tests__/workload-normalization.test.ts | sed -n '1,260p'
rg -n "TaskDashboard|AgentPerformanceMetrics|ProductivityMetrics|QualityMetrics|TimelinessMetrics|BottleneckReport|MetricIntegrity|average_time_to_complete|slaCompliance|Goodhart|workload|SLA|assignment|teamUtilization|customerSatisfaction|peerReview|time tracking|anomaly" frontend/src src spine_api tests frontend/docs --glob '!frontend/docs/TASK_MGMT_04_ANALYTICS.md'
nl -ba spine_api/server.py | sed -n '2020,2120p'
nl -ba spine_api/server.py | sed -n '3088,3192p'
nl -ba spine_api/server.py | sed -n '3880,3935p'
nl -ba frontend/src/app/'(agency)'/insights/page.tsx | sed -n '1,620p'
nl -ba frontend/src/hooks/useGovernance.ts | sed -n '1,270p'
nl -ba frontend/src/lib/governance-api.ts | sed -n '1,260p'
nl -ba frontend/src/types/governance.ts | sed -n '1,240p'
nl -ba tests/test_team_metrics_contract.py | sed -n '1,220p'
nl -ba tests/test_routing_state_machine.py | sed -n '1,340p'
nl -ba tests/test_revenue_analytics.py | sed -n '1,130p'
rg -n "api/insights|insights/summary|def get_.*insight|compute_team_metrics|compute_bottlenecks|compute_pipeline_metrics|compute_revenue_metrics|compute_alerts" spine_api/server.py src tests frontend/src/types/governance.ts
rg -n "insights|team metrics|bottleneck|revenue|workload|sla_service|compute_sla|assignment" tests frontend/src -g '*test*' -g '*.spec*'
rg -n "agent-trips|analytics/agent|drill-down|insights" frontend/src/app frontend/src/lib/route-map.ts spine_api/server.py
nl -ba frontend/src/app/api/insights/agent-trips/route.ts | sed -n '1,180p'
rg -n "os\.getenv|environ|process\.env|lru_cache|cache" src/analytics spine_api/services/sla_service.py spine_api/services/routing_service.py spine_api/server.py frontend/src/app/api/insights frontend/src/app/'(agency)'/insights frontend/src/lib/governance-api.ts frontend/src/hooks/useGovernance.ts
uv run pytest -q
uv run pytest -q tests/test_team_metrics_contract.py tests/test_revenue_analytics.py tests/test_routing_state_machine.py
npm test -- --run src/lib/__tests__/workload-normalization.test.ts src/components/visual/__tests__/TeamPerformanceChart.test.tsx src/components/visual/__tests__/TeamPerformanceChart.drilldown.test.tsx src/app/__tests__/e2e_metric_drilldown.test.tsx
```
