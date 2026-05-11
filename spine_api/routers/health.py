"""
Health router — liveness/version endpoint extraction from server.py.

Scope: move GET /health only.
"""

from __future__ import annotations

from fastapi import APIRouter

from spine_api.contract import HealthResponse
from spine_api.version import APP_VERSION

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
