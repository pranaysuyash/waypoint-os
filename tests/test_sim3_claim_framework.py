"""tests/test_sim3_claim_framework.py — Sim-3 canonical claim-framework matrix (FND-0312 + FND-0319).

Live defect being guarded: for the identical flight (TG318, CANCELLED, 19h,
2400 km, Thai Airways, BKK→BOM) the /evaluate endpoint classified US_DOT
($300/pax) while generate-claim letter-headed EU261/2004 and the ghost
concierge drafted DRAFT_EU261_CLAIM. Ground truth: a Thai-carrier
Bangkok→Mumbai flight has NO EU/UK/US touchpoint — the truthful framework is
NONE with the Montreal Convention 1999 Art. 19 carrier-policy lane.

Fail-before evidence (2026-10-05, pre-fix):
  evaluate_statutory_compensation('TG318', 2400, 19.0, 2) →
  {'regulatory_framework': 'US_DOT', 'compensation_per_passenger_eur': 300.0,
   'claim_reason': 'Eligible under US_DOT for 19.0h delay on TG318 (2400 km flight)'}
"""

import os

import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.services.claim_framework import (
    MONTREAL_ARTICLE_19,
    normalize_country,
    resolve_framework,
)
from spine_api.services.ghost_concierge import FlightTelemetry, evaluate_flight_telemetry
from spine_api.services.ghost_concierge_monitor import telemetry_from_trip_facts
from spine_api.services.passenger_rights_claims import evaluate_statutory_compensation


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


# --- resolver rule-table matrix ----------------------------------------------


@pytest.mark.parametrize(
    "dep,arr,carrier,expected_framework,expected_basis",
    [
        # (THA→IND, Thai carrier) → NONE + Montreal — the sim case.
        ("Thailand", "India", "Thailand", "NONE", "outside_regulated_jurisdictions"),
        # FRA→BOM on Lufthansa: EU departure, any carrier → EU261.
        ("Germany", "India", "Germany", "EU261", "eu_departure"),
        # BOM→FRA on Lufthansa: EU arrival on EU carrier → EU261.
        ("India", "Germany", "Germany", "EU261", "eu_arrival_eu_carrier"),
        # BOM→FRA on Emirates: EU arrival but non-EU carrier → NONE.
        ("India", "Germany", "United Arab Emirates", "NONE", "outside_regulated_jurisdictions"),
        # LHR→JFK on BA: UK departure → UK261.
        ("United Kingdom", "United States", "United Kingdom", "UK261", "uk_departure"),
        # JFK→LHR on United: US departure → US_DOT (no UK carrier branch).
        ("United States", "United Kingdom", "United States", "US_DOT", "us_route"),
        # MAN→DXB on BA: UK departure any carrier → UK261.
        ("United Kingdom", "United Arab Emirates", "United Kingdom", "UK261", "uk_departure"),
        # LHR→JFK on United: UK departure wins over carrier nationality.
        ("United Kingdom", "United States", "United States", "UK261", "uk_departure"),
        # Route unknown + Thai carrier → NONE with the route-unknown reason.
        (None, None, "Thailand", "NONE", "route_unknown"),
        # Route unknown + unrecognizable carrier → NONE.
        (None, None, None, "NONE", "outside_regulated_jurisdictions"),
        # Route unknown + EU carrier prefix → historical carrier-license lane.
        (None, None, "Germany", "EU261", "carrier_license_inference"),
    ],
)
def test_resolver_matrix(dep, arr, carrier, expected_framework, expected_basis):
    resolved = resolve_framework(
        departure_country=dep,
        arrival_country=arr,
        carrier_country=carrier,
        distance_km=2400.0,
        delay_hours=19.0,
        disruption_type="CANCELLED",
    )
    assert resolved["framework"] == expected_framework
    assert resolved["basis"] == expected_basis


def test_none_framework_names_montreal_and_flags_it():
    resolved = resolve_framework("Thailand", "India", "Thailand", 2400, 19.0, "CANCELLED")
    assert resolved["montreal_applies"] is True
    assert MONTREAL_ARTICLE_19 in resolved["reason"]


def test_regulated_frameworks_do_not_claim_montreal():
    for dep, arr, car in (("Germany", "India", "Germany"), ("United Kingdom", "United States", "United Kingdom"), ("United States", "United Kingdom", "United States")):
        resolved = resolve_framework(dep, arr, car, 5000, 5.0, "DELAYED")
        assert resolved["montreal_applies"] is False


def test_country_alias_normalization():
    assert normalize_country("UK") == "united kingdom"
    assert normalize_country("USA") == "united states"
    assert normalize_country("") is None
    assert normalize_country(None) is None


# --- evaluate path (the actual FND-0312 misclassification) -------------------


