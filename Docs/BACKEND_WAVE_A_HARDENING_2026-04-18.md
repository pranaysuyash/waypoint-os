# Wave A — Hardening Gate Closure Notes
**Date**: 2026-04-18  
**Status**: All 10/10 criteria implemented. Pending reviewer verification of integration path.  
**Previous**: `BACKEND_WAVE_A_IMPL_NOTES_2026-04-18.md`

---

## Changes Made vs Initial Wave A

| Criterion | Initial state | After hardening |
|---|---|---|
| 1. Transition guards end-to-end | `assert_can_transition` imported but unused in ledger | Every ledger mutation (`set_state`, `complete`, `fail`, `block`) calls `assert_can_transition` before writing |
| 2. Terminal semantics | Correct conceptually | Tested via unit tests, ledger guards enforce it |
| 3. Event coverage | Only run-level events | `pipeline_stage_entered` + `pipeline_stage_completed` emitted around each `save_step` |
| 4. Step ledger completeness | safety step missing | safety checkpointed from `leakage_result`; output step in KNOWN_STEPS |
| 5. Consistency invariant | Not tested | Integration tests cross-check `run_id` across response + ledger + events |
| 6. Write failure isolation | try/except present but not tested | Static source verification test + confirmed golden run returns 200 |
| 7. Idempotency defined | Not documented | Explicit policy: each `POST /run` = new `run_id`, no deduplication. Tested. |
| 8. Endpoint robustness | Not edge-case tested | All edge cases tested: unknown run, unknown step, filter params, limit |
| 9. Observability | Structured logs present | Maintained; `run_id` in every log line |
| 10. Eval harness quality | Mixed unit+integration | Split: `test_run_state_unit.py` (pure, no server) + `test_run_lifecycle.py` (integration, `@pytest.mark.integration`) |

---

## New Files

| File | Purpose |
|---|---|
| `tests/test_run_state_unit.py` | Pure unit tests — state machine, ledger guards, step checkpoints, event log. No live API. |
| `tests/test_run_lifecycle.py` | Integration-only — all 10 hardening criteria via live API calls. |

---

## CI Command Set

### Unit tests (CI-safe, no API required):
```bash
.venv/bin/pytest tests/test_run_state_unit.py -v
```

### Integration tests (requires live spine-api):
```bash
# Start spine-api first
python -m uvicorn spine-api.server:app --host 127.0.0.1 --port 8000 &
sleep 2
.venv/bin/pytest tests/test_run_lifecycle.py -v -m integration
```

### All non-integration tests (full suite excluding live API):
```bash
.venv/bin/pytest -v -m "not integration"
```

### Full suite (requires live spine-api):
```bash
.venv/bin/pytest -v
```

---

## Key Design Decisions (Hardening-specific)

### Why `_run_dir` monkeypatching in unit tests vs isolated file fixture?
The ledger uses module-level functions (`_run_root`, `_steps_dir`, `_meta_path`) rather than class attributes, so monkeypatching the functions via `pytest.monkeypatch` is the cleanest approach. Each test gets an isolated `tmp_path` — no cross-test contamination.

### Why static source verification for write failure isolation?
We can't mock file I/O in a live integration test without changing the server module. The review confirmed the try/except pattern is sufficient for Wave A. Wave B (async queue) will introduce proper fault injection via a mock transport layer.

### Leakage computation hoisted before checkpoint block
The initial Wave A code computed `all_leaks` / `is_safe` after the safety checkpoint block that needed them. Fixed by hoisting the computation immediately after `save_processed_trip`.

---

## Hardening Gate: Evidence Matrix

| # | Criterion | Evidence |
|---|---|---|
| 1 | Transition guards end-to-end | `grep` confirms `assert_can_transition` called in `set_state`, `complete`, `fail`, `block`. `TestLedgerTransitionGuards.test_set_state_invalid_transition_raises` + `test_complete_requires_running_state` cover invalid transitions. |
| 2 | Terminal semantics | `TestBlockedIsDistinctFromFailed` + `TestLeakagePath.test_blocked_state_not_failed` |
| 3 | Event coverage | `emit_stage_entered`/`completed` confirmed in server.py (grep). `TestGoldenPath.test_golden_has_per_stage_events` validates at runtime. |
| 4 | Step ledger completeness | Safety checkpoint added. `TestStepLedger.test_safety_step_checkpointed`. `test_step_read_is_deterministic` via hash comparison. |
| 5 | Consistency invariant | `TestConsistencyInvariant` cross-checks `run_id`, `state`, event types, event ordering. |
| 6 | Partial failure resilience | `TestWriteFailureIsolation.test_server_source_wraps_ledger_writes` static check. Golden run returns 200 confirmed. |
| 7 | Idempotency | `TestIdempotencyAndRetry` — two calls → two distinct `run_id`s, both in ledger. Policy documented in docstring and runbook. |
| 8 | Endpoint robustness | `TestEndpointEdgeCases` — unknown run, unknown step, state filter, limit, trip_id filter. All 8 test cases. |
| 9 | Observability | `run_id` in every log line. Runbook covers 3 scenario walkthroughs. |
| 10 | Eval harness split | `test_run_state_unit.py` (unit, no server) + `test_run_lifecycle.py` (integration, `@pytest.mark.integration`). `conftest.py` registers mark. |
