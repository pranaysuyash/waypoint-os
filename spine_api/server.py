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
from typing import Any, Dict, List, Literal, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root to Python path so we can import from src
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, UploadFile, Form, File
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

# --- OpenTelemetry instrumentation ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource

def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except ValueError:
        return default


# Backend uses OTLP gRPC exporter. Keep an explicit backend endpoint variable to
# avoid frontend/backend format conflicts (frontend needs OTLP HTTP URL).
otel_endpoint = (
    os.environ.get("SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT")
    or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
)
otel_service_name = os.environ.get("OTEL_SERVICE_NAME", "spine_api")
if otel_endpoint:
    try:
        resource = Resource.create({"service.name": otel_service_name})
        provider = TracerProvider(resource=resource)
        otel_export_timeout_ms = _int_env("SPINE_OTEL_BSP_EXPORT_TIMEOUT_MS", 3000)
        otel_schedule_delay_ms = _int_env("SPINE_OTEL_BSP_SCHEDULE_DELAY_MS", 1500)
        otel_max_queue_size = _int_env("SPINE_OTEL_BSP_MAX_QUEUE_SIZE", 512)
        otel_max_export_batch_size = _int_env("SPINE_OTEL_BSP_MAX_EXPORT_BATCH_SIZE", 128)
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=otel_endpoint, timeout=otel_export_timeout_ms / 1000.0),
                schedule_delay_millis=otel_schedule_delay_ms,
                max_queue_size=otel_max_queue_size,
                max_export_batch_size=otel_max_export_batch_size,
                export_timeout_millis=otel_export_timeout_ms,
            )
        )
        trace.set_tracer_provider(provider)
    except Exception as e:
        import logging
        logging.getLogger("spine_api.otel").warning(f"OTel init failed (non-fatal): {e}")
# --- End OTel ---

from spine_api.core.env import load_project_env

load_project_env()

from spine_api.core.auth import get_current_user, get_current_agency_id, get_current_agency, _auth_or_skip, require_permission
from spine_api.core.database import engine, get_db
from spine_api.core.rls import inspect_rls_runtime_posture, get_rls_db, rls_session
from spine_api.models.tenant import Agency, User
from spine_api.core.logging_filter import install_sensitive_data_filter
from spine_api.core.middleware import AuthMiddleware, PUBLIC_CHECKER_MAX_BYTES, RequestBodySizeMiddleware
from spine_api.core.rate_limiter import limiter, RateLimitExceededHandler, SlowAPIMiddleware
from spine_api.version import APP_VERSION
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
    TimelineEvent,
    TimelineResponse,
    ReviewActionRequest,
    SuitabilityAcknowledgeRequest,
    SnoozeRequest,
    InviteTeamMemberRequest,
    TeamMember,
    ExplicitReassessRequest,
    IntegrityIssuesResponse,
    UnifiedStateResponse,
    DashboardStatsResponse,
    SuitabilityFlagsResponse,
)
from spine_api.services.live_checker_service import (
    apply_live_checker_adjustments,
    build_consented_submission,
    collect_raw_text_sources,
)
from spine_api.services.public_checker_service import run_public_checker_submission
from spine_api.services.pipeline_execution_service import execute_spine_pipeline
from spine_api.services import trip_lifecycle_service
from spine_api.product_b_events import ProductBEventStore  # noqa: F401  # Legacy re-export for tests/compatibility

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.safety import set_strict_mode
from src.public_checker.live_checks import build_live_checker_signals

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
save_processed_trip = persistence.save_processed_trip
save_processed_trip_async = persistence.save_processed_trip_async

DEFAULT_PUBLIC_CHECKER_AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"


def _get_public_checker_agency_id() -> str:
    """Resolve public-checker agency id from environment with strict normalization."""
    agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
    return str(agency_id or "").strip()


def _is_sql_tripstore_backend() -> bool:
    return _get_tripstore_backend() == "sql"


def _validate_tripstore_backend_configuration() -> None:
    """Fail fast on invalid TripStore backend configuration before serving traffic."""
    backend = _get_tripstore_backend()
    if backend not in {"file", "sql"}:
        raise RuntimeError(
            "Invalid TRIPSTORE_BACKEND after normalization. Allowed values are file, json, or sql."
        )

    if backend == "sql":
        logger.info("TripStore configured for SQL persistence")
    else:
        logger.info("TripStore configured for file persistence")


def _get_tripstore_backend() -> str:
    """Resolve and validate TRIPSTORE_BACKEND with explicit environment safety checks."""
    raw_backend = os.getenv("TRIPSTORE_BACKEND", "").strip().lower()
    if not raw_backend:
        environment = os.getenv("ENVIRONMENT", os.getenv("NODE_ENV", "development")).lower().strip()
        if environment in {"production", "staging"}:
            raise RuntimeError(
                "TRIPSTORE_BACKEND must be set explicitly in production/staging. "
                "Current ENVIRONMENT is set to production/staging, and no value was provided."
            )
        logger.warning("TRIPSTORE_BACKEND is unset; defaulting to file store")
        return "file"

    backend = raw_backend
    if backend == "json":
        backend = "file"
    if backend not in {"file", "sql"}:
        raise RuntimeError(
            f"Unknown TRIPSTORE_BACKEND='{backend}'. Allowed values: file, json, sql."
        )
    return backend


def _get_startup_db_timeout(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value or default


async def _apply_startup_db_timeouts(conn) -> None:
    """
    Bound startup compatibility queries so stale transactions cannot keep the API offline indefinitely.

    The settings are transaction-local via PostgreSQL set_config(..., true), so
    they apply only to the current startup guard transaction and never leak into
    normal request handling.
    """
    await conn.execute(
        text("""
            SELECT
              set_config('lock_timeout', :lock_timeout, true),
              set_config('statement_timeout', :statement_timeout, true)
        """),
        {
            "lock_timeout": _get_startup_db_timeout("SPINE_API_STARTUP_LOCK_TIMEOUT", "5s"),
            "statement_timeout": _get_startup_db_timeout("SPINE_API_STARTUP_STATEMENT_TIMEOUT", "20s"),
        },
    )

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
)
from spine_api.run_ledger import RunLedger
from spine_api.draft_store import DraftStore
from src.intake.config.agency_settings import AgencySettingsStore
from src.analytics.policy_rules import ready_gate_failures
from src.agents.recovery_agent import RecoveryAgent
from src.agents.runtime import AgentSupervisor, build_default_registry
from spine_api.services.agent_work_coordinator import SQLWorkCoordinator


class _TripStoreAdapter:
    """Thin adapter so backend agents can query TripStore through a stable boundary."""

    def list_active(self) -> list:
        """Return trips that are in processing stages (not closed/cancelled)."""
        trips_raw = self._resolve_sync(TripStore.list_trips(limit=500))
        terminal = {"closed", "cancelled", "completed", "archived"}
        return [t for t in trips_raw if (t.get("stage") or t.get("state") or t.get("status")) not in terminal]

    def set_review_status(self, trip_id: str, status: str) -> None:
        self._resolve_sync(TripStore.update_trip(trip_id, {"review_status": status}))

    def update_trip(self, trip_id: str, updates: dict) -> Optional[dict]:
        return self._resolve_sync(TripStore.update_trip(trip_id, updates))

    def _resolve_sync(self, value):
        if asyncio.iscoroutine(value):
            return persistence._run_async_blocking(value)
        return value


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
_agent_work_coordinator = (
    SQLWorkCoordinator(lease_seconds=int(os.environ.get("AGENT_WORK_LEASE_SECONDS", "60")))
    if os.environ.get("AGENT_WORK_COORDINATOR", "").lower() == "sql" or os.environ.get("TRIPSTORE_BACKEND", "").lower() == "sql"
    else None
)
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
    coordinator=_agent_work_coordinator,
)

