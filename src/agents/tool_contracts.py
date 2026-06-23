"""
Shared contracts for agent tool evidence.

Tool-calling agents must normalize live/provider data into this shape before
another agent or reasoning layer consumes it. The raw provider response should
never be treated as canonical state.

Tool input/output validation uses Pydantic models to enforce schema boundaries
at the tool calling interface.  Raw provider payloads (provider_payload) are
stripped before data enters trip records to prevent supplier-specific fields
from leaking into canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


# ---------------------------------------------------------------------------
# Tool freshness policy (dataclass)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ToolFreshnessPolicy:
    max_age_seconds: int
    fail_closed: bool = True


# ---------------------------------------------------------------------------
# Tool input validation schemas
# ---------------------------------------------------------------------------

class WeatherInput(BaseModel):
    """Validated input for weather tool queries."""
    destination: str = Field(min_length=1, max_length=200)


class FlightStatusInput(BaseModel):
    """Validated input for flight status tool queries."""
    carrier: str = Field(default="", max_length=20)
    flight_number: str = Field(default="", max_length=20)
    origin: str = Field(default="", max_length=10)
    destination: str = Field(default="", max_length=10)
    date: str = Field(default="", max_length=30)


class PriceWatchInput(BaseModel):
    """Validated input for price watch tool queries."""
    quote_id: str = Field(default="", max_length=100)
    origin: str = Field(default="", max_length=10)
    destination: str = Field(default="", max_length=10)
    departure_date: str = Field(default="", max_length=30)
    return_date: str = Field(default="", max_length=30)
    currency: str = Field(default="USD", max_length=10)
    quoted_price: Optional[float] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0)
    total: Optional[float] = Field(default=None, ge=0)


class SafetyAlertInput(BaseModel):
    """Validated input for safety alert tool queries."""
    destination: str = Field(min_length=1, max_length=200)


# ---------------------------------------------------------------------------
# Tool output validation schemas
# ---------------------------------------------------------------------------

class ToolLocation(BaseModel):
    """Normalized location data from weather/provider tools."""
    name: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WeatherCurrent(BaseModel):
    """Current weather conditions."""
    temperature_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    precipitation_mm: Optional[float] = None


class WeatherDaily(BaseModel):
    """Daily weather summary."""
    precipitation_probability_max: Optional[float] = None
    uv_index_max: Optional[float] = None


class WeatherOutput(BaseModel):
    """Validated output from weather tools."""
    location: ToolLocation = Field(default_factory=ToolLocation)
    current: WeatherCurrent = Field(default_factory=WeatherCurrent)
    daily: WeatherDaily = Field(default_factory=WeatherDaily)
    status: Optional[str] = None
    message: Optional[str] = None
    mode: str = "mock"


class FlightOutput(BaseModel):
    """Validated output from flight status tools."""
    status: str = Field(default="unknown", max_length=50)
    delay_minutes: int = Field(default=0, ge=0)
    route: Optional[str] = None
    provider: Optional[str] = None
    mode: str = "mock"


class PriceOutput(BaseModel):
    """Validated output from price watch tools."""
    quoted_price: Optional[float] = Field(default=None, ge=0)
    current_price: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    drift_percent: Optional[float] = None
    provider: Optional[str] = None
    mode: str = "mock"


class SafetyAlertRecord(BaseModel):
    """A single safety alert record."""
    category: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None


class SafetyOutput(BaseModel):
    """Validated output from safety alert tools."""
    destination: str = Field(default="")
    alerts: list[SafetyAlertRecord] = Field(default_factory=list)
    severity: str = Field(default="unknown", max_length=20)
    provider: Optional[str] = None
    mode: str = "mock"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

# Fields that must never appear in canonical tool output stored in trip records.
STRIPPED_PROVIDER_FIELDS = frozenset({"provider_payload"})


def sanitize_tool_data(data: dict[str, Any], extra_strip: frozenset[str] | None = None) -> dict[str, Any]:
    """
    Strip provider-specific fields from tool result data before storage.

    Removes provider_payload and any other supplier-specific fields that should
    not leak into canonical trip records.
    """
    stripped = STRIPPED_PROVIDER_FIELDS | (extra_strip or frozenset())
    return {k: v for k, v in data.items() if k not in stripped}


# Input schema registry for tool name → input model mapping.
_TOOL_INPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "weather": WeatherInput,
    "open_meteo_weather": WeatherInput,
    "mock_weather": WeatherInput,
    "flight_status": FlightStatusInput,
    "mock_flight_status": FlightStatusInput,
    "price_watch": PriceWatchInput,
    "mock_price_watch": PriceWatchInput,
    "safety_alerts": SafetyAlertInput,
    "mock_safety_alerts": SafetyAlertInput,
}

# Output schema registry for tool name → output model mapping.
_TOOL_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "weather": WeatherOutput,
    "open_meteo_weather": WeatherOutput,
    "mock_weather": WeatherOutput,
    "flight_status": FlightOutput,
    "mock_flight_status": FlightOutput,
    "price_watch": PriceOutput,
    "mock_price_watch": PriceOutput,
    "safety_alerts": SafetyOutput,
    "mock_safety_alerts": SafetyOutput,
}


def validate_tool_input(tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate tool input against the registered Pydantic schema.

    Strips the provider prefix (e.g. "configured_http_flight_status" → "flight_status")
    before lookup.  Returns the validated/coerced dict on success; on validation
    error returns the original dict unchanged so callers are never broken.
    """
    schema_key = _resolve_schema_key(tool_name, _TOOL_INPUT_SCHEMAS)
    schema_cls = _TOOL_INPUT_SCHEMAS.get(schema_key)
    if schema_cls is None:
        return data
    try:
        validated = schema_cls.model_validate(data)
        return validated.model_dump(exclude_none=True)
    except (ValidationError, ValueError, TypeError):
        return data