def test_evaluate_tg318_bkk_bom_is_none_not_us_dot():
    """THE regression: Thai-carrier BKK→BOM CANCELLED is not US_DOT $300.

    Fail-before: regulatory_framework == 'US_DOT' with $300/pax.
    """
    result = evaluate_statutory_compensation(
        flight_number="TG318",
        distance_km=2400,
        delay_hours=19.0,
        passengers_count=2,
        departure_country="Thailand",
        arrival_country="India",
        carrier_country="Thailand",
        disruption_type="CANCELLED",
    )
    assert result["regulatory_framework"] == "NONE"
    assert result["is_eligible"] is False
    assert result["compensation_per_passenger_eur"] == 0.0  # no fabricated statutory number
    assert result["montreal_applies"] is True
    assert MONTREAL_ARTICLE_19 in result["claim_reason"]


def test_evaluate_carrier_prefix_only_thai_route_unknown_is_none():
    """No geography at all: TG prefix → Thailand → carrier-license rule has no
    EU/UK/US branch to fire → NONE with the route-unknown reason."""
    result = evaluate_statutory_compensation("TG318", 2400, 19.0, 2)
    assert result["regulatory_framework"] == "NONE"
    assert result["framework_basis"] == "route_unknown"
    assert "Route geography unknown" in result["claim_reason"]


@pytest.mark.parametrize(
    "flight,distance,delay,pax,dep,arr,car,expected_framework,expected_amount",
    [
        # FRA-BOM ≈ 6700 km > 3500 → 600 EUR band.
        ("LH758", 6700, 5.0, 1, "Germany", "India", "Germany", "EU261", 600.0),
        # Short-haul EU departure → 250 EUR.
        ("LH100", 900, 3.5, 2, "Germany", "Austria", "Germany", "EU261", 250.0),
        # UK departure → GBP bands (220/350/520).
        ("BA112", 5500, 4.0, 1, "United Kingdom", "United States", "United Kingdom", "UK261", 520.0),
        ("BA201", 1200, 3.2, 1, "United Kingdom", "Spain", "United Kingdom", "UK261", 220.0),
        # JFK departure, any carrier → US DOT flat.
        ("UA1", 5500, 5.0, 1, "United States", "United Kingdom", "United States", "US_DOT", 300.0),
    ],
)
def test_evaluate_amount_matrix(flight, distance, delay, pax, dep, arr, car, expected_framework, expected_amount):
    result = evaluate_statutory_compensation(
        flight_number=flight,
        distance_km=distance,
        delay_hours=delay,
        passengers_count=pax,
        departure_country=dep,
        arrival_country=arr,
        carrier_country=car,
        disruption_type="DELAYED",
    )
    assert result["regulatory_framework"] == expected_framework
    assert result["compensation_per_passenger_eur"] == expected_amount
    assert result["is_eligible"] is True


# --- evaluate vs generate-claim: ONE classification (FND-0312 root fix) ------


@pytest.fixture()
def api_client():
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from spine_api.core.auth import get_current_agency
    from spine_api.server import app

    app.dependency_overrides[get_current_agency] = lambda: SimpleNamespace(
        id="sim3-test-agency"
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_agency, None)


SIM3_TRIP_ID = "sim3trip318"


@pytest.fixture()
def sim3_trip(api_client):
    """The sim flight as trip facts: TG318 BKK→BOM, Thai Airways, CANCELLED."""
    from spine_api.persistence import TripStore

    agency_id = "sim3-test-agency"
    trip = {
        "id": SIM3_TRIP_ID,
        "agency_id": agency_id,
        "status": "active",
        "destination": "Mumbai",
        "flight_status_updates": [
            {
                "flight_number": "TG318",
                "carrier": "TG",
                "origin_iata": "BKK",
                "destination_iata": "BOM",
                "status": "cancelled",
                "delay_minutes": 19 * 60,
            }
        ],
    }
    TripStore.save_trip(trip, agency_id=agency_id)
    return agency_id


def test_evaluate_and_generate_claim_agree_on_framework(api_client, sim3_trip):
    """THE FND-0312 regression: same flight through both endpoints must yield
    the SAME framework (fail-before: evaluate=US_DOT, generate-claim=EU261)."""
    evaluate = api_client.post(
        "/api/v1/passenger-rights/evaluate",
        json={
            "trip_id": SIM3_TRIP_ID,
            "flight_number": "TG318",
            "disruption_type": "CANCELLED",
            "delay_hours": 19.0,
            "distance_km": 2400.0,
            "passengers_count": 2,
            "departure_country": "Thailand",
            "arrival_country": "India",
            "carrier_country": "Thailand",
        },
        headers={"X-Agency-ID": sim3_trip},
    ).json()
    generate = api_client.post(
        f"/api/v1/passenger-rights/{SIM3_TRIP_ID}/generate-claim",
        json={
            "trip_id": SIM3_TRIP_ID,
            "passenger_names": ["Ada Sim", "Alan Sim"],
            "booking_reference": "BK-SIM3",
        },
        headers={"X-Agency-Id": sim3_trip},
    ).json()

    assert evaluate["regulatory_framework"] == "NONE"
    # Both consumers resolve through claim_framework → identical classification.
    assert generate["regulatory_framework"] == evaluate["regulatory_framework"] == "NONE"
    # The letter's LEGAL BASIS is the honest Montreal lane — it may mention
    # EU261 only to state that EU261 does NOT apply; it must not be headed
    # or grounded in EU261/2004.
    letter = generate["claim_letter_text"]
    assert not letter.startswith("FORMAL STATUTORY COMPENSATION CLAIM UNDER EU261")
    assert "Pursuant to Regulation (EC) No 261/2004" not in letter
    assert "MONTREAL CONVENTION 1999" in letter.upper()
    assert "ARTICLE 19" in letter.upper()


