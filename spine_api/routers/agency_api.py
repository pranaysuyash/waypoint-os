"""Agency-facing agent/MCP API (R2-A tranche, 2026-11-04).

Read-only, provenance-gated surface for external agency integrations. Every
response carries the BD provenance envelope (license_tier / as_of / sources)
per the 2026-10-30 adjudication: a consumer can always tell what tier of
data it received and when it was observed. Timatic-tier and other
credential-gated data NEVER flows through this surface.

Auth: per-agency API key (X-API-Key) — NOT the operator JWT. See
``spine_api/core/api_key_auth.py`` for the key/RLS posture.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from spine_api.core.api_key_auth import (
    get_agency_api_key,
    issue_agency_api_key,
    revoke_agency_api_key,
)
from spine_api.core.auth import get_current_agency
from spine_api.persistence import AuditStore, TripStore
from spine_api.services.commercial_agreement import project_commercial_pricing

router = APIRouter(prefix="/api/v1/agency-api", tags=["Agency API (external)"])

# License tiers a public/agency surface may serve. Anything credential-gated
# (e.g. Timatic travel-rule rows) is excluded by construction — it cannot be
# produced without the credential gate, and the envelope refuses to claim it.
_SERVABLE_LICENSE_TIER = "agency_internal"


def _envelope(data: Dict[str, Any], sources: list) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "license_tier": _SERVABLE_LICENSE_TIER,
        "as_of": now,
        "sources": sources,
        "data": data,
    }


class IssueKeyRequest(BaseModel):
    label: str = ""


class IssueKeyResponse(BaseModel):
    key_id: str
    api_key: str  # plaintext — returned exactly once, never stored


@router.post("/keys", response_model=IssueKeyResponse)
async def create_api_key(
    body: IssueKeyRequest,
    agency=Depends(get_current_agency),
):
    """Mint an agency API key (operator JWT session required).

    The plaintext key is shown ONCE in this response; only its hash is
    stored. Revocation is immediate on the next lookup."""
    result = await issue_agency_api_key(agency.id, label=body.label)
    AuditStore.log_event(
        event_type="agency_api_key_issued",
        user_id=agency.id,
        details={"key_id": result["key_id"], "label": (body.label or "")[:120]},
    )
    return IssueKeyResponse(**result)


@router.delete("/keys/{key_id}")
async def revoke_key(
    key_id: str,
    agency=Depends(get_current_agency),
):
    """Revoke an agency API key (operator JWT session required)."""
    revoked = await revoke_agency_api_key(agency.id, key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Key not found for this agency")
    AuditStore.log_event(
        event_type="agency_api_key_revoked",
        user_id=agency.id,
        details={"key_id": key_id},
    )
    return {"ok": True, "key_id": key_id, "revoked": True}


@router.get("/trips/{trip_id}/summary")
async def get_trip_summary(
    trip_id: str,
    agency_id: str = Depends(get_agency_api_key),
):
    """Trip summary for external agent consumption — provenance-gated.

    Serves ONLY agency-internal tier data: trip basics + canonical facts
    (de-PII'd: customer identity fields withheld) + quote preview when
    pricing is ready. Sources and as_of travel with every response."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    facts = ((trip.get("extracted") or {}).get("facts") or {})
    safe_facts = {
        name: slot.get("value")
        for name, slot in facts.items()
        if isinstance(slot, dict)
        and name not in {"customer_name", "customer_contact", "customer_email", "customer_phone"}
        and slot.get("value") is not None
    }

    commercial = project_commercial_pricing(trip, agency_id)
    quote: Optional[Dict[str, Any]] = None
    if commercial is not None and commercial.ready:
        quote = {
            "currency": commercial.currency,
            "net_cost": commercial.net_cost,
            "net_cost_basis": "persisted_modeled_cost",
            "retail_price": commercial.retail_price,
            "retail_basis": commercial.retail_basis,
        }

    data = {
        "trip_id": str(trip.get("id") or trip_id),
        "destination": trip.get("destination"),
        "stage": trip.get("stage"),
        "facts": safe_facts,
        "quote_preview": quote,
    }
    sources = [
        {"kind": "trip_store", "as_of": datetime.now(timezone.utc).isoformat()},
    ]
    if quote is not None:
        sources.append({"kind": "commercial_pricing_projection", "as_of": sources[0]["as_of"]})

    AuditStore.log_event(
        event_type="agency_api_trip_summary_served",
        user_id=agency_id,
        details={"trip_id": trip_id},
    )
    return _envelope(data, sources)
