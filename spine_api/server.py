"""
spine_api — FastAPI service exposing run_spine_once as an HTTP endpoint.

Architecture:
    Next.js (BFF)  →  HTTP POST /run  →  FastAPI spine_api  →  run_spine_once
                                                           (persistent process,
                                                            modules pre-loaded)

Canonical response contract (always returned, never raises):
    {
        ok: bool,
        run_id: str,
        packet: object | null,
        validation: object | null,
        decision: object | null,
        strategy: object | null,
        traveler_bundle: object | null,   # null on strict leakage failure
        internal_bundle: object | null,
        safety: { strict_leakage, leakage_passed, leakage_errors },
        assertions: [{ type, passed, message, field }] | null,  # populated when scenario_id provided
        meta: { stage, operating_mode, fixture_id, execution_ms }
    }

On non-leakage errors: raises HTTPException (500)

Environment variables:
    SPINE_API_HOST       — bind address (default: 127.0.0.1)
    SPINE_API_PORT       — port (default: 8000)
    SPINE_API_WORKERS    — number of uvicorn workers (default: 1)
    SPINE_API_CORS       — comma-separated allowed CORS origins
    SPINE_API_RELOAD     — set to 0 to disable dev reload
    TRAVELER_SAFE_STRICT — set to 1 to enable strict leakage globally
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root to Python path so we can import from src
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_user
from spine_api.core.middleware import AuthMiddleware

from spine_api.contract import (
    SafetyResult,
    AssertionResult,
    AutonomyOutcome,
    RunMeta,
    SpineRunRequest,
    SpineRunResponse,
    OverrideRequest,
    OverrideResponse,
    HealthResponse,
    TimelineEvent,
    TimelineResponse,
    ReviewActionRequest,
    SuitabilityAcknowledgeRequest,
    SnoozeRequest,
    InviteTeamMemberRequest,
    PipelineStageConfig,
    ApprovalThresholdConfig,
    ExportRequest,
    ExportResponse,
    UpdateOperationalSettings,
    UpdateAutonomyPolicy,
    UnifiedStateResponse,
    DashboardStatsResponse,
)

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.safety import set_strict_mode

# Import persistence logic
try:
    from . import persistence
except (ImportError, ValueError):
    import persistence

TripStore = persistence.TripStore
AssignmentStore = persistence.AssignmentStore
AuditStore = persistence.AuditStore
OverrideStore = persistence.OverrideStore
TeamStore = persistence.TeamStore
ConfigStore = persistence.ConfigStore
save_processed_trip = persistence.save_processed_trip

# Import TimelineEventMapper from analytics
# Note: logger not available yet, so we suppress warnings here
try:
    from src.analytics.logger import TimelineEventMapper
except ImportError:
    TimelineEventMapper = None

# Import Watchdog
try:
    from .watchdog import watchdog
except (ImportError, ValueError):
    try:
        from watchdog import watchdog  # type: ignore[attr-defined]
    except ImportError:
        # When spine_api is not a package (e.g., uvicorn spine_api.server:app),
        # load the local watchdog module directly from the filesystem.
        import importlib.util
        _watchdog_path = str(Path(__file__).resolve().parent / "watchdog.py")
        _watchdog_spec = importlib.util.spec_from_file_location("_local_watchdog", _watchdog_path)
        _watchdog_mod = importlib.util.module_from_spec(_watchdog_spec)  # type: ignore[arg-type]
        _watchdog_spec.loader.exec_module(_watchdog_mod)  # type: ignore[union-attr]
        watchdog = _watchdog_mod.watchdog

# Wave A: run lifecycle modules
from spine_api.run_state import RunState, assert_can_transition, terminal_state_for_run_result
from spine_api.run_events import (
    emit_run_started,
    emit_run_completed,
    emit_run_failed,
    emit_run_blocked,
    emit_stage_entered,
    emit_stage_completed,
    get_run_events,
)
from spine_api.run_ledger import RunLedger
from src.intake.config.agency_settings import AgencySettingsStore
from src.analytics.policy_rules import ready_gate_failures

# Auth — Phase 1
try:
    from routers import auth as auth_router
    from routers import workspace as workspace_router
    from routers import frontier as frontier_router
except (ImportError, ValueError):
    import importlib.util
    _base = Path(__file__).resolve().parent
    _auth_spec = importlib.util.spec_from_file_location("routers.auth", _base / "routers" / "auth.py")
    _auth_mod = importlib.util.module_from_spec(_auth_spec)
    _auth_spec.loader.exec_module(_auth_mod)
    auth_router = _auth_mod

    _ws_spec = importlib.util.spec_from_file_location("routers.workspace", _base / "routers" / "workspace.py")
    _ws_mod = importlib.util.module_from_spec(_ws_spec)
    _ws_spec.loader.exec_module(_ws_mod)
    workspace_router = _ws_mod

    _fr_spec = importlib.util.spec_from_file_location("routers.frontier", _base / "routers" / "frontier.py")
    _fr_mod = importlib.util.module_from_spec(_fr_spec)
    _fr_spec.loader.exec_module(_fr_mod)
    frontier_router = _fr_mod

logger = logging.getLogger("spine_api")

if TimelineEventMapper is None:
    logger.warning("TimelineEventMapper not available - timeline endpoint will use fallback")

# Pydantic models imported from spine_api/contract.py (canonical contract)
# All response schemas are defined there. Do not add new models here.


# =============================================================================
# Runtime config
# =============================================================================

HOST = os.environ.get("SPINE_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("SPINE_API_PORT", "8000"))
WORKERS = int(os.environ.get("SPINE_API_WORKERS", "1"))
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "SPINE_API_CORS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]

if os.environ.get("TRAVELER_SAFE_STRICT", "").strip() in ("1", "true", "yes"):
    set_strict_mode(True)

# =============================================================================
# Lifespan handler
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager (replaces deprecated on_event)."""
    # Startup
    watchdog.start()
    _seed_scenario()
    logger.info("Spine API startup complete")
    yield
    # Shutdown
    watchdog.stop()
    logger.info("Spine API shutdown complete")


