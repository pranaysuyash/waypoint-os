"""Contract regressions for the honest insurance quote preview.

Introduced through failing-first checks, these tests preserve the implemented
quote evidence boundary. Prices remain illustrative, while policy
eligibility and timing stay explicitly unevaluated until a versioned provider
rule and the required evidence exist.
"""

from datetime import datetime, timedelta, timezone
import os
import uuid

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only-32byt")

from spine_api.persistence import TripStore


AGENCY = "insurance_quote_evidence_agency"


@pytest.fixture(autouse=True)
def quote_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


@pytest.fixture(autouse=True)
def materialize_attach_tenant(boundary_principal_factory):
    """F-31 (FND-0118): the attach path now writes the canonical SQL
    BookingConfirmation whose agency_id is an FK to agencies.id, so the tenant
    must exist in SQL before attach tests run.

    Uses the shared additive factory (ON CONFLICT DO NOTHING): existing test
    data is never overwritten or removed.
    """
    boundary_principal_factory("usr_insurance_attach", AGENCY)


def _headers(agency_id: str = AGENCY) -> dict[str, str]:
    return {"X-Agency-ID": agency_id}


def _make_trip(*, agency_id: str = AGENCY) -> str:
    trip_id = f"trip_insurance_{uuid.uuid4().hex[:12]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": agency_id,
            "status": "new",
            "destination": "Rome",
        },
        agency_id=agency_id,
    )
    return trip_id


def _attach_body(trip_id: str, **overrides) -> dict:
    body = {
        "trip_id": trip_id,
        "selected_plan_id": "ins_cfar_03",
        "policy_number": f"POL-{uuid.uuid4().hex[:8].upper()}",
        "insurance_provider": "Acme Insurance Co",
        "premium_paid_usd": 500.0,
    }
    body.update(overrides)
    return body


def _attach(session_client, trip_id: str, **overrides):
    return session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy",
        json=_attach_body(trip_id, **overrides),
        headers=_headers(),
    )


def _run_coro(coro):
    import asyncio

    return asyncio.run(coro)


def _read_confirmation(confirmation_id: str) -> dict:
    """Read one canonical confirmation row with a private engine (the same
    per-call engine pattern the conftest principal factory uses), decrypting
    private fields through the canonical service helpers.

    booking_confirmations is RLS-protected, so the tenant context is bound
    explicitly (mirrors spine_api.core.rls.rls_session).
    """
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from spine_api.core.database import DATABASE_URL
    from spine_api.models.tenant import BookingConfirmation
    from spine_api.services.private_fields import decrypt_field

    async def _run() -> dict:
        engine = create_async_engine(DATABASE_URL)
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                await session.execute(
                    text("SELECT set_config('app.current_agency_id', :agency, false)"),
                    {"agency": AGENCY},
                )
                row = (
                    await session.execute(
                        select(BookingConfirmation).where(
                            BookingConfirmation.id == confirmation_id
                        )
                    )
                ).scalar_one()
                return {
                    "agency_id": row.agency_id,
                    "trip_id": row.trip_id,
                    "type": row.confirmation_type,
                    "status": row.confirmation_status,
                    "recorded_by": row.recorded_by,
                    "created_by": row.created_by,
                    "supplier_name": decrypt_field(row.supplier_name_encrypted),
                    "confirmation_number": decrypt_field(
                        row.confirmation_number_encrypted
                    ),
                    "notes": decrypt_field(row.notes_encrypted),
                }
        finally:
            await engine.dispose()

    return _run_coro(_run())


def _count_active_insurance_confirmations(trip_id: str) -> int:
    from sqlalchemy import func, select, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from spine_api.core.database import DATABASE_URL
    from spine_api.models.tenant import BookingConfirmation

    async def _run() -> int:
        engine = create_async_engine(DATABASE_URL)
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                await session.execute(
                    text("SELECT set_config('app.current_agency_id', :agency, false)"),
                    {"agency": AGENCY},
                )
                total = (
                    await session.execute(
                        select(func.count())
                        .select_from(BookingConfirmation)
                        .where(
                            BookingConfirmation.agency_id == AGENCY,
                            BookingConfirmation.trip_id == trip_id,
                            BookingConfirmation.confirmation_type == "insurance",
                            BookingConfirmation.confirmation_status != "voided",
                        )
                    )
                ).scalar_one()
                return int(total)
        finally:
            await engine.dispose()

    return _run_coro(_run())


def _quote(session_client, *, trip_id: str | None = None, **extra):
    body = {"total_trip_cost_usd": 5000.0, **extra}
    if trip_id is not None:
        body["trip_id"] = trip_id
    return session_client.post(
        "/api/v1/insurance/quote",
        json=body,
        headers=_headers(),
    )


