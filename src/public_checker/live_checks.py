"""
Live travel checks for the public itinerary checker.

This module keeps the live-data lookup isolated from the main spine pipeline.
The checker best-effort enriches a trip with destination climate signals from
Open-Meteo so the public wedge can make concrete seasonality suggestions.
"""

from __future__ import annotations

import calendar
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


@dataclass(frozen=True)
class ClimateLocation:
    name: str
    latitude: float
    longitude: float
    country_code: Optional[str] = None


def _flatten_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if "destination" in key.lower():
                strings.extend(_flatten_strings(item))
            elif isinstance(item, (dict, list, tuple)):
                strings.extend(_flatten_strings(item))
            elif isinstance(item, str):
                strings.append(item)
        return strings
    if isinstance(value, (list, tuple)):
        strings: list[str] = []
        for item in value:
            strings.extend(_flatten_strings(item))
        return strings
    return []


def _extract_destination(packet: dict[str, Any], text: str) -> Optional[str]:
    for candidate in (
        packet.get("destination"),
        packet.get("resolved_destination"),
        packet.get("destination_name"),
        packet.get("location"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    facts = packet.get("facts")
    for candidate in _flatten_strings(facts):
        if candidate.strip():
            return candidate.strip()

    candidates = _flatten_strings(packet.get("destination_candidates"))
    if candidates:
        return candidates[0].strip()

    text_match = re.search(r"\bto\s+([A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]+){0,3})", text)
    if text_match:
        return text_match.group(1).strip()

    return None


def _extract_month_year(text: str) -> tuple[int, int]:
    month_number = 0
    month_match = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        text,
        flags=re.IGNORECASE,
    )
    if month_match:
        month_number = MONTHS[month_match.group(1).lower()]

    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))
    else:
        today = date.today()
        year = today.year
        if month_number and month_number < today.month:
            year += 1

    if not month_number:
        today = date.today()
        month_number = today.month
        year = today.year

    return month_number, year


def _month_window(month: int, year: int) -> tuple[str, str]:
    days_in_month = calendar.monthrange(year, month)[1]
    return (
        f"{year:04d}-{month:02d}-01",
        f"{year:04d}-{month:02d}-{days_in_month:02d}",
    )


def _geocode_destination(destination: str) -> Optional[ClimateLocation]:
    try:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": destination, "count": 1, "language": "en", "format": "json"},
            timeout=4,
        )
        response.raise_for_status()
        payload = response.json()
        result = (payload.get("results") or [None])[0]
        if not result:
            return None
        return ClimateLocation(
            name=str(result.get("name") or destination),
            latitude=float(result["latitude"]),
            longitude=float(result["longitude"]),
            country_code=result.get("country_code"),
        )
    except Exception as exc:
        logger.debug("Public checker geocoding failed for %s: %s", destination, exc)
        return None


def _climate_summary(location: ClimateLocation, month: int, year: int) -> Optional[dict[str, Any]]:
    start_date, end_date = _month_window(month, year)
    try:
        response = requests.get(
            "https://climate-api.open-meteo.com/v1/climate",
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "start_date": start_date,
                "end_date": end_date,
                "models": "EC_Earth3P_HR",
                "daily": (
                    "temperature_2m_mean,"
                    "temperature_2m_max,"
                    "mean_wind_speed_10m,"
                    "precipitation_sum,"
                    "relative_humidity_2m_mean"
                ),
                "timezone": "auto",
            },
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        daily = payload.get("daily") or {}

        def _mean(series: Any) -> Optional[float]:
            values = [float(v) for v in series or [] if v is not None]
            if not values:
                return None
            return sum(values) / len(values)

        precipitation = _mean(daily.get("precipitation_sum"))
        wind = _mean(daily.get("mean_wind_speed_10m"))
        temperature = _mean(daily.get("temperature_2m_mean"))
        humidity = _mean(daily.get("relative_humidity_2m_mean"))

        hard_blockers: list[str] = []
        soft_blockers: list[str] = []
        notes: list[str] = []
        score_penalty = 0

        if precipitation is not None and precipitation >= 300:
            hard_blockers.append(
                f"{location.name} looks extremely wet in {calendar.month_name[month]} ({precipitation:.0f} mm avg monthly precipitation)."
            )
            notes.append("heavy rain and disruption risk")
            score_penalty += 20
        elif precipitation is not None and precipitation >= 180:
            soft_blockers.append(
                f"{location.name} is wet in {calendar.month_name[month]} ({precipitation:.0f} mm avg monthly precipitation)."
            )
            notes.append("storm-prone month")
            score_penalty += 10

        if wind is not None and wind >= 30:
            hard_blockers.append(
                f"Average wind in {location.name} is high for {calendar.month_name[month]} ({wind:.0f} km/h)."
            )
            notes.append("wind disruption risk")
            score_penalty += 10
        elif wind is not None and wind >= 20:
            soft_blockers.append(
                f"Average wind in {location.name} is elevated for {calendar.month_name[month]} ({wind:.0f} km/h)."
            )
            notes.append("gusty month")
            score_penalty += 5

        if temperature is not None and humidity is not None and temperature >= 30 and humidity >= 75:
            soft_blockers.append(
                f"{location.name} is hot and humid in {calendar.month_name[month]} ({temperature:.1f}°C / {humidity:.0f}% humidity)."
            )
            notes.append("heat and humidity load")
            score_penalty += 5

        if location.latitude and abs(location.latitude) <= 30 and month in {6, 7, 8, 9, 10, 11}:
            soft_blockers.append(
                f"{location.name} sits in a tropical-storm-prone season during {calendar.month_name[month]}."
            )
            notes.append("tropical storm season")
            score_penalty += 5

        if not hard_blockers and not soft_blockers:
            return None

        return {
            "destination": location.name,
            "country_code": location.country_code,
            "travel_window": {
                "start_date": start_date,
                "end_date": end_date,
                "month": month,
                "year": year,
            },
            "climate": {
                "precipitation_mm_avg": round(precipitation, 1) if precipitation is not None else None,
                "wind_kmh_avg": round(wind, 1) if wind is not None else None,
                "temperature_c_avg": round(temperature, 1) if temperature is not None else None,
                "humidity_pct_avg": round(humidity, 1) if humidity is not None else None,
            },
            "signals": notes,
            "hard_blockers": hard_blockers,
            "soft_blockers": soft_blockers,
            "score_penalty": min(30, score_penalty),
            "source": "open-meteo-climate-api",
        }
    except Exception as exc:
        logger.debug(
            "Public checker climate lookup failed for %s (%s-%s): %s",
            location.name,
            start_date,
            end_date,
            exc,
        )
        return None


