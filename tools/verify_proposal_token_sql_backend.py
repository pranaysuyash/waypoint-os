"""Runtime verification: ProposalTokenStore SQL backend against the real dev
Postgres (waypoint_os). Additive only — creates the proposal_access_tokens
table via checkfirst and leaves one revoked, clearly test-scoped row.

Usage: .venv/bin/python tools/verify_proposal_token_sql_backend.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(".env")

from spine_api.services.proposal_token_store import (  # noqa: E402 (needs .env loaded)
    ProposalTokenStore,
    SqlProposalTokenBackend,
    TokenStatus,
    hash_token,
    new_token_material,
)

# Test-scoped binding values for this verification row (additive only).
_VERIFY_TRIP_ID = "trip_sql_verify_fnd0219"
_VERIFY_AGENCY_ID = "agency-sql-verify"


def main() -> int:
    assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set (.env)"
    backend = SqlProposalTokenBackend()
    store = ProposalTokenStore(backend=backend)

    token = new_token_material()
    created, record = store.issue(
        token=token,
        format_version="v3",
        agency_id=_VERIFY_AGENCY_ID,
        trip_id=_VERIFY_TRIP_ID,
        proposal_id="PROP-SQLVERIFY",
        consented_by="tooling:fnd0219_runtime_check",
        purpose="runtime_verification",
        ttl_hours=1,
    )
    assert created is True, "issue should create a new row"
    print(f"1. issue -> created row prefix={record.lookup_prefix} trip={record.trip_id}")

    status, looked_up = store.verify(token)
    assert status == TokenStatus.VALID and looked_up is not None
    print(f"2. verify -> {status.value}, bound trip={looked_up.trip_id}")

    # Idempotent replay against real Postgres unique constraint.
    created2, replayed = store.issue(
        token=token,
        format_version="v3",
        agency_id=_VERIFY_AGENCY_ID,
        trip_id=_VERIFY_TRIP_ID,
        consented_by="someone-else",
        ttl_hours=99,
    )
    assert created2 is False and replayed.consented_by == "tooling:fnd0219_runtime_check"
    assert replayed.expires_at == record.expires_at, "replay must not refresh TTL"
    print("3. replay -> idempotent, consent + TTL not refreshed")

    # Raw material must not exist in the table: inspect the durable row via
    # the same ORM lookup the backend uses (token_hash is the only key).
    raw_lookup = backend.lookup(hash_token(token)[0])
    assert raw_lookup is not None
    assert raw_lookup.token_hash == hash_token(token)[0]
    assert raw_lookup.lookup_prefix == hash_token(token)[1]
    assert raw_lookup.trip_id == _VERIFY_TRIP_ID
    assert raw_lookup.agency_id == _VERIFY_AGENCY_ID
    assert raw_lookup.purpose == "runtime_verification"
    assert token not in str(raw_lookup)
    print("4. storage -> sha256 hash + prefix only, raw material absent")

    assert store.revoke(token) is True
    status_after, rec_after = store.verify(token)
    assert status_after == TokenStatus.REVOKED and rec_after is None
    print(f"5. revoke -> {status_after.value} (durable row revoked_at set)")

    print("OK: SQL backend verified against real Postgres (5/5 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
