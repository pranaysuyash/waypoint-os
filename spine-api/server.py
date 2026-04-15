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

logger = logging.getLogger("spine-api")

# =============================================================================
# Pydantic models — canonical contract
# =============================================================================

class SafetyResult(BaseModel):
    strict_leakage: bool = False
    leakage_passed: bool = True
    leakage_errors: List[str] = Field(default_factory=list)


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


def serialize_bundle(bundle: Any) -> Optional[dict[str, Any]]:
    if bundle is None:
        return None
    return _to_dict(bundle)


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

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)

        logger.info(
            "spine_run ok=True run_id=%s stage=%s mode=%s execution_ms=%.2f",
            run_id,
            request.stage,
            request.operating_mode,
            execution_ms,
        )

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

        return SpineRunResponse(
            ok=True,
            run_id=run_id,
            packet=_to_dict(result.packet) if hasattr(result, "packet") else None,
            validation=_to_dict(result.validation) if hasattr(result, "validation") else None,
            decision=_to_dict(result.decision) if hasattr(result, "decision") else None,
            strategy=_to_dict(result.strategy) if hasattr(result, "strategy") else None,
            traveler_bundle=serialize_bundle(result.traveler_bundle)
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