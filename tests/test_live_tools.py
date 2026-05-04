from __future__ import annotations

from src.agents import live_tools
from src.agents.live_tools import (
    HTTPFlightStatusTool,
    HTTPPriceWatchTool,
    HTTPSafetyAlertTool,
    MockFlightStatusTool,
    MockPriceWatchTool,
    MockSafetyAlertTool,
    StateDeptTravelAdvisoryTool,
    build_flight_status_tool_from_env,
    build_price_watch_tool_from_env,
    build_safety_alert_tool_from_env,
)


def test_http_flight_status_tool_normalizes_provider_payload_and_redacts_reference(monkeypatch):
    captured = {}

    def fake_get_json(url, timeout_seconds, headers=None):
        captured["url"] = url
        captured["headers"] = headers
        return {"data": [{"flight_status": "delayed", "delay_minutes": 65}]}

    monkeypatch.setattr(live_tools, "_get_json", fake_get_json)

    tool = HTTPFlightStatusTool(
        "https://flight.example/status?carrier={carrier}&number={flight_number}&api_key=secret",
        "flight_provider",
        headers={"X-API-Key": "secret"},
    )
    result = tool.flight_status({"carrier": "sq", "flight_number": "321"})

    assert captured["url"] == "https://flight.example/status?carrier=SQ&number=321&api_key=secret"
    assert captured["headers"] == {"X-API-Key": "secret"}
    assert result.tool_name == "flight_provider_flight_status"
    assert result.data["status"] == "delayed"
    assert result.data["delay_minutes"] == 65.0
    assert result.evidence.raw_reference.endswith("api_key=redacted")


def test_http_price_watch_tool_computes_quote_drift(monkeypatch):
    monkeypatch.setattr(
        live_tools,
        "_get_json",
        lambda url, timeout_seconds, headers=None: {"data": {"price": 1250, "currency": "USD"}},
    )

    tool = HTTPPriceWatchTool("https://price.example/offers?quote={quote_id}", "price_provider")
    result = tool.quote_price({"quote_id": "Q1", "quoted_price": 1000, "currency": "USD"})

    assert result.tool_name == "price_provider_price_watch"
    assert result.data["quoted_price"] == 1000.0
    assert result.data["current_price"] == 1250.0
    assert result.data["drift_percent"] == 25.0


def test_http_safety_alert_tool_normalizes_alerts(monkeypatch):
    monkeypatch.setattr(
        live_tools,
        "_get_json",
        lambda url, timeout_seconds, headers=None: {"alerts": [{"severity": "high", "message": "Review unrest."}]},
    )

    tool = HTTPSafetyAlertTool("https://safety.example/alerts?destination={destination}", "safety_provider")
    result = tool.destination_alerts("Paris")

    assert result.tool_name == "safety_provider_safety_alerts"
    assert result.data["severity"] == "high"
    assert result.data["alerts"][0]["message"] == "Review unrest."


def test_state_dept_tool_matches_destination_from_feature_attributes(monkeypatch):
    monkeypatch.setattr(
        live_tools,
        "_get_json",
        lambda url, timeout_seconds, headers=None: {
            "features": [
                {"attributes": {"Country": "Singapore", "AdvisoryLevel": "Level 1: Exercise Normal Precautions"}},
            ]
        },
    )

    tool = StateDeptTravelAdvisoryTool(endpoint="https://state.example/query")
    result = tool.destination_alerts("Singapore")

    assert result.tool_name == "state_dept_safety_alerts"
    assert result.evidence.source == "travel.state.gov"
    assert result.data["severity"] == "low"
    assert result.data["alerts"][0]["Country"] == "Singapore"


def test_live_tool_builders_use_configured_http_adapters_when_env_is_present(monkeypatch):
    monkeypatch.setenv("TRAVEL_AGENT_FLIGHT_STATUS_URL_TEMPLATE", "https://flight.example/{carrier}")
    monkeypatch.setenv("TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE", "https://price.example/{quote_id}")
    monkeypatch.setenv("TRAVEL_AGENT_SAFETY_ALERT_URL_TEMPLATE", "https://safety.example/{destination}")

    assert isinstance(build_flight_status_tool_from_env(), HTTPFlightStatusTool)
    assert isinstance(build_price_watch_tool_from_env(), HTTPPriceWatchTool)
    assert isinstance(build_safety_alert_tool_from_env(), HTTPSafetyAlertTool)


def test_live_tool_builders_keep_deterministic_fallbacks_without_provider_env(monkeypatch):
    monkeypatch.delenv("TRAVEL_AGENT_FLIGHT_STATUS_URL_TEMPLATE", raising=False)
    monkeypatch.delenv("TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE", raising=False)
    monkeypatch.delenv("TRAVEL_AGENT_SAFETY_ALERT_URL_TEMPLATE", raising=False)
    monkeypatch.delenv("TRAVEL_AGENT_SAFETY_PROVIDER", raising=False)

    assert isinstance(build_flight_status_tool_from_env(), MockFlightStatusTool)
    assert isinstance(build_price_watch_tool_from_env(), MockPriceWatchTool)
    assert isinstance(build_safety_alert_tool_from_env(), MockSafetyAlertTool)