# Auth — Phase 1
try:
    from spine_api.routers import auth as auth_router
    from spine_api.routers import workspace as workspace_router
    from spine_api.routers import frontier as frontier_router
    from spine_api.routers import audit as audit_router
    from spine_api.routers import assignments as assignments_router
    from spine_api.routers import run_status as run_status_router
    from spine_api.routers import health as health_router
    from spine_api.routers import system_dashboard as system_dashboard_router
    from spine_api.routers import followups as followups_router
    from spine_api.routers import team as team_router
    from spine_api.routers import settings as settings_router
    from spine_api.routers import drafts as drafts_router
    from spine_api.routers import inbox as inbox_router
    from spine_api.routers import agent_runtime as agent_runtime_router
    from spine_api.routers import analytics as analytics_router
    from spine_api.routers import product_b_analytics as product_b_analytics_router
    from spine_api.routers import booking_tasks as booking_tasks_router
    from spine_api.routers import confirmations as confirmations_router
    from spine_api.routers import public_checker as public_checker_router
    from spine_api.routers import public_collection as public_collection_router
    from spine_api.routers import legacy_ops as legacy_ops_router
    from spine_api.routers import trip_actions as trip_actions_router
    from spine_api.routers import trip_observability as trip_observability_router
    from spine_api.routers import trip_lifecycle as trip_lifecycle_router
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

    _run_status_spec = importlib.util.spec_from_file_location("routers.run_status", _base / "routers" / "run_status.py")
    _run_status_mod = importlib.util.module_from_spec(_run_status_spec)
    _run_status_spec.loader.exec_module(_run_status_mod)
    run_status_router = _run_status_mod

    _health_spec = importlib.util.spec_from_file_location("routers.health", _base / "routers" / "health.py")
    _health_mod = importlib.util.module_from_spec(_health_spec)
    _health_spec.loader.exec_module(_health_mod)
    health_router = _health_mod

    _system_dashboard_spec = importlib.util.spec_from_file_location("routers.system_dashboard", _base / "routers" / "system_dashboard.py")
    _system_dashboard_mod = importlib.util.module_from_spec(_system_dashboard_spec)
    _system_dashboard_spec.loader.exec_module(_system_dashboard_mod)
    system_dashboard_router = _system_dashboard_mod

    _followups_spec = importlib.util.spec_from_file_location("routers.followups", _base / "routers" / "followups.py")
    _followups_mod = importlib.util.module_from_spec(_followups_spec)
    _followups_spec.loader.exec_module(_followups_mod)
    followups_router = _followups_mod

    _team_spec = importlib.util.spec_from_file_location("routers.team", _base / "routers" / "team.py")
    _team_mod = importlib.util.module_from_spec(_team_spec)
    _team_spec.loader.exec_module(_team_mod)
    team_router = _team_mod

    _settings_spec = importlib.util.spec_from_file_location("routers.settings", _base / "routers" / "settings.py")
    _settings_mod = importlib.util.module_from_spec(_settings_spec)
    _settings_spec.loader.exec_module(_settings_mod)
    settings_router = _settings_mod

    _drafts_spec = importlib.util.spec_from_file_location("routers.drafts", _base / "routers" / "drafts.py")
    _drafts_mod = importlib.util.module_from_spec(_drafts_spec)
    _drafts_spec.loader.exec_module(_drafts_mod)
    drafts_router = _drafts_mod

    _inbox_spec = importlib.util.spec_from_file_location("routers.inbox", _base / "routers" / "inbox.py")
    _inbox_mod = importlib.util.module_from_spec(_inbox_spec)
    _inbox_spec.loader.exec_module(_inbox_mod)
    inbox_router = _inbox_mod

    _agent_runtime_spec = importlib.util.spec_from_file_location("routers.agent_runtime", _base / "routers" / "agent_runtime.py")
    _agent_runtime_mod = importlib.util.module_from_spec(_agent_runtime_spec)
    _agent_runtime_spec.loader.exec_module(_agent_runtime_mod)
    agent_runtime_router = _agent_runtime_mod

    _analytics_spec = importlib.util.spec_from_file_location("routers.analytics", _base / "routers" / "analytics.py")
    _analytics_mod = importlib.util.module_from_spec(_analytics_spec)
    _analytics_spec.loader.exec_module(_analytics_mod)
    analytics_router = _analytics_mod

    _product_b_analytics_spec = importlib.util.spec_from_file_location("routers.product_b_analytics", _base / "routers" / "product_b_analytics.py")
    _product_b_analytics_mod = importlib.util.module_from_spec(_product_b_analytics_spec)
    _product_b_analytics_spec.loader.exec_module(_product_b_analytics_mod)
    product_b_analytics_router = _product_b_analytics_mod

    _booking_tasks_spec = importlib.util.spec_from_file_location("routers.booking_tasks", _base / "routers" / "booking_tasks.py")
    _booking_tasks_mod = importlib.util.module_from_spec(_booking_tasks_spec)
    _booking_tasks_spec.loader.exec_module(_booking_tasks_mod)
    booking_tasks_router = _booking_tasks_mod

    _confirmations_spec = importlib.util.spec_from_file_location("routers.confirmations", _base / "routers" / "confirmations.py")
    _confirmations_mod = importlib.util.module_from_spec(_confirmations_spec)
    _confirmations_spec.loader.exec_module(_confirmations_mod)
    confirmations_router = _confirmations_mod

    _public_checker_spec = importlib.util.spec_from_file_location("routers.public_checker", _base / "routers" / "public_checker.py")
    _public_checker_mod = importlib.util.module_from_spec(_public_checker_spec)
    _public_checker_spec.loader.exec_module(_public_checker_mod)
    public_checker_router = _public_checker_mod

    _public_collection_spec = importlib.util.spec_from_file_location(
        "routers.public_collection",
        _base / "routers" / "public_collection.py",
    )
    _public_collection_mod = importlib.util.module_from_spec(_public_collection_spec)
    _public_collection_spec.loader.exec_module(_public_collection_mod)
    public_collection_router = _public_collection_mod

    _legacy_ops_spec = importlib.util.spec_from_file_location(
        "routers.legacy_ops",
        _base / "routers" / "legacy_ops.py",
    )
    _legacy_ops_mod = importlib.util.module_from_spec(_legacy_ops_spec)
    _legacy_ops_spec.loader.exec_module(_legacy_ops_mod)
    legacy_ops_router = _legacy_ops_mod

    _trip_actions_spec = importlib.util.spec_from_file_location(
        "routers.trip_actions",
        _base / "routers" / "trip_actions.py",
    )
    _trip_actions_mod = importlib.util.module_from_spec(_trip_actions_spec)
    _trip_actions_spec.loader.exec_module(_trip_actions_mod)
    trip_actions_router = _trip_actions_mod

    _trip_observability_spec = importlib.util.spec_from_file_location(
        "routers.trip_observability",
        _base / "routers" / "trip_observability.py",
    )
    _trip_observability_mod = importlib.util.module_from_spec(_trip_observability_spec)
    _trip_observability_spec.loader.exec_module(_trip_observability_mod)
    trip_observability_router = _trip_observability_mod

    _trip_lifecycle_spec = importlib.util.spec_from_file_location(
        "routers.trip_lifecycle",
        _base / "routers" / "trip_lifecycle.py",
    )
    _trip_lifecycle_mod = importlib.util.module_from_spec(_trip_lifecycle_spec)
    _trip_lifecycle_spec.loader.exec_module(_trip_lifecycle_mod)
    trip_lifecycle_router = _trip_lifecycle_mod


def _register_router_module_aliases() -> None:
    """Keep legacy `routers.*` imports pointed at canonical router modules."""
    routers_pkg = sys.modules.get("spine_api.routers") or sys.modules.get("routers")
    if routers_pkg is not None:
        sys.modules["routers"] = routers_pkg

    modules = {
        "agent_runtime": agent_runtime_router,
        "analytics": analytics_router,
        "followups": followups_router,
        "inbox": inbox_router,
    }
    for name, module in modules.items():
        sys.modules[f"routers.{name}"] = module
        if routers_pkg is not None:
            setattr(routers_pkg, name, module)


