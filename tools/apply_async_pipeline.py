#!/usr/bin/env python3
"""Apply all remaining async pipeline changes to spine_api/server.py"""
import sys

path = "spine_api/server.py"

with open(path, "r") as f:
    content = f.read()

# --- 1. Add import asyncio ---
if "import asyncio" not in content:
    content = content.replace(
        "import json\nimport logging",
        "import asyncio\nimport json\nimport logging",
        1,
    )

# --- 2. Add BackgroundTasks to fastapi import ---
content = content.replace(
    "from fastapi import Depends, FastAPI, HTTPException",
    "from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException",
    1 if "BackgroundTasks" not in content else 0,
)

# --- 3. Add RunAcceptedResponse, RunStatusResponse to contract imports ---
content = content.replace(
    "SpineRunRequest,\n    SpineRunResponse,\n    OverrideRequest,",
    "SpineRunRequest,\n    SpineRunResponse,\n    RunAcceptedResponse,\n    RunStatusResponse,\n    OverrideRequest,",
    1,
)

# --- 4. Add _execute_spine_pipeline before @app.post("/run") ---
background_fn = '''

def _execute_spine_pipeline(
    run_id: str,
    request_dict: dict,
    agency_id: str,
) -> None:
    """Background executor for the spine pipeline. Single-call site: POST /run."""
    t0 = time.perf_counter()

    request = SpineRunRequest(**request_dict)
    if request.strict_leakage:
        set_strict_mode(True)

    RunLedger.set_state(run_id, RunState.RUNNING)
    emit_run_started(
        run_id=run_id,
        trip_id=None,
        stage=request.stage,
        operating_mode=request.operating_mode,
    )

    meta = RunMeta(
        stage=request.stage,
        operating_mode=request.operating_mode,
        fixture_id=request.scenario_id,
        execution_ms=0.0,
    )

    try:
        envelopes = build_envelopes(request_dict)
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = AgencySettingsStore.load(agency_id)

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)

        logger.info(
            "spine_run ok=True run_id=%s stage=%s mode=%s execution_ms=%.2f agency_id=%s",
            run_id, request.stage, request.operating_mode, execution_ms, agency_id,
        )

        trip_id_saved: Optional[str] = None
        try:
            trip_id_saved = save_processed_trip(
                {
                    "run_id": run_id,
                    "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                    "strategy": _to_dict(result.strategy) if hasattr(result, "strategy") else None,
                    "meta": meta.model_dump(),
                },
                source="spine_api",
                agency_id=agency_id,
            )
            logger.info("Trip saved: %s", trip_id_saved)

            if trip_id_saved:
                RunLedger.update_meta(run_id, trip_id=trip_id_saved)
                trip_post = TripStore.get_trip(trip_id_saved)
                if trip_post and trip_post.get("analytics", {}).get("feedback_reopen"):
                    from src.analytics.review import trigger_feedback_recovery
                    trigger_feedback_recovery(trip_id_saved, reason=trip_post["analytics"].get("review_reason"))
        except Exception as e:
            logger.error("Failed to save trip: %s", e)
            raise RuntimeError(f"Trip persistence failed for run {run_id}: {e}") from e

        all_leaks: List[str] = (
            result.leakage_result.get("leaks", [])
            if hasattr(result, "leakage_result") and result.leakage_result
            else []
        )
        is_safe: bool = (
            result.leakage_result.get("is_safe", len(all_leaks) == 0)
            if hasattr(result, "leakage_result") and result.leakage_result
            else len(all_leaks) == 0
        )

        try:
            for step_name, step_attr in [
                ("packet", "packet"), ("validation", "validation"),
                ("decision", "decision"), ("strategy", "strategy"),
            ]:
                if hasattr(result, step_attr):
                    val = _to_dict(getattr(result, step_attr))
                    if val is not None:
                        t_step = time.perf_counter()
                        emit_stage_entered(run_id, step_name, trip_id=trip_id_saved)
                        RunLedger.save_step(run_id, step_name, val)
                        emit_stage_completed(
                            run_id, step_name,
                            execution_ms=(time.perf_counter() - t_step) * 1000,
                            trip_id=trip_id_saved,
                        )

            if hasattr(result, "leakage_result") and result.leakage_result:
                safety_payload = {
                    "strict_leakage": request.strict_leakage,
                    "leakage_passed": is_safe,
                    "leakage_errors": all_leaks,
                    "raw": result.leakage_result,
                }
                emit_stage_entered(run_id, "safety", trip_id=trip_id_saved)
                RunLedger.save_step(run_id, "safety", safety_payload)
                emit_stage_completed(run_id, "safety", execution_ms=0.0, trip_id=trip_id_saved)
        except Exception as e:
            logger.error("Wave A: step checkpoint failed run_id=%s error=%s", run_id, e)

        try:
            RunLedger.complete(run_id, total_ms=execution_ms)
            emit_run_completed(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
        except Exception as e:
            logger.error("Wave A: ledger complete failed for run %s: %s", run_id, e)

    except ValueError as e:
        execution_ms = (time.perf_counter() - t0) * 1000
        error_message = str(e)
        logger.warning(
            "spine_run ok=False run_id=%s strict_leakage=True error=%s execution_ms=%.2f",
            run_id, error_message, execution_ms,
        )
        try:
            RunLedger.block(run_id, block_reason=error_message)
            emit_run_blocked(run_id=run_id, block_reason=error_message, trip_id=None)
        except Exception as ledger_err:
            logger.error("Wave A: block ledger failed for run %s: %s", run_id, ledger_err)

    except Exception as e:
        execution_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            "spine_run FAILED run_id=%s error_type=%s error=%s execution_ms=%.2f",
            run_id, type(e).__name__, e, execution_ms,
        )
        try:
            RunLedger.fail(run_id, error_type=type(e).__name__, error_message=str(e))
            emit_run_failed(
                run_id=run_id, error_type=type(e).__name__,
                error_message=str(e), trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: fail ledger failed for run %s: %s", run_id, ledger_err)


'''

