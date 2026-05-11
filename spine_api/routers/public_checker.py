from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from spine_api.contract import PublicCheckerDeleteResponse, PublicCheckerExportResponse
from spine_api.core.auth import get_current_agency, get_current_user
from spine_api.models.tenant import Agency, User
from spine_api.core.rate_limiter import limiter
from spine_api.product_b_events import ProductBEventStore

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.public_checker")

router = APIRouter()

PUBLIC_CHECKER_EVENT_MAX_BYTES = 16 * 1024


class PublicCheckerEventEnvelope(BaseModel):
    event_name: str
    event_version: int = 1
    event_id: Optional[str] = None
    occurred_at: Optional[str] = None
    session_id: str
    inquiry_id: str
    trip_id: Optional[str] = None
    actor_type: str
    actor_id: Optional[str] = None
    workspace_id: Optional[str] = None
    channel: str
    locale: Optional[str] = None
    currency: Optional[str] = None
    properties: Dict[str, Any]


@router.post("/api/public-checker/events")
@limiter.limit("30/minute")
def post_public_checker_event(
    request: Request,
    response: Response,
    event: PublicCheckerEventEnvelope,
):
    payload = event.model_dump(exclude_none=False)
    payload_size = len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    if payload_size > PUBLIC_CHECKER_EVENT_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Event payload too large")

    if not payload.get("event_id"):
        payload["event_id"] = str(uuid.uuid4())
    if not payload.get("occurred_at"):
        payload["occurred_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = ProductBEventStore.log_event(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("public_checker_event_write_failed error=%s", exc)
        raise HTTPException(status_code=500, detail="Could not record event")

    _ = (request, response)
    return {"ok": True, **result}


@router.get("/api/public-checker/{trip_id}", response_model=PublicCheckerExportResponse)
def get_public_checker_package(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    _ = (agency, user)
    package = persistence.PublicCheckerArtifactStore.export_trip_package(trip_id)
    if not package:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return package


@router.get("/api/public-checker/{trip_id}/export", response_model=PublicCheckerExportResponse)
def export_public_checker_package(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    _ = (agency, user)
    package = persistence.PublicCheckerArtifactStore.export_trip_package(trip_id)
    if not package:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return package


@router.delete("/api/public-checker/{trip_id}", response_model=PublicCheckerDeleteResponse)
def delete_public_checker_package(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
):
    _ = (agency, user)
    deleted_artifacts = persistence.PublicCheckerArtifactStore.delete_trip_artifacts(trip_id)
    deleted_trip = persistence.TripStore.delete_trip(trip_id)
    if not deleted_artifacts and not deleted_trip:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return {
        "ok": True,
        "trip_id": trip_id,
        "deleted_trip": deleted_trip,
        "deleted_artifacts": deleted_artifacts,
    }
