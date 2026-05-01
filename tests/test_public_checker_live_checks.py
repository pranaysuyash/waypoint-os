"""
Tests for the public checker live-data enrichment helpers.
"""

from __future__ import annotations

from src.public_checker.live_checks import build_live_checker_signals


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_hong_kong_august_surface_climate_risk(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        if "geocoding-api.open-meteo.com" in url:
            return _FakeResponse({
                "results": [
                    {
                        "name": "Hong Kong",
                        "latitude": 22.3193,
                        "longitude": 114.1694,
                        "country_code": "HK",
                    }
                ]
            })
        if "climate-api.open-meteo.com" in url:
            return _FakeResponse({
                "daily": {
                    "precipitation_sum": [220.0, 240.0, 260.0],
                    "mean_wind_speed_10m": [18.0, 19.0, 21.0],
                    "temperature_2m_mean": [29.2, 29.8, 30.1],
                    "relative_humidity_2m_mean": [79.0, 81.0, 82.0],
                }
            })
        raise AssertionError(f"Unexpected URL {url}")

    monkeypatch.setattr("src.public_checker.live_checks.requests.get", fake_get)

    live = build_live_checker_signals(
        {"destination": "Hong Kong"},
        "Hong Kong in August for 2 elders and 1 child",
    )

    assert live is not None
    assert live["destination"] == "Hong Kong"
    assert live["country_code"] == "HK"
    assert live["score_penalty"] > 0
    assert any("storm-prone" in item.lower() for item in live["soft_blockers"])
    assert any("wet" in item.lower() for item in live["soft_blockers"])
