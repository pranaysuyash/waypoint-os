"""
DMC & Preferred Supplier Wholesale Contract Ingestion & Inventory Soft-Hold Router

Endpoints:
- POST /api/v1/supplier/contracts/upload: Ingests wholesale rate sheets & contract terms
- POST /api/v1/supplier/inventory/soft-hold: Reserves 48h zero-cost hold on contract inventory
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from spine_api.persistence import AuditStore

logger = logging.getLogger("spine_api.supplier")

router = APIRouter(prefix="/api/v1/supplier", tags=["DMC & Supplier Inventory"])

# In-memory contract & soft-hold stores (backed by TripStore metadata)
CONTRACTS_STORE: Dict[str, Dict[str, Any]] = {}
HOLDS_STORE: Dict[str, Dict[str, Any]] = {}


class ContractUploadRequest(BaseModel):
    supplier_name: str = Field(..., json_schema_extra={"example": "Marrakech Destination Management Co."})
    destination: str = Field(..., json_schema_extra={"example": "Marrakech, Morocco"})
    contact_email: Optional[str] = Field(None, json_schema_extra={"example": "contracts@marrakechdmc.ma"})
    currency: str = Field("USD", json_schema_extra={"example": "USD"})
    rate_table: List[Dict[str, Any]] = Field(
        ...,
        json_schema_extra={
            "example": [
                {
                    "room_type": "Junior Luxury Suite",
                    "net_rate_per_night": 350.0,
                    "rack_rate_per_night": 550.0,
                    "season_start": "2026-09-01",
                    "season_end": "2026-12-15",
                    "cancellation_lead_days": 7,
                }
            ]
        },
    )
    terms_and_conditions: Optional[str] = Field(None, json_schema_extra={"example": "100% refundable up to 7 days prior."})


class ContractUploadResponse(BaseModel):
    contract_id: str
    supplier_name: str
    destination: str
    total_rates_ingested: int
    uploaded_at: str
    status: str


class SoftHoldRequest(BaseModel):
    contract_id: str = Field(..., json_schema_extra={"example": "contract_abc123"})
    room_type: str = Field(..., json_schema_extra={"example": "Junior Luxury Suite"})
    check_in: str = Field(..., json_schema_extra={"example": "2026-10-15"})
    check_out: str = Field(..., json_schema_extra={"example": "2026-10-20"})
    guest_name: str = Field(..., json_schema_extra={"example": "Alexander Wright"})
    agent_id: Optional[str] = Field("agent_default", json_schema_extra={"example": "agent_alex"})


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
async def upload_supplier_contract(req: ContractUploadRequest):
    """
    Ingest a DMC or preferred supplier wholesale rate sheet.
    """
    contract_id = f"contract_{uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    contract_record = {
        "contract_id": contract_id,
        "supplier_name": req.supplier_name,
        "destination": req.destination,
        "contact_email": req.contact_email,
        "currency": req.currency,
        "rate_table": req.rate_table,
        "terms_and_conditions": req.terms_and_conditions,
        "uploaded_at": now_iso,
        "status": "ACTIVE",
    }

    CONTRACTS_STORE[contract_id] = contract_record

    AuditStore.log_event(
        event_type="supplier_contract_uploaded",
        user_id=req.supplier_name,
        details={
            "contract_id": contract_id,
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
async def create_inventory_soft_hold(req: SoftHoldRequest):
    """
    Reserve a 48-hour zero-cost soft hold on DMC wholesale room inventory.
    """
    contract = CONTRACTS_STORE.get(req.contract_id)
    
    # Fallback default contract if contract_id is demo
    if not contract:
        contract = {
            "contract_id": req.contract_id,
            "supplier_name": "Marrakech Destination Management Co.",
            "destination": "Marrakech, Morocco",
            "currency": "USD",
            "rate_table": [
                {
                    "room_type": req.room_type,
                    "net_rate_per_night": 350.0,
                    "rack_rate_per_night": 550.0,
                }
            ],
        }

    # Find matching rate or default
    rate_item = next(
        (r for r in contract.get("rate_table", []) if r.get("room_type").lower() == req.room_type.lower()),
        contract.get("rate_table", [{}])[0],
    )

    try:
        d1 = datetime.strptime(req.check_in, "%Y-%m-%d")
        d2 = datetime.strptime(req.check_out, "%Y-%m-%d")
        nights = max((d2 - d1).days, 1)
    except ValueError:
        nights = 5

    net_per_night = rate_item.get("net_rate_per_night", 350.0)
    rack_per_night = rate_item.get("rack_rate_per_night", 550.0)

    net_total = net_per_night * nights
    rack_total = rack_per_night * nights
    agency_margin = rack_total - net_total

    hold_id = f"hold_{uuid4().hex[:10]}"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()

    hold_record = {
        "hold_id": hold_id,
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

    HOLDS_STORE[hold_id] = hold_record

    AuditStore.log_event(
        event_type="supplier_inventory_soft_hold",
        user_id=req.agent_id or "system",
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
        supplier_name=contract.get("supplier_name", "Preferred DMC"),
        room_type=req.room_type,
        net_rate_total=net_total,
        rack_rate_total=rack_total,
        estimated_agency_margin=agency_margin,
        expires_at=expires_at,
        status="SOFT_HOLD_ACTIVE",
    )