_register_router_module_aliases()

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
            await _apply_startup_db_timeouts(conn)
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
            await _apply_startup_db_timeouts(conn)
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


async def _ensure_users_have_memberships() -> None:
    """
    Backfill default agencies + memberships for orphan users.

    When the membership table was added without a backfill for existing users,
    every user without a membership row became unable to log in. This guard
    ensures every existing user has at least one agency and membership.

    Idempotent: safe to run on every startup. Skips users that already
    have memberships.
    """
    try:
        async with engine.begin() as conn:
            await _apply_startup_db_timeouts(conn)
            # Guard: ensure both tables exist (fresh migrations or partial deploy)
            for table_name in ("users", "memberships", "agencies"):
                exists_result = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :table_name
                    )
                """), {"table_name": table_name})
                if not bool(exists_result.scalar()):
                    logger.warning(
                        "Users membership backfill skipped: '%s' table missing", table_name
                    )
                    return

            # Find all orphan users
            orphan_result = await conn.execute(text("""
                SELECT u.id, u.email, u.name
                FROM users u
                LEFT JOIN memberships m ON m.user_id = u.id
                WHERE m.id IS NULL
            """))
            orphan_rows = [dict(r) for r in orphan_result.mappings().fetchall()]
            if not orphan_rows:
                logger.info("Users membership backfill: all users have memberships")
                return

            logger.info(
                "Users membership backfill: %d orphan users found", len(orphan_rows)
            )

            for row in orphan_rows:
                user_id = row["id"]
                email = row["email"]
                name = row["name"]
                agency_name = f"{name or email}'s Agency"
                slug_base = agency_name.lower().replace("'s agency", "").replace(" ", "-")
                slug = f"{slug_base[:40]}-{uuid.uuid4().hex[:8]}"

                agency_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)

                # Insert agency
                await conn.execute(
                    text("""
                        INSERT INTO agencies (
                            id, name, slug, plan, settings, created_at, jurisdiction, is_test
                        ) VALUES (
                            :id, :name, :slug, :plan, CAST(:settings AS JSONB),
                            :created_at, :jurisdiction, :is_test
                        )
                    """),
                    {
                        "id": agency_id,
                        "name": agency_name,
                        "slug": slug,
                        "plan": "free",
                        "settings": "{}",
                        "created_at": now,
                        "jurisdiction": "other",
                        "is_test": False,
                    },
                )

                # Set RLS context so the membership insert passes tenant policy
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_id},
                )

                # Insert membership
                await conn.execute(
                    text("""
                        INSERT INTO memberships (
                            id, user_id, agency_id, role, is_primary, status, created_at
                        ) VALUES (
                            :id, :user_id, :agency_id, :role, :is_primary,
                            :status, :created_at
                        )
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "agency_id": agency_id,
                        "role": "owner",
                        "is_primary": True,
                        "status": "active",
                        "created_at": now,
                    },
                )

                logger.info(
                    "Backfilled agency + membership for user=%s email=%s agency=%s",
                    user_id, email, agency_id,
                )

            logger.info("Users membership backfill complete")
    except Exception as e:
        logger.error("Failed users membership backfill: %s", e)
        raise


async def _ensure_rls_no_force_on_auth_tables() -> None:
    """
    Remove FORCE ROW LEVEL SECURITY from auth-critical tables.

    The memberships and workspace_codes tables must be queryable during the
    login/auth flow without a prior `app.current_agency_id` context, because
    the auth layer needs to discover the user's workspace before it knows
    which agency to scope to.

    With FORCE RLS, the table owner is also subject to the policy, which
    means any SELECT on these tables returns zero rows until
    `app.current_agency_id` is set — a chicken-and-egg problem for login.

    Regular RLS (without FORCE) still protects against non-owner roles.
    This is a pragmatic concession: RLS hardening of the auth path is paused
    until the login flow can reliably bypass or set the agency context before
    querying these tables.

    Idempotent: ALTER TABLE ... NO FORCE ROW LEVEL SECURITY is a no-op if
    FORCE is not already set.
    """
    _AUTH_TABLES = ("memberships", "workspace_codes")
    for table in _AUTH_TABLES:
        try:
            async with engine.begin() as conn:
                await _apply_startup_db_timeouts(conn)
                exists = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :t
                    )
                """), {"t": table})
                if not bool(exists.scalar()):
                    continue
                await conn.execute(text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
                logger.info("Removed FORCE RLS from %s (auth tables)", table)
        except Exception as e:
            logger.error("Failed to remove FORCE RLS from %s: %s", table, e)


async def _deduplicate_memberships_and_agencies() -> None:
    """
    Clean up duplicate memberships and orphan agencies.

    Each time login() could not discover existing memberships (because FORCE
    RLS blocked the SELECT), it created a new agency + membership for the
    same user, producing N memberships per user and orphan agencies.

    Single-pass SQL: no per-user iteration.

    Rules:
    - Keep exactly one membership per user (is_primary first, else most recent).
    - Delete agencies that have zero memberships.
    - Preserve the public-checker agency (no memberships expected).

    Idempotent: safe to re-run.
    """
    try:
        async with engine.begin() as conn:
            await _apply_startup_db_timeouts(conn)

            # Step 1: Deduplicate memberships — keep one per user (primary wins, then most recent).
            del_result = await conn.execute(text("""
                WITH kept AS (
                    SELECT DISTINCT ON (user_id) id
                    FROM memberships
                    ORDER BY user_id, is_primary DESC, created_at DESC
                ),
                removed AS (
                    DELETE FROM memberships m
                    WHERE m.id NOT IN (SELECT id FROM kept)
                    RETURNING 1
                )
                SELECT COUNT(*) AS deleted FROM removed
            """))
            deleted = del_result.scalar() or 0
            if deleted:
                logger.info("Deduplicated %d duplicate memberships", deleted)
            else:
                logger.info("No duplicate memberships found")

            # Step 2: Delete orphan agencies (no associated memberships).
            del_agency = await conn.execute(text("""
                WITH removed AS (
                    DELETE FROM agencies a
                    WHERE NOT EXISTS (SELECT 1 FROM memberships m WHERE m.agency_id = a.id)
                      AND a.id != :checker_id
                    RETURNING 1
                )
                SELECT COUNT(*) AS deleted FROM removed
            """), {"checker_id": _get_public_checker_agency_id()})
            deleted_agencies = del_agency.scalar() or 0
            if deleted_agencies:
                logger.info("Deleted %d orphan agencies (no memberships)", deleted_agencies)

            logger.info("Membership and agency cleanup complete")
    except Exception as e:
        logger.error("Failed membership/agency cleanup: %s", e)


async def _validate_public_checker_agency_configuration() -> None:
    """
    Enforce public-checker agency invariants before serving traffic.

    In SQL mode, public-checker trips persist with a fixed agency_id. That id
    must be explicitly configured (or use default) and must exist in agencies.
    """
    agency_id = _get_public_checker_agency_id()
    if not agency_id:
        raise RuntimeError(
            "PUBLIC_CHECKER_AGENCY_ID resolved to empty string. "
            "Set PUBLIC_CHECKER_AGENCY_ID to a valid agencies.id."
        )

    if not _is_sql_tripstore_backend():
        logger.info(
            "Public checker agency validation skipped (TRIPSTORE_BACKEND!=sql). "
            "configured_agency_id=%s",
            agency_id,
        )
        return

    try:
        async with engine.begin() as conn:
            await _apply_startup_db_timeouts(conn)
            table_exists_result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'agencies'
                )
            """))
            agencies_table_exists = bool(table_exists_result.scalar())
            if not agencies_table_exists:
                raise RuntimeError(
                    "Public checker requires SQL agencies table, but 'agencies' does not exist. "
                    "Run migrations before starting in TRIPSTORE_BACKEND=sql mode."
                )

            agency_exists_result = await conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM agencies WHERE id = :agency_id)"),
                {"agency_id": agency_id},
            )
            agency_exists = bool(agency_exists_result.scalar())
            if not agency_exists:
                raise RuntimeError(
                    "Public checker agency invariant failed: configured agency_id "
                    f"'{agency_id}' (env PUBLIC_CHECKER_AGENCY_ID) is missing from agencies table. "
                    "Create/seed that agency or set PUBLIC_CHECKER_AGENCY_ID to an existing agencies.id."
                )

        logger.info("Public checker agency validation passed for agency_id=%s", agency_id)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed public checker agency validation: {exc}") from exc


