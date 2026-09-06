"""
Private Aviation & Charter API Router (PER-AV-CHARTER).

Provides endpoints for private jet pricing, runway distance feasibility,
empty-leg arbitrage discovery, and FBO handling.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.charter.aviation_engine import PrivateAviationEngine

router = APIRouter(prefix="/api/v1/charter-aviation", tags=["charter-aviation"])


class CharterQuoteRequest(BaseModel):
    origin_icao: str = Field("KTEB", description="Origin airport ICAO code (e.g. KTEB, EGLF)")
    destination_icao: str = Field("KOPF", description="Destination airport ICAO code (e.g. KOPF, LFPB)")
    passengers_count: int = Field(4, description="Number of passengers")
    distance_nm: Optional[int] = Field(None, description="Optional flight distance in nautical miles")


@router.post("/quotes/calculate")
def calculate_charter_quote(payload: CharterQuoteRequest) -> Dict[str, Any]:
    """Calculates private aviation quote, aircraft selection, and empty-leg matches."""
    quote = PrivateAviationEngine.calculate_charter_quote(
        origin_icao=payload.origin_icao,
        destination_icao=payload.destination_icao,
        passengers_count=payload.passengers_count,
        distance_nm=payload.distance_nm,
    )
    return {
        "status": "success",
        "quote": quote.to_dict(),
    }


@router.get("/empty-legs/available")
def get_available_empty_legs() -> Dict[str, Any]:
    """Returns all currently indexed empty-leg repositioning flights."""
    legs = PrivateAviationEngine.list_available_empty_legs()
    return {
        "status": "success",
        "empty_legs": [leg.to_dict() for leg in legs],
    }
