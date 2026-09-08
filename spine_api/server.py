"""
spine_api — FastAPI service exposing run_spine_once as an HTTP endpoint.

Architecture:
    Next.js (BFF)  →  HTTP POST /run  →  FastAPI spine_api  →  run_spine_once
                                                           (persistent process,
                                                            modules pre-loaded)

POST /run contract:
    Returns RunAcceptedResponse(run_id, state="queued") immediately.
    Poll GET /runs/{run_id} for the terminal artifact contract:
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
            assertions: [{ type, passed, message, field }] | null,
            meta: { stage, operating_mode, fixture_id, execution_ms }
        }

On non-leakage errors: raises HTTPException (500)

Environment variables:
    SPINE_API_HOST       — bind address (default: 127.0.0.1)
    SPINE_API_PORT       — port (default: 8000)
    SPINE_API_WORKERS    — number of uvicorn workers (default: 1)
    SPINE_API_CORS       — comma-separated allowed CORS origins
    SPINE_API_RELOAD     — set to 0 to disable dev reload
    TRAVELER_SAFE_STRICT — legacy compatibility env var; request-scoped strictness is read from SpineRunRequest.strict_leakage
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import threading
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import is_dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root and src/ to Python path so intake, agents, etc. are importable
_SRC_ROOT = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from starlette.requests import Request
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import asyncpg

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
    except (ValueError, TypeError, OSError) as e:
        import logging
        logging.getLogger("spine_api.otel").warning(f"OTel init failed (non-fatal): {e}")
# --- End OTel ---

from spine_api.core.env import load_project_env

load_project_env()

from spine_api.core.auth import get_current_user, get_current_agency, _auth_or_skip
from spine_api.core.database import engine
from spine_api.core.rls import inspect_rls_runtime_posture, rls_session
from spine_api.models.tenant import Agency, User
from spine_api.core.logging_filter import install_sensitive_data_filter
from spine_api.core.middleware import AuthMiddleware, PUBLIC_CHECKER_MAX_BYTES, RequestBodySizeMiddleware
from spine_api.core.rate_limiter import limiter, RateLimitExceededHandler, SlowAPIMiddleware
from spine_api.version import APP_VERSION
from slowapi.errors import RateLimitExceeded

from spine_api.contract import (
    SpineRunRequest,
    RunAcceptedResponse,
    RunStatusResponse,
    SuitabilityFlagsResponse,
    TripPatchRequest,
    TripResponse,
)
from src.intake.normalizer import Normalizer
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus  # noqa: E402 (PA-13)
from spine_api.services.public_checker_service import run_public_checker_submission
from spine_api.services.pipeline_execution_service import execute_spine_pipeline
from spine_api.services import trip_lifecycle_service
from spine_api.services.payment_queue_service import build_payment_queue_response_for_agency
from spine_api.product_b_events import ProductBEventStore  # noqa: F401  # Legacy re-export for tests/compatibility

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
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

DEFAULT_PUBLIC_CHECKER_AGENCY_ID = "__UNSET__"


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
    elif backend in {"postgres", "postgresql"}:
        backend = "sql"
    if backend not in {"file", "sql"}:
        raise RuntimeError(
            f"Unknown TRIPSTORE_BACKEND='{backend}'. Allowed values: file, json, sql, postgres, postgresql."
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
from spine_api.run_state import RunState
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
from spine_api.services.agent_runtime_adapters import TripStoreAdapter, AuditStoreAdapter
from spine_api.services.agent_runtime_factory import build_agent_runtime


_agent_trip_repo = TripStoreAdapter()
_agent_audit_sink = AuditStoreAdapter()
_agent_runtime_bundle = None
_agent_work_coordinator = None
_recovery_agent = None
_agent_supervisor = None
_requeue_worker_service = None


def _build_agent_runtime_bundle():
    """Construct and wire the agent runtime bundle during lifespan startup."""
    global _agent_runtime_bundle, _agent_work_coordinator, _recovery_agent, _agent_supervisor, _requeue_worker_service

    from spine_api.routers import agent_runtime as agent_runtime_router

    bundle = build_agent_runtime(
        _trip_repo=_agent_trip_repo,
        _audit_sink=_agent_audit_sink,
        _run_spine_fn=run_spine_once,
    )
    _agent_runtime_bundle = bundle
    _agent_work_coordinator = bundle.coordinator
    _recovery_agent = bundle.recovery_agent
    _agent_supervisor = bundle.supervisor
    _requeue_worker_service = bundle.requeue_worker_service
    agent_runtime_router.configure_runtime(
        agent_supervisor=_agent_supervisor,
        recovery_agent=_recovery_agent,
        requeue_worker_service=_requeue_worker_service,
        runtime_config=bundle.config.to_dict(),
    )
    return bundle

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
    from spine_api.routers import settings_health as settings_health_router
    from spine_api.routers import drafts as drafts_router
    from spine_api.routers import inbox as inbox_router
    from spine_api.routers import agent_runtime as agent_runtime_router
    from spine_api.routers import analytics as analytics_router
    from spine_api.routers import product_b_analytics as product_b_analytics_router
    from spine_api.routers import booking_tasks as booking_tasks_router
    from spine_api.routers import confirmations as confirmations_router
    from spine_api.routers import integrations as integrations_router
    from spine_api.routers import public_checker as public_checker_router
    from spine_api.routers import public_collection as public_collection_router
    from spine_api.routers import legacy_ops as legacy_ops_router
    from spine_api.routers import trip_actions as trip_actions_router
    from spine_api.routers import trip_observability as trip_observability_router
    from spine_api.routers import trip_lifecycle as trip_lifecycle_router
    from spine_api.routers import extraction as extraction_router
    from spine_api.routers import kdd as kdd_router
    from spine_api.routers import inbound as inbound_router
    from spine_api.routers import trust_scorecard as trust_scorecard_router
    from spine_api.routers import messaging as messaging_router
    from spine_api.routers import yield_arbitrage as yield_arbitrage_router
    from spine_api.routers import concierge as concierge_router
    from spine_api.routers import team_workflows as team_workflows_router
    from spine_api.routers import social_inbound as social_inbound_router
    from spine_api.routers import corporate as corporate_router
    from spine_api.routers import supplier as supplier_router
    from spine_api.routers import group_booking as group_booking_router
    from spine_api.routers import price_lock as price_lock_router
    from spine_api.routers import customer_memory as customer_memory_router
    from spine_api.routers import multimodal as multimodal_router
    from spine_api.routers import commission as commission_router
    from spine_api.routers import fx_sentinel as fx_sentinel_router
    from spine_api.routers import disruption_radar as disruption_radar_router
    from spine_api.routers import corporate_policy as corporate_policy_router
    from spine_api.routers import concierge_upsell as concierge_upsell_router
    from spine_api.routers import passenger_rights as passenger_rights_router
    from spine_api.routers import constraints as constraints_router
    from spine_api.routers import resilience as resilience_router
    from spine_api.routers import boundaries as boundaries_router
    from spine_api.routers import financial_ops as financial_ops_router
    from spine_api.routers import counterfactual as counterfactual_router
    from spine_api.routers import trip_documents as trip_documents_router
    from spine_api.routers import public_proposals as public_proposals_router
    from spine_api.routers import distribution as distribution_router
    from spine_api.routers import negotiation as negotiation_router
    from spine_api.routers import crisis_ops as crisis_ops_router
    from spine_api.routers import visa_radar as visa_radar_router
    from spine_api.routers import subagent_payouts as subagent_payouts_router
    from spine_api.routers import insurance as insurance_router
    from spine_api.routers import loyalty as loyalty_router
    from spine_api.routers import feedback as feedback_router
    from spine_api.routers import tax_compliance as tax_compliance_router
    from spine_api.routers import epistemic as epistemic_router
    from spine_api.routers import document_extraction as document_extraction_router
    from spine_api.routers import financial_settlement as financial_settlement_router
    from spine_api.routers import group_pareto as group_pareto_router
    from spine_api.routers import proposal_compiler as proposal_compiler_router
    from spine_api.routers import irops_healer as irops_healer_router
    from spine_api.routers import duty_of_care_radar as duty_of_care_radar_router
    from spine_api.routers import logistics as logistics_router
    from spine_api.routers import charter_aviation as charter_aviation_router
    from spine_api.routers import ivr_bypass as ivr_bypass_router
    from spine_api.routers import stress_benchmark as stress_benchmark_router
    from spine_api.routers import gds_sandbox as gds_sandbox_router
    from spine_api.routers import journey_graph as journey_graph_router
    from spine_api.routers import agent_lease as agent_lease_router
    from spine_api.routers import trip_history as trip_history_router
    from spine_api.routers import itinerary_export as itinerary_export_router
    from spine_api.routers import yield_benchmark as yield_benchmark_router
    from spine_api.routers import fulfillment as fulfillment_router
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

    _kdd_spec = importlib.util.spec_from_file_location(
        "routers.kdd",
        _base / "routers" / "kdd.py",
    )
    _kdd_mod = importlib.util.module_from_spec(_kdd_spec)
    _kdd_spec.loader.exec_module(_kdd_mod)
    kdd_router = _kdd_mod

    _social_inbound_spec = importlib.util.spec_from_file_location("routers.social_inbound", _base / "routers" / "social_inbound.py")
    _social_inbound_mod = importlib.util.module_from_spec(_social_inbound_spec)
    _social_inbound_spec.loader.exec_module(_social_inbound_mod)
    social_inbound_router = _social_inbound_mod

    _corporate_spec = importlib.util.spec_from_file_location("routers.corporate", _base / "routers" / "corporate.py")
    _corporate_mod = importlib.util.module_from_spec(_corporate_spec)
    _corporate_spec.loader.exec_module(_corporate_mod)
    corporate_router = _corporate_mod

    _supplier_spec = importlib.util.spec_from_file_location("routers.supplier", _base / "routers" / "supplier.py")
    _supplier_mod = importlib.util.module_from_spec(_supplier_spec)
    _supplier_spec.loader.exec_module(_supplier_mod)
    supplier_router = _supplier_mod

    _group_booking_spec = importlib.util.spec_from_file_location("routers.group_booking", _base / "routers" / "group_booking.py")
    _group_booking_mod = importlib.util.module_from_spec(_group_booking_spec)
    _group_booking_spec.loader.exec_module(_group_booking_mod)
    group_booking_router = _group_booking_mod

    _price_lock_spec = importlib.util.spec_from_file_location("routers.price_lock", _base / "routers" / "price_lock.py")
    _price_lock_mod = importlib.util.module_from_spec(_price_lock_spec)
    _price_lock_spec.loader.exec_module(_price_lock_mod)
    price_lock_router = _price_lock_mod

    _customer_memory_spec = importlib.util.spec_from_file_location("routers.customer_memory", _base / "routers" / "customer_memory.py")
    _customer_memory_mod = importlib.util.module_from_spec(_customer_memory_spec)
    _customer_memory_spec.loader.exec_module(_customer_memory_mod)
    customer_memory_router = _customer_memory_mod

    _multimodal_spec = importlib.util.spec_from_file_location("routers.multimodal", _base / "routers" / "multimodal.py")
    _multimodal_mod = importlib.util.module_from_spec(_multimodal_spec)
    _multimodal_spec.loader.exec_module(_multimodal_mod)
    multimodal_router = _multimodal_mod

    _commission_spec = importlib.util.spec_from_file_location("routers.commission", _base / "routers" / "commission.py")
    _commission_mod = importlib.util.module_from_spec(_commission_spec)
    _commission_spec.loader.exec_module(_commission_mod)
    commission_router = _commission_mod

    _fx_sentinel_spec = importlib.util.spec_from_file_location("routers.fx_sentinel", _base / "routers" / "fx_sentinel.py")
    _fx_sentinel_mod = importlib.util.module_from_spec(_fx_sentinel_spec)
    _fx_sentinel_spec.loader.exec_module(_fx_sentinel_mod)
    fx_sentinel_router = _fx_sentinel_mod

    _disruption_radar_spec = importlib.util.spec_from_file_location("routers.disruption_radar", _base / "routers" / "disruption_radar.py")
    _disruption_radar_mod = importlib.util.module_from_spec(_disruption_radar_spec)
    _disruption_radar_spec.loader.exec_module(_disruption_radar_mod)
    disruption_radar_router = _disruption_radar_mod

    _corporate_policy_spec = importlib.util.spec_from_file_location("routers.corporate_policy", _base / "routers" / "corporate_policy.py")
    _corporate_policy_mod = importlib.util.module_from_spec(_corporate_policy_spec)
    _corporate_policy_spec.loader.exec_module(_corporate_policy_mod)
    corporate_policy_router = _corporate_policy_mod

    _concierge_upsell_spec = importlib.util.spec_from_file_location("routers.concierge_upsell", _base / "routers" / "concierge_upsell.py")
    _concierge_upsell_mod = importlib.util.module_from_spec(_concierge_upsell_spec)
    _concierge_upsell_spec.loader.exec_module(_concierge_upsell_mod)
    concierge_upsell_router = _concierge_upsell_mod

    _passenger_rights_spec = importlib.util.spec_from_file_location("routers.passenger_rights", _base / "routers" / "passenger_rights.py")
    _passenger_rights_mod = importlib.util.module_from_spec(_passenger_rights_spec)
    _passenger_rights_spec.loader.exec_module(_passenger_rights_mod)
    passenger_rights_router = _passenger_rights_mod

    _constraints_spec = importlib.util.spec_from_file_location("routers.constraints", _base / "routers" / "constraints.py")
    _constraints_mod = importlib.util.module_from_spec(_constraints_spec)
    _constraints_spec.loader.exec_module(_constraints_mod)
    constraints_router = _constraints_mod

    _resilience_spec = importlib.util.spec_from_file_location("routers.resilience", _base / "routers" / "resilience.py")
    _resilience_mod = importlib.util.module_from_spec(_resilience_spec)
    _resilience_spec.loader.exec_module(_resilience_mod)
    resilience_router = _resilience_mod

    _boundaries_spec = importlib.util.spec_from_file_location("routers.boundaries", _base / "routers" / "boundaries.py")
    _boundaries_mod = importlib.util.module_from_spec(_boundaries_spec)
    _boundaries_spec.loader.exec_module(_boundaries_mod)
    boundaries_router = _boundaries_mod

    _passenger_rights_spec = importlib.util.spec_from_file_location("routers.passenger_rights", _base / "routers" / "passenger_rights.py")
    _passenger_rights_mod = importlib.util.module_from_spec(_passenger_rights_spec)
    _passenger_rights_spec.loader.exec_module(_passenger_rights_mod)
    passenger_rights_router = _passenger_rights_mod

    _financial_ops_spec = importlib.util.spec_from_file_location("routers.financial_ops", _base / "routers" / "financial_ops.py")
    _financial_ops_mod = importlib.util.module_from_spec(_financial_ops_spec)
    _financial_ops_spec.loader.exec_module(_financial_ops_mod)
    financial_ops_router = _financial_ops_mod

    _counterfactual_spec = importlib.util.spec_from_file_location("routers.counterfactual", _base / "routers" / "counterfactual.py")
    _counterfactual_mod = importlib.util.module_from_spec(_counterfactual_spec)
    _counterfactual_spec.loader.exec_module(_counterfactual_mod)
    counterfactual_router = _counterfactual_mod

    _trip_documents_spec = importlib.util.spec_from_file_location("routers.trip_documents", _base / "routers" / "trip_documents.py")
    _trip_documents_mod = importlib.util.module_from_spec(_trip_documents_spec)
    _trip_documents_spec.loader.exec_module(_trip_documents_mod)
    trip_documents_router = _trip_documents_mod

    _dist_spec = importlib.util.spec_from_file_location("routers.distribution", _base / "routers" / "distribution.py")
    _dist_mod = importlib.util.module_from_spec(_dist_spec)
    _dist_spec.loader.exec_module(_dist_mod)
    distribution_router = _dist_mod

    _neg_spec = importlib.util.spec_from_file_location("routers.negotiation", _base / "routers" / "negotiation.py")
    _neg_mod = importlib.util.module_from_spec(_neg_spec)
    _neg_spec.loader.exec_module(_neg_mod)
    negotiation_router = _neg_mod

    _crisis_spec = importlib.util.spec_from_file_location("routers.crisis_ops", _base / "routers" / "crisis_ops.py")
    _crisis_mod = importlib.util.module_from_spec(_crisis_spec)
    _crisis_spec.loader.exec_module(_crisis_mod)
    crisis_ops_router = _crisis_mod

    _visa_spec = importlib.util.spec_from_file_location("routers.visa_radar", _base / "routers" / "visa_radar.py")
    _visa_mod = importlib.util.module_from_spec(_visa_spec)
    _visa_spec.loader.exec_module(_visa_mod)
    visa_radar_router = _visa_mod

    _subagent_spec = importlib.util.spec_from_file_location("routers.subagent_payouts", _base / "routers" / "subagent_payouts.py")
    _subagent_mod = importlib.util.module_from_spec(_subagent_spec)
    _subagent_spec.loader.exec_module(_subagent_mod)
    subagent_payouts_router = _subagent_mod

    _ins_spec = importlib.util.spec_from_file_location("routers.insurance", _base / "routers" / "insurance.py")
    _ins_mod = importlib.util.module_from_spec(_ins_spec)
    _ins_spec.loader.exec_module(_ins_mod)
    insurance_router = _ins_mod

    _loyalty_spec = importlib.util.spec_from_file_location("routers.loyalty", _base / "routers" / "loyalty.py")
    _loyalty_mod = importlib.util.module_from_spec(_loyalty_spec)
    _loyalty_spec.loader.exec_module(_loyalty_mod)
    loyalty_router = _loyalty_mod

    _feedback_spec = importlib.util.spec_from_file_location("routers.feedback", _base / "routers" / "feedback.py")
    _feedback_mod = importlib.util.module_from_spec(_feedback_spec)
    _feedback_spec.loader.exec_module(_feedback_mod)
    feedback_router = _feedback_mod

    _epistemic_spec = importlib.util.spec_from_file_location("routers.epistemic", _base / "routers" / "epistemic.py")
    _epistemic_mod = importlib.util.module_from_spec(_epistemic_spec)
    _epistemic_spec.loader.exec_module(_epistemic_mod)
    epistemic_router = _epistemic_mod

    _doc_ext_spec = importlib.util.spec_from_file_location("routers.document_extraction", _base / "routers" / "document_extraction.py")
    _doc_ext_mod = importlib.util.module_from_spec(_doc_ext_spec)
    _doc_ext_spec.loader.exec_module(_doc_ext_mod)
    document_extraction_router = _doc_ext_mod

    _fin_spec = importlib.util.spec_from_file_location("routers.financial_settlement", _base / "routers" / "financial_settlement.py")
    _fin_mod = importlib.util.module_from_spec(_fin_spec)
    _fin_spec.loader.exec_module(_fin_mod)
    financial_settlement_router = _fin_mod

    _grp_spec = importlib.util.spec_from_file_location("routers.group_pareto", _base / "routers" / "group_pareto.py")
    _grp_mod = importlib.util.module_from_spec(_grp_spec)
    _grp_spec.loader.exec_module(_grp_mod)
    group_pareto_router = _grp_mod

    _prop_comp_spec = importlib.util.spec_from_file_location("routers.proposal_compiler", _base / "routers" / "proposal_compiler.py")
    _prop_comp_mod = importlib.util.module_from_spec(_prop_comp_spec)
    _prop_comp_spec.loader.exec_module(_prop_comp_mod)
    proposal_compiler_router = _prop_comp_mod

    _irops_spec = importlib.util.spec_from_file_location("routers.irops_healer", _base / "routers" / "irops_healer.py")
    _irops_mod = importlib.util.module_from_spec(_irops_spec)
    _irops_spec.loader.exec_module(_irops_mod)
    irops_healer_router = _irops_mod

    _doc_radar_spec = importlib.util.spec_from_file_location("routers.duty_of_care_radar", _base / "routers" / "duty_of_care_radar.py")
    _doc_radar_mod = importlib.util.module_from_spec(_doc_radar_spec)
    _doc_radar_spec.loader.exec_module(_doc_radar_mod)
    duty_of_care_radar_router = _doc_radar_mod

    _cht_spec = importlib.util.spec_from_file_location("routers.charter_aviation", _base / "routers" / "charter_aviation.py")
    _cht_mod = importlib.util.module_from_spec(_cht_spec)
    _cht_spec.loader.exec_module(_cht_mod)
    charter_aviation_router = _cht_mod

    _yld_spec = importlib.util.spec_from_file_location("routers.yield_arbitrage", _base / "routers" / "yield_arbitrage.py")
    _yld_mod = importlib.util.module_from_spec(_yld_spec)
    _yld_spec.loader.exec_module(_yld_mod)
    yield_arbitrage_router = _yld_mod

    _ivr_spec = importlib.util.spec_from_file_location("routers.ivr_bypass", _base / "routers" / "ivr_bypass.py")
    _ivr_mod = importlib.util.module_from_spec(_ivr_spec)
    _ivr_spec.loader.exec_module(_ivr_mod)
    ivr_bypass_router = _ivr_mod

    _stress_spec = importlib.util.spec_from_file_location("routers.stress_benchmark", _base / "routers" / "stress_benchmark.py")
    _stress_mod = importlib.util.module_from_spec(_stress_spec)
    _stress_spec.loader.exec_module(_stress_mod)
    stress_benchmark_router = _stress_mod

    _gds_sb_spec = importlib.util.spec_from_file_location("routers.gds_sandbox", _base / "routers" / "gds_sandbox.py")
    _gds_sb_mod = importlib.util.module_from_spec(_gds_sb_spec)
    _gds_sb_spec.loader.exec_module(_gds_sb_mod)
    gds_sandbox_router = _gds_sb_mod

    _itin_exp_spec = importlib.util.spec_from_file_location("routers.itinerary_export", _base / "routers" / "itinerary_export.py")
    _itin_exp_mod = importlib.util.module_from_spec(_itin_exp_spec)
    _itin_exp_spec.loader.exec_module(_itin_exp_mod)
    itinerary_export_router = _itin_exp_mod

    _yield_bench_spec = importlib.util.spec_from_file_location("routers.yield_benchmark", _base / "routers" / "yield_benchmark.py")
    _yield_bench_mod = importlib.util.module_from_spec(_yield_bench_spec)
    _yield_bench_spec.loader.exec_module(_yield_bench_mod)
    yield_benchmark_router = _yield_bench_mod

    _fulfill_spec = importlib.util.spec_from_file_location("routers.fulfillment", _base / "routers" / "fulfillment.py")
    _fulfill_mod = importlib.util.module_from_spec(_fulfill_spec)
    _fulfill_spec.loader.exec_module(_fulfill_mod)
    fulfillment_router = _fulfill_mod


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
    except (SQLAlchemyError, asyncpg.PostgresError) as e:
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
    except (SQLAlchemyError, asyncpg.PostgresError) as e:
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
                exists_result = await conn.execute(text("""
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
    except (SQLAlchemyError, asyncpg.PostgresError) as e:
        logger.error("Failed users membership backfill: %s", e)
        raise


