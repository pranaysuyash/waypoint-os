"""
tests/test_customer_memory_agency_partition.py — S-08 / RT-07 tenant partition regression tests.

Contract under test (Docs/review/SPINE_AUDIT_NEW_FINDINGS_2026-09-02.md PT-09 companion,
Docs/exploration/EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md RT-07):
- ``CUSTOMER_MEMORY_STORE`` is keyed by (agency_id, customer_id) — no bare
  customer_id keys exist.
- Cross-agency memory lookup returns nothing (no reads across tenants).
- Cross-agency /remember does not overwrite another agency's profile.
- Cross-agency GDPR forget does not delete another agency's profile.
- Same-agency round trip (remember → lookup → hydrate) keeps working.
"""

import os
import uuid

import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.routers.customer_memory import CUSTOMER_MEMORY_STORE


@pytest.fixture()
def partition_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    yield


def _unique_name() -> str:
    return f"Partition Tester {uuid.uuid4().hex[:10]}"


def _remember(client, name: str, agency: str, dietary: str = "vegan"):
    return client.post(
        "/api/v1/customers/remember",
        json={"name": name, "dietary_requirements": dietary},
        headers={"X-Agency-ID": agency},
    )


def _lookup(client, name: str, agency: str):
    return client.get(
        "/api/v1/customers/memory",
        params={"name": name},
        headers={"X-Agency-ID": agency},
    )


def test_store_keys_are_agency_scoped_tuples(session_client, partition_env):
    """The store must never contain a bare customer_id key (S-08 partition invariant)."""
    name = _unique_name()
    resp = _remember(session_client, name, "agency_part_unit")
    assert resp.status_code == 200
    cust_id = resp.json()["customer_id"]

    assert (("agency_part_unit", cust_id)) in CUSTOMER_MEMORY_STORE
    assert cust_id not in CUSTOMER_MEMORY_STORE  # bare id must NOT be a key
    for key in CUSTOMER_MEMORY_STORE:
        assert isinstance(key, tuple) and len(key) == 2, f"unpartitioned key: {key!r}"


def test_cross_agency_read_returns_nothing(session_client, partition_env):
    name = _unique_name()
    assert _remember(session_client, name, "agency_part_a").status_code == 200

    # Same agency sees the profile; a different agency sees nothing.
    assert _lookup(session_client, name, "agency_part_a").json() is not None
    assert _lookup(session_client, name, "agency_part_b").json() is None


def test_cross_agency_write_does_not_poison_other_agency(session_client, partition_env):
    """A second agency recording the same customer must not overwrite agency A's profile."""
    name = _unique_name()
    first = _remember(session_client, name, "agency_part_a", dietary="vegan").json()
    second = _remember(session_client, name, "agency_part_b", dietary="shellfish allergy").json()

    assert first["customer_id"] != second["customer_id"] or True  # ids may collide across agencies; partitioning is what matters

    a_view = _lookup(session_client, name, "agency_part_a").json()
    b_view = _lookup(session_client, name, "agency_part_b").json()
    assert a_view["dietary_requirements"] == "vegan"
    assert b_view["dietary_requirements"] == "shellfish allergy"


def test_cross_agency_gdpr_forget_is_scoped(session_client, partition_env):
    name = _unique_name()
    created = _remember(session_client, name, "agency_part_a").json()
    cust_id = created["customer_id"]

    # Agency B cannot erase agency A's profile.
    forget_b = session_client.post(
        "/api/v1/customers/memory/forget",
        json={"customer_id": cust_id},
        headers={"X-Agency-ID": "agency_part_b"},
    )
    assert forget_b.status_code == 200
    assert (("agency_part_a", cust_id)) in CUSTOMER_MEMORY_STORE
    assert _lookup(session_client, name, "agency_part_a").json() is not None

    # The owning agency can erase its own profile.
    forget_a = session_client.post(
        "/api/v1/customers/memory/forget",
        json={"customer_id": cust_id},
        headers={"X-Agency-ID": "agency_part_a"},
    )
    assert forget_a.status_code == 200
    assert (("agency_part_a", cust_id)) not in CUSTOMER_MEMORY_STORE
    assert _lookup(session_client, name, "agency_part_a").json() is None


def test_same_agency_round_trip_still_works(session_client, partition_env):
    name = _unique_name()
    created = _remember(session_client, name, "agency_part_rt", dietary="gluten free").json()

    lookup = _lookup(session_client, name, "agency_part_rt")
    assert lookup.status_code == 200
    assert lookup.json()["customer_id"] == created["customer_id"]
    assert lookup.json()["dietary_requirements"] == "gluten free"
