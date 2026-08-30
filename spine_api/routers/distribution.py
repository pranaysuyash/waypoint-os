"""
Distribution & GDS/NDC API Router (PER-950887, PER-950895, PER-0967).

Provides REST endpoints for GDS EDIFACT terminal parsing, NDC 21.3 order
management, and ATPCO Cat 16/35 fare rules evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.distribution.edifact_parser import EDIFACTParser
from src.distribution.ndc_client import NDCProtocolEngine
from src.distribution.fare_rules_engine import FareRulesEngine

router = APIRouter(prefix="/api/v1/distribution", tags=["distribution"])


class ParseEdifactRequest(BaseModel):
    raw_terminal_dump: str = Field(..., description="Raw Amadeus or Sabre terminal string")
    pcc: str = Field("NYC1A0982", description="Agency Pseudo City Code")


class GenerateCrypticsRequest(BaseModel):
    pax_names: List[str] = Field(..., description="Passenger names list")
    segments: List[Dict[str, str]] = Field(..., description="Flight segments info")
    ticketing_limit: str = Field("30SEP", description="Ticketing time limit string")


class AirShoppingRequest(BaseModel):
    origin: str = Field(..., description="Origin airport 3-letter IATA code")
    destination: str = Field(..., description="Destination airport 3-letter IATA code")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    passengers_count: int = Field(1, description="Number of passengers")
    cabin_preference: str = Field("BUSINESS", description="Cabin preference (ECONOMY, BUSINESS, FIRST)")


class OrderCreateRequest(BaseModel):
    offer_id: str
    airline_code: str
    passengers: List[str]
    segments: List[Dict[str, Any]]
    total_amount: float
    currency: str = "USD"


class FareRuleCheckRequest(BaseModel):
    fare_basis: str
    is_departure_passed: bool = False
    is_no_show: bool = False


class Cat35MarkupRequest(BaseModel):
    net_fare: float
    agency_markup_percent: float
    contract_code: str = "CORP-WP-2026"


@router.post("/gds/parse-edifact")
def parse_gds_terminal_dump(payload: ParseEdifactRequest) -> Dict[str, Any]:
    """Parses raw GDS terminal output into structured GDSPNRRecord."""
    record = EDIFACTParser.parse_amadeus_dump(payload.raw_terminal_dump, pcc=payload.pcc)
    return {
        "status": "success",
        "pnr": record.to_dict(),
    }


@router.post("/gds/generate-cryptics")
def generate_gds_cryptic_commands(payload: GenerateCrypticsRequest) -> Dict[str, Any]:
    """Generates standard Amadeus/Sabre cryptic commands."""
    commands = EDIFACTParser.generate_booking_cryptics(
        pax_names=payload.pax_names,
        segments=payload.segments,
        ticketing_limit=payload.ticketing_limit,
    )
    return {
        "status": "success",
        "commands": commands,
        "command_count": len(commands),
    }


@router.post("/ndc/air-shopping")
def request_ndc_air_shopping(payload: AirShoppingRequest) -> Dict[str, Any]:
    """Builds IATA NDC 21.3 AirShopping message payload."""
    req = NDCProtocolEngine.create_air_shopping_request(
        origin=payload.origin,
        destination=payload.destination,
        departure_date=payload.departure_date,
        passengers_count=payload.passengers_count,
        cabin_preference=payload.cabin_preference,
    )
    return {
        "status": "success",
        "ndc_payload": req,
    }


@router.post("/ndc/orders/create")
def create_ndc_order(payload: OrderCreateRequest) -> Dict[str, Any]:
    """Creates a confirmed IATA NDC 21.3 Order."""
    order = NDCProtocolEngine.execute_order_create(
        offer_id=payload.offer_id,
        airline_code=payload.airline_code,
        passengers=payload.passengers,
        segments=payload.segments,
        total_amount=payload.total_amount,
        currency=payload.currency,
    )
    return {
        "status": "success",
        "order": order.to_dict(),
    }


@router.post("/fare-rules/penalties")
def check_fare_penalties(payload: FareRuleCheckRequest) -> Dict[str, Any]:
    """Evaluates ATPCO Category 16 change/cancellation penalties."""
    res = FareRulesEngine.evaluate_penalties(
        fare_basis=payload.fare_basis,
        is_departure_passed=payload.is_departure_passed,
        is_no_show=payload.is_no_show,
    )
    return {
        "status": "success",
        "evaluation": res,
    }


@router.post("/fare-rules/cat35-markup")
def evaluate_cat35_markup(payload: Cat35MarkupRequest) -> Dict[str, Any]:
    """Evaluates ATPCO Category 35 net fare markup limits to prevent ADMs."""
    res = FareRulesEngine.evaluate_cat35_negotiated_markup(
        net_fare=payload.net_fare,
        agency_markup_percent=payload.agency_markup_percent,
        contract_code=payload.contract_code,
    )
    return {
        "status": "success",
        "cat35_evaluation": res,
    }
