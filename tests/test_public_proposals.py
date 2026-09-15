import os
import json
import subprocess
import sys

import pytest
from starlette.testclient import TestClient

import spine_api.routers.public_proposals as public_proposals
from spine_api.routers.public_proposals import (
    _require_signing_key,
    generate_proposal_token,
    generate_signed_proposal_token,
    revoke_proposal_token,
    verify_proposal_token,
)
from spine_api.server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_revocation_store(tmp_path, monkeypatch):
    """PT-05: revocations persist to disk — point tests at a temp store and
    reset the in-memory view so tests stay order-independent."""
    monkeypatch.setattr(public_proposals, "_REVOCATIONS_PATH", tmp_path / "revoked_tokens.json")
    monkeypatch.setattr(public_proposals, "_REVOKED_TOKENS", {})
    # The rich allowlisted fixtures are intentionally test-only. Production
    # callers must opt in explicitly via PUBLIC_PROPOSAL_DEMO_MODE=1.
    monkeypatch.setenv("PUBLIC_PROPOSAL_DEMO_MODE", "1")
    public_proposals._PROPOSAL_VIEW_CACHE.clear()
    # FND-0219: credential lifecycle tests must run against the in-memory
    # backend regardless of any ambient backend/DATABASE_URL configuration.
    from spine_api.services.proposal_token_store import MemoryProposalTokenBackend

    monkeypatch.setattr(
        public_proposals.ProposalTokenStore,
        "_instance",
        public_proposals.ProposalTokenStore(backend=MemoryProposalTokenBackend()),
    )


def test_generate_proposal_token_deterministic():
    trip_id = "trip_2333bff6434d"
    token1 = generate_proposal_token(trip_id, "agency_1")
    token2 = generate_proposal_token(trip_id, "agency_1")
    assert token1 == token2
    assert token1.startswith("prop_")


# ---------------------------------------------------------------------------
# PT-01 (S-01): signing key is required, no committed fallback
# ---------------------------------------------------------------------------

def test_missing_signing_key_raises(monkeypatch):
    monkeypatch.delenv("PROPOSAL_SIGNING_KEY", raising=False)
    with pytest.raises(RuntimeError, match="PROPOSAL_SIGNING_KEY"):
        _require_signing_key()


@pytest.mark.parametrize("weak_key", ["short", "waypoint_secret_proposal_key_2026", "change-me-to-a-random-secret"])
def test_weak_or_placeholder_signing_key_raises(monkeypatch, weak_key):
    monkeypatch.setenv("PROPOSAL_SIGNING_KEY", weak_key)
    with pytest.raises(RuntimeError, match="too weak|placeholder"):
        _require_signing_key()


def test_import_fails_without_signing_key():
    """Subprocess proof: importing the router raises RuntimeError when the key
    is unset. The child env pre-seeds PROPOSAL_SIGNING_KEY as empty so the
    local .env cannot satisfy it (load_project_env never overrides keys that
    already exist in the environment)."""
    result = subprocess.run(
        [sys.executable, "-c", "import spine_api.routers.public_proposals"],
        capture_output=True,
        text=True,
        env={**os.environ, "PROPOSAL_SIGNING_KEY": ""},
        timeout=120,
    )
    assert result.returncode != 0
    assert "PROPOSAL_SIGNING_KEY is not set" in result.stderr


# ---------------------------------------------------------------------------
# PT-02 (S-02): legacy length-heuristic bypass is gone; only exact demo
# token strings still resolve
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "junk",
    [
        "A" * 40,  # >=16 chars of junk — previously accepted as legacy_ok
        "prop_legacy_freebie_999",  # junk with prop_ prefix and underscores
        "prop_trip_x_system_9999999999_" + "a" * 64,  # signed-shaped forgery
        "totally-not-a-token-but-long-enough",
    ],
)
def test_forged_junk_tokens_rejected(junk):
    is_valid, _reason, trip_id = verify_proposal_token(junk)
    assert is_valid is False
    assert trip_id is None


def test_forged_junk_token_http_unauthorized():
    resp = client.get(f"/api/public/proposals/{'A' * 40}")
    assert resp.status_code == 401


@pytest.mark.parametrize("demo_token", sorted(public_proposals._DEMO_TOKEN_ALLOWLIST))
def test_demo_allowlist_tokens_still_resolve(demo_token):
    is_valid, reason, trip_id = verify_proposal_token(demo_token)
    assert is_valid, reason
    assert trip_id == "trip_legacy"


def test_demo_allowlist_is_rejected_without_explicit_demo_gate(monkeypatch):
    """A recognized fixture token must not expose fabricated content by default."""
    monkeypatch.delenv("PUBLIC_PROPOSAL_DEMO_MODE", raising=False)

    response = client.get("/api/public/proposals/prop_demo_italy_123")

    assert response.status_code == 404
    assert "resource" in response.json()["detail"].lower()


