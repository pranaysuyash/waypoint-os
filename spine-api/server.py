"""
spine-api — FastAPI service exposing run_spine_once as an HTTP endpoint.

Architecture:
    Next.js (BFF)  →  HTTP POST /run  →  FastAPI spine-api  →  run_spine_once
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

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add spine-api directory to Python path for local imports
SPINE_API_DIR = Path(__file__).resolve().parent
if str(SPINE_API_DIR) not in sys.path:
    sys.path.insert(0, str(SPINE_API_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Standard imports follow package structure


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
save_processed_trip = persistence.save_processed_trip

# Wave A: run lifecycle modules
from run_state import RunState, assert_can_transition, terminal_state_for_run_result
from run_events import (
    emit_run_started,
    emit_run_completed,
    emit_run_failed,
    emit_run_blocked,
    emit_stage_entered,
    emit_stage_completed,
    get_run_events,
)
from run_ledger import RunLedger
from src.intake.config.agency_settings import AgencySettingsStore

logger = logging.getLogger("spine-api")

# =============================================================================
# Pydantic models — canonical contract
# =============================================================================

class SafetyResult(BaseModel):
    strict_leakage: bool = False
    leakage_passed: bool = True
    leakage_errors: List[str] = Field(default_factory=list)


class AssertionResult(BaseModel):
    type: str
    passed: bool
    message: str
    field: Optional[str] = None


class AutonomyOutcome(BaseModel):
    """D1 autonomy policy outcome — separates raw NB02 verdict from agency policy."""
    raw_verdict: str
    effective_action: str
    approval_required: bool
    rule_source: str
    safety_invariant_applied: bool
    mode_override_applied: Optional[str] = None
    warning_override_applied: bool = False
    reasons: List[str] = Field(default_factory=list)


class RunMeta(BaseModel):
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    fixture_id: Optional[str] = None
    execution_ms: float = 0.0


class SpineRunResponse(BaseModel):
    ok: bool = True
    run_id: str = ""
    packet: Optional[dict[str, Any]] = None
    validation: Optional[dict[str, Any]] = None
    decision: Optional[dict[str, Any]] = None
    strategy: Optional[dict[str, Any]] = None
    traveler_bundle: Optional[dict[str, Any]] = None
    internal_bundle: Optional[dict[str, Any]] = None
    safety: SafetyResult = Field(default_factory=SafetyResult)
    fees: Optional[dict[str, Any]] = None
    autonomy_outcome: Optional[AutonomyOutcome] = None
    assertions: Optional[List[AssertionResult]] = None
    meta: RunMeta = Field(default_factory=RunMeta)


class SpineRunRequest(BaseModel):
    raw_note: Optional[str] = Field(default=None)
    owner_note: Optional[str] = Field(default=None)
    structured_json: Optional[dict[str, Any]] = Field(default=None)
    itinerary_text: Optional[str] = Field(default=None)
    stage: str = Field(default="discovery")
    operating_mode: str = Field(default="normal_intake")
    strict_leakage: bool = Field(default=False)
    scenario_id: Optional[str] = Field(default=None)

    model_config = {"extra": "forbid"}


class HealthResponse(BaseModel):
    status: str
    version: str


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
# FastAPI app
# =============================================================================

app = FastAPI(
    title="Spine API",
    description="Canonical HTTP wrapper around run_spine_once",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    trips = TripStore.list_trips(limit=1000)
    return aggregate_insights(trips)


@app.get("/analytics/pipeline", response_model=List[StageMetrics])
def get_analytics_pipeline(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    return compute_pipeline_metrics(trips)


@app.get("/analytics/team", response_model=List[TeamMemberMetrics])
def get_analytics_team(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    assignments = list(AssignmentStore._load_assignments().values())
    return compute_team_metrics(trips, assignments)


@app.get("/analytics/bottlenecks", response_model=List[BottleneckAnalysis])
def get_analytics_bottlenecks(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    return compute_bottlenecks(trips)


@app.get("/analytics/revenue", response_model=RevenueMetrics)
def get_analytics_revenue(range: str = "30d"):
    trips = TripStore.list_trips(limit=1000)
    return compute_revenue_metrics(trips)


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

class ReviewActionRequest(BaseModel):
    action: str
    notes: str
    reassign_to: Optional[str] = None


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
            reassign_to=request.reassign_to
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
    """Return the complete agency configuration (operational + autonomy)."""
    settings = AgencySettingsStore.load(agency_id)
    return {
        "agency_id": settings.agency_id,
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


class UpdateAutonomyPolicy(BaseModel):
    approval_gates: Optional[dict[str, str]] = None
    mode_overrides: Optional[dict[str, dict[str, str]]] = None
    auto_proceed_with_warnings: Optional[bool] = None
    learn_from_overrides: Optional[bool] = None


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


# =============================================================================
# Dev entrypoint
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    uvicorn.run(
        "spine-api.server:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        reload=os.environ.get("SPINE_API_RELOAD", "1") == "1",
    )