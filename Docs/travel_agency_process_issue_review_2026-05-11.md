# Slot Lineage Serialization and Confidence Contract Supersession

**Date:** 2026-05-11  
**Status:** Implemented and targeted-verified  
**Source audit:** Random code-file audit of `tests/test_spine_hardening_temp.py`  
**Checklist applied:** IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md

---

## 1. Summary

The random code-file audit selected `tests/test_spine_hardening_temp.py`. The file was temporary in name but contained two useful contracts:

1. `run_gap_and_decision()` exposes a structured `ConfidenceScorecard` and mirrors confidence sub-scores into `DecisionResult.rationale`.
2. `Slot.derived_from` preserves lineage values in memory.

Static verification found that lineage was only partially preserved: `Slot.derived_from` existed on the dataclass, but `Slot.to_dict()` omitted it. Since `CanonicalPacket.to_dict()` serializes facts, derived signals, and hypotheses through `Slot.to_dict()`, packet serialization dropped lineage.

## 2. First-Principles Decision

Lineage is not a decorative field. It is part of the trust contract for automation:

- Operators need to know where a fact came from.
- Review workflows need to distinguish explicit user facts from derived signals.
- Future analytics/evals need provenance to debug weak or wrong decisions.

Therefore, the long-term correct behavior is to preserve `derived_from` across packet serialization. This is additive: existing consumers that ignore unknown JSON keys continue to work, while consumers that need traceability can use the field.

## 3. Changes Made

### `src/intake/packet_models.py`

- Added `derived_from` to `Slot.to_dict()`.
- Used `list(self.derived_from)` so serialized output cannot mutate the slot's internal list by reference.

### `tests/test_api_contract_v02.py`

- Added `test_slot_to_dict_preserves_lineage`.
- Added `test_packet_to_dict_preserves_slot_lineage`.

These tests prove both the direct slot serialization boundary and the packet serialization boundary.

### `tests/test_p1_backend_regressions.py`

- Added `test_run_gap_and_decision_exposes_scorecard_contract`.
- The test verifies:
  - `result.confidence` is a `ConfidenceScorecard`.
  - `rationale["confidence_scorecard"]` contains `data`, `judgment`, and `commercial`.
  - `rationale["confidence"]` mirrors the rounded overall confidence score.

### `tests/test_spine_hardening_temp.py`

Removed after supersession.

Supersession analysis:

```text
Removal: tests/test_spine_hardening_temp.py — superseded by canonical API contract and P1 backend regression tests
Comparison:
- Confidence object type: covered by tests/test_p1_backend_regressions.py::TestConfidenceScorecard::test_run_gap_and_decision_exposes_scorecard_contract
- Confidence rationale data key: covered and expanded to data/judgment/commercial/overall mapping
- Slot in-memory lineage: covered and expanded to Slot.to_dict() and CanonicalPacket.to_dict() serialization boundaries
Call sites: 0 — test file only, no production imports
```

## 4. Verification

Pre-change targeted baseline:

```bash
uv run pytest -q tests/test_api_contract_v02.py tests/test_p1_backend_regressions.py tests/test_spine_hardening_temp.py
```

Result:

```text
47 passed
```

Post-change targeted verification:

```bash
uv run pytest -q tests/test_api_contract_v02.py tests/test_p1_backend_regressions.py
```

Result:

```text
48 passed
```

Collection verification:

```bash
uv run pytest --collect-only -q tests | rg "spine_hardening_temp|test_slot_to_dict_preserves_lineage|test_packet_to_dict_preserves_slot_lineage|test_run_gap_and_decision_exposes_scorecard_contract"
```

Result:

```text
tests/test_api_contract_v02.py::TestDataclassStructures::test_slot_to_dict_preserves_lineage
tests/test_api_contract_v02.py::TestDataclassStructures::test_packet_to_dict_preserves_slot_lineage
tests/test_p1_backend_regressions.py::TestConfidenceScorecard::test_run_gap_and_decision_exposes_scorecard_contract
```

Production-file lint:

```bash
uv run ruff check src/intake/packet_models.py
```

Result:

```text
All checks passed!
```

Full-suite status:

```bash
uv run pytest -q
```

Result:

```text
5 failed, 2019 passed, 6 skipped
```

The failure set matches the known pre-change baseline below. The pass count increased by one because the superseded temp-file coverage was replaced with stronger canonical coverage.

