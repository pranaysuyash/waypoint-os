"""
tests/test_cross_tenant_router_probe.py — Cross-tenant HTTP probes for the
routers converted to get_rls_db (A-19 / RQ-03, 2026-08-30).

Mechanism: under SPINE_API_DISABLE_AUTH the membership dependency trusts the
token's agency_id claim, so minting two tokens with different agencies runs
each request as a genuinely distinct tenant. The probes pin the app-level
scoping that is the *active* guard for the RLS-exempt tables (audit_logs,
ghost_workflows, ...) and fail closed on any leak.
"""

import os
from datetime import timedelta

import pytest

os.environ["RUNNING_TESTS"] = "1"

from spine_api.core.security import create_access_token

AGENCY_A = "tenant_probe_agency_a"
AGENCY_B = "tenant_probe_agency_b"


def _headers_for(agency_id: str) -> dict:
    token = create_access_token(
        user_id=f"user_{agency_id}",
        agency_id=agency_id,
        role="owner",
        expires_delta=timedelta(hours=2),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def probe_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _ensure_agencies() -> None:
    """Insert the two probe agencies idempotently (additive test data only).

    Endpoints that resolve the full Agency object (team router via
    get_current_agency) need real rows; get_current_agency_id-only endpoints
    work from the token claim alone.
    """
    import asyncio

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from spine_api.models.tenant import Agency

    async def _insert():
        engine = create_async_engine(
            os.environ.get(
                "DATABASE_URL",
                "postgresql+asyncpg://waypoint:waypoint_dev_password@localhost:5432/waypoint_os",
            )
        )
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                for agency_id in (AGENCY_A, AGENCY_B):
                    exists = await session.scalar(
                        select(Agency.id).where(Agency.id == agency_id)
                    )
                    if not exists:
                        session.add(
                            Agency(
                                id=agency_id,
                                name=f"Tenant Probe {agency_id[-1].upper()}",
                                slug=f"tenant-probe-{agency_id[-1]}",
                                is_test=True,
                            )
                        )
                await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(_insert())


def test_ghost_workflow_read_fails_closed_cross_tenant(session_client):
    """RQ-03: ghost_workflows is RLS-exempt — the read path must stay
    agency-checked. Agency B must get 404 (existence not confirmed)."""
    # The SQL schema intentionally enforces the agency FK; seed the two
    # synthetic tenants before exercising the cross-tenant read contract.
    _ensure_agencies()
    created = session_client.post(
        "/frontier/ghost/workflows",
        json={"trip_id": "tenant_probe_trip_001", "task_type": "monitor", "autonomic_level": 0},
        headers=_headers_for(AGENCY_A),
    )
    assert created.status_code == 200, created.text
    workflow_id = created.json()["id"]

    own = session_client.get(
        f"/frontier/ghost/workflows/{workflow_id}", headers=_headers_for(AGENCY_A)
    )
    assert own.status_code == 200, own.text
    assert own.json()["agency_id"] == AGENCY_A

    other = session_client.get(
        f"/frontier/ghost/workflows/{workflow_id}", headers=_headers_for(AGENCY_B)
    )
    assert other.status_code == 404, f"Agency B saw Agency A's ghost workflow: {other.text}"


def test_team_members_list_scoped_to_caller_agency(session_client):
    _ensure_agencies()
    res = session_client.get("/api/team/members", headers=_headers_for(AGENCY_B))
    assert res.status_code == 200, res.text
    for member in res.json().get("items", []):
        leaked_agency = member.get("agency_id")
        assert leaked_agency in (None, AGENCY_B), f"cross-tenant member leaked: {member}"


def test_audit_list_scoped_to_caller_agency(session_client):
    res_a = session_client.get("/api/audit", headers=_headers_for(AGENCY_A))
    assert res_a.status_code == 200, res_a.text
    for entry in res_a.json().get("entries", []):
        assert entry.get("agency_id") == AGENCY_A, f"cross-tenant audit row leaked: {entry}"

    res_b = session_client.get("/api/audit", headers=_headers_for(AGENCY_B))
    assert res_b.status_code == 200, res_b.text
    for entry in res_b.json().get("entries", []):
        assert entry.get("agency_id") == AGENCY_B, f"cross-tenant audit row leaked: {entry}"


def test_integrations_list_available_to_each_agency(session_client):
    """Post-conversion smoke: get_rls_db adoption must not break the surface."""
    for agency in (AGENCY_A, AGENCY_B):
        res = session_client.get("/api/integrations", headers=_headers_for(agency))
        assert res.status_code == 200, res.text
        assert isinstance(res.json().get("integrations"), list)


def test_team_member_detail_fails_closed_cross_tenant(session_client):
    """membership_service.get_member is scoped by (member_id, agency_id) — a
    foreign membership id must 404, not return the row."""
    res = session_client.get(
        "/api/team/members/00000000-0000-0000-0000-000000000000",
        headers=_headers_for(AGENCY_B),
    )
    assert res.status_code == 404, res.text
