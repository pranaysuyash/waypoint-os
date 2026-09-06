"""
tests/test_live_connectors_and_scrapers.py — Tests for Free Live Connectors & AI Scraper Engines.
"""


from src.agents.live_tools import (
    AmadeusFlightSearchTool,
    MockFlightRadarTool,
    MockFlightSearchTool,
    OpenSkyFlightRadarTool,
)
from src.charter.empty_leg_scraper import EmptyLegScraperEngine


def test_mock_flight_search_tool():
    """Verify MockFlightSearchTool returns valid structured offers."""
    tool = MockFlightSearchTool()
    res = tool.search_offers(origin="LHR", destination="JFK", departure_date="2026-10-15", adults=2)
    assert res.is_fresh() is True
    assert res.data["status"] == "success"
    assert res.data["offers_count"] == 1
    assert res.data["offers"][0]["airline"] == "BA"
    assert res.data["offers"][0]["total_price_usd"] == 1300.0


def test_amadeus_flight_search_tool_fallback():
    """Verify AmadeusFlightSearchTool falls back to deterministic mock when unconfigured."""
    tool = AmadeusFlightSearchTool(client_id="", client_secret="")
    res = tool.search_offers(origin="CDG", destination="DXB", departure_date="2026-11-01", adults=1)
    assert res.is_fresh() is True
    assert res.data["status"] == "success"
    assert res.data["offers_count"] == 1


def test_mock_flight_radar_tool():
    """Verify MockFlightRadarTool returns structured live aircraft state vectors."""
    tool = MockFlightRadarTool()
    res = tool.live_radar_vectors(bounds={"lamin": 40.0, "lamax": 60.0, "lomin": -80.0, "lomax": 0.0})
    assert res.is_fresh() is True
    assert res.data["count"] >= 1
    assert res.data["states"][0]["callsign"] == "BAW177"


def test_opensky_flight_radar_tool():
    """Verify OpenSkyFlightRadarTool handles calls and fallback gracefully."""
    tool = OpenSkyFlightRadarTool(timeout_seconds=2.0)
    res = tool.live_radar_vectors(bounds={"lamin": 50.0, "lamax": 55.0, "lomin": -5.0, "lomax": 5.0})
    assert res.is_fresh() is True
    assert "states" in res.data


def test_empty_leg_scraper_feed_parsing():
    """Verify EmptyLegScraperEngine parses raw items and verifies mountain runway constraints."""
    raw_feed = [
        {
            "origin": "KTEB",
            "destination": "KOPF",
            "aircraft": "Challenger 3500",
            "standard_price": 24000.0,
            "discounted_price": 8000.0,
        },
        {
            "origin": "KTEB",
            "destination": "KASE",  # Aspen mountain airport
            "aircraft": "Gulfstream G650ER",  # Heavy jet requiring long runway
            "standard_price": 45000.0,
            "discounted_price": 16000.0,
        },
    ]
    results = EmptyLegScraperEngine.parse_and_validate_feed(raw_feed)
    assert len(results) == 2

    # First offer: KTEB -> KOPF (Super-midsize on standard sea-level runways)
    assert results[0].is_runway_feasible is True
    assert results[0].offer.discount_percent == 66.7

    # Second offer: KTEB -> KASE (Gulfstream G650ER at Aspen with 1.78x runway penalty)
    # 5858ft * 1.78 = 10,427ft req vs 8,006ft available at Aspen -> infeasible!
    assert results[1].is_runway_feasible is False
    assert any("too short" in w for w in results[1].runway_warnings)


def test_empty_leg_scraper_markdown_table_parsing():
    """Verify EmptyLegScraperEngine parses scraped markdown tables directly from Crawl4AI / Stagehand."""
    md_table = """
    | Origin | Destination | Aircraft | Price |
    |---|---|---|---|
    | KTEB | KOPF | Citation Latitude | $6,200 |
    | EGLF | LFPB | Phenom 300E | $3,800 |
    """
    results = EmptyLegScraperEngine.parse_markdown_table_feed(md_table)
    assert len(results) == 2
    assert results[0].offer.origin_icao == "KTEB"
    assert results[0].offer.destination_icao == "KOPF"
    assert results[0].offer.empty_leg_discounted_price_usd == 6200.0
    assert results[1].offer.origin_icao == "EGLF"
    assert results[1].offer.destination_icao == "LFPB"
    assert results[1].offer.empty_leg_discounted_price_usd == 3800.0
