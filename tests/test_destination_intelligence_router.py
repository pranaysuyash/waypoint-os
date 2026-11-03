"""Contract tests for the destination-intelligence router.

Upstream fetchers are monkeypatched (no network in unit tests — the live
fetches were verified separately in the research passes). These tests pin
the REAL HTTP contract: route shapes, auth gating, error semantics, cache
behavior.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from spine_api.server import app

# House auth-bypass seam (FND-0259): _auth_or_skip + get_current_agency_id
# honor SPINE_API_DISABLE_AUTH at call time; X-Agency-ID then scopes.
HEADERS = {"X-Agency-ID": "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"}


@pytest.fixture(autouse=True)
def auth_bypass(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


client = TestClient(app)


def _patch_fcdo(band="1", slug="japan"):
    def fake(slug_arg):
        assert slug_arg == slug
        return {
            "country_slug": slug,
            "content_payload": {"details": {}},
            "advisory_band": band,
            "raw_alert_status": [],
            "public_updated_at": "2026-08-28T16:22:35+01:00",
            "provenance": {"source_id": "fcdo-content-api", "retrieved_at": "2026-10-30T00:00:00+00:00"},
        }
    return patch("spine_api.routers.destination_intelligence.fetch_fcdo_country", side_effect=fake)


@pytest.fixture()
def clear_cache():
    from spine_api.routers.destination_intelligence import _safety_cache
    _safety_cache.clear()
    yield
    _safety_cache.clear()


def test_safety_verdict_shape_and_gating(clear_cache):
    with _patch_fcdo(band="1"), patch(
        "spine_api.routers.destination_intelligence.fetch_worldbank_homicide"
    ) as fw:
        fw.return_value = {
            "rate_per_100k": 0.229, "year": "2023",
            "provenance": {"source_id": "worldbank-api", "retrieved_at": "2026-10-30T00:00:00+00:00"},
        }
        resp = client.get("/api/v1/destination-intelligence/safety/japan?iso3=JPN", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["destination_slug"] == "japan"
    assert body["band"] == "1" and body["label"] == "Normal precautions"
    assert "c1_advisory" in body["coverage"] and "c2_violent_crime" in body["coverage"]
    assert body["coverage_gaps"] == ["c3_neighborhood", "c4_events"]
    assert body["cached"] is False


def test_safety_verdict_cached_second_call(clear_cache):
    with _patch_fcdo() as p:
        client.get("/api/v1/destination-intelligence/safety/japan", headers=HEADERS)
        client.get("/api/v1/destination-intelligence/safety/japan", headers=HEADERS)
    assert p.call_count == 1  # one upstream fetch, second served from cache
    resp = client.get("/api/v1/destination-intelligence/safety/japan", headers=HEADERS)
    assert resp.json()["cached"] is True


def test_safety_upstream_failure_is_502_not_500(clear_cache, monkeypatch):
    def boom(slug):
        from src.intake.external_fetch import ExternalFetchError
        raise ExternalFetchError("HTTP 503")
    monkeypatch.setattr("spine_api.routers.destination_intelligence.fetch_fcdo_country", boom)
    resp = client.get("/api/v1/destination-intelligence/safety/japan", headers=HEADERS)
    assert resp.status_code == 502
    assert resp.json()["detail"]["error"] == "upstream_fetch_failed"


def test_weather_suitability_contract(clear_cache, monkeypatch):
    # Mock matches the REAL forecast-path shape: provenance is a single
    # metadata dict (the router normalizes it to a list at the boundary —
    # the climate path emits a list, live-run-caught divergence).
    monkeypatch.setattr(
        "spine_api.routers.destination_intelligence.grade_trip_conditions",
        lambda lat, lng, s, e, activity: {
            "mode": "forecast", "activity": activity, "status": "graded",
            "verdict": "green", "days": [], "summary": {"green": 2, "yellow": 0, "red": 0, "unverifiable": 0},
            "timezone": "Asia/Tokyo", "provenance": {"source_id": "open-meteo-forecast", "retrieved_at": "2026-11-03T00:00:00+00:00"},
        },
    )
    resp = client.get(
        "/api/v1/destination-intelligence/weather-suitability"
        "?lat=35.7&lng=139.7&start_date=2026-11-05&end_date=2026-11-08&activity=city", headers=HEADERS
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "forecast" and body["verdict"] == "green"
    assert body["activity"] == "city"
    assert isinstance(body["provenance"], list)  # boundary-normalized from dict


def test_weather_suitability_bad_activity_is_422(clear_cache, monkeypatch):
    def bad(*a, **k):
        raise ValueError("unknown activity 'skiing'; use one of ['beach', 'city', 'hiking']")
    monkeypatch.setattr("spine_api.routers.destination_intelligence.grade_trip_conditions", bad)
    resp = client.get(
        "/api/v1/destination-intelligence/weather-suitability"
        "?lat=35.7&lng=139.7&start_date=2026-11-05&end_date=2026-11-08&activity=skiing", headers=HEADERS
    )
    assert resp.status_code == 422


def test_ratings_read_contract(clear_cache, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.intake.federated_intelligence.STORE_PATH", tmp_path / "pool.jsonl"
    )
    from src.intake.federated_intelligence import FederatedIntelligenceService, DestinationRating
    svc = FederatedIntelligenceService(store_path=tmp_path / "pool.jsonl")
    svc.report_rating("agency-T", DestinationRating(location="Bali", dimension="safety", score=4))
    resp = client.get("/api/v1/destination-intelligence/ratings/Bali", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["location"] == "Bali" and body["total_ratings"] == 1
    assert body["dimensions"]["safety"]["mean"] == 4.0
