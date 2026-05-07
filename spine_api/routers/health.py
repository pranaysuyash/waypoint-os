"""
Health router — liveness/version endpoint extraction from server.py.

Scope: move GET /health only.
"""

from __future__ import annotations

from fastapi import APIRouter

from spine_api.contract import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
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