Known pre-change full-suite baseline from 2026-05-11:

```text
5 failed, 2018 passed, 6 skipped
```

Known baseline failures:

- `tests/test_health_router_behavior.py` expected version `1.0.0`, actual `0.0.1`.
- `tests/test_llm_clients.py::TestLLMDecide::test_openai_decide` hit OpenAI quota/429.
- `tests/test_rls.py::TestApplyRls::test_issues_set_local_statement` expected `SET LOCAL`, implementation uses `set_config(...)`.
- `tests/test_run_lifecycle.py::TestWriteFailureIsolation::test_server_source_wraps_ledger_writes` expected stale source text.

## 5. Notes for Future Agents

- Do not recreate `tests/test_spine_hardening_temp.py`; its useful coverage now lives in canonical suites.
- If adding new serialized `Slot` fields, test both `Slot.to_dict()` and `CanonicalPacket.to_dict()`.
- Ruff on the broader touched test files still reports older pre-existing unused imports/style findings. Avoid deleting imports solely to satisfy lint unless you verify the deletion is behavior-neutral and within scope.
- No online research was needed; this was a repo-contract issue.

---

# Baseline Suite Stabilization Addendum

**Date:** 2026-05-11  
**Status:** Implemented and full-suite verified  
**Scope:** Convert the known full-suite failures from the previous audit into stable, evidence-backed tests.

## Summary

The previous full-suite baseline had five known failures. Static review showed that the failures were not product regressions; they were stale or environment-sensitive tests:

- Health tests hardcoded `1.0.0` while the app exposes the canonical `APP_VERSION`.
- RLS tests asserted a literal `SET LOCAL` string while implementation uses transaction-local `set_config(..., true)` with a bound parameter.
- The live OpenAI integration test ran whenever `OPENAI_API_KEY` existed, making the default suite dependent on quota/network state.
- The ledger-write isolation test inspected the old `server.py` location after the logic moved into `spine_api/services/pipeline_execution_service.py`.

## Changes Made

- `spine_api/routers/health.py`: call `health_check_dict()` once and reuse its result.
- `tests/test_health_router_behavior.py`: assert `APP_VERSION` instead of a stale literal version.
- `spine_api/core/rls.py` and `Docs/RLS_TENANT_ISOLATION_2026-05-04.md`: document transaction-local `set_config(..., true)` as the canonical RLS mechanism.
- `tests/test_rls.py`: assert transaction-local config, tenant setting name, and bound parameter behavior.
- `tests/test_llm_clients.py`: require `RUN_LIVE_LLM_TESTS=1` plus provider API key before making live paid/network calls.
- `tests/test_run_lifecycle.py`: inspect the current pipeline execution service for Wave A ledger write isolation guards.

## Verification

Targeted failure slice:

```bash
uv run pytest -q tests/test_health_router_behavior.py tests/test_rls.py::TestApplyRls tests/test_llm_clients.py::TestLLMDecide tests/test_run_lifecycle.py::TestWriteFailureIsolation::test_server_source_wraps_ledger_writes
```

Result:

```text
4 passed, 3 skipped
```

Full suite:

```bash
uv run pytest -q
```

Result:

```text
1988 passed, 42 skipped, 3 warnings in 79.32s
```

The three warnings are pre-existing async mock warnings in `tests/test_audit_bridge.py`.

Focused ruff check:

```bash
uv run ruff check spine_api/routers/health.py spine_api/core/rls.py tests/test_health_router_behavior.py tests/test_rls.py tests/test_llm_clients.py tests/test_run_lifecycle.py
```

Result:

```text
13 F401 unused-import findings
```

These are syntax-safe but include pre-existing unused imports in legacy tests and `spine_api/core/rls.py`. They were intentionally not removed in this stabilization unit because the repo preservation rule says not to delete code/imports solely to satisfy lint without a scoped neutrality check.

## Long-Term Notes

- Default test suites should not call paid/network LLM APIs based only on the presence of API keys. Keep live-provider tests opt-in through `RUN_LIVE_LLM_TESTS=1`.
- Prefer behavior or canonical-location assertions over source-string assertions. The ledger test was kept as a narrow source guard only because that was the existing test's purpose; the stronger long-term path is expanding `tests/test_pipeline_execution_service_boundaries.py` with behavioral fake-ledger failure cases.
- RLS tenant scoping should continue to prioritize bound parameters and transaction-local behavior over matching a specific SQL spelling.

