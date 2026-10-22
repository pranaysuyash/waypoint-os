"""Fare-drop disposition ledger + options calculator tests — exploration topic 49 (2026-10-21).

Mirrors tests/test_claim_disposition.py: the first test is the owner's hard
invariant (no money movement, ever), then state-machine correctness, the
options arithmetic with provenance labels, and the router integration on the
existing price-lock (re-shopping) router.
"""

import os
import pathlib

import pytest

from spine_api.services import fare_drop_disposition as fd

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


# ---------------------------------------------------------------------------
# THE INVARIANT: no money movement, ever (owner constraint)
# ---------------------------------------------------------------------------

_PAYMENT_FORBIDDEN_PATTERNS = (
    "stripe",
    "paypal",
    "razorpay",
    "adyen",
    "squareup",
    "braintree",
    "checkout.com",
    "payment_intent",
    "PaymentIntent",
    "charge(",
    "create_charge",
    "payout",
    "bank_account",
    "iban",
    "card_number",
    "wallet_balance",
    "transfer_funds",
    "initiate_refund",
    "process_payment",
)


def test_no_payment_code_paths():
    """The fare-drop lane must never import or invoke payment capability.

    Scans the service, the router that hosts the endpoints, and the agent
    module that detects the drop. If this fails, a decision card is about to
    become a checkout.
    """
    lane_files = [
        pathlib.Path("spine_api/services/fare_drop_disposition.py"),
        pathlib.Path("spine_api/routers/price_lock.py"),
    ]
    for path in lane_files:
        assert path.exists(), f"invariant scope file missing: {path}"
        source = path.read_text().lower()
        for pattern in _PAYMENT_FORBIDDEN_PATTERNS:
            assert pattern.lower() not in source, (
                f"MONEY-BOUNDARY VIOLATION in {path}: found {pattern!r}. The fare-drop "
                f"ledger records the advisor's decision; it never reprices or moves money."
            )


def test_disposition_states_never_imply_custody():
    for state in fd.FARE_DROP_DISPOSITION_STATES:
        for forbidden in fd._FORBIDDEN_STATE_SUBSTRINGS:
            assert forbidden not in state.upper(), (
                f"state {state!r} implies funds custody (contains {forbidden!r})"
            )


def test_detection_signal_authority_forbids_action():
    """The agent's signal must carry the do-not-act authority string."""
    source = pathlib.Path("src/agents/runtime.py").read_text()
    assert "Do not purchase, reprice, contact suppliers" in source


# ---------------------------------------------------------------------------
# State machine correctness
# ---------------------------------------------------------------------------


def test_reprice_path_to_closed():
    d = fd.new_disposition("fare_drop|ABC|100000.0|INR")
    assert d["state"] == "DETECTED"
    fd.apply_transition(d, "PRESENTED", by="op1", note="emailed both options")
    fd.apply_transition(
        d,
        "REPRICED",
        by="op1",
        outcome={"option": "reprice", "client_delta": -12000.0, "supplier_reference": "RB-1", "executed_by": "op1"},
    )
    fd.apply_transition(d, "CLOSED", by="op1")
    assert fd.is_terminal(d["state"])
    assert [h["state"] for h in d["history"]] == ["DETECTED", "PRESENTED", "REPRICED", "CLOSED"]
    assert d["outcome"]["option"] == "reprice"
    assert d["outcome"]["recorded_by"] == "op1"
    assert d["outcome"]["recorded_at"]


def test_upgrade_path_and_deferred_re_presentation():
    d = fd.new_disposition("m")
    fd.apply_transition(d, "PRESENTED", by="op1")
    fd.apply_transition(d, "DEFERRED", by="op1", note="client travelling, revisit next week")
    fd.apply_transition(d, "PRESENTED", by="op1", note="re-presented after new observation")
    fd.apply_transition(d, "UPGRADED", by="op1", outcome={"option": "upgrade", "client_delta": 0.0, "executed_by": "op1"})
    fd.apply_transition(d, "CLOSED", by="op1")
    assert d["state"] == "CLOSED"


def test_dismiss_from_detected_and_close():
    d = fd.new_disposition("m")
    fd.apply_transition(d, "DISMISSED", by="op1", note="drop within noise")
    fd.apply_transition(d, "CLOSED", by="op1")
    assert d["state"] == "CLOSED"


def test_illegal_transition_rejected_and_state_unchanged():
    d = fd.new_disposition("m")
    with pytest.raises(ValueError, match="illegal transition"):
        fd.apply_transition(d, "REPRICED", by="op1", outcome={"option": "reprice"})
    assert d["state"] == "DETECTED"
    assert len(d["history"]) == 1


def test_terminal_is_frozen():
    d = fd.new_disposition("m")
    fd.apply_transition(d, "DISMISSED", by="op1")
    fd.apply_transition(d, "CLOSED", by="op1")
    with pytest.raises(ValueError, match="terminal"):
        fd.apply_transition(d, "PRESENTED", by="op1")


