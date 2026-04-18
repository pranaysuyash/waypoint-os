# Wave A — Agentic Flow v0: Scope & Brief
**Date**: 2026-04-18  
**Track**: Backend (parallel to Wave 2 frontend)  
**Do not**: replace `run_spine_once` or any existing orchestration logic  
**Do**: formalize run lifecycle, observability, and operator control plane around the existing spine pipeline

---

## Context

Existing primitives confirmed in repo scan:
- `orchestration.py` — `run_spine_once` (core pipeline)
- `server.py` — `POST /run` (API wrapper)
- `persistence.py` — audit scaffolding (JSON-based, file-backed)

The next leverage move is **not** a new AI brain. It is formalizing what happens to a run: before, during, after, and on failure.

---

## Deliverables

### 1. Run Lifecycle State Machine

A shared enum + transition guard helpers. States:

```
queued → running → completed
                 → failed
                 → blocked        ← strict leakage as first-class terminal
```

- Define in a shared module (e.g. `run_state.py`)
- Expose transition guards: `can_transition(from, to)` — prevents invalid state jumps
- `blocked` is not the same as `failed`: blocked means the pipeline detected a leakage condition or ambiguity that requires operator review, not a crash

### 2. Run Audit Trail (Event-Sourced)

Append-only events for every run. Emit on:

| Event | Payload |
|---|---|
| `run_started` | `run_id`, `trip_id`, `stage`, `timestamp` |
| `pipeline_stage_entered` | `run_id`, `stage_name`, `timestamp` |
| `pipeline_stage_completed` | `run_id`, `stage_name`, `execution_ms`, `timestamp` |
| `run_completed` | `run_id`, `trip_id`, `final_state`, `total_ms` |
| `run_failed` | `run_id`, `error_type`, `error_message`, `stage_at_failure` |
| `run_blocked` | `run_id`, `block_reason`, `stage_at_block` |

Storage: current JSON persistence (file-based). No new infra. One file per run or append to existing audit log.

### 3. Deterministic Step Ledger

Per-run checkpoints. Persist each stage's output with a timestamp:

```
runs/
  {run_id}/
    meta.json          ← run_id, trip_id, state, started_at, completed_at
    events.jsonl       ← append-only event log
    steps/
      packet.json      ← output of packet stage + timestamp
      validation.json  ← output of validation stage + timestamp
      decision.json    ← output of decision stage + timestamp
      strategy.json    ← output of strategy stage + timestamp
      safety.json      ← output of safety stage + timestamp
```

Goal: any run can be replayed or debugged from persisted outputs without re-execution.

### 4. Operator Status Endpoints

Three new read-only GET routes on top of existing `server.py`:

| Endpoint | Returns |
|---|---|
| `GET /runs/{run_id}` | Full run status + latest step output |
| `GET /runs?trip_id={id}` | Run history for a trip (most recent first) |
| `GET /runs/{run_id}/events` | Append-only event stream for a run |

No mutations. These are operator inspection endpoints.

### 5. Eval Harness for Flow Correctness

Three eval paths:

| Eval | What it verifies |
|---|---|
| **Golden path** | Run succeeds, all expected stage events emitted in correct order |
| **Failure path** | Injected failure at a stage produces correct terminal `failed` state + audit events |
| **Leakage path** | Strict leakage condition marks run as `blocked` (not `failed`), preserves step ledger up to block point |

Evals should be runnable without live LLM calls — use fixture inputs from `SYNTHETIC_DATA_AND_FIXTURES.md`.

### 6. Operator Handoff Runbook

One doc under `Docs/`: how to inspect a stuck or failed run, how to retry safely, what to trust in the logs first.

Covers:
- How to find a `run_id` from a `trip_id`
- How to read the event stream to identify where a run stopped
- How to distinguish `blocked` (needs operator review) from `failed` (system error)
- How to safely re-trigger a run without creating duplicate ledger entries

---

## What Does Not Change

- `run_spine_once` logic — do not touch
- `POST /run` request/response contract — do not break
- Existing persistence file format — extend, never rewrite
- Any frontend code — this is backend-only

---

## Files to Create

| File | Purpose |
|---|---|
| `backend/run_state.py` | State machine enum + transition guards |
| `backend/run_ledger.py` | Step ledger read/write helpers |
| `backend/run_events.py` | Event emission + append helpers |
| `backend/evals/test_run_lifecycle.py` | Golden/failure/leakage eval harness |
| `Docs/OPERATOR_RUN_RUNBOOK.md` | Operator inspection + retry doc |

Registered in `server.py`:
- `GET /runs/{run_id}` 
- `GET /runs`
- `GET /runs/{run_id}/events`

---

## Sequencing Relationship to Frontend Wave 2

These are **parallel tracks** — neither blocks the other:

| Track | Dependency | Can start |
|---|---|---|
| **Wave 2** (frontend layout) | `useTrip()` + `Trip` type — both exist | ✅ Now |
| **Wave A** (backend agentic flow) | `run_spine_once` — exists | ✅ Now |

Wave A's `/runs/{run_id}` endpoint will eventually be consumed by the workspace right-rail panel (operator can see run status inline). That connection happens in Wave 3+, not Wave 2.

---

*Scope locked 2026-04-18. No implementation in this session — brief for next agent session.*
