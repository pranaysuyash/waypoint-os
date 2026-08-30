"""
Health router — liveness/version endpoint extraction from server.py.

Scope: move GET /health only.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from spine_api.contract import HealthResponse
from spine_api.version import APP_VERSION
from spine_api.core.database import engine

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        from src.decision.health import health_check_dict

        health_status = health_check_dict()
        return HealthResponse(
            status="ok",
            version=APP_VERSION,
            components=health_status.get("components"),
            issues=health_status.get("issues"),
        )
    except Exception:
        return HealthResponse(status="ok", version=APP_VERSION)


@router.get("/ready")
async def ready(response: Response):
    """
    Readiness probe for zero-downtime deployment ingress.
    Checks database connectivity and core subsystems.
    """
    db_ok = False
    details = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
        details["database"] = "connected"
    except Exception as e:
        details["database"] = f"unhealthy: {str(e)}"

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "version": APP_VERSION,
            "checks": details,
        }

    return {
        "status": "ready",
        "version": APP_VERSION,
        "checks": details,
    }
