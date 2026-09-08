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
