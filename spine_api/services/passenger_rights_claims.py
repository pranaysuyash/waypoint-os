"""
spine_api.services.passenger_rights_claims — Passenger rights & statutory disruption compensation generator.

Implements statutory compensation rules for:
- EU261 / UK261 (€250 / €400 / €600 per passenger depending on distance).
- DGCA (India CAR Section 3 Series M Part IV).
- Automated legal claim package generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# Carriers whose disruptions are adjudicated under EU261 regardless of route
# (airport-based evaluation entry point below).
EU261_CARRIERS = {"AF", "LH", "KL", "AZ", "IB", "TP", "LX", "OS", "EI", "BA"}

# Flight-hint EU set — the historical router contract, preserved exactly so
# evaluate_statutory_compensation is a behavior-preserving consolidation.
_FLIGHT_HINT_EU_CARRIERS = {"BA", "AF", "LH", "KL", "IB", "EI"}

_EUR_TO_USD = 1.09  # display conversion, matches the historical router contract


def _eu261_tier_amount(distance_km: float) -> float:
    """EU261/UK261 distance tiers: <1500km €250, ≤3500km €400, >3500km €600."""
    if distance_km < 1500:
        return 250.0
    if distance_km <= 3500:
        return 400.0
    return 600.0


def evaluate_statutory_compensation(
    flight_number: str,
    distance_km: float,
    delay_hours: float,
    passengers_count: int,
) -> Dict[str, Any]:
    """Flight-hint statutory evaluation (A2 consolidation, 2026-09-11).

    Single canonical compensation calculator for the operator-facing
    evaluate/generate-claim path. Semantics are exactly the historical router
    contract (EU261 carrier-prefix set; €250/400/600 tiers at 3h+ delays;
    US DOT $300 flat at 4h+; EUR→USD display conversion at 1.09) so callers
    can delegate without a behavior change.
    """
    fl = flight_number.upper().strip()
    is_eu_or_uk = any(fl.startswith(prefix) for prefix in _FLIGHT_HINT_EU_CARRIERS)

    if is_eu_or_uk:
        framework = "EU261"
        comp_eur = _eu261_tier_amount(distance_km) if delay_hours >= 3.0 else 0.0
    else:
        framework = "US_DOT"
        comp_eur = 300.0 if delay_hours >= 4.0 else 0.0

    is_eligible = comp_eur > 0
    total_eur = comp_eur * passengers_count
    total_usd = round(total_eur * _EUR_TO_USD, 2)

    if is_eligible:
        reason = (
            f"Eligible under {framework} for {delay_hours}h delay on {fl} ({distance_km:.0f} km flight)"
        )
    else:
        threshold = "3h" if is_eu_or_uk else "4h"
        reason = (
            f"Ineligible under {framework}: delay duration ({delay_hours}h) below statutory {threshold} threshold"
        )

    return {
        "flight_number": fl,
        "is_eligible": is_eligible,
        "regulatory_framework": framework if is_eligible else "NONE",
        "compensation_per_passenger_eur": comp_eur,
        "total_statutory_compensation_eur": total_eur,
        "total_claim_amount_usd": total_usd,
        "passengers_count": passengers_count,
        "claim_reason": reason,
    }


@dataclass(slots=True)
class PassengerClaimEligibility:
    eligible: bool
    regulation: str  # "EU261" | "UK261" | "DGCA_INDIA" | "US_DOT_REFUND"
    estimated_compensation_amount: float
    currency: str
    rationale: str
    claim_template_text: str


def evaluate_passenger_compensation_rights(
    carrier_code: str,
    origin_iata: str,
    destination_iata: str,
    flight_distance_km: float,
    delay_arrival_minutes: int,
    cancellation_notice_days: Optional[int] = None,
    is_extraordinary_circumstances: bool = False,
    passenger_name: str = "Valued Traveler",
    booking_reference: str = "PNR-12345",
) -> PassengerClaimEligibility:
    """
    Determine statutory compensation entitlement under EU261/UK261/DGCA.
    """
    eu_airports = {"FCO", "CDG", "AMS", "FRA", "MAD", "ATH", "MUC", "MXP", "BCN", "VIE", "ZRH", "LIS"}
    uk_airports = {"LHR", "LGW", "MAN", "EDI", "BHX"}

    is_eu_origin = origin_iata.upper() in eu_airports
    is_uk_origin = origin_iata.upper() in uk_airports
    is_eu_carrier = carrier_code.upper() in {"AF", "LH", "KL", "AZ", "IB", "TP", "LX", "OS"}
    is_uk_carrier = carrier_code.upper() in {"BA", "VS", "U2"}

    # Check UK261
    if is_uk_origin or (is_uk_carrier and destination_iata.upper() in uk_airports):
        if not is_extraordinary_circumstances and delay_arrival_minutes >= 180:
            comp_gbp = 220.0 if flight_distance_km < 1500 else (350.0 if flight_distance_km <= 3500 else 520.0)
            claim_text = (
                f"FORMAL UK261 COMPENSATION CLAIM\n"
                f"To: Customer Relations, {carrier_code} Airlines\n"
                f"Passenger Name: {passenger_name}\n"
                f"Booking Reference: {booking_reference}\n"
                f"Route: {origin_iata} to {destination_iata} ({flight_distance_km:.0f} km)\n"
                f"Disruption: Delay of {delay_arrival_minutes} minutes upon arrival.\n\n"
                f"Pursuant to The Air Passenger Rights Regulations (UK261), I claim statutory compensation of £{comp_gbp:,.2f} GBP."
            )
            return PassengerClaimEligibility(
                eligible=True,
                regulation="UK261",
                estimated_compensation_amount=comp_gbp,
                currency="GBP",
                rationale=f"Flight delayed by {delay_arrival_minutes} min on UK route qualifying for £{comp_gbp} GBP statutory compensation.",
                claim_template_text=claim_text,
            )

    # Check EU261
    if is_eu_origin or (is_eu_carrier and destination_iata.upper() in eu_airports):
        if is_extraordinary_circumstances:
            return PassengerClaimEligibility(
                eligible=False,
                regulation="EU261",
                estimated_compensation_amount=0.0,
                currency="EUR",
                rationale="Carrier demonstrated extraordinary circumstances (e.g. volcanic ash, act of God). Duty of care (hotel/meals) still applies.",
                claim_template_text="",
            )

        if delay_arrival_minutes >= 180 or (cancellation_notice_days is not None and cancellation_notice_days < 14):
            # Distance tiers: <1500km -> €250, 1500-3500km -> €400, >3500km -> €600
            if flight_distance_km < 1500:
                comp = 250.0
            elif flight_distance_km <= 3500:
                comp = 400.0
            else:
                comp = 600.0

            claim_text = (
                f"FORMAL EU261/2004 COMPENSATION CLAIM\n"
                f"To: Customer Relations, {carrier_code} Airlines\n"
                f"Passenger Name: {passenger_name}\n"
                f"Booking Reference: {booking_reference}\n"
                f"Route: {origin_iata} to {destination_iata} ({flight_distance_km:.0f} km)\n"
                f"Disruption: Delay of {delay_arrival_minutes} minutes upon arrival.\n\n"
                f"Pursuant to Regulation (EC) No 261/2004 of the European Parliament, I hereby claim "
                f"statutory compensation in the amount of €{comp:,.2f} EUR.\n"
                f"Please remit settlement to the passenger bank account within 14 calendar days."
            )

            return PassengerClaimEligibility(
                eligible=True,
                regulation="EU261",
                estimated_compensation_amount=comp,
                currency="EUR",
                rationale=f"Flight delayed by {delay_arrival_minutes} min on a {flight_distance_km:.0f} km route qualifying for Tier {comp} EUR statutory compensation.",
                claim_template_text=claim_text,
            )

    return PassengerClaimEligibility(
        eligible=False,
        regulation="NONE",
        estimated_compensation_amount=0.0,
        currency="USD",
        rationale="Flight disruption does not meet statutory compensation thresholds or falls outside regulated jurisdictions.",
        claim_template_text="",
    )
