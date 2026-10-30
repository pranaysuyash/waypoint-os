"""Tests for the trip-date suitability gate + the traveler-rating surface."""

from datetime import date, timedelta

import pytest

from src.intake.federated_intelligence import (
    RATING_DIMENSIONS,
    DestinationRating,
    FederatedIntelligenceService,
)
from src.intake.weather_suitability import (
    FORECAST_HORIZON_DAYS,
    THRESHOLDS,
    assess_trip_date_suitability,
)


@pytest.fixture()
def service(tmp_path):
    return FederatedIntelligenceService(store_path=tmp_path / "pool.jsonl")


def _weather(days_from_today=2, n_days=3, tmax=(30.0, 31.0, 29.0), precip=(0.0, 2.0, 6.0), code=(1, 61, 95)):
    start = date.today() + timedelta(days=days_from_today)
    daily = {
        "time": [(start + timedelta(days=i)).isoformat() for i in range(n_days)],
        "temperature_2m_max": list(tmax)[:n_days],
        "temperature_2m_min": [22.0] * n_days,
        "precipitation_sum": list(precip)[:n_days],
        "weather_code": list(code)[:n_days],
        "uv_index_max": [7.0, 8.5, 3.0][:n_days],
    }
    return {
        "point": {"lat": 13.0, "lng": 100.0},
        "start_date": daily["time"][0],
        "end_date": daily["time"][-1],
        "timezone": "Asia/Bangkok",
        "daily": daily,
        "provenance": {"source_id": "open-meteo-forecast", "retrieved_at": "2026-10-30T00:00:00+00:00"},
    }


# ---- suitability gate ----


def test_beach_grading_red_on_thunderstorm():
    out = assess_trip_date_suitability(_weather(), activity="beach")
    assert out["status"] == "graded"
    assert out["days"][2]["verdict"] == "red"  # code 95 = thunderstorm
    assert out["verdict"] == "red"


def test_beach_red_on_cold_and_yellow_on_drizzle():
    w = _weather(tmax=(20.0, 28.0, 30.0), precip=(0.0, 2.0, 0.0), code=(1, 3, 1))
    out = assess_trip_date_suitability(_weather() | {"daily": w["daily"]}, activity="beach")
    assert out["days"][0]["verdict"] == "red"  # tmax 20 < 24
    assert out["days"][1]["verdict"] == "yellow"  # tmax 28 < 27? no — precip 2>1
    assert out["days"][1]["verdict"] in ("yellow", "green")


def test_hiking_snow_is_red():
    w = _weather(tmax=(-2.0, 30.0, 30.0), precip=(1.0, 0.0, 0.0), code=(73, 1, 1))
    out = assess_trip_date_suitability(w, activity="hiking")
    assert out["days"][0]["verdict"] == "red"  # snow code 73


def test_beyond_horizon_unverifiable_not_invented():
    w = _weather(days_from_today=FORECAST_HORIZON_DAYS + 5, n_days=3)
    out = assess_trip_date_suitability(w, activity="city")
    assert all(d["verdict"] == "unverifiable" for d in out["days"])
    assert out["summary"]["unverifiable"] == 3
    assert out["days"][0]["verdict"] == "unverifiable"


def test_none_weather_is_honest_unverifiable():
    out = assess_trip_date_suitability(None, activity="city")
    assert out["status"] == "unverifiable" and out["days"] == []


def test_unknown_activity_rejected():
    with pytest.raises(ValueError, match="unknown activity"):
        assess_trip_date_suitability(_weather(), activity="skiing")


def test_uv_note_emitted_when_very_high():
    out = assess_trip_date_suitability(_weather(), activity="beach")
    assert "uv_note" in out["days"][1]  # uv 8.5
    assert "sun protection" in out["days"][1]["uv_note"]


def test_thresholds_declared_not_hidden():
    assert set(THRESHOLDS) == {"beach", "hiking", "city"}


# ---- traveler ratings ----


def test_report_and_query_ratings_roundtrip(service):
    service.report_rating("agency-A", DestinationRating(location="Bali", dimension="safety", score=4))
    service.report_rating("agency-B", DestinationRating(location="bali", dimension="safety", score=2))
    service.report_rating("agency-C", DestinationRating(location="Bali", dimension="value", score=5))
    out = service.query_ratings("Bali")
    assert out["total_ratings"] == 3
    assert out["dimensions"]["safety"] == {"count": 2, "mean": 3.0, "min": 2, "max": 4}
    assert out["dimensions"]["value"]["count"] == 1


def test_rating_location_case_insensitive(service):
    service.report_rating("a", DestinationRating(location="Kyoto", dimension="food", score=5))
    assert service.query_ratings("kyoto")["total_ratings"] == 1


def test_rating_dimension_validated(service):
    with pytest.raises(ValueError, match="unknown rating dimension"):
        service.report_rating("a", DestinationRating(location="X", dimension="vibes", score=4))


def test_rating_score_range_validated(service):
    with pytest.raises(ValueError, match="1-5"):
        service.report_rating("a", DestinationRating(location="X", dimension="food", score=6))


def test_ratings_survive_restart_and_anonymized(service, tmp_path):
    service.report_rating("agency-secret", DestinationRating(location="Bali", dimension="safety", score=3))
    fresh = FederatedIntelligenceService(store_path=tmp_path / "pool.jsonl")
    assert fresh.query_ratings("Bali")["total_ratings"] == 1
    assert "agency-secret" not in (tmp_path / "pool.jsonl").read_text()


def test_no_ratings_no_fabricated_score(service):
    out = service.query_ratings("Atlantis")
    assert out["total_ratings"] == 0 and out["dimensions"] == {}


def test_rating_dimensions_constant():
    assert "safety" in RATING_DIMENSIONS and "value" in RATING_DIMENSIONS