def test_demo_gate_precedes_cached_fixture(monkeypatch):
    """Disabling demo mode cannot be bypassed by a same-process registry row."""
    first = client.get("/api/public/proposals/prop_demo_italy_123")
    assert first.status_code == 200

    monkeypatch.delenv("PUBLIC_PROPOSAL_DEMO_MODE", raising=False)
    second = client.get("/api/public/proposals/prop_demo_italy_123")

    assert second.status_code == 404


def test_signed_token_requires_persisted_agency_bound_proposal(monkeypatch):
    """A valid signature alone cannot mint a proposal resource."""
    agency_id = "agency_bound_1"
    trip_id = "trip_bound_1"
    token = generate_signed_proposal_token(trip_id, agency_id=agency_id, ttl_hours=24)

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

    response = client.get(f"/api/public/proposals/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["trip_id"] == trip_id
    assert data["destination"] == "Kyoto"
    assert data["title"] == "Kyoto Garden Villa"
    assert data["base_price_usd"] == 7500
    assert data["days"] == []
    assert data["available_options"] == []
    assert "Italy" not in response.text


def test_signed_token_for_missing_or_foreign_resource_is_not_fabricated(monkeypatch):
    """Unknown and cross-agency signed claims both fail closed at resource lookup."""
    monkeypatch.setattr(public_proposals.TripStore, "get_trip_for_agency", lambda *_args: None)
    token = generate_signed_proposal_token("trip_not_persisted", agency_id="agency_other", ttl_hours=24)

    response = client.get(f"/api/public/proposals/{token}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Proposal resource not found or link expired"


# ---------------------------------------------------------------------------
# PT-03/PT-04 (S-03): agency is embedded in the token and verified from the
# token's own fields (no guess-loop, no hardcoded agency list)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "agency_id",
    [
        "system",
        "agency_42",
        "agency_test",  # contains '_' — exercises the ~5F escaping
        "acme-travel-co",
        "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",  # a plain UUID agency id
    ],
)
def test_round_trip_with_non_default_agency(agency_id):
    trip_id = "trip_roundtrip_1"
    token = generate_signed_proposal_token(trip_id=trip_id, agency_id=agency_id, ttl_hours=24)
    assert token.startswith("prop_")
    is_valid, reason, resolved_trip = verify_proposal_token(token)
    assert is_valid, reason
    assert resolved_trip == trip_id


def test_agency_underscore_is_normalized_in_token():
    """'_' is the field delimiter, so agency ids must not carry raw '_'."""
    assert public_proposals._encode_agency_field("agency_test") == "agency~5Ftest"


def test_noncanonical_agency_encoding_is_rejected():
    """The signed value must use the issuer's canonical wire encoding."""
    token = generate_signed_proposal_token("trip_canonical_1", agency_id="agency/slash", ttl_hours=24)
    noncanonical = token.replace("agency~2Fslash", "agency/slash", 1)
    is_valid, reason, trip_id = verify_proposal_token(noncanonical)
    assert is_valid is False
    assert "malformed" in reason.lower()
    assert trip_id is None


def test_empty_agency_cannot_issue_unscoped_token():
    with pytest.raises(ValueError, match="agency_id"):
        generate_signed_proposal_token("trip_unscoped_1", agency_id="", ttl_hours=24)


@pytest.mark.parametrize(
    "agency_id",
    [
        "system",
        "agency_test",
        "acme-travel",
        "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
        "100%",  # percent-decoding bait: must survive HTTP path normalization
        "a~b",  # literal escape char
        "агентство",  # multi-byte UTF-8
        "",
    ],
)
def test_agency_field_codec_round_trip(agency_id):
    field = public_proposals._encode_agency_field(agency_id)
    # Percent-decoding intermediaries must not alter the field.
    from urllib.parse import unquote

    assert unquote(field) == field
    assert public_proposals._decode_agency_field(field) == agency_id


def test_signed_token_http_requires_persisted_resource_non_default_agency():
    """HTTP verification must not turn a valid claim into fabricated content."""
    token = generate_signed_proposal_token("trip_http_agency_1", agency_id="agency_42", ttl_hours=24)
    resp = client.get(f"/api/public/proposals/{token}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Proposal resource not found or link expired"


# ---------------------------------------------------------------------------
# PT-06 (S-11b) + TTL: full-length signature, expired tokens rejected
# ---------------------------------------------------------------------------

def test_signature_is_full_digest():
    token = generate_signed_proposal_token("trip_sig_len_1", agency_id="system")
    signature = token.rsplit("_", 1)[-1]
    assert len(signature) == 64  # full SHA-256 hex digest (256-bit), not [:16]


def test_expired_token_rejected():
    token = generate_signed_proposal_token("trip_expired_1", agency_id="system", ttl_hours=-1)
    is_valid, reason, _trip_id = verify_proposal_token(token)
    assert is_valid is False
    assert "expired" in reason.lower()


# ---------------------------------------------------------------------------
# PT-05 (S-11a): revocation persists (survives a simulated restart)
# ---------------------------------------------------------------------------

def test_revoked_token_rejected_and_persisted():
    token = generate_signed_proposal_token("trip_revoked_1", agency_id="system", ttl_hours=24)
    assert verify_proposal_token(token)[0] is True

    assert revoke_proposal_token(token) is True
    is_valid, reason, _ = verify_proposal_token(token)
    assert is_valid is False
    assert "revoked" in reason.lower()

    # Simulate a process restart: wipe the in-memory view and reload from disk.
    public_proposals._REVOKED_TOKENS.clear()
    public_proposals._load_revocations()
    is_valid_after_restart, reason_after_restart, _ = verify_proposal_token(token)
    assert is_valid_after_restart is False
    assert "revoked" in reason_after_restart.lower()
    assert public_proposals._REVOCATIONS_PATH.exists()


def test_revocation_write_merges_another_workers_update():
    """A concurrent worker's revocation must not be lost by read/replace.

    FND-0219: the store is hash-keyed — raw token material is never
    persisted. Legacy raw keys written by another worker are normalized
    (re-keyed by hashing) on load/merge.
    """
    first = generate_signed_proposal_token("trip_revoked_merge_1", agency_id="system", ttl_hours=24)
    second = generate_signed_proposal_token("trip_revoked_merge_2", agency_id="system", ttl_hours=24)
    public_proposals._REVOCATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    public_proposals._REVOCATIONS_PATH.write_text(
        json.dumps({public_proposals.hash_token(first)[0]: "other-worker"}), encoding="utf-8"
    )
    public_proposals._REVOKED_TOKENS[public_proposals.hash_token(second)[0]] = "this-worker"

    with public_proposals._revocations_lock:
        assert public_proposals._persist_revocations_locked() is True

    persisted = json.loads(public_proposals._REVOCATIONS_PATH.read_text(encoding="utf-8"))
    assert set(persisted) == {public_proposals.hash_token(first)[0], public_proposals.hash_token(second)[0]}
    # Raw credential material must never appear in the durable file.
    assert first not in persisted and second not in persisted


def test_verification_observes_revocation_written_after_import():
    token = generate_signed_proposal_token("trip_revoked_reload_1", agency_id="system", ttl_hours=24)
    assert verify_proposal_token(token)[0] is True
    public_proposals._REVOCATIONS_PATH.write_text(json.dumps({token: "other-worker"}), encoding="utf-8")
    is_valid, reason, trip_id = verify_proposal_token(token)
    assert is_valid is False
    assert "revoked" in reason.lower()
    assert trip_id is None


def test_corrupt_revocation_store_fails_closed():
    token = generate_signed_proposal_token("trip_revocation_store_corrupt", agency_id="system", ttl_hours=24)
    public_proposals._REVOCATIONS_PATH.write_text("[]", encoding="utf-8")
    is_valid, reason, trip_id = verify_proposal_token(token)
    assert is_valid is False
    assert "revocation store" in reason.lower()
    assert trip_id is None


def test_get_public_proposal_by_token():
    token = "prop_demo_italy_123"
    response = client.get(f"/api/public/proposals/{token}")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == token
    assert "destination" in data
    assert len(data["days"]) > 0
    assert len(data["available_options"]) > 0
    assert data["status"] == "open"


def test_calculate_proposal_options():
    token = "prop_calc_test_456"
    # First get proposal
    init_res = client.get(f"/api/public/proposals/{token}")
    assert init_res.status_code == 200
    base_price = init_res.json()["base_price_usd"]

    # Select hotel upgrade option
    calc_res = client.post(
        f"/api/public/proposals/{token}/calculate",
        json={"selected_option_ids": ["opt_hotel_upgrade"]},
    )
    assert calc_res.status_code == 200
    updated_data = calc_res.json()
    assert updated_data["selected_total_price_usd"] == round(base_price + 450.0, 2)


def test_accept_proposal_success_and_validation():
    token = "prop_accept_test_789"
    # Missing consent should fail with 400
    fail_res = client.post(
        f"/api/public/proposals/{token}/accept",
        json={
            "signer_name": "Priya Sharma",
            "signer_email": "priya@example.com",
            "selected_option_ids": [],
            "e_signature_consent": False,
        },
    )
    assert fail_res.status_code == 400

    # With consent should succeed
    success_res = client.post(
        f"/api/public/proposals/{token}/accept",
        json={
            "signer_name": "Priya Sharma",
            "signer_email": "priya@example.com",
            "selected_option_ids": ["opt_wine_tour"],
            "e_signature_consent": True,
        },
    )
    assert success_res.status_code == 200
    data = success_res.json()
    assert data["status"] == "accepted"
    assert "Priya Sharma" in data["accepted_by"]
    assert data["accepted_at"] is not None
