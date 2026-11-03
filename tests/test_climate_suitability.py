"""Tests for the ERA5 climate-baseline path + the horizon-dispatching
trip-conditions orchestrator."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from src.intake.weather_suitability import (
    assess_climate_suitability,
    grade_trip_conditions,
)


def _climate(mean_tmax=32.0, mean_precip=0.3, years=(2021, 2022, 2023, 2024, 2025)):
    return {
        "point": {"lat": 13.7, "lng": 100.5},
        "window": {"start_mmdd": "12-10", "end_mmdd": "12-16"},
        "years_used": list(years),
        "years_skipped": [],
        "normals": {
            "mean_tmax_c": mean_tmax,
            "mean_precip_mm": mean_precip,
            "rain_day_fraction": 0.1,
        },
        "provenance": [{"source_id": "open-meteo-archive-era5"}],
    }


def test_climate_beach_green_on_hot_dry_normal():
    out = assess_climate_suitability(_climate(), activity="beach")
    assert out["mode"] == "climate_baseline" and out["status"] == "graded"
    assert out["verdict"] == "green"
    assert "climate expectation, not a forecast" in out["confidence_note"]
    assert out["years_used"] == [2021, 2022, 2023, 2024, 2025]


def test_climate_beach_red_on_cold_normal():
    out = assess_climate_suitability(_climate(mean_tmax=18.0), activity="beach")
    assert out["verdict"] == "red"


def test_climate_city_red_on_monsoon_precip():
    out = assess_climate_suitability(_climate(mean_precip=20.0), activity="city")
    assert out["verdict"] == "red"


def test_climate_hiking_yellow_on_moderate_precip():
    out = assess_climate_suitability(_climate(mean_precip=5.0), activity="hiking")
    assert out["verdict"] == "yellow"


def test_climate_unknown_activity_rejected():
    with pytest.raises(ValueError, match="unknown activity"):
        assess_climate_suitability(_climate(), activity="surfing")


def test_climate_empty_normals_unverifiable():
    out = assess_climate_suitability({"normals": {}, "provenance": []}, activity="city")
    assert out["status"] == "unverifiable"


def test_orchestrator_dispatches_forecast_within_horizon():
    start = (date.today() + timedelta(days=5)).isoformat()
    end = (date.today() + timedelta(days=7)).isoformat()
    with patch("src.intake.external_sources.fetch_open_meteo_trip_weather") as fw, patch(
        "src.intake.external_sources.fetch_open_meteo_climate_normals"
    ) as fc:
        fw.return_value = {
            "daily": {"time": [start, start[:8] + "16"], "temperature_2m_max": [30.0, 31.0],
                      "temperature_2m_min": [24.0, 24.0], "precipitation_sum": [0.0, 0.0],
                      "weather_code": [1, 1], "uv_index_max": [6.0, 6.0]},
            "timezone": "X",
            "provenance": {"source_id": "open-meteo-forecast"},
        }
        out = grade_trip_conditions(13.7, 100.5, start, end, activity="beach")
    assert out["mode"] == "forecast"
    fw.assert_called_once()
    fc.assert_not_called()


def test_orchestrator_dispatches_climate_beyond_horizon():
    start = (date.today() + timedelta(days=45)).isoformat()
    end = (date.today() + timedelta(days=50)).isoformat()
    with patch("src.intake.external_sources.fetch_open_meteo_trip_weather") as fw, patch(
        "src.intake.external_sources.fetch_open_meteo_climate_normals"
    ) as fc:
        fc.return_value = _climate()
        out = grade_trip_conditions(13.7, 100.5, start, end, activity="beach")
    assert out["mode"] == "climate_baseline"
    assert out["verdict"] == "green"
    fc.assert_called_once()
    fw.assert_not_called()
