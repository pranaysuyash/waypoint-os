"""
tests/test_pa_corporate_override_authority.py — PA-26: corporate override authority.

Before PA-26 the approve endpoint was self-certifying: any authenticated user
could write a free-text ``approver_name`` as approval evidence, with no role
check, and ``require_pre_approval`` was ignored (one call approved outright).
"""

import uuid

import pytest
from fastapi import HTTPException

from spine_api.models.tenant import Membership, User
from spine_api.persistence import TripStore
from spine_api.routers.corporate_policy import (
    CorporatePolicyRules,
    OverrideRequest,
    approve_corporate_policy_override,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _principal(user_id: str, email: str, role: str) -> tuple[Membership, User]:
    membership = Membership(user_id=user_id, agency_id="agency_pa26", role=role, is_primary=True)
    user = User(id=user_id, email=email, is_active=True)
    return membership, user


def _seed_trip() -> str:
    trip_id = f"trip_pa26_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "agency_pa26",
            "status": "assigned",
            "destination": "Tokyo",
            "strategy": {"recommended_option": {"cost": 3000.0}},
        },
        agency_id="agency_pa26",
    )
    return trip_id


def _approve(trip_id: str, membership: Membership, user: User):
    return approve_corporate_policy_override(
        trip_id=trip_id,
        body=OverrideRequest(
            trip_id=trip_id,
            approver_name="Free Text Name (ignored)",
            reason="policy exception",
        ),
        agency_id="agency_pa26",
        membership=membership,
        current_user=user,
    )


def test_non_admin_role_is_rejected_403():
    trip_id = _seed_trip()
    membership, user = _principal("u_agent", "agent@x.test", "senior_agent")
    with pytest.raises(HTTPException) as excinfo:
        _approve(trip_id, membership, user)
    assert excinfo.value.status_code == 403
    assert "owner or admin" in excinfo.value.detail
    stored = TripStore.get_trip(trip_id)
    assert "corporate_policy_override" not in stored


def test_first_approval_stages_pending_second_approval():
    trip_id = _seed_trip()
    membership, user = _principal("u_owner_1", "owner1@x.test", "owner")
    response = _approve(trip_id, membership, user)

    assert response.override_approved is False
    assert response.pending_second_approval is True
    assert response.status == "pending_second_approval"

    stored = TripStore.get_trip(trip_id)
    override = stored["corporate_policy_override"]
    assert override["approved"] is False
    assert override["status"] == "pending_second_approval"
    assert override["first_approved_by_id"] == "u_owner_1"
    # PA-26: approver identity is the principal; the free-text name is ignored.
    assert override["first_approved_by"] == "owner1@x.test"
    assert override["first_approved_by"] != "Free Text Name (ignored)"


def test_second_approval_by_same_principal_is_rejected_409():
    trip_id = _seed_trip()
    membership, user = _principal("u_owner_1", "owner1@x.test", "owner")
    _approve(trip_id, membership, user)

    with pytest.raises(HTTPException) as excinfo:
        _approve(trip_id, membership, user)
    assert excinfo.value.status_code == 409
    assert "distinct owner/admin" in excinfo.value.detail
    stored = TripStore.get_trip(trip_id)
    assert stored["corporate_policy_override"]["approved"] is False


def test_second_approval_by_distinct_admin_finalizes():
    trip_id = _seed_trip()
    first_membership, first_user = _principal("u_owner_1", "owner1@x.test", "owner")
    _approve(trip_id, first_membership, first_user)

    second_membership, second_user = _principal("u_admin_1", "admin1@x.test", "admin")
    response = _approve(trip_id, second_membership, second_user)

    assert response.override_approved is True
    assert response.status == "approved"
    assert response.pending_second_approval is False
    assert response.approved_by == "admin1@x.test"

    stored = TripStore.get_trip(trip_id)
    override = stored["corporate_policy_override"]
    assert override["approved"] is True
    assert override["approved_by"] == "admin1@x.test"
    # Dual-control evidence is preserved on the durable record.
    assert override["first_approved_by"] == "owner1@x.test"


def test_no_pre_approval_policy_approves_in_single_call(monkeypatch):
    from spine_api.routers import corporate_policy as cp_module

    class NoPreApprovalPolicy(CorporatePolicyRules):
        require_pre_approval: bool = False

    monkeypatch.setattr(cp_module, "CorporatePolicyRules", NoPreApprovalPolicy)
    trip_id = _seed_trip()
    membership, user = _principal("u_admin_2", "admin2@x.test", "admin")
    response = _approve(trip_id, membership, user)
    assert response.override_approved is True
    assert response.pending_second_approval is False
    stored = TripStore.get_trip(trip_id)
    assert stored["corporate_policy_override"]["approved"] is True