def test_quote_without_trip_keeps_illustrative_prices_but_does_not_claim_policy_facts(
    session_client,
):
    response = _quote(session_client)

    assert response.status_code == 200
    data = response.json()
    assert len(data["plans"]) == 3
    assert data["reality_tier"] == "deterministic_preview"
    assert data["cfar_deadline"] is None
    assert data["days_remaining_for_cfar"] is None
    assert data["cfar_deadline_anchor"] == "not_evaluated"
    assert data["cfar_timing_status"] == "not_evaluated"
    assert data["cfar_evidence"]["policy_rule_status"] == "not_adopted"
    assert data["cfar_evidence"]["unresolved_predicates"] == [
        "provider_rule",
        "plan_version",
        "coverage_facts",
    ]
    for plan in data["plans"]:
        assert plan["pre_existing_waiver_eligible"] is None
        assert plan["pre_existing_waiver_status"] == "not_evaluated"
        assert plan["eligibility_evidence"]["policy_rule_status"] == "not_adopted"


def test_quote_with_trip_id_requires_an_existing_trip_in_the_current_tenant(session_client):
    missing = _quote(session_client, trip_id="trip_insurance_missing")

    assert missing.status_code == 404
    assert missing.json()["detail"] == "Trip not found"


def test_quote_with_existing_same_tenant_trip_succeeds_without_mutating_trip(session_client):
    trip_id = _make_trip()
    before = TripStore.get_trip_for_agency(trip_id, AGENCY)

    response = _quote(session_client, trip_id=trip_id)

    assert response.status_code == 200
    assert TripStore.get_trip_for_agency(trip_id, AGENCY) == before


def test_quote_with_cross_tenant_trip_id_fails_closed(session_client):
    foreign_trip = _make_trip(agency_id="insurance_quote_other_agency")

    response = _quote(session_client, trip_id=foreign_trip)

    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def test_missing_and_explicit_null_deposit_are_distinct_from_blank_input(session_client):
    omitted = _quote(session_client)
    explicit_null = _quote(session_client, deposit_date=None)

    for response in (omitted, explicit_null):
        assert response.status_code == 200
        evidence = response.json()["cfar_evidence"]
        assert evidence["source"] is None
        assert evidence["verification"] == "not_available"
        assert evidence["deposit_date_utc"] is None

    blank = _quote(session_client, deposit_date="")
    assert blank.status_code == 422


@pytest.mark.parametrize(
    "deposit_date",
    [
        "not-a-date",
        0,
        "0001-01-01T00:00:00+14:00",
        "9999-12-31T23:59:59-14:00",
    ],
    ids=["malformed", "numeric-timestamp", "utc-normalization-underflow", "utc-normalization-overflow"],
)
def test_invalid_or_unsupported_deposit_evidence_is_a_validation_error(
    session_client, deposit_date
):
    response = _quote(session_client, deposit_date=deposit_date)

    assert response.status_code == 422
    assert any(
        "deposit_date" in str(error.get("loc", []))
        for error in response.json()["detail"]
    )