# Insert before @app.post("/run")
marker = '\n\n@app.post("/run", response_model=SpineRunResponse)'
if marker in content and "_execute_spine_pipeline" not in content:
    content = content.replace(marker, background_fn + marker, 1)

# --- 5. Replace sync POST /run with async version ---
old_run = '''@app.post("/run", response_model=SpineRunResponse)
def run_spine(
    request: SpineRunRequest,
    agency: Agency = Depends(get_current_agency),
) -> SpineRunResponse:
    """
    Execute one spine run, returning the canonical SpineRunResponse.

    Always returns 200 with a SpineRunResponse.
    - ok=True + populated fields: spine completed normally
    - ok=False + null fields: strict leakage violation (traveler_bundle suppressed)
    - HTTPException (500): internal error (non-leakage)
    """
    run_id = str(uuid.uuid4())[:8]
    t0 = time.perf_counter()

    if request.strict_leakage:
        set_strict_mode(True)

    meta = RunMeta(
        stage=request.stage,
        operating_mode=request.operating_mode,
        fixture_id=request.scenario_id,
        execution_ms=0.0,
    )

    # Wave A: create ledger entry and emit run_started
    RunLedger.create(
        run_id=run_id,
        trip_id=None,  # trip_id assigned after save_processed_trip completes
        stage=request.stage,
        operating_mode=request.operating_mode,
    )
    RunLedger.set_state(run_id, RunState.RUNNING)
    emit_run_started(
        run_id=run_id,
        trip_id=None,
        stage=request.stage,
        operating_mode=request.operating_mode,
    )

    try:
        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = AgencySettingsStore.load("waypoint-hq")

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)

        logger.info(
            "spine_run ok=True run_id=%s stage=%s mode=%s scenario_id=%s execution_ms=%.2f agency_id=%s",
            run_id,
            request.stage,
            request.operating_mode,
            request.scenario_id,
            execution_ms,
            agency.id,
        )

        # Save the trip to persistence scoped to the user's agency
        trip_id_saved: Optional[str] = None
        try:
            trip_id_saved = save_processed_trip(
                {
                    "run_id": run_id,
                    "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                    "strategy": _to_dict(result.strategy) if hasattr(result, "strategy") else None,
                    "meta": meta.model_dump(),
                },
                source="spine_api",
                agency_id=agency.id,
            )
            logger.info("Trip saved: %s", trip_id_saved)
            
            # Wave 10: Feedback-Driven Recovery Trigger
            if trip_id_saved:
                trip_post = TripStore.get_trip(trip_id_saved)
                if trip_post and trip_post.get("analytics", {}).get("feedback_reopen"):
                    from src.analytics.review import trigger_feedback_recovery
                    trigger_feedback_recovery(trip_id_saved, reason=trip_post["analytics"].get("review_reason"))
                    logger.info("Feedback recovery triggered for trip: %s", trip_id_saved)
        except Exception as e:
            logger.error("Failed to save trip: %s", e)
            # Don't fail the request if saving fails

        # Compute leakage results first — used both by checkpoint and response
        all_leaks: List[str] = (
            result.leakage_result.get("leaks", [])
            if hasattr(result, "leakage_result") and result.leakage_result
            else []
        )
        is_safe: bool = (
            result.leakage_result.get("is_safe", len(all_leaks) == 0)
            if hasattr(result, "leakage_result") and result.leakage_result
            else len(all_leaks) == 0
        )

        # Wave A: checkpoint each step with per-stage events (criteria 3 + 4)
        # safety is checkpointed from leakage_result which is available post-run.
        # emit_stage_entered / completed are emitted around each save_step to provide
        # a granular event stream even though run_spine_once is a single call.
        try:
            for step_name, step_attr in [
                ("packet",     "packet"),
                ("validation", "validation"),
                ("decision",   "decision"),
                ("strategy",   "strategy"),
            ]:
                if hasattr(result, step_attr):
                    val = _to_dict(getattr(result, step_attr))
                    if val is not None:
                        t_step = time.perf_counter()
                        emit_stage_entered(run_id, step_name, trip_id=trip_id_saved)
                        RunLedger.save_step(run_id, step_name, val)
                        emit_stage_completed(
                            run_id, step_name,
                            execution_ms=(time.perf_counter() - t_step) * 1000,
                            trip_id=trip_id_saved,
                        )

            # Checkpoint safety separately from leakage_result
            if hasattr(result, "leakage_result") and result.leakage_result:
                safety_payload = {
                    "strict_leakage": request.strict_leakage,
                    "leakage_passed": is_safe,
                    "leakage_errors": all_leaks,
                    "raw": result.leakage_result,
                }
                emit_stage_entered(run_id, "safety", trip_id=trip_id_saved)
                RunLedger.save_step(run_id, "safety", safety_payload)
                emit_stage_completed(run_id, "safety", execution_ms=0.0, trip_id=trip_id_saved)

        except Exception as e:
            logger.error(
                "Wave A: step checkpoint failed run_id=%s error=%s",
                run_id, e,
            )




        assertions_out: Optional[List[AssertionResult]] = None
        if result.assertion_result is not None:
            assertions_out = [
                AssertionResult(
                    type=a.get("type", ""),
                    passed=a.get("passed", False),
                    message=a.get("message", ""),
                    field=a.get("field"),
                )
                for a in result.assertion_result.get("assertions", [])
            ]

        # Wave A: complete the ledger and emit terminal event
        try:
            RunLedger.complete(run_id, total_ms=execution_ms)
            emit_run_completed(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
        except Exception as e:
            logger.error("Wave A: ledger complete failed for run %s: %s", run_id, e)

        return SpineRunResponse(
            ok=True,
            run_id=run_id,
            packet=_to_dict(result.packet) if hasattr(result, "packet") else None,
            validation=_to_dict(result.validation) if hasattr(result, "validation") else None,
            decision=_to_dict(result.decision) if hasattr(result, "decision") else None,
            strategy=_to_dict(result.strategy) if hasattr(result, "strategy") else None,
            traveler_bundle=serialize_bundle(result.traveler_bundle, traveler_safe=True)
            if result.traveler_bundle is not None
            else None,
            internal_bundle=serialize_bundle(result.internal_bundle)
            if hasattr(result, "internal_bundle") and result.internal_bundle is not None
            else None,
            safety=SafetyResult(
                strict_leakage=request.strict_leakage,
                leakage_passed=is_safe,
                leakage_errors=all_leaks,
            ),
            fees=_to_dict(result.fees) if hasattr(result, "fees") else None,
            autonomy_outcome=AutonomyOutcome(**result.autonomy_outcome.to_dict())
            if hasattr(result, "autonomy_outcome") and result.autonomy_outcome is not None
            else None,
            assertions=assertions_out,
            meta=meta,
        )

    except ValueError as e:
        # Strict leakage violation — traveler_bundle suppressed, ok=False
        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)

        error_message = str(e)
        logger.warning(
            "spine_run ok=False run_id=%s strict_leakage=True error=%s execution_ms=%.2f",
            run_id,
            error_message,
            execution_ms,
        )

        # Wave A: mark as BLOCKED (distinct from FAILED)
        try:
            RunLedger.block(run_id, block_reason=error_message)
            emit_run_blocked(run_id=run_id, block_reason=error_message, trip_id=None)
        except Exception as ledger_err:
            logger.error("Wave A: block ledger failed for run %s: %s", run_id, ledger_err)

        return SpineRunResponse(
            ok=False,
            run_id=run_id,
            packet=None,
            validation=None,
            decision=None,
            strategy=None,
            traveler_bundle=None,
            internal_bundle=None,
            safety=SafetyResult(
                strict_leakage=True,
                leakage_passed=False,
                leakage_errors=[error_message],
            ),
            meta=meta,
        )

    except Exception as e:
        execution_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            "spine_run error run_id=%s type=%s error=%s execution_ms=%.2f",
            run_id,
            type(e).__name__,
            str(e),
            execution_ms,
        )

        # Wave A: mark as FAILED
        try:
            RunLedger.fail(run_id, error_type=type(e).__name__, error_message=str(e))
            emit_run_failed(
                run_id=run_id,
                error_type=type(e).__name__,
                error_message=str(e),
                trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: fail ledger failed for run %s: %s", run_id, ledger_err)

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__,
                "run_id": run_id,
            },
        )

    finally:
        # Reset strict mode after every request to prevent state leaking to the next
        set_strict_mode(False)'''

