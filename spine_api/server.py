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

import asyncio
import json
import logging
import multiprocessing
import os
import re
import sys
import threading
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import is_dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root to Python path so we can import from src
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# --- OpenTelemetry instrumentation ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
otel_service_name = os.environ.get("OTEL_SERVICE_NAME", "spine_api")
if otel_endpoint:
    try:
        resource = Resource.create({"service.name": otel_service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint))
        )
        trace.set_tracer_provider(provider)
    except Exception as e:
        import logging
        logging.getLogger("spine_api.otel").warning(f"OTel init failed (non-fatal): {e}")
# --- End OTel ---

from spine_api.core.env import load_project_env

load_project_env()

from spine_api.core.auth import get_current_user, get_current_agency_id, get_current_agency
from spine_api.core.database import engine, get_db
from spine_api.models.tenant import Agency, User
from spine_api.core.logging_filter import install_sensitive_data_filter
from spine_api.core.middleware import AuthMiddleware
from spine_api.core.rate_limiter import limiter, RateLimitExceededHandler, SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from spine_api.contract import (
    SafetyResult,
    AssertionResult,
    AutonomyOutcome,
    RunMeta,
    SpineRunRequest,
    SpineRunResponse,
    RunAcceptedResponse,
    RunStatusResponse,
    OverrideRequest,
    OverrideResponse,
    HealthResponse,
    TimelineEvent,
    TimelineResponse,
    ReviewActionRequest,
    SuitabilityAcknowledgeRequest,
    SnoozeRequest,
    InviteTeamMemberRequest,
    TeamMember,
    PipelineStageConfig,
    ApprovalThresholdConfig,
    ExportRequest,
    ExportResponse,
    PublicCheckerExportResponse,
    PublicCheckerDeleteResponse,
    UpdateOperationalSettings,
    UpdateAutonomyPolicy,
    IntegrityIssuesResponse,
    UnifiedStateResponse,
    DashboardStatsResponse,
    SuitabilityFlagsResponse,
    InboxResponse,
    InboxStatsResponse,
)
from spine_api.services import membership_service
from spine_api.services.inbox_projection import InboxProjectionService, build_inbox_response

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.safety import set_strict_mode
from src.public_checker.live_checks import build_live_checker_signals
from src.services.integrity_service import IntegrityService

# OTel tracer for pipeline spans
_otel_tracer = trace.get_tracer("spine_api.pipeline")

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
save_processed_trip_async = persistence.save_processed_trip_async

PUBLIC_CHECKER_AGENCY_ID = "waypoint-hq"

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
from spine_api.draft_store import DraftStore
from src.intake.config.agency_settings import AgencySettingsStore
from src.analytics.policy_rules import ready_gate_failures
from src.agents.recovery_agent import RecoveryAgent
from src.agents.runtime import AgentSupervisor, build_default_registry


class _TripStoreAdapter:
    """Thin adapter so backend agents can query TripStore through a stable boundary."""

    def list_active(self) -> list:
        """Return trips that are in processing stages (not closed/cancelled)."""
        trips_raw = TripStore.list_trips(limit=500)
        terminal = {"closed", "cancelled", "completed", "archived"}
        return [t for t in trips_raw if (t.get("stage") or t.get("state") or t.get("status")) not in terminal]

    def set_review_status(self, trip_id: str, status: str) -> None:
        TripStore.update_trip(trip_id, {"review_status": status})

    def update_trip(self, trip_id: str, updates: dict) -> Optional[dict]:
        return TripStore.update_trip(trip_id, updates)


class _AuditStoreAdapter:
    """Thin adapter mapping product-agent audit events to AuditStore.log_event()."""

    def log(self, event_type: str, trip_id: str, payload: dict, user_id: Optional[str] = None) -> None:
        AuditStore.log_event(
            event_type=event_type,
            user_id=user_id or payload.get("agent_name") or "agent_runtime",
            details={"trip_id": trip_id, **payload},
        )


_agent_trip_repo = _TripStoreAdapter()
_agent_audit_sink = _AuditStoreAdapter()
_recovery_agent = RecoveryAgent(
    audit_store=_agent_audit_sink,
    trip_repo=_agent_trip_repo,
    # spine_runner left None — re-queue not wired until async job queue is added
)
_agent_supervisor = AgentSupervisor(
    registry=build_default_registry(),
    trip_repo=_agent_trip_repo,
    audit=_agent_audit_sink,
    interval_seconds=int(os.environ.get("AGENT_SUPERVISOR_INTERVAL_S", "300")),
)

# Auth — Phase 1
try:
    from routers import auth as auth_router
    from routers import workspace as workspace_router
    from routers import frontier as frontier_router
    from routers import audit as audit_router
    from routers import assignments as assignments_router
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

    _audit_spec = importlib.util.spec_from_file_location("routers.audit", _base / "routers" / "audit.py")
    _audit_mod = importlib.util.module_from_spec(_audit_spec)
    _audit_spec.loader.exec_module(_audit_mod)
    audit_router = _audit_mod

    _asgn_spec = importlib.util.spec_from_file_location("routers.assignments", _base / "routers" / "assignments.py")
    _asgn_mod = importlib.util.module_from_spec(_asgn_spec)
    _asgn_spec.loader.exec_module(_asgn_mod)
    assignments_router = _asgn_mod

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

async def _ensure_agencies_schema_compatibility() -> None:
    """
    Backfill missing agencies columns for local/stale databases.
    """
    try:
        async with engine.begin() as conn:
            table_exists_result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'agencies'
                )
            """))
            if not bool(table_exists_result.scalar()):
                return

            await conn.execute(text("""
                ALTER TABLE agencies
                ADD COLUMN IF NOT EXISTS is_test BOOLEAN DEFAULT false
            """))
            await conn.execute(text("""
                ALTER TABLE agencies
                ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(10) DEFAULT 'other'
            """))
            logger.info("Schema compatibility check complete for agencies table")
    except Exception as e:
        logger.error("Failed agencies schema compatibility check: %s", e)
        raise


async def _ensure_memberships_schema_compatibility() -> None:
    """
    Backfill missing memberships columns for local/stale databases.

    This is an additive startup migration guard to prevent auth failures when
    the running database lags the ORM model.
    """
    try:
        async with engine.begin() as conn:
            table_exists_result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'memberships'
                )
            """))
            table_exists = bool(table_exists_result.scalar())
            if not table_exists:
                return

            await conn.execute(text("""
                ALTER TABLE memberships
                ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 5
            """))
            await conn.execute(text("""
                ALTER TABLE memberships
                ADD COLUMN IF NOT EXISTS specializations JSONB DEFAULT '[]'::jsonb
            """))
            await conn.execute(text("""
                ALTER TABLE memberships
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'
            """))
            await conn.execute(text("""
                ALTER TABLE memberships
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NULL
            """))
            await conn.execute(text("""
                ALTER TABLE memberships
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()
            """))
            logger.info("Schema compatibility check complete for memberships table")
    except Exception as e:
        logger.error("Failed memberships schema compatibility check: %s", e)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager (replaces deprecated on_event)."""
    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
    if os.environ.get("SPINE_API_DISABLE_AUTH") and env in ("production", "staging"):
        raise RuntimeError(
            "SPINE_API_DISABLE_AUTH cannot be enabled in production or staging. "
            f"Current ENVIRONMENT={env}"
        )
    if os.environ.get("SPINE_API_DISABLE_AUTH"):
        logger.warning("⚠️  AUTH DISABLED — local/test only. Do not use in production.")
    await _ensure_agencies_schema_compatibility()
    await _ensure_memberships_schema_compatibility()
    install_sensitive_data_filter()
    app.state.limiter = limiter
    watchdog.start()
    _recovery_agent.start()
    _agent_supervisor.start()
    _zombie_reaper_start()
    # Note: We no longer auto-seed at startup.
    # Seeding is now done per-agency for test users in the /trips endpoint.
    logger.info("Spine API startup complete")
    yield
    # Shutdown
    _zombie_reaper_stop()
    _agent_supervisor.stop()
    _recovery_agent.stop()
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

app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, RateLimitExceededHandler.handler)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Phase 1: Auth + Workspace routers
app.include_router(auth_router.router)
app.include_router(
    workspace_router.router,
    dependencies=[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else [],
)
app.include_router(frontier_router.router, dependencies=[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else [])
app.include_router(audit_router.router, dependencies=[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else [])
app.include_router(assignments_router.router, dependencies=[Depends(get_current_user)] if not os.environ.get("SPINE_API_DISABLE_AUTH") else [])


def _seed_scenario(agency_id: Optional[str] = None):
    """
    Load a scenario fixture at startup if SEED_SCENARIO env var is set.
    
    Args:
        agency_id: Optional agency ID to associate with seeded trips.
            If not provided, trips will not have agency_id set.
    
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
                "agency_id": agency_id,  # Associate with agency if provided
            }
            
            TripStore.save_trip(trip_record, agency_id=agency_id)
            
            if trip_data.get("assignedTo"):
                AssignmentStore.assign_trip(
                    trip_id,
                    trip_data["assignedTo"],
                    trip_data.get("assignedToName", "Unknown"),
                    "seed",
                )
            
            loaded += 1
        
        logger.info("SEED_SCENARIO: loaded %d trips from %s (agency_id=%s)", loaded, seed_name, agency_id)
    except Exception as e:
        logger.error("SEED_SCENARIO: failed to load fixture: %s", e)


def _seed_scenario_for_agency(agency_id: str, seed_name: Optional[str] = None) -> int:
    """
    Seed a scenario fixture for a specific agency.
    
    Args:
        agency_id: The agency ID to associate trips with
        seed_name: Optional fixture name (defaults to SEED_SCENARIO env var)
        
    Returns:
        Number of trips loaded
    """
    if seed_name is None:
        seed_name = os.environ.get("SEED_SCENARIO", "scenario_alpha").strip()
    
    if not seed_name:
        return 0
    
    fixture_path = PROJECT_ROOT / "data" / "fixtures" / f"{seed_name}.json"
    if not fixture_path.exists():
        logger.warning("SEED_SCENARIO: fixture not found: %s", fixture_path)
        return 0
    
    try:
        with open(fixture_path) as f:
            trips = json.load(f)
        
        if not isinstance(trips, list):
            logger.warning("SEED_SCENARIO: fixture must be a JSON array of trips")
            return 0
        
        loaded = 0
        for trip_data in trips:
            trip_id = trip_data.get("id")
            if not trip_id:
                continue
            
            existing = TripStore.get_trip(trip_id)
            if existing:
                # Update existing trip with agency_id
                if existing.get("agency_id") != agency_id:
                    existing["agency_id"] = agency_id
                    TripStore.update_trip(trip_id, {"agency_id": agency_id})
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
                "agency_id": agency_id,
            }
            
            TripStore.save_trip(trip_record, agency_id=agency_id)
            
            if trip_data.get("assignedTo"):
                AssignmentStore.assign_trip(
                    trip_id,
                    trip_data["assignedTo"],
                    trip_data.get("assignedToName", "Unknown"),
                    "seed",
                )
            
            loaded += 1
        
        logger.info("SEED_SCENARIO: loaded %d trips for agency %s", loaded, agency_id)
        return loaded
    except Exception as e:
        logger.error("SEED_SCENARIO: failed to load fixture: %s", e)
        return 0


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

    extra_fields = {
        field: data[field]
        for field in (
            "follow_up_due_date",
            "pace_preference",
            "lead_source",
            "activity_provenance",
            "date_year_confidence",
        )
        if data.get(field)
    }
    if extra_fields:
        envelopes.append(
            SourceEnvelope.from_structured(
                extra_fields, "structured_import", "system"
            )
        )

    return envelopes


