"""
src/decision/passenger_rights.py — Automated EU261 / UK261 / US DOT Passenger Rights Engine.

Grounding doctrine:
- Travel Entitlements Graph Architect & Regulatory Protection: Deterministic passenger claims calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DisruptionType(str, Enum):
    DELAY = "DELAY"
    CANCELLATION = "CANCELLATION"
    DENIED_BOARDING = "DENIED_BOARDING"


class Jurisdiction(str, Enum):
    EU_261 = "EU_261"      # European Union Regulation (EC) No 261/2004
    UK_261 = "UK_261"      # UK Air Passenger Rights (The Air Passenger Rights and Air Travel Organisers' Licensing (Amendment) (EU Exit) Regulations 2019)
    US_DOT = "US_DOT"      # US Department of Transportation Automatic Refund Rule (2024)


@dataclass(slots=True)
class PassengerRightsClaim:
    """Calculated legal entitlement for a disrupted air passenger."""
    is_eligible_for_compensation: bool
    is_eligible_for_full_refund: bool
    jurisdiction: Jurisdiction
    compensation_currency: str
    compensation_amount: float
    right_to_care_required: bool  # Meals, hotel, communications
    duty_of_care_items: list[str]
    statutory_reference: str
    claim_rationale: str
    rebooking_entitlement: str


class PassengerRightsEngine:
    """Deterministic legal calculation for air passenger rights during disruptions."""

    @staticmethod
    def evaluate_eu261(
        disruption_type: DisruptionType,
        flight_distance_km: float,
        delay_arrival_hours: float,
        cancellation_notice_days: Optional[int] = None,
        is_extraordinary_circumstances: bool = False,
    ) -> PassengerRightsClaim:
        """
        Evaluate compensation under Regulation (EC) No 261/2004.
        Tiers:
        - Tier 1: <= 1,500 km -> €250 (3+ hour arrival delay)
        - Tier 2: 1,500 - 3,500 km -> €400 (3+ hour arrival delay)
        - Tier 3: > 3,500 km -> €600 (4+ hour arrival delay; €300 if 3-4 hours)
        """
        care_items = ["Meals and refreshments commensurate with wait time", "Two free telephone calls or emails"]
        if delay_arrival_hours >= 8.0:
            care_items.append("Complimentary hotel accommodation and round-trip airport transfers")

        # Extraordinary circumstances exempt airline from lump-sum compensation, but NEVER from duty of care or refund
        if is_extraordinary_circumstances:
            return PassengerRightsClaim(
                is_eligible_for_compensation=False,
                is_eligible_for_full_refund=delay_arrival_hours >= 5.0,
                jurisdiction=Jurisdiction.EU_261,
                compensation_currency="EUR",
                compensation_amount=0.0,
                right_to_care_required=delay_arrival_hours >= 2.0,
                duty_of_care_items=care_items if delay_arrival_hours >= 2.0 else [],
                statutory_reference="Regulation (EC) No 261/2004, Article 5(3)",
                claim_rationale="Extraordinary circumstances (e.g. severe meteorological conditions, air traffic control strike) exempt monetary compensation; duty of care applies.",
                rebooking_entitlement="Rerouting under comparable transport conditions at earliest opportunity or reimbursement within 7 days.",
            )

        # Cancellations with > 14 days notice exempt compensation
        if disruption_type == DisruptionType.CANCELLATION and cancellation_notice_days is not None and cancellation_notice_days >= 14:
            return PassengerRightsClaim(
                is_eligible_for_compensation=False,
                is_eligible_for_full_refund=True,
                jurisdiction=Jurisdiction.EU_261,
                compensation_currency="EUR",
                compensation_amount=0.0,
                right_to_care_required=False,
                duty_of_care_items=[],
                statutory_reference="Regulation (EC) No 261/2004, Article 5(1)(c)(i)",
                claim_rationale="Cancellation notified 14+ days prior to departure; full ticket refund or alternative rebooking required without statutory penalty.",
                rebooking_entitlement="Rerouting or full ticket refund.",
            )

        # Monetary compensation tiers
        amount = 0.0
        if delay_arrival_hours >= 3.0 or disruption_type in (DisruptionType.DENIED_BOARDING, DisruptionType.CANCELLATION):
            if flight_distance_km <= 1500:
                amount = 250.0
            elif flight_distance_km <= 3500:
                amount = 400.0
            else:
                amount = 600.0 if delay_arrival_hours >= 4.0 or disruption_type != DisruptionType.DELAY else 300.0

        is_eligible = amount > 0.0

        return PassengerRightsClaim(
            is_eligible_for_compensation=is_eligible,
            is_eligible_for_full_refund=delay_arrival_hours >= 5.0 or disruption_type == DisruptionType.CANCELLATION,
            jurisdiction=Jurisdiction.EU_261,
            compensation_currency="EUR",
            compensation_amount=amount,
            right_to_care_required=delay_arrival_hours >= 2.0,
            duty_of_care_items=care_items if delay_arrival_hours >= 2.0 else [],
            statutory_reference="Regulation (EC) No 261/2004, Article 7",
            claim_rationale=f"Flight distance {flight_distance_km:.0f}km with {delay_arrival_hours:.1f}h arrival delay qualifies for statutory €{amount:.0f} compensation.",
            rebooking_entitlement="Immediate comparable rerouting or full refund of unused flight coupons within 7 days.",
        )