def _is_strict_startup_environment() -> bool:
    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
    return env.strip().lower() in {"production", "staging"}


def _should_run_startup_mutations() -> bool:
    """Whether startup schema/data mutations are permitted.

    In production/staging, mutations are skipped by default unless
    explicitly opted in via SPINE_API_ENABLE_STARTUP_MUTATIONS.
    Migrations and maintenance commands are the canonical path.
    """
    if os.environ.get("SPINE_API_ENABLE_STARTUP_MUTATIONS", "").lower() in ("1", "true", "yes"):
        return True
    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
    return env.strip().lower() not in ("production", "staging")


async def _validate_rls_runtime_posture_configuration() -> None:
    """
    Enforce that production-like SQL startup cannot silently run with bypassable tenant RLS.

    Validates all 11 tables in RLS_TENANT_TABLES have RLS enabled and FORCE RLS.
    Local development keeps running with a warning because the current dev database
    uses the owner role for app access while the long-term fix moves runtime access
    to a distinct non-owner database role.
    """
    if not _is_sql_tripstore_backend():
        logger.info("RLS runtime posture validation skipped (TRIPSTORE_BACKEND!=sql)")
        return

    try:
        async with engine.begin() as conn:
            await _apply_startup_db_timeouts(conn)
            posture = await inspect_rls_runtime_posture(conn)
    except Exception as exc:
        raise RuntimeError(f"Failed RLS runtime posture validation: {exc}") from exc

    if posture.is_enforced_for_runtime_role:
        logger.info(
            "RLS runtime posture validation passed for current_user=%s",
            posture.current_user,
        )
        return

    risk_summary = "; ".join(posture.risks)
    message = (
        "RLS runtime posture invariant failed: "
        f"{risk_summary}. Use a non-owner application runtime DB role, or enable "
        "FORCE ROW LEVEL SECURITY only after every SQL trip read/write path sets "
        "app.current_agency_id transaction-locally."
    )
    if _is_strict_startup_environment():
        raise RuntimeError(message)

    logger.warning(
        "%s Local/development startup will continue, but tenant RLS is not an "
        "active defense-in-depth layer.",
        message,
    )


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
    _validate_tripstore_backend_configuration()

    if _should_run_startup_mutations():
        await _ensure_agencies_schema_compatibility()
        await _ensure_memberships_schema_compatibility()
        await _ensure_rls_no_force_on_auth_tables()
        await _deduplicate_memberships_and_agencies()
        await _ensure_users_have_memberships()
    else:
        logger.info(
            "Skipping startup schema/data mutations (ENVIRONMENT=%s). "
            "Set SPINE_API_ENABLE_STARTUP_MUTATIONS=1 to override.",
            env,
        )

    await _validate_public_checker_agency_configuration()
    await _validate_rls_runtime_posture_configuration()
    install_sensitive_data_filter()
    app.state.limiter = limiter
    watchdog.start()

    # Skip background agents during test runs so they don't create the
    # TripStore SQL bridge (agent_work_coordinator always uses
    # _run_async_blocking, bypassing TRIPSTORE_BACKEND=file), which can
    # leave the bridge's event loop in a broken state after teardown.
    if not os.environ.get("RUNNING_TESTS"):
        _recovery_agent.start()
        _agent_supervisor.start()
        _zombie_reaper_start()
    # Note: We no longer auto-seed at startup.
    # Seeding is now done per-agency for test users in the /trips endpoint.
    logger.info("Spine API startup complete")
    yield
    # Shutdown
    if not os.environ.get("RUNNING_TESTS"):
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
    version=APP_VERSION,
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
app.add_middleware(RequestBodySizeMiddleware)

