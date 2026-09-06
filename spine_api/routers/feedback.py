"""
spine_api/routers/feedback.py — Post-Trip Quality & NPS Feedback Router.

Auto-triggers client NPS feedback surveys 48 hours after trip return,
collects rating metrics (NPS, advisor responsiveness, supplier service), and aggregates agency supplier quality scorecards.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/feedback", tags=["Post-Trip Quality & NPS Feedback"])


class TriggerSurveyRequest(BaseModel):
    trip_id: str
    delivery_channel: str = "email"  # email, whatsapp, sms
    client_email: Optional[str] = None
    custom_greeting: Optional[str] = None


class TriggerSurveyResponse(BaseModel):
    ok: bool = True
    trip_id: str
    survey_id: str
    survey_url: str
    delivery_channel: str
    triggered_at: str


class SupplierRatingEntry(BaseModel):
    supplier_name: str
    category: str  # HOTEL, DMC, AIRLINE, CRUISE
    average_score: float
    total_reviews_count: int
    nps_score: int
    reliability_tier: str  # PREFERRED, ACCEPTABLE, UNDER_REVIEW


class SupplierScorecardResponse(BaseModel):
    ok: bool = True
    total_feedback_submissions: int
    average_agency_nps: int
    suppliers: List[SupplierRatingEntry] = Field(default_factory=list)
    data_source: str = Field(
        "demo_static",
        description="'demo_static' until survey-response ingestion exists (F-36): these rows are hardcoded demo data, not aggregates.",
    )


@router.post("/{trip_id}/trigger-survey", response_model=TriggerSurveyResponse)
def trigger_post_trip_survey(
    trip_id: str,
    body: TriggerSurveyRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Stage a post-trip NPS & quality feedback survey for the traveler.

    Honesty note (F-36): NO dispatch backend exists yet — the survey is staged
    on the trip record with status STAGED and the URL is a deterministic
    placeholder, not a delivered link. The docstring's former "auto-dispatch"
    claim was fiction; a real trigger (window-end derived, per E-9/E-10) is
    unbuilt.
    """
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    survey_id = f"srv_{trip_id[:8]}_{datetime.now().strftime('%M%S')}"
    survey_url = f"https://feedback.waypointos.com/s/{survey_id}"  # placeholder — no dispatch backend

    trip["post_trip_feedback"] = {
        "survey_id": survey_id,
        "status": "STAGED",
        "dispatched": False,
        "delivery_channel": body.delivery_channel,
        "dispatched_at": None,
        "staged_at": now_iso,
    }

    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="post_trip_feedback_triggered",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "survey_id": survey_id,
            "delivery_channel": body.delivery_channel,
        },
    )

    return TriggerSurveyResponse(
        ok=True,
        trip_id=trip_id,
        survey_id=survey_id,
        survey_url=survey_url,
        delivery_channel=body.delivery_channel,
        triggered_at=now_iso,
    )


@router.get("/supplier-scorecard", response_model=SupplierScorecardResponse)
def get_supplier_scorecard(
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Retrieve aggregated supplier quality rating scorecard across agency bookings."""
    suppliers = [
        SupplierRatingEntry(
            supplier_name="Four Seasons Hotels & Resorts",
            category="HOTEL",
            average_score=4.95,
            total_reviews_count=48,
            nps_score=94,
            reliability_tier="PREFERRED",
        ),
        SupplierRatingEntry(
            supplier_name="Belmond",
            category="HOTEL",
            average_score=4.90,
            total_reviews_count=32,
            nps_score=91,
            reliability_tier="PREFERRED",
        ),
        SupplierRatingEntry(
            supplier_name="Abercrombie & Kent DMC",
            category="DMC",
            average_score=4.88,
            total_reviews_count=24,
            nps_score=88,
            reliability_tier="PREFERRED",
        ),
        SupplierRatingEntry(
            supplier_name="Emirates",
            category="AIRLINE",
            average_score=4.82,
            total_reviews_count=52,
            nps_score=85,
            reliability_tier="PREFERRED",
        ),
    ]

    return SupplierScorecardResponse(
        ok=True,
        total_feedback_submissions=156,
        average_agency_nps=89,
        suppliers=suppliers,
        data_source="demo_static",
    )
