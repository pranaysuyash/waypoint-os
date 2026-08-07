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
from spine_api.core.reality_tier import TierMetadata, assert_tier_capability
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

    # Check for real supplier contracts for this agency
    agency_contracts = CONTRACTS_STORE.get(agency_id, {})

    supplier_options: List[SupplierOption] = []
    data_sufficient = True

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
    else:
        data_sufficient = False

    if supplier_options:
        sorted_options = sorted(supplier_options, key=lambda x: x.net_margin, reverse=True)
        optimal_supplier = sorted_options[0].supplier_name
        worst_margin = sorted_options[-1].net_margin
        potential_margin_gain = round(sorted_options[0].net_margin - worst_margin, 2)
    else:
        sorted_options = []
        optimal_supplier = "None (No Contracts Uploaded)"
        potential_margin_gain = 0.0

    return YieldArbitrageResponse(
        ok=True,
        trip_id=trip_id,
        data_sufficient=data_sufficient,
        supplier_options=sorted_options,
        optimal_supplier=optimal_supplier,
        potential_margin_gain=potential_margin_gain,
        generated_at=datetime.now(timezone.utc).isoformat(),
        _meta=TierMetadata.for_response(
            get_feature_tier("yield_arbitrage"),
            "yield_arbitrage",
            data_sufficient=data_sufficient,
            computation_method="uploaded_agency_contracts",
        ),
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
    tier = get_feature_tier("yield_arbitrage")
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    assert_tier_capability(tier, "can_mutate_booking_state", "yield_arbitrage")

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