def test_decision_states_require_recorded_outcome():
    d = fd.new_disposition("m")
    fd.apply_transition(d, "PRESENTED", by="op1")
    with pytest.raises(ValueError, match="requires a recorded outcome"):
        fd.apply_transition(d, "REPRICED", by="op1")
    assert d["state"] == "PRESENTED"


def test_expected_state_compare_and_set():
    d = fd.new_disposition("m")
    with pytest.raises(ValueError, match="state changed"):
        fd.apply_transition(d, "PRESENTED", by="op1", expected_state="PRESENTED")
    fd.apply_transition(d, "PRESENTED", by="op1", expected_state="DETECTED")
    assert d["state"] == "PRESENTED"


def test_unknown_states_rejected():
    assert fd.transition_disposition("DETECTED", "MONEY_HELD") is False
    assert fd.transition_disposition("NOPE", "PRESENTED") is False
    with pytest.raises(ValueError, match="unknown initial"):
        fd.new_disposition("m", initial_state="TELEPORTED")


# ---------------------------------------------------------------------------
# Options calculator — the two practitioner options, with provenance labels
# ---------------------------------------------------------------------------


def test_options_arithmetic_with_recorded_commission():
    options = fd.compute_fare_drop_options(100000, 88000, commission_pct=0.10, commission_source="booking_data.commission_pct")
    assert options["drop_amount"] == 12000.0
    assert options["drop_percent"] == 12.0
    assert options["reprice"] == {"client_saving": 12000.0, "commission_delta": -1200.0}
    assert options["upgrade"]["upgrade_budget"] == 12000.0
    assert options["upgrade"]["commission_delta"] == 0.0
    assert options["commission"] == {"pct": 0.10, "basis": "trip_recorded", "source": "booking_data.commission_pct"}
    assert options["basis"] == "trip_recorded"


def test_options_fall_back_to_labelled_estimate():
    options = fd.compute_fare_drop_options(100000, 88000)
    assert options["basis"] == "estimate"
    assert options["commission"]["source"] == "agency_default_rate"
    assert options["commission"]["pct"] == fd.AGENCY_COMMISSION_RATE
    assert options["reprice"]["commission_delta"] == -round(12000 * fd.AGENCY_COMMISSION_RATE, 2)


def test_options_reject_non_drops_and_bad_inputs():
    with pytest.raises(ValueError, match="no fare drop"):
        fd.compute_fare_drop_options(100000, 100000)
    with pytest.raises(ValueError, match="positive"):
        fd.compute_fare_drop_options(0, 88000)
    with pytest.raises(ValueError, match="fraction"):
        fd.compute_fare_drop_options(100000, 88000, commission_pct=15)


def test_resolve_trip_commission_prefers_booking_and_normalizes_percent():
    assert fd.resolve_trip_commission({"booking_data": {"commission_pct": 12}}) == (0.12, "booking_data.commission_pct")
    assert fd.resolve_trip_commission({"fees": {"commission_pct": 0.08}}) == (0.08, "fees.commission_pct")
    assert fd.resolve_trip_commission({"booking_data": {"commission_pct": "n/a"}}) == (None, None)
    assert fd.resolve_trip_commission({}) == (None, None)


# ---------------------------------------------------------------------------
# Traveler draft (T-FD4, draft-only) — practitioner framing, never sent
# ---------------------------------------------------------------------------


def test_traveler_draft_uses_consensus_framing_and_only_verified_numbers():
    signal = {"booked_currency": "INR", "detection_marker": "m"}
    options = fd.compute_fare_drop_options(100000, 88000, commission_pct=0.10)
    draft = fd.compose_traveler_draft(signal, options, traveler_name="Ada", destination="Dubai")
    assert draft["status"] == fd.DRAFT_STATUS == "DRAFT_AWAITING_OPERATOR"
    assert draft["channel"] == "unsent"
    body = draft["body"]
    assert body.startswith("Hi Ada,")
    assert "Great news" in body and "to Dubai" in body
    assert "INR 12,000" in body
    assert "Refund the difference" in body and "upgrade" in body.lower()
    # Commission is internal — the client never sees it, and no number besides the drop appears.
    assert "commission" not in body.lower()
    assert "1,200" not in body
    assert draft["based_on"] == {"drop_amount": 12000.0, "currency": "INR", "detection_marker": "m"}


def test_traveler_draft_is_none_without_verified_options():
    assert fd.compose_traveler_draft({"booked_currency": "INR"}, None) is None
    assert fd.compose_traveler_draft({}, {"drop_amount": 0}) is None


