"""FND-0219 — durable public proposal capability credentials.

Covers the SQL/memory-backed ``ProposalTokenStore`` and its router wiring in
``spine_api/routers/public_proposals.py``:

- issue -> access roundtrip (HTTP response shape unchanged for the traveler)
- TTL enforcement (expired credentials rejected)
- durable revocation (rejected, uniform errors, survives a simulated restart)
- resource binding (a credential only ever resolves to its own trip)
- hashed-at-rest storage (raw token material never persisted; memory + SQL)
- idempotent issue replay (no TTL/consent refresh) and explicit format version
- legacy raw-token revocation files are normalized (graceful, no silent
  upgrade)
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

import spine_api.routers.public_proposals as public_proposals
from spine_api.models.proposal_tokens import ProposalAccessToken
from spine_api.routers.public_proposals import (
    PublicProposalView,
    issue_proposal_capability,
    verify_proposal_token,
)
from spine_api.server import app
from spine_api.services.proposal_token_store import (
    DEFAULT_ISSUANCE_TTL_HOURS,
    PROPOSAL_TOKEN_BACKEND_ENV,
    PROPOSAL_TOKEN_TTL_HOURS_ENV,
    MemoryProposalTokenBackend,
    ProposalTokenStore,
    SqlProposalTokenBackend,
    TokenStatus,
    hash_token,
    new_token_material,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Shared stubs: a persisted, agency-bound trip resource for the public view.
# ---------------------------------------------------------------------------


def _stub_trip_store(monkeypatch, trip_id: str, agency_id: str):
    monkeypatch.setattr(
        public_proposals.TripStore,
        "get_trip_for_agency",
        lambda requested_trip_id, requested_agency_id: (
            {"id": trip_id, "agency_id": agency_id}
            if requested_trip_id == trip_id and requested_agency_id == agency_id
            else None
        ),
    )
    monkeypatch.setattr(
        public_proposals.TripStore,
        "get_trip_for_public_access",
        lambda requested_trip_id: {
            "id": requested_trip_id,
            "destination": "Kyoto",
            "stage": "proposal",
            "packet": {
                "destination": "Kyoto",
                "start_date": "2026-10-01",
                "end_date": "2026-10-10",
            },
            "strategy": {
                "recommended_option": {
                    "name": "Kyoto Garden Villa",
                    "cost": 7500,
                    "currency": "USD",
                }
            },
        },
    )


@pytest.fixture(autouse=True)
def _memory_token_store(monkeypatch):
    """FND-0219 lifecycle tests always run against the in-memory backend."""
    monkeypatch.setattr(
        public_proposals.ProposalTokenStore,
        "_instance",
        public_proposals.ProposalTokenStore(backend=MemoryProposalTokenBackend()),
    )


@pytest.fixture()
def isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        public_proposals, "_REVOCATIONS_PATH", tmp_path / "revoked_tokens.json"
    )
    monkeypatch.setattr(public_proposals, "_REVOKED_TOKENS", {})
    return tmp_path


# ---------------------------------------------------------------------------
# Hashing / TTL constants
# ---------------------------------------------------------------------------


def test_hash_token_is_deterministic_with_bounded_prefix():
    digest, prefix = hash_token("propv3_example")
    assert digest == hash_token("propv3_example")[0]
    assert len(digest) == 64  # full sha256 hex
    assert prefix == digest[:16]


def test_default_ttl_is_documented_30_days_and_env_overridable(monkeypatch):
    monkeypatch.delenv(PROPOSAL_TOKEN_TTL_HOURS_ENV, raising=False)
    assert DEFAULT_ISSUANCE_TTL_HOURS == 720
    from spine_api.services import proposal_token_store as store_module

    assert store_module.default_ttl_hours() == 720
    monkeypatch.setenv(PROPOSAL_TOKEN_TTL_HOURS_ENV, "48")
    assert store_module.default_ttl_hours() == 48
    monkeypatch.setenv(PROPOSAL_TOKEN_TTL_HOURS_ENV, "not-a-number")
    assert store_module.default_ttl_hours() == 720


def test_new_token_material_is_opaque_urlsafe_256bit():
    token = new_token_material()
    other = new_token_material()
    assert token.startswith("propv3_") and other.startswith("propv3_")
    assert token != other  # fresh random material every issuance
    # base64url alphabet only (no path/percent hazards)
    material = token[len("propv3_") :]
    assert all(c.isalnum() or c in "-_" for c in material)
    assert len(material) == 43  # 32 bytes urlsafe-base64


def test_issue_requires_consent_artifact():
    with pytest.raises(ValueError, match="consented_by"):
        issue_proposal_capability("trip_x", "agency_x", consented_by="")


# ---------------------------------------------------------------------------
# Issue -> access roundtrip through the public HTTP surface
# ---------------------------------------------------------------------------


def test_issue_access_roundtrip_and_response_shape_unchanged(monkeypatch):
    trip_id, agency_id = "trip_fnd_roundtrip", "agency_fnd"
    _stub_trip_store(monkeypatch, trip_id, agency_id)

    token, record = issue_proposal_capability(
        trip_id,
        agency_id,
        consented_by="advisor@agency.test",
        purpose="proposal_share",
    )
    assert record.format_version == "v3"
    assert record.trip_id == trip_id
    assert record.agency_id == agency_id
    assert record.consented_by == "advisor@agency.test"
    assert record.purpose == "proposal_share"
    assert record.revoked_at is None
    assert record.expires_at > record.issued_at

    response = client.get(f"/api/public/proposals/{token}")
    assert response.status_code == 200
    data = response.json()
    # Traveler contract (PublicProposalView) unchanged — same keys as before.
    expected_keys = set(PublicProposalView.model_fields.keys())
    assert set(data.keys()) == expected_keys
    assert data["trip_id"] == trip_id
    assert data["destination"] == "Kyoto"
    assert data["title"] == "Kyoto Garden Villa"
    assert data["base_price_usd"] == 7500
    assert data["reality_tier"] == "persisted_observed"


# ---------------------------------------------------------------------------
# TTL enforcement
# ---------------------------------------------------------------------------


def test_expired_token_rejected_store_and_http(monkeypatch):
    trip_id, agency_id = "trip_fnd_expired", "agency_fnd"
    _stub_trip_store(monkeypatch, trip_id, agency_id)
    store = public_proposals.ProposalTokenStore.get_instance()

    token = new_token_material()
    store.issue(
        token=token,
        format_version="v3",
        agency_id=agency_id,
        trip_id=trip_id,
        consented_by="advisor@agency.test",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    is_valid, reason, resolved_trip = verify_proposal_token(token)
    assert is_valid is False
    assert resolved_trip is None

    response = client.get(f"/api/public/proposals/{token}")
    assert response.status_code == 410


# ---------------------------------------------------------------------------
# Revocation: durable, uniform, restart-safe
# ---------------------------------------------------------------------------


def test_revoked_v3_token_rejected_durably(monkeypatch, isolation):
    trip_id, agency_id = "trip_fnd_revoked", "agency_fnd"
    _stub_trip_store(monkeypatch, trip_id, agency_id)
    store = public_proposals.ProposalTokenStore.get_instance()

    token, _record = issue_proposal_capability(trip_id, agency_id, consented_by="advisor@agency.test")
    assert verify_proposal_token(token)[0] is True

    assert store.revoke(token) is True
    is_valid, reason, resolved_trip = verify_proposal_token(token)
    assert is_valid is False
    assert resolved_trip is None

    # Uniform public surface: revoked and expired are indistinguishable.
    expired_token = new_token_material()
    store.issue(
        token=expired_token,
        format_version="v3",
        agency_id=agency_id,
        trip_id=trip_id,
        consented_by="advisor@agency.test",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    unknown_token = new_token_material()
    for failing in (expired_token, unknown_token):
        is_valid_f, reason_f, _ = verify_proposal_token(failing)
        assert is_valid_f is False
        assert reason_f == reason  # same reason -> same HTTP 410 detail

    # Durable across a simulated process restart: a fresh store facade over
    # the same persistent backend (the stand-in for the SQL table) must still
    # see the revocation.
    restarted_store = ProposalTokenStore(backend=store._backend)
    original_instance = ProposalTokenStore._instance
    ProposalTokenStore._instance = restarted_store
    try:
        is_valid_after_restart, _, _ = verify_proposal_token(token)
        assert is_valid_after_restart is False
    finally:
        ProposalTokenStore._instance = original_instance


# ---------------------------------------------------------------------------
# Resource binding
# ---------------------------------------------------------------------------


def test_token_bound_to_its_own_trip_only(monkeypatch):
    trip_a, trip_b, agency_id = "trip_fnd_a", "trip_fnd_b", "agency_fnd"
    _stub_trip_store(monkeypatch, trip_a, agency_id)

    token, record = issue_proposal_capability(trip_a, agency_id, consented_by="advisor@agency.test")
    assert record.trip_id == trip_a

    # Verification only ever resolves the bound trip.
    is_valid, _reason, resolved_trip = verify_proposal_token(token)
    assert is_valid is True
    assert resolved_trip == trip_a

    # The public projection must be scoped to the bound agency+trip: a fetch
    # cannot be steered to another trip's data.
    response = client.get(f"/api/public/proposals/{token}")
    assert response.status_code == 200
    assert response.json()["trip_id"] == trip_a
    assert "trip_fnd_b" not in response.text

    # Journey-graph binding: the credential cannot authorize trip B's graph.
    # The endpoint's first check rejects any trip_id other than the BOUND one
    # — trip B's data is never even looked up with this credential.
    from spine_api import persistence as journey_persistence

    seen = {}
    response_cross = client.get(
        f"/api/public/journey-graph/{trip_b}",
        params={"token": token},
    )
    assert response_cross.status_code == 404
    assert seen == {}  # no lookup ever ran against trip_b

    # And when the BOUND trip is requested, the scoped lookup receives the
    # credential's bound agency+trip (never client-supplied values).
    monkeypatch.setattr(
        journey_persistence.TripStore,
        "get_trip_for_agency",
        lambda requested_trip_id, requested_agency_id: (
            seen.update(trip_id=requested_trip_id, agency_id=requested_agency_id) or None
        ),
    )
    response_bound = client.get(
        f"/api/public/journey-graph/{trip_a}",
        params={"token": token},
    )
    assert seen["trip_id"] == trip_a
    assert seen["agency_id"] == agency_id
    assert response_bound.status_code == 404  # unknown resource fails closed


# ---------------------------------------------------------------------------
# Hashed-at-rest storage
# ---------------------------------------------------------------------------


def test_memory_store_never_persists_raw_token():
    backend = MemoryProposalTokenBackend()
    store = ProposalTokenStore(backend=backend)
    token = new_token_material()
    _created, _record = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd",
        trip_id="trip_fnd_hashed",
        consented_by="advisor@agency.test",
    )
    stored = backend._rows
    assert len(stored) == 1
    row_hash, record = next(iter(stored.items()))
    assert row_hash == hash_token(token)[0]  # keyed by hash
    assert record.token_hash == hash_token(token)[0]
    assert record.lookup_prefix == hash_token(token)[1]
    assert token not in str(record)  # raw material never in the record
    assert token not in str(stored)


@pytest.mark.asyncio
async def test_sql_backend_stores_hash_never_raw_token(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path/'tokens.db'}")
    from spine_api.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[ProposalAccessToken.__table__], checkfirst=True
            )
        )
    backend = SqlProposalTokenBackend(engine=engine, session_maker=async_sessionmaker(engine, expire_on_commit=False))
    store = ProposalTokenStore(backend=backend)

    token = new_token_material()
    created, record = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd_sql",
        trip_id="trip_fnd_sql",
        proposal_id="PROP-ABC123",
        consented_by="advisor@agency.test",
        purpose="proposal_share",
    )
    assert created is True
    assert record.trip_id == "trip_fnd_sql"

    status, looked_up = store.verify(token)
    assert status == TokenStatus.VALID
    assert looked_up is not None

    # Raw token material must not exist anywhere in the durable table.
    async with engine.begin() as conn:
        rows = (
            await conn.execute(text("SELECT token_hash, lookup_prefix, trip_id, agency_id, proposal_id, consented_by, purpose, format_version FROM proposal_access_tokens"))
        ).fetchall()
    assert len(rows) == 1
    persisted = rows[0]
    assert token not in str(persisted)
    assert persisted[0] == hash_token(token)[0]
    assert persisted[1] == hash_token(token)[1]
    assert persisted[2] == "trip_fnd_sql"
    assert persisted[3] == "agency_fnd_sql"
    assert persisted[4] == "PROP-ABC123"
    assert persisted[5] == "advisor@agency.test"
    assert persisted[6] == "proposal_share"
    assert persisted[7] == "v3"

    # Durable revocation.
    assert store.revoke(token) is True
    status_after, record_after = store.verify(token)
    assert status_after == TokenStatus.REVOKED
    assert record_after is None

    await engine.dispose()


# ---------------------------------------------------------------------------
# Idempotent replay / explicit versioning
# ---------------------------------------------------------------------------


def test_issue_replay_is_idempotent_and_refreshes_nothing():
    store = ProposalTokenStore(backend=MemoryProposalTokenBackend())
    token = new_token_material()
    issued_at = datetime.now(timezone.utc) - timedelta(days=3)
    expires_at = issued_at + timedelta(hours=720)
    consented_at = issued_at

    created_first, first = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd",
        trip_id="trip_fnd_replay",
        consented_by="advisor@agency.test",
        issued_at=issued_at,
        expires_at=expires_at,
        consented_at=consented_at,
    )
    created_second, second = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd",
        trip_id="trip_fnd_replay",
        consented_by="someone-else@agency.test",
    )
    assert created_first is True
    assert created_second is False  # replay, not a new credential
    assert second is first  # stored row returned unchanged
    assert second.consented_by == "advisor@agency.test"  # consent NOT overwritten
    assert second.expires_at == expires_at  # TTL NOT refreshed
    assert second.format_version == "v3"  # replay is explicitly versioned


def test_sql_backend_issue_replay_replays_row(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path/'replay.db'}")
    backend = SqlProposalTokenBackend(engine=engine, session_maker=async_sessionmaker(engine, expire_on_commit=False))
    store = ProposalTokenStore(backend=backend)
    token = new_token_material()
    created_first, first = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd",
        trip_id="trip_fnd_replay_sql",
        consented_by="advisor@agency.test",
    )
    created_second, second = store.issue(
        token=token,
        format_version="v3",
        agency_id="agency_fnd",
        trip_id="trip_fnd_replay_sql",
        consented_by="advisor@agency.test",
    )
    assert (created_first, created_second) == (True, False)
    assert first.token_hash == second.token_hash


def test_legacy_v2_registration_via_store_is_supported():
    """Deterministic legacy minting + store registration = idempotent replay."""
    store = ProposalTokenStore(backend=MemoryProposalTokenBackend())
    legacy_token = public_proposals.generate_signed_proposal_token(
        "trip_fnd_legacy", agency_id="agency_fnd", ttl_hours=24
    )
    created_first, _ = store.issue(
        token=legacy_token,
        format_version="v2",
        agency_id="agency_fnd",
        trip_id="trip_fnd_legacy",
        consented_by="advisor@agency.test",
        ttl_hours=24,
    )
    created_second, _ = store.issue(
        token=legacy_token,
        format_version="v2",
        agency_id="agency_fnd",
        trip_id="trip_fnd_legacy",
        consented_by="advisor@agency.test",
        ttl_hours=24,
    )
    assert (created_first, created_second) == (True, False)
    is_valid, _reason, resolved_trip = verify_proposal_token(legacy_token)
    assert is_valid is True  # legacy signed path still verifies independently
    assert resolved_trip == "trip_fnd_legacy"


# ---------------------------------------------------------------------------
# Legacy raw-token revocation files normalize gracefully
# ---------------------------------------------------------------------------


def test_legacy_raw_key_revocation_file_is_normalized(monkeypatch, isolation):
    import json as _json

    legacy_v2_token = public_proposals.generate_signed_proposal_token(
        "trip_fnd_legacy_revoke", agency_id="system", ttl_hours=24
    )
    # A pre-FND-0219 file keyed by RAW token material.
    isolation.mkdir(parents=True, exist_ok=True)
    (isolation / "revoked_tokens.json").write_text(
        _json.dumps({legacy_v2_token: "2026-08-01T00:00:00+00:00"}), encoding="utf-8"
    )

    is_valid, _reason, _trip = verify_proposal_token(legacy_v2_token)
    assert is_valid is False  # legacy revocation still honored

    # And no re-write persists raw material going forward.
    assert public_proposals.revoke_proposal_token(legacy_v2_token) is True
    persisted = _json.loads((isolation / "revoked_tokens.json").read_text())
    assert legacy_v2_token not in persisted
    assert all(len(key) == 64 for key in persisted)  # hash keys only


def test_backend_env_selection_defaults_to_memory(monkeypatch):
    monkeypatch.delenv(PROPOSAL_TOKEN_BACKEND_ENV, raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    ProposalTokenStore.reset_instance()
    try:
        store = ProposalTokenStore.get_instance()
        assert store._backend is None  # memory path
    finally:
        ProposalTokenStore.reset_instance()