new_run = '''
@app.post("/run", response_model=RunAcceptedResponse)
async def run_spine(
    request: SpineRunRequest,
    background_tasks: BackgroundTasks,
    agency: Agency = Depends(get_current_agency),
) -> RunAcceptedResponse:
    """
    Submit a spine run for async execution. Returns immediately with a run_id.
    Poll GET /runs/{run_id} for status, events, and the eventual trip_id.
    Mode: This is the canonical path. There is no synchronous fallback.
    """
    run_id = str(uuid.uuid4())

    RunLedger.create(
        run_id=run_id,
        trip_id=None,
        stage=request.stage,
        operating_mode=request.operating_mode,
        agency_id=agency.id,
    )

    request_dict = request.model_dump(exclude_none=True)
    asyncio.create_task(asyncio.to_thread(_execute_spine_pipeline, run_id, request_dict, agency.id))

    logger.info("spine_run queued run_id=%s agency_id=%s", run_id, agency.id)
    return RunAcceptedResponse(run_id=run_id, state="queued")
'''

content = content.replace(old_run, new_run, 1)

# --- 6. Add agency scoping to /runs endpoints ---

# 6a: /runs list
content = content.replace(
    '@app.get("/runs")\ndef list_runs(\n    trip_id: Optional[str] = None,\n    state: Optional[str] = None,\n    limit: int = 50,\n):',
    '@app.get("/runs")\ndef list_runs(\n    trip_id: Optional[str] = None,\n    state: Optional[str] = None,\n    limit: int = 50,\n    agency: Agency = Depends(get_current_agency),\n):',
    1,
)
content = content.replace(
    '    runs = RunLedger.list_runs(trip_id=trip_id, state=state, limit=limit)\n    return {"items": runs, "total": len(runs)}',
    '    runs = RunLedger.list_runs(trip_id=trip_id, state=state, limit=limit)\n    agency_runs = [r for r in runs if r.get("agency_id") == agency.id]\n    return {"items": agency_runs, "total": len(agency_runs)}',
    1,
)

