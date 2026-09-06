"""
Luxury Itinerary Export API Router.

Provides endpoints for rendering standalone HTML and print-ready luxury itineraries.
"""

from __future__ import annotations

from typing import Dict, List
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from src.compilers.itinerary_export_engine import (
    LuxuryItineraryExportEngine,
    ExportDocumentPayload,
    ItineraryDayItem,
)

router = APIRouter(prefix="/api/v1/trips", tags=["itinerary-export"])


class DayInput(BaseModel):
    day_number: int
    date_str: str
    title: str
    location: str
    description: str
    vouchers: List[str] = Field(default_factory=list)
    meal_plan: str = "Breakfast Included"
    dress_code: str | None = None


class CompileItineraryRequest(BaseModel):
    client_name: str = "Alex & Taylor Morgan"
    destination_title: str = "10-Day Japan Cultural Immersion"
    travel_dates: str = "April 10 - April 20, 2027"
    total_cost_usd: float = 14500.0
    allergies: List[str] = Field(default_factory=lambda: ["Peanut allergy (Leo)"])
    emergency_contact: str = "+1 (800) 555-WAYPOINT"
    days: List[DayInput] = Field(default_factory=list)
    vouchers: Dict[str, str] = Field(default_factory=dict)


@router.post("/{trip_id}/export/html")
def export_trip_itinerary_html(trip_id: str, payload: CompileItineraryRequest) -> Response:
    """Renders standalone luxury print-ready HTML document."""
    day_items = [
        ItineraryDayItem(
            day_number=d.day_number,
            date_str=d.date_str,
            title=d.title,
            location=d.location,
            description=d.description,
            vouchers=d.vouchers,
            meal_plan=d.meal_plan,
            dress_code=d.dress_code,
        )
        for d in payload.days
    ]

    doc_payload = ExportDocumentPayload(
        trip_id=trip_id,
        client_name=payload.client_name,
        destination_title=payload.destination_title,
        travel_dates=payload.travel_dates,
        total_cost_usd=payload.total_cost_usd,
        allergies=payload.allergies,
        emergency_contact=payload.emergency_contact,
        days=day_items,
        vouchers=payload.vouchers,
    )

    html_content = LuxuryItineraryExportEngine.compile_html(doc_payload)
    return Response(content=html_content, media_type="text/html")
