"""
intake.weather_suitability — trip-date suitability gate (AW12 cluster).

Implements the Trip-Date Suitability Gate from
Docs/research/AW12_WEATHER_AQI_SOURCE_EVALUATION_2026-10-30.md: itinerary
dates + destination → green/yellow/red per activity type, from the Open-Meteo
daily slice fetched through the governed pipeline.

Honesty rules:
- Dates beyond the ~16-day live-forecast horizon are ``unverifiable`` —
  never graded from invented numbers (climate-normals path is a future
  tranche; ERA5 history makes it data-backed when built).
- Thresholds are explicit v1 constants (editorial-calibratable), documented
  here — not hidden magic.
- Every verdict carries the fetch provenance through unchanged.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from src.intake.data_normalization import AQIScale  # re-export convenience  # noqa: F401

# Open-Meteo live forecast horizon (documented ~16 days; conservative pin).
FORECAST_HORIZON_DAYS = 16

# WMO weather-code groups (Open-Meteo docs): thunderstorm 95-99, snow 71-77
# + 85-86, rain/showers 51-67 + 80-82, fog 45-48.
_THUNDERSTORM = range(95, 100)
_SNOW = list(range(71, 78)) + [85, 86]
_RAIN = list(range(51, 68)) + [80, 81, 82]

# v1 activity thresholds — explicit, editorially calibratable.
THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "beach": {"min_tmax_c": 24.0, "yellow_tmax_c": 27.0, "red_precip_mm": 5.0, "yellow_precip_mm": 1.0},
    "hiking": {"red_precip_mm": 8.0, "yellow_precip_mm": 2.0},
    "city": {"red_precip_mm": 15.0, "yellow_precip_mm": 5.0},
}


def _verdict_for_day(activity: str, tmax: Optional[float], precip: Optional[float], code: Optional[int]) -> str:
    t = THRESHOLDS[activity]
    if code is not None and int(code) in _THUNDERSTORM:
        return "red"
    if activity == "beach":
        if tmax is not None and tmax < t["min_tmax_c"]:
            return "red"
        if (precip is not None and precip > t["red_precip_mm"]) or (tmax is not None and tmax < t["yellow_tmax_c"]):
            return "yellow"
        if precip is not None and precip > t["yellow_precip_mm"]:
            return "yellow"
    else:
        if precip is not None and precip > t["red_precip_mm"]:
            return "red"
        if precip is not None and precip > t["yellow_precip_mm"]:
            return "yellow"
        if code is not None and int(code) in _SNOW and activity == "hiking":
            return "red"
    return "green"


def assess_trip_date_suitability(
    weather: Optional[Dict[str, Any]],
    *,
    activity: str,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """Grade a trip window day-by-day for one activity type.

    ``weather``: output of ``fetch_open_meteo_trip_weather`` (or None =
    fetch failed upstream → whole window unverifiable, honest gap).
    Verdicts: green / yellow / red / unverifiable (per day).
    """
    if activity not in THRESHOLDS:
        raise ValueError(f"unknown activity {activity!r}; use one of {sorted(THRESHOLDS)}")
    provenance = (weather or {}).get("provenance")
    if weather is None or not weather.get("daily", {}).get("time"):
        return {
            "activity": activity,
            "status": "unverifiable",
            "days": [],
            "summary": {"green": 0, "yellow": 0, "red": 0, "unverifiable": 0},
            "provenance": provenance,
        }

    daily = weather["daily"]
    times: List[str] = daily["time"]
    tmaxs = daily.get("temperature_2m_max", [])
    precips = daily.get("precipitation_sum", [])
    codes = daily.get("weather_code", [])
    uvs = daily.get("uv_index_max", [])

    current = today or date.today()
    horizon = current + timedelta(days=FORECAST_HORIZON_DAYS)

    days: List[Dict[str, Any]] = []
    summary = {"green": 0, "yellow": 0, "red": 0, "unverifiable": 0}
    for i, day_iso in enumerate(times):
        day = date.fromisoformat(day_iso)
        if day > horizon:
            verdict = "unverifiable"  # beyond live-forecast horizon — never invented
        else:
            tmax = tmaxs[i] if i < len(tmaxs) else None
            precip = precips[i] if i < len(precips) else None
            code = codes[i] if i < len(codes) else None
            verdict = _verdict_for_day(activity, tmax, precip, code)
        summary[verdict] += 1
        day_out: Dict[str, Any] = {"date": day_iso, "verdict": verdict}
        if verdict != "unverifiable":
            day_out.update({
                "tmax_c": tmaxs[i] if i < len(tmaxs) else None,
                "precip_mm": precips[i] if i < len(precips) else None,
                "weather_code": codes[i] if i < len(codes) else None,
            })
            uv = uvs[i] if i < len(uvs) else None
            if uv is not None and float(uv) >= 8.0:
                day_out["uv_note"] = f"very high UV ({uv}) — sun protection advised"
        days.append(day_out)

    worst = "red" if summary["red"] else ("yellow" if summary["yellow"] else "green")
    return {
        "activity": activity,
        "status": "graded",
        "verdict": worst,
        "days": days,
        "summary": summary,
        "timezone": weather.get("timezone"),
        "provenance": provenance,
    }
