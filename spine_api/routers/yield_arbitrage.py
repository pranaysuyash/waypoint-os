"""
spine_api/routers/yield_arbitrage.py — Yield & Commission Arbitrage Engine for Travel Agencies.

First-principles implementation:
  - Requires JWT authentication on all endpoints
  - Scopes trip access via TripStore.get_trip_for_agency
  - Integrates with real uploaded supplier contracts when present
  - No hardcoded trip_demo123 defaults
  - Includes reality tier metadata (DATA_DEPENDENT)

Endpoints:
  GET  /api/v1/yield/arbitrage/{trip_id} — Compare supplier options by commission yield
  GET  /api/v1/yield/opportunities — Scan active proposals for yield optimization
  POST /api/v1/yield/swap-supplier — Select preferred supplier option for a trip
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.contract import SupplierOption, YieldArbitrageResponse
from spine_api.core.auth import get_current_agency_id
from spine_api.core.feature_gates import get_feature_tier
from spine_api.core.reality_tier import TierMetadata
from spine_api.persistence import AuditStore, TripStore
from spine_api.routers.supplier import CONTRACTS_STORE

logger = logging.getLogger("spine_api.yield_arbitrage")

router = APIRouter(prefix="/api/v1/yield", tags=["yield_arbitrage"])


class SupplierSwapRequest(BaseModel):
    trip_id: str = Field(..., description="Trip ID to update")
    supplier_name: str = Field(..., description="Selected supplier option name")


@router.get("/arbitrage/{trip_id}", response_model=YieldArbitrageResponse)
async def compute_yield_arbitrage(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Compute supplier commission arbitrage and net margin highlights for a trip.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    packet = trip.get("packet", {}) or {}
    budget_max = float(packet.get("budget_max") or 5000.0)
    base = budget_max * 0.85

    # Check for real supplier contracts for this agency
    agency_contracts = CONTRACTS_STORE.get(agency_id, {})

    supplier_options: List[SupplierOption] = []

    if agency_contracts:
        for c_id, contract in agency_contracts.items():
            s_name = contract.get("supplier_name", "Uploaded Contract")
            rate_table = contract.get("rate_table", [])
            rate = rate_table[0] if rate_table else {}
            net_rate = float(rate.get("net_rate_per_night", 300.0))
            rack_rate = float(rate.get("rack_rate_per_night", 450.0))
            margin = max(rack_rate - net_rate, 50.0)
            comm_pct = round((margin / rack_rate) * 100.0, 1) if rack_rate > 0 else 15.0

            supplier_options.append(
                SupplierOption(
                    supplier_name=f"{s_name} (Direct Contract)",
                    supplier_type="direct_contract",
                    base_cost=round(net_rate * 5, 2),
                    commission_pct=comm_pct,
                    net_margin=round(margin * 5, 2),
                    bonus_override_eligible=True,
                    suitability_score=95.0,
                )
            )

    # Standard channel comparisons if needed
    if not supplier_options:
        supplier_options = [
            SupplierOption(
                supplier_name="Direct Preferred Resort Contract (Estimated)",
                supplier_type="direct_contract",
                base_cost=round(base, 2),
                commission_pct=18.0,
                net_margin=round(base * 0.18, 2),
                bonus_override_eligible=True,
                suitability_score=95.0,
            ),
            SupplierOption(
                supplier_name="GDS Preferred Channel (Estimated)",
                supplier_type="gds",
                base_cost=round(base * 0.95, 2),
                commission_pct=12.0,
                net_margin=round(base * 0.95 * 0.12, 2),
                bonus_override_eligible=False,
                suitability_score=90.0,
            ),
            SupplierOption(
                supplier_name="Wholesaler Channel (Estimated)",
                supplier_type="bedbank",
                base_cost=round(base * 0.90, 2),
                commission_pct=10.0,
                net_margin=round(base * 0.90 * 0.10, 2),
                bonus_override_eligible=False,
                suitability_score=85.0,
            ),
        ]

    sorted_options = sorted(supplier_options, key=lambda x: x.net_margin, reverse=True)
    optimal = sorted_options[0]
    worst = sorted_options[-1]
    potential_margin_gain = round(optimal.net_margin - worst.net_margin, 2)

    return YieldArbitrageResponse(
        ok=True,
        trip_id=trip_id,
        supplier_options=sorted_options,
        optimal_supplier=optimal.supplier_name,
        potential_margin_gain=potential_margin_gain,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/opportunities", response_model=YieldArbitrageResponse)
async def list_global_yield_opportunities(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Scans supplier rates for a specified active proposal to surface high-margin opportunities.
    """
    return await compute_yield_arbitrage(trip_id=trip_id, agency_id=agency_id)


@router.post("/swap-supplier")
async def swap_supplier_option(
    body: SupplierSwapRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """
    Apply a 1-click supplier swap to maximize commission yield on a trip.
    """
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip["selected_supplier"] = body.supplier_name
    trip["yield_optimized"] = True
    trip["updated_at"] = datetime.now(timezone.utc).isoformat()
    TripStore.save_trip(trip)

    AuditStore.log_event(
        event_type="supplier_swapped_yield_optimized",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "selected_supplier": body.supplier_name,
        },
    )

    return {
        "ok": True,
        "trip_id": body.trip_id,
        "selected_supplier": body.supplier_name,
        "message": f"Supplier successfully swapped to {body.supplier_name}. Commission yield locked.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "_meta": TierMetadata.for_response(
            get_feature_tier("yield_arbitrage"),
            "yield_arbitrage",
            missing_for_upgrade=["gds_live_rate_api"],
        ),
    }
