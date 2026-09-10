"""
spine_api/routers/feedback.py — Post-Trip Quality & NPS Feedback Router.

Auto-triggers client NPS feedback surveys 48 hours after trip return,
collects rating metrics (NPS, advisor responsiveness, supplier service), and aggregates agency supplier quality scorecards.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore
from src.memory.feedback_bridge import bridge_feedback_response_to_memory
from src.memory.store import MemoryStore

router = APIRouter(prefix="/api/v1/feedback", tags=["Post-Trip Quality & NPS Feedback"])

_MEMORY_STORE = MemoryStore()


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


class SupplierRatingInput(BaseModel):
    supplier_name: str = Field(min_length=1)
    category: Optional[str] = None  # HOTEL, DMC, AIRLINE, CRUISE, ...
    score: float = Field(ge=1, le=5)


class FeedbackResponseRequest(BaseModel):
    """Operator-recorded post-trip feedback response (E-10 E10.2).

    The operator transcribes the traveler's reply (WhatsApp/email) — traveler
    self-service survey surfaces are a future public-token path. nps_score is
    agency-level (scorecard aggregation only); supplier_ratings + free_text
    additionally flow through the feedback→memory bridge.
    """

    nps_score: Optional[int] = Field(default=None, ge=0, le=10)
    supplier_ratings: List[SupplierRatingInput] = Field(default_factory=list)
    free_text: Optional[str] = Field(default=None, max_length=4000)
    respondent_name: Optional[str] = None
    respondent_email: Optional[str] = None
    respondent_phone: Optional[str] = None


class FeedbackResponseAck(BaseModel):
    ok: bool = True
    trip_id: str
    response_recorded: bool
    memory_writes_persisted: int
    memory_writes_skipped: int
    received_at: str


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
    average_agency_nps: Optional[int] = None
    suppliers: List[SupplierRatingEntry] = Field(default_factory=list)
    data_source: str = Field(
        "computed_from_responses",
        description="'computed_from_responses' once survey responses exist; the aggregator never fabricates rows.",
    )


@router.post("/{trip_id}/trigger-survey", response_model=TriggerSurveyResponse)
def trigger_post_trip_survey(
    trip_id: str,
    body: TriggerSurveyRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Stage a post-trip NPS & quality feedback survey for the traveler.

    Honesty note (F-36): NO dispatch backend exists yet — the survey is staged
    on the trip record with status STAGED and the URL is a deterministic
    placeholder, not a delivered link. The docstring's former "auto-dispatch"
    claim was fiction; a real trigger (window-end derived, per E-9/E-10) is
    unbuilt.
    """
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


def _reliability_tier(avg: float) -> str:
    if avg >= 4.5:
        return "PREFERRED"
    if avg >= 3.5:
        return "ACCEPTABLE"
    return "UNDER_REVIEW"


@router.get("/supplier-scorecard", response_model=SupplierScorecardResponse)
def get_supplier_scorecard(
    agency_id: str = Depends(get_current_agency_id),
):
    """Aggregate supplier quality scorecard from stored post-trip survey
    responses (F-36/E-10). Honest aggregation: scans agency trips for
    `post_trip_feedback.response` records — no fabricated rows. An agency
    with no responses gets an empty scorecard, which is the true state."""
    trips = TripStore.list_trips(agency_id=agency_id, limit=10000)

    nps_values: List[int] = []
    submissions = 0
    per_supplier: dict = {}
    for trip in trips:
        feedback = trip.get("post_trip_feedback") or {}
        response = feedback.get("response") or {}
        if not isinstance(response, dict) or not response.get("received"):
            continue
        submissions += 1
        nps = response.get("nps_score")
        if isinstance(nps, int):
            nps_values.append(nps)
        for rating in response.get("supplier_ratings") or []:
            name = str((rating or {}).get("supplier_name") or "").strip()
            score = (rating or {}).get("score")
            if not name or score is None:
                continue
            entry = per_supplier.setdefault(
                name, {"category": (rating or {}).get("category") or "GENERAL", "scores": []}
            )
            entry["scores"].append(float(score))

    suppliers = []
    for name, agg in sorted(per_supplier.items()):
        scores = agg["scores"]
        avg = round(sum(scores) / len(scores), 2)
        suppliers.append(
            SupplierRatingEntry(
                supplier_name=name,
                category=agg["category"],
                average_score=avg,
                total_reviews_count=len(scores),
                nps_score=0,
                reliability_tier=_reliability_tier(avg),
            )
        )

    return SupplierScorecardResponse(
        ok=True,
        total_feedback_submissions=submissions,
        average_agency_nps=(round(sum(nps_values) / len(nps_values)) if nps_values else None),
        suppliers=suppliers,
        data_source="computed_from_responses",
    )


@router.post("/{trip_id}/response", response_model=FeedbackResponseAck)
def record_feedback_response(
    trip_id: str,
    body: FeedbackResponseRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Record a post-trip feedback response (E-10 E10.2) and bridge it into
    durable memory under the event-class rules (E10.3).

    The operator transcribes the traveler's reply; nps_score feeds scorecard
    aggregation only. supplier_ratings and free_text additionally flow through
    `bridge_feedback_response_to_memory` → `MemoryStore.ingest_memory` (gate →
    sanitizer → provenance → supersession). Writes are currently influence-
    inert for suitability ranking until F-13 trust-weighting ships (shadow).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    response_payload = {
        "received": True,
        "received_at": now_iso,
        "nps_score": body.nps_score,
        "free_text": body.free_text,
        "respondent_name": body.respondent_name,
        "respondent_email": body.respondent_email,
        "respondent_phone": body.respondent_phone,
        "supplier_ratings": [r.model_dump() for r in body.supplier_ratings],
    }

    feedback = dict(trip.get("post_trip_feedback") or {})
    feedback["response"] = response_payload
    feedback["status"] = "RESPONSE_RECEIVED"
    trip["post_trip_feedback"] = feedback
    TripStore.save_trip(trip, agency_id=agency_id)

    memory_result = bridge_feedback_response_to_memory(
        store=_MEMORY_STORE,
        agency_id=agency_id,
        trip_id=trip_id,
        response={
            "free_text": body.free_text,
            "supplier_ratings": [r.model_dump() for r in body.supplier_ratings],
            "respondent_email": body.respondent_email,
            "respondent_phone": body.respondent_phone,
        },
        actor_id=agency_id,
    )

    AuditStore.log_event(
        event_type="post_trip_feedback_response_recorded",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "agency_id": agency_id,
            "nps_score": body.nps_score,
            "supplier_rating_count": len(body.supplier_ratings),
            "memory_writes_persisted": len(memory_result.persisted),
            "memory_writes_skipped": len(memory_result.skipped),
        },
    )

    return FeedbackResponseAck(
        ok=True,
        trip_id=trip_id,
        response_recorded=True,
        memory_writes_persisted=len(memory_result.persisted),
        memory_writes_skipped=len(memory_result.skipped),
        received_at=now_iso,
    )
