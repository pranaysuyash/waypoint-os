from spine_api.services.ghost_concierge import (
    FlightTelemetry,
    GhostConciergeReport,
    evaluate_flight_telemetry,
)
from spine_api.services.passenger_rights_claims import (
    PassengerClaimEligibility,
    evaluate_passenger_compensation_rights,
)


def test_ghost_concierge_detects_missed_connection():
    flights = [
        FlightTelemetry(
            flight_number="AZ601",
            carrier="ITA Airways",
            origin_iata="JFK",
            destination_iata="FCO",
            scheduled_departure="2026-09-01T17:00:00Z",
            scheduled_arrival="2026-09-02T07:30:00Z",
            delay_minutes=75,  # 75 min delay into Rome
            status="delayed",
        ),
        FlightTelemetry(
            flight_number="AZ1120",
            carrier="ITA Airways",
            origin_iata="FCO",
            destination_iata="FLR",
            scheduled_departure="2026-09-02T09:00:00Z",
            scheduled_arrival="2026-09-02T09:55:00Z",
            delay_minutes=0,
            status="scheduled",
        ),
    ]

    report: GhostConciergeReport = evaluate_flight_telemetry(
        trip_id="trip_italy_01",
        flights=flights,
        minimum_connection_time_minutes=60,
    )

    assert report.overall_health == "DISRUPTED"
    assert len(report.connection_risks) == 1
    risk = report.connection_risks[0]
    assert risk.is_at_risk is True
    assert risk.effective_layover_minutes == 15  # 90 - 75 = 15 min
    assert risk.risk_level == "CRITICAL_MISSED_CONNECTION"
    assert any("Tight connection" in i.summary for i in report.interventions)


def test_eu261_compensation_calculation_over_3500km():
    eligibility: PassengerClaimEligibility = evaluate_passenger_compensation_rights(
        carrier_code="AF",
        origin_iata="CDG",
        destination_iata="JFK",
        flight_distance_km=5800.0,
        delay_arrival_minutes=240,  # 4 hours delay
        passenger_name="Rajesh Sharma",
        booking_reference="PNR-ITALY-77",
    )

    assert eligibility.eligible is True
    assert eligibility.regulation == "EU261"
    assert eligibility.estimated_compensation_amount == 600.0
    assert eligibility.currency == "EUR"
    assert "FORMAL EU261/2004 COMPENSATION CLAIM" in eligibility.claim_template_text
    assert "€600.00 EUR" in eligibility.claim_template_text