app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, RateLimitExceededHandler.handler)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Phase 1: Auth + Workspace routers
# Auth enforcement: _auth_or_skip checks SPINE_API_DISABLE_AUTH at call time,
# so tests can toggle auth behavior without importlib.reload().
app.include_router(auth_router.router)
app.include_router(workspace_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(frontier_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(audit_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(assignments_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(run_status_router.router)
app.include_router(health_router.router)
app.include_router(system_dashboard_router.router)
app.include_router(followups_router.router)
app.include_router(team_router.router)
app.include_router(settings_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(drafts_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(inbox_router.router, dependencies=[Depends(_auth_or_skip)])
agent_runtime_router.configure_runtime(
    agent_supervisor=_agent_supervisor,
    recovery_agent=_recovery_agent,
)
app.include_router(agent_runtime_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(analytics_router.router)
app.include_router(product_b_analytics_router.router)
app.include_router(booking_tasks_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(confirmations_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(public_checker_router.router)
app.include_router(public_collection_router.router)
app.include_router(legacy_ops_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_actions_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_observability_router.router)
app.include_router(trip_lifecycle_router.router, dependencies=[Depends(_auth_or_skip)])


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
                if existing.get("agency_id") != agency_id:
                    logger.warning(
                        "Seed fixture trip %s already exists with agency_id=%s; "
                        "not reassigning to agency_id=%s. Skipping.",
                        trip_id, existing.get("agency_id"), agency_id,
                    )
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


def _execute_spine_pipeline(
    run_id: str,
    request_dict: dict[str, Any],
    agency_id: str,
    user_id: str,
    target_trip_id: Optional[str] = None,
    audit_event_type: str = "trip_created",
    existing_trip_status: Optional[str] = None,
) -> None:
    """Run the spine pipeline in the background and persist status/events."""
    return execute_spine_pipeline(
        run_id=run_id,
        request_dict=request_dict,
        agency_id=agency_id,
        user_id=user_id,
        build_envelopes=build_envelopes,
        load_fixture_expectations=load_fixture_expectations,
        to_dict=_to_dict,
        close_inherited_lock_fds=_close_inherited_lock_fds,
        save_processed_trip=save_processed_trip,
        trip_store=TripStore,
        audit_store=AuditStore,
        run_spine_once_fn=run_spine_once,
        logger=logger,
        otel_tracer=_otel_tracer,
        run_ledger=RunLedger,
        run_state_running=RunState.RUNNING,
        draft_store=DraftStore,
        agency_settings_store=AgencySettingsStore,
        set_strict_mode_fn=set_strict_mode,
        build_live_checker_signals_fn=build_live_checker_signals,
        emit_run_started_fn=emit_run_started,
        emit_run_completed_fn=emit_run_completed,
        emit_run_failed_fn=emit_run_failed,
        emit_run_blocked_fn=emit_run_blocked,
        emit_stage_entered_fn=emit_stage_entered,
        emit_stage_completed_fn=emit_stage_completed,
        target_trip_id=target_trip_id,
        audit_event_type=audit_event_type,
        existing_trip_status=existing_trip_status,
    )


trip_lifecycle_router.configure(execute_pipeline_fn=_execute_spine_pipeline)


def _run_public_checker_submission(request_dict: dict[str, Any]) -> RunStatusResponse:
    return run_public_checker_submission(
        request_dict=request_dict,
        build_envelopes=build_envelopes,
        load_fixture_expectations=load_fixture_expectations,
        to_dict=_to_dict,
        save_processed_trip=save_processed_trip,
        get_public_checker_agency_id=_get_public_checker_agency_id,
    logger=logger,
    )


@app.post("/api/public-checker/run", response_model=RunStatusResponse)
@limiter.limit("12/minute")
def run_public_checker(
    request: Request,
    response: Response,
    payload: SpineRunRequest,
) -> RunStatusResponse:
    """Submit a public itinerary checker run without agency auth."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > PUBLIC_CHECKER_MAX_BYTES:
                raise HTTPException(status_code=413, detail="Request body too large")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid content-length header")
    _ = (request, response)
    return _run_public_checker_submission(payload.model_dump(exclude_none=True))


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
# Draft Management Endpoints (Phase 0)
# =============================================================================

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
        existing_trips = await _ts(TripStore.list_trips, agency_id=agency_id)
        if not existing_trips:
            try:
                seed_count = await _ts(_seed_scenario_for_agency, agency_id)
                logger.info("Auto-seeded %d mock trips for test agency %s", seed_count, agency_id)
            except Exception as e:
                logger.warning("Failed to auto-seed for test agency: %s", e)
    
    trips = await _ts(TripStore.list_trips, status=status, limit=limit, agency_id=agency_id)
    total = await _ts(TripStore.count_trips, status=status, agency_id=agency_id)
    return {"items": trips, "total": total}


@app.get("/trips/{trip_id}")
def get_trip(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
):
    """Get a specific trip by ID."""
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
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
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Fetch suitability flags from the trip's decision output
    suitability_flags = []
    
    try:
        # Get the decision output if it exists
        decision_output = trip.get("decision")
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


@app.patch("/trips/{trip_id}")
def patch_trip(
    trip_id: str,
    updates: Dict[str, Any],
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """
    Update trip fields (e.g. status, follow_up_due_date).
    
    Supported fields:
    - status: Trip status (new, in_progress, completed, etc.)
    - follow_up_due_date: ISO-8601 datetime string for promised follow-up
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
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

        if "dateWindow" in incoming_updates:
            dw_value = _trimmed_string(incoming_updates.get("dateWindow"))
            if dw_value:
                facts["date_window"] = {
                    "value": dw_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                fields_to_clear.add("date_window")

        if "party" in incoming_updates:
            party_value = incoming_updates.get("party")
            if party_value is not None:
                try:
                    party_number = int(party_value)
                    facts["party_size"] = {
                        "value": party_number,
                        "confidence": 1.0,
                        "authority_level": "explicit_user",
                    }
                    fields_to_clear.add("party_size")
                except (ValueError, TypeError):
                    pass

        if "destination" in incoming_updates:
            dest_value = _trimmed_string(incoming_updates.get("destination"))
            if dest_value:
                facts["destination_candidates"] = {
                    "value": [dest_value],
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                fields_to_clear.add("destination_candidates")

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

    edited_fields = set(updates.keys())

    # Perform update (tenant-scoped)
    updated_trip = TripStore.update_trip_for_agency(trip_id, agency.id, updates)
    
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

    # Auto reassessment on meaningful edits when policy + stage allow.
    settings = AgencySettingsStore.load(agency.id)
    policy = settings.autonomy
    current_stage = str((updated_trip or {}).get("stage") or "discovery")
    should_auto_reassess = (
        bool(updated_trip)
        and policy.auto_reprocess_on_edit
        and policy.auto_reprocess_stages.get(current_stage, False)
        and bool(edited_fields & trip_lifecycle_service.REASSESS_EDIT_TRIGGER_FIELDS)
    )
    if should_auto_reassess and updated_trip:
        request_dict = trip_lifecycle_service.build_reassessment_request_from_trip(updated_trip)
        run_id = trip_lifecycle_service.queue_trip_reassessment(
            updated_trip,
            agency_id=agency.id,
            user_id=user.id,
            request_dict=request_dict,
            trigger="auto_edit",
            reason=f"fields_changed:{','.join(sorted(edited_fields & trip_lifecycle_service.REASSESS_EDIT_TRIGGER_FIELDS))}",
            execute_pipeline_fn=_execute_spine_pipeline,
        )
        updated_trip["reassess"] = {
            "queued": True,
            "run_id": run_id,
            "trigger": "auto_edit",
        }

    return updated_trip


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


class PaymentTrackingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agreed_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    amount_paid: Optional[float] = None
    balance_due: Optional[float] = None
    payment_status: Literal[
        "not_started",
        "deposit_paid",
        "partially_paid",
        "paid",
        "overdue",
        "waived",
        "refunded",
        "unknown",
    ] = "unknown"
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_proof_url: Optional[str] = None
    refund_status: Literal[
        "not_applicable",
        "not_requested",
        "pending_review",
        "approved",
        "processing",
        "paid",
        "rejected",
        "cancelled",
    ] = "not_applicable"
    refund_amount_agreed: Optional[float] = None
    refund_method: Optional[str] = None
    refund_reference: Optional[str] = None
    refund_paid_by_agency: bool = False
    notes: Optional[str] = None
    tracking_only: bool = True

    @field_validator("agreed_amount", "amount_paid", "balance_due", "refund_amount_agreed")
    @classmethod
    def non_negative_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "INR"
        stripped = v.strip().upper()
        if not stripped:
            return "INR"
        if len(stripped) != 3:
            raise ValueError("must be a 3-letter currency code")
        return stripped

    @model_validator(mode="after")
    def compute_balance_due(self) -> "PaymentTrackingModel":
        agreed = self.agreed_amount or 0.0
        paid = self.amount_paid or 0.0
        self.balance_due = round(max(agreed - paid, 0.0), 2)
        self.tracking_only = True
        return self


class BookingDataModel(BaseModel):
    travelers: List[BookingTravelerModel]
    payer: Optional[BookingPayerModel] = None
    special_requirements: Optional[str] = None
    booking_notes: Optional[str] = None
    payment_tracking: Optional[PaymentTrackingModel] = None

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
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    booking_data = TripStore.get_booking_data_for_agency(trip_id, agency.id)
    return _booking_data_envelope(trip, booking_data)


@app.patch("/trips/{trip_id}/booking-data")
def update_booking_data(
    trip_id: str,
    request: BookingDataUpdateRequest,
    agency: Agency = Depends(get_current_agency),
):
    """Update booking data with stage gate, optimistic lock, audit, readiness recompute.

    Booking data and readiness are written in a single atomic update_trip_if_version
    call to prevent partial updates (booking data written but readiness stale).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Stage gate: only proposal/booking
    current_stage = trip.get("stage", "discovery")
    if current_stage not in ("proposal", "booking"):
        raise HTTPException(
            status_code=403,
            detail=f"Booking data can only be updated at proposal/booking stage, current: {current_stage}",
        )

    bd_dict = request.booking_data.model_dump()

    # Compute readiness BEFORE writing so both booking_data and validation
    # can be persisted in a single atomic update.
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

    # Atomic write: booking_data + readiness together, with compare-and-set and tenant scoping
    expected = request.expected_updated_at
    updated = TripStore.update_trip_if_version_for_agency(
        trip_id,
        agency.id,
        {"booking_data": bd_dict, "validation": validation},
        expected_updated_at=expected,
    )
    if not updated:
        actual = trip.get("updated_at")
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Booking data conflict",
                "expected_updated_at": expected,
                "actual_updated_at": actual,
            },
        )

    # Audit: metadata only, no raw PII
    AuditStore.log_event("booking_data_updated", agency.id, {
        "trip_id": trip_id,
        "stage": current_stage,
        "reason_present": bool(request.reason),
        "reason_length": len(request.reason or ""),
        "fields_changed": [
            f for f in [
                "travelers",
                "payer" if request.booking_data.payer else None,
                "special_requirements" if request.booking_data.special_requirements else None,
                "booking_notes" if request.booking_data.booking_notes else None,
                "payment_tracking" if request.booking_data.payment_tracking else None,
            ]
            if f is not None
        ],
        "traveler_count": len(request.booking_data.travelers),
        "has_passport_data": any(t.passport_number for t in request.booking_data.travelers),
        "has_payer": request.booking_data.payer is not None,
        "has_payment_tracking": request.booking_data.payment_tracking is not None,
        "payment_status": request.booking_data.payment_tracking.payment_status if request.booking_data.payment_tracking else None,
        "refund_status": request.booking_data.payment_tracking.refund_status if request.booking_data.payment_tracking else None,
        "has_payment_reference": bool(request.booking_data.payment_tracking and request.booking_data.payment_tracking.payment_reference),
        "has_payment_proof_url": bool(request.booking_data.payment_tracking and request.booking_data.payment_tracking.payment_proof_url),
        "has_refund_reference": bool(request.booking_data.payment_tracking and request.booking_data.payment_tracking.refund_reference),
        "actor": "operator",
    })

    booking_data = TripStore.get_booking_data_for_agency(trip_id, agency.id)
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


class PendingBookingReviewActionRequest(BaseModel):
    reason: Optional[str] = None


class GenerateCollectionLinkRequest(BaseModel):
    expires_in_hours: int = 168


# ---------------------------------------------------------------------------
# Document upload models (Phase 4B)
# ---------------------------------------------------------------------------

from enum import Enum as _Enum

class DocumentTypeEnum(str, _Enum):
    passport = "passport"
    visa = "visa"
    insurance = "insurance"
    flight_ticket = "flight_ticket"
    hotel_confirmation = "hotel_confirmation"
    other = "other"

class DocumentResponse(BaseModel):
    id: str
    trip_id: str
    traveler_id: Optional[str] = None
    uploaded_by_type: str
    document_type: str
    filename_present: bool = True
    filename_ext: str
    mime_type: str
    size_bytes: int
    status: str
    scan_status: str
    review_notes_present: bool
    created_at: str
    updated_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None

class DocumentListResponse(BaseModel):
    trip_id: str
    documents: list[DocumentResponse]

class DownloadUrlResponse(BaseModel):
    url: str
    expires_in: int

class ReviewDocumentRequest(BaseModel):
    traveler_id: Optional[str] = None
    notes_present: bool = False


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
    request: GenerateCollectionLinkRequest = GenerateCollectionLinkRequest(),
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Generate a customer collection link for this trip.

    Creates a token that can be shared with the customer to collect booking data.
    The token is single-use and expires after the configured TTL.
    Returns the token ID, collection URL, and expiration time.
    """
    from spine_api.services.collection_service import generate_token

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(
            status_code=403,
            detail="Collection links can only be generated at proposal/booking stage",
        )

    async with rls_session(agency.id) as db:
        plain_token, record = await generate_token(
            db,
            trip_id=trip_id,
            agency_id=agency.id,
            created_by=user.id,
            ttl_hours=request.expires_in_hours,
        )

    base_url = os.getenv("PUBLIC_COLLECTION_BASE_URL", "")
    path = f"/api/public/booking-collection/{agency.id}/{plain_token}"
    collection_url = f"{base_url}{path}" if base_url else path

    return CollectionLinkResponse(
        token_id=record.id,
        collection_url=collection_url,
        expires_at=record.expires_at.isoformat(),
        trip_id=trip_id,
        status="active",
    )


@app.get("/trips/{trip_id}/collection-link", response_model=CollectionLinkStatusResponse)
async def get_collection_link_status(trip_id: str, agency: Agency = Depends(get_current_agency)):
    """Check collection link status and pending submission."""
    from spine_api.services.collection_service import get_active_token_for_trip

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    async with rls_session(agency.id) as db:
        token = await get_active_token_for_trip(db, trip_id)
    pending = await _ts(TripStore.get_pending_booking_data_for_agency, trip_id, agency.id)

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

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    async with rls_session(agency.id) as db:
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
    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    pending = await _ts(TripStore.get_pending_booking_data_for_agency, trip_id, agency.id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data")

    return PendingBookingDataResponse(
        trip_id=trip_id,
        pending_booking_data=pending,
        booking_data_source=trip.get("booking_data_source"),
    )


@app.post("/trips/{trip_id}/pending-booking-data/accept")
async def accept_pending_booking_data(trip_id: str, request: Optional[PendingBookingReviewActionRequest] = None, agency: Agency = Depends(get_current_agency)):
    """Accept pending customer submission into trusted booking_data.

    Computes readiness BEFORE writing, then persists booking_data, pending_booking_data,
    booking_data_source, and validation (with readiness) in a single atomic
    versioned update. This prevents the trip from being left with booking data
    accepted but readiness stale if the second write fails.
    """
    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Accept only allowed at proposal/booking stage")

    pending = await _ts(TripStore.get_pending_booking_data_for_agency, trip_id, agency.id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data to accept")
    if isinstance(pending, dict) and pending.get("payment_tracking") is not None:
        raise HTTPException(
            status_code=422,
            detail="Customer-submitted booking data cannot include payment tracking",
        )

    # Re-validate through Pydantic (defensive)
    validated = BookingDataModel(**pending)
    bd_dict = validated.model_dump()

    # Compute readiness BEFORE writing
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

    # Atomic write: all fields in one versioned update
    expected = trip.get("updated_at")
    updated = await _ts(TripStore.update_trip_if_version_for_agency, trip_id, agency.id, {
        "booking_data": bd_dict,
        "pending_booking_data": None,
        "booking_data_source": "customer_accepted",
        "validation": validation,
    }, expected_updated_at=expected)
    if not updated:
        raise HTTPException(
            status_code=409,
            detail="Trip was modified while processing acceptance",
        )

    AuditStore.log_event("booking_data_accepted_from_customer", agency.id, {
        "trip_id": trip_id,
        "traveler_count": len(validated.travelers),
        "has_payer": validated.payer is not None,
        "has_passport_data": any(t.passport_number for t in validated.travelers),
        "reason_present": bool(request and request.reason),
    })

    booking_data = await _ts(TripStore.get_booking_data_for_agency, trip_id, agency.id)
    return _booking_data_envelope(updated, booking_data)


@app.post("/trips/{trip_id}/pending-booking-data/reject")
async def reject_pending_booking_data(trip_id: str, request: Optional[PendingBookingReviewActionRequest] = None, agency: Agency = Depends(get_current_agency)):
    """Reject pending customer submission. Clears pending data."""
    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    pending = await _ts(TripStore.get_pending_booking_data_for_agency, trip_id, agency.id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending booking data to reject")

    await _ts(TripStore.update_trip_for_agency, trip_id, agency.id, {"pending_booking_data": None})

    AuditStore.log_event("booking_data_rejected_from_customer", agency.id, {
        "trip_id": trip_id,
        "reason_present": bool(request and request.reason),
    })

    return {"ok": True, "message": "Pending booking data rejected"}


# ---------------------------------------------------------------------------
# Document endpoints (Phase 4B)
# ---------------------------------------------------------------------------

def _doc_to_response(doc) -> DocumentResponse:
    """Convert a BookingDocument model to DocumentResponse."""
    return DocumentResponse(
        id=doc.id,
        trip_id=doc.trip_id,
        traveler_id=doc.traveler_id,
        uploaded_by_type=doc.uploaded_by_type,
        document_type=doc.document_type,
        filename_present=True,
        filename_ext=doc.filename_ext,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        status=doc.status,
        scan_status=doc.scan_status,
        review_notes_present=doc.review_notes_present,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
        reviewed_at=doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        reviewed_by=doc.reviewed_by,
    )


@app.post("/trips/{trip_id}/documents", response_model=DocumentResponse)
async def upload_trip_document(
    trip_id: str,
    document_type: DocumentTypeEnum = Form(...),
    traveler_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Agent uploads a document for a trip."""
    from spine_api.services.document_service import (
        validate_file_upload, sanitize_extension, upload_document,
    )
    import hashlib

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Documents only accepted at proposal/booking stage")

    file_data, mime_type = await validate_file_upload(file)
    ext = sanitize_extension(file.filename)
    filename_hash = hashlib.sha256((file.filename or "").encode()).hexdigest()
    doc_type_value = document_type.value

    doc = await upload_document(
        db,
        trip_id=trip_id,
        agency_id=agency.id,
        file_data=file_data,
        mime_type=mime_type,
        filename_hash=filename_hash,
        filename_ext=ext,
        document_type=doc_type_value,
        uploaded_by_type="agent",
        uploaded_by_id=agency.id,
        traveler_id=traveler_id,
    )

    AuditStore.log_event("document_uploaded", agency.id, {
        "trip_id": trip_id,
        "document_id": doc.id,
        "document_type": doc_type_value,
        "uploaded_by_type": "agent",
        "size_bytes": doc.size_bytes,
        "mime_type": mime_type,
        "sha256_present": True,
        "filename_present": True,
        "status": doc.status,
        "scan_status": doc.scan_status,
    })

    return _doc_to_response(doc)


@app.get("/trips/{trip_id}/documents", response_model=DocumentListResponse)
async def list_trip_documents(trip_id: str, agency: Agency = Depends(get_current_agency), db: AsyncSession = Depends(get_rls_db)):
    """List all non-deleted documents for a trip."""
    from spine_api.services.document_service import get_documents_for_trip

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    docs = await get_documents_for_trip(db, trip_id, agency.id)

    return DocumentListResponse(
        trip_id=trip_id,
        documents=[_doc_to_response(d) for d in docs],
    )


@app.get("/trips/{trip_id}/documents/{document_id}/download-url", response_model=DownloadUrlResponse)
async def get_document_download_url(trip_id: str, document_id: str, agency: Agency = Depends(get_current_agency), db: AsyncSession = Depends(get_rls_db)):
    """Get a short-lived signed URL for downloading a document."""
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    url = await storage.get_signed_url(document_id, "download")

    return DownloadUrlResponse(url=url, expires_in=900)


@app.post("/trips/{trip_id}/documents/{document_id}/accept", response_model=DocumentResponse)
async def accept_trip_document(
    trip_id: str,
    document_id: str,
    request: Optional[ReviewDocumentRequest] = None,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Accept a pending document. Only allowed from pending_review status."""
    from spine_api.services.document_service import accept_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Accept only allowed at proposal/booking stage")

    doc = await accept_document(
        db, document_id, agency.id, reviewed_by=agency.id,
        notes_present=request.notes_present if request else False,
    )

    AuditStore.log_event("document_accepted", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "review_notes_present": doc.review_notes_present,
    })

    return _doc_to_response(doc)


@app.post("/trips/{trip_id}/documents/{document_id}/reject", response_model=DocumentResponse)
async def reject_trip_document(
    trip_id: str,
    document_id: str,
    request: Optional[ReviewDocumentRequest] = None,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Reject a pending document. Only allowed from pending_review status."""
    from spine_api.services.document_service import reject_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Reject only allowed at proposal/booking stage")

    doc = await reject_document(
        db, document_id, agency.id, reviewed_by=agency.id,
        notes_present=request.notes_present if request else False,
    )

    AuditStore.log_event("document_rejected", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "review_notes_present": doc.review_notes_present,
    })

    return _doc_to_response(doc)


@app.delete("/trips/{trip_id}/documents/{document_id}")
async def delete_trip_document(trip_id: str, document_id: str, agency: Agency = Depends(get_current_agency), db: AsyncSession = Depends(get_rls_db)):
    """Soft-delete a document. Only allowed from accepted/rejected status."""
    from spine_api.services.document_service import soft_delete_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Delete only allowed at proposal/booking stage")

    doc = await soft_delete_document(db, document_id, agency.id, deleted_by=agency.id)

    AuditStore.log_event("document_deleted", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "storage_delete_status": doc.storage_delete_status,
    })

    return {"ok": True, "status": "deleted"}


@app.get("/api/internal/documents/{document_id}/download")
async def internal_document_download(
    document_id: str,
    token: str = Query(...),
    expires: str = Query(...),
):
    """Internal signed URL endpoint for document download.

    Validates HMAC claim keyed by document_id. Returns file content.
    Uses a plain session because auth is HMAC-based (not agency-scoped JWT),
    and the document_id is validated by the signed URL before this endpoint runs.
    """
    from spine_api.services.document_storage import verify_signed_url, get_document_storage
    from spine_api.core.database import async_session_maker
    from spine_api.models.tenant import BookingDocument
    from fastapi.responses import Response as FastAPIResponse
    from spine_api.core.rls import apply_rls

    if not verify_signed_url(document_id, "download", token, expires):
        raise HTTPException(status_code=403, detail="Invalid or expired download URL")

    async with async_session_maker() as db:
        # Two-step lookup: first get the doc to learn its agency_id, then apply RLS
        result = await db.execute(
            select(BookingDocument).where(BookingDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            await apply_rls(db, doc.agency_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    try:
        data = await storage.get(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FastAPIResponse(
        content=data,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="document{doc.filename_ext}"',
        },
    )


# ---------------------------------------------------------------------------
# Extraction endpoints (Phase 4C)
# ---------------------------------------------------------------------------


class ExtractionFieldView(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: float
    present: bool


class ExtractionResponse(BaseModel):
    id: str
    document_id: str
    status: str
    extracted_by: str
    overall_confidence: Optional[float] = None
    field_count: int
    fields: list[ExtractionFieldView]
    created_at: str
    updated_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    # Phase 4D provider metadata
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    error_code: Optional[str] = None
    error_summary: Optional[str] = None
    confidence_method: Optional[str] = None
    # Phase 4E attempt tracking
    attempt_count: int = 0
    run_count: int = 0
    current_attempt_id: Optional[str] = None
    page_count: Optional[int] = None


class AttemptSummaryResponse(BaseModel):
    attempt_id: str
    run_number: int
    attempt_number: int
    fallback_rank: Optional[int] = None
    provider_name: str
    model_name: Optional[str] = None
    latency_ms: Optional[int] = None
    status: str
    error_code: Optional[str] = None
    created_at: Optional[str] = None


class ApplyExtractionRequest(BaseModel):
    traveler_id: str
    fields_to_apply: list[str]
    allow_overwrite: bool = False
    create_traveler_if_missing: bool = False


class ApplyConflict(BaseModel):
    field_name: str
    existing_value: str
    extracted_value: str


class ApplyExtractionResponse(BaseModel):
    applied: bool
    conflicts: list[ApplyConflict] = Field(default_factory=list)
    extraction: Optional[ExtractionResponse] = None


def _extraction_to_response(ext) -> ExtractionResponse:
    """Convert DocumentExtraction to API response with decrypted fields."""
    from spine_api.services.extraction_service import decrypt_extraction_fields, VALID_EXTRACTION_FIELDS

    decrypted = decrypt_extraction_fields(ext) or {}
    confidence = ext.confidence_scores or {}
    fields = []
    for fname in VALID_EXTRACTION_FIELDS:
        if fname in decrypted or fname in confidence:
            fields.append(ExtractionFieldView(
                field_name=fname,
                value=decrypted.get(fname),
                confidence=confidence.get(fname, 0.0),
                present=fname in decrypted and decrypted[fname] is not None,
            ))

    return ExtractionResponse(
        id=ext.id,
        document_id=ext.document_id,
        status=ext.status,
        extracted_by=ext.extracted_by,
        overall_confidence=ext.overall_confidence,
        field_count=ext.field_count,
        fields=fields,
        created_at=ext.created_at.isoformat() if ext.created_at else "",
        updated_at=ext.updated_at.isoformat() if ext.updated_at else "",
        reviewed_at=ext.reviewed_at.isoformat() if ext.reviewed_at else None,
        reviewed_by=ext.reviewed_by,
        provider_name=getattr(ext, "provider_name", None),
        model_name=getattr(ext, "model_name", None),
        latency_ms=getattr(ext, "latency_ms", None),
        prompt_tokens=getattr(ext, "prompt_tokens", None),
        completion_tokens=getattr(ext, "completion_tokens", None),
        total_tokens=getattr(ext, "total_tokens", None),
        cost_estimate_usd=getattr(ext, "cost_estimate_usd", None),
        error_code=getattr(ext, "error_code", None),
        error_summary=getattr(ext, "error_summary", None),
        confidence_method=getattr(ext, "confidence_method", None),
        attempt_count=getattr(ext, "attempt_count", 0) or 0,
        run_count=getattr(ext, "run_count", 0) or 0,
        current_attempt_id=getattr(ext, "current_attempt_id", None),
        page_count=getattr(ext, "page_count", None),
    )


@app.post("/trips/{trip_id}/documents/{document_id}/extract", response_model=ExtractionResponse)
async def extract_document(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Run OCR extraction on a document. Allowed for pending_review or accepted documents."""
    from spine_api.services.extraction_service import run_extraction, get_extractor, ExtractionValidationError
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Extraction requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in ("pending_review", "accepted"):
        raise HTTPException(status_code=409, detail=f"Cannot extract from document with status {doc.status}")

    # MIME prevalidation: reject unsupported MIME before creating any extraction row
    ALLOWED_EXTRACTION_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
    if doc.mime_type not in ALLOWED_EXTRACTION_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "unsupported_mime_type",
                "message": f"MIME type '{doc.mime_type}' not supported for extraction",
            },
        )

    storage = get_document_storage()
    try:
        extraction = await run_extraction(db, doc, storage, agency.id)
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Handle failed extraction
    if extraction.status == "failed":
        AuditStore.log_event("extraction_failed", agency.id, {
            "trip_id": trip_id,
            "document_id": document_id,
            "provider": extraction.provider_name,
            "model": getattr(extraction, "model_name", None),
            "error_code": extraction.error_code,
            "latency_ms": getattr(extraction, "latency_ms", None),
        })
        raise HTTPException(status_code=422, detail={
            "message": "Extraction failed",
            "error_code": extraction.error_code,
            "error_summary": extraction.error_summary,
            "provider": extraction.provider_name,
        })

    AuditStore.log_event("extraction_created", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "document_type": doc.document_type,
        "field_count": extraction.field_count,
        "overall_confidence": extraction.overall_confidence,
        "fields_present": extraction.fields_present,
        "provider": extraction.provider_name,
        "model": getattr(extraction, "model_name", None),
        "latency_ms": getattr(extraction, "latency_ms", None),
        "confidence_method": getattr(extraction, "confidence_method", None),
    })

    return _extraction_to_response(extraction)


@app.get("/trips/{trip_id}/documents/{document_id}/extraction", response_model=ExtractionResponse)
async def get_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Get extraction results for a document."""
    from spine_api.services.extraction_service import get_extraction_for_document

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found for this document")

    return _extraction_to_response(extraction)


@app.post("/trips/{trip_id}/documents/{document_id}/extraction/retry", response_model=ExtractionResponse)
async def retry_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Retry a failed extraction. Creates new run with attempt rows."""
    from spine_api.services.extraction_service import run_extraction, ExtractionValidationError
    from spine_api.services.document_service import get_document_by_id
    from spine_api.services.document_storage import get_document_storage

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Retry requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    try:
        extraction = await run_extraction(db, doc, storage, agency.id)
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if extraction.status == "failed":
        raise HTTPException(status_code=422, detail={
            "message": "Extraction retry failed",
            "error_code": extraction.error_code,
            "error_summary": extraction.error_summary,
            "provider": extraction.provider_name,
        })

    return _extraction_to_response(extraction)


@app.get("/trips/{trip_id}/documents/{document_id}/extraction/attempts", response_model=list[AttemptSummaryResponse])
async def list_extraction_attempts(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """List all extraction attempts for a document (audit trail). No PII."""
    from spine_api.services.extraction_service import get_extraction_for_document
    from spine_api.models.tenant import DocumentExtractionAttempt
    from sqlalchemy import select

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    attempts = (await db.execute(
        select(DocumentExtractionAttempt)
        .where(DocumentExtractionAttempt.extraction_id == extraction.id)
        .order_by(DocumentExtractionAttempt.attempt_number)
    )).scalars().all()

    return [
        AttemptSummaryResponse(
            attempt_id=a.id,
            run_number=a.run_number,
            attempt_number=a.attempt_number,
            fallback_rank=a.fallback_rank,
            provider_name=a.provider_name,
            model_name=a.model_name,
            latency_ms=a.latency_ms,
            status=a.status,
            error_code=a.error_code,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in attempts
    ]


@app.post("/trips/{trip_id}/documents/{document_id}/extraction/apply", response_model=ApplyExtractionResponse)
async def apply_extraction(
    trip_id: str,
    document_id: str,
    payload: ApplyExtractionRequest,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Apply selected extraction fields to booking_data. Requires document accepted."""
    from spine_api.services.extraction_service import (
        get_extraction_for_document, apply_extraction as do_apply,
        ExtractionValidationError,
    )
    from spine_api.services.document_service import get_document_by_id

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.get("stage", "discovery") not in ("proposal", "booking"):
        raise HTTPException(status_code=403, detail="Apply requires proposal or booking stage")

    doc = await get_document_by_id(db, document_id, agency.id)
    if not doc or doc.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "accepted":
        raise HTTPException(status_code=409, detail="Document must be accepted before applying extraction")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    try:
        result = await do_apply(
            db=db, document=doc, extraction=extraction,
            fields_to_apply=payload.fields_to_apply,
            traveler_id=payload.traveler_id,
            reviewed_by=agency.id,
            allow_overwrite=payload.allow_overwrite,
            create_traveler_if_missing=payload.create_traveler_if_missing,
        )
    except ExtractionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    applied = result["applied"]
    conflicts = result["conflicts"]
    extraction = result["extraction"]

    if applied:
        AuditStore.log_event("extraction_applied", agency.id, {
            "trip_id": trip_id,
            "document_id": document_id,
            "fields_applied": payload.fields_to_apply,
            "field_count": len(payload.fields_to_apply),
            "min_confidence": min(
                (extraction.confidence_scores or {}).get(f, 0.0) for f in payload.fields_to_apply
            ) if payload.fields_to_apply else 0.0,
            "overall_confidence": extraction.overall_confidence,
        })

    return ApplyExtractionResponse(
        applied=applied,
        conflicts=[ApplyConflict(**c) for c in conflicts],
        extraction=_extraction_to_response(extraction) if extraction else None,
    )


@app.post("/trips/{trip_id}/documents/{document_id}/extraction/reject", response_model=ExtractionResponse)
async def reject_extraction(
    trip_id: str,
    document_id: str,
    agency: Agency = Depends(get_current_agency),
    db: AsyncSession = Depends(get_rls_db),
):
    """Reject extraction results. Does not modify booking_data. Allowed at any stage."""
    from spine_api.services.extraction_service import get_extraction_for_document, reject_extraction as do_reject

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    extraction = await get_extraction_for_document(db, document_id, agency.id)
    if not extraction:
        raise HTTPException(status_code=404, detail="No extraction found")

    try:
        extraction = await do_reject(db, extraction, reviewed_by=agency.id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    AuditStore.log_event("extraction_rejected", agency.id, {
        "trip_id": trip_id,
        "document_id": document_id,
        "extraction_id": extraction.id,
        "field_count": extraction.field_count,
    })

    return _extraction_to_response(extraction)



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
        "spine_api.server:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        reload=os.environ.get("SPINE_API_RELOAD", "1") == "1",
    )
