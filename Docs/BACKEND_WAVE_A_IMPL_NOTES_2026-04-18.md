# Wave A — Implementation Notes
**Date**: 2026-04-18  
**Status**: ✅ Implemented  
**Spec doc**: `BACKEND_WAVE_A_AGENTIC_FLOW_2026-04-18.md`

---

## Files Created

| File | Purpose |
|---|---|
| `spine-api/run_state.py` | State machine enum + transition guards |
| `spine-api/run_events.py` | Append-only JSONL event emitter per run |
| `spine-api/run_ledger.py` | Deterministic step ledger (read/write) |
| `tests/test_run_lifecycle.py` | Golden/leakage paths + state machine unit tests |
| `Docs/OPERATOR_RUN_RUNBOOK_2026-04-18.md` | Operator inspection + retry doc |

## Files Modified

| File | What |
|---|---|
| `spine-api/server.py` | Fixed 2 broken `from spine-api.persistence` imports (hyphen = invalid Python). Added Wave A imports. Instrumented `/run` handler with ledger + events. Added `/runs`, `/runs/{run_id}`, `/runs/{run_id}/steps/{step}`, `/runs/{run_id}/events` endpoints. |

---

## What Each Piece Does

### `run_state.py`
- `RunState` enum: `queued | running | completed | failed | blocked`
- `blocked` ≠ `failed`: blocked = policy violation needing operator review; failed = system error
- `can_transition(from, to)` — safe predicate check
- `assert_can_transition(from, to)` — raises `ValueError` on invalid transitions
- `terminal_state_for_run_result(ok, is_blocked)` — derives terminal state from API response

### `run_events.py`
- Events written to `data/runs/{run_id}/events.jsonl` (one JSON object per line, append-only)
- Convenience emitters: `emit_run_started`, `emit_run_completed`, `emit_run_failed`, `emit_run_blocked`, `emit_stage_entered`, `emit_stage_completed`
- `get_run_events(run_id)` reads chronologically

### `run_ledger.py`
- `RunLedger.create`, `set_state`, `save_step`, `complete`, `fail`, `block` — write operations
- `RunLedger.get_meta`, `get_step`, `get_all_steps`, `list_runs` — read operations
- File layout: `data/runs/{run_id}/meta.json` + `steps/{step_name}.json`
- `list_runs(trip_id, state, limit)` enables operator queries

### New API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /runs` | List all runs (filter: `trip_id`, `state`, `limit`) |
| `GET /runs/{run_id}` | Full run status + step checkpoint timestamps |
| `GET /runs/{run_id}/steps/{step}` | Full step output data |
| `GET /runs/{run_id}/events` | Chronological event stream |

### Bug Fixes in `server.py`

Two pre-existing import bugs fixed (`from spine-api.persistence import ...` — hyphen makes the module name invalid Python syntax; these lines would have caused `SyntaxError` at import time):
- Line 438: removed entirely (was a duplicate `from spine-api.persistence import ...` block)
- Line 634 (inside `list_assignments`): replaced with a comment noting `AssignmentStore` is already available at module scope

---

## Data Layout

```
data/runs/
  {run_id}/
    meta.json          ← { run_id, trip_id, state, stage, created_at, started_at, completed_at, total_ms }
    events.jsonl       ← append-only event log
    steps/
      packet.json      ← { step, run_id, checkpointed_at, data: {...} }
      validation.json
      decision.json
      strategy.json
```

---

## Design Decisions

**Errors in Wave A code do not fail the `/run` request.** Every ledger/event write is wrapped in `try/except` with `logger.error`. The user-facing response is never degraded by observability infrastructure failing. This is by design — the spine pipeline result is the primary contract; the ledger is secondary.

**`blocked` is a first-class terminal state** — not an alias for `failed`. This distinction matters for operator tooling: `GET /runs?state=blocked` queries policy violations requiring human review; `GET /runs?state=failed` queries system errors requiring engineering attention.

**File-based storage is intentional for Wave A.** No new infra (Redis, Postgres) is introduced. The `data/runs/` directory layout is structured for easy future migration to a DB: each `run_id` folder maps cleanly to a DB row + child tables.

---

## Verification

State machine unit tests require no live API — run with:
```bash
pytest tests/test_run_lifecycle.py::TestRunStateMachine -v
```

Full integration tests (golden + leakage paths) require a live `spine-api`:
```bash
# Start spine-api, then:
pytest tests/test_run_lifecycle.py -v
```
