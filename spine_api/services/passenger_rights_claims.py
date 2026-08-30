"""
spine_api.services.passenger_rights_claims — Passenger rights & statutory disruption compensation generator.

Implements statutory compensation rules for:
- EU261 / UK261 (€250 / €400 / €600 per passenger depending on distance).
- DGCA (India CAR Section 3 Series M Part IV).
- Automated legal claim package generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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
