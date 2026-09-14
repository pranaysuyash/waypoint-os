"""X-14 purge propagation — forgetting must reach EVERY hydration key.

ADR-008 council (Addendum 9): a customer may exist under more than one
store key with the same contact identity. Forgetting only the exact
(agency_id, customer_id) key left duplicates hydratable by email — a GDPR
leak. The forget handler now propagates removal across matching contact
identities within the agency.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.routers.customer_memory import (
    CUSTOMER_MEMORY_STORE,
    _find_customer_profile,
    router as customer_memory_router,
)


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(customer_memory_router)
    from spine_api.core.auth import get_current_agency_id

    app.dependency_overrides[get_current_agency_id] = lambda: "agency-x"
    with TestClient(app) as c:
        yield c


def _seed(agency, key, email, name):
    CUSTOMER_MEMORY_STORE[(agency, key)] = {
        "customer_id": key,
        "name": name,
        "normalized_email": email.lower(),
        "normalized_phone": None,
    }


def test_forget_propagates_to_duplicate_contact_keys(client):
    _seed("agency-x", "cust-a", "Jane@Example.com", "jane")
    _seed("agency-x", "cust-b", "jane@example.com", "jane")  # duplicate identity

    resp = client.post("/api/v1/customers/memory/forget", json={"customer_id": "cust-a"})
    assert resp.status_code == 200, resp.text

    # Both keys gone; hydration by the shared email finds nothing.
    assert ("agency-x", "cust-a") not in CUSTOMER_MEMORY_STORE
    assert ("agency-x", "cust-b") not in CUSTOMER_MEMORY_STORE
    assert _find_customer_profile("agency-x", email="jane@example.com") is None


def test_forget_is_agency_scoped(client):
    _seed("agency-x", "cust-a", "sam@example.com", "sam")
    _seed("agency-y", "cust-b", "sam@example.com", "sam")

    resp = client.post("/api/v1/customers/memory/forget", json={"customer_id": "cust-a"})
    assert resp.status_code == 200

    assert ("agency-x", "cust-a") not in CUSTOMER_MEMORY_STORE
    # agency-y's profile must survive (S-08 tenant partition).
    assert ("agency-y", "cust-b") in CUSTOMER_MEMORY_STORE
    assert _find_customer_profile("agency-y", email="sam@example.com") is not None


def teardown_function():
    CUSTOMER_MEMORY_STORE.clear()
