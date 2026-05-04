"""
Live and mock tool adapters for product agents.

Adapters return normalized ToolResult objects. Agent code should consume these
contracts, not raw provider payloads.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from string import Formatter
from typing import Any, Protocol

from src.agents.tool_contracts import ToolFreshnessPolicy, ToolResult


class WeatherTool(Protocol):
    def current_conditions(self, destination: str) -> ToolResult:
        ...


class FlightStatusTool(Protocol):
    def flight_status(self, flight: dict[str, Any]) -> ToolResult:
        ...


class PriceWatchTool(Protocol):
    def quote_price(self, quote: dict[str, Any]) -> ToolResult:
        ...


class SafetyAlertTool(Protocol):
    def destination_alerts(self, destination: str) -> ToolResult:
        ...


class MockWeatherTool:
    """Deterministic weather adapter for local/runtime-safe operation."""

    def current_conditions(self, destination: str) -> ToolResult:
        normalized = destination.strip().lower()
        warm = any(term in normalized for term in {"singapore", "dubai", "doha", "bangkok"})
        rainy = any(term in normalized for term in {"singapore", "bali", "tokyo", "london"})
        data = {
            "location": {"name": destination},
            "current": {
                "temperature_c": 31.0 if warm else 22.0,
                "wind_speed_kmh": 14.0,
                "precipitation_mm": 0.0,
            },
            "daily": {
                "precipitation_probability_max": 68 if rainy else 25,
                "uv_index_max": 8.0 if warm else 5.0,
            },
            "mode": "mock",
        }
        return ToolResult.from_static(
            tool_name="mock_weather",
            query={"destination": destination},
            data=data,
            source="in_repo_mock_weather",
            freshness=ToolFreshnessPolicy(max_age_seconds=3_600),
            confidence=0.55,
            raw_reference="src/agents/live_tools.py:MockWeatherTool",
        )


class MockFlightStatusTool:
    """Deterministic flight-status adapter for local/runtime-safe operation."""

    def flight_status(self, flight: dict[str, Any]) -> ToolResult:
        carrier = str(flight.get("carrier") or flight.get("airline") or "").upper()
        number = str(flight.get("flight_number") or flight.get("number") or "")
        delayed = "delay" in str(flight.get("status_hint") or "").lower()
        delay_minutes = int(flight.get("delay_minutes") or (75 if delayed else 0))
        status = "delayed" if delay_minutes >= 45 else "scheduled"
        return ToolResult.from_static(
            tool_name="mock_flight_status",
            query={"carrier": carrier, "flight_number": number},
            data={
                "status": status,
                "delay_minutes": delay_minutes,
                "route": flight.get("route"),
                "mode": "mock",
            },
            source="in_repo_mock_flight_status",
            freshness=ToolFreshnessPolicy(max_age_seconds=1_800),
            confidence=0.55,
            raw_reference="src/agents/live_tools.py:MockFlightStatusTool",
        )


class MockPriceWatchTool:
    """Deterministic quote-price adapter for local/runtime-safe operation."""

    def quote_price(self, quote: dict[str, Any]) -> ToolResult:
        quoted_price = _number(quote.get("quoted_price") or quote.get("price") or quote.get("total"))
        current_price = _number(quote.get("current_price") or quote.get("market_price") or quoted_price)
        drift_percent = 0.0
        if quoted_price and current_price:
            drift_percent = round(((current_price - quoted_price) / quoted_price) * 100, 2)
        return ToolResult.from_static(
            tool_name="mock_price_watch",
            query={"quote_id": quote.get("id") or quote.get("quote_id")},
            data={
                "quoted_price": quoted_price,
                "current_price": current_price,
                "currency": quote.get("currency") or "USD",
                "drift_percent": drift_percent,
                "mode": "mock",
            },
            source="in_repo_mock_price_watch",
            freshness=ToolFreshnessPolicy(max_age_seconds=1_800),
            confidence=0.5,
            raw_reference="src/agents/live_tools.py:MockPriceWatchTool",
        )


class MockSafetyAlertTool:
    """Deterministic safety alert adapter for local/runtime-safe operation."""

    def destination_alerts(self, destination: str) -> ToolResult:
        normalized = destination.strip().lower()
        elevated = any(term in normalized for term in {"israel", "ukraine", "haiti"})
        data = {
            "destination": destination,
            "alerts": [
                {
                    "category": "security" if elevated else "routine",
                    "severity": "high" if elevated else "low",
                    "message": "Review active security advisory." if elevated else "No material advisory in mock feed.",
                }
            ],
            "mode": "mock",
        }
        return ToolResult.from_static(
            tool_name="mock_safety_alerts",
            query={"destination": destination},
            data=data,
            source="in_repo_mock_safety_alerts",
            freshness=ToolFreshnessPolicy(max_age_seconds=3_600),
            confidence=0.5,
            raw_reference="src/agents/live_tools.py:MockSafetyAlertTool",
        )


class OpenMeteoWeatherTool:
    """Open-Meteo geocoding + forecast adapter.

    Open-Meteo is keyless, which makes it useful for local travel-ops drills.
    Production usage should still be rate-limited and monitored by the caller.
    """

    geocoding_endpoint = "https://geocoding-api.open-meteo.com/v1/search"
    forecast_endpoint = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def current_conditions(self, destination: str) -> ToolResult:
        location = self._geocode(destination)
        if not location:
            return ToolResult.from_static(
                tool_name="open_meteo_weather",
                query={"destination": destination},
                data={"status": "not_found", "message": "No geocoding result returned."},
                source="open_meteo",
                freshness=ToolFreshnessPolicy(max_age_seconds=900),
                confidence=0.2,
                raw_reference=self.geocoding_endpoint,
            )

        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,precipitation,wind_speed_10m",
            "daily": "precipitation_probability_max,uv_index_max",
            "forecast_days": "3",
            "timezone": "auto",
        }
        forecast_url = f"{self.forecast_endpoint}?{urllib.parse.urlencode(params)}"
        payload = self._get_json(forecast_url)
        current = payload.get("current") if isinstance(payload, dict) else {}
        daily = payload.get("daily") if isinstance(payload, dict) else {}
        data = {
            "location": {
                "name": destination,
                "provider_name": location.get("name"),
                "country": location.get("country"),
                "latitude": location["latitude"],
                "longitude": location["longitude"],
            },
            "current": {
                "temperature_c": current.get("temperature_2m") if isinstance(current, dict) else None,
                "wind_speed_kmh": current.get("wind_speed_10m") if isinstance(current, dict) else None,
                "precipitation_mm": current.get("precipitation") if isinstance(current, dict) else None,
            },
            "daily": {
                "precipitation_probability_max": _max_number(daily.get("precipitation_probability_max")) if isinstance(daily, dict) else None,
                "uv_index_max": _max_number(daily.get("uv_index_max")) if isinstance(daily, dict) else None,
            },
            "mode": "live",
        }
        return ToolResult.from_static(
            tool_name="open_meteo_weather",
            query={"destination": destination, "latitude": location["latitude"], "longitude": location["longitude"]},
            data=data,
            source="open_meteo",
            freshness=ToolFreshnessPolicy(max_age_seconds=3_600),
            confidence=0.82,
            raw_reference=forecast_url,
            now=datetime.now(timezone.utc),
        )

    def _geocode(self, destination: str) -> dict[str, Any] | None:
        url = f"{self.geocoding_endpoint}?{urllib.parse.urlencode({'name': destination, 'count': 1, 'format': 'json'})}"
        payload = self._get_json(url)
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list) or not results:
            return None
        first = results[0]
        if not isinstance(first, dict) or first.get("latitude") is None or first.get("longitude") is None:
            return None
        return first

    def _get_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "travel-agency-agent/0.1"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


class HTTPFlightStatusTool:
    """Configurable HTTP JSON flight-status adapter.

    The URL template can reference flight fields such as `{carrier}`,
    `{flight_number}`, `{origin}`, `{destination}`, and `{date}`. This keeps
    supplier-specific credentials/configuration outside the runtime.
    """

    def __init__(self, url_template: str, provider_name: str, timeout_seconds: float = 10.0, headers: dict[str, str] | None = None):
        self.url_template = url_template
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.headers = headers or {}

    def flight_status(self, flight: dict[str, Any]) -> ToolResult:
        mapping = _flight_mapping(flight)
        url = _format_url_template(self.url_template, mapping)
        payload = _get_json(url, self.timeout_seconds, self.headers)
        status = _first_nested(payload, ["status", "flight_status", "data.0.status", "data.0.flight_status", "flights.0.status"])
        delay_minutes = _number(_first_nested(payload, ["delay_minutes", "delay", "data.0.delay_minutes", "data.0.delay", "flights.0.delay_minutes"]))
        data = {
            "status": status or "unknown",
            "delay_minutes": delay_minutes,
            "provider": self.provider_name,
            "provider_payload": payload,
            "mode": "live",
        }
        return ToolResult.from_static(
            tool_name=f"{self.provider_name}_flight_status",
            query=mapping,
            data=data,
            source=self.provider_name,
            freshness=ToolFreshnessPolicy(max_age_seconds=900),
            confidence=0.75 if status else 0.45,
            raw_reference=_redact_url(url),
            now=datetime.now(timezone.utc),
        )


class HTTPPriceWatchTool:
    """Configurable HTTP JSON quote-price adapter."""

    def __init__(self, url_template: str, provider_name: str, timeout_seconds: float = 10.0, headers: dict[str, str] | None = None):
        self.url_template = url_template
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.headers = headers or {}

    def quote_price(self, quote: dict[str, Any]) -> ToolResult:
        mapping = _quote_mapping(quote)
        url = _format_url_template(self.url_template, mapping)
        payload = _get_json(url, self.timeout_seconds, self.headers)
        current_price = _number(_first_nested(payload, ["current_price", "price", "total", "data.current_price", "data.price", "data.total", "offers.0.total"]))
        quoted_price = _number(mapping.get("quoted_price") or mapping.get("price") or mapping.get("total"))
        drift_percent = None
        if quoted_price and current_price:
            drift_percent = round(((current_price - quoted_price) / quoted_price) * 100, 2)
        data = {
            "quoted_price": quoted_price,
            "current_price": current_price,
            "currency": _first_nested(payload, ["currency", "data.currency", "offers.0.currency"]) or mapping.get("currency") or "USD",
            "drift_percent": drift_percent,
            "provider": self.provider_name,
            "provider_payload": payload,
            "mode": "live",
        }
        return ToolResult.from_static(
            tool_name=f"{self.provider_name}_price_watch",
            query={"quote_id": mapping.get("quote_id") or mapping.get("id")},
            data=data,
            source=self.provider_name,
            freshness=ToolFreshnessPolicy(max_age_seconds=900),
            confidence=0.72 if current_price is not None else 0.4,
            raw_reference=_redact_url(url),
            now=datetime.now(timezone.utc),
        )


class HTTPSafetyAlertTool:
    """Configurable HTTP JSON destination safety adapter."""

    def __init__(self, url_template: str, provider_name: str, timeout_seconds: float = 10.0, headers: dict[str, str] | None = None):
        self.url_template = url_template
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.headers = headers or {}

    def destination_alerts(self, destination: str) -> ToolResult:
        mapping = {"destination": destination, "destination_encoded": destination}
        url = _format_url_template(self.url_template, mapping)
        payload = _get_json(url, self.timeout_seconds, self.headers)
        alerts = _first_nested(payload, ["alerts", "data.alerts", "items", "features"])
        normalized_alerts = alerts if isinstance(alerts, list) else ([payload] if isinstance(payload, dict) else [])
        severity = _highest_severity(normalized_alerts)
        return ToolResult.from_static(
            tool_name=f"{self.provider_name}_safety_alerts",
            query={"destination": destination},
            data={
                "destination": destination,
                "alerts": normalized_alerts,
                "severity": severity,
                "provider": self.provider_name,
                "mode": "live",
            },
            source=self.provider_name,
            freshness=ToolFreshnessPolicy(max_age_seconds=3_600),
            confidence=0.7 if normalized_alerts else 0.35,
            raw_reference=_redact_url(url),
            now=datetime.now(timezone.utc),
        )


class StateDeptTravelAdvisoryTool:
    """U.S. State Department travel advisory adapter.

    The public data endpoint is treated as advisory evidence for operators, not
    legal/compliance finality. Destination matching is best-effort by country or
    advisory title and the agent still requires human verification.
    """

    data_api_endpoint = "https://travelmaps.state.gov/TSGMap/services/TravelAdvisory/MapServer/0/query"

    def __init__(self, endpoint: str | None = None, timeout_seconds: float = 10.0):
        self.endpoint = endpoint or self.data_api_endpoint
        self.timeout_seconds = timeout_seconds

    def destination_alerts(self, destination: str) -> ToolResult:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
        }
        url = f"{self.endpoint}?{urllib.parse.urlencode(params)}"
        payload = _get_json(url, self.timeout_seconds, {"User-Agent": "travel-agency-agent/0.1"})
        advisory = self._match_advisory(payload, destination)
        severity = _state_dept_severity(advisory)
        data = {
            "destination": destination,
            "alerts": [advisory] if advisory else [],
            "severity": severity,
            "provider": "state_dept_travel_advisory",
            "mode": "live",
        }
        return ToolResult.from_static(
            tool_name="state_dept_safety_alerts",
            query={"destination": destination},
            data=data,
            source="travel.state.gov",
            freshness=ToolFreshnessPolicy(max_age_seconds=21_600),
            confidence=0.78 if advisory else 0.35,
            raw_reference=_redact_url(url),
            now=datetime.now(timezone.utc),
        )

    def _match_advisory(self, payload: dict[str, Any], destination: str) -> dict[str, Any] | None:
        destination_norm = destination.strip().lower()
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            return None
        for feature in features:
            attributes = feature.get("attributes") if isinstance(feature, dict) else None
            if not isinstance(attributes, dict):
                continue
            values = [str(value).strip().lower() for value in attributes.values() if value is not None]
            if any(destination_norm == value or destination_norm in value for value in values):
                return attributes
        return None


def build_weather_tool_from_env() -> WeatherTool:
    if os.getenv("TRAVEL_AGENT_ENABLE_LIVE_TOOLS", "").strip().lower() in {"1", "true", "yes"}:
        return OpenMeteoWeatherTool()
    return MockWeatherTool()


def build_flight_status_tool_from_env() -> FlightStatusTool:
    url_template = os.getenv("TRAVEL_AGENT_FLIGHT_STATUS_URL_TEMPLATE", "").strip()
    if url_template:
        return HTTPFlightStatusTool(
            url_template=url_template,
            provider_name=os.getenv("TRAVEL_AGENT_FLIGHT_STATUS_PROVIDER", "configured_http").strip() or "configured_http",
            headers=_headers_from_env("TRAVEL_AGENT_FLIGHT_STATUS_HEADER_"),
        )
    return MockFlightStatusTool()


def build_price_watch_tool_from_env() -> PriceWatchTool:
    url_template = os.getenv("TRAVEL_AGENT_PRICE_WATCH_URL_TEMPLATE", "").strip()
    if url_template:
        return HTTPPriceWatchTool(
            url_template=url_template,
            provider_name=os.getenv("TRAVEL_AGENT_PRICE_WATCH_PROVIDER", "configured_http").strip() or "configured_http",
            headers=_headers_from_env("TRAVEL_AGENT_PRICE_WATCH_HEADER_"),
        )
    return MockPriceWatchTool()


def build_safety_alert_tool_from_env() -> SafetyAlertTool:
    url_template = os.getenv("TRAVEL_AGENT_SAFETY_ALERT_URL_TEMPLATE", "").strip()
    if url_template:
        return HTTPSafetyAlertTool(
            url_template=url_template,
            provider_name=os.getenv("TRAVEL_AGENT_SAFETY_ALERT_PROVIDER", "configured_http").strip() or "configured_http",
            headers=_headers_from_env("TRAVEL_AGENT_SAFETY_ALERT_HEADER_"),
        )
    if os.getenv("TRAVEL_AGENT_SAFETY_PROVIDER", "").strip().lower() in {"state_dept", "travel_state_gov"}:
        return StateDeptTravelAdvisoryTool(endpoint=os.getenv("TRAVEL_AGENT_STATE_DEPT_ADVISORY_ENDPOINT") or None)
    return MockSafetyAlertTool()


def _max_number(value: Any) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, list):
        numbers = [item for item in value if isinstance(item, (int, float))]
        return max(numbers) if numbers else None
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("$", "").strip())
        except ValueError:
            return None
    return None


def _get_json(url: str, timeout_seconds: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "travel-agency-agent/0.1"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _headers_from_env(prefix: str) -> dict[str, str]:
    headers: dict[str, str] = {"User-Agent": "travel-agency-agent/0.1"}
    for key, value in os.environ.items():
        if key.startswith(prefix) and value:
            header_name = key.removeprefix(prefix).replace("__", "-").replace("_", "-")
            headers[header_name] = value
    return headers


def _format_url_template(template: str, mapping: dict[str, Any]) -> str:
    encoded_mapping = {key: urllib.parse.quote(str(value or "")) for key, value in mapping.items()}
    referenced = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    missing = referenced.difference(encoded_mapping)
    if missing:
        encoded_mapping.update({key: "" for key in missing})
    return template.format(**encoded_mapping)


def _redact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted = []
    for key, value in query:
        if any(secret in key.lower() for secret in {"key", "token", "secret", "password", "auth"}):
            redacted.append((key, "redacted"))
        else:
            redacted.append((key, value))
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(redacted), parsed.fragment))


def _first_nested(payload: Any, paths: list[str]) -> Any:
    for path in paths:
        current = payload
        found = True
        for part in path.split("."):
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    found = False
                    break
                continue
            if not isinstance(current, dict) or part not in current:
                found = False
                break
            current = current[part]
        if found and current is not None:
            return current
    return None


def _flight_mapping(flight: dict[str, Any]) -> dict[str, Any]:
    return {
        "carrier": str(flight.get("carrier") or flight.get("airline") or "").upper(),
        "flight_number": flight.get("flight_number") or flight.get("number") or "",
        "origin": flight.get("origin") or flight.get("departure_airport") or "",
        "destination": flight.get("destination") or flight.get("arrival_airport") or "",
        "date": flight.get("date") or flight.get("departure_date") or "",
    }


def _quote_mapping(quote: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": quote.get("id") or "",
        "quote_id": quote.get("quote_id") or quote.get("id") or "",
        "origin": quote.get("origin") or "",
        "destination": quote.get("destination") or "",
        "departure_date": quote.get("departure_date") or quote.get("date") or "",
        "return_date": quote.get("return_date") or "",
        "currency": quote.get("currency") or "USD",
        "quoted_price": quote.get("quoted_price") or quote.get("price") or quote.get("total") or "",
        "price": quote.get("price") or quote.get("quoted_price") or "",
        "total": quote.get("total") or quote.get("quoted_price") or quote.get("price") or "",
    }


def _highest_severity(alerts: list[Any]) -> str:
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "routine": 1}
    best = "unknown"
    best_score = 0
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        raw = str(
            _first_nested(
                alert,
                [
                    "severity",
                    "level",
                    "risk",
                    "AdvisoryLevel",
                    "advisory_level",
                    "properties.severity",
                    "attributes.AdvisoryLevel",
                ],
            )
            or ""
        ).lower()
        if raw.startswith("4") or "do not travel" in raw:
            raw = "critical"
        elif raw.startswith("3") or "reconsider" in raw:
            raw = "high"
        elif raw.startswith("2") or "increased caution" in raw:
            raw = "medium"
        elif raw.startswith("1") or "normal precautions" in raw:
            raw = "low"
        score = rank.get(raw, 0)
        if score > best_score:
            best = raw
            best_score = score
    return best


def _state_dept_severity(advisory: dict[str, Any] | None) -> str:
    if not advisory:
        return "unknown"
    return _highest_severity([advisory])
