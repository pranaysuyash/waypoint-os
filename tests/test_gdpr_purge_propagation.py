"""X-14 purge propagation — forgetting must reach EVERY hydration key.

ADR-008 council (Addendum 9): a customer may exist under more than one
customer_id with the same contact identity. Forgetting only the exact id
left duplicates hydratable by email — a GDPR leak. The forget handler
propagates removal across matching contact identities within the agency.

FND-0060 residual: the store behind this is now the durable SQL table
``customer_memory_profiles`` (RLS-scoped) instead of the process-local dict.
Duplicates that predate a normalization fix are seeded directly through the
ORM (the exact legacy-shape rows the propagation exists to reach), then the
HTTP forget must remove every one of them — and never touch another
agency's rows.
"""

import os
import uuid

import pytest

os.environ["RUNNING_TESTS"] = "1"

AGENCY_X = "agency_mem_gdpr_x"
AGENCY_Y = "agency_mem_gdpr_y"


@pytest.fixture()
def gdpr_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    yield


@pytest.fixture(autouse=True)
def materialize_gdpr_agencies(boundary_principal_factory):
    boundary_principal_factory("usr_mem_gdpr_x", AGENCY_X)
    boundary_principal_factory("usr_mem_gdpr_y", AGENCY_Y)


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def _seed_via_sql(agency: str, customer_id: str, email: str, name: str) -> str:
    """Insert a profile row directly (legacy-shape duplicate the X-14
    propagation exists to reach — /remember's find-by-identity would have
    merged these). Returns the row's primary key for later get()-verification.
    """
    from spine_api.core.rls import rls_session
    from spine_api.models.tenant import CustomerMemoryProfile

    row_id = uuid.uuid4().hex

    async def _insert() -> str:
        async with rls_session(agency) as session:
            session.add(
                CustomerMemoryProfile(
                    id=row_id,
                    agency_id=agency,
                    customer_id=customer_id,
                    name=name,
                    email=email,
                    normalized_email=email.lower(),
                )
            )
            await session.commit()
            return row_id

    return _run(_insert())


def _row_exists(agency: str, row_id: str) -> bool:
    """PK lookup through the canonical rls_session seam: True when the row is
    still present under this agency's RLS context."""
    from spine_api.core.rls import rls_session
    from spine_api.models.tenant import CustomerMemoryProfile

    async def _read() -> bool:
        async with rls_session(agency) as session:
            return await session.get(CustomerMemoryProfile, row_id) is not None

    return _run(_read())


def _forget(client, agency: str, customer_id: str):
    return client.post(
        "/api/v1/customers/memory/forget",
        json={"customer_id": customer_id},
        headers={"X-Agency-ID": agency},
    )


def test_forget_propagates_to_duplicate_contact_ids(session_client, gdpr_env):
    # Two ids in the same agency sharing one contact identity (the legacy
    # duplicate shape X-14 exists to reach). cust_b is seeded directly.
    # Run-unique ids: the durable table persists across runs in the shared
    # test database, so ids from a previous run must never collide.
    run = uuid.uuid4().hex[:6]
    id_a = _seed_via_sql(AGENCY_X, f"cust_a_{run}", "jane@example.com", "jane")
    id_b = _seed_via_sql(AGENCY_X, f"cust_b_{run}", "jane@example.com", "jane")
    assert _row_exists(AGENCY_X, id_a)
    assert _row_exists(AGENCY_X, id_b)

    resp = _forget(session_client, AGENCY_X, f"cust_a_{run}")
    assert resp.status_code == 200, resp.text

    # Propagation erased EVERY same-identity row, not just the exact id.
    assert not _row_exists(AGENCY_X, id_a)
    assert not _row_exists(AGENCY_X, id_b)
    # Hydration by the shared email finds nothing.
    lookup = session_client.get(
        "/api/v1/customers/memory",
        params={"email": "jane@example.com"},
        headers={"X-Agency-ID": AGENCY_X},
    )
    assert lookup.json() is None


def test_forget_is_agency_scoped(session_client, gdpr_env):
    # Run-unique ids: the durable table persists across tests in the shared
    # test database, so ids from a previous run must never collide.
    run = uuid.uuid4().hex[:6]
    id_x = _seed_via_sql(AGENCY_X, f"cust_a_{run}", "sam@example.com", "sam")
    id_y = _seed_via_sql(AGENCY_Y, f"cust_b_{run}", "sam@example.com", "sam")

    resp = _forget(session_client, AGENCY_X, f"cust_a_{run}")
    assert resp.status_code == 200

    # agency-x row gone; agency-y's profile must survive (S-08 partition).
    assert not _row_exists(AGENCY_X, id_x)
    assert _row_exists(AGENCY_Y, id_y)