def _to_dict(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
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
    try:
        from src.decision.health import health_check_dict
        return HealthResponse(
            status="ok",
            version="1.0.0",
            components=health_check_dict().get("components"),
            issues=health_check_dict().get("issues"),
        )
    except Exception:
        return HealthResponse(status="ok", version="1.0.0")


_zombie_thread: Optional[threading.Thread] = None
_zombie_stop = threading.Event()

def _reap_zombies() -> None:
    """Background thread that periodically reaps zombie child processes."""
    while not _zombie_stop.is_set():
        try:
            # WNOHANG = non-blocking, reap any finished children
            while True:
                try:
                    pid, _status = os.waitpid(-1, os.WNOHANG)
                    if pid == 0:
                        break
                except ChildProcessError:
                    break
        except Exception:
            pass
        _zombie_stop.wait(5)  # check every 5 seconds


def _zombie_reaper_start() -> None:
    global _zombie_thread
    if _zombie_thread is not None:
        return
    _zombie_stop.clear()
    _zombie_thread = threading.Thread(target=_reap_zombies, daemon=True, name="zombie-reaper")
    _zombie_thread.start()


def _zombie_reaper_stop() -> None:
    global _zombie_thread
    _zombie_stop.set()
    if _zombie_thread is not None:
        _zombie_thread.join(timeout=2)
        _zombie_thread = None


def _close_inherited_lock_fds() -> None:
    """
    Close any parent-inherited lock file descriptors to prevent
    fcntl.flock deadlock when multiprocessing forks on macOS.

    When the parent holds any fcntl.flock and forks, the child inherits
    all open fds — including the locked ones. We close all fds above 2
    that have .lock in their path to release the inherited lock references.
    """
    import os as _os

    closed = 0
    for fd in range(3, 256):
        try:
            path = _os.readlink(f"/dev/fd/{fd}")
        except (OSError, FileNotFoundError):
            continue
        if path.endswith(".lock"):
            try:
                _os.close(fd)
                closed += 1
            except OSError:
                pass
    if closed:
        import logging
        logging.getLogger("spine_api").debug("Closed %d inherited lock fds", closed)


def _update_draft_for_terminal_state(
    run_id: str,
    run_state: str,
    trip_id: Optional[str] = None,
    snapshot: Optional[dict] = None,
) -> None:
    """Update the draft linked to this run with its final state.

    Looks up draft_id from RunLedger meta and calls DraftStore.update_run_state.
    No-ops if no draft is linked.
    """
    try:
        meta = RunLedger.get_meta(run_id)
        if not meta:
            return
        draft_id = meta.get("draft_id")
        if not draft_id:
            return
        DraftStore.update_run_state(
            draft_id=draft_id,
            run_id=run_id,
            run_state=run_state,
            run_snapshot=snapshot,
        )
    except Exception as exc:
        logger.debug("Draft state update skipped for run %s: %s", run_id, exc)


def _execute_spine_pipeline(
    run_id: str,
    request_dict: dict[str, Any],
    agency_id: str,
    user_id: str,
) -> None:
    """Run the spine pipeline in the background and persist status/events."""
    t0 = time.perf_counter()
    current_stage: Optional[str] = None

    def _checkpoint_result_steps(run_id: str, result: Any) -> None:
        """Persist core result artifacts for observability even on partial/early exits."""
        try:
            existing = RunLedger.get_all_steps(run_id)
            if "packet" not in existing and hasattr(result, "packet"):
                RunLedger.save_step(run_id, "packet", _to_dict(result.packet))
            if "validation" not in existing and hasattr(result, "validation"):
                RunLedger.save_step(run_id, "validation", _to_dict(result.validation))
            if "decision" not in existing and hasattr(result, "decision"):
                RunLedger.save_step(run_id, "decision", _to_dict(result.decision))
            if "strategy" not in existing and hasattr(result, "strategy"):
                RunLedger.save_step(run_id, "strategy", _to_dict(result.strategy))
        except Exception as e:
            logger.error("Wave A: result step checkpointing failed for run %s: %s", run_id, e)

    try:
        # Close inherited lock file descriptors to prevent fork-deadlock on macOS.
        # When multiprocessing forks, the child inherits all parent fds including
        # fcntl.flock-held files. Closing them here ensures the child can acquire
        # fresh locks via the file_lock context manager.
        _close_inherited_lock_fds()

        request = SpineRunRequest(**request_dict)
        consented_submission = request_dict if request.retention_consent else {
            key: value
            for key, value in request_dict.items()
            if key not in {"raw_note", "owner_note", "itinerary_text", "structured_json"}
        }

        if request.strict_leakage:
            set_strict_mode(True)

        meta = RunMeta(
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_id=request.scenario_id,
            execution_ms=0.0,
        )

        RunLedger.set_state(run_id, RunState.RUNNING)
        
        # Update linked draft status if draft_id was provided
        draft_id = request_dict.get("draft_id")
        if draft_id:
            try:
                DraftStore.update_run_state(draft_id, run_id, "running")
                AuditStore.log_event("draft_process_started", user_id, {
                    "draft_id": draft_id,
                    "run_id": run_id,
                    "stage": request.stage,
                    "operating_mode": request.operating_mode,
                    "scenario_id": request.scenario_id,
                })
            except Exception as draft_err:
                logger.warning("Failed to update draft state for draft_id=%s: %s", draft_id, draft_err)
        
        emit_run_started(
            run_id=run_id,
            trip_id=None,
            stage=request.stage,
            operating_mode=request.operating_mode,
        )

        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = AgencySettingsStore.load(agency_id)
        stage_started_at: dict[str, float] = {}

        def _stage_checkpoint(stage_name: str, data: Any) -> None:
            """Emit lifecycle-aware stage events and checkpoint data."""
            nonlocal current_stage
            try:
                event = "completed"
                payload_data = data
                error_message: Optional[str] = None

                if isinstance(data, dict) and isinstance(data.get("event"), str):
                    event = data.get("event", "completed")
                    payload_data = data.get("data")
                    error_message = data.get("error")

                if event == "entered":
                    current_stage = stage_name
                    stage_started_at[stage_name] = time.perf_counter()
                    emit_stage_entered(run_id, stage_name, trip_id=None)
                    return

                if event == "failed":
                    current_stage = stage_name
                    RunLedger.save_step(run_id, f"{stage_name}_failed", {
                        "stage_name": stage_name,
                        "error": error_message or "stage_failed",
                    })
                    return

                stage_start = stage_started_at.get(stage_name)
                if stage_start is None:
                    current_stage = stage_name
                    emit_stage_entered(run_id, stage_name, trip_id=None)
                    stage_start = time.perf_counter()
                    stage_started_at[stage_name] = stage_start

                val = _to_dict(payload_data) if payload_data is not None else None
                if val is not None:
                    RunLedger.save_step(run_id, stage_name, val)

                emit_stage_completed(
                    run_id,
                    stage_name,
                    execution_ms=(time.perf_counter() - stage_start) * 1000,
                    trip_id=None,
                )
                current_stage = stage_name
            except Exception as e:
                logger.error("Wave A: mid-run checkpoint failed stage=%s error=%s", stage_name, e)

        with _otel_tracer.start_as_current_span("spine_pipeline") as pipeline_span:
            pipeline_span.set_attribute("stage", request.stage)
            pipeline_span.set_attribute("run_id", run_id)
            pipeline_span.set_attribute("agency_id", agency_id)
            pipeline_span.set_attribute("user_id", user_id)

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
            stage_callback=_stage_checkpoint,
        )

        execution_ms = (time.perf_counter() - t0) * 1000
        meta.execution_ms = round(execution_ms, 2)
        pipeline_span.set_attribute("execution_ms", round(execution_ms, 2))
        if hasattr(result, "packet"):
            pipeline_span.set_attribute("trip_id", result.packet.packet_id if hasattr(result.packet, "packet_id") else "")

        raw_text_sources = [
            request.raw_note,
            request.owner_note,
            request.itinerary_text,
        ]
        if isinstance(request.structured_json, dict):
            source_payload = request.structured_json.get("source_payload")
            if isinstance(source_payload, dict):
                uploaded_file = source_payload.get("uploaded_file")
                if isinstance(uploaded_file, dict):
                    raw_text_sources.append(str(uploaded_file.get("extracted_text") or ""))
        raw_text = "\n".join(str(item) for item in raw_text_sources if item)

        packet_payload = _to_dict(result.packet) if hasattr(result, "packet") else {}
        live_checker = build_live_checker_signals(packet_payload or {}, raw_text)
        if live_checker:
            validation_payload = _to_dict(result.validation) if hasattr(result, "validation") else {}
            decision_payload = _to_dict(result.decision) if hasattr(result, "decision") else {}

            validation_base = validation_payload.get("overall_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = validation_payload.get("quality_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = packet_payload.get("quality_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = packet_payload.get("score")
            if not isinstance(validation_base, (int, float)):
                decision_state = str(decision_payload.get("decision_state") or "").upper()
                decision_base = {
                    "PROCEED_TRAVELER_SAFE": 82,
                    "PROCEED_INTERNAL_DRAFT": 74,
                    "ASK_FOLLOWUP": 64,
                    "STOP_NEEDS_REVIEW": 42,
                }.get(decision_state)
                validation_base = decision_base if decision_base is not None else 70

            adjusted_score = max(0, min(100, round(float(validation_base) - float(live_checker.get("score_penalty", 0)))))
            validation_payload["overall_score"] = adjusted_score
            validation_payload["public_checker_live_checks"] = live_checker
            decision_payload["public_checker_live_checks"] = live_checker
            decision_payload["hard_blockers"] = list(dict.fromkeys([
                *([str(item) for item in decision_payload.get("hard_blockers") or []]),
                *([str(item) for item in live_checker.get("hard_blockers") or []]),
            ]))
            decision_payload["soft_blockers"] = list(dict.fromkeys([
                *([str(item) for item in decision_payload.get("soft_blockers") or []]),
                *([str(item) for item in live_checker.get("soft_blockers") or []]),
            ]))
            packet_payload["public_checker_live_checks"] = live_checker
            packet_payload["score"] = adjusted_score
            result.validation = validation_payload
            result.decision = decision_payload
            result.packet = packet_payload

        _checkpoint_result_steps(run_id, result)

        if getattr(result, "early_exit", False):
            logger.warning(
                "spine_run early_exit run_id=%s reason=%s execution_ms=%.2f",
                run_id,
                result.early_exit_reason,
                execution_ms,
            )
            RunLedger.save_step(run_id, "blocked_result", {
                "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                "early_exit_reason": result.early_exit_reason,
                "meta": meta.model_dump(),
            })
            block_reason = result.early_exit_reason or "Pipeline blocked"
            RunLedger.block(run_id, block_reason=block_reason)
            _update_draft_for_terminal_state(run_id, "blocked", snapshot={"block_reason": block_reason, "stage_at_block": current_stage})
            emit_run_blocked(
                run_id=run_id,
                block_reason=block_reason,
                stage_at_block=current_stage,
                trip_id=None,
            )
            return

        if getattr(result, "partial_intake", False):
            logger.info(
                "spine_run partial_intake run_id=%s reason=%s execution_ms=%.2f",
                run_id,
                result.early_exit_reason,
                execution_ms,
            )
            # Save the partial trip with incomplete status
            # (packet is valid but missing quote-ready fields)
            trip_id_saved = save_processed_trip(
                {
                    "run_id": run_id,
                    "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                    "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                    "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                    "strategy": _to_dict(result.strategy) if hasattr(result, "strategy") else None,
                    "plan_candidate": _to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                    "traveler_bundle": _to_dict(result.traveler_bundle) if hasattr(result, "traveler_bundle") and result.traveler_bundle else None,
                    "internal_bundle": _to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
                    "safety": _to_dict(result.safety) if hasattr(result, "safety") else None,
                    "fees": _to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
                    "frontier_result": _to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
                    "meta": {
                        **meta.model_dump(),
                        "submission": consented_submission,
                        "retention_consent": request.retention_consent,
                    },
                },
                source="spine_api",
                agency_id=agency_id,
                user_id=user_id,
                trip_status="incomplete",
            )
            if not trip_id_saved:
                raise RuntimeError("save_processed_trip returned no trip_id for partial intake")
            RunLedger.update_meta(run_id, trip_id=trip_id_saved)
            logger.info("Partial trip saved: %s", trip_id_saved)

            RunLedger.complete(run_id, total_ms=execution_ms)
            _update_draft_for_terminal_state(run_id, "completed", trip_id=trip_id_saved, snapshot={"early_exit_reason": "partial_intake", "trip_id": trip_id_saved})
            emit_run_completed(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
            return

        if hasattr(result, "validation") and result.validation and not getattr(result.validation, "is_valid", True):
            logger.warning(
                "spine_run validation_invalid run_id=%s execution_ms=%.2f",
                run_id,
                execution_ms,
            )
            RunLedger.save_step(run_id, "blocked_result", {
                "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                "early_exit_reason": "validation_invalid",
                "meta": meta.model_dump(),
            })
            RunLedger.block(run_id, block_reason="Validation failed (defense-in-depth)")
            _update_draft_for_terminal_state(run_id, "blocked", snapshot={"block_reason": "Validation failed (defense-in-depth)", "stage_at_block": current_stage})
            emit_run_blocked(
                run_id=run_id,
                block_reason="Validation failed (defense-in-depth)",
                stage_at_block=current_stage,
                trip_id=None,
            )
            return

        logger.info(
            "spine_run ok=True run_id=%s stage=%s mode=%s scenario_id=%s execution_ms=%.2f agency_id=%s",
            run_id,
            request.stage,
            request.operating_mode,
            request.scenario_id,
            execution_ms,
            agency_id,
        )

        # Save the trip to persistence scoped to the user's agency
        trip_id_saved = save_processed_trip(
            {
                "run_id": run_id,
                "packet": _to_dict(result.packet) if hasattr(result, "packet") else None,
                "validation": _to_dict(result.validation) if hasattr(result, "validation") else None,
                "decision": _to_dict(result.decision) if hasattr(result, "decision") else None,
                "strategy": _to_dict(result.strategy) if hasattr(result, "strategy") else None,
                "plan_candidate": _to_dict(result.plan_candidate) if hasattr(result, "plan_candidate") and result.plan_candidate else None,
                "traveler_bundle": _to_dict(result.traveler_bundle) if hasattr(result, "traveler_bundle") and result.traveler_bundle else None,
                "internal_bundle": _to_dict(result.internal_bundle) if hasattr(result, "internal_bundle") and result.internal_bundle else None,
                "safety": _to_dict(result.safety) if hasattr(result, "safety") else None,
                "fees": _to_dict(result.fees) if hasattr(result, "fees") and result.fees else None,
                "frontier_result": _to_dict(result.frontier_result) if hasattr(result, "frontier_result") and result.frontier_result else None,
                "meta": {
                    **meta.model_dump(),
                    "submission": consented_submission,
                    "retention_consent": request.retention_consent,
                },
            },
            source="spine_api",
            agency_id=agency_id,
            user_id=user_id,
        )
        if not trip_id_saved:
            raise RuntimeError("save_processed_trip returned no trip_id")
        RunLedger.update_meta(run_id, trip_id=trip_id_saved)
        logger.info("Trip saved: %s", trip_id_saved)

        # Wave 10: Feedback-Driven Recovery Trigger
        trip_post = TripStore.get_trip(trip_id_saved)
        if trip_post and trip_post.get("analytics", {}).get("feedback_reopen"):
            from src.analytics.review import trigger_feedback_recovery
            trigger_feedback_recovery(trip_id_saved, reason=trip_post["analytics"].get("review_reason"))
            logger.info("Feedback recovery triggered for trip: %s", trip_id_saved)

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

        # Wave A: complete the ledger and emit terminal event
        # (All pipeline steps were already checkpointed incrementally via
        # stage_callback inside run_spine_once above.)
        try:
            RunLedger.complete(run_id, total_ms=execution_ms)
            _update_draft_for_terminal_state(run_id, "completed", trip_id=trip_id_saved, snapshot={"trip_id": trip_id_saved})
            emit_run_completed(run_id=run_id, trip_id=trip_id_saved, total_ms=execution_ms)
        except Exception as e:
            logger.error("Wave A: ledger complete failed for run %s: %s", run_id, e)

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
            _update_draft_for_terminal_state(run_id, "blocked", snapshot={"block_reason": error_message, "stage_at_block": current_stage})
            emit_run_blocked(
                run_id=run_id,
                block_reason=error_message,
                stage_at_block=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: block ledger failed for run %s: %s", run_id, ledger_err)

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
            _update_draft_for_terminal_state(run_id, "failed", snapshot={"error_type": type(e).__name__, "error_message": str(e), "stage_at_failure": current_stage})
            emit_run_failed(
                run_id=run_id,
                error_type=type(e).__name__,
                error_message=str(e),
                stage_at_failure=current_stage,
                trip_id=None,
            )
        except Exception as ledger_err:
            logger.error("Wave A: fail ledger failed for run %s: %s", run_id, ledger_err)

    finally:
        # Reset strict mode after every request to prevent state leaking to the next
        set_strict_mode(False)


def _run_public_checker_submission(request_dict: dict[str, Any]) -> RunStatusResponse:
    """Run the public checker synchronously and return a result payload."""
    t0 = time.perf_counter()
    request = SpineRunRequest(**request_dict)
    consented_submission = request_dict if request.retention_consent else {
        key: value
        for key, value in request_dict.items()
        if key not in {"raw_note", "owner_note", "itinerary_text", "structured_json"}
    }
    run_id = str(uuid.uuid4())
    steps_completed: list[str] = []

    if request.strict_leakage:
        set_strict_mode(True)

    try:
        envelopes = build_envelopes(request.model_dump(exclude_none=True))
        fixture_expectations = load_fixture_expectations(request.scenario_id)
        agency_settings = AgencySettingsStore.load(PUBLIC_CHECKER_AGENCY_ID)
        stage_started_at: dict[str, float] = {}
        current_stage: Optional[str] = None

        def _stage_checkpoint(stage_name: str, data: Any) -> None:
            nonlocal current_stage
            event = "completed"
            payload_data = data

            if isinstance(data, dict) and isinstance(data.get("event"), str):
                event = data.get("event", "completed")
                payload_data = data.get("data")

            if event == "entered":
                current_stage = stage_name
                stage_started_at[stage_name] = time.perf_counter()
                return

            if event == "completed":
                if stage_name not in steps_completed:
                    steps_completed.append(stage_name)
            current_stage = stage_name
            _ = payload_data

        result = run_spine_once(
            envelopes=envelopes,
            stage=request.stage,
            operating_mode=request.operating_mode,
            fixture_expectations=fixture_expectations,
            agency_settings=agency_settings,
            stage_callback=_stage_checkpoint,
        )

        execution_ms = (time.perf_counter() - t0) * 1000

        raw_text_sources = [
            request.raw_note,
            request.owner_note,
            request.itinerary_text,
        ]
        if isinstance(request.structured_json, dict):
            source_payload = request.structured_json.get("source_payload")
            if isinstance(source_payload, dict):
                uploaded_file = source_payload.get("uploaded_file")
                if isinstance(uploaded_file, dict):
                    raw_text_sources.append(str(uploaded_file.get("extracted_text") or ""))
        raw_text = "\n".join(str(item) for item in raw_text_sources if item)

        packet_payload = _to_dict(result.packet) if hasattr(result, "packet") else {}
        live_checker = build_live_checker_signals(packet_payload or {}, raw_text)
        validation_payload = _to_dict(result.validation) if hasattr(result, "validation") else {}
        decision_payload = _to_dict(result.decision) if hasattr(result, "decision") else {}

        if live_checker:
            validation_base = validation_payload.get("overall_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = validation_payload.get("quality_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = packet_payload.get("quality_score")
            if not isinstance(validation_base, (int, float)):
                validation_base = packet_payload.get("score")
            if not isinstance(validation_base, (int, float)):
                decision_state = str(decision_payload.get("decision_state") or "").upper()
                validation_base = {
                    "PROCEED_TRAVELER_SAFE": 82,
                    "PROCEED_INTERNAL_DRAFT": 74,
                    "ASK_FOLLOWUP": 64,
                    "STOP_NEEDS_REVIEW": 42,
                }.get(decision_state, 70)

            adjusted_score = max(0, min(100, round(float(validation_base) - float(live_checker.get("score_penalty", 0)))))
            validation_payload["overall_score"] = adjusted_score
            validation_payload["public_checker_live_checks"] = live_checker
            decision_payload["public_checker_live_checks"] = live_checker
            decision_payload["hard_blockers"] = list(dict.fromkeys([
                *([str(item) for item in decision_payload.get("hard_blockers") or []]),
                *([str(item) for item in live_checker.get("hard_blockers") or []]),
            ]))
            decision_payload["soft_blockers"] = list(dict.fromkeys([
                *([str(item) for item in decision_payload.get("soft_blockers") or []]),
                *([str(item) for item in live_checker.get("soft_blockers") or []]),
            ]))
            packet_payload["public_checker_live_checks"] = live_checker
            packet_payload["score"] = adjusted_score

        result_state = "completed"
        error_type: Optional[str] = None
        error_message: Optional[str] = None
        block_reason: Optional[str] = None

        if getattr(result, "early_exit", False):
            result_state = "blocked"
            block_reason = result.early_exit_reason or "Pipeline blocked"

        if hasattr(result, "validation") and result.validation and not getattr(result.validation, "is_valid", True):
            result_state = "blocked"
            block_reason = "Validation failed (defense-in-depth)"

        if getattr(result, "partial_intake", False):
            trip_status = "incomplete"
        elif result_state == "blocked":
            trip_status = "blocked"
        else:
            trip_status = "new"

        trip_id_saved = save_processed_trip(
            # Reduced persistence contract: public checker only persists the 5
            # non-private compartments. Internal/frontier/fees data is intentionally
            # excluded — public checker is customer-facing and should not persist
            # agent-only private compartments (internal_bundle, safety, fees,
            # frontier_result, traveler_bundle). See TRIP_STATE_CONTRACT.md.
            {
                "run_id": run_id,
                "packet": packet_payload if packet_payload else None,
                "validation": validation_payload if validation_payload else None,
                "decision": decision_payload if decision_payload else None,
                "strategy": _to_dict(result.strategy) if hasattr(result, "strategy") else None,
                "meta": {
                    "stage": request.stage,
                    "operating_mode": request.operating_mode,
                    "fixture_id": request.scenario_id,
                    "execution_ms": round(execution_ms, 2),
                    "submission": consented_submission,
                    "retention_consent": request.retention_consent,
                },
            },
            source="public_checker",
            agency_id=PUBLIC_CHECKER_AGENCY_ID,
            user_id=None,
            trip_status=trip_status,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        return RunStatusResponse(
            run_id=run_id,
            state=result_state,
            trip_id=trip_id_saved,
            stage=request.stage,
            operating_mode=request.operating_mode,
            agency_id=PUBLIC_CHECKER_AGENCY_ID,
            created_at=now_iso,
            started_at=now_iso,
            completed_at=now_iso,
            total_ms=round(execution_ms, 2),
            steps_completed=steps_completed,
            events=[],
            error_type=error_type,
            error_message=error_message,
            stage_at_failure=None,
            block_reason=block_reason,
            validation=validation_payload if validation_payload else None,
            packet=packet_payload if packet_payload else None,
            decision_state=str(decision_payload.get("decision_state") or None),
            follow_up_questions=list(result.follow_up_questions) if hasattr(result, "follow_up_questions") else [],
            hard_blockers=list(decision_payload.get("hard_blockers") or []),
            soft_blockers=list(decision_payload.get("soft_blockers") or []),
        )
    except Exception as exc:
        execution_ms = (time.perf_counter() - t0) * 1000
        logger.error("Public checker submission failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        set_strict_mode(False)


@app.post("/api/public-checker/run", response_model=RunStatusResponse)
def run_public_checker(
    request: SpineRunRequest,
) -> RunStatusResponse:
    """Submit a public itinerary checker run without agency auth."""
    return _run_public_checker_submission(request.model_dump(exclude_none=True))


@app.post("/run", response_model=RunAcceptedResponse)
async def run_spine(
    request: SpineRunRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
) -> RunAcceptedResponse:
    """
    Submit a spine run and return immediately.

    This is the canonical Process Trip path. Poll GET /runs/{run_id} for
    status, checkpointed steps, events, and final trip_id.
    """
    run_id = str(uuid.uuid4())
    RunLedger.create(
        run_id=run_id,
        trip_id=None,
        stage=request.stage,
        operating_mode=request.operating_mode,
        agency_id=agency.id,
        draft_id=request.draft_id,
    )
    request_dict = request.model_dump(exclude_none=True)
    # Run pipeline in a daemon thread (not multiprocessing) to avoid
    # all file-descriptor-inheritance and lock-deadlock issues across
    # fork/spawn on macOS/Linux.
    thread = threading.Thread(
        target=_execute_spine_pipeline,
        args=(run_id, request_dict, agency.id, user.id),
        daemon=True,
        name=f"spine-{run_id[:8]}",
    )
    thread.start()

    logger.info("spine_run queued run_id=%s agency_id=%s", run_id, agency.id)
    return RunAcceptedResponse(run_id=run_id, state="queued")


# =============================================================================
# Run Status Endpoints (Wave A)
# =============================================================================

@app.get("/runs")
def list_runs(
    trip_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
    agency: Agency = Depends(get_current_agency),
):
    """
    List run records, newest first.
    Optionally filter by trip_id and/or state (queued|running|completed|failed|blocked).
    """
    runs = RunLedger.list_runs(trip_id=trip_id, state=state, limit=500)
    agency_runs = [r for r in runs if r.get("agency_id") == agency.id][:limit]
    return {"items": agency_runs, "total": len(agency_runs)}


@app.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(
    run_id: str,
    agency: Agency = Depends(get_current_agency),
) -> RunStatusResponse:
    """
    Full run status including metadata and latest checkpointed steps.
    Returns 404 if the run_id is not found in the ledger.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    if meta.get("state") in ("queued", "running"):
        RunLedger.timeout_stale_runs(max_age_seconds=300)

    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    steps = RunLedger.get_all_steps(run_id)
    events = get_run_events(run_id)

    decision_data = None
    blocked_result_data = None
    if "decision" in steps:
        decision_data = steps["decision"].get("data")
    elif "blocked_result" in steps:
        blocked_result_data = steps["blocked_result"].get("data") or {}
        decision_data = blocked_result_data.get("decision")

    decision_state = None
    follow_up_questions: list[dict[str, Any]] = []
    hard_blockers: list[str] = []
    soft_blockers: list[str] = []
    if isinstance(decision_data, dict):
        decision_state = decision_data.get("decision_state")
        follow_up_questions = decision_data.get("follow_up_questions") or []
        hard_blockers = decision_data.get("hard_blockers") or []
        soft_blockers = decision_data.get("soft_blockers") or []

    # Extract validation and packet from blocked_result or individual steps
    validation_data = None
    packet_data = None
    if blocked_result_data:
        validation_data = blocked_result_data.get("validation")
        packet_data = blocked_result_data.get("packet")
    if not validation_data and "validation" in steps:
        validation_data = steps["validation"].get("data")
    if not packet_data and "packet" in steps:
        packet_data = steps["packet"].get("data")

    return RunStatusResponse(
        **meta,
        steps_completed=list(steps.keys()),
        events=events,
        decision_state=decision_state,
        follow_up_questions=follow_up_questions,
        hard_blockers=hard_blockers,
        soft_blockers=soft_blockers,
        validation=validation_data,
        packet=packet_data,
    )


@app.get("/runs/{run_id}/steps/{step_name}")
def get_run_step(
    run_id: str,
    step_name: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Return the full checkpointed output for a single pipeline step.
    Returns 404 if the step has not been checkpointed yet.
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    step = RunLedger.get_step(run_id, step_name)
    if step is None:
        raise HTTPException(
            status_code=404,
            detail=f"Step '{step_name}' not yet checkpointed for run {run_id}",
        )
    return step


@app.get("/runs/{run_id}/events")
def get_run_event_stream(
    run_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Return the append-only event log for a run in chronological order.
    Returns empty list if the run_id is unknown (no events written yet).
    """
    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    meta = RunLedger.get_meta(run_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    if meta.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    events = get_run_events(run_id)
    return {"run_id": run_id, "events": events, "total": len(events)}


@app.get("/api/public-checker/{trip_id}", response_model=PublicCheckerExportResponse)
def get_public_checker_package(trip_id: str):
    package = persistence.PublicCheckerArtifactStore.export_trip_package(trip_id)
    if not package:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return package


@app.get("/api/public-checker/{trip_id}/export", response_model=PublicCheckerExportResponse)
def export_public_checker_package(trip_id: str):
    package = persistence.PublicCheckerArtifactStore.export_trip_package(trip_id)
    if not package:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return package


@app.delete("/api/public-checker/{trip_id}", response_model=PublicCheckerDeleteResponse)
def delete_public_checker_package(trip_id: str):
    deleted_artifacts = persistence.PublicCheckerArtifactStore.delete_trip_artifacts(trip_id)
    deleted_trip = TripStore.delete_trip(trip_id)
    if not deleted_artifacts and not deleted_trip:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return {
        "ok": True,
        "trip_id": trip_id,
        "deleted_trip": deleted_trip,
        "deleted_artifacts": deleted_artifacts,
    }


# =============================================================================
# Draft Management Endpoints (Phase 0)
# =============================================================================

class CreateDraftRequest(BaseModel):
    name: Optional[str] = None
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    stage: str = "discovery"
    operating_mode: str = "normal_intake"
    scenario_id: Optional[str] = None
    strict_leakage: bool = False


class UpdateDraftRequest(BaseModel):
    name: Optional[str] = None
    customer_message: Optional[str] = None
    agent_notes: Optional[str] = None
    structured_json: Optional[dict] = None
    itinerary_text: Optional[str] = None
    stage: Optional[str] = None
    operating_mode: Optional[str] = None
    scenario_id: Optional[str] = None
    strict_leakage: Optional[bool] = None
    expected_version: Optional[int] = None
    is_auto_save: bool = False


class PromoteDraftRequest(BaseModel):
    trip_id: str


@app.post("/api/drafts")
def create_draft(
    request: CreateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Create a new draft. Auto-generates name if not provided."""
    name = request.name or _generate_draft_name(request.customer_message, request.agent_notes)
    draft = DraftStore.create(
        agency_id=agency.id,
        created_by=user.id,
        name=name,
        customer_message=request.customer_message,
        agent_notes=request.agent_notes,
        stage=request.stage,
        operating_mode=request.operating_mode,
        scenario_id=request.scenario_id,
        strict_leakage=request.strict_leakage,
    )
    AuditStore.log_event("draft_created", user.id, {
        "draft_id": draft.id,
        "agency_id": agency.id,
        "name": draft.name,
    })
    return {
        "draft_id": draft.id,
        "name": draft.name,
        "status": draft.status,
        "created_at": draft.created_at,
    }


def _generate_draft_name(customer_message: Optional[str], agent_notes: Optional[str]) -> str:
    """Auto-generate draft name from first line of content."""
    content = (customer_message or "").strip() or (agent_notes or "").strip()
    if content:
        first_line = content.split("\n")[0].strip()
        if len(first_line) > 60:
            first_line = first_line[:57] + "..."
        return first_line or f"Draft — {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}"
    return f"Draft — {datetime.now(timezone.utc).strftime('%b %d, %H:%M')}"


@app.get("/api/drafts")
def list_drafts(
    status: Optional[str] = None,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """List drafts for the current agency, optionally filtered by status."""
    drafts = DraftStore.list_by_agency(agency.id, status=status, limit=limit)
    return {
        "items": [
            {
                "draft_id": d.id,
                "name": d.name,
                "status": d.status,
                "stage": d.stage,
                "operating_mode": d.operating_mode,
                "last_run_state": d.last_run_state,
                "promoted_trip_id": d.promoted_trip_id,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "created_by": d.created_by,
            }
            for d in drafts
        ],
        "total": len(drafts),
    }


@app.get("/api/drafts/{draft_id}")
def get_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a single draft by ID."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft.model_dump()


@app.put("/api/drafts/{draft_id}")
def update_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Full update of a draft. Requires version match for optimistic concurrency."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft.status in ("promoted", "merged", "discarded"):
        raise HTTPException(status_code=409, detail=f"Cannot update draft in status: {draft.status}")
    
    updates = request.model_dump(exclude_none=True)
    is_auto_save = updates.pop("is_auto_save", False)
    expected_version = updates.pop("expected_version", None)
    
    try:
        updated = DraftStore.patch(draft_id, updates, expected_version=expected_version)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    
    if updated:
        AuditStore.log_event(
            "draft_autosaved" if is_auto_save else "draft_saved",
            user.id,
            {"draft_id": draft_id, "fields_changed": list(updates.keys()), "auto_save": is_auto_save},
        )
    return updated.model_dump() if updated else None


@app.patch("/api/drafts/{draft_id}")
def patch_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Partial update of a draft. Same as PUT but semantic PATCH."""
    return update_draft(draft_id, request, agency, user)


@app.delete("/api/drafts/{draft_id}")
def discard_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Soft-delete a draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    discarded = DraftStore.discard(draft_id, user.id)
    if discarded:
        AuditStore.log_event("draft_discarded", user.id, {"draft_id": draft_id})
    return {"ok": True, "draft_id": draft_id, "status": "discarded"}


@app.post("/api/drafts/{draft_id}/restore")
def restore_draft(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Restore a discarded draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    restored = DraftStore.restore(draft_id)
    if restored:
        AuditStore.log_event("draft_restored", user.id, {"draft_id": draft_id})
    return {"ok": True, "draft_id": draft_id, "status": restored.status if restored else "unknown"}


@app.get("/api/drafts/{draft_id}/events")
def get_draft_events(
    draft_id: str,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """Get audit events for a draft."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    all_events = AuditStore.get_events(limit=limit * 2)  # Overfetch and filter
    draft_events = [
        e for e in all_events
        if e.get("details", {}).get("draft_id") == draft_id
    ]
    return {"draft_id": draft_id, "events": draft_events[-limit:], "total": len(draft_events)}


@app.get("/api/drafts/{draft_id}/runs")
def get_draft_runs(
    draft_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get runs linked to this draft via run_snapshots."""
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Use run_snapshots from draft to find linked runs
    runs = []
    for snapshot in (draft.run_snapshots or []):
        run_id = snapshot.get("run_id")
        if not run_id:
            continue
        meta = RunLedger.get_meta(run_id)
        if meta and meta.get("agency_id") == agency.id:
            runs.append(meta)
    
    return {"draft_id": draft_id, "runs": runs, "total": len(runs)}


@app.post("/api/drafts/{draft_id}/promote")
def promote_draft(
    draft_id: str,
    request: PromoteDraftRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Promote a draft to a trip. Marks draft as promoted and read-only."""
    trip_id = request.trip_id
    draft = DraftStore.get(draft_id)
    if not draft or draft.agency_id != agency.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft.status == "promoted":
        raise HTTPException(status_code=409, detail="Draft already promoted")
    
    promoted = DraftStore.promote(draft_id, trip_id)
    if promoted:
        AuditStore.log_event("draft_promoted", user.id, {
            "draft_id": draft_id,
            "trip_id": trip_id,
        })
    return {"ok": True, "draft_id": draft_id, "trip_id": trip_id, "status": "promoted"}


# =============================================================================
# Trip Management Endpoints
# =============================================================================

@app.get("/trips")
async def list_trips(
    status: Optional[str] = None,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """
    List trips for the current user's agency, optionally filtered by status.
    
    Test agencies (is_test=True) will automatically get mock data seeded
    if no trips exist yet.
    """
    agency_id = agency.id
    
    # Auto-seed for test agencies if no trips exist
    if agency.is_test:
        existing_trips = TripStore.list_trips(agency_id=agency_id)
        if not existing_trips:
            try:
                seed_count = await _seed_scenario_for_agency(agency_id)
                logger.info("Auto-seeded %d mock trips for test agency %s", seed_count, agency_id)
            except Exception as e:
                logger.warning("Failed to auto-seed for test agency: %s", e)
    
    trips = TripStore.list_trips(status=status, limit=limit, agency_id=agency_id)
    total = TripStore.count_trips(status=status, agency_id=agency_id)
    return {"items": trips, "total": total}


# Canonical inbox statuses — shared source of truth for frontend + backend
_INBOX_STATUSES = "new,incomplete,needs_followup,awaiting_customer_details,snoozed"

@app.get("/inbox", response_model=InboxResponse)
def get_inbox(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    filter_key: Optional[str] = Query(None, alias="filter"),
    sort: Optional[str] = Query("priority"),
    dir: Optional[str] = Query("desc"),
    q: Optional[str] = Query(None),
    # Composable multi-select filter params
    priority: Optional[str] = Query(None),
    slaStatus: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    assignedTo: Optional[str] = Query(None),
    minValue: Optional[int] = Query(None),
    maxValue: Optional[int] = Query(None),
    agency: Agency = Depends(get_current_agency),
):
    """
    Canonical inbox endpoint — service-level projected, filtered, sorted, paginated.

    Returns a stable {items, total, hasMore, filterCounts} envelope.
    filterCounts are computed over the FULL projected dataset so tab counts
    are accurate regardless of active filter or page size.

    Query params:
      filter     — tab filter: all | at_risk | incomplete | unassigned
      sort       — sort key: priority | destination | value | party | dates | sla
      dir        — asc | desc
      q          — fuzzy search on customerName, destination, reference, id
      priority   — comma-separated: low,medium,high,critical
      slaStatus  — comma-separated: on_track,at_risk,breached
      stage      — comma-separated: intake,details,options,review,booking,completed
      assignedTo — comma-separated agent IDs (or "unassigned")
      minValue   — minimum trip budget
      maxValue   — maximum trip budget
    """
    agency_id = agency.id

    # Fetch ALL inbox trips for this agency (bounded set, typically <10k).
    raw_trips = TripStore.list_trips(
        status=_INBOX_STATUSES,
        limit=5000,
        agency_id=agency_id,
    )

    result = build_inbox_response(
        raw_trips,
        page=page,
        limit=limit,
        filter_key=filter_key,
        sort_key=sort,
        sort_dir=dir,
        search_query=q,
        priorities=priority.split(",") if priority else None,
        sla_statuses=slaStatus.split(",") if slaStatus else None,
        stages=stage.split(",") if stage else None,
        assigned_to=assignedTo.split(",") if assignedTo else None,
        min_value=minValue,
        max_value=maxValue,
    )

    return result


@app.get("/inbox/stats", response_model=InboxStatsResponse)
def get_inbox_stats(
    agency: Agency = Depends(get_current_agency),
):
    """Return aggregate inbox statistics for Overview cards."""
    agency_id = agency.id
    total = TripStore.count_trips(status=_INBOX_STATUSES, agency_id=agency_id)

    # TODO: replace with DB-level aggregations when analytics/assignment columns are indexed
    # For now, fetch a bounded subset for stat accuracy under 100 trips.
    trips = TripStore.list_trips(status=_INBOX_STATUSES, limit=500, agency_id=agency_id)

    unassigned = sum(1 for t in trips if not t.get("assigned_to"))
    critical = sum(
        1 for t in trips
        if t.get("analytics", {}).get("escalation_severity") in ("high", "critical")
    )
    at_risk = sum(
        1 for t in trips
        if t.get("analytics", {}).get("sla_status") == "at_risk"
    )

    return {"total": total, "unassigned": unassigned, "critical": critical, "atRisk": at_risk}


@app.get("/trips/{trip_id}")
def get_trip(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a specific trip by ID."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Include assignment info
    assignment = AssignmentStore.get_assignment(trip_id)
    if assignment:
        trip["assigned_to"] = assignment["agent_id"]
        trip["assigned_to_name"] = assignment["agent_name"]
    
    return trip


@app.get("/trips/{trip_id}/suitability", response_model=SuitabilityFlagsResponse)
def get_trip_suitability(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Get all suitability flags for a trip.
    
    Returns suitability signals with confidence scores and tier information.
    Tier 1 (critical/high): Hard blockers requiring operator acknowledgment
    Tier 2 (medium/low): Warnings for operator review
    """
    # Verify trip exists and belongs to the agency
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Fetch suitability flags from the trip's decision output
    suitability_flags = []
    
    try:
        # Get the decision output if it exists
        decision_output = trip.get("decision_output")
        if decision_output and isinstance(decision_output, dict):
            # Extract suitability_flags from decision_output
            flags_from_decision = decision_output.get("suitability_flags", [])
            if flags_from_decision:
                for flag in flags_from_decision:
                    if isinstance(flag, dict):
                        # Convert flag to the expected format with id, name, confidence, tier
                        suitability_flags.append({
                            "id": str(uuid.uuid4()),
                            "trip_id": trip_id,
                            "name": flag.get("flag_type", "unknown"),
                            "confidence": int(flag.get("confidence", 0) * 100),  # Convert 0-1 to 0-100
                            "tier": flag.get("severity", "low"),
                            "reason": flag.get("reason", ""),
                            "created_at": trip.get("created_at"),
                        })
    except Exception as e:
        logger.warning(f"Error extracting suitability flags for trip {trip_id}: {e}")
    
    return SuitabilityFlagsResponse(
        trip_id=trip_id,
        suitability_flags=suitability_flags,
    )


@app.get("/trips/{trip_id}/agent-events")
def get_trip_agent_events(
    trip_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    agency: Agency = Depends(get_current_agency),
):
    """
    Return product-agent observability events for a single trip.

    Includes only canonical `agent_event` records emitted by backend product
    agents. Trip and agency access controls are enforced.
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    events = AuditStore.get_agent_events_for_trip(trip_id=trip_id, limit=limit)
    return {"trip_id": trip_id, "events": events, "total": len(events)}


@app.get("/agents/runtime")
def get_agent_runtime(
    agency: Agency = Depends(get_current_agency),
):
    """
    Return canonical backend product-agent registry and supervisor health.

    This is the single runtime introspection surface for backend product agents;
    it intentionally exposes static in-repo registry contracts instead of
    dynamic plugin metadata.
    """
    _ = agency
    return {
        "registry": _agent_supervisor.registry.definitions(),
        "supervisor": _agent_supervisor.health(),
        "recovery_agent": {
            "name": "recovery_agent",
            "running": _recovery_agent.is_running,
            "trigger_contract": "Trips stuck beyond configured stage thresholds.",
            "input_contract": "Active trip with id, stage/state, and updated_at/updatedAt.",
            "output_contract": "Re-queue through runner when configured, else escalate review_status.",
            "idempotency_contract": "Per-trip in-memory requeue count with max attempts before escalation.",
            "failure_contract": "Fail closed by emitting agent_failed audit events.",
        },
    }


@app.post("/agents/runtime/run-once")
def run_agent_runtime_once(
    agent_name: Optional[str] = Query(default=None),
    agency: Agency = Depends(get_current_agency),
):
    """
    Synchronously run one supervisor pass for testing/admin operations.
    """
    _ = agency
    if agent_name and agent_name not in _agent_supervisor.health()["registered_agents"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    results = _agent_supervisor.run_once(agent_name=agent_name)
    return {
        "agent_name": agent_name,
        "results": [result.to_dict() for result in results],
        "total": len(results),
        "supervisor": _agent_supervisor.health(),
    }


@app.get("/agents/runtime/events")
def get_agent_runtime_events(
    limit: int = Query(default=100, ge=1, le=1000),
    agent_name: Optional[str] = Query(default=None),
    correlation_id: Optional[str] = Query(default=None),
    agency: Agency = Depends(get_current_agency),
):
    """Return canonical backend product-agent events across trips."""
    _ = agency
    events = AuditStore.get_agent_events(limit=limit, agent_name=agent_name, correlation_id=correlation_id)
    return {"events": events, "total": len(events)}


@app.patch("/trips/{trip_id}")
def patch_trip(
    trip_id: str,
    updates: Dict[str, Any],
    agency: Agency = Depends(get_current_agency),
):
    """
    Update trip fields (e.g. status, follow_up_due_date).
    
    Supported fields:
    - status: Trip status (new, in_progress, completed, etc.)
    - follow_up_due_date: ISO-8601 datetime string for promised follow-up
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    if "stage" in updates:
        raise HTTPException(
            status_code=400,
            detail="Use PATCH /trips/{trip_id}/stage to change stage",
        )

    if "booking_data" in updates:
        raise HTTPException(
            status_code=400,
            detail="Use PATCH /trips/{trip_id}/booking-data to update booking data",
        )

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
    
    def _clone_json(value: Any, fallback: Any) -> Any:
        if isinstance(value, (dict, list)):
            return json.loads(json.dumps(value))
        return fallback

    def _trimmed_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _parse_budget_amount(raw_budget: Optional[str]) -> Optional[float]:
        if not raw_budget:
            return None
        normalized = raw_budget.replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)", normalized)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _sync_manual_trip_fields(current_trip: Dict[str, Any], incoming_updates: Dict[str, Any]) -> Dict[str, Any]:
        synced_updates = dict(incoming_updates)
        extracted = _clone_json(current_trip.get("extracted"), {}) or {}
        facts = extracted.setdefault("facts", {})
        validation = _clone_json(current_trip.get("validation"), {}) or {}
        warnings = validation.get("warnings")
        warning_list = warnings if isinstance(warnings, list) else []

        fields_to_clear: set[str] = set()

        if "origin" in incoming_updates:
            origin_value = _trimmed_string(incoming_updates.get("origin"))
            if origin_value:
                facts["origin_city"] = {
                    "value": origin_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                fields_to_clear.add("origin_city")

        if "budget" in incoming_updates:
            budget_text = _trimmed_string(incoming_updates.get("budget"))
            if budget_text:
                facts["budget_raw_text"] = {
                    "value": budget_text,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                parsed_budget = _parse_budget_amount(budget_text)
                if parsed_budget is not None:
                    facts["budget"] = {
                        "value": parsed_budget,
                        "confidence": 1.0,
                        "authority_level": "explicit_user",
                    }
                fields_to_clear.add("budget_raw_text")

        if "trip_priorities" in incoming_updates:
            priorities_value = _trimmed_string(incoming_updates.get("trip_priorities"))
            if priorities_value:
                facts["trip_priorities"] = {
                    "value": priorities_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                fields_to_clear.add("trip_priorities")

        if "date_flexibility" in incoming_updates:
            flexibility_value = _trimmed_string(incoming_updates.get("date_flexibility"))
            if flexibility_value:
                facts["date_flexibility"] = {
                    "value": flexibility_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                fields_to_clear.add("date_flexibility")

        if fields_to_clear:
            validation["warnings"] = [
                warning
                for warning in warning_list
                if str((warning or {}).get("field") or "") not in fields_to_clear
            ]
            synced_updates["extracted"] = extracted
            synced_updates["validation"] = validation

        return synced_updates

    updates = _sync_manual_trip_fields(trip, updates)

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


VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}


class StageTransitionRequest(BaseModel):
    target_stage: str
    reason: Optional[str] = None
    expected_current_stage: Optional[str] = None


@app.patch("/trips/{trip_id}/stage")
def transition_trip_stage(
    trip_id: str,
    request: StageTransitionRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Durable manual stage transition with optimistic concurrency and audit."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    if request.target_stage not in VALID_STAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid target_stage '{request.target_stage}'. Must be one of {sorted(VALID_STAGES)}",
        )

    current_stage = trip.get("stage", "discovery")

    if request.expected_current_stage is not None and request.expected_current_stage != current_stage:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Stage conflict",
                "expected": request.expected_current_stage,
                "actual": current_stage,
            },
        )

    if request.target_stage == current_stage:
        return {
            "trip_id": trip_id,
            "old_stage": current_stage,
            "new_stage": current_stage,
            "changed": False,
            "readiness": trip.get("validation", {}).get("readiness"),
        }

    TripStore.update_trip(trip_id, {"stage": request.target_stage})

    AuditStore.log_event("stage_transition", agency.id, {
        "trip_id": trip_id,
        "from": current_stage,
        "to": request.target_stage,
        "trigger": "manual",
        "reason": request.reason,
        "actor": "operator",
    })

    return {
        "trip_id": trip_id,
        "old_stage": current_stage,
        "new_stage": request.target_stage,
        "changed": True,
        "readiness": trip.get("validation", {}).get("readiness"),
    }


# ---------------------------------------------------------------------------
# Booking Data Models & Endpoints
# ---------------------------------------------------------------------------

class BookingTravelerModel(BaseModel):
    traveler_id: str
    full_name: str
    date_of_birth: str
    passport_number: Optional[str] = None
    passport_expiry: Optional[str] = None
    nationality: Optional[str] = None
    emergency_contact: Optional[str] = None

    @field_validator("full_name", "traveler_id", "date_of_birth")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class BookingPayerModel(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class BookingDataModel(BaseModel):
    travelers: List[BookingTravelerModel]
    payer: Optional[BookingPayerModel] = None
    special_requirements: Optional[str] = None
    booking_notes: Optional[str] = None

    @field_validator("travelers")
    @classmethod
    def non_empty(cls, v: List[BookingTravelerModel]) -> List[BookingTravelerModel]:
        if not v:
            raise ValueError("must contain at least one traveler")
        return v


class BookingDataUpdateRequest(BaseModel):
    booking_data: BookingDataModel
    reason: Optional[str] = None
    expected_updated_at: Optional[str] = None


def _booking_data_envelope(trip: dict, booking_data: Any) -> dict:
    return {
        "trip_id": trip.get("id"),
        "booking_data": booking_data,
        "updated_at": trip.get("updated_at"),
        "stage": trip.get("stage", "discovery"),
        "readiness": (trip.get("validation") or {}).get("readiness"),
    }


@app.get("/trips/{trip_id}/booking-data")
def get_booking_data(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Lazy-load booking data for a trip. Not included in generic GET /trips."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    booking_data = TripStore.get_booking_data(trip_id)
    return _booking_data_envelope(trip, booking_data)


@app.patch("/trips/{trip_id}/booking-data")
def update_booking_data(
    trip_id: str,
    request: BookingDataUpdateRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Update booking data with stage gate, optimistic lock, audit, readiness recompute."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Stage gate: only proposal/booking
    current_stage = trip.get("stage", "discovery")
    if current_stage not in ("proposal", "booking"):
        raise HTTPException(
            status_code=403,
            detail=f"Booking data can only be updated at proposal/booking stage, current: {current_stage}",
        )

    # Optimistic lock
    if request.expected_updated_at is not None:
        actual = trip.get("updated_at")
        if actual and request.expected_updated_at != actual:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Booking data conflict",
                    "expected_updated_at": request.expected_updated_at,
                    "actual_updated_at": actual,
                },
            )

    bd_dict = request.booking_data.model_dump()

    # Save booking_data
    updated = TripStore.update_trip(trip_id, {"booking_data": bd_dict})

    # Audit: metadata only, no raw PII
    AuditStore.log_event("booking_data_updated", agency.id, {
        "trip_id": trip_id,
        "stage": current_stage,
        "reason": request.reason,
        "fields_changed": [
            "travelers",
            "payer" if request.booking_data.payer else None,
            "special_requirements" if request.booking_data.special_requirements else None,
            "booking_notes" if request.booking_data.booking_notes else None,
        ],
        "traveler_count": len(request.booking_data.travelers),
        "has_passport_data": any(t.passport_number for t in request.booking_data.travelers),
        "has_payer": request.booking_data.payer is not None,
        "actor": "operator",
    })

    # Readiness recompute: reload trip data and persist updated validation.readiness
    from intake.readiness import compute_readiness
    from intake.packet_models import CanonicalPacket
    packet = CanonicalPacket(packet_id=trip_id)
    packet.facts.update((trip.get("extracted") or {}).get("facts", {}))
    readiness = compute_readiness(
        packet,
        validation=trip.get("validation"),
        decision=trip.get("decision"),
        traveler_bundle=trip.get("traveler_bundle"),
        internal_bundle=trip.get("internal_bundle"),
        safety=trip.get("safety"),
        fees=trip.get("fees"),
        booking_data=bd_dict,
    )
    validation = dict(trip.get("validation") or {})
    validation["readiness"] = readiness.to_dict()
    updated = TripStore.update_trip(trip_id, {"validation": validation})

    booking_data = TripStore.get_booking_data(trip_id)
    return _booking_data_envelope(updated, booking_data)


# ---------------------------------------------------------------------------
# Booking collection tokens + customer review
# ---------------------------------------------------------------------------

def _get_db_session():
    """Get an async DB session for use in sync endpoints."""
    from spine_api.core.database import async_session_maker
    return async_session_maker()


class CollectionLinkResponse(BaseModel):
    token_id: str
    collection_url: str
    expires_at: str
    trip_id: str
    status: str


class CollectionLinkStatusResponse(BaseModel):
    has_active_token: bool
    token_id: Optional[str] = None
    expires_at: Optional[str] = None
    status: Optional[str] = None
    has_pending_submission: bool


class PendingBookingDataResponse(BaseModel):
    trip_id: str
    pending_booking_data: Optional[dict] = None
    booking_data_source: Optional[str] = None
    submitted_at: Optional[str] = None


class ReviewActionRequest(BaseModel):
    reason: Optional[str] = None


class PublicCollectionContext(BaseModel):
    valid: bool
    reason: Optional[str] = None
    trip_summary: Optional[dict] = None
    already_submitted: bool = False
    expires_at: Optional[str] = None


class PublicSubmissionResponse(BaseModel):
    ok: bool
    message: str


async def _ts(fn, *args, **kwargs):
    """Run a sync TripStore call from an async endpoint without blocking the event loop.

    Offloads to a thread where _run_async_blocking creates a fresh asyncio loop
    for asyncpg, avoiding deadlocks with TestClient's anyio loop.
    """
    import asyncio
    return await asyncio.to_thread(fn, *args, **kwargs)


@app.post("/trips/{trip_id}/collection-link", response_model=CollectionLinkResponse)
async def create_collection_link(
    trip_id: str,
    expires_in_hours: int = 168,
    agency: Agency = Depends(get_current_agency),
):
    """Generate a customer collection link for this trip."""
    from spine_api.services.collection_service import generate_token
    from spine_api.core.database import async_session_maker

    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    current_stage = trip.get("stage", "discovery")
    if current_stage not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail=f"Collection links only available at proposal/booking, current: {current_stage}")

    async with async_session_maker() as db:
        plain_token, record = await generate_token(
            db, trip_id, agency.id, agency.id, expires_in_hours,
        )

    host = os.getenv("FRONTEND_URL", "http://localhost:3000")
    collection_url = f"{host}/c/{plain_token}"

    AuditStore.log_event("booking_collection_link_created", agency.id, {
        "trip_id": trip_id,
        "token_id": record.id,
        "expires_at": record.expires_at.isoformat(),
    })

    return CollectionLinkResponse(
        token_id=record.id,
        collection_url=collection_url,
        expires_at=record.expires_at.isoformat(),
        trip_id=trip_id,
        status=record.status,
    )


@app.get("/trips/{trip_id}/collection-link", response_model=CollectionLinkStatusResponse)
async def get_collection_link_status(trip_id: str, agency: Agency = Depends(get_current_agency)):
    """Check collection link status and pending submission."""
    from spine_api.services.collection_service import get_active_token_for_trip
    from spine_api.core.database import async_session_maker

    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    async with async_session_maker() as db:
        token = await get_active_token_for_trip(db, trip_id)
    pending = await _ts(TripStore.get_pending_booking_data, trip_id)

    return CollectionLinkStatusResponse(
        has_active_token=token is not None,
        token_id=token.id if token else None,
        expires_at=token.expires_at.isoformat() if token else None,
        status=token.status if token else None,
        has_pending_submission=pending is not None,
    )


@app.delete("/trips/{trip_id}/collection-link")
async def revoke_collection_link(trip_id: str, agency: Agency = Depends(get_current_agency)):
    """Revoke the active collection link."""
    from spine_api.services.collection_service import revoke_token
    from spine_api.core.database import async_session_maker

    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    async with async_session_maker() as db:
        revoked = await revoke_token(db, trip_id, agency.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="No active collection link found")

    AuditStore.log_event("booking_collection_link_revoked", agency.id, {
        "trip_id": trip_id,
    })
    return {"ok": True}


@app.get("/trips/{trip_id}/pending-booking-data", response_model=PendingBookingDataResponse)
async def get_pending_booking_data(trip_id: str, agency: Agency = Depends(get_current_agency)):
    """View pending customer submission. Agent-only."""
    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    pending = await _ts(TripStore.get_pending_booking_data, trip_id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data")

    return PendingBookingDataResponse(
        trip_id=trip_id,
        pending_booking_data=pending,
        booking_data_source=trip.get("booking_data_source"),
    )


@app.post("/trips/{trip_id}/pending-booking-data/accept")
async def accept_pending_booking_data(trip_id: str, request: ReviewActionRequest = ReviewActionRequest(), agency: Agency = Depends(get_current_agency)):
    """Accept pending customer submission into trusted booking_data."""
    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    pending = await _ts(TripStore.get_pending_booking_data, trip_id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data to accept")

    # Re-validate through Pydantic (defensive)
    validated = BookingDataModel(**pending)
    bd_dict = validated.model_dump()

    # Promote to trusted booking_data
    await _ts(TripStore.update_trip, trip_id, {
        "booking_data": bd_dict,
        "pending_booking_data": None,
        "booking_data_source": "customer_accepted",
    })

    # Readiness recompute
    from intake.readiness import compute_readiness
    from intake.packet_models import CanonicalPacket
    refreshed_trip = await _ts(TripStore.get_trip, trip_id)
    packet = CanonicalPacket(packet_id=trip_id)
    packet.facts.update((refreshed_trip.get("extracted") or {}).get("facts", {}))
    readiness = compute_readiness(
        packet,
        validation=refreshed_trip.get("validation"),
        decision=refreshed_trip.get("decision"),
        traveler_bundle=refreshed_trip.get("traveler_bundle"),
        internal_bundle=refreshed_trip.get("internal_bundle"),
        safety=refreshed_trip.get("safety"),
        fees=refreshed_trip.get("fees"),
        booking_data=bd_dict,
    )
    validation = dict(refreshed_trip.get("validation") or {})
    validation["readiness"] = readiness.to_dict()
    updated = await _ts(TripStore.update_trip, trip_id, {"validation": validation})

    AuditStore.log_event("booking_data_accepted_from_customer", agency.id, {
        "trip_id": trip_id,
        "traveler_count": len(validated.travelers),
        "has_payer": validated.payer is not None,
        "has_passport_data": any(t.passport_number for t in validated.travelers),
        "reason": request.reason,
    })

    booking_data = await _ts(TripStore.get_booking_data, trip_id)
    return _booking_data_envelope(updated, booking_data)


@app.post("/trips/{trip_id}/pending-booking-data/reject")
async def reject_pending_booking_data(trip_id: str, request: ReviewActionRequest = ReviewActionRequest(), agency: Agency = Depends(get_current_agency)):
    """Reject pending customer submission. Clears pending data."""
    trip = await _ts(TripStore.get_trip, trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")

    pending = await _ts(TripStore.get_pending_booking_data, trip_id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data to reject")

    await _ts(TripStore.update_trip, trip_id, {"pending_booking_data": None})

    AuditStore.log_event("booking_data_rejected_from_customer", agency.id, {
        "trip_id": trip_id,
        "reason": request.reason,
    })

    return {"ok": True, "message": "Pending booking data rejected"}


# ---------------------------------------------------------------------------
# Public customer endpoints (no auth)
# ---------------------------------------------------------------------------

@app.get("/api/public/booking-collection/{token}", response_model=PublicCollectionContext)
@limiter.limit("20/minute")
async def get_public_collection_form(request: Request, response: Response, token: str):
    """Customer loads form context. No auth required. Shows safe trip summary only."""
    from spine_api.services.collection_service import validate_token
    from spine_api.core.database import async_session_maker

    async with async_session_maker() as db:
        record = await validate_token(db, token)
    if not record:
        return PublicCollectionContext(valid=False, reason="invalid")

    trip = await _ts(TripStore.get_trip, record.trip_id)
    if not trip:
        return PublicCollectionContext(valid=False, reason="invalid")

    # Build safe summary — NO PII, NO internal fields
    extracted = trip.get("extracted") or {}
    facts = extracted.get("facts", {}) if isinstance(extracted, dict) else {}

    dest = facts.get("destination_candidates")
    dest_val = getattr(dest, "value", dest) if dest else None
    date_win = facts.get("date_window")
    date_val = getattr(date_win, "value", date_win) if date_win else None

    pending = await _ts(TripStore.get_pending_booking_data, record.trip_id)

    return PublicCollectionContext(
        valid=True,
        trip_summary={
            "destination": dest_val,
            "date_window": date_val,
            "traveler_count": trip.get("party_composition"),
            "agency_name": "Waypoint Travel",
        },
        already_submitted=pending is not None,
        expires_at=record.expires_at.isoformat(),
    )


@app.post("/api/public/booking-collection/{token}/submit", response_model=PublicSubmissionResponse)
@limiter.limit("5/minute")
async def submit_public_booking_data(request: Request, response: Response, token: str, booking_data: BookingDataModel):
    """Customer submits booking data. No auth. Writes to pending_booking_data."""
    from spine_api.services.collection_service import validate_token, mark_token_used
    from spine_api.core.database import async_session_maker

    async with async_session_maker() as db:
        record = await validate_token(db, token)
    if not record:
        raise HTTPException(status_code=410, detail="invalid")

    # Check not already submitted
    pending = await _ts(TripStore.get_pending_booking_data, record.trip_id)
    if pending:
        raise HTTPException(status_code=409, detail="already_submitted")

    # Validate via Pydantic (already done by model binding, but explicit)
    bd_dict = booking_data.model_dump()

    # Write to pending_booking_data (encrypted)
    await _ts(TripStore.update_trip, record.trip_id, {"pending_booking_data": bd_dict})

    # Mark token as used
    customer_ip = request.client.host if request.client else None

    async with async_session_maker() as db:
        await mark_token_used(db, record.id, customer_ip)

    AuditStore.log_event("customer_booking_data_submitted", record.agency_id, {
        "trip_id": record.trip_id,
        "token_id": record.id,
        "traveler_count": len(booking_data.travelers),
        "has_payer": booking_data.payer is not None,
        "has_passport_data": any(t.passport_number for t in booking_data.travelers),
    })

    return PublicSubmissionResponse(
        ok=True,
        message="Your booking details have been submitted. The travel agent will review them shortly.",
    )


@app.post("/trips/{trip_id}/assign")
def assign_trip(
    trip_id: str,
    agent_id: str,
    agent_name: str,
    assigned_by: str = "system",
    agency: Agency = Depends(get_current_agency),
):
    """Assign a trip to an agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, assigned_by)
    
    # Update trip status
    TripStore.update_trip(trip_id, {"status": "assigned"})
    
    return {"success": True, "trip_id": trip_id, "assigned_to": agent_id}


@app.post("/trips/{trip_id}/unassign")
def unassign_trip(
    trip_id: str,
    unassigned_by: str = "system",
    agency: Agency = Depends(get_current_agency),
):
    """Remove assignment from a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    AssignmentStore.unassign_trip(trip_id, unassigned_by)
    
    return {"success": True, "trip_id": trip_id}


@app.post("/trips/{trip_id}/snooze")
def snooze_trip(
    trip_id: str,
    request: SnoozeRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Snooze a trip until a specified time."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
def acknowledge_suitability_flags(
    trip_id: str,
    request: SuitabilityAcknowledgeRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Acknowledge suitability flags for a trip, allowing it to proceed."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
def list_assignments(
    agent_id: Optional[str] = None,
    agency: Agency = Depends(get_current_agency),
):
    """List assignments for trips in the current agency."""
    # Get all trips for this agency first
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}
    
    if agent_id:
        assignments = AssignmentStore.get_trips_for_agent(agent_id)
    else:
        assignments = list(AssignmentStore._load_assignments().values())
    
    # Filter to only assignments for trips in this agency
    filtered = [a for a in assignments if a.get("trip_id") in agency_trip_ids]
    
    return {"items": filtered, "total": len(filtered)}


@app.get("/audit")
def get_audit_events(
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """Get recent audit events for the current agency."""
    events = AuditStore.get_events(limit=limit)
    # Get agency trip IDs to filter events
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}
    
    # Filter events to only those related to this agency's trips
    filtered = [
        e for e in events
        if e.get("details", {}).get("trip_id") in agency_trip_ids
        or e.get("details", {}).get("agency_id") == agency.id
    ]
    return {"items": filtered, "total": len(filtered)}


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
def get_analytics_summary(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=10000, agency_id=agency.id)
    canonical_trips = [t for t in trips if t.get("id")]
    return aggregate_insights(canonical_trips)


@app.get("/analytics/pipeline", response_model=List[StageMetrics])
def get_analytics_pipeline(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=10000, agency_id=agency.id)
    canonical_trips = [t for t in trips if t.get("id")]
    return compute_pipeline_metrics(canonical_trips)


@app.get("/analytics/team", response_model=List[TeamMemberMetrics])
async def get_analytics_team(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    members = await membership_service.list_members(db, agency_id=agency.id)
    return compute_team_metrics(trips, members)


@app.get("/analytics/bottlenecks", response_model=List[BottleneckAnalysis])
def get_analytics_bottlenecks(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_bottlenecks(trips)


@app.get("/analytics/revenue", response_model=RevenueMetrics)
def get_analytics_revenue(
    range: str = "30d",
    agency: Agency = Depends(get_current_agency),
):
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_revenue_metrics(trips)


@app.get("/analytics/agent/{agent_id}/drill-down")
def get_agent_drill_down(
    agent_id: str,
    metric: str = "conversion",
    agency: Agency = Depends(get_current_agency),
):
    """Return trips and metrics for a specific agent."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
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
def get_analytics_alerts(agency: Agency = Depends(get_current_agency)):
    """List pending operational alerts (Wave 10)."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    return compute_alerts(trips)


@app.post("/analytics/alerts/{alert_id}/dismiss")
def post_dismiss_alert(alert_id: str, agency: Agency = Depends(get_current_agency)):
    """Dismiss an operational alert by flagging the source trip."""
    # Alert ID format is alert_{trip_id}
    trip_id = alert_id.replace("alert_", "")
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
def get_pending_reviews(agency: Agency = Depends(get_current_agency)):
    """List all trips currently flagged for owner review."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    # Filter for trips requiring review (per engine.py / review.py logic)
    pending = [
        trip_to_review(t) 
        for t in trips 
        if t.get("analytics", {}).get("requires_review") is True
    ]
    return {"items": pending, "total": len(pending)}


@app.post("/trips/{trip_id}/review/action")
def post_review_action(
    trip_id: str,
    request: ReviewActionRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Apply a review action (approve/reject/request_changes/escalate) to a trip."""
    try:
        updated_trip = process_review_action(
            trip_id=trip_id,
            action=request.action,
            notes=request.notes,
            user_id=user.id,
            reassign_to=request.reassign_to,
            error_category=request.error_category,
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
                if mapped_event.actor is not None:
                    event_dict["actor"] = mapped_event.actor
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
                actor = audit_event.get("user_id")
                if actor is not None:
                    event_dict["actor"] = actor
                
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


# Activity Provenance Endpoint
@app.get("/trips/{trip_id}/activities/provenance")
def get_activities_provenance(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Retrieve activity provenance for a trip.
    
    Returns all activities with their source (suggested by AI or requested by traveler)
    and confidence scores for suggested activities.
    
    Response format:
    {
        "trip_id": "trip_xyz",
        "activities": [
            {"name": "Hiking", "source": "suggested", "confidence": 95},
            {"name": "Dining", "source": "requested", "confidence": null}
        ]
    }
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")
    
    # Extract activity provenance from trip
    # Currently using activity_provenance field which stores comma-separated activities
    # In Phase 6, we enhance this to track source and confidence
    activities = []
    
    activity_provenance = trip.get("activity_provenance", "")
    if activity_provenance:
        # Parse comma-separated activities
        activity_names = [a.strip() for a in activity_provenance.split(",")]
        
        # For now, assume all activities from activity_provenance are suggested by AI
        # This can be enhanced in future phases to track actual source in database
        for activity_name in activity_names:
            if activity_name:
                activities.append({
                    "name": activity_name,
                    "source": "suggested",
                    "confidence": 85,  # Default confidence for suggested activities
                })
    
    return {
        "trip_id": trip_id,
        "activities": activities,
    }


# =============================================================================
# Override API endpoints
# =============================================================================

@app.post("/trips/{trip_id}/override", response_model=OverrideResponse)
def create_override(
    trip_id: str,
    request: OverrideRequest,
    agency: Agency = Depends(get_current_agency),
) -> OverrideResponse:
    """
    Record an operator override of a risk flag for a trip.
    
    Validation:
    - If action="downgrade", new_severity must be provided and < original_severity
    - reason field is mandatory and must be non-empty
    - original_severity must match actual flag severity or reject with 409 Conflict
    
    Returns updated state and audit event ID.
    """
    # Validate trip exists and belongs to agency
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
def list_overrides(trip_id: str, agency: Agency = Depends(get_current_agency)) -> dict:
    """List all overrides for a trip."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
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
async def get_unified_state(agency: Agency = Depends(get_current_agency)):
    """
    Return unified state. Scoped to the current user's agency.
    """
    try:
        return DashboardAggregator.get_unified_state(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to aggregate unified state: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal integrity error"
        )


@app.get("/api/system/integrity/issues", response_model=IntegrityIssuesResponse)
async def get_integrity_issues(agency: Agency = Depends(get_current_agency)):
    """
    Return typed integrity issues. Scoped to the current user's agency.
    """
    try:
        return IntegrityService.list_integrity_issues(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to aggregate integrity issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal integrity error",
        )


@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(agency: Agency = Depends(get_current_agency)):
    """
    Dashboard stat cards — computed entirely by the backend aggregator.
    Scopes all metrics to the current user's agency.
    """
    try:
        return DashboardAggregator.get_dashboard_stats(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to compute dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to compute dashboard stats"
        )

# =============================================================================
# Team Management API
# =============================================================================

@app.get("/api/team/members", response_model=dict)
async def list_team_members(
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """List all team members for the current agency."""
    members = await membership_service.list_members(db, agency_id=agency.id)
    return {"items": members, "total": len(members)}


@app.get("/api/team/members/{member_id}")
async def get_team_member(
    member_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single team member by membership ID."""
    member = await membership_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@app.post("/api/team/invite")
async def invite_team_member(
    request: InviteTeamMemberRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a new team member (creates User + Membership)."""
    try:
        member = await membership_service.invite_member(
            db=db,
            agency_id=agency.id,
            email=request.email,
            name=request.name,
            role=request.role,
            capacity=request.capacity,
            specializations=request.specializations,
            invited_by=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"success": True, "member": member}


@app.patch("/api/team/members/{member_id}")
async def update_team_member(
    member_id: str,
    request: InviteTeamMemberRequest,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """Update a team member's role, capacity, or specializations."""
    updates = request.model_dump(exclude_none=True, include={"role", "capacity", "specializations"})
    member = await membership_service.update_member(db, member_id, agency.id, updates)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")
    return member


@app.delete("/api/team/members/{member_id}")
async def deactivate_team_member(
    member_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a team member."""
    success = await membership_service.deactivate_member(db, member_id, agency.id)
    if not success:
        raise HTTPException(status_code=404, detail="Team member not found")
    return {"success": True}


@app.get("/api/team/workload")
async def get_workload_distribution(
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_db),
):
    """Get workload distribution across active team members."""
    members = await membership_service.list_members(db, agency_id=agency.id, active_only=True)
    assignments = AssignmentStore._load_assignments()
    
    # Get agency trip IDs to filter assignments
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}
    
    distribution = []
    for member in members:
        member_id = member["id"]
        assigned_trips = [
            a for a in assignments.values()
            if a.get("agent_id") == member_id and a.get("trip_id") in agency_trip_ids
        ]
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
def get_review(review_id: str, agency: Agency = Depends(get_current_agency)):
    """Get a single review by trip ID."""
    trip = TripStore.get_trip(review_id)
    if not trip or trip.get("agency_id") != agency.id:
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
def get_escalation_heatmap(agency: Agency = Depends(get_current_agency)):
    """Return escalation heatmap data."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    
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
def get_conversion_funnel(agency: Agency = Depends(get_current_agency)):
    """Return conversion funnel metrics."""
    trips = TripStore.list_trips(limit=1000, agency_id=agency.id)
    
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
def reassign_trip(
    trip_id: str,
    agent_id: str,
    agent_name: str,
    reassigned_by: str = "owner",
    agency: Agency = Depends(get_current_agency),
):
    """Reassign a trip to a different agent."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Unassign first if already assigned
    existing = AssignmentStore.get_assignment(trip_id)
    if existing:
        AssignmentStore.unassign_trip(trip_id, reassigned_by)
    
    AssignmentStore.assign_trip(trip_id, agent_id, agent_name, reassigned_by)
    TripStore.update_trip(trip_id, {"status": "assigned"})
    
    return {"success": True, "trip_id": trip_id, "reassigned_to": agent_id}


@app.post("/inbox/bulk")
def bulk_inbox_action(
    request: dict,
    agency: Agency = Depends(get_current_agency),
):
    """Apply bulk actions to inbox items."""
    action = request.get("action")
    trip_ids = request.get("trip_ids", [])
    
    # Verify all trips belong to this agency
    agency_trips = TripStore.list_trips(agency_id=agency.id, limit=10000)
    agency_trip_ids = {t["id"] for t in agency_trips if t.get("id")}
    trip_ids = [tid for tid in trip_ids if tid in agency_trip_ids]
    
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
# Follow-up Workflow & Reminders (Phase 5)
# =============================================================================

@app.get("/followups/dashboard")
def get_followups_dashboard(
    status: Optional[str] = None,
    filter: Optional[str] = None,
    agency: Agency = Depends(get_current_agency),
):
    """
    Get all trips with follow-up reminders.
    
    Query params:
    - status: pending|completed|snoozed
    - filter: due_today|overdue|upcoming
    
    Returns: List of trips with follow-up info sorted by due date
    """
    from pathlib import Path
    
    trips_dir = Path(__file__).parent.parent / "data" / "trips"
    followups = []
    
    if trips_dir.exists():
        for trip_file in trips_dir.glob("*.json"):
            try:
                with open(trip_file, "r") as f:
                    trip = json.load(f)
                
                # Only include trips for this agency
                if trip.get("agency_id") != agency.id:
                    continue
                
                # Only include trips with follow_up_due_date
                due_date_str = trip.get("follow_up_due_date")
                if not due_date_str:
                    continue
                
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue
                
                # Extract follow-up status
                follow_up_status = trip.get("follow_up_status", "pending")
                trip_status = trip.get("status", "new")
                
                # Filter by status if provided
                if status and follow_up_status != status:
                    continue
                
                # Apply filter if provided
                now = datetime.now(timezone.utc)
                if filter == "due_today":
                    if due_date.date() != now.date():
                        continue
                elif filter == "overdue":
                    if due_date > now:
                        continue
                elif filter == "upcoming":
                    if due_date <= now:
                        continue
                
                followups.append({
                    "trip_id": trip.get("id"),
                    "traveler_name": trip.get("traveler_name", "Unknown"),
                    "agent_name": trip.get("agent_name", "Unassigned"),
                    "due_date": due_date_str,
                    "status": follow_up_status,
                    "trip_status": trip_status,
                    "days_until_due": (due_date.date() - now.date()).days,
                })
            except (json.JSONDecodeError, IOError):
                continue
    
    # Sort by due_date ascending
    followups.sort(key=lambda x: x["due_date"])
    
    return {
        "items": followups,
        "total": len(followups),
    }


@app.patch("/followups/{trip_id}/mark-complete")
def mark_followup_complete(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Mark a follow-up as completed."""
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")
    
    updated = TripStore.update_trip(trip_id, {
        "follow_up_status": "completed",
        "follow_up_completed_at": datetime.now(timezone.utc).isoformat(),
    })
    
    AuditStore.log_event("followup_completed", "operator", {
        "trip_id": trip_id,
        "due_date": trip.get("follow_up_due_date"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    
    return updated


@app.patch("/followups/{trip_id}/snooze")
def snooze_followup(
    trip_id: str,
    days: int = 1,
    agency: Agency = Depends(get_current_agency),
):
    """
    Snooze a follow-up reminder.
    
    Query params:
    - days: 1, 3, or 7 (default: 1)
    """
    from datetime import timedelta
    
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")
    
    # Validate days parameter
    if days not in [1, 3, 7]:
        raise HTTPException(status_code=400, detail="days must be 1, 3, or 7")
    
    # Parse current due_date and add days
    try:
        current_due = datetime.fromisoformat(
            trip.get("follow_up_due_date", "").replace('Z', '+00:00')
        )
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid follow_up_due_date format")
    
    new_due_date = (current_due + timedelta(days=days)).isoformat()
    
    updated = TripStore.update_trip(trip_id, {
        "follow_up_due_date": new_due_date,
        "follow_up_status": "snoozed",
    })
    
    AuditStore.log_event("followup_snoozed", "operator", {
        "trip_id": trip_id,
        "original_due_date": trip.get("follow_up_due_date"),
        "new_due_date": new_due_date,
        "snooze_days": days,
    })
    
    return updated


@app.patch("/followups/{trip_id}/reschedule")
def reschedule_followup(
    trip_id: str,
    new_date: str,
    agency: Agency = Depends(get_current_agency),
):
    """
    Reschedule a follow-up to a new date.
    
    Body: {"new_date": "2026-05-15T14:00:00Z"}
    """
    trip = TripStore.get_trip(trip_id)
    if not trip or trip.get("agency_id") != agency.id:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.get("follow_up_due_date"):
        raise HTTPException(status_code=400, detail="Trip has no follow-up scheduled")
    
    # Validate new_date format
    try:
        datetime.fromisoformat(new_date.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO-8601")
    
    updated = TripStore.update_trip(trip_id, {
        "follow_up_due_date": new_date,
        "follow_up_status": "pending",
    })
    
    AuditStore.log_event("followup_rescheduled", "operator", {
        "trip_id": trip_id,
        "old_due_date": trip.get("follow_up_due_date"),
        "new_due_date": new_date,
    })
    
    return updated


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
