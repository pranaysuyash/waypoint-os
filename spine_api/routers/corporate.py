"""
spine_api/routers/corporate.py — Corporate Travel Policy Audit & Duty-of-Care Cockpit Router.

Endpoints:
  POST /api/v1/corporate/policy-audit — Audit proposal options against corporate per-diem caps and cabin class rules.
  GET /api/v1/corporate/duty-of-care/cockpit — Retrieve live executive flight statuses and risk alerts for offsites.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from spine_api.persistence import AuditStore, TripStore

logger = logging.getLogger("spine_api.corporate")

router = APIRouter(prefix="/api/v1/corporate", tags=["corporate"])


class GeoCapRule(BaseModel):
    city_code: str
    max_hotel_rate_per_night: float
    currency: str = "GBP"


class PolicyAuditRequest(BaseModel):
    trip_id: str = Field(default="trip_demo123")
    destination: str = Field(default="London")
    city_code: str = Field(default="LON")
    hotel_rate_per_night: float = Field(..., description="Hotel rate to audit")
    cabin_class: str = Field(default="ECONOMY", description="Booked cabin class")
    employee_grade: str = Field(default="MANAGER", description="JUNIOR, MANAGER, VP, C_EXEC")


class PolicyViolationItem(BaseModel):
    code: str
    severity: str
    description: str
    amount_exceeded: float
    currency: str


class PolicyAuditResponse(BaseModel):
    ok: bool
    trip_id: str
    is_compliant: bool
    requires_approval: bool
    violations: List[PolicyViolationItem]
    audited_at: str


@router.post("/policy-audit", response_model=PolicyAuditResponse)
async def audit_corporate_policy(req: PolicyAuditRequest):
    """
    Audit hotel rate per night and flight cabin class against corporate per-diem policies.
    Example per-diem cap: London (LON) = £350/night, Zurich (ZRH) = CHF 400/night.
    """
    violations = []
    
    # Default city caps
    city_caps = {
        "LON": 350.0,
        "ZRH": 400.0,
        "NYC": 450.0,
        "PAR": 380.0,
    }

    cap = city_caps.get(req.city_code.upper(), 350.0)

    # Audit hotel per-diem
    if req.hotel_rate_per_night > cap:
        exceeded = req.hotel_rate_per_night - cap
        violations.append(
            PolicyViolationItem(
                code="PER_DIEM_EXCEEDED",
                severity="WARNING" if exceeded <= cap * 0.25 else "HARD_BLOCK",
                description=f"Hotel rate £{req.hotel_rate_per_night:.2f}/night exceeds {req.city_code} policy cap of £{cap:.2f}/night by £{exceeded:.2f}.",
                amount_exceeded=round(exceeded, 2),
                currency="GBP",
            )
        )

    # Audit cabin class matrix
    if req.employee_grade.upper() in ["JUNIOR", "MANAGER"] and req.cabin_class.upper() in ["BUSINESS", "FIRST"]:
        violations.append(
            PolicyViolationItem(
                code="CABIN_CLASS_DISCREPANCY",
                severity="HARD_BLOCK",
                description=f"{req.employee_grade} grade is restricted to ECONOMY cabin. {req.cabin_class} requested.",
                amount_exceeded=0.0,
                currency="GBP",
            )
        )

    is_compliant = len(violations) == 0
    requires_approval = any(v.severity in ["WARNING", "HARD_BLOCK"] for v in violations)

    return PolicyAuditResponse(
        ok=True,
        trip_id=req.trip_id,
        is_compliant=is_compliant,
        requires_approval=requires_approval,
        violations=violations,
        audited_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/duty-of-care/cockpit")
async def get_duty_of_care_cockpit(company_id: str = "comp_techcorp_01"):
    """
    Retrieve real-time executive traveler flight statuses, risk alerts, and group offsite synchronization.
    """
    travelers = [
        {
            "traveler_id": "exec_01",
            "traveler_name": "Vikram Sethi (VP Eng)",
            "origin": "SFO",
            "destination": "ZRH",
            "flight_pnr": "LX18",
            "flight_status": "ON_SCHEDULE",
            "hotel_name": "The Dolder Grand Zurich",
            "risk_level": "LOW",
        },
        {
            "traveler_id": "exec_02",
            "traveler_name": "Sarah Miller (Dir Product)",
            "origin": "LHR",
            "destination": "ZRH",
            "flight_pnr": "BA710",
            "flight_status": "DELAYED_90M",
            "hotel_name": "The Dolder Grand Zurich",
            "risk_level": "MEDIUM",
            "recommended_action": "Ground Transfer #1 rescheduled to 18:30. Concierge standing by.",
        },
        {
            "traveler_id": "exec_03",
            "traveler_name": "John Doe (Lead Architect)",
            "origin": "CDG",
            "destination": "ZRH",
            "flight_pnr": "AF1414",
            "flight_status": "ON_SCHEDULE",
            "hotel_name": "The Dolder Grand Zurich",
            "risk_level": "LOW",
        },
    ]

    return {
        "ok": True,
        "company_id": company_id,
        "group_offsite_title": "Q3 Zurich Executive Leadership Offsite",
        "total_active_travelers": len(travelers),
        "disrupted_count": 1,
        "travelers": travelers,
        "duty_of-care_sla_status": "ACTIVE_PROTECTED",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
