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
from spine_api.services.agency_marketplace import (
    AgencyMarketplaceStore,
    derive_brief_needs,
    match_agencies_for_needs,
    valid_contact,
)
from spine_api.services.live_checker_service import apply_live_checker_adjustments
from src.public_checker.entity_checks import run_entity_checks
from src.public_checker.live_checks import build_live_checker_signals, extract_destination

try:
    from spine_api import persistence
except (ImportError, ValueError):
    import persistence

logger = logging.getLogger("spine_api.public_checker")

router = APIRouter()

PUBLIC_CHECKER_EVENT_MAX_BYTES = 16 * 1024
DEFAULT_PUBLIC_CHECKER_AGENCY_ID = "__UNSET__"


def public_checker_enabled() -> bool:
    """Runtime kill switch (RDA-2026-09-08 FT-05).

    Read at call time so tests and operators can toggle without a reload.
    Set PUBLIC_CHECKER_ENABLED=0 (or "false") to return 503 on every public
    checker surface — run, events, result fetch, export, and delete.
    """
    return os.environ.get("PUBLIC_CHECKER_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _require_public_checker_enabled() -> None:
    if not public_checker_enabled():
        raise HTTPException(
            status_code=503,
            detail="Public checker temporarily disabled",
        )


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
    public_checker_agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
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


def _validate_structure_depth(data: Any, current_depth: int = 0, max_depth: int = 10) -> None:
    """Security (S-07): Prevent recursion stack exhaustion on untrusted structured payloads."""
    if current_depth > max_depth:
        raise HTTPException(status_code=400, detail=f"Structured JSON nesting exceeds maximum allowed depth ({max_depth})")
    if isinstance(data, dict):
        for val in data.values():
            _validate_structure_depth(val, current_depth + 1, max_depth)
    elif isinstance(data, (list, tuple)):
        for item in data:
            _validate_structure_depth(item, current_depth + 1, max_depth)


@router.post("/api/public-checker/events")
@limiter.limit("30/minute")
def post_public_checker_event(
    request: Request,
    response: Response,
    event: PublicCheckerEventEnvelope,
):
    _require_public_checker_enabled()
    # Gate 0 (WOBS P1): check_completed is the sealed funnel-completion counter,
    # emitted only by the run service after the trip row is persisted. The
    # client-fed events endpoint must never accept it.
    if event.event_name == "check_completed":
        raise HTTPException(status_code=403, detail="check_completed is server-emitted only")
    payload = event.model_dump(exclude_none=False)
    payload_size = len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    if payload_size > PUBLIC_CHECKER_EVENT_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Event payload too large")

    # Security (S-07): Recursion depth validation on untrusted properties
    _validate_structure_depth(event.properties)

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


@router.post("/api/public-checker/matches")
@limiter.limit("12/minute")
def post_public_checker_matches(
    request: Request,
    response: Response,
    body: Dict[str, Any],
):
    """Matched-choice marketplace close (WOBS P2).

    Returns the top matched agencies for a stored brief. Works at any supply
    level: an empty match list is the demand-capture signal, never a dead end.
    Derived needs only — raw text and consented artifacts are never returned.
    """
    _require_public_checker_enabled()
    trip_id = str(body.get("trip_id") or "").strip()
    if not trip_id:
        raise HTTPException(status_code=422, detail="trip_id is required")
    _load_public_checker_package_or_404(trip_id)

    trip = persistence.TripStore.get_trip_for_agency(
        trip_id, os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
    ) or {}
    packet = trip.get("packet") if isinstance(trip.get("packet"), dict) else {}
    decision = trip.get("decision") if isinstance(trip.get("decision"), dict) else {}
    blocker_texts = [
        *(decision.get("hard_blockers") or []),
        *(decision.get("soft_blockers") or []),
    ]
    needs = derive_brief_needs(packet, [str(item) for item in blocker_texts])
    matches = match_agencies_for_needs(needs, AgencyMarketplaceStore.list_profiles())
    _ = (request, response)
    return {
        "trip_id": trip_id,
        "needs": needs,
        "matches": [match.as_dict() for match in matches],
    }


@router.post("/api/public-checker/route-request")
@limiter.limit("6/minute")
def post_public_checker_route_request(
    request: Request,
    response: Response,
    body: Dict[str, Any],
):
    """Consented route request / demand capture (WOBS P2).

    The consent moment IS the product: a user who opts in here has performed
    the highest-intent action on the surface. With a matched agency_id the
    lead is 'routed'; without one it is 'captured' (waitlist recruits supply).
    """
    _require_public_checker_enabled()
    trip_id = str(body.get("trip_id") or "").strip()
    contact = str(body.get("contact") or "").strip()
    agency_id = str(body.get("agency_id") or "").strip() or None
    if body.get("consent") is not True:
        raise HTTPException(status_code=422, detail="Explicit consent is required")
    if not trip_id:
        raise HTTPException(status_code=422, detail="trip_id is required")
    if not valid_contact(contact):
        raise HTTPException(status_code=422, detail="A valid email or phone number is required")

    _load_public_checker_package_or_404(trip_id)
    trip = persistence.TripStore.get_trip_for_agency(
        trip_id, os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
    ) or {}
    packet = trip.get("packet") if isinstance(trip.get("packet"), dict) else {}
    decision = trip.get("decision") if isinstance(trip.get("decision"), dict) else {}
    needs = derive_brief_needs(
        packet,
        [str(item) for item in (decision.get("hard_blockers") or []) + (decision.get("soft_blockers") or [])],
    )
    record = AgencyMarketplaceStore.capture_route_lead(
        trip_id=trip_id, contact=contact, agency_id=agency_id, needs=needs
    )
    _ = (request, response)
    return {"ok": True, "lead_id": record["lead_id"], "status": record["status"]}


@router.post("/api/public-checker/re-verify")
@limiter.limit("6/minute")
def post_public_checker_re_verify(
    request: Request,
    response: Response,
    body: Dict[str, Any],
):
    """On-demand re-verification (WOBS P3 v0): "what would the check say now?".

    Read-only: recomputes live climate/safety signals and advisory entity
    checks against the STORED packet and returns a fresh score preview. Never
    mutates the stored trip — report versioning waits for exposure (WOBS P3).
    Fail-open on provider outage.
    """
    _require_public_checker_enabled()
    trip_id = str(body.get("trip_id") or "").strip()
    if not trip_id:
        raise HTTPException(status_code=422, detail="trip_id is required")
    _load_public_checker_package_or_404(trip_id)

    trip = persistence.TripStore.get_trip_for_agency(
        trip_id, os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
    ) or {}
    packet = trip.get("packet") if isinstance(trip.get("packet"), dict) else {}
    validation = trip.get("validation") if isinstance(trip.get("validation"), dict) else {}
    decision = trip.get("decision") if isinstance(trip.get("decision"), dict) else {}

    fresh_score = validation.get("overall_score")
    live_checks_payload = None
    try:
        live = build_live_checker_signals(packet, "")
        if live:
            _, fresh_validation, _ = apply_live_checker_adjustments(
                packet_payload=dict(packet),
                validation_payload=dict(validation),
                decision_payload=dict(decision),
                live_checker=live,
            )
            fresh_score = fresh_validation.get("overall_score")
            live_checks_payload = fresh_validation.get("public_checker_live_checks")
    except Exception:
        live_checks_payload = None

    try:
        entity_results = run_entity_checks(
            "", city=extract_destination(packet, ""), max_entities=3
        )
        entity_checks_payload = [item.as_dict() for item in entity_results]
    except Exception:
        entity_checks_payload = []

    checked_at = datetime.now(timezone.utc).isoformat()
    _ = (request, response)
    return {
        "trip_id": trip_id,
        "refreshed": True,
        "checked_at": checked_at,
        "overall_score_preview": fresh_score,
        "live_checks": live_checks_payload,
        "entity_checks": entity_checks_payload,
    }


@router.get("/api/public-checker/{trip_id}", response_model=PublicCheckerExportResponse)
@limiter.limit("30/minute")
def get_public_checker_package(
    request: Request,
    trip_id: str,
):
    _require_public_checker_enabled()
    return _load_public_checker_package_or_404(trip_id)


@router.get("/api/public-checker/{trip_id}/export", response_model=PublicCheckerExportResponse)
@limiter.limit("30/minute")
def export_public_checker_package(
    request: Request,
    trip_id: str,
):
    _require_public_checker_enabled()
    return _load_public_checker_package_or_404(trip_id)


@router.delete("/api/public-checker/{trip_id}", response_model=PublicCheckerDeleteResponse)
@limiter.limit("30/minute")
def delete_public_checker_package(
    request: Request,
    trip_id: str,
):
    _require_public_checker_enabled()
    _package = _load_public_checker_package_or_404(trip_id)
    public_checker_agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", DEFAULT_PUBLIC_CHECKER_AGENCY_ID)
    deleted_artifacts = persistence.PublicCheckerArtifactStore.delete_trip_artifacts(trip_id)
    deleted_trip = persistence.TripStore.delete_trip_for_agency(trip_id, public_checker_agency_id)
    if not deleted_artifacts and not deleted_trip:
        raise HTTPException(status_code=404, detail="Public checker record not found")
    return {
        "ok": True,
        "trip_id": trip_id,
        "deleted_trip": deleted_trip,
        "deleted_artifacts": deleted_artifacts,
    }