async def _ensure_rls_no_force_on_auth_tables() -> None:
    """
    Remove FORCE ROW LEVEL SECURITY from auth-critical tables.

    memberships and workspace_codes (RLS_FORCE_EXEMPT_TABLES) are queried
    during login/join before app.current_agency_id is known — a chicken-and-
    egg problem. ENABLE RLS is kept (protects against non-owner roles) but
    FORCE is removed so the table owner can query without agency context.

    Idempotent: ALTER TABLE ... NO FORCE ROW LEVEL SECURITY is a no-op if
    FORCE is not already set.
    """
    from spine_api.core.rls import RLS_FORCE_EXEMPT_TABLES

    for table in RLS_FORCE_EXEMPT_TABLES:
        try:
            async with engine.begin() as conn:
                await _apply_startup_db_timeouts(conn)
                exists = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :t
                    )
                """), {"t": table})
                if not bool(exists.scalar()):
                    continue
                await conn.execute(text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
                logger.info("Removed FORCE RLS from %s (auth exempt)", table)
        except (SQLAlchemyError, asyncpg.PostgresError) as e:
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
    except (SQLAlchemyError, asyncpg.PostgresError) as e:
        logger.error("Failed membership/agency cleanup: %s", e)


async def _validate_public_checker_agency_configuration() -> None:
    """
    Enforce public-checker agency invariants before serving traffic.

    In SQL mode, public-checker trips persist with a fixed agency_id. That id
    must be explicitly configured (or use default) and must exist in agencies.
    """
    agency_id = _get_public_checker_agency_id()
    if not agency_id or agency_id == "__UNSET__":
        raise RuntimeError(
            "PUBLIC_CHECKER_AGENCY_ID is not configured. "
            "Set PUBLIC_CHECKER_AGENCY_ID to a real agencies.id in your environment. "
            "The old default UUID has been removed to prevent silent misconfiguration."
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
        # Broad catch is intentional: startup invariant wraps ALL exceptions
        # (including non-DB errors like config validation) in RuntimeError.
        # Verified by test_startup_invariant_sql_wraps_unexpected_exception.
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
    if os.environ.get("RUNNING_TESTS", "").lower() in ("1", "true", "yes"):
        return False
    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
    return env.strip().lower() not in ("production", "staging")


async def _validate_rls_runtime_posture_configuration() -> None:
    """
    Enforce that production-like SQL startup cannot silently run with bypassable tenant RLS.

    Validates all 11 tables in RLS_TENANT_TABLES have RLS enabled, and that all
    non-exempt tables have FORCE ROW LEVEL SECURITY. memberships and workspace_codes
    (RLS_FORCE_EXEMPT_TABLES) keep ENABLE RLS only — they are queried during
    login/join before agency context is known.
    """
    if not _is_sql_tripstore_backend():
        logger.info("RLS runtime posture validation skipped (TRIPSTORE_BACKEND!=sql)")
        return

    try:
        async with engine.begin() as conn:
            await _apply_startup_db_timeouts(conn)
            posture = await inspect_rls_runtime_posture(conn)
    except Exception as exc:
        # Broad catch is intentional: startup invariant wraps ALL exceptions
        # in RuntimeError for clean operator-facing failure messages.
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
    from spine_api.core.startup_assertions import run_startup_assertions
    from spine_api.core.feature_gates import log_feature_status

    # Run fail-closed boot checks
    run_startup_assertions(strict=True)
    log_feature_status()

    env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development")).lower().strip()
    from spine_api.core.startup_assertions import auth_bypass_enabled

    if auth_bypass_enabled() and env in ("production", "staging"):
        raise RuntimeError(
            "SPINE_API_DISABLE_AUTH cannot be enabled in production or staging. "
            f"Current ENVIRONMENT={env}"
        )
    if auth_bypass_enabled():
        logger.warning("⚠️  AUTH DISABLED — local/test only. Do not use in production.")

    # CORS production safety guard
    if env in ("production", "staging"):
        raw_cors = os.environ.get("SPINE_API_CORS", "").strip()
        if not raw_cors:
            raise RuntimeError(
                "SPINE_API_CORS environment variable must be set explicitly in production/staging "
                "to prevent default fallback to localhost."
            )
        for origin in CORS_ORIGINS:
            low_origin = origin.lower()
            if "*" in low_origin:
                raise RuntimeError(
                    f"CORS wildcard '*' is forbidden in production/staging environments (origin='{origin}')."
                )
            if "localhost" in low_origin or "127.0.0.1" in low_origin:
                raise RuntimeError(
                    f"CORS origins cannot include localhost or 127.0.0.1 in production/staging (origin='{origin}')."
                )

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

    # Build agent runtime bundle at startup (not import time) so env vars
    # are read fresh and router wiring happens after app construction.
    # Skip during test runs to avoid creating the TripStore SQL bridge
    # (agent_work_coordinator uses _run_async_blocking which can leave
    # the bridge's event loop in a broken state after teardown).
    if not os.environ.get("RUNNING_TESTS"):
        _build_agent_runtime_bundle()
        _recovery_agent.start()
        _agent_supervisor.start()
        if _requeue_worker_service is not None:
            _requeue_worker_service.start()
        _zombie_reaper_start()

    # Wire per-agency usage guards so each agency gets its own rate limits,
    # budget caps, and alert destinations.
    try:
        from src.llm.usage_guard import get_usage_guard, get_guard_for_agency
        from src.llm.alert_service import alert_service_from_env

        if not os.environ.get("RUNNING_TESTS"):
            alert_agency_id = os.environ.get("LLM_ALERT_AGENCY_ID", "waypoint-hq")
            try:
                # Initialize the per-agency guard from persisted settings.
                # This creates a guard instance keyed by agency_id with its own
                # limits, budget, and alert destinations.
                agency_guard = get_guard_for_agency(alert_agency_id)
                logger.info(
                    "Per-agency usage guard initialized (agency=%s, enabled=%s, budget=%s)",
                    alert_agency_id, agency_guard.enabled, agency_guard.daily_budget,
                )
                # Health check: verify at least one alert destination is configured
                # when alerts are enabled. A silent no-destination config means threshold
                # warnings and rate-limit blocks will be silently dropped.
                ad = AgencySettingsStore.load(alert_agency_id).alert_destinations
                if ad.enabled and not ad.destinations:
                    logger.warning(
                        "ALERT HEALTH: Alerts enabled for agency=%s but no destinations configured. "
                        "Alerts will be silently dropped. Configure at least one destination in "
                        "Settings > Alert Destinations.",
                        alert_agency_id,
                    )
            except (OSError, ValueError, KeyError):
                # Settings store unavailable — fall back to default env-based guard
                default_guard = get_usage_guard()
                default_guard.set_alert_service(alert_service_from_env())
                logger.info("Fallback default usage guard configured from env")
        else:
            # Test mode: default guard with env-var alert service
            default_guard = get_usage_guard()
            default_guard.set_alert_service(alert_service_from_env())
    except (OSError, ValueError, KeyError) as exc:
        logger.warning("Failed to configure usage guard: %s", exc)

    # Note: We no longer auto-seed at startup.
    # Seeding is now done per-agency for test users in the /trips endpoint.
    logger.info("Spine API startup complete")
    yield
    # Shutdown
    if not os.environ.get("RUNNING_TESTS"):
        _zombie_reaper_stop()
        if _requeue_worker_service is not None:
            _requeue_worker_service.stop()
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
app.state.limiter = limiter

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

# Trip-status invariant violations are client errors (policy rejection), not
# server faults: map to 422 instead of a raw 500 (review cycle 2, finding D).
# Raw-SQL update paths enforce via pre-SELECT raising the same exception, so
# every backend surfaces the same signal.
from fastapi import Request as _FastAPIRequest  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from spine_api.core.trip_status import IllegalTripStatusTransition  # noqa: E402


@app.exception_handler(IllegalTripStatusTransition)
async def _illegal_trip_status_transition_handler(
    request: _FastAPIRequest, exc: IllegalTripStatusTransition
):
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "reason": "illegal_trip_status_transition",
                "from_status": exc.old_status,
                "to_status": exc.new_status,
                "message": str(exc),
            }
        },
    )

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
app.include_router(settings_health_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(drafts_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(inbox_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(agent_runtime_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(analytics_router.router)
app.include_router(product_b_analytics_router.router)
app.include_router(booking_tasks_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(confirmations_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(integrations_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(public_checker_router.router)
app.include_router(public_collection_router.router)
app.include_router(legacy_ops_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_actions_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_observability_router.router)
app.include_router(trip_lifecycle_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(extraction_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(kdd_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(inbound_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trust_scorecard_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trust_scorecard_router.public_router)
app.include_router(messaging_router.router)
app.include_router(yield_arbitrage_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(concierge_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(team_workflows_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(social_inbound_router.router)
app.include_router(corporate_router.router)
app.include_router(supplier_router.router)
app.include_router(group_booking_router.router)
app.include_router(price_lock_router.router)
app.include_router(customer_memory_router.router)
app.include_router(multimodal_router.router)
app.include_router(commission_router.router)
app.include_router(fx_sentinel_router.router)
app.include_router(disruption_radar_router.router)
app.include_router(corporate_policy_router.router)
app.include_router(concierge_upsell_router.router)
app.include_router(constraints_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(resilience_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(boundaries_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(passenger_rights_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(financial_ops_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(counterfactual_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_documents_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(public_proposals_router.router)
app.include_router(journey_graph_router.public_router)
# PA-09 (2026-09-06): distribution / negotiation / crisis_ops / subagent_payouts
# were mounted with NO include-level auth dependency — subagent_payouts in
# particular is the advisor-payout (money-adjacent) surface. All four now use
# the same include-level `_auth_or_skip` dependency as the other protected
# routers in this file. Include order is otherwise preserved exactly.
app.include_router(distribution_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(negotiation_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(crisis_ops_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(visa_radar_router.router)
app.include_router(subagent_payouts_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(insurance_router.router)
# PT-09 / GM-07: every router below is agency-scoped internal tooling — none is
# public-by-design (public-by-design surfaces are auth_router, health_router,
# public_checker/public_collection/public_proposals, trust_scorecard.public_router,
# messaging/social_inbound webhook receivers, and customer_memory et al. which
# enforce get_current_agency_id in-file). Each gets the explicit per-route
# _auth_or_skip dependency so the security posture is visible at the include
# site and does not silently depend on AuthMiddleware's prefix allowlist.
app.include_router(loyalty_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(feedback_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(tax_compliance_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(epistemic_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(document_extraction_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(financial_settlement_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(group_pareto_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(proposal_compiler_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(irops_healer_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(duty_of_care_radar_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(logistics_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(charter_aviation_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(ivr_bypass_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(stress_benchmark_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(gds_sandbox_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(journey_graph_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(agent_lease_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(trip_history_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(itinerary_export_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(yield_benchmark_router.router, dependencies=[Depends(_auth_or_skip)])
app.include_router(fulfillment_router.router, dependencies=[Depends(_auth_or_skip)])


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
    except (OSError, ValueError, KeyError) as e:
        logger.error("SEED_SCENARIO: failed to load fixture: %s", e)


def _is_trip_id_integrity_conflict(exc: IntegrityError) -> bool:
    """Return True only for a duplicate ``trips.id`` insert.

    Fixture seeding runs under the requesting agency's RLS context.  A trip
    owned by another agency is therefore intentionally invisible to the
    preflight lookup, while the database primary key remains global.  Treat
    that one expected race/collision as an idempotent skip, but re-raise other
    integrity failures (for example a broken foreign key or malformed row).
    """
    original = getattr(exc, "orig", None)
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    constraint = getattr(original, "constraint_name", None)
    detail = str(getattr(original, "detail", "") or exc).lower()
    message = str(exc).lower()

    if sqlstate == "23505":  # PostgreSQL unique_violation
        return constraint in {"trips_pkey", "trip_pkey"} or "trips.id" in detail or "(id)" in detail

    # SQLite/local test backends expose the table/column in the message rather
    # than a PostgreSQL SQLSTATE.
    return "unique constraint failed: trips.id" in message


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
            
            try:
                TripStore.save_trip(trip_record, agency_id=agency_id)
            except IntegrityError as exc:
                if not _is_trip_id_integrity_conflict(exc):
                    raise
                logger.warning(
                    "Seed fixture trip %s was inserted concurrently or already "
                    "exists globally; preserving tenant ownership and skipping.",
                    trip_id,
                )
                continue
            
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
    except (OSError, ValueError, KeyError) as e:
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
            "trip_priorities",
            "date_flexibility",
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
        except (ValueError, KeyError, TypeError):
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
            # Broad catch is intentional: background thread must never crash.
            # Covers os.waitpid failures, ChildProcessError edge cases, and
            # any OS-level surprises during zombie reaping.
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


_IDEMPOTENCY_INFLIGHT_TTL_SECONDS = 1800  # 30-minute stale-reclaim window


@app.post("/run", response_model=RunAcceptedResponse)
async def run_spine(
    request: SpineRunRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
    idempotency_key_header: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        description="Optional client-supplied idempotency key (PA-13). "
        "Scopes to the authenticated agency; completed keys replay the "
        "original run, in-flight keys yield 409.",
    ),
) -> RunAcceptedResponse:
    """
    Submit a spine run and return immediately.

    This is the canonical Process Trip path. Poll GET /runs/{run_id} for
    status, checkpointed steps, events, and final trip_id.

    PA-13 (2026-09-06): when an ``Idempotency-Key`` header is present, the key
    ``(agency_id, header)`` is resolved against the durable idempotency
    registry (src/agents/idempotency.py — the same CAS machinery wired at
    routers/inbound.py). A COMPLETED record replays the original run_id;
    a PENDING record yields 409; PENDING records older than 30 minutes are
    stale-reclaimable via the registry's TTL path. Without the header the
    behavior is unchanged (fresh uuid4 per submission).
    """
    if idempotency_key_header:
        registry = IdempotencyRegistry.get_instance()
        idem_key = f"run:{agency.id}:{idempotency_key_header}"
        acquired, existing = registry.try_acquire(
            idem_key,
            trip_id="",  # trip is assigned later by the pipeline
            action_name="run_spine",
            # Include the body hash so one key cannot silently alias different
            # payloads into a replay; distinct payloads for the same key
            # remain distinguishable in the registry record.
            payload=request.model_dump(exclude_none=True),
            ttl_seconds=_IDEMPOTENCY_INFLIGHT_TTL_SECONDS,
        )
        if not acquired and existing is not None:
            if existing.status == IdempotencyStatus.COMPLETED:
                payload = existing.response_payload or {}
                return RunAcceptedResponse(
                    run_id=payload.get("run_id", ""),
                    state=payload.get("state", "completed"),
                    idempotent_replay=True,
                )
            # PENDING (in-flight, or a failed attempt pending retry per the
            # registry's FAILED->retry semantics is handled inside try_acquire).
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": "run_already_in_flight_for_idempotency_key",
                    "idempotency_key": idempotency_key_header,
                },
            )
        # acquired == True: the registry now holds this key as in-flight.
        # TODO(integrator, PA-13): record COMPLETED (registry.mark_completed
        # with the acquired fencing_token) when the run reaches its terminal
        # state — the terminal callback lives in
        # spine_api/services/pipeline_execution_service.py, owned by another
        # workstream. Until that lands, keys stay in-flight and age out of
        # replay via the 30-minute TTL reclaim above.
        run_id = str(uuid.uuid4())
        RunLedger.create(
            run_id=run_id,
            trip_id=None,
            stage=request.stage,
            operating_mode=request.operating_mode,
            agency_id=agency.id,
            draft_id=request.draft_id,
        )
        try:
            # PA-13: stash the idempotency key + fencing token into run meta so
            # the pipeline's terminal callback (pipeline_execution_service) can
            # close the registry record and replays return the original run_id.
            RunLedger.update_meta(
                run_id,
                idempotency_key=idem_key,
                idempotency_fencing_token=getattr(existing, "fencing_token", None),
            )
        except Exception as meta_err:  # enrichment is best-effort; run proceeds
            logger.warning(
                "PA-13 idempotency meta stash skipped for run %s: %s", run_id, meta_err
            )
        _launch_spine_pipeline_thread(run_id, request, agency.id, user.id)
        logger.info(
            "spine_run queued run_id=%s agency_id=%s idempotency_key=%s",
            run_id,
            agency.id,
            idempotency_key_header,
        )
        return RunAcceptedResponse(run_id=run_id, state="queued")

    run_id = str(uuid.uuid4())
    RunLedger.create(
        run_id=run_id,
        trip_id=None,
        stage=request.stage,
        operating_mode=request.operating_mode,
        agency_id=agency.id,
        draft_id=request.draft_id,
    )
    _launch_spine_pipeline_thread(run_id, request, agency.id, user.id)

    logger.info("spine_run queued run_id=%s agency_id=%s", run_id, agency.id)
    return RunAcceptedResponse(run_id=run_id, state="queued")


def _launch_spine_pipeline_thread(
    run_id: str, request: SpineRunRequest, agency_id: str, user_id: str
) -> None:
    """Start the pipeline daemon thread (shared by both /run entry paths)."""
    request_dict = request.model_dump(exclude_none=True)
    # Run pipeline in a daemon thread (not multiprocessing) to avoid
    # all file-descriptor-inheritance and lock-deadlock issues across
    # fork/spawn on macOS/Linux.
    thread = threading.Thread(
        target=_execute_spine_pipeline,
        args=(run_id, request_dict, agency_id, user_id),
        daemon=True,
        name=f"spine-{run_id[:8]}",
    )
    thread.start()


# =============================================================================
# Draft Management Endpoints (Phase 0)
# =============================================================================

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint (PA-10, 2026-09-06).

    Previously returned a static JSON body while claiming to be Prometheus.
    Now renders the real in-process registry
    (spine_api/metrics_registry.py) as Prometheus text exposition v0.0.4.
    Stays in the public auth allowlist per Prometheus convention — the
    AuthMiddleware PUBLIC_PATHS set is intentionally untouched.
    """
    from spine_api.metrics_registry import collect_runtime_gauges, render

    collect_runtime_gauges()
    return Response(
        content=render(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/trips")

async def list_trips(
    status: Optional[str] = None,
    limit: int = 100,
    agency: Agency = Depends(get_current_agency),
):
    """
    List trips for the current user's agency, optionally filtered by status.
    
    Test agencies (is_test=True) will automatically get test data seeded
    if no trips exist yet.
    """
    agency_id = agency.id
    
    # Auto-seed for test agencies if no trips exist
    if agency.is_test:
        existing_trips = await _ts(TripStore.list_trips, agency_id=agency_id)
        if not existing_trips:
            try:
                seed_count = await _ts(_seed_scenario_for_agency, agency_id)
                logger.info("Auto-seeded %d test trips for test agency %s", seed_count, agency_id)
            except (OSError, ValueError, KeyError) as e:
                logger.warning("Failed to auto-seed for test agency: %s", e)
    
    trips = await _ts(TripStore.list_trips, status=status, limit=limit, agency_id=agency_id)
    total = await _ts(TripStore.count_trips, status=status, agency_id=agency_id)
    return {"items": trips, "total": total}


@app.get("/stats")
async def trip_stats(agency: Agency = Depends(get_current_agency)):
    """Trip stats for the operator overview (F-40): the frontend `useTripStats`
    hook and its contract tests call `/api/stats`; this route makes the
    contract real. Counts use the status vocabulary writers actually emit."""
    agency_id = agency.id
    total = await _ts(TripStore.count_trips, agency_id=agency_id)
    terminal = 0
    for status_name in ("booked", "delivered", "completed", "cancelled"):
        terminal += await _ts(TripStore.count_trips, status=status_name, agency_id=agency_id)
    pending_review = await _ts(TripStore.count_trips, status="pending_review", agency_id=agency_id)
    ready_to_book = await _ts(TripStore.count_trips, status="ready_to_book", agency_id=agency_id)
    needs_attention = await _ts(
        TripStore.count_trips,
        status="blocked,incomplete,needs_followup,escalated",
        agency_id=agency_id,
    )
    return {
        "active": max(0, total - terminal),
        "pendingReview": pending_review,
        "readyToBook": ready_to_book,
        "needsAttention": needs_attention,
    }


@app.get("/trips/{trip_id}", response_model=TripResponse)
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

    return TripResponse.from_dict(trip)


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
                for index, flag in enumerate(flags_from_decision):
                    if isinstance(flag, dict):
                        stable_flag_id = uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            json.dumps(
                                {
                                    "trip_id": trip_id,
                                    "index": index,
                                    "flag_type": flag.get("flag_type", "unknown"),
                                    "severity": flag.get("severity", "low"),
                                    "reason": flag.get("reason", ""),
                                    "confidence": flag.get("confidence", 0),
                                },
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                        )
                        # Convert flag to the expected format with id, name, confidence, tier
                        suitability_flags.append({
                            "id": str(stable_flag_id),
                            "trip_id": trip_id,
                            "name": flag.get("flag_type", "unknown"),
                            "confidence": int(flag.get("confidence", 0) * 100),  # Convert 0-1 to 0-100
                            "tier": flag.get("severity", "low"),
                            "reason": flag.get("reason", ""),
                            "created_at": trip.get("created_at"),
                        })
    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Error extracting suitability flags for trip {trip_id}: {e}")
    
    return SuitabilityFlagsResponse(
        trip_id=trip_id,
        suitability_flags=suitability_flags,
    )


@app.patch("/trips/{trip_id}", response_model=TripResponse)
def patch_trip(
    trip_id: str,
    updates: TripPatchRequest,
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

    updates_dict = updates.model_dump(exclude_unset=True)

    old_status = trip.get("status")
    new_status = updates_dict.get("status")

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
        parsed = Normalizer.parse_budget(normalized)
        budget_min = parsed.get("min")
        budget_max = parsed.get("max")
        if isinstance(budget_min, (int, float)) and budget_min > 0:
            return float(budget_min)
        if isinstance(budget_max, (int, float)) and budget_max > 0:
            return float(budget_max)
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
        raw_input = _clone_json(current_trip.get("raw_input"), {}) or {}
        submission = raw_input.setdefault("submission", {})
        structured_json = _clone_json(submission.get("structured_json"), {}) or {}
        validation = _clone_json(current_trip.get("validation"), {}) or {}
        warnings = validation.get("warnings")
        warning_list = warnings if isinstance(warnings, list) else []

        fields_to_clear: set[str] = set()
        structured_overlay: Dict[str, Any] = {}

        def _set_structured_overlay(field_name: str, value: Any) -> None:
            if value is None:
                structured_overlay.pop(field_name, None)
                return
            if isinstance(value, str):
                normalized_value = value.strip()
                if not normalized_value:
                    structured_overlay.pop(field_name, None)
                    return
                structured_overlay[field_name] = normalized_value
                return
            structured_overlay[field_name] = value

        if "origin" in incoming_updates:
            origin_raw = incoming_updates.get("origin")
            origin_value = _trimmed_string(origin_raw)
            if origin_value is not None:
                facts["origin_city"] = {
                    "value": origin_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("origin", origin_value)
                _set_structured_overlay("origin_city", origin_value)
            else:
                facts.pop("origin_city", None)
                structured_overlay.pop("origin", None)
                structured_overlay.pop("origin_city", None)
            fields_to_clear.add("origin_city")

        if "budget" in incoming_updates:
            budget_raw = incoming_updates.get("budget")
            budget_text = _trimmed_string(budget_raw)
            if budget_text is not None:
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
                    _set_structured_overlay("budget", parsed_budget)
                else:
                    # Store raw text so extracted.facts.budget is always populated after PATCH.
                    # Downstream resolution via resolve_trip_field() will read this value;
                    # legacy top-level fallbacks exist for pre-fix trips until Phase 5.
                    facts["budget"] = {
                        "value": budget_text,
                        "confidence": 0.5,
                        "authority_level": "explicit_user_raw",
                    }
                    _set_structured_overlay("budget", budget_text)
            else:
                facts.pop("budget_raw_text", None)
                facts.pop("budget", None)
                structured_overlay.pop("budget", None)
            fields_to_clear.add("budget_raw_text")
            fields_to_clear.add("budget")

        if "trip_priorities" in incoming_updates:
            priorities_raw = incoming_updates.get("trip_priorities")
            priorities_value = _trimmed_string(priorities_raw)
            if priorities_value is not None:
                facts["trip_priorities"] = {
                    "value": priorities_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("trip_priorities", priorities_value)
            else:
                facts.pop("trip_priorities", None)
                structured_overlay.pop("trip_priorities", None)
            fields_to_clear.add("trip_priorities")

        if "trip_purpose" in incoming_updates:
            purpose_raw = incoming_updates.get("trip_purpose")
            purpose_value = _trimmed_string(purpose_raw)
            if purpose_value is not None:
                facts["trip_purpose"] = {
                    "value": purpose_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("trip_purpose", purpose_value)
            else:
                facts.pop("trip_purpose", None)
                structured_overlay.pop("trip_purpose", None)
            fields_to_clear.add("trip_purpose")

        if "date_flexibility" in incoming_updates:
            flexibility_raw = incoming_updates.get("date_flexibility")
            flexibility_value = _trimmed_string(flexibility_raw)
            if flexibility_value is not None:
                facts["date_flexibility"] = {
                    "value": flexibility_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("date_flexibility", flexibility_value)
            else:
                facts.pop("date_flexibility", None)
                structured_overlay.pop("date_flexibility", None)
            fields_to_clear.add("date_flexibility")

        if "date_window" in incoming_updates:
            date_window_raw = incoming_updates.get("date_window")
            dw_value = _trimmed_string(date_window_raw)
            if dw_value is not None:
                facts["date_window"] = {
                    "value": dw_value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("date_window", dw_value)
                _set_structured_overlay("dateWindow", dw_value)
            else:
                facts.pop("date_window", None)
                structured_overlay.pop("date_window", None)
                structured_overlay.pop("dateWindow", None)
            fields_to_clear.add("date_window")

        if "party_composition" in incoming_updates:
            value_raw = incoming_updates.get("party_composition")
            value = _trimmed_string(value_raw)
            if value is not None:
                facts["party_composition"] = {
                    "value": value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("party_composition", value)
            else:
                facts.pop("party_composition", None)
                structured_overlay.pop("party_composition", None)
            fields_to_clear.add("party_composition")

        if "pace_preference" in incoming_updates:
            value_raw = incoming_updates.get("pace_preference")
            value = _trimmed_string(value_raw)
            if value is not None:
                facts["pace_preference"] = {
                    "value": value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("pace_preference", value)
            else:
                facts.pop("pace_preference", None)
                structured_overlay.pop("pace_preference", None)
            fields_to_clear.add("pace_preference")

        if "date_year_confidence" in incoming_updates:
            value_raw = incoming_updates.get("date_year_confidence")
            value = _trimmed_string(value_raw)
            if value is not None:
                facts["date_year_confidence"] = {
                    "value": value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("date_year_confidence", value)
            else:
                facts.pop("date_year_confidence", None)
                structured_overlay.pop("date_year_confidence", None)
            fields_to_clear.add("date_year_confidence")

        if "lead_source" in incoming_updates:
            value_raw = incoming_updates.get("lead_source")
            value = _trimmed_string(value_raw)
            if value is not None:
                facts["lead_source"] = {
                    "value": value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("lead_source", value)
            else:
                facts.pop("lead_source", None)
                structured_overlay.pop("lead_source", None)
            fields_to_clear.add("lead_source")

        if "activity_provenance" in incoming_updates:
            value_raw = incoming_updates.get("activity_provenance")
            value = _trimmed_string(value_raw)
            if value is not None:
                facts["activity_provenance"] = {
                    "value": value,
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("activity_provenance", value)
            else:
                facts.pop("activity_provenance", None)
                structured_overlay.pop("activity_provenance", None)
            fields_to_clear.add("activity_provenance")

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
                    _set_structured_overlay("party", party_number)
                    _set_structured_overlay("party_size", party_number)
                except (ValueError, TypeError):
                    facts.pop("party_size", None)
            else:
                facts.pop("party_size", None)
                structured_overlay.pop("party", None)
                structured_overlay.pop("party_size", None)
            fields_to_clear.add("party_size")

        if "destination" in incoming_updates:
            dest_raw = incoming_updates.get("destination")
            dest_value = _trimmed_string(dest_raw)
            if dest_value is not None:
                facts["destination_candidates"] = {
                    "value": [dest_value],
                    "confidence": 1.0,
                    "authority_level": "explicit_user",
                }
                _set_structured_overlay("destination", dest_value)
                _set_structured_overlay("destination_candidates", [dest_value])
            else:
                facts.pop("destination_candidates", None)
                structured_overlay.pop("destination", None)
                structured_overlay.pop("destination_candidates", None)
            fields_to_clear.add("destination_candidates")

        if "customer_message" in incoming_updates:
            customer_message_raw = incoming_updates.get("customer_message")
            customer_message_value = _trimmed_string(customer_message_raw)
            submission["raw_note"] = customer_message_value

        if "agent_notes" in incoming_updates:
            agent_notes_raw = incoming_updates.get("agent_notes")
            agent_notes_value = _trimmed_string(agent_notes_raw)
            submission["owner_note"] = agent_notes_value

        if "contact_name" in incoming_updates:
            contact_name_raw = incoming_updates.get("contact_name")
            contact_name_value = _trimmed_string(contact_name_raw)
            if contact_name_value is not None:
                raw_input["customer_name"] = contact_name_value
            else:
                raw_input.pop("customer_name", None)
            synced_updates["raw_input"] = raw_input

        if fields_to_clear:
            validation["warnings"] = [
                warning
                for warning in warning_list
                if str((warning or {}).get("field") or "") not in fields_to_clear
            ]
            synced_updates["extracted"] = extracted
            synced_updates["validation"] = validation

        if structured_overlay:
            merged_structured_json = dict(structured_json)
            merged_structured_json.update(structured_overlay)
            submission["structured_json"] = merged_structured_json
            synced_updates["raw_input"] = raw_input
        elif "structured_json" in submission:
            submission.pop("structured_json", None)
            synced_updates["raw_input"] = raw_input

        if "customer_message" in incoming_updates or "agent_notes" in incoming_updates:
            synced_updates["raw_input"] = raw_input

        return synced_updates

    updates = _sync_manual_trip_fields(trip, updates_dict)

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

    return TripResponse.from_dict(updated_trip)


# ---------------------------------------------------------------------------
# Booking Data Models & Endpoints
# ---------------------------------------------------------------------------


class PaymentQueueItemModel(BaseModel):
    trip_id: str
    trip_name: str
    destination: Optional[str] = None
    start_date: Optional[str] = None
    status: Optional[str] = None
    queue_status: Literal[
        "not_configured",
        "unknown",
        "overdue",
        "due_soon",
        "due_later",
        "paid_complete",
        "refund_in_progress",
    ]
    payment_status: Literal[
        "not_started",
        "deposit_paid",
        "partially_paid",
        "paid",
        "overdue",
        "waived",
        "refunded",
        "unknown",
    ]
    refund_status: Literal[
        "not_applicable",
        "not_requested",
        "pending_review",
        "approved",
        "processing",
        "paid",
        "rejected",
        "cancelled",
    ]
    agreed_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    balance_due: Optional[float] = None
    currency: str = "INR"
    final_payment_due: Optional[str] = None
    payment_reference_present: bool = False
    payment_proof_url_present: bool = False
    refund_paid_by_agency: bool = False
    updated_at: Optional[str] = None


class PaymentQueueSummaryModel(BaseModel):
    total: int
    by_queue_status: dict[str, int]
    overdue_count: int
    due_soon_count: int
    not_configured_count: int
    paid_complete_count: int
    refund_in_progress_count: int
    due_within_7_days_count: int


class PaymentQueuePaginationModel(BaseModel):
    limit: int
    offset: int
    returned: int
    total: int
    has_more: bool


class PaymentQueueResponseModel(BaseModel):
    summary: PaymentQueueSummaryModel
    pagination: PaymentQueuePaginationModel
    items: list[PaymentQueueItemModel]


@app.get("/payments", response_model=PaymentQueueResponseModel)
def get_payments_queue(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    queue_status: Optional[Literal[
        "not_configured",
        "unknown",
        "overdue",
        "due_soon",
        "due_later",
        "paid_complete",
        "refund_in_progress",
    ]] = Query(None),
    payment_status: Optional[Literal[
        "not_started",
        "deposit_paid",
        "partially_paid",
        "paid",
        "overdue",
        "waived",
        "refunded",
        "unknown",
    ]] = Query(None),
    refund_status: Optional[Literal[
        "not_applicable",
        "not_requested",
        "pending_review",
        "approved",
        "processing",
        "paid",
        "rejected",
        "cancelled",
    ]] = Query(None),
    due_bucket: Optional[Literal["none", "overdue", "due_0_3", "due_4_7", "due_8_14"]] = Query(None),
    agency: Agency = Depends(get_current_agency),
):
    return build_payment_queue_response_for_agency(
        agency_id=agency.id,
        limit=limit,
        offset=offset,
        queue_status=queue_status,
        payment_status=payment_status,
        refund_status=refund_status,
        due_bucket=due_bucket,
    )


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
    final_payment_due: Optional[str] = None

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

    @field_validator("final_payment_due")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        from datetime import date
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("must be a valid ISO date (YYYY-MM-DD)")
        return v

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
    user: User = Depends(get_current_user),
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

    # Backend split: traveler endpoint owns travelers/payer/notes only.
    # Preserve existing payment_tracking from storage so payment edits
    # via the dedicated /booking-data/payment endpoint are never overwritten.
    existing_bd = TripStore.get_booking_data_for_agency(trip_id, agency.id) or {}
    bd_dict["payment_tracking"] = existing_bd.get("payment_tracking")

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
    AuditStore.log_event("booking_data_updated", user.id, {
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
            ]
            if f is not None
        ],
        "traveler_count": len(request.booking_data.travelers),
        "has_passport_data": any(t.passport_number for t in request.booking_data.travelers),
        "has_payer": request.booking_data.payer is not None,
        "actor": "operator",
        "actor_user_id": user.id,
    })

    booking_data = TripStore.get_booking_data_for_agency(trip_id, agency.id)
    return _booking_data_envelope(updated, booking_data)


class PaymentTrackingUpdateRequest(BaseModel):
    payment_tracking: PaymentTrackingModel
    expected_updated_at: Optional[str] = None


@app.patch("/trips/{trip_id}/booking-data/payment")
def update_payment_tracking(
    trip_id: str,
    request: PaymentTrackingUpdateRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    """Update payment tracking only. Preserves travelers/payer/notes unchanged.

    Read-merge-write: fetches current booking data, replaces only payment_tracking,
    writes back atomically with the same trip-level optimistic lock.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    current_stage = trip.get("stage", "discovery")
    if current_stage not in ("proposal", "booking"):
        raise HTTPException(
            status_code=403,
            detail=f"Booking data can only be updated at proposal/booking stage, current: {current_stage}",
        )

    # Read-merge-write: preserve all non-payment fields from current storage
    existing_bd = TripStore.get_booking_data_for_agency(trip_id, agency.id) or {}
    bd_dict = dict(existing_bd)
    bd_dict["payment_tracking"] = request.payment_tracking.model_dump()

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
                "message": "Payment tracking conflict",
                "expected_updated_at": expected,
                "actual_updated_at": actual,
            },
        )

    AuditStore.log_event("payment_tracking_updated", user.id, {
        "trip_id": trip_id,
        "stage": current_stage,
        "payment_status": request.payment_tracking.payment_status,
        "refund_status": request.payment_tracking.refund_status,
        "has_payment_reference": bool(request.payment_tracking.payment_reference),
        "has_payment_proof_url": bool(request.payment_tracking.payment_proof_url),
        "has_final_payment_due": request.payment_tracking.final_payment_due is not None,
        "actor": "operator",
        "actor_user_id": user.id,
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
    collection_url: Optional[str] = None  # Only set for active, non-expired tokens
    expires_at: Optional[str] = None
    status: Optional[str] = None
    has_pending_submission: bool


# secrets.token_urlsafe(32) produces URL-safe base64 characters: letters, digits,
# hyphen, underscore. Nothing else. Whitelist-validate to prevent garbage ciphertext
# or injected path characters from reaching URL assembly.
_COLLECTION_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")


def _safe_collection_plain_token(blob: Optional[dict]) -> Optional[str]:
    """Decrypt and validate a plain_token_encrypted blob.

    Returns the plain token string only if it matches the expected token_urlsafe
    character set and length. Rejects on any decryption failure, wrong type,
    or characters outside [A-Za-z0-9_-] (which rules out ?, #, &, %, =, :,
    slashes, whitespace, and everything else that could alter URL semantics).
    """
    if not blob:
        return None
    try:
        from spine_api.services.private_fields import decrypt_field
        token = decrypt_field(blob)
    except (ValueError, TypeError, OSError):
        return None
    if not isinstance(token, str):
        return None
    if not _COLLECTION_TOKEN_RE.fullmatch(token):
        return None
    return token


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
        # DEBUG
        _ctx = await db.execute(text("SELECT current_setting('app.current_agency_id', TRUE)"))
        _trip_row = await db.execute(text("SELECT id, agency_id FROM trips WHERE id = :trip_id"), {"trip_id": trip_id})
        _trip_data = _trip_row.fetchone()
        print(f"DEBUG collection-link: trip_id={trip_id} agency.id={agency.id} rls_ctx={_ctx.scalar()} trip_row={_trip_data}")
        # END DEBUG
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
    """Check collection link status, pending submission, and re-expose active URL.

    Returns collection_url for authenticated agency operators when a valid active
    token exists. The plain token is decrypted from plain_token_encrypted and the
    URL is assembled from the current PUBLIC_COLLECTION_BASE_URL at read time.

    collection_url is None when: no active token, token is expired/revoked/used,
    plain_token_encrypted is null (pre-migration rows), or decryption fails.
    """
    from spine_api.services.collection_service import get_active_token_for_trip

    trip = await _ts(TripStore.get_trip_for_agency, trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    async with rls_session(agency.id) as db:
        token = await get_active_token_for_trip(db, trip_id)
    pending = await _ts(TripStore.get_pending_booking_data_for_agency, trip_id, agency.id)

    # Assemble collection_url from encrypted plain token (authenticated only).
    # Never logged; never returned from public endpoints.
    collection_url = None
    if token:
        plain = _safe_collection_plain_token(token.plain_token_encrypted)
        if plain:
            base_url = os.getenv("PUBLIC_COLLECTION_BASE_URL", "")
            path = f"/api/public/booking-collection/{agency.id}/{plain}"
            collection_url = f"{base_url}{path}" if base_url else path

    return CollectionLinkStatusResponse(
        has_active_token=token is not None,
        token_id=token.id if token else None,
        collection_url=collection_url,
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
    existing_bd = await _ts(TripStore.get_booking_data_for_agency, trip_id, agency.id) or {}
    existing_payment_tracking = existing_bd.get("payment_tracking")
    if existing_payment_tracking is not None:
        bd_dict["payment_tracking"] = existing_payment_tracking

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


# Note: All Document and Extraction endpoints are modularized in spine_api.routers.trip_documents



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