def test_generate_claim_eu_letter_for_eu_route(api_client, sim3_trip):
    """A genuinely EU-covered route still gets the EU261 statutory letter."""
    from spine_api.persistence import TripStore

    TripStore.save_trip(
        {
            "id": "sim3trip_lh",
            "agency_id": sim3_trip,
            "status": "active",
            "flight_status_updates": [
                {
                    "flight_number": "LH758",
                    "carrier": "LH",
                    "origin_iata": "FRA",
                    "destination_iata": "BOM",
                    "status": "cancelled",
                    "delay_minutes": 300,
                }
            ],
        },
        agency_id=sim3_trip,
    )
    res = api_client.post(
        "/api/v1/passenger-rights/sim3trip_lh/generate-claim",
        json={
            "trip_id": "sim3trip_lh",
            "passenger_names": ["Ada Sim"],
            "booking_reference": "BK-EU",
        },
        headers={"X-Agency-Id": sim3_trip},
    ).json()
    assert res["regulatory_framework"] == "EU261"
    assert "EU261/2004" in res["claim_letter_text"]


# --- ghost concierge draft label (FND-0312) + route summary (FND-0319) -------


def test_ghost_concierge_draft_label_matches_framework():
    flights = [
        FlightTelemetry(
            flight_number="TG318", carrier="TG", origin_iata="BKK",
            destination_iata="BOM", scheduled_departure="", scheduled_arrival="",
            status="cancelled",
        ),
        FlightTelemetry(
            flight_number="LH758", carrier="LH", origin_iata="FRA",
            destination_iata="BOM", scheduled_departure="", scheduled_arrival="",
            status="cancelled",
        ),
    ]
    report = evaluate_flight_telemetry("sim3trip318", flights)
    drafts = [i for i in report.interventions if i.action_type.startswith("DRAFT")]
    by_flight = {
        flight: next((i for i in drafts if flight in i.summary), None)
        for flight in ("TG318", "LH758")
    }

    # Thai flight: no statutory regime → honest DRAFT_CLAIM (Montreal), not EU261.
    assert by_flight["TG318"] is not None
    assert by_flight["TG318"].action_type == "DRAFT_CLAIM"
    assert MONTREAL_ARTICLE_19 in by_flight["TG318"].summary
    # Lufthansa FRA departure → DRAFT_EU261_CLAIM stands.
    assert by_flight["LH758"] is not None
    assert by_flight["LH758"].action_type == "DRAFT_EU261_CLAIM"


def test_ghost_concierge_omits_arrow_when_route_unknown():
    """FND-0319: no route on the telemetry ⇒ 'Flight TG318' — never '(->)'."""
    flights = [
        FlightTelemetry(
            flight_number="TG318", carrier="TG", origin_iata="",
            destination_iata="", scheduled_departure="", scheduled_arrival="",
            status="cancelled",
        ),
    ]
    report = evaluate_flight_telemetry("sim3trip318", flights)
    cancelled_summary = next(
        i.summary for i in report.interventions if i.action_type == "SEARCH_FALLBACK_FLIGHTS"
    )
    assert "(->)" not in cancelled_summary
    assert cancelled_summary.startswith("Flight TG318")


def test_monitor_telemetry_falls_back_to_trip_origin_destination():
    """FND-0319: flight facts without an IATA route inherit the trip's
    origin/destination so the summary carries a usable route."""
    trip = {
        "id": "t",
        "origin": "Bangkok",
        "destination": "Mumbai",
        "flight_status_updates": [
            {"flight_number": "TG318", "status": "cancelled", "delay_minutes": 0}
        ],
    }
    telemetry = telemetry_from_trip_facts(trip)
    assert len(telemetry) == 1
    assert telemetry[0].origin_iata == "Bangkok"
    assert telemetry[0].destination_iata == "Mumbai"


# --- historical contract guards (evaluate behavior preserved) ----------------


def test_historical_carrier_prefix_lanes_preserved():
    """A2 consolidation contract (2026-09-11) must not regress: BA → EU261
    hint lane, DL → US DOT hint lane, ineligible EU flight reports NONE."""
    ba = evaluate_statutory_compensation("BA123", 1000, 3.0, 2)
    assert ba["regulatory_framework"] == "EU261"
    assert ba["compensation_per_passenger_eur"] == 250.0

    dl = evaluate_statutory_compensation("DL456", 8000, 4.0, 3)
    assert dl["regulatory_framework"] == "US_DOT"
    assert dl["compensation_per_passenger_eur"] == 300.0

    below = evaluate_statutory_compensation("BA123", 1000, 2.5, 1)
    assert below["is_eligible"] is False
    assert below["regulatory_framework"] == "NONE"