def test_future_deposit_evidence_is_a_validation_error(session_client):
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    response = _quote(session_client, deposit_date=future)

    assert response.status_code == 422
    assert any(
        "future" in str(error).lower() or "deposit_date" in str(error)
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize("total_trip_cost_usd", [0, -1, True, False, "nan", "inf"])
def test_quote_rejects_non_positive_or_non_finite_trip_cost(session_client, total_trip_cost_usd):
    response = _quote(session_client, total_trip_cost_usd=total_trip_cost_usd)

    assert response.status_code == 422


def test_quote_request_does_not_fabricate_default_traveler_ages():
    from spine_api.routers.insurance import InsuranceQuoteRequest

    assert InsuranceQuoteRequest(total_trip_cost_usd=5000).traveler_ages is None


def test_attach_policy_does_not_fabricate_default_insurer(session_client):
    """FND-0182: no internal record may be attributed to a specific insurer.

    The attach-policy request must never default to a vendor name (the
    historical default was "Allianz Global Assistance"), and the endpoint must
    reject a policy attachment that does not name its insurer.
    """
    from spine_api.routers import insurance as insurance_router

    fields = insurance_router.AttachPolicyRequest.model_fields
    provider_field = fields["insurance_provider"]
    assert provider_field.is_required(), (
        "insurance_provider must be explicitly provided; a default fabricates "
        "carrier attribution for an internally recorded policy"
    )
    assert "Allianz" not in str(provider_field.default)
    assert "Allianz" not in str(insurance_router.AttachPolicyResponse.model_fields)

    missing_provider = session_client.post(
        f"/api/v1/insurance/{_make_trip()}/attach-policy",
        json={
            "trip_id": _make_trip(),
            "selected_plan_id": "ins_cfar_03",
            "policy_number": "POL-NO-PROVIDER",
            "premium_paid_usd": 100.0,
        },
        headers=_headers(),
    )
    assert missing_provider.status_code == 422
    assert any(
        "insurance_provider" in str(error.get("loc", []))
        for error in missing_provider.json()["detail"]
    )


def test_attach_policy_records_explicit_provider_with_honest_provenance(session_client):
    """FND-0182: an attached policy labels its provider assertion honestly.

    Even with an explicitly named insurer, the record must never claim
    carrier-verified coverage: provenance stays agent_recorded /
    deterministic_preview with carrier_confirmed=False.
    """
    trip_id = _make_trip()

    response = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy",
        json={
            "trip_id": trip_id,
            "selected_plan_id": "ins_cfar_03",
            "policy_number": "POL-EXPLICIT-1",
            "insurance_provider": "  Acme Insurance Co  ",
            "premium_paid_usd": 500.0,
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider_source"] == "agent_recorded"
    assert data["carrier_confirmed"] is False
    assert data["provider_connected"] is False
    assert data["reality_tier"] == "deterministic_preview"

    stored = TripStore.get_trip_for_agency(trip_id, AGENCY)["insurance_policy"]
    assert stored["provider"] == "Acme Insurance Co"
    assert stored["provider_source"] == "agent_recorded"
    assert stored["carrier_confirmed"] is False

    blank_provider = session_client.post(
        f"/api/v1/insurance/{_make_trip()}/attach-policy",
        json={
            "trip_id": _make_trip(),
            "selected_plan_id": "ins_std_01",
            "policy_number": "POL-BLANK-PROVIDER",
            "insurance_provider": "   ",
            "premium_paid_usd": 100.0,
        },
        headers=_headers(),
    )
    assert blank_provider.status_code == 422


def test_equivalent_deposit_instants_have_identical_utc_provenance(session_client):
    first = _quote(session_client, deposit_date="2026-09-04T23:30:00-02:00")
    second = _quote(session_client, deposit_date="2026-09-05T01:30:00Z")

    assert first.status_code == second.status_code == 200
    first_evidence = first.json()["cfar_evidence"]
    second_evidence = second.json()["cfar_evidence"]
    assert first_evidence["deposit_date_utc"] == "2026-09-05T01:30:00+00:00"
    assert second_evidence["deposit_date_utc"] == "2026-09-05T01:30:00+00:00"
    assert first_evidence["source"] == second_evidence["source"] == "request.deposit_date"
    assert first_evidence["verification"] == second_evidence["verification"] == "unverified"


# ---------------------------------------------------------------------------
# F-31 / FND-0118: canonical BookingConfirmation transaction/replay migration
#
# The attach handler is an adapter to the canonical insurance evidence
# lifecycle: transactional save, replay idempotency, principal actor, and
# audit written strictly after the durable commit.
# ---------------------------------------------------------------------------


def test_attach_policy_records_canonical_insurance_confirmation(session_client):
    """FND-0118: the durable authority is the canonical SQL row, not the blob."""
    trip_id = _make_trip()

    response = _attach(session_client, trip_id)

    assert response.status_code == 200
    data = response.json()
    confirmation_id = data["confirmation_id"]
    assert confirmation_id
    assert data["actor_id"]
    assert data["replayed"] is False
    assert data["audit_recorded"] is True

    row = _read_confirmation(confirmation_id)
    assert row["type"] == "insurance"
    assert row["status"] == "recorded"
    assert row["agency_id"] == AGENCY
    assert row["trip_id"] == trip_id
    # Actor semantics: recorded/created by the authenticated principal, with
    # agency as a separate tenant dimension.
    assert row["recorded_by"] == data["actor_id"]
    assert row["created_by"] == data["actor_id"]
    assert row["agency_id"] != data["actor_id"]
    # Explicit-provider contract preserved through the canonical record:
    # encrypted private fields carry the insurer and policy number, and the
    # encrypted notes carry the agent_recorded provenance markers.
    assert row["supplier_name"] == "Acme Insurance Co"
    assert row["confirmation_number"] == data["policy_number"]
    assert "provider_source=agent_recorded" in row["notes"]
    assert "carrier_confirmed=false" in row["notes"]

    # Legacy trip blob projection preserved, now referencing the canonical row.
    blob = TripStore.get_trip_for_agency(trip_id, AGENCY)["insurance_policy"]
    assert blob["provider"] == "Acme Insurance Co"
    assert blob["provider_source"] == "agent_recorded"
    assert blob["confirmation_id"] == confirmation_id


def test_attach_policy_replay_with_same_key_attaches_once(session_client):
    """FND-0118: same confirmation key → same outcome, no double-attach."""
    trip_id = _make_trip()
    body = _attach_body(trip_id)  # built once: identical payload → identical key

    first = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy", json=body, headers=_headers()
    )
    assert first.status_code == 200

    second = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy", json=body, headers=_headers()
    )

    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert second.json()["confirmation_id"] == first.json()["confirmation_id"]
    assert _count_active_insurance_confirmations(trip_id) == 1