---

# Audit Bridge Warning Cleanup Addendum

**Date:** 2026-05-11  
**Status:** Implemented and full-suite verified  
**Scope:** Remove async mock warnings from `tests/test_audit_bridge.py` without changing production audit behavior.

## Root Cause

`tests/test_audit_bridge.py` had two mock-shape problems:

- `_write_to_sql` was patched without `new=...`; because it is an async function, `unittest.mock.patch()` created an `AsyncMock`. Scheduler tests called it but intentionally did not await it because they were testing scheduling, leaving un-awaited mock coroutines behind.
- SQLAlchemy `AsyncSession.add()` is synchronous while `commit()` is async. The tests modeled the whole session with async-style mocks, so the sync `session.add(entry)` call produced coroutine warnings.

## Change

- Added a small `FakeAsyncSessionContext` for the async context-manager boundary.
- Added `AsyncCallRecorder` for the awaited `commit()` call.
- Patched scheduler `_write_to_sql` with a regular `MagicMock(return_value=object())` because these tests only verify scheduling handoff, not the coroutine body.
- Removed an unused `os` import from the test file after proving it was not referenced.

## Verification

Targeted warning run:

```bash
uv run pytest -q tests/test_audit_bridge.py -W always
```

Result:

```text
10 passed in 9.43s
```

Focused lint:

```bash
uv run ruff check tests/test_audit_bridge.py
```

Result:

```text
All checks passed!
```

Full suite:

```bash
uv run pytest -q
```

Result:

```text
2023 passed, 7 skipped in 122.84s
```

## Notes for Future Agents

- When patching async functions in tests, remember `patch()` creates `AsyncMock` by default. If the test is intentionally checking scheduling handoff and will not await the returned object, patch with `new=MagicMock(...)` or explicitly close the coroutine.
- Model SQLAlchemy async sessions precisely: methods such as `add()` are sync; methods such as `commit()` are awaited.

---

## Overview/Workbench Stability Addendum (2026-05-11)

### Problem
During randomized user testing, we observed intermittent `Internal Server Error` in governance surfaces and count drift symptoms in overview (top cards vs progress strip) when upstream payload quality varied.

### Root-cause findings
1. Backend endpoints still contained unsafe nested access patterns like `trip.get("analytics", {}).get(...)`.
2. Legacy or partially-migrated records can contain non-dict `analytics` payloads (e.g., `None`, string/object mismatch), which can trigger runtime errors in aggregation endpoints.
3. Overview progress display depended on stage-sum totals while other overview widgets are keyed to canonical planning totals; this permits visual drift when stage data is stale/noisy.

### Changes implemented
1. Hardened backend aggregations in `/Users/pranay/Projects/travel_agency_agent/spine_api/server.py`:
- `/inbox/stats` now normalizes analytics payloads with dict guards before reading `escalation_severity` and `sla_status`.
- `/analytics/escalations` now applies the same dict guard before escalation checks.

2. Added explicit regression coverage:
- `/Users/pranay/Projects/travel_agency_agent/tests/test_overview_analytics_hardening.py`
- Validates both endpoints remain stable and numerically correct with malformed analytics payloads.

3. Removed overview total drift path:
- `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/overview/page.tsx`
- `PipelineBar` now accepts canonical `planningTripsTotal` and displays that single source-of-truth total, while still rendering stage distribution bars from available stage data.

### Verification
- `uv run pytest -q tests/test_overview_analytics_hardening.py` → `2 passed`
- `cd frontend && npm run -s test -- --run 'src/app/(agency)/overview'` → `11 passed`
- `cd frontend && npm run -s test -- --run 'src/app/(agency)/workbench/__tests__/page.test.tsx'` → `4 passed`
- `cd frontend && npm run -s build` → build/typecheck passed
- Runtime health checks:
  - `curl http://localhost:8000/health` → `200`
  - `curl http://localhost:3000` → `200`

### Architectural note
This is not a UI-only patch. It is a contract-hardening correction that isolates user-facing overview stability from malformed legacy records while preserving canonical totals across surfaces.

## Risk Review UX Consistency Pass (2026-05-11, Session 2)

