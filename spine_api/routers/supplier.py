"""
spine_api/routers/supplier.py — DMC & Preferred Supplier Wholesale Contract Router.

First-principles implementation:
  - Requires JWT authentication on all endpoints
  - Scopes contract storage and inventory holds per agency
  - Persists operator-recorded contracts & holds in local SQLite across restarts
  - No hardcoded demo contract fallbacks (unknown contracts return 404)
  - Computes net/rack totals and agency margin from uploaded rate sheets
  - Includes reality tier metadata (DP-04a live provider feed not connected)

Endpoints:
  GET  /api/v1/supplier/contracts — List agency-recorded wholesale contracts
  POST /api/v1/supplier/contracts/upload — Ingest wholesale rate sheets
  GET  /api/v1/supplier/inventory/holds — List agency-recorded soft holds
  POST /api/v1/supplier/inventory/soft-hold — Reserve 48h zero-cost hold on contract inventory
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency_id, require_permission
from spine_api.core.feature_gates import get_feature_tier
from spine_api.core.reality_tier import TierMetadata
from spine_api.persistence import AuditStore
from spine_api.services import supplier_evidence

logger = logging.getLogger("spine_api.supplier")

router = APIRouter(prefix="/api/v1/supplier", tags=["DMC & Supplier Inventory"])

# Agency-scoped stores: {agency_id: {contract_id: contract_data}}
CONTRACTS_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}
HOLDS_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}

_DB_LOCK = threading.Lock()
_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "suppliers" / "supplier_ledger.db"


def _sqlite_enabled() -> bool:
    return "PYTEST_CURRENT_TEST" not in os.environ


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS supplier_contracts (
            contract_id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS supplier_inventory_holds (
            hold_id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_sc_agency_id ON supplier_contracts (agency_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS ix_sh_agency_id ON supplier_inventory_holds (agency_id)"
    )


def _persist_contract_record(record: Dict[str, Any]) -> None:
    if not _sqlite_enabled():
        return
    with _DB_LOCK:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(_DB_PATH) as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO supplier_contracts (contract_id, agency_id, uploaded_at, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    record["contract_id"],
                    record["agency_id"],
                    record["uploaded_at"],
                    json.dumps(record),
                ),
            )
            conn.commit()


def _persist_hold_record(record: Dict[str, Any]) -> None:
    if not _sqlite_enabled():
        return
    with _DB_LOCK:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(_DB_PATH) as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO supplier_inventory_holds (hold_id, agency_id, created_at, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    record["hold_id"],
                    record["agency_id"],
                    record["created_at"],
                    json.dumps(record),
                ),
            )
            conn.commit()


def _hydrate_stores_from_sqlite() -> None:
    if not _sqlite_enabled() or not _DB_PATH.exists():
        return
    with _DB_LOCK:
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                _ensure_tables(conn)
                for row in conn.execute("SELECT payload_json FROM supplier_contracts ORDER BY uploaded_at DESC"):
                    record = json.loads(row[0])
                    CONTRACTS_STORE.setdefault(record["agency_id"], {})[record["contract_id"]] = record
                for row in conn.execute("SELECT payload_json FROM supplier_inventory_holds ORDER BY created_at DESC"):
                    record = json.loads(row[0])
                    HOLDS_STORE.setdefault(record["agency_id"], {})[record["hold_id"]] = record
        except Exception as exc:
            logger.warning("Failed hydrating supplier ledger from SQLite: %s", exc)


_hydrate_stores_from_sqlite()


class RateTableItem(BaseModel):
    room_type: str
    net_rate_per_night: float
    rack_rate_per_night: float
    season_start: Optional[str] = None
    season_end: Optional[str] = None
    cancellation_lead_days: Optional[int] = 7


class ContractUploadRequest(BaseModel):
    supplier_name: str = Field(..., description="Supplier / DMC company name")
    supplier_category: str = Field("dmc", description="Supplier category (dmc, hotel, airline, rail_charter, transfer, safari, insurance)")
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
    _meta: Optional[Dict[str, Any]] = None


class SupplierContractsListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    _meta: Optional[Dict[str, Any]] = None


class SupplierHoldsListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    _meta: Optional[Dict[str, Any]] = None


@router.get("/availability/evidence")
def get_supplier_availability_evidence(
    service_date: date,
    supplier_id: str = Query(min_length=1, max_length=96),
    service_id: str = Query(min_length=1, max_length=96),
    guests: int = Query(ge=1, le=10_000),
    staff=require_permission("trips:write"),
) -> dict:
    """Return source-linked rate and availability observations for staff review."""
    return supplier_evidence.lookup(
        os.getenv("WAYPOINT_SUPPLIER_EVIDENCE_FILE", "").strip(),
        staff.agency_id, supplier_id, service_id, service_date, guests,
    )


@router.get("/contracts")
async def list_supplier_contracts(
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """List agency-recorded supplier/DMC rate-sheet contracts (oldest-safe, newest first)."""
    records = list(CONTRACTS_STORE.get(agency_id, {}).values())
    records.sort(key=lambda r: str(r.get("uploaded_at") or ""), reverse=True)
    return {
        "items": records,
        "total": len(records),
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_management"),
            "supplier_management",
            computation_method="operator_recorded_contract_ledger",
            missing_for_upgrade=["dp04a_provider_feed"],
        ),
    }


@router.get("/inventory/holds")
async def list_inventory_soft_holds(
    agency_id: str = Depends(get_current_agency_id),
) -> Dict[str, Any]:
    """List agency-recorded 48-hour inventory soft holds (newest first)."""
    records = list(HOLDS_STORE.get(agency_id, {}).values())
    records.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return {
        "items": records,
        "total": len(records),
        "_meta": TierMetadata.for_response(
            get_feature_tier("supplier_management"),
            "supplier_management",
            computation_method="stored_contract_rate_hold",
            missing_for_upgrade=["supplier_hold_gds_api"],
        ),
    }


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
        "supplier_category": (req.supplier_category or "dmc").strip().lower(),
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
    _persist_contract_record(contract_record)

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
    _persist_hold_record(hold_record)

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
        _meta=TierMetadata.for_response(
            get_feature_tier("supplier_management"),
            "supplier_management",
            computation_method="stored_contract_rate_hold",
            missing_for_upgrade=["supplier_hold_gds_api"],
        ),
    )