# =============================================================================
# FastAPI app
# =============================================================================

app = FastAPI(
    title="Spine API",
    description="Canonical HTTP wrapper around run_spine_once",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

# Phase 1: Auth + Workspace routers
app.include_router(auth_router.router)
app.include_router(
    workspace_router.router,
    dependencies=[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else [],
)
app.include_router(frontier_router.router)


def _seed_scenario():
    """
    Load a scenario fixture at startup if SEED_SCENARIO env var is set.

    Usage: SEED_SCENARIO=scenario_alpha uvicorn spine_api.server:app

    This seeds the TripStore with fixture data for deterministic testing.
    If the env var is set to a filename (without .json) in data/fixtures/,
    all trips from that file are loaded into persistence.
    """
    seed_name = os.environ.get("SEED_SCENARIO", "").strip()
    if not seed_name:
        return

    fixture_path = PROJECT_ROOT / "data" / "fixtures" / f"{seed_name}.json"
    if not fixture_path.exists():
        logger.warning("SEED_SCENARIO: fixture not found: %s", fixture_path)
        return

    try:
        with open(fixture_path) as f:
            trips = json.load(f)

        if not isinstance(trips, list):
            logger.warning("SEED_SCENARIO: fixture must be a JSON array of trips")
            return

        loaded = 0
        for trip_data in trips:
            trip_id = trip_data.get("id")
            if not trip_id:
                continue

            existing = TripStore.get_trip(trip_id)
            if existing:
                continue

            trip_record = {
                "id": trip_id,
                "run_id": f"seed_{trip_id}",
                "source": "seed_scenario",
                "status": trip_data.get("status", "new"),
                "created_at": trip_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                "updated_at": trip_data.get("updated_at"),
                "extracted": trip_data.get("extracted"),
                "validation": trip_data.get("validation"),
                "decision": trip_data.get("decision"),
                "analytics": trip_data.get("analytics"),
                "assigned_to": trip_data.get("assignedTo"),
                "assigned_to_name": trip_data.get("assignedToName"),
                "meta": trip_data.get("meta", {"stage": trip_data.get("status", "new"), "seed": True}),
            }

            TripStore.save_trip(trip_record)

            if trip_data.get("assignedTo"):
                AssignmentStore.assign_trip(
                    trip_id,
                    trip_data["assignedTo"],
                    trip_data.get("assignedToName", "Unknown"),
                    "seed",
                )

            loaded += 1

        logger.info("SEED_SCENARIO: loaded %d trips from %s", loaded, seed_name)
    except Exception as e:
        logger.error("SEED_SCENARIO: failed to load fixture: %s", e)


# =============================================================================
# Helpers
# =============================================================================

def build_envelopes(data: dict[str, Any]) -> List[SourceEnvelope]:
    envelopes: List[SourceEnvelope] = []

    if data.get("raw_note"):
        envelopes.append(
            SourceEnvelope.from_freeform(data["raw_note"], "agency_notes", "agent")
        )
    if data.get("owner_note"):
        envelopes.append(
            SourceEnvelope.from_freeform(data["owner_note"], "agency_notes", "owner")
        )
    if data.get("structured_json"):
        envelopes.append(
            SourceEnvelope.from_structured(
                data["structured_json"], "structured_import", "system"
            )
        )
    if data.get("itinerary_text"):
        envelopes.append(
            SourceEnvelope.from_freeform(
                data["itinerary_text"], "traveler_form", "traveler"
            )
        )

    return envelopes


def _to_dict(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj


def serialize_bundle(bundle: Any, traveler_safe: bool = False) -> Optional[dict[str, Any]]:
    if bundle is None:
        return None
    if traveler_safe and hasattr(bundle, "to_traveler_dict"):
        # Prefer traveler-safe serialization to prevent internal field leakage.
        return bundle.to_traveler_dict()
    return _to_dict(bundle)


def _normalize_scenario_id(id: str) -> str:
    """
    Normalize a scenario ID for comparison.

    Handles case, separator (/ vs -, _), and SC- prefix variations.
    Examples:
        SC-001  -> sc001
        sc_001  -> sc001
        SC001   -> sc001
        001     -> 001
    """
    normalized = id.lower().strip()
    # Strip SC prefix consistently
    for prefix in ("sc-", "sc_", "sc"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    # Normalize separators
    return normalized.replace("-", "").replace("_", "")


def _scenario_ids_match(a: str, b: str) -> bool:
    """Check if two scenario IDs refer to the same fixture."""
    return _normalize_scenario_id(a) == _normalize_scenario_id(b)


def load_fixture_expectations(scenario_id: Optional[str]) -> Optional[dict[str, Any]]:
    """Load fixture expectations from scenario file if scenario_id is provided."""
    if not scenario_id:
        return None

    fixtures_dir = PROJECT_ROOT / "data" / "fixtures" / "scenarios"
    if not fixtures_dir.exists():
        return None

    for fname in fixtures_dir.glob("*.json"):
        try:
            import json as _json

            with open(fname) as f:
                fixture = _json.load(f)
            fid = fixture.get("scenario_id", "")
            if _scenario_ids_match(fid, scenario_id):
                return fixture.get("expected")
        except Exception:
            continue

    return None


# =============================================================================
# Routes
# =============================================================================

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/run", response_model=SpineRunResponse)
def run_spine(request: SpineRunRequest) -> SpineRunResponse:
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
            "spine_run ok=True run_id=%s stage=%s mode=%s scenario_id=%s execution_ms=%.2f",
            run_id,
            request.stage,
            request.operating_mode,
            request.scenario_id,
            execution_ms,
        )

        # Save the trip to persistence
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
        set_strict_mode(False)


# =============================================================================
# Run Status Endpoints (Wave A)
# =============================================================================

@app.get("/runs")
def list_runs(
    trip_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
):
    """
    List run records, newest first.
    Optionally filter by trip_id and/or state (queued|running|completed|failed|blocked).
    """
    runs = RunLedger.list_runs(trip_id=trip_id, state=state, limit=limit)
    return {"items": runs, "total": len(runs)}


@app.get("/runs/{run_id}")
def get_run_status(run_id: str):
    """
    Full run status including metadata and latest checkpointed steps.
    Returns 404 if the run_id is not found in the ledger.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    steps = RunLedger.get_all_steps(run_id)
    return {
        **meta,
        "steps": {name: step.get("checkpointed_at") for name, step in steps.items()},
        "steps_available": list(steps.keys()),
    }


@app.get("/runs/{run_id}/steps/{step_name}")
def get_run_step(run_id: str, step_name: str):
    """
    Return the full checkpointed output for a single pipeline step.
    Returns 404 if the step has not been checkpointed yet.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    step = RunLedger.get_step(run_id, step_name)
    if step is None:
        raise HTTPException(
            status_code=404,
            detail=f"Step '{step_name}' not yet checkpointed for run {run_id}",
        )
    return step


@app.get("/runs/{run_id}/events")
def get_run_event_stream(run_id: str):
    """
    Return the append-only event log for a run in chronological order.
    Returns empty list if the run_id is unknown (no events written yet).
    """
    events = get_run_events(run_id)
    return {"run_id": run_id, "events": events, "total": len(events)}


# =============================================================================
# Trip Management Endpoints
# =============================================================================

@app.get("/trips")
def list_trips(status: Optional[str] = None, limit: int = 100):
    """List all trips, optionally filtered by status."""
    trips = TripStore.list_trips(status=status, limit=limit)
    return {"items": trips, "total": len(trips)}


@app.get("/trips/{trip_id}")
def get_trip(trip_id: str):
    """Get a specific trip by ID."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Include assignment info
    assignment = AssignmentStore.get_assignment(trip_id)
    if assignment:
        trip["assigned_to"] = assignment["agent_id"]
        trip["assigned_to_name"] = assignment["agent_name"]
    
    return trip


@app.patch("/trips/{trip_id}")
def patch_trip(trip_id: str, updates: Dict[str, Any]):
    """Update trip fields (e.g. status)."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    old_status = trip.get("status")
    new_status = updates.get("status")

    # Enforce ready gate when marking trip as completed/ready.
    if new_status == "completed":
        overrides_by_flag: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ov in OverrideStore.get_overrides_for_trip(trip_id):
            flag_key = str(ov.get("flag") or "").strip()
            if flag_key:
                overrides_by_flag[flag_key].append(ov)
        failures = ready_gate_failures(trip, dict(overrides_by_flag))
        if failures:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Ready gate failed",
                    "failures": failures,
                },
            )
    
    # Perform update
    updated_trip = TripStore.update_trip(trip_id, updates)
    
    # Handle status-specific side effects
    if new_status and new_status != old_status:
        # Log status change
        AuditStore.log_event("trip_status_changed", "operator", {
            "trip_id": trip_id,
            "old_status": old_status,
            "new_status": new_status,
            "reason": "manual_update"
        })
        
        # If moving back to 'new', ensure it's unassigned
        if new_status == "new":
            AssignmentStore.unassign_trip(trip_id, "operator")
            
    return updated_trip


@app.post("/trips/{trip_id}/assign")
def assign_trip(trip_id: str, agent_id: str, agent_name: str, assigned_by: str = "system"):
    """Assign a trip to an agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, assigned_by)
    
    # Update trip status
    TripStore.update_trip(trip_id, {"status": "assigned"})
    
    return {"success": True, "trip_id": trip_id, "assigned_to": agent_id}


@app.post("/trips/{trip_id}/unassign")
def unassign_trip(trip_id: str, unassigned_by: str = "system"):
    """Remove assignment from a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    AssignmentStore.unassign_trip(trip_id, unassigned_by)
    
    return {"success": True, "trip_id": trip_id}


@app.post("/trips/{trip_id}/snooze")
def snooze_trip(trip_id: str, request: SnoozeRequest):
    """Snooze a trip until a specified time."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    analytics = trip.get("analytics") or {}
    analytics["snooze_until"] = request.snooze_until
    TripStore.update_trip(trip_id, {"analytics": analytics})
    
    AuditStore.log_event("trip_snoozed", "owner", {
        "trip_id": trip_id,
        "snooze_until": request.snooze_until,
    })
    
    return {"success": True, "trip_id": trip_id, "snooze_until": request.snooze_until}


@app.post("/trips/{trip_id}/suitability/acknowledge")
def acknowledge_suitability_flags(trip_id: str, request: SuitabilityAcknowledgeRequest):
    """Acknowledge suitability flags for a trip, allowing it to proceed."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    analytics = trip.get("analytics") or {}
    existing = analytics.get("acknowledged_flags", [])
    updated = list(set(existing + request.acknowledged_flags))
    analytics["acknowledged_flags"] = updated
    analytics["suitability_acknowledged_at"] = datetime.now(timezone.utc).isoformat()
    TripStore.update_trip(trip_id, {"analytics": analytics})
    
    AuditStore.log_event("suitability_acknowledged", "owner", {
        "trip_id": trip_id,
        "acknowledged_flags": request.acknowledged_flags,
    })
    
    return {"success": True, "trip_id": trip_id, "acknowledged_flags": updated}


@app.get("/assignments")
def list_assignments(agent_id: Optional[str] = None):
    """List assignments, optionally filtered by agent."""
    if agent_id:
        assignments = AssignmentStore.get_trips_for_agent(agent_id)
    else:
        # Get all assignments — AssignmentStore already imported at module level
        assignments = list(AssignmentStore._load_assignments().values())
    
    return {"items": assignments, "total": len(assignments)}


@app.get("/audit")
def get_audit_events(limit: int = 100):
    """Get recent audit events."""
    events = AuditStore.get_events(limit=limit)
    return {"items": events, "total": len(events)}


# =============================================================================
# Analytics Endpoints (Wave 1 Governance)
# =============================================================================

from src.analytics.models import InsightsSummary, StageMetrics
from src.analytics.metrics import (
    aggregate_insights,
    compute_pipeline_metrics,
    compute_team_metrics,
    compute_bottlenecks,
    compute_revenue_metrics,
    compute_alerts,
    TeamMemberMetrics,
    BottleneckAnalysis,
    RevenueMetrics,
    OperationalAlert
)

@app.get("/analytics/summary", response_model=InsightsSummary)
def get_analytics_summary(range: str = "30d"):
    trips = TripStore.list_trips(limit=10000)
    # Ensure consistency with DashboardAggregator by only including trips with IDs
    canonical_trips = [t for t in trips if t.get("id")]
    return aggregate_insights(canonical_trips)


@app.get("/analytics/pipeline", response_model=List[StageMetrics])
def get_analytics_pipeline(range: str = "30d"):
    trips = TripStore.list_trips(limit=10000)
    canonical_trips = [t for t in trips if t.get("id")]
    return compute_pipeline_metrics(canonical_trips)


@app.get("/analytics/team", response_model=List[TeamMemberMetrics])
def get_analytics_team(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    members = TeamStore.list_members(active_only=False)
    return compute_team_metrics(trips, members)


@app.get("/analytics/bottlenecks", response_model=List[BottleneckAnalysis])
def get_analytics_bottlenecks(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    return compute_bottlenecks(trips)


@app.get("/analytics/revenue", response_model=RevenueMetrics)
def get_analytics_revenue(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    return compute_revenue_metrics(trips)


@app.get("/analytics/agent/{agent_id}/drill-down")
def get_agent_drill_down(agent_id: str, metric: str = "conversion"):
    """Return trips and metrics for a specific agent."""
    trips = TripStore.list_trips(limit=1000)
    agent_trips = [
        t for t in trips
        if t.get("assigned_to") == agent_id or t.get("agent_id") == agent_id
    ]
    
    return {
        "agent_id": agent_id,
        "metric": metric,
        "trips": agent_trips,
        "count": len(agent_trips),
    }


@app.get("/analytics/alerts", response_model=List[OperationalAlert])
def get_analytics_alerts():
    """List pending operational alerts (Wave 10)."""
    trips = TripStore.list_trips(limit=1000)
    return compute_alerts(trips)


@app.post("/analytics/alerts/{alert_id}/dismiss")
def post_dismiss_alert(alert_id: str):
    """Dismiss an operational alert by flagging the source trip."""
    # Alert ID format is alert_{trip_id}
    trip_id = alert_id.replace("alert_", "")
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Target trip for alert {alert_id} not found")
    
    analytics = trip.get("analytics") or {}
    analytics["feedback_dismissed"] = True
    
    TripStore.update_trip(trip_id, {"analytics": analytics})
    return {"success": True}


# =============================================================================
# Review Management Endpoints (Wave 4)
# =============================================================================

from src.analytics.review import process_review_action, trip_to_review


@app.get("/analytics/reviews")
def get_pending_reviews():
    """List all trips currently flagged for owner review."""
    trips = TripStore.list_trips(limit=1000)
    # Filter for trips requiring review (per engine.py / review.py logic)
    pending = [
        trip_to_review(t) 
        for t in trips 
        if t.get("analytics", {}).get("requires_review") is True
    ]
    return {"items": pending, "total": len(pending)}


@app.post("/trips/{trip_id}/review/action")
def post_review_action(trip_id: str, request: ReviewActionRequest):
    """Apply a review action (approve/reject/request_changes/escalate) to a trip."""
    try:
        updated_trip = process_review_action(
            trip_id=trip_id,
            action=request.action,
            notes=request.notes,
            user_id="owner",  # Hardcoded for now, should come from auth
            reassign_to=request.reassign_to,
            error_category=request.error_category
        )
        return {"success": True, "trip": updated_trip}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Review action failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during review action")


# ============================================================================
# Agency Autonomy Settings (D1)
# ============================================================================

@app.get("/api/settings")
def get_agency_settings(agency_id: str = "waypoint-hq"):
    """Return the complete agency configuration (profile + operational + autonomy)."""
    settings = AgencySettingsStore.load(agency_id)
    return {
        "agency_id": settings.agency_id,
        "profile": {
            "agency_name": settings.agency_name,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "logo_url": settings.logo_url,
            "website": settings.website,
        },
        "operational": {
            "target_margin_pct": settings.target_margin_pct,
            "default_currency": settings.default_currency,
            "operating_hours": {
                "start": settings.operating_hours_start,
                "end": settings.operating_hours_end,
            },
            "operating_days": settings.operating_days,
            "preferred_channels": settings.preferred_channels,
            "brand_tone": settings.brand_tone,
        },
        "autonomy": {
            "approval_gates": settings.autonomy.approval_gates,
            "mode_overrides": settings.autonomy.mode_overrides,
            "auto_proceed_with_warnings": settings.autonomy.auto_proceed_with_warnings,
            "learn_from_overrides": settings.autonomy.learn_from_overrides,
            "min_proceed_confidence": settings.autonomy.min_proceed_confidence,
            "min_draft_confidence": settings.autonomy.min_draft_confidence,
        },
    }

@app.post("/api/settings/operational")
def update_agency_operational_settings(
    request: UpdateOperationalSettings,
    agency_id: str = "waypoint-hq",
):
    """
    Update agency operational and profile settings.
    Only fields provided in the request are modified; others remain unchanged.
    """
    settings = AgencySettingsStore.load(agency_id)
    changes: list[str] = []

    # Profile fields
    if request.agency_name is not None:
        settings.agency_name = request.agency_name
        changes.append("agency_name")
    if request.contact_email is not None:
        settings.contact_email = request.contact_email
        changes.append("contact_email")
    if request.contact_phone is not None:
        settings.contact_phone = request.contact_phone
        changes.append("contact_phone")
    if request.logo_url is not None:
        settings.logo_url = request.logo_url
        changes.append("logo_url")
    if request.website is not None:
        settings.website = request.website
        changes.append("website")

    # Operational fields
    if request.target_margin_pct is not None:
        settings.target_margin_pct = request.target_margin_pct
        changes.append("target_margin_pct")
    if request.default_currency is not None:
        settings.default_currency = request.default_currency
        changes.append("default_currency")
    if request.operating_hours_start is not None:
        settings.operating_hours_start = request.operating_hours_start
        changes.append("operating_hours_start")
    if request.operating_hours_end is not None:
        settings.operating_hours_end = request.operating_hours_end
        changes.append("operating_hours_end")
    if request.operating_days is not None:
        settings.operating_days = request.operating_days
        changes.append("operating_days")
    if request.preferred_channels is not None:
        settings.preferred_channels = request.preferred_channels
        changes.append("preferred_channels")
    if request.brand_tone is not None:
        settings.brand_tone = request.brand_tone
        changes.append("brand_tone")

    AgencySettingsStore.save(settings)

    return {
        "agency_id": settings.agency_id,
        "changes": changes,
        "profile": {
            "agency_name": settings.agency_name,
            "contact_email": settings.contact_email,
            "contact_phone": settings.contact_phone,
            "logo_url": settings.logo_url,
            "website": settings.website,
        },
        "operational": {
            "target_margin_pct": settings.target_margin_pct,
            "default_currency": settings.default_currency,
            "operating_hours": {
                "start": settings.operating_hours_start,
                "end": settings.operating_hours_end,
            },
            "operating_days": settings.operating_days,
            "preferred_channels": settings.preferred_channels,
            "brand_tone": settings.brand_tone,
        },
    }


@app.get("/api/settings/autonomy")
def get_agency_autonomy_settings(agency_id: str = "waypoint-hq"):
    """Return the agency autonomy policy (gates, overrides, flags)."""
    settings = AgencySettingsStore.load(agency_id)
    policy = settings.autonomy
    return {
        "agency_id": settings.agency_id,
        "approval_gates": policy.approval_gates,
        "mode_overrides": policy.mode_overrides,
        "auto_proceed_with_warnings": policy.auto_proceed_with_warnings,
        "learn_from_overrides": policy.learn_from_overrides,
        "min_proceed_confidence": policy.min_proceed_confidence,
        "min_draft_confidence": policy.min_draft_confidence,
    }


@app.post("/api/settings/autonomy")
def update_agency_autonomy_settings(
    request: UpdateAutonomyPolicy,
    agency_id: str = "waypoint-hq",
):
    """
    Update the agency autonomy policy.

    - Rejects any attempt to set STOP_NEEDS_REVIEW to anything other than block.
    - Persists to the file-backed AgencySettingsStore.
    """
    settings = AgencySettingsStore.load(agency_id)
    policy = settings.autonomy
    changes: list[str] = []

    if request.approval_gates is not None:
        for state, action in request.approval_gates.items():
            if state == "STOP_NEEDS_REVIEW" and action != "block":
                raise HTTPException(
                    status_code=400,
                    detail="Safety invariant: STOP_NEEDS_REVIEW must always be 'block'",
                )
            if action not in ("auto", "review", "block"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid action '{action}' for state '{state}'. Must be auto|review|block.",
                )
            policy.approval_gates[state] = action
        changes.append("approval_gates")

    if request.mode_overrides is not None:
        policy.mode_overrides = {
            k: dict(v) if isinstance(v, dict) else {}
            for k, v in request.mode_overrides.items()
        }
        changes.append("mode_overrides")

    if request.auto_proceed_with_warnings is not None:
        policy.auto_proceed_with_warnings = request.auto_proceed_with_warnings
        changes.append("auto_proceed_with_warnings")

    if request.learn_from_overrides is not None:
        policy.learn_from_overrides = request.learn_from_overrides
        changes.append("learn_from_overrides")

    # Persist
    AgencySettingsStore.save(settings)

    return {
        "agency_id": settings.agency_id,
        "approval_gates": policy.approval_gates,
        "mode_overrides": policy.mode_overrides,
        "auto_proceed_with_warnings": policy.auto_proceed_with_warnings,
        "learn_from_overrides": policy.learn_from_overrides,
        "changes": changes,
    }


@app.get("/api/trips/{trip_id}/timeline", response_model=TimelineResponse)
def get_trip_timeline(
    trip_id: str,
    stage: Optional[str] = None,
) -> TimelineResponse:
    """
    Retrieve the unified timeline for a trip from AuditStore.
    
    Returns all audit events related to the trip, transformed to presentation-ready format.
    Events are sorted by timestamp (ascending).
    
    Args:
        trip_id: Unique trip identifier
        stage: Optional filter by stage (intake, packet, decision, strategy, safety)
    
    Returns:
        TimelineResponse with mapped events, or empty events list if no events exist
    
    Raises:
        HTTPException 400: If stage parameter is invalid
        HTTPException 500: If timeline retrieval fails
    """
    # Validate stage parameter if provided
    if stage:
        valid_stages = {"intake", "packet", "decision", "strategy", "safety"}
        if stage.lower() not in valid_stages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage parameter. Must be one of: {', '.join(valid_stages)}"
            )
    
    try:
        # Fetch all audit events for this trip
        audit_events = AuditStore.get_events_for_trip(trip_id)
        
        # Use mapper to transform raw audit events to presentation format
        if TimelineEventMapper:
            mapped_events = TimelineEventMapper.map_events_for_trip(
                audit_events,
                stage_filter=stage
            )
            # Convert mapped TimelineEvent objects (from logger) to dicts for server.py's TimelineEvent validation
            events: List[TimelineEvent] = []
            for mapped_event in mapped_events:
                # Clamp confidence score to 0-100 if present
                confidence = mapped_event.confidence
                if confidence is not None:
                    if isinstance(confidence, (int, float)):
                        # Clamp to valid range
                        confidence = max(0, min(100, float(confidence)))
                    else:
                        logger.error(f"Invalid confidence type {type(confidence)} for trip {trip_id}, using None")
                        confidence = None
                
                # The mapper returns logger.TimelineEvent objects, convert to dict then to server.py TimelineEvent
                event_dict = {
                    "trip_id": mapped_event.trip_id,
                    "timestamp": mapped_event.timestamp,
                    "stage": mapped_event.stage,
                    "status": mapped_event.status,
                    "state_snapshot": mapped_event.state_snapshot,
                }
                if mapped_event.decision is not None:
                    event_dict["decision"] = mapped_event.decision
                if confidence is not None:
                    event_dict["confidence"] = confidence
                if mapped_event.reason is not None:
                    event_dict["reason"] = mapped_event.reason
                if mapped_event.pre_state is not None:
                    event_dict["pre_state"] = mapped_event.pre_state
                if mapped_event.post_state is not None:
                    event_dict["post_state"] = mapped_event.post_state
                
                events.append(TimelineEvent(**event_dict))
        else:
            # Fallback: use old schema if mapper unavailable
            events: List[TimelineEvent] = []
            for audit_event in audit_events:
                details = audit_event.get("details", {})
                
                if details.get("trip_id") != trip_id:
                    continue
                
                resolved_state = details.get("state")
                if not resolved_state and isinstance(details.get("post_state"), dict):
                    resolved_state = details.get("post_state", {}).get("state")
                
                event_dict = {
                    "trip_id": trip_id,
                    "timestamp": audit_event.get("timestamp", ""),
                    "stage": details.get("stage", "unknown"),
                    "status": resolved_state or "unknown",
                    "state_snapshot": {"stage": details.get("stage", "unknown")},
                }
                
                if details.get("decision_type"):
                    event_dict["decision"] = details.get("decision_type")
                
                if details.get("reason"):
                    event_dict["reason"] = details.get("reason")
                
                # Defensive clamping: if confidence is ever extracted from audit events,
                # ensure it's within valid range (0-100)
                if details.get("confidence") is not None:
                    try:
                        confidence = float(details.get("confidence"))
                        event_dict["confidence"] = max(0, min(100, confidence))
                    except (ValueError, TypeError):
                        logger.error(f"Invalid confidence value in fallback: {details.get('confidence')}")
                
                if stage and event_dict.get("stage") != stage:
                    continue
                
                events.append(TimelineEvent(**event_dict))
        
        return TimelineResponse(trip_id=trip_id, events=events)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve timeline for trip {trip_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trip timeline"
        )



# =============================================================================
# Override API endpoints
# =============================================================================

@app.post("/trips/{trip_id}/override", response_model=OverrideResponse)
def create_override(trip_id: str, request: OverrideRequest) -> OverrideResponse:
    """
    Record an operator override of a risk flag for a trip.
    
    Validation:
    - If action="downgrade", new_severity must be provided and < original_severity
    - reason field is mandatory and must be non-empty
    - original_severity must match actual flag severity or reject with 409 Conflict
    
    Returns updated state and audit event ID.
    """
    # Validate trip exists
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")
    
    # Validate request fields
    if not request.reason or len(request.reason.strip()) < 1:
        raise HTTPException(
            status_code=400,
            detail="reason field is mandatory and must be non-empty"
        )
    
    if request.action == "downgrade":
        if not request.new_severity:
            raise HTTPException(
                status_code=400,
                detail="new_severity required for downgrade action"
            )
    
    # Get current suitability flags from trip decision
    current_flags = trip.get("decision", {}).get("suitability_flags", [])
    flag_info = None
    for flag in current_flags:
        if flag.get("flag") == request.flag:
            flag_info = flag
            break
    
    # Validate original_severity if provided
    if request.original_severity and flag_info:
        actual_severity = flag_info.get("severity")
        if actual_severity != request.original_severity:
            raise HTTPException(
                status_code=409,
                detail=f"Stale override: flag '{request.flag}' severity is '{actual_severity}', not '{request.original_severity}'"
            )
    
    # Save override to persistence
    override_data = {
        "flag": request.flag,
        "decision_type": request.decision_type or request.flag,
        "action": request.action,
        "new_severity": request.new_severity,
        "overridden_by": request.overridden_by,
        "reason": request.reason,
        "scope": request.scope,
        "original_severity": request.original_severity or (flag_info.get("severity") if flag_info else None),
        "rescinded": False,
    }
    
    override_id = OverrideStore.save_override(trip_id, override_data)
    
    # Create audit event
    audit_event_id = f"evt_{uuid.uuid4().hex[:12]}"
    AuditStore.log_event("override_created", request.overridden_by, {
        "trip_id": trip_id,
        "override_id": override_id,
        "flag": request.flag,
        "action": request.action,
        "reason": request.reason,
    })
    
    logger.info(
        "Override created: override_id=%s trip_id=%s flag=%s action=%s by=%s",
        override_id, trip_id, request.flag, request.action, request.overridden_by
    )
    
    return OverrideResponse(
        ok=True,
        override_id=override_id,
        trip_id=trip_id,
        flag=request.flag,
        action=request.action,
        new_severity=request.new_severity,
        cache_invalidated=False,
        rule_graduated=False,
        pattern_learning_queued=request.scope == "pattern",
        warnings=[],
        audit_event_id=audit_event_id,
    )


@app.get("/trips/{trip_id}/overrides")
def list_overrides(trip_id: str) -> dict:
    """List all overrides for a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")
    
    overrides = OverrideStore.get_overrides_for_trip(trip_id)
    
    return {
        "ok": True,
        "trip_id": trip_id,
        "overrides": overrides,
        "total": len(overrides),
    }


@app.get("/overrides/{override_id}")
def get_override(override_id: str) -> dict:
    """Get a specific override by ID."""
    override = OverrideStore.get_override(override_id)
    if not override:
        raise HTTPException(status_code=404, detail=f"Override not found: {override_id}")
    
    return {
        "ok": True,
        "override": override,
    }


# =============================================================================
# Dev entrypoint
# =============================================================================


# =============================================================================
# System Integrity API
# =============================================================================

from src.services.dashboard_aggregator import DashboardAggregator

@app.get("/api/system/unified-state")
def get_unified_state():
    """
    Canonical SSOT for dashboard metrics.
    Returns mathematically consistent data for Inbox, Overview, and Analytics.
    """
    try:
        return DashboardAggregator.get_unified_state()
    except Exception as e:
        logger.error(f"Failed to aggregate unified state: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal integrity error"
        )


@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats():
    """
    Dashboard stat cards — computed entirely by the backend aggregator.
    Replaces all frontend Math.floor / filter / reduce logic.
    """
    try:
        return DashboardAggregator.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Failed to compute dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to compute dashboard stats"
        )

# =============================================================================
# Team Management API
# =============================================================================

@app.get("/api/team/members")
def list_team_members():
    """List all team members."""
    members = TeamStore.list_members(active_only=False)
    return {"items": members, "total": len(members)}


@app.get("/api/team/members/{member_id}")
def get_team_member(member_id: str):
    """Get a team member by ID."""
    member = TeamStore.get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@app.post("/api/team/invite")
def invite_team_member(request: InviteTeamMemberRequest):
    """Invite a new team member."""
    member_id = TeamStore.create_member(request.model_dump())
    member = TeamStore.get_member(member_id)
    return {"success": True, "member": member}


@app.patch("/api/team/members/{member_id}")
def update_team_member(member_id: str, request: InviteTeamMemberRequest):
    """Update a team member."""
    updates = request.model_dump(exclude_none=True)
    member = TeamStore.update_member(member_id, updates)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@app.delete("/api/team/members/{member_id}")
def deactivate_team_member(member_id: str):
    """Deactivate a team member."""
    success = TeamStore.deactivate_member(member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Team member not found")
    return {"success": True}


@app.get("/api/team/workload")
def get_workload_distribution():
    """Get workload distribution across active team members."""
    members = TeamStore.list_members(active_only=True)
    assignments = AssignmentStore._load_assignments()
    
    distribution = []
    for member in members:
        member_id = member["id"]
        assigned_trips = [a for a in assignments.values() if a.get("agent_id") == member_id]
        distribution.append({
            "member_id": member_id,
            "name": member.get("name"),
            "role": member.get("role"),
            "capacity": member.get("capacity", 5),
            "assigned": len(assigned_trips),
            "available": max(0, member.get("capacity", 5) - len(assigned_trips)),
        })
    
    return {"items": distribution, "total": len(distribution)}


# =============================================================================
# Single Review + Bulk Review Actions
# =============================================================================

@app.get("/analytics/reviews/{review_id}")
def get_review(review_id: str):
    """Get a single review by trip ID."""
    trip = TripStore.get_trip(review_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Review not found")
    
    from src.analytics.review import trip_to_review
    return trip_to_review(trip)


@app.post("/analytics/reviews/bulk-action")
def bulk_review_action(actions: List[dict]):
    """Apply review actions in bulk."""
    from src.analytics.review import process_review_action
    
    processed = 0
    failed = 0
    results = []
    
    for action in actions:
        try:
            trip_id = action.get("trip_id") or action.get("review_id")
            if not trip_id:
                failed += 1
                continue
            
            process_review_action(
                trip_id=trip_id,
                action=action.get("action", "approve"),
                notes=action.get("notes", ""),
                user_id="owner",
                reassign_to=action.get("reassign_to"),
                error_category=action.get("error_category"),
            )
            processed += 1
            results.append({"trip_id": trip_id, "status": "processed"})
        except Exception as e:
            logger.error(f"Bulk review action failed for {action}: {e}")
            failed += 1
            results.append({"trip_id": action.get("trip_id"), "status": "failed", "error": str(e)})
    
    return {"success": failed == 0, "processed": processed, "failed": failed, "results": results}


# =============================================================================
# Escalations + Funnel Insights
# =============================================================================

@app.get("/analytics/escalations")
def get_escalation_heatmap():
    """Return escalation heatmap data."""
    trips = TripStore.list_trips(limit=1000)
    
    heatmap = defaultdict(lambda: {"total": 0, "escalated": 0})
    for trip in trips:
        agent = trip.get("assigned_to") or trip.get("agent_id") or "unassigned"
        heatmap[agent]["total"] += 1
        if trip.get("analytics", {}).get("escalation_severity") in ("high", "critical"):
            heatmap[agent]["escalated"] += 1
    
    return {
        "items": [
            {"agent_id": k, "total": v["total"], "escalated": v["escalated"]}
            for k, v in heatmap.items()
        ],
        "total": len(heatmap),
    }


@app.get("/analytics/funnel")
def get_conversion_funnel():
    """Return conversion funnel metrics."""
    trips = TripStore.list_trips(limit=1000)
    
    stages = ["new", "assigned", "in_progress", "review", "completed", "cancelled"]
    funnel = {stage: 0 for stage in stages}
    
    for trip in trips:
        status = trip.get("status", "new")
        if status in funnel:
            funnel[status] += 1
    
    return {
        "items": [
            {"stage": stage, "count": count}
            for stage, count in funnel.items()
        ],
        "total": len(trips),
    }


# =============================================================================
# Inbox Reassign + Bulk Actions
# =============================================================================

@app.post("/trips/{trip_id}/reassign")
def reassign_trip(trip_id: str, agent_id: str, agent_name: str, reassigned_by: str = "owner"):
    """Reassign a trip to a different agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Unassign first if already assigned
    existing = AssignmentStore.get_assignment(trip_id)
    if existing:
        AssignmentStore.unassign_trip(trip_id, reassigned_by)
    
    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, reassigned_by)
    TripStore.update_trip(trip_id, {"status": "assigned"})
    
    return {"success": True, "trip_id": trip_id, "reassigned_to": agent_id}


@app.post("/inbox/bulk")
def bulk_inbox_action(request: dict):
    """Apply bulk actions to inbox items."""
    action = request.get("action")
    trip_ids = request.get("trip_ids", [])
    
    if not action or not trip_ids:
        raise HTTPException(status_code=400, detail="action and trip_ids are required")
    
    processed = 0
    failed = 0
    
    for trip_id in trip_ids:
        try:
            if action == "assign":
                agent_id = request.get("agent_id", "system")
                AssignmentStore.assign_trip(trip_id, agent_id, agent_id, "bulk")
                TripStore.update_trip(trip_id, {"status": "assigned"})
            elif action == "unassign":
                AssignmentStore.unassign_trip(trip_id, "bulk")
            elif action == "archive":
                TripStore.update_trip(trip_id, {"status": "archived"})
            processed += 1
        except Exception as e:
            logger.error(f"Bulk action failed for {trip_id}: {e}")
            failed += 1
    
    return {"success": failed == 0, "processed": processed, "failed": failed}


# =============================================================================
# Pipeline Stages + Approval Thresholds Settings
# =============================================================================

@app.get("/api/settings/pipeline")
def get_pipeline_stages():
    """Get pipeline stage configuration."""
    stages = ConfigStore.get_pipeline_stages()
    return {"items": stages}


@app.put("/api/settings/pipeline")
def set_pipeline_stages(request: List[PipelineStageConfig]):
    """Update pipeline stage configuration."""
    ConfigStore.set_pipeline_stages([s.model_dump() for s in request])
    return {"success": True}


@app.get("/api/settings/approvals")
def get_approval_thresholds():
    """Get approval threshold configuration."""
    thresholds = ConfigStore.get_approval_thresholds()
    return {"items": thresholds}


@app.put("/api/settings/approvals")
def set_approval_thresholds(request: List[ApprovalThresholdConfig]):
    """Update approval threshold configuration."""
    ConfigStore.set_approval_thresholds([t.model_dump() for t in request])
    return {"success": True}


# =============================================================================
# Insights Export
# =============================================================================

@app.post("/analytics/export")
def export_insights(request: ExportRequest):
    """Export insights data. Returns a mock export URL for now."""
    export_id = f"export_{uuid.uuid4().hex[:12]}"
    expires = datetime.now(timezone.utc).isoformat()
    
    # In production this would generate a real file and return a signed URL
    return ExportResponse(
        download_url=f"/api/exports/{export_id}.{request.format}",
        expires_at=expires,
    )


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    uvicorn.run(
        "spine_api.server:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        reload=os.environ.get("SPINE_API_RELOAD", "1") == "1",
    )
