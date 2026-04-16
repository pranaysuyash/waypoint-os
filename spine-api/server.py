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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.safety import set_strict_mode

# Import persistence (handle hyphen in path)
import importlib.util
import sys
from pathlib import Path
_persistence_path = Path(__file__).parent / "persistence.py"
spec = importlib.util.spec_from_file_location("persistence", _persistence_path)
persistence = importlib.util.module_from_spec(spec)
sys.modules["persistence"] = persistence
spec.loader.exec_module(persistence)
TripStore = persistence.TripStore
AssignmentStore = persistence.AssignmentStore
AuditStore = persistence.AuditStore
save_processed_trip = persistence.save_processed_trip

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

    try:
        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
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
        try:
            trip_id = save_processed_trip(
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
            logger.info("Trip saved: %s", trip_id)
        except Exception as e:
            logger.error("Failed to save trip: %s", e)
            # Don't fail the request if saving fails

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


from spine-api.persistence import TripStore, AssignmentStore, AuditStore, save_processed_trip


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
        # Get all assignments
        import json
        from spine-api.persistence import AssignmentStore
        assignments = list(AssignmentStore._load_assignments().values())
    
    return {"items": assignments, "total": len(assignments)}


@app.get("/audit")
def get_audit_events(limit: int = 100):
    """Get recent audit events."""
    events = AuditStore.get_events(limit=limit)
    return {"items": events, "total": len(events)}


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
        reload=bool(os.environ.get("SPINE_API_RELOAD", "1")),
    )