def validate_tool_output(tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate tool output against the registered Pydantic schema.

    Enforces output shape before data enters ToolResult or trip records.
    Returns the validated/coerced dict on success; on validation error returns
    the original dict unchanged (fail-open for resilience).
    """
    schema_key = _resolve_schema_key(tool_name, _TOOL_OUTPUT_SCHEMAS)
    schema_cls = _TOOL_OUTPUT_SCHEMAS.get(schema_key)
    if schema_cls is None:
        return data
    try:
        validated = schema_cls.model_validate(data)
        # Re-build dict, stripping None values and extra provider fields
        return sanitize_tool_data(validated.model_dump(exclude_none=True))
    except (ValidationError, ValueError, TypeError):
        return data


def _resolve_schema_key(tool_name: str, registry: dict[str, Any]) -> str:
    """
    Resolve a tool name to its schema key.

    Handles provider-prefixed names like "configured_http_flight_status" → "flight_status"
    by checking for known suffixes.
    """
    if tool_name in registry:
        return tool_name
    # Strip provider prefix: e.g. "acme_flight_status" → "flight_status"
    for suffix in ("_flight_status", "_price_watch", "_safety_alerts"):
        if tool_name.endswith(suffix):
            return suffix.lstrip("_")
    return tool_name


@dataclass(frozen=True, slots=True)
class ToolEvidence:
    source: str
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_reference: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    query: dict[str, Any]
    data: dict[str, Any]
    evidence: ToolEvidence
    expires_at: Optional[str] = None

    def is_fresh(self, now: Optional[datetime] = None) -> bool:
        if not self.expires_at:
            return True
        now = now or datetime.now(timezone.utc)
        expires = _parse_dt(self.expires_at)
        return bool(expires and now <= expires)

    def to_dict(self, now: Optional[datetime] = None) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "query": self.query,
            "data": self.data,
            "evidence": self.evidence.to_dict(),
            "expires_at": self.expires_at,
            "fresh": self.is_fresh(now=now),
        }

    @classmethod
    def from_static(
        cls,
        tool_name: str,
        query: dict[str, Any],
        data: dict[str, Any],
        source: str,
        freshness: ToolFreshnessPolicy,
        confidence: float = 1.0,
        raw_reference: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> "ToolResult":
        timestamp = now or datetime.now(timezone.utc)
        return cls(
            tool_name=tool_name,
            query=query,
            data=data,
            evidence=ToolEvidence(
                source=source,
                fetched_at=timestamp.isoformat(),
                raw_reference=raw_reference,
                confidence=confidence,
            ),
            expires_at=(timestamp + timedelta(seconds=freshness.max_age_seconds)).isoformat(),
        )


def _parse_dt(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