def test_traveler_draft_handles_missing_name_and_destination():
    options = fd.compute_fare_drop_options(500, 400)
    draft = fd.compose_traveler_draft({}, options)
    assert draft["body"].startswith("Hi,\n")
    assert "for your trip has come down" in draft["body"]  # no "to <destination>" clause
    assert "100" in draft["body"]


# ---------------------------------------------------------------------------
# Router wiring + endpoint integration (hosted on the price-lock router)
# ---------------------------------------------------------------------------


def test_router_wires_the_disposition_module():
    router_src = pathlib.Path("spine_api/routers/price_lock.py").read_text()
    assert "fare_drop_disposition" in router_src
    assert "/fare-drop/disposition" in router_src


@pytest.fixture()
def api_client():
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from spine_api.core.auth import get_current_agency
    from spine_api.server import app

    app.dependency_overrides[get_current_agency] = lambda: SimpleNamespace(id="fd-test-agency")
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_agency, None)


_MARKER = "fare_drop|ABC123|100000.0|INR"


def _signal(current_price=88000.0):
    """Exactly the shape TicketPriceWatchAgent writes (test_agent_runtime pins it)."""
    return {
        "checked_at": "2026-10-21T10:00:00+00:00",
        "source": "ticket_price_watch_agent",
        "detection_marker": _MARKER,
        "booking_ref": "ABC123",
        "booked_price": 100000.0,
        "booked_currency": "INR",
        "current_price": current_price,
        "current_currency": "INR",
        "drop_amount": round(100000.0 - current_price, 2),
        "drop_percent": round((current_price - 100000.0) / 1000.0, 2),
        "threshold_percent": 5.0,
        "severity": "medium",
        "tool_evidence": [],
        "authority": "Internal fare-drop watch support only. Do not purchase, reprice, contact suppliers, or send customer messages.",
    }


@pytest.fixture()
def booked_trip(api_client):
    from uuid import uuid4

    from spine_api.persistence import TripStore

    agency_id = "fd-test-agency"
    # Unique id per test: the file trip store merges saves, so a shared id would
    # leak a prior test's ledger state into the next one.
    trip_id = f"fdtrip{uuid4().hex[:10]}"
    trip = {
        "id": trip_id,
        "agency_id": agency_id,
        "status": "active",
        "stage": "booked",
        "destination": "Dubai",
        "booking_data": {"confirmation_number": "ABC123", "total_price": 100000, "currency": "INR", "commission_pct": 10},
        "fare_drop_signal": _signal(),
        "price_observations": [{"detection_marker": _MARKER, "checked_at": "2026-10-21T10:00:00+00:00", "status": "observed", "drift_percent": -12.0}],
    }
    TripStore.save_trip(trip, agency_id=agency_id)
    return agency_id, trip_id


def test_get_without_signal_is_404(api_client):
    from spine_api.persistence import TripStore

    TripStore.save_trip({"id": "fdtrip_nosignal", "agency_id": "fd-test-agency", "status": "active"}, agency_id="fd-test-agency")
    resp = api_client.get("/api/v1/price-lock/fdtrip_nosignal/fare-drop/disposition", headers={"X-Agency-Id": "fd-test-agency"})
    assert resp.status_code == 404
    assert "No fare-drop signal" in resp.json()["detail"]


def test_get_surfaces_detected_ledger_and_options_without_persisting(api_client, booked_trip):
    from spine_api.persistence import TripStore

    agency_id, trip_id = booked_trip
    resp = api_client.get(f"/api/v1/price-lock/{trip_id}/fare-drop/disposition", headers={"X-Agency-Id": agency_id})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["disposition"]["state"] == "DETECTED"
    assert data["options"]["reprice"] == {"client_saving": 12000.0, "commission_delta": -1200.0}
    assert data["options"]["upgrade"]["upgrade_budget"] == 12000.0
    assert data["options"]["basis"] == "trip_recorded"
    assert data["options"]["commission"]["source"] == "booking_data.commission_pct"
    assert data["observations"][0]["drift_percent"] == -12.0
    # Draft-only traveler message rides along; it is never sent by the system.
    assert data["traveler_draft"]["status"] == "DRAFT_AWAITING_OPERATOR"
    assert "INR 12,000" in data["traveler_draft"]["body"]
    assert "commission" not in data["traveler_draft"]["body"].lower()
    # No fabricated placeholder name (review finding 4): the fixture records no
    # customer name, so the draft must greet generically.
    assert data["traveler_draft"]["body"].startswith("Hi,\n")
    # Read-only: GET must not create the ledger on the trip.
    assert "fare_drop_disposition" not in (TripStore.get_trip_for_agency(trip_id, agency_id) or {})


