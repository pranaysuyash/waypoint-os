"""
Booking Fulfillment API Router (PER-FULFILL-OPS).

Provides endpoints to execute accepted proposals into supplier commitments:
VCC generation, GDS PNR creation, and Journey Dependency Graph node minting.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.orchestration.booking_fulfillment import BookingFulfillmentEngine

router = APIRouter(prefix="/api/v1/fulfillment", tags=["fulfillment"])


class FulfillProposalRequest(BaseModel):
    trip_id: str = Field(..., description="Unique trip identifier")
    proposal_token: str = Field(..., description="Cryptographically signed proposal capability token")
    holder_id: str = Field("fulfillment_advisor", description="Agent or advisor executing fulfillment")


@router.post("/proposals/fulfill")
async def fulfill_proposal(payload: FulfillProposalRequest) -> Dict[str, Any]:
    """Execute accepted client proposal into confirmed supplier bookings and VCC settlement."""
    try:
        result = await BookingFulfillmentEngine.fulfill_accepted_proposal(
            trip_id=payload.trip_id,
            proposal_token=payload.proposal_token,
            holder_id=payload.holder_id,
        )
        return {
            "status": "success",
            "fulfillment": result.to_dict(),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fulfillment error: {exc}",
        )