### Objective
Continue randomized QA hardening by aligning workbench/trip review language with industry-facing operations terminology and reducing ambiguous labels for agents.

### Changes implemented
1. Updated planning-gate unlock copy in `/Users/pranay/Projects/travel_agency_agent/frontend/src/lib/planning-status.ts`:
- `...unlock quote, options, output, and safety review.`
- → `...unlock quote, options, output, and risk review.`

2. Refined workbench risk tab messaging in `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/workbench/SafetyTab.tsx`:
- "No review data" → "No risk review data yet"
- Section title "Content Review" → "Risk Gate"
- Added explanatory helper text for send-readiness intent
- "Special Handling Checklist" → "Special Handling Controls"
- "Safety Notes" → "Risk Notes"
- "Customer-Facing Message" → "Customer Message QA"
- "System Context" → "Generation Context"
- "User Message" → "Message Preview"
- "Technical Data" toggle → "Diagnostic Data"

3. Mirrored naming consistency in `/Users/pranay/Projects/travel_agency_agent/frontend/src/components/workspace/panels/SafetyPanel.tsx`:
- "Content Review" → "Risk Gate" (+ helper text)
- "Customer-Facing Message" → "Customer Message QA"
- "Technical Data" → "Diagnostic Data"

4. Updated assertion in `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx` for the new unlock hint copy.

### Verification
- `cd frontend && npm run -s test -- --run 'src/app/(agency)/trips/[tripId]/__tests__/layout.test.tsx' 'src/app/(agency)/workbench/__tests__/page.test.tsx'`
  - Result: `12 passed`
  - Note: pre-existing `act(...)` warnings in layout tests remain non-failing.
- `cd frontend && npm run -s build`
  - Result: build + typecheck passed.

### Runtime stability checks
- Restarted frontend dev server successfully on `http://localhost:3000`.
- Backend initially failed when launched from `/spine_api` subdir with module import path; relaunched from repo root and stabilized.
- Health checks after restart:
  - `curl http://localhost:8000/health` → `200`
  - `curl http://localhost:3000` → `200`

### Operational note
Keep backend startup command anchored at repo root when using `spine_api.server:app` import mode to avoid module path drift.

---

## Pipeline Ledger Isolation Behavioral Test Supersession (2026-05-11)

### Objective
Replace the brittle Wave A ledger source-string guard with behavioral tests against the current canonical pipeline execution service.

### Root-cause finding
`tests/test_run_lifecycle.py::TestWriteFailureIsolation::test_server_source_wraps_ledger_writes` only inspected source text for four log messages. That was weak evidence after pipeline execution moved from `spine_api/server.py` into `spine_api/services/pipeline_execution_service.py`: it proved the strings existed, not that ledger failures remained non-fatal.

### Changes implemented
1. Added behavioral fake-ledger coverage in `tests/test_pipeline_execution_service_boundaries.py`:
- result checkpoint ledger failure is logged and the run still saves/completes
- terminal `complete()` ledger failure is logged and does not escape
- terminal `block()` ledger failure is logged and does not escape
- terminal `fail()` ledger failure is logged and does not escape

2. Removed the superseded source-string check from `tests/test_run_lifecycle.py`.

Supersession analysis:

```text
Removal: TestWriteFailureIsolation.test_server_source_wraps_ledger_writes
Replacement: tests/test_pipeline_execution_service_boundaries.py behavioral fake-ledger tests
Comparison:
- Result checkpoint failure: behavior now exercised directly
- Complete ledger failure: behavior now exercised directly
- Block ledger failure: behavior now exercised directly
- Fail ledger failure: behavior now exercised directly
Call sites: test-only static check; no production imports
```

### Verification
Targeted behavioral suite:

```bash
uv run pytest -q tests/test_pipeline_execution_service_boundaries.py tests/test_run_lifecycle.py::TestWriteFailureIsolation
```

Result:

```text
6 passed, 1 skipped
```

Focused lint:

```bash
uv run ruff check tests/test_pipeline_execution_service_boundaries.py tests/test_run_lifecycle.py
```

Result:

```text
All checks passed!
```

Full-suite status:

```bash
uv run pytest -q
```

Result:

```text
6 failed, 2038 passed, 7 skipped, 1 error
```

Failure set:
- `tests/test_call_capture_phase2.py::TestPhase2StructuredFields` had six PATCH/list-state failures.
- `tests/test_run_lifecycle.py::TestLeakagePath::test_blocked_event_consistency_when_blocked` had a live run status 500.

