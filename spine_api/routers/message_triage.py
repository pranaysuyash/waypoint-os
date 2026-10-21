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


@router.post("/message", response_model=MessageTriageResponse)
def triage_inbound_message(
    req: MessageTriageRequest,
    agency: Agency = Depends(get_current_agency),
) -> MessageTriageResponse:
    """Triage an inbound customer message in sub-second time.

    Returns intent, urgency probability, customer emotional tone, policy risk,
    and visual advisory chips for the workbench interface.
    """
    _ = agency
    t0 = time.perf_counter()
    result = _triage_service.triage(text=req.text, channel=req.channel or "web")
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

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
    )