# 6b: /runs/{run_id}
content = content.replace(
    '@app.get("/runs/{run_id}")\ndef get_run_status(run_id: str):',
    '@app.get("/runs/{run_id}")\ndef get_run_status(\n    run_id: str,\n    agency: Agency = Depends(get_current_agency),\n):',
    1,
)
content = content.replace(
    '    meta = RunLedger.get_meta(run_id)\n    if meta is None:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n\n    steps = RunLedger.get_all_steps(run_id)\n    return {\n        **meta,\n        "steps": {name: step.get("checkpointed_at") for name, step in steps.items()},\n        "steps_available": list(steps.keys()),\n    }',
    '    meta = RunLedger.get_meta(run_id)\n    if meta is None:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n    if meta.get("agency_id") != agency.id:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n\n    steps = RunLedger.get_all_steps(run_id)\n    events = get_run_events(run_id)\n    return {\n        **meta,\n        "steps_completed": list(steps.keys()),\n        "events": events,\n    }',
    1,
)

# 6c: /runs/{run_id}/steps/{step_name}
content = content.replace(
    '@app.get("/runs/{run_id}/steps/{step_name}")\ndef get_run_step(run_id: str, step_name: str):',
    '@app.get("/runs/{run_id}/steps/{step_name}")\ndef get_run_step(\n    run_id: str,\n    step_name: str,\n    agency: Agency = Depends(get_current_agency),\n):',
    1,
)
content = content.replace(
    '    meta = RunLedger.get_meta(run_id)\n    if meta is None:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n\n    step = RunLedger.get_step(run_id, step_name)\n    if step is None:\n        raise HTTPException(\n            status_code=404,\n            detail=f"Step \'{step_name}\' not yet checkpointed for run {run_id}",\n        )\n    return step',
    '    meta = RunLedger.get_meta(run_id)\n    if meta is None:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n    if meta.get("agency_id") != agency.id:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n\n    step = RunLedger.get_step(run_id, step_name)\n    if step is None:\n        raise HTTPException(\n            status_code=404,\n            detail=f"Step \'{step_name}\' not yet checkpointed for run {run_id}",\n        )\n    return step',
    1,
)

# 6d: /runs/{run_id}/events
content = content.replace(
    '@app.get("/runs/{run_id}/events")\ndef get_run_event_stream(run_id: str):',
    '@app.get("/runs/{run_id}/events")\ndef get_run_event_stream(\n    run_id: str,\n    agency: Agency = Depends(get_current_agency),\n):',
    1,
)
content = content.replace(
    '    events = get_run_events(run_id)\n    return {"run_id": run_id, "events": events, "total": len(events)}',
    '    meta = RunLedger.get_meta(run_id)\n    if meta is None:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n    if meta.get("agency_id") != agency.id:\n        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")\n\n    events = get_run_events(run_id)\n    return {"run_id": run_id, "events": events, "total": len(events)}',
    1,
)

with open(path, "w") as f:
    f.write(content)

print("All changes applied successfully")
print(f"Lines: {len(content.splitlines())}")