Isolation rerun:

```bash
uv run pytest -q tests/test_call_capture_phase2.py::TestPhase2StructuredFields tests/test_run_lifecycle.py::TestLeakagePath::test_blocked_event_consistency_when_blocked
```

Result:

```text
18 passed
```

Earlier in the same session, a full-suite run also produced one transient `data/audit/events.jsonl.lockdir` ownerless-lock race in `tests/test_document_extractions.py`; the exact failed test passed on immediate rerun.

### Current interpretation
The ledger behavior change is targeted-verified and lint-clean. The full suite is currently order-dependent in the dirty multi-agent worktree; the observed failures reproduce only in full-suite order, not in isolation. Treat this as a separate test-isolation/worktree-state issue before claiming a global green baseline.

### Next recommended work
Investigate full-suite order dependence around:
- `tests/test_call_capture_phase2.py` selecting `trips[0]` from shared state and then PATCHing it
- `tests/test_run_lifecycle.py` live run status 500 in strict leakage flow
- `spine_api/persistence.py:file_lock()` ownerless-lock race on `data/audit/events.jsonl.lockdir`

## Dev Server Lifecycle Hardening (2026-05-11, Session 3)

### Problem
Randomized QA loops were blocked by server sessions dropping between turns, causing false completion claims and repeated manual restarts.

### Root cause
- Ad-hoc terminal-bound process starts were not durable across tool sessions.
- Runtime checks became inconsistent when PID ownership drifted or when Turbopack cold-compile delays outlived short health timeouts.

### Solution implemented
1. Added reusable supervisor tool:
- `/Users/pranay/Projects/travel_agency_agent/tools/dev_server_manager.py`

2. Capabilities:
- `start`, `stop`, `restart`, `status`, `check`, `logs`
- Detached process start with PID/log files under `.runtime/`
- Port-based PID recovery (`lsof -ti tcp:<port>`) when PID files drift
- Health checks for both backend and frontend

3. Stability improvements:
- Backend launch switched to `.venv/bin/python -m uvicorn spine_api.server:app ...` for direct process ownership.
- Health probe timeout increased to handle Turbopack cold-start latency.

4. Documentation updated:
- `/Users/pranay/Projects/travel_agency_agent/tools/README.md`

### Verification evidence
- `python tools/dev_server_manager.py restart --service all` → both healthy
- `python tools/dev_server_manager.py status --service all` → backend/frontend running + `health=200`
- `python tools/dev_server_manager.py check --service all` → both `200`
- Direct URL checks:
  - `http://localhost:8000/health` → `200`
  - `http://localhost:3000/workbench?draft=new&tab=safety` → `200`

### Operator note
Use the supervisor commands as the canonical startup path for randomized testing to reduce runtime drift and false-negative availability checks.

## Full-Suite Order-Dependence Stabilization (2026-05-11, Session 4)

### Problem
The backend full suite had become order-dependent after the ledger-isolation test cleanup. Focused tests passed, but full-suite order exposed:
- `tests/test_call_capture_phase2.py::TestPhase2StructuredFields` PATCH/GET failures when tests selected `trips[0]` from `/trips`.
- `tests/test_integrity.py::TestIntegrityIssues::test_integrity_endpoint_passes_current_agency_scope` returning `401` after the suite had been running for longer than the default access-token lifetime.

### Root Causes
1. `tests/test_call_capture_phase2.py` used shared API list state as a fixture. In SQL-backed test runs, `/trips` can include seeded or previously-created trips, so `trips[0]` is not a stable ownership or schema contract for a PATCH test.
2. `tests/conftest.py::session_client` created a real JWT with the production 15-minute default expiry. The full suite reached later authenticated endpoints after that token had expired.
3. A parallel fixture edit briefly introduced `TripStore.delete_trip()` cleanup. That was rejected because repo data-safety rules prohibit deleting from the shared test database without explicit permission.
4. The first unique trip ID format exceeded the SQL `trips.id varchar(36)` limit. The fixture now uses `trip_p2_` plus a 28-character hex suffix, exactly 36 characters.

