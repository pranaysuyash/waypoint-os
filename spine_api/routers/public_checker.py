from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response

from spine_api.contract import PublicCheckerDeleteResponse, PublicCheckerExportResponse
from spine_api.core.rate_limiter import limiter
from spine_api.product_b_events import ProductBEventStore

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.public_checker")

router = APIRouter()

PUBLIC_CHECKER_EVENT_MAX_BYTES = 16 * 1024
DEFAULT_PUBLIC_CHECKER_AGENCY_ID = "__UNSET__"


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


def _load_public_checker_package_or_404(trip_id: str) -> dict[str, Any]:
    trip = persistence.TripStore.get_trip(trip_id)
    if not trip:
        public_checker_agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
        if public_checker_agency_id and public_checker_agency_id != DEFAULT_PUBLIC_CHECKER_AGENCY_ID:
            trip = persistence.TripStore.get_trip_for_agency(trip_id, public_checker_agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Public checker record not found")

    artifact_manifest = persistence.PublicCheckerArtifactStore.get_trip_artifacts(trip_id)
    trip_source = str(trip.get("source") or "")
    has_public_checker_artifacts = artifact_manifest is not None

    if trip_source != "public_checker" and not has_public_checker_artifacts:
        raise HTTPException(status_code=404, detail="Public checker record not found")

    return {
        "trip_id": trip_id,
        "trip": trip,
        "artifact_manifest": artifact_manifest,
    }


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
):
    return _load_public_checker_package_or_404(trip_id)


@router.get("/api/public-checker/{trip_id}/export", response_model=PublicCheckerExportResponse)
def export_public_checker_package(
    trip_id: str,
):
    return _load_public_checker_package_or_404(trip_id)


@router.delete("/api/public-checker/{trip_id}", response_model=PublicCheckerDeleteResponse)
def delete_public_checker_package(
    trip_id: str,
):
    package = _load_public_checker_package_or_404(trip_id)
    trip = package.get("trip") or {}
    deleted_artifacts = persistence.PublicCheckerArtifactStore.delete_trip_artifacts(trip_id)
    trip_agency_id = trip.get("agency_id")
    if isinstance(trip_agency_id, str) and trip_agency_id.strip():
        deleted_trip = persistence.TripStore.delete_trip_for_agency(trip_id, trip_agency_id)
    else:
        deleted_trip = persistence.TripStore.delete_trip(trip_id)
    if not deleted_artifacts and not deleted_trip:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return {
        "ok": True,
        "trip_id": trip_id,
        "deleted_trip": deleted_trip,
        "deleted_artifacts": deleted_artifacts,
    }
