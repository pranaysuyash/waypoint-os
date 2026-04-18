# Operator Run Runbook
**Date**: 2026-04-18  
**Scope**: Inspecting, debugging, and safely retrying spine runs  
**Applies to**: spine-api Wave A and later

---

## What a "run" is

Every call to `POST /run` creates one run record. Runs have a lifecycle:

```
queued → running → completed   ← normal success
                → blocked      ← strict leakage violation (policy, not crash)
                → failed       ← unexpected error (exception, infra)
```

**`blocked` ≠ `failed`:**
- `failed` means the system crashed or errored. Something went wrong with infrastructure or code.
- `blocked` means the pipeline ran correctly but the output violated the leakage policy. This requires operator review of the trip content, not a bug fix.

---

## Finding a run

### By run_id (fastest)

Every `/run` response includes `run_id`. It's also logged on the server:
```
spine_run ok=True run_id=abc12345 stage=discovery ...
```

Once you have a `run_id`:
```bash
curl http://localhost:8000/runs/abc12345
```

### By trip_id

```bash
curl "http://localhost:8000/runs?trip_id=trip_xyz123abc"
```

### Most recent runs

```bash
curl "http://localhost:8000/runs?limit=20"
```

Filter by state:
```bash
curl "http://localhost:8000/runs?state=blocked"
curl "http://localhost:8000/runs?state=failed"
```

---

## Reading a run's event stream

The event log is the most reliable source of truth for what happened inside a run:

```bash
curl http://localhost:8000/runs/abc12345/events
```

Expected events on a successful run:
```json
[
  { "event_type": "run_started",   "stage": "discovery", ... },
  { "event_type": "run_completed", "total_ms": 4231.5, ... }
]
```

On a blocked run:
```json
[
  { "event_type": "run_started", ... },
  { "event_type": "run_blocked", "block_reason": "...", ... }
]
```

On a failed run:
```json
[
  { "event_type": "run_started", ... },
  { "event_type": "run_failed",  "error_type": "...", "error_message": "...", ... }
]
```

**Rule**: If you see `run_blocked`, look at `block_reason` in the event. The issue is in the trip content, not the code. If you see `run_failed`, look at `error_type` and `error_message` — this is likely a code or config issue.

---

## Reading checkpointed step outputs

Each pipeline stage is checkpointed to disk as it completes. You can inspect what the pipeline produced up to the point it stopped, without re-running anything:

```bash
# See which steps were checkpointed
curl http://localhost:8000/runs/abc12345
# → { "steps_available": ["packet", "validation", "decision", "strategy"], ... }

# Read a specific step's output
curl http://localhost:8000/runs/abc12345/steps/decision
```

On disk:
```
data/runs/abc12345/
    meta.json             ← run state, timing, trip_id
    events.jsonl          ← append-only event stream
    steps/
        packet.json
        validation.json
        decision.json
        strategy.json
```

---

## Diagnosing a stuck or failed run

**Step 1**: Get the run's event stream
```bash
curl http://localhost:8000/runs/{run_id}/events
```

**Step 2**: Find the last event. If the last event is `run_started` with no terminal event (`run_completed`, `run_failed`, `run_blocked`), the run may be in-flight (if the server just started), or it crashed before writing its terminal event.

**Step 3**: Check `meta.json` on disk:
```bash
cat data/runs/{run_id}/meta.json
```

If `state` is still `"running"` after the server has been idle for >30 seconds, the run crashed without writing a terminal event. In this case:
- The server process likely restarted mid-run
- The checkpointed steps (in `steps/`) are valid up to the last checkpoint
- The run will not auto-resume — a new run must be triggered

**Step 4**: Check server logs for the `run_id`:
```bash
grep run_id=abc12345 backend.log
```

---

## Distinguishing blocked vs failed: checklist

| Symptom | Likely cause | Action |
|---|---|---|
| `state: "blocked"`, `run_blocked` event | Strict leakage in pipeline output | Review trip content; check `block_reason`; re-run with corrected traveller note |
| `state: "failed"`, `run_failed` event | Code or infra error | Check `error_type` and `error_message`; check server logs |
| `state: "running"` after >30s idle | Server restart mid-run | Trigger a new run; old steps are preserved on disk |
| `state: "queued"` | Run registered but never started | Not expected in current single-worker setup; check for startup errors |

---

## Retrying safely

Retrying does **not** overwrite the original run. Every call to `POST /run` creates a new `run_id` and a new ledger entry. Old runs are preserved.

Safe retry:
1. Call `POST /run` again with the same payload
2. Check the new `run_id` via `GET /runs/{new_run_id}`
3. Old run's checkpoints remain at `data/runs/{old_run_id}/`

**Do not** manually edit `meta.json` to reset state — this will create inconsistency between the meta state and the event log.

---

## Logs to trust first

In order of reliability:

1. **Event log** (`GET /runs/{run_id}/events` or `data/runs/{run_id}/events.jsonl`) — most reliable; append-only, never overwritten
2. **meta.json** (`GET /runs/{run_id}`) — reflects final state after write; may be stale if server crashed before writing
3. **Server log** (`backend.log`) — most verbose but may be rotated or truncated; grep by `run_id`

---

## Monitoring threshold for removing compat redirects (Wave 3)

Wave 1L introduced compat redirects from `/workspace/{tripId}/{stage}` → workbench. 
These should only be removed when:

1. A real panel exists at the stage route AND
2. The native-stage success rate is observable (track via analytics or logs)

To query blocked runs (use as proxy for "trips that need attention"):
```bash
curl "http://localhost:8000/runs?state=blocked&limit=50"
```

---

*Written 2026-04-18. Update after Wave B (async queue) changes the lifecycle model.*