def _current_conditions(location: ClimateLocation) -> Optional[dict[str, Any]]:
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "relative_humidity_2m,"
                    "wind_speed_10m,"
                    "weather_code"
                ),
                "timezone": "auto",
            },
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current") or {}
        if not current:
            return None

        temperature = current.get("temperature_2m")
        apparent = current.get("apparent_temperature")
        precipitation = current.get("precipitation")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        weather_code = current.get("weather_code")

        hard_blockers: list[str] = []
        soft_blockers: list[str] = []
        notes: list[str] = []
        score_penalty = 0

        if isinstance(precipitation, (int, float)) and precipitation >= 3:
            soft_blockers.append(
                f"{location.name} is currently seeing measurable precipitation ({float(precipitation):.1f} mm)."
            )
            notes.append("active precipitation")
            score_penalty += 5

        if isinstance(wind, (int, float)) and wind >= 30:
            soft_blockers.append(
                f"Current wind in {location.name} is strong ({float(wind):.0f} km/h)."
            )
            notes.append("strong wind")
            score_penalty += 5

        if isinstance(humidity, (int, float)) and humidity >= 85:
            soft_blockers.append(
                f"{location.name} is currently very humid ({float(humidity):.0f}% relative humidity)."
            )
            notes.append("humid right now")
            score_penalty += 3

        if isinstance(apparent, (int, float)) and apparent >= 35:
            soft_blockers.append(
                f"It feels very hot in {location.name} right now ({float(apparent):.1f}°C apparent temperature)."
            )
            notes.append("heat stress")
            score_penalty += 3

        if not hard_blockers and not soft_blockers:
            return None

        return {
            "destination": location.name,
            "current": {
                "temperature_c": float(temperature) if isinstance(temperature, (int, float)) else None,
                "apparent_temperature_c": float(apparent) if isinstance(apparent, (int, float)) else None,
                "precipitation_mm": float(precipitation) if isinstance(precipitation, (int, float)) else None,
                "relative_humidity_pct": float(humidity) if isinstance(humidity, (int, float)) else None,
                "wind_kmh": float(wind) if isinstance(wind, (int, float)) else None,
                "weather_code": weather_code,
            },
            "signals": notes,
            "hard_blockers": hard_blockers,
            "soft_blockers": soft_blockers,
            "score_penalty": min(15, score_penalty),
            "source": "open-meteo-current-conditions",
        }
    except Exception as exc:
        logger.debug("Public checker current weather lookup failed for %s: %s", location.name, exc)
        return None


def build_live_checker_signals(packet: dict[str, Any], raw_text: str) -> Optional[dict[str, Any]]:
    destination = _extract_destination(packet, raw_text)
    if not destination:
        return None

    month, year = _extract_month_year(raw_text)
    location = _geocode_destination(destination)
    if not location:
        return None

    climate = _climate_summary(location, month, year)
    current = _current_conditions(location)

    if not climate and not current:
        return None

    hard_blockers: list[str] = []
    soft_blockers: list[str] = []
    signals: list[str] = []
    score_penalty = 0

    if climate:
        hard_blockers.extend(climate.get("hard_blockers") or [])
        soft_blockers.extend(climate.get("soft_blockers") or [])
        signals.extend(climate.get("signals") or [])
        score_penalty += int(climate.get("score_penalty") or 0)

    if current:
        hard_blockers.extend(current.get("hard_blockers") or [])
        soft_blockers.extend(current.get("soft_blockers") or [])
        signals.extend(current.get("signals") or [])
        score_penalty += int(current.get("score_penalty") or 0)

    return {
        "destination": location.name,
        "country_code": location.country_code,
        "travel_window": climate.get("travel_window") if climate else None,
        "seasonality": climate,
        "current_conditions": current,
        "signals": list(dict.fromkeys(signals)),
        "hard_blockers": list(dict.fromkeys(hard_blockers)),
        "soft_blockers": list(dict.fromkeys(soft_blockers)),
        "score_penalty": min(35, score_penalty),
        "source": "open-meteo",
    }