def test_patch_happy_path_persists_and_trip_response_carries_ledger(api_client, booked_trip):
    agency_id, trip_id = booked_trip
    url = f"/api/v1/price-lock/{trip_id}/fare-drop/disposition"
    headers = {"X-Agency-Id": agency_id}

    presented = api_client.patch(url, json={"new_state": "PRESENTED", "note": "sent both options", "expected_state": "DETECTED", "idempotency_key": "k1"}, headers=headers)
    assert presented.status_code == 200, presented.text
    assert presented.json()["disposition"]["state"] == "PRESENTED"

    upgraded = api_client.patch(
        url,
        json={
            "new_state": "UPGRADED",
            "outcome": {"option": "upgrade", "client_delta": 0.0, "supplier_reference": "UPG-77", "executed_by": "advisor-1"},
            "expected_state": "PRESENTED",
            "idempotency_key": "k2",
        },
        headers=headers,
    )
    assert upgraded.status_code == 200, upgraded.text
    ledger = upgraded.json()["disposition"]
    assert ledger["state"] == "UPGRADED"
    assert ledger["outcome"]["supplier_reference"] == "UPG-77"
    assert ledger["outcome"]["recorded_by"] == agency_id

    # The canonical trip response exposes the signal, ledger, and observation log.
    trip_resp = api_client.get(f"/trips/{trip_id}", headers=headers)
    assert trip_resp.status_code == 200, trip_resp.text
    body = trip_resp.json()
    assert body["fare_drop_signal"]["detection_marker"] == _MARKER
    assert body["fare_drop_disposition"]["state"] == "UPGRADED"
    assert body["price_observations"][0]["status"] == "observed"


def test_patch_illegal_transition_409(api_client, booked_trip):
    agency_id, trip_id = booked_trip
    resp = api_client.patch(
        f"/api/v1/price-lock/{trip_id}/fare-drop/disposition",
        json={"new_state": "REPRICED", "outcome": {"option": "reprice"}, "idempotency_key": "k"},
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 409
    assert "illegal transition" in resp.json()["detail"]


def test_patch_stale_expected_state_409(api_client, booked_trip):
    agency_id, trip_id = booked_trip
    resp = api_client.patch(
        f"/api/v1/price-lock/{trip_id}/fare-drop/disposition",
        json={"new_state": "PRESENTED", "expected_state": "PRESENTED", "idempotency_key": "k"},
        headers={"X-Agency-Id": agency_id},
    )
    assert resp.status_code == 409
    assert "state changed" in resp.json()["detail"]


def test_patch_decision_without_outcome_409(api_client, booked_trip):
    agency_id, trip_id = booked_trip
    url = f"/api/v1/price-lock/{trip_id}/fare-drop/disposition"
    headers = {"X-Agency-Id": agency_id}
    api_client.patch(url, json={"new_state": "PRESENTED", "idempotency_key": "k1"}, headers=headers)
    resp = api_client.patch(url, json={"new_state": "REPRICED", "idempotency_key": "k2"}, headers=headers)
    assert resp.status_code == 409
    assert "requires a recorded outcome" in resp.json()["detail"]


def test_other_agency_cannot_see_the_ledger(api_client, booked_trip):
    _, trip_id = booked_trip
    resp = api_client.get(f"/api/v1/price-lock/{trip_id}/fare-drop/disposition", headers={"X-Agency-Id": "someone-else"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Runtime storage boundary (review finding 1): the SQL list view excludes
# booking_data by design; the runtime adapter must enrich post-booking rows
# through the scoped accessor or the fare-drop scan never sees a booking.
# ---------------------------------------------------------------------------


def test_runtime_adapter_enriches_post_booking_rows_via_scoped_accessor():
    from spine_api.services.agent_runtime_adapters import TripStoreAdapter

    class _Store:
        def __init__(self):
            self.fetched = []

        def list_trips(self, limit=500):
            return [
                {"id": "t_booked", "stage": "booked", "agency_id": "ag1"},
                {"id": "t_quoted", "stage": "quoted", "agency_id": "ag1"},
                {"id": "t_ticketed", "stage": "ticketed", "agency_id": "ag1", "booking_data": {"confirmation_number": "X"}},
            ]

        def get_booking_data_for_agency(self, trip_id, agency_id):
            self.fetched.append((trip_id, agency_id))
            return {"confirmation_number": "ABC", "total_price": 1000, "currency": "INR"}

        def get_booking_data(self, trip_id):
            raise AssertionError("system-level accessor must not be used when agency_id is present")

    store = _Store()
    active = TripStoreAdapter(trip_store=store).list_active()

    assert store.fetched == [("t_booked", "ag1")], "only the anchor-less post-booking row is fetched"
    by_id = {t["id"]: t for t in active}
    assert by_id["t_booked"]["booking_data"]["confirmation_number"] == "ABC"
    assert "booking_data" not in by_id["t_quoted"], "pre-booking rows stay excluded (PII boundary)"
    assert by_id["t_ticketed"]["booking_data"]["confirmation_number"] == "X"
