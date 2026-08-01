"""
src/intake/lifecycle.py — Lead Lifecycle & Retention State Machine for Waypoint OS.

Formalizes lead classification, ghosting risk detection, window-shopping intent scoring,
and automated retention intervention triggers per LEAD_LIFECYCLE_AND_RETENTION.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List


class LeadStage(str, Enum):
    NEW_INQUIRY = "new_inquiry"
    QUALIFIED_LEAD = "qualified_lead"
    PROPOSAL_SENT = "proposal_sent"
    ACCEPTED_BOOKED = "accepted_booked"
    GHOSTED_STALE = "ghosted_stale"
    CHURNED = "churned"


class RetentionInterventionType(str, Enum):
    PERSONALIZED_WHATSAPP = "personalized_whatsapp"
    PRICE_LOCK_EXPIRING_EMAIL = "price_lock_expiring_email"
    PERK_INCENTIVE_OFFER = "perk_incentive_offer"
    HUMAN_SENIOR_CALL = "human_senior_call"


@dataclass
class LeadLifecycleState:
    trip_id: str
    agency_id: str
    stage: LeadStage = LeadStage.NEW_INQUIRY
    intent_score: float = 0.5  # 0.0 to 1.0
    ghosting_risk: float = 0.0  # 0.0 to 1.0
    days_since_last_interaction: int = 0
    recommended_interventions: List[RetentionInterventionType] = field(default_factory=list)
    last_evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def evaluate(self) -> None:
        """Evaluate lead lifecycle metrics and assign retention interventions."""
        if self.days_since_last_interaction >= 7:
            self.ghosting_risk = min(1.0, 0.3 + (self.days_since_last_interaction * 0.1))
            if self.stage == LeadStage.PROPOSAL_SENT:
                self.stage = LeadStage.GHOSTED_STALE
        elif self.days_since_last_interaction >= 3:
            self.ghosting_risk = 0.4
        else:
            self.ghosting_risk = 0.1

        # Interventions assignment logic
        self.recommended_interventions.clear()

        if self.stage == LeadStage.GHOSTED_STALE:
            self.recommended_interventions.append(RetentionInterventionType.PERSONALIZED_WHATSAPP)
            self.recommended_interventions.append(RetentionInterventionType.PERK_INCENTIVE_OFFER)
        elif self.ghosting_risk >= 0.4:
            self.recommended_interventions.append(RetentionInterventionType.PRICE_LOCK_EXPIRING_EMAIL)

        if self.intent_score > 0.8 and self.ghosting_risk > 0.5:
            self.recommended_interventions.append(RetentionInterventionType.HUMAN_SENIOR_CALL)
