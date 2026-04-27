# Implementation Plan: Async Spine Pipeline
## From Synchronous 504 → Durable Long-Running Workflow

**Date:** 2026-04-27
**Status:** Awaiting approval

---

## 1. Infrastructure Already Exists

The `run_ledger.py`, `run_events.py`, and `run_state.py` infrastructure is already a full async-compatible run tracking system:

### What the RunLedger Already Does
```
POST /run →
  RunLedger.create(run_id, trip_id=None, stage, mode)    → QUEUED
  RunLedger.set_state(run_id, RUNNING)                    → RUNNING
  emit_run_started(run_id, ...)                           → events.jsonl
  run_spine_once(...)                                      ← sync blocking
  save_step("packet", ...)                                 → steps/packet.json
  emit_stage_completed("packet", ...)                      → events.jsonl
  ... (same for validation, decision, strategy, safety)
  save_processed_trip(...)                                 → TripStore
  RunLedger.update(trip_id=...)                            → meta.json
  RunLedger.complete(run_id, total_ms)                     → COMPLETED
  emit_run_completed(run_id, ...)                          → events.jsonl
  return SpineRunResponse                                  ← 200 after 30-120s
```

### State Machine
```
QUEUED → RUNNING → COMPLETED  (normal execution)
                 → FAILED     (unexpected error)
                 → BLOCKED    (leakage violation)
```

### Event Types
- `run_started`
- `pipeline_stage_entered` (packet, validation, decision, strategy, safety, output)
- `pipeline_stage_completed` (with execution_ms per stage)
- `run_completed` (with total_ms)
- `run_failed` (with error_type, error_message, stage_at_failure)
- `run_blocked` (with block_reason, stage_at_block)

### What's Missing
- `GET /runs/{run_id}` — read meta + steps + events (backend)
- Background task execution instead of synchronous blocking
- `run_id → trip_id` update in meta.json after save_processed_trip completes inline
- Frontend polling for status
- Frontend progress UI

---

## 2. What Needs to Change

### 2.1 Backend: GET /runs/{run_id} endpoint

**New endpoint:**

```python
@app.get("/runs/{run_id}")
def get_run_status(run_id: str, agency: Agency = Depends(get_current_agency)):
    """
    Return the current state of a spine run: meta + steps + events.
    Frontend polls this to show progress.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Scope to agency: only show runs for this agency
    # (uses agency_id stored in run meta)
    
    steps = RunLedger.get_all_steps(run_id)
    events = get_run_events(run_id)
    
    return {
        "run_id": run_id,
        "state": meta.get("state"),
        "trip_id": meta.get("trip_id"),
        "started_at": meta.get("started_at"),
        "completed_at": meta.get("completed_at"),
        "total_ms": meta.get("total_ms"),
        "steps_completed": list(steps.keys()),
        "steps": steps,
        "events": events,
        "error": meta.get("error_message") if meta.get("state") == "failed" else None,
    }
```

### 2.2 Backend: Convert POST /run to async

**Current behavior:**
```python
@app.post("/run")
def run_spine(request, agency):
    run_id = uuid4()[:8]
    RunLedger.create(run_id, ...)        # QUEUED
    RunLedger.set_state(run_id, RUNNING) # RUNNING
    result = run_spine_once(...)         # BLOCKS for 30-120s
    # ... save, checkpoint, complete ...
    return SpineRunResponse              # returns after 30-120s
```

**New behavior — extract execution into background task:**
```python
async def _execute_spine_pipeline(run_id, request, agency):
    """Background task — runs the full pipeline and records results."""
    try:
        RunLedger.set_state(run_id, RunState.RUNNING)
        emit_run_started(...)
        
        result = run_spine_once(...)
        
        # Save trip, checkpoint steps, emit events
        trip_id = save_processed_trip(...)
        
        # Update meta with trip_id
        meta = RunLedger.get_meta(run_id)
        meta["trip_id"] = trip_id
        # write meta.json back
        
        RunLedger.complete(run_id, execution_ms)
        emit_run_completed(...)
    except Exception as e:
        RunLedger.fail(run_id, type(e).__name__, str(e))
        emit_run_failed(...)

@app.post("/run")
async def run_spine_async(request, agency, background_tasks: BackgroundTasks):
    """Submit a spine run. Returns run_id immediately. Poll /runs/{run_id} for status."""
    run_id = str(uuid4())[:8]
    
    RunLedger.create(run_id, trip_id=None, stage=request.stage, operating_mode=request.operating_mode)
    
    background_tasks.add_task(_execute_spine_pipeline, run_id, request, agency)
    
    return {"run_id": run_id, "state": "queued"}
```

**Why BackgroundTasks (not asyncio.create_task):**
- FastAPI BackgroundTasks are tied to the request lifecycle
- If the server restarts, in-flight tasks are lost (acceptable — agent sees error and clicks Retry)
- For persistence across restarts: Phase 3 adds a queue worker (Celery/Redis)
- For now, durability comes from RunLedger (meta.json persists to disk immediately)

### 2.3 Frontend: Polling hook

