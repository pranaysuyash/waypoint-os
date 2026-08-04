"""
spine_api/routers/supplier.py — DMC & Preferred Supplier Wholesale Contract Router.

First-principles implementation:
  - Requires JWT authentication on all endpoints
  - Scopes contract storage and inventory holds per agency
  - No hardcoded demo contract fallbacks (unknown contracts return 404)
  - Computes net/rack totals and agency margin from real uploaded rate sheets
  - Includes reality tier metadata (DATA_DEPENDENT)

Endpoints:
  POST /api/v1/supplier/contracts/upload — Ingest wholesale rate sheets
  POST /api/v1/supplier/inventory/soft-hold — Reserve 48h zero-cost hold on contract inventory
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore

logger = logging.getLogger("spine_api.supplier")

router = APIRouter(prefix="/api/v1/supplier", tags=["DMC & Supplier Inventory"])

# Agency-scoped in-memory stores: {agency_id: {contract_id: contract_data}}
CONTRACTS_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}
HOLDS_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}


class RateTableItem(BaseModel):
    room_type: str
    net_rate_per_night: float
    rack_rate_per_night: float
    season_start: Optional[str] = None
    season_end: Optional[str] = None
    cancellation_lead_days: Optional[int] = 7


class ContractUploadRequest(BaseModel):
    supplier_name: str = Field(..., description="Supplier / DMC company name")
    destination: str = Field(..., description="Destination covered by contract")
    contact_email: Optional[str] = Field(None, description="Contract manager contact email")
    currency: str = Field("USD", description="Currency code")
    rate_table: List[RateTableItem] = Field(..., description="List of room types and rates")
    terms_and_conditions: Optional[str] = Field(None, description="Cancellation / payment terms")


class ContractUploadResponse(BaseModel):
    contract_id: str
    supplier_name: str
    destination: str
    total_rates_ingested: int
    uploaded_at: str
    status: str


class SoftHoldRequest(BaseModel):
    contract_id: str = Field(..., description="Contract ID to hold inventory against")
    room_type: str = Field(..., description="Room type")
    check_in: str = Field(..., description="Check-in date YYYY-MM-DD")
    check_out: str = Field(..., description="Check-out date YYYY-MM-DD")
    guest_name: str = Field(..., description="Traveler / guest name")
    agent_id: Optional[str] = Field("agent_default", description="Requesting agent ID")


class SoftHoldResponse(BaseModel):
    hold_id: str
    contract_id: str
    supplier_name: str
    room_type: str
    net_rate_total: float
    rack_rate_total: float
    estimated_agency_margin: float
    expires_at: str
    status: str


@router.post("/contracts/upload", response_model=ContractUploadResponse)
async def upload_supplier_contract(
    req: ContractUploadRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Ingest a DMC or preferred supplier wholesale rate sheet for the requesting agency.
    """
    if not req.rate_table:
        raise HTTPException(status_code=400, detail="rate_table cannot be empty")

    contract_id = f"contract_{uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    rate_table_dicts = [r.model_dump() for r in req.rate_table]

    contract_record = {
        "contract_id": contract_id,
        "agency_id": agency_id,
        "supplier_name": req.supplier_name,
        "destination": req.destination,
        "contact_email": req.contact_email,
        "currency": req.currency,
        "rate_table": rate_table_dicts,
        "terms_and_conditions": req.terms_and_conditions,
        "uploaded_at": now_iso,
        "status": "ACTIVE",
    }

    if agency_id not in CONTRACTS_STORE:
        CONTRACTS_STORE[agency_id] = {}
    CONTRACTS_STORE[agency_id][contract_id] = contract_record

    AuditStore.log_event(
        event_type="supplier_contract_uploaded",
        user_id=agency_id,
        details={
            "contract_id": contract_id,
            "supplier_name": req.supplier_name,
            "destination": req.destination,
            "rates_count": len(req.rate_table),
        },
    )

    return ContractUploadResponse(
        contract_id=contract_id,
        supplier_name=req.supplier_name,
        destination=req.destination,
        total_rates_ingested=len(req.rate_table),
        uploaded_at=now_iso,
        status="ACTIVE",
    )


@router.post("/inventory/soft-hold", response_model=SoftHoldResponse)
async def create_inventory_soft_hold(
    req: SoftHoldRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Reserve a 48-hour zero-cost soft hold on contract inventory for the requesting agency.
    """
    agency_contracts = CONTRACTS_STORE.get(agency_id, {})
    contract = agency_contracts.get(req.contract_id)

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract '{req.contract_id}' not found for agency",
        )

    # Find matching rate in contract
    rate_item = None
    for r in contract.get("rate_table", []):
        if r.get("room_type", "").lower() == req.room_type.lower():
            rate_item = r
            break

    if not rate_item:
        raise HTTPException(
            status_code=400,
            detail=f"Room type '{req.room_type}' not found in contract '{req.contract_id}'",
        )

    try:
        d1 = datetime.strptime(req.check_in, "%Y-%m-%d")
        d2 = datetime.strptime(req.check_out, "%Y-%m-%d")
        nights = max((d2 - d1).days, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format for check_in or check_out (use YYYY-MM-DD)")

    net_per_night = float(rate_item.get("net_rate_per_night", 0.0))
    rack_per_night = float(rate_item.get("rack_rate_per_night", 0.0))

    net_total = round(net_per_night * nights, 2)
    rack_total = round(rack_per_night * nights, 2)
    agency_margin = round(rack_total - net_total, 2)

    hold_id = f"hold_{uuid4().hex[:10]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()

    hold_record = {
        "hold_id": hold_id,
        "agency_id": agency_id,
        "contract_id": req.contract_id,
        "supplier_name": contract.get("supplier_name"),
        "room_type": req.room_type,
        "guest_name": req.guest_name,
        "check_in": req.check_in,
        "check_out": req.check_out,
        "net_rate_total": net_total,
        "rack_rate_total": rack_total,
        "estimated_agency_margin": agency_margin,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "status": "SOFT_HOLD_ACTIVE",
    }

    if agency_id not in HOLDS_STORE:
        HOLDS_STORE[agency_id] = {}
    HOLDS_STORE[agency_id][hold_id] = hold_record

    AuditStore.log_event(
        event_type="supplier_inventory_soft_hold",
        user_id=agency_id,
        details={
            "hold_id": hold_id,
            "contract_id": req.contract_id,
            "guest_name": req.guest_name,
            "expires_at": expires_at,
        },
    )

    return SoftHoldResponse(
        hold_id=hold_id,
        contract_id=req.contract_id,
        supplier_name=contract.get("supplier_name", "Supplier"),
        room_type=req.room_type,
        net_rate_total=net_total,
        rack_rate_total=rack_total,
        estimated_agency_margin=agency_margin,
        expires_at=expires_at,
        status="SOFT_HOLD_ACTIVE",
    )
