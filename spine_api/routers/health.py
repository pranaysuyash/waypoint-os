"""
Health router — liveness/version endpoint extraction from server.py.

Scope: move GET /health only.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from alembic.config import Config
from alembic.script import ScriptDirectory

from spine_api.contract import HealthResponse
from spine_api.version import APP_VERSION
from spine_api.core.database import engine

router = APIRouter()

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _expected_migration_heads() -> tuple[str, ...]:
    """Return the migration heads shipped with this application artifact."""
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    heads = tuple(script.get_heads())
    if len(heads) != 1:
        raise RuntimeError("application migration graph must have exactly one head")
    return heads


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        from src.decision.health import health_check_dict

        health_status = health_check_dict()
        components = health_status.get("components") or {}
        issues = health_status.get("issues") or []
        overall = "ok" if not any(c.get("healthy") is False for c in components.values() if isinstance(c, dict)) else "degraded"
        return HealthResponse(
            status=overall,
            version=APP_VERSION,
            components=components,
            issues=issues,
        )
    except Exception as exc:
        return HealthResponse(status="degraded", version=APP_VERSION, issues=[f"health_probe_error: {exc}"])


@router.get("/ready")
async def ready(response: Response):
    """
    Readiness probe for zero-downtime deployment ingress.
    Checks database connectivity and core subsystems.
    """
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        # Do not expose connection strings or driver errors from a public probe.
        checks["database"] = "failed"

    # A migrated SQL database is a runtime invariant, not merely a reachable
    # socket. The table check is intentionally separate so operators can see
    # whether a release was deployed before its migration.
    if checks["database"] == "ok":
        try:
            expected_heads = _expected_migration_heads()
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version ORDER BY version_num")
                )
                versions = tuple(result.scalars().all())
                checks["migrations"] = (
                    "ok"
                    if len(versions) == 1 and versions[0] in expected_heads
                    else "failed"
                )
        except Exception:
            checks["migrations"] = "failed"
    else:
        checks["migrations"] = "blocked"

    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        try:
            from redis.asyncio import from_url

            client = from_url(redis_url, decode_responses=True)
            try:
                await client.ping()
            finally:
                await client.aclose()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "failed"
    else:
        # Development/test can intentionally run without shared Redis; the
        # startup assertion rejects this topology in staging/production.
        checks["redis"] = "not_configured"

    required = {"database", "migrations"}
    if redis_url or os.environ.get("ENVIRONMENT", "development").strip().lower() in {"production", "staging"}:
        required.add("redis")
    ready = all(checks.get(name) == "ok" for name in required)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "version": APP_VERSION,
            "checks": checks,
        }

    return {
        "status": "ready",
        "version": APP_VERSION,
        "checks": checks,
    }
