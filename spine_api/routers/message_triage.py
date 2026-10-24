"""
spine_api.routers.message_triage — Live message triage API for workbench.

Provides sub-second triage of incoming messages (WhatsApp, web, email) using
TypeSafe System One (Jev) with deterministic fallback.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from src.decision.live_triage import LiveMessageTriageService

logger = logging.getLogger("spine_api.message_triage")

router = APIRouter(prefix="/api/triage", tags=["message-triage"])

_triage_service = LiveMessageTriageService()


class MessageTriageRequest(BaseModel):
    text: str = Field(..., description="The raw customer or operator message text to triage.")
    channel: Optional[str] = Field("web", description="Origin channel: 'web', 'whatsapp', or 'email'.")


class MessageTriageResponse(BaseModel):
    ok: bool = True
    intent: str
    is_urgent: bool
    urgency_probability: float
    frustration_level: str
    sentiment: str = "NEUTRAL"
    has_policy_risk: bool
    policy_risk_probability: float
    confidence: Optional[float]
    routing_recommendation: str = "PLANNING_QUEUE"
    advisory: str = ""
    source: str
    advisory_chips: List[str]
    latency_ms: float = 0.0
    raw_probabilities: Dict[str, Any] = Field(default_factory=dict)
    # E2 (INCOMING_WORK_CLASSIFICATION_MAP_2026-10-24): triage is the first
    # consumer of the canonical work classifier — the same axes every door
    # records. Preview-only: nothing is persisted here.
    work_origin: str = "demand"
    work_authority: str = "explicit_user"
    urgency_class: str = "normal"
    identity_known: bool = False
    returning_customer: bool = False
    duplicate_risk: bool = False


@router.post("/message", response_model=MessageTriageResponse)
def triage_inbound_message(
    req: MessageTriageRequest,
    agency: Agency = Depends(get_current_agency),
) -> MessageTriageResponse:
    """Triage an inbound customer message in sub-second time.

    Returns intent, urgency probability, customer emotional tone, policy risk,
    and visual advisory chips for the workbench interface — now classified on
    the canonical work-intake axes (origin/authority/urgency/identity) via
    spine_api.services.work_intake.classify (E2; preview-only, no recording).
    """
    _ = agency
    t0 = time.perf_counter()
    result = _triage_service.triage(text=req.text, channel=req.channel or "web")
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # Canonical classification on the shared axes. The triage intent maps onto
    # the work-intake intents where a clean mapping exists; unknown intents
    # keep the door default (info). Failures degrade to door defaults.
    intent_map = {
        "price_quote": "query",
        "trip_modification": "info",
        "cancellation": "decision",
        "complaint": "exception",
        "general": "query",
    }
    try:
        from spine_api.services import work_intake

        work = work_intake.classify(
            "triage_preview",
            agency_id=agency.id,
            text=req.text,
            channel=req.channel,
            intent_override=intent_map.get(result.intent),
            urgency_override="high" if result.is_urgent else None,
        )
    except Exception:
        work = {
            "origin": "demand",
            "authority": "explicit_user",
            "urgency": "high" if result.is_urgent else "normal",
            "identity_known": False,
            "returning_customer": False,
            "identity_key": None,
        }
    duplicate_risk = False
    if work.get("identity_known"):
        try:
            from spine_api.services.work_intake import duplicate_risk as _has_duplicate
            from spine_api.services.work_intake import harvest_contact

            harvested = harvest_contact(req.text)
            duplicate_risk = bool(harvested) and _has_duplicate(agency.id, harvested)
        except Exception:
            duplicate_risk = False

    # Derive sentiment tone matching frontend UI expectations
    frustration = (result.frustration_level or "").lower()
    if frustration == "angry":
        sentiment = "ANGRY"
    elif frustration == "frustrated":
        sentiment = "FRUSTRATED"
    elif frustration == "calm":
        sentiment = "CALM"
    else:
        sentiment = "NEUTRAL"

    # Derive recommended dispatch route
    if result.is_urgent:
        routing_rec = "SENIOR_AGENT_DISPATCH"
    elif result.intent == "cancellation":
        routing_rec = "CANCELLATIONS_DESK"
    elif result.intent == "complaint":
        routing_rec = "ESCALATIONS_SUPERVISOR"
    elif result.intent == "trip_modification":
        routing_rec = "OPERATIONS_DESK"
    elif result.intent == "price_quote":
        routing_rec = "PRICING_DESK"
    else:
        routing_rec = "PLANNING_QUEUE"

    advisory = "; ".join(result.advisory_chips) if result.advisory_chips else "Standard inquiry - normal processing"

    return MessageTriageResponse(
        ok=True,
        intent=result.intent,
        is_urgent=result.is_urgent,
        urgency_probability=result.urgency_probability,
        frustration_level=result.frustration_level,
        sentiment=sentiment,
        has_policy_risk=result.has_policy_risk,
        policy_risk_probability=result.policy_risk_probability,
        confidence=result.confidence,
        routing_recommendation=routing_rec,
        advisory=advisory,
        source=result.source,
        advisory_chips=result.advisory_chips,
        latency_ms=latency_ms,
        raw_probabilities=result.raw_probabilities,
        work_origin=str(work.get("origin", "demand")),
        work_authority=str(work.get("authority", "explicit_user")),
        urgency_class=str(work.get("urgency", "normal")),
        identity_known=bool(work.get("identity_known")),
        returning_customer=bool(work.get("returning_customer")),
        duplicate_risk=duplicate_risk,
    )