def test_attach_policy_conflicting_second_policy_is_rejected_not_double_attached(
    session_client,
):
    """FND-0118: immutable-create contract — one active policy per trip.

    A different payload is a deliberate 409 carrying the existing
    confirmation id; it never silently double-attaches or resurrects the
    superseded record.
    """
    trip_id = _make_trip()

    first = _attach(session_client, trip_id)
    assert first.status_code == 200

    conflict = _attach(
        session_client,
        trip_id,
        policy_number=f"POL-OTHER-{uuid.uuid4().hex[:6].upper()}",
        premium_paid_usd=750.0,
    )

    assert conflict.status_code == 409
    detail = conflict.json()["detail"]
    assert detail["existing_confirmation_id"] == first.json()["confirmation_id"]
    assert _count_active_insurance_confirmations(trip_id) == 1
    # The legacy projection still shows the winning policy.
    blob = TripStore.get_trip_for_agency(trip_id, AGENCY)["insurance_policy"]
    assert blob["policy_number"] == first.json()["policy_number"]


def test_attach_policy_audit_attributes_the_authenticated_principal(
    session_client, capture_audit_events
):
    """FND-0118: actor is the principal; agency is a separate dimension;
    the policy number never reaches general audit logs."""
    trip_id = _make_trip()

    response = _attach(session_client, trip_id)
    assert response.status_code == 200
    actor_id = response.json()["actor_id"]

    # Other subsystems (e.g. the beta-mode privacy guard) may audit during the
    # same request; the contract under test is exactly one attach event.
    attach_events = [
        event
        for event in capture_audit_events
        if event["event_type"] == "insurance_policy_attached"
    ]
    assert len(attach_events) == 1
    event = attach_events[0]
    assert event["user_id"] == actor_id  # authenticated principal, not "agency"
    assert event["details"]["agency_id"] == AGENCY  # tenant dimension
    assert event["details"]["confirmation_id"] == response.json()["confirmation_id"]
    # Privacy: the policy number is referenced through the canonical row,
    # never copied into general logs.
    assert "policy_number" not in event["details"]
    import json as _json

    assert response.json()["policy_number"] not in _json.dumps(event["details"])


def test_attach_policy_audit_failure_surfaces_but_save_persists(
    session_client, monkeypatch
):
    """FND-0118: audit runs strictly after the durable commit; its failure
    must not roll back the save and must be surfaced on the response."""
    from spine_api.persistence import AuditStore

    def _audit_raises(*args, **kwargs):
        raise RuntimeError("audit sink down")

    monkeypatch.setattr(AuditStore, "log_event", _audit_raises)

    trip_id = _make_trip()
    response = _attach(session_client, trip_id)

    assert response.status_code == 200
    assert response.json()["audit_recorded"] is False
    # The durable evidence survives the audit failure.
    row = _read_confirmation(response.json()["confirmation_id"])
    assert row["status"] == "recorded"


def test_viewer_role_cannot_attach_policy(session_client, boundary_principal_factory):
    """FND-0118: action permission — membership alone grants nothing.

    A viewer principal is denied before any mutation; no confirmation row and
    no audit event is produced.
    """
    from spine_api.core.security import create_access_token

    viewer_user = "usr_insurance_viewer"
    boundary_principal_factory(viewer_user, AGENCY, role="viewer")
    token = create_access_token(
        user_id=viewer_user,
        agency_id=AGENCY,
        role="viewer",
        expires_delta=timedelta(hours=1),
    )
    trip_id = _make_trip()
    before = TripStore.get_trip_for_agency(trip_id, AGENCY)

    response = session_client.post(
        f"/api/v1/insurance/{trip_id}/attach-policy",
        json=_attach_body(trip_id),
        headers={"X-Agency-ID": AGENCY, "Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    # No policy mutation on rejection: the trip record is byte-identical.
    assert TripStore.get_trip_for_agency(trip_id, AGENCY) == before
    assert _count_active_insurance_confirmations(trip_id) == 0


def test_attach_policy_rejects_non_finite_or_negative_premium(session_client):
    """FND-0118: money recorded as evidence must be a real non-negative amount."""
    trip_id = _make_trip()

    for premium in (-1.0, True, "nan"):
        response = _attach(session_client, trip_id, premium_paid_usd=premium)
        assert response.status_code == 422
        assert any(
            "premium_paid_usd" in str(error.get("loc", []))
            for error in response.json()["detail"]
        )
    assert _count_active_insurance_confirmations(trip_id) == 0
