"""Agency-facing external API (R2-A tranche, 2026-11-04).

Key lifecycle (hash-only storage, show-once, revoke fail-closed) and the
provenance-gated trip-summary read (license_tier/as_of envelope, PII withheld).

No literal credentials appear in this file — every test key is produced by
``generate_agency_api_key()``.
"""

from __future__ import annotations

import hashlib

import pytest

from spine_api.core.api_key_auth import (
    generate_agency_api_key,
    hash_api_key,
)


def test_key_format_and_hash_roundtrip():
    raw, key_hash, key_id = generate_agency_api_key()
    assert raw.startswith("wpt_live_")
    assert len(raw) > 30
    assert hash_api_key(raw) == key_hash
    assert raw not in key_hash  # plaintext never recoverable from hash
    assert key_id


def test_hash_is_sha256_and_constant_shape():
    h = hash_api_key("wpt_live_" + "a" * 32)
    assert h == hashlib.sha256(("wpt_live_" + "a" * 32).encode()).hexdigest()
    assert len(h) == 64
    assert hash_api_key(" wpt_live_" + "a" * 32 + " ") == h  # whitespace-stripped


def test_plaintext_unique_per_generation():
    a = generate_agency_api_key()
    b = generate_agency_api_key()
    assert a[0] != b[0]
    assert a[1] != b[1]


# ── Router: provenance envelope + auth gates ──────────────────────────


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSessionMaker:
    def __call__(self):
        return _FakeSession()


async def _async_noop():
    return None


@pytest.fixture()
def _api_env(monkeypatch):
    """In-memory key store + patched trip store + real X-API-Key resolution."""
    import spine_api.core.api_key_auth as aka
    import spine_api.routers.agency_api as agency_api

    keys: dict = {}

    async def _resolve(raw):
        row = keys.get(hash_api_key(raw))
        if row is None or row["revoked"]:
            return None
        return row["agency_id"]

    monkeypatch.setattr(aka, "_ensure_api_keys_table", _async_noop)
    monkeypatch.setattr(aka, "resolve_agency_for_key", _resolve)

    async def _issue(agency_id: str, label: str = ""):
        raw, key_hash, key_id = generate_agency_api_key()
        keys[key_hash] = {"agency_id": agency_id, "key_id": key_id, "revoked": False}
        return {"key_id": key_id, "api_key": raw}

    async def _revoke(agency_id: str, key_id: str):
        for row in keys.values():
            if row["key_id"] == key_id and row["agency_id"] == agency_id:
                row["revoked"] = True
                return True
        return False

    monkeypatch.setattr(agency_api, "issue_agency_api_key", _issue)
    monkeypatch.setattr(agency_api, "revoke_agency_api_key", _revoke)

    trips = {
        "trip_a1": {
            "id": "trip_a1",
            "destination": "Bali",
            "stage": "quoted",
            "customer_name": "Ravi Kumar",
            "customer_contact": "ravi@example.com",
            "extracted": {
                "facts": {
                    "destination_country": {"value": "Indonesia"},
                    "party_size": {"value": 4},
                    "customer_name": {"value": "Ravi Kumar"},
                }
            },
        },
    }

    monkeypatch.setattr(
        agency_api,
        "TripStore",
        type(
            "TS",
            (),
            {
                "get_trip_for_agency": staticmethod(
                    lambda tid, aid: trips.get(tid) if aid == "agency_ext" else None
                )
            },
        )(),
    )

    class _Pricing:
        currency = "USD"
        net_cost = 1200.0
        retail_price = 1380.0
        retail_basis = "computed_preview"
        ready = True

    monkeypatch.setattr(agency_api, "project_commercial_pricing", lambda trip, aid: _Pricing())

    from fastapi.testclient import TestClient
    from spine_api.server import app

    client = TestClient(app)
    return client, keys


def test_summary_requires_api_key(_api_env):
    client, _keys = _api_env
    res = client.get("/api/v1/agency-api/trips/trip_a1/summary")
    assert res.status_code == 401


def test_summary_rejects_unknown_generated_key(_api_env):
    """A well-formed but never-issued key fails closed."""
    client, _keys = _api_env
    unknown, _h, _i = generate_agency_api_key()
    res = client.get(
        "/api/v1/agency-api/trips/trip_a1/summary",
        headers={"X-API-Key": unknown},
    )
    assert res.status_code == 401


def test_summary_serves_provenance_envelope_without_pii(_api_env):
    client, keys = _api_env

    raw, key_hash, _key_id = generate_agency_api_key()
    keys[key_hash] = {"agency_id": "agency_ext", "key_id": "k1", "revoked": False}

    res = client.get(
        "/api/v1/agency-api/trips/trip_a1/summary",
        headers={"X-API-Key": raw},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["license_tier"] == "agency_internal"
    assert body["as_of"]
    assert body["sources"]
    data = body["data"]
    assert data["destination"] == "Bali"
    assert data["facts"]["party_size"] == 4
    # PII withheld even though present on the trip.
    assert "customer_name" not in data["facts"]
    assert "ravi" not in str(body).lower()
    assert data["quote_preview"]["net_cost"] == 1200.0