```typescript
// useSpineRun.ts — updated
async function execute(payload: SpineRunRequest) {
  setIsProcessing(true);
  setError(null);
  
  // 1. Submit run
  const { run_id } = await api.post("/api/spine/run", payload);
  setRunId(run_id);
  
  // 2. Poll for completion
  while (true) {
    await sleep(2000);
    const status = await api.get(`/api/runs/${run_id}`);
    
    setProgress(status);  // { state, steps_completed, total_ms, events }
    
    if (["completed", "failed", "blocked"].includes(status.state)) {
      setIsProcessing(false);
      if (status.state === "completed") {
        onComplete(status.trip_id);
      } else {
        setError(status.error);
      }
      return;
    }
  }
}
```

### 2.4 Frontend: Progress UI

```tsx
// In Workbench page.tsx — while processing
{isProcessing && (
  <div className="processing-panel">
    <div className="processing-header">
      <Spinner />
      <span>Processing trip...</span>
      <span className="elapsed">{formatElapsed(elapsed)}</span>
    </div>
    
    {/* Step-by-step progress */}
    <div className="steps">
      {STEPS.map(step => (
        <StepRow
          key={step.name}
          label={step.label}
          status={getStepStatus(step.name, progress.steps_completed)}
          duration={progress.events.find(e => e.stage_name === step.name)?.execution_ms}
        />
      ))}
    </div>
    
    {error && (
      <div className="error-panel">
        <p>{error}</p>
        <button onClick={retry}>Retry</button>
      </div>
    )}
  </div>
)}
```

### 2.5 Run ID → Trip ID Cleanup

When the pipeline completes and `save_processed_trip` is called, the trip_id needs to be written back to the run's meta.json. Currently the RunLedger doesn't have an `update` method — need to add one, or re-read/write the meta dict.

Add to RunLedger:
```python
@staticmethod
def update_meta(run_id: str, **kwargs) -> None:
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise FileNotFoundError(...)
    meta.update(kwargs)
    with _meta_path(run_id).open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
```

---

## 3. Files to Modify

| # | File | Change | Lines |
|---|------|--------|-------|
| B1 | `spine_api/server.py` | Add `GET /runs/{run_id}` endpoint | ~30 |
| B2 | `spine_api/server.py` | Convert `POST /run` to async background task | ~40 |
| B3 | `spine_api/run_ledger.py` | Add `update_meta()` method | ~10 |
| F1 | `frontend/src/hooks/useSpineRun.ts` | Replace sync execute with submit+poll | ~60 |
| F2 | `frontend/src/app/workbench/page.tsx` | Add progress UI with step tracking | ~50 |
| F3 | `frontend/src/app/api/runs/route.ts` | Already exists — works as-is | 0 |
| F4 | `frontend/src/app/api/spine/run/route.ts` | Removed; catch-all route-map is canonical for `/api/spine/run` | 0 |

**Total new code: ~200 lines. No new files. No duplicate routes.**

---

## 4. What Already Works / Architectural Constraints

- `RunLedger.create/get_meta/get_step/get_all_steps/list_runs` ✅
- `RunLedger.set_state/complete/fail/block` ✅
- `run_events.py` emit functions ✅
- `run_state.py` state machine + guards ✅
- `save_processed_trip` with agency_id ✅
- Agency scoping on `/run` and `/runs/*` endpoints ✅
- Catch-all frontend proxy for /api/runs ✅
- `POST /run` is async-only; no synchronous fallback route is retained ✅
- `frontend/src/app/api/spine/run/route.ts` was removed because the route-map catch-all is the canonical BFF path for `/api/spine/run` ✅

---

## 5. Verification Plan and Recovery Evidence

Required behavior:

1. **Backend test:** `curl POST /run` → returns `{run_id, state: "queued"}` immediately (<100ms)
2. **Backend test:** `curl GET /runs/{run_id}` → returns `{state: "running", steps_completed: ["packet"]}`
3. **Backend test:** Repeat GET until `{state: "completed", trip_id: "trip_xxx"}`
4. **Frontend test:** Click Process Trip → see progress UI with step-by-step updates
5. **Frontend test:** On completion → auto-redirect to workspace
6. **Frontend test:** Kill backend mid-run → retry works (error shown, Retry button)
7. **Singapore scenario:** Run all 3 test input variants, verify trips created + scoped correctly

Recovery verification recorded on 2026-04-27:

- `python -m py_compile spine_api/server.py spine_api/contract.py spine_api/run_ledger.py` passed.
- `uv run pytest -q tests/test_run_state_unit.py` passed: 46 tests.
- `./node_modules/.bin/tsc --noEmit` passed from `frontend/`.
- `npm run build` passed from `frontend/`; route output showed `/api/[...path]` and no explicit duplicate `/api/spine/run` route.
- Live backend health returned 200 at `http://127.0.0.1:8000/health`.
- Live frontend health returned 200 at `http://127.0.0.1:3000/api/health`.
- Unauthenticated `GET /api/runs/00000000-0000-4000-8000-000000000000` reached the backend and returned `401 Not authenticated`, proving the canonical `/api/runs/{id}` polling path is mapped.

Known remaining limitation:

- The async contract removes the HTTP timeout and gives the frontend a durable run_id immediately. Real per-phase progress is still coarse until `run_spine_once()` / orchestration emits phase events during execution rather than after the blocking call returns.

---

## 6. No Duplicate Routes

The existing `POST /run` is the ONLY run submission endpoint. The new `GET /runs/{run_id}` is a read-only status endpoint. No duplicate paths. No `/run/async`. No `/run/v2`.

---

**Plan complete.** Approve and I'll implement.