### Changes Implemented
- `tests/test_call_capture_phase2.py`
  - Added per-test `patchable_trip_id` fixture backed by a unique additive trip ID.
  - Replaced PATCH/GET tests that depended on `trips[0]` with explicit fixture-owned trip IDs.
  - Removed delete cleanup; fixture records are additive and bounded to test data markers.
- `tests/conftest.py`
  - Extended only the shared test client's JWT lifetime to 12 hours via `expires_delta=timedelta(hours=12)`.
  - Left production token expiry unchanged in `spine_api/core/security.py`.

### Verification
Focused lint:

```bash
uv run ruff check tests/conftest.py tests/test_call_capture_phase2.py
```

Result:

```text
All checks passed!
```

Focused runtime checks:

```bash
uv run pytest -q tests/test_integrity.py::TestIntegrityIssues::test_integrity_endpoint_returns_items_and_total tests/test_integrity.py::TestIntegrityIssues::test_integrity_endpoint_passes_current_agency_scope
uv run pytest -q tests/test_auth_integration.py::TestAuthMiddleware::test_expired_token_returns_401
uv run pytest -q tests/test_call_capture_phase2.py::TestPhase2StructuredFields
```

Result:

```text
2 passed
1 passed
17 passed
```

Full-suite verification:

```bash
uv run pytest -q
```

Result:

```text
2057 passed, 7 skipped in 48.28s
```

### Notes for Future Agents
- Do not reintroduce `trips[0]` as a mutable test target for PATCH/GET tests. Seed an explicit fixture-owned trip and use its ID.
- Do not delete shared SQL test data as fixture cleanup. Use unique additive IDs and synthetic markers unless the user explicitly authorizes database deletion.
- Keep production JWT expiry short; use explicit long-lived test fixture tokens only for session-scoped full-suite clients.

## Dev Server Runtime State Hygiene (2026-05-11, Session 5)

### Problem
The dev server manager wrote live PID/log state directly under `.runtime/`, but `.runtime/backend.pid` and `.runtime/frontend.pid` were already tracked files. Running `python tools/dev_server_manager.py status --service all` therefore dirtied the worktree whenever the live frontend/backend PID changed.

### Root Cause
Mutable process state was sharing paths with tracked repository files. This made normal local QA operations look like source changes and created noise for every parallel agent doing a status check.

### Changes Implemented
- `.gitignore`
  - Added `.runtime/local/` for ignored local dev-server runtime state.
- `tools/dev_server_manager.py`
  - Changed `RUNTIME_DIR` from `.runtime/` to `.runtime/local/`.
  - Existing port-based PID recovery behavior is preserved.
- `tools/README.md`
  - Updated dev server manager documentation to point at `.runtime/local/*.pid` and `.runtime/local/*.log`.

### Verification
Focused lint:

```bash
uv run ruff check tools/dev_server_manager.py
```

Result:

```text
All checks passed!
```

Runtime status check:

```bash
python tools/dev_server_manager.py status --service all
```

Result:

```text
backend: running pid=50561 health=200
frontend: running pid=66461 health=200
```

### Notes for Future Agents
- Keep mutable server state under `.runtime/local/`; do not write changing PID/log files to tracked `.runtime/*` paths.
- The old tracked PID files remain in the repository history. Removing them from tracking would require an explicit git index operation and was intentionally not performed in this session.

## Runtime Truth Automation Addendum (2026-05-11, Session 4)

### Why
Randomized testing quality depends on repeatable runtime checks, not ad-hoc manual curl sequences.

### What was added
1. Reusable smoke tool:
- `/Users/pranay/Projects/travel_agency_agent/tools/runtime_smoke_matrix.py`

2. Tool docs:
- `/Users/pranay/Projects/travel_agency_agent/tools/README.md`

### Smoke scope
The script logs in and verifies status contracts for:
- `/api/auth/me`
- `/overview`
- `/workbench?draft=new&tab=safety`
- `/api/inbox?page=1&limit=1`
- `/api/trips?view=workspace&limit=5`
- `/api/reviews?status=pending`
- `/api/inbox/stats`
- `/api/pipeline`

### Verification run
```bash
python tools/runtime_smoke_matrix.py
```
Result:
- login `200`
- all route checks `200`
- `Smoke matrix passed.`

### Operational rule (recommended)
Before claiming frontend/backend stability in local QA:
1. `python tools/dev_server_manager.py status --service all`
2. `python tools/runtime_smoke_matrix.py`
Only claim stable when both pass.
