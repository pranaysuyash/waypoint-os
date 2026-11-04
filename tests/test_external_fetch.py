"""Tests for the governed external-fetch pipeline + FCDO source.

Transport is monkeypatched (no network in unit tests); the live FCDO
endpoint was verified separately in the AW3 research pass (2026-10-30).
"""

import pytest
from unittest.mock import patch

from src.intake.external_fetch import ExternalFetchError, fetch_json
from src.intake.external_reference import DataCategory, LicenseTier
from src.intake.external_sources import fetch_fcdo_country, normalize_fcdo_status


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, body=b"{}"):
        self.status_code = status_code
        self._payload = payload
        self._body = body

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


@pytest.fixture()
def allowlisted_http(monkeypatch):
    """Capture the URL and return a canned JSON payload."""
    calls = {}

    def _get(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return _FakeResponse(payload={"ok": True, "details": {"alert_level": "do not travel"}})

    monkeypatch.setattr("src.intake.external_fetch.httpx.get", _get)
    return calls


def test_fetch_json_attaches_provenance(allowlisted_http):
    result = fetch_json(
        "https://www.gov.uk/api/content/foreign-travel-advice/japan",
        source_id="fcdo-content-api",
        category=DataCategory.SAFETY_ADVISORY,
        license_tier=LicenseTier.SHARE_ALIKE,
    )
    assert result.payload == {"ok": True, "details": {"alert_level": "do not travel"}}
    meta = result.reference.to_metadata()
    assert meta["source_id"] == "fcdo-content-api"
    assert meta["license_tier"] == "share_alike"
    assert meta["retrieved_at"]
    assert result.is_stale() is False


def test_non_allowlisted_host_rejected():
    with pytest.raises(ExternalFetchError, match="allowlist"):
        fetch_json(
            "https://evil.example.com/data",
            source_id="x",
            category=DataCategory.WEATHER,
        )


def test_http_and_credentialed_urls_rejected():
    with pytest.raises(ExternalFetchError, match="https"):
        fetch_json("http://www.gov.uk/x", source_id="x", category=DataCategory.WEATHER)
    with pytest.raises(ExternalFetchError, match="credentialed"):
        fetch_json(
            "https://user:pass@www.gov.uk/x", source_id="x", category=DataCategory.WEATHER
        )


def test_http_error_raises(allowlisted_http, monkeypatch):
    monkeypatch.setattr(
        "src.intake.external_fetch.httpx.get",
        lambda url, **k: _FakeResponse(status_code=403),
    )
    with pytest.raises(ExternalFetchError, match="403"):
        fetch_json(
            "https://www.gov.uk/api/content/foreign-travel-advice/x",
            source_id="x",
            category=DataCategory.SAFETY_ADVISORY,
        )


def test_non_json_body_raises(allowlisted_http, monkeypatch):
    monkeypatch.setattr(
        "src.intake.external_fetch.httpx.get",
        lambda url, **k: _FakeResponse(payload=None, body=b"<html>"),
    )
    with pytest.raises(ExternalFetchError, match="non-JSON"):
        fetch_json(
            "https://www.gov.uk/api/content/foreign-travel-advice/x",
            source_id="x",
            category=DataCategory.SAFETY_ADVISORY,
        )


def test_redirects_not_followed(allowlisted_http):
    fetch_json(
        "https://www.gov.uk/api/content/foreign-travel-advice/japan",
        source_id="x",
        category=DataCategory.SAFETY_ADVISORY,
    )
    assert allowlisted_http["kwargs"]["follow_redirects"] is False


# ---- FCDO source ----


def test_fcdo_status_normalization_full_ladder():
    # Live-verified shapes (2026-10-30): russia=['avoid_all_travel_to_whole_country'],
    # israel=['avoid_all_travel_to_parts','avoid_all_but_essential_travel_to_parts'], japan=[]
    assert normalize_fcdo_status([]) == "1"  # no advisory (Japan)
    assert normalize_fcdo_status(["avoid_all_travel_to_whole_country"]) == "4"  # (Russia)
    assert normalize_fcdo_status(["avoid_all_travel_to_parts"]) == "3"
    assert normalize_fcdo_status(["avoid_all_but_essential_travel_to_whole_country"]) == "3"
    assert normalize_fcdo_status(["avoid_all_but_essential_travel_to_parts"]) == "2"
    # Max across entries (Israel's real shape)
    assert (
        normalize_fcdo_status(["avoid_all_travel_to_parts", "avoid_all_but_essential_travel_to_parts"])
        == "3"
    )
    # Unknown slug: cautious floor 3, never dropped
    assert normalize_fcdo_status(["some_new_status_slug"]) == "3"
    assert normalize_fcdo_status(["no_advisory"]) == "1"
    assert normalize_fcdo_status(None) == "1"


def test_fcdo_slug_alias_bali():
    """bali was the original live-404 — FCDO advises at country level."""
    with patch("spine_api.routers.destination_intelligence.fetch_fcdo_country"):
        pass  # (no-op; keep patch import used)
    with patch("src.intake.external_sources.fetch_json") as fj:
        fj.return_value = type("R", (), {"payload": {"details": {"alert_status": []}, "public_updated_at": "x"},
                                          "reference": None, "category": None})()
        # reference is only used via to_metadata; stub it properly
        class _Ref:
            def to_metadata(self):
                return {"source_id": "fcdo-content-api", "retrieved_at": "t", "license_tier": "share_alike"}
        r = type("R2", (), {"payload": {"details": {"alert_status": []}, "public_updated_at": "x"},
                             "reference": _Ref(), "category": DataCategory.SAFETY_ADVISORY})()
        fj.return_value = r
        out = fetch_fcdo_country("bali")
    assert out["requested_slug"] == "bali"
    assert out["country_slug"] == "indonesia"
    assert "alias_note" in out


def test_fcdo_direct_country_no_alias_note():
    with patch("src.intake.external_sources.fetch_json") as fj:
        class _Ref:
            def to_metadata(self):
                return {"source_id": "fcdo-content-api"}
        r = type("R2", (), {"payload": {"details": {"alert_status": []}, "public_updated_at": "x"},
                             "reference": _Ref(), "category": DataCategory.SAFETY_ADVISORY})()
        fj.return_value = r
        out = fetch_fcdo_country("japan")
    assert "alias_note" not in out
    assert out["requested_slug"] == "japan"


def test_fetch_fcdo_country_shape(allowlisted_http, monkeypatch):
    monkeypatch.setattr(
        "src.intake.external_fetch.httpx.get",
        lambda url, **k: _FakeResponse(
            payload={"details": {"alert_status": ["avoid_all_travel_to_whole_country"]},
                     "public_updated_at": "2026-08-28T16:22:35+01:00"}
        ),
    )
    out = fetch_fcdo_country("Russia")
    assert out["country_slug"] == "russia"
    assert out["advisory_band"] == "4"
    assert out["raw_alert_status"] == ["avoid_all_travel_to_whole_country"]
    assert out["public_updated_at"] == "2026-08-28T16:22:35+01:00"
    prov = out["provenance"]
    assert prov["source_id"] == "fcdo-content-api"
    assert prov["category"] == "safety_advisory"
    assert prov["license_tier"] == "share_alike"
