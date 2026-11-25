"""
Backend tests for GET /payments read-model API.

Run:
  uv run pytest tests/test_payments_queue_api.py -q
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

import server
from spine_api.persistence import TripStore


@pytest.fixture()
def trip_factory(session_agency_id):
    created_trips: list[tuple[str, str]] = []

    def _create_trip(source: str = "payments_queue_api_test", *, agency_id: str = session_agency_id) -> str:
        trip_id = TripStore.save_trip(
            {
                "source": source,
                "agency_id": agency_id,
                "status": "assigned",
                "stage": "proposal",
                "extracted": {},
                "validation": {},
                "decision": {},
                "raw_input": {},
            },
            agency_id=agency_id,
        )
        created_trips.append((trip_id, agency_id))
        return trip_id

    yield _create_trip

    for trip_id, agency_id in created_trips:
        try:
            TripStore.delete_trip_for_agency(trip_id, agency_id)
        except Exception:
            pass


def _set_booking_data(trip_id: str, agency_id: str, booking_data: dict | None) -> None:
    updates = {"booking_data": booking_data}
    updated = TripStore.update_trip_for_agency(trip_id, agency_id, updates)
    assert updated is not None


def _payment_tracking(*, payment_status: str, refund_status: str = "not_applicable", agreed: float | None = None, paid: float | None = None, final_due: date | None = None, notes: str | None = None) -> dict:
    payload = {
        "payment_status": payment_status,
        "refund_status": refund_status,
    }
    if agreed is not None:
        payload["agreed_amount"] = agreed
    if paid is not None:
        payload["amount_paid"] = paid
    if final_due is not None:
        payload["final_payment_due"] = final_due.isoformat()
    if notes is not None:
        payload["notes"] = notes
    return payload


class TestPaymentsQueueApi:
    def test_full_tenant_scope_not_limited_to_initial_5000(self, session_client, monkeypatch, session_agency_id):
        total_trips = 5002

        call_offsets: list[int] = []
        booking_lookup_called = False

        def fake_list_trip_payment_records_for_agency(*, agency_id: str, limit: int = 100, offset: int = 0):
            assert agency_id == session_agency_id
            call_offsets.append(offset)
            if offset >= total_trips:
                return []
            end = min(offset + limit, total_trips)
            return [
                {
                    "id": f"trip_{idx}",
                    "status": "assigned",
                    "start_date": None,
                    "updated_at": None,
                    "booking_data": {
                        "payment_tracking": {
                            "payment_status": "partially_paid" if idx >= 5000 else "paid",
                            "refund_status": "not_applicable",
                            "agreed_amount": 1000,
                            "amount_paid": 200 if idx >= 5000 else 1000,
                            "final_payment_due": (date.today() + timedelta(days=2)).isoformat() if idx >= 5000 else None,
                        }
                    },
                }
                for idx in range(offset, end)
            ]

        def fake_get_booking_data_for_agency(*args, **kwargs):
            nonlocal booking_lookup_called
            booking_lookup_called = True
            raise AssertionError("payments queue should not do per-trip booking lookups anymore")

        monkeypatch.setattr(server.TripStore, "list_trip_payment_records_for_agency", fake_list_trip_payment_records_for_agency)
        monkeypatch.setattr(server.TripStore, "get_booking_data_for_agency", fake_get_booking_data_for_agency)

        resp = session_client.get("/payments?queue_status=due_soon&limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()

        assert body["pagination"]["total"] == 2
        assert body["summary"]["total"] == 2
        assert body["summary"]["by_queue_status"]["due_soon"] == 2
        assert body["pagination"]["returned"] == 2
        assert [item["trip_id"] for item in body["items"]] == ["trip_5000", "trip_5001"]
        assert body["items"][0]["trip_name"].startswith("Trip details incomplete")
        assert body["items"][1]["trip_name"].startswith("Trip details incomplete")

        # Ensure backend iterated beyond the initial 5000 records without N+1 booking fetches.
        assert any(offset >= 5000 for offset in call_offsets)
        assert booking_lookup_called is False

    def test_tenant_isolation(
        self, session_client, session_agency_id, trip_factory, auth_enforced,
        boundary_principal_factory, boundary_token_factory,
    ):
        trip_id = trip_factory("payments_queue_tenant")
        _set_booking_data(
            trip_id,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=100,
                    final_due=date.today() + timedelta(days=3),
                )
            },
        )

        other_agency_id = "agency_payments_boundary"
        other_user_id = "usr_payments_boundary"
        assert other_agency_id != session_agency_id
        boundary_principal_factory(other_user_id, other_agency_id)
        other_trip_id = trip_factory("payments_queue_other_tenant", agency_id=other_agency_id)

        baseline = session_client.get("/payments")
        assert baseline.status_code == 200
        baseline_ids = {item["trip_id"] for item in baseline.json()["items"]}
        assert trip_id in baseline_ids
        assert other_trip_id not in baseline_ids

        token = boundary_token_factory(other_user_id, other_agency_id)
        isolated = session_client.get("/payments", headers={"Authorization": f"Bearer {token}"})
        assert isolated.status_code == 200
        isolated_ids = {item["trip_id"] for item in isolated.json()["items"]}
        assert other_trip_id in isolated_ids
        assert trip_id not in isolated_ids

    def test_queue_derivation_missing_partial_overdue_paid_refund(self, session_client, session_agency_id, trip_factory):
        trip_missing = trip_factory("payments_queue_missing")
        trip_partial = trip_factory("payments_queue_partial")
        trip_overdue = trip_factory("payments_queue_overdue")
        trip_paid = trip_factory("payments_queue_paid")
        trip_refund = trip_factory("payments_queue_refund")

        _set_booking_data(trip_missing, session_agency_id, None)
        _set_booking_data(
            trip_partial,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(payment_status="unknown", notes="internal note should not leak"),
            },
        )
        _set_booking_data(
            trip_overdue,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=200,
                    final_due=date.today() - timedelta(days=1),
                )
            },
        )
        _set_booking_data(
            trip_paid,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="paid",
                    agreed=1000,
                    paid=1000,
                )
            },
        )
        _set_booking_data(
            trip_refund,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    refund_status="processing",
                    agreed=1000,
                    paid=400,
                )
            },
        )

        resp = session_client.get("/payments?limit=200")
        assert resp.status_code == 200
        body = resp.json()
        by_id = {item["trip_id"]: item for item in body["items"]}

        assert by_id[trip_missing]["queue_status"] == "not_configured"
        assert by_id[trip_partial]["queue_status"] == "unknown"
        assert by_id[trip_overdue]["queue_status"] == "overdue"
        assert by_id[trip_paid]["queue_status"] == "paid_complete"
        assert by_id[trip_refund]["queue_status"] == "refund_in_progress"

        for trip_id in [trip_missing, trip_partial, trip_overdue, trip_paid, trip_refund]:
            assert "notes" not in by_id[trip_id]

    @pytest.mark.parametrize(
        "path",
        [
            "/payments?queue_status=bad_value",
            "/payments?payment_status=bad_value",
            "/payments?refund_status=bad_value",
            "/payments?due_bucket=bad_value",
            "/payments?limit=0",
            "/payments?offset=-1",
        ],
    )
    def test_invalid_filters_and_pagination_validation(self, session_client, path):
        resp = session_client.get(path)
        assert resp.status_code == 422

    def test_pagination_after_filtering_and_filtered_summary(self, session_client, session_agency_id, trip_factory):
        trip_due_old = trip_factory("payments_queue_due_old")
        trip_overdue = trip_factory("payments_queue_between")
        trip_due_new = trip_factory("payments_queue_due_new")

        _set_booking_data(
            trip_due_old,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=100,
                    final_due=date.today() + timedelta(days=2),
                )
            },
        )
        _set_booking_data(
            trip_overdue,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=100,
                    final_due=date.today() - timedelta(days=2),
                )
            },
        )
        _set_booking_data(
            trip_due_new,
            session_agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=100,
                    final_due=date.today() + timedelta(days=3),
                )
            },
        )

        query = "queue_status=due_soon&payment_status=partially_paid&refund_status=not_applicable"
        all_filtered = session_client.get(f"/payments?{query}&limit=200&offset=0")
        assert all_filtered.status_code == 200
        all_body = all_filtered.json()

        filtered_ids = [item["trip_id"] for item in all_body["items"]]
        assert trip_due_old in filtered_ids
        assert trip_due_new in filtered_ids
        assert trip_overdue not in filtered_ids
        assert all_body["pagination"]["total"] >= 2

        paged = session_client.get(f"/payments?{query}&limit=1&offset=1")
        assert paged.status_code == 200
        page_body = paged.json()

        assert page_body["pagination"]["returned"] == 1
        assert page_body["pagination"]["limit"] == 1
        assert page_body["pagination"]["offset"] == 1
        assert page_body["pagination"]["total"] >= 2
        assert len(page_body["items"]) == 1

        assert page_body["summary"]["total"] == page_body["pagination"]["total"]
        assert page_body["summary"]["by_queue_status"]["due_soon"] >= 2
        assert page_body["summary"]["by_queue_status"]["overdue"] == 0

    def test_urgent_sort_configured_only_and_search(self, session_client, session_agency_id, trip_factory):
        """GET /payments?sort=urgent&configured_only=true&q=... ranks overdue first and filters cleanly."""
        trip_unconfigured = trip_factory("payments_urgent_unconf")
        trip_overdue = trip_factory("payments_urgent_overdue")
        trip_due_later = trip_factory("payments_urgent_later")

        TripStore.update_trip_for_agency(
            trip_unconfigured,
            session_agency_id,
            {"extracted": {"destination_raw": "Lisbon"}},
        )
        TripStore.update_trip_for_agency(
            trip_due_later,
            session_agency_id,
            {
                "extracted": {"destination_raw": "Kyoto"},
                "booking_data": {
                    "payment_tracking": _payment_tracking(
                        payment_status="partially_paid",
                        agreed=2000,
                        paid=500,
                        final_due=date.today() + timedelta(days=30),
                    )
                },
            },
        )
        TripStore.update_trip_for_agency(
            trip_overdue,
            session_agency_id,
            {
                "extracted": {"destination_raw": "Amalfi"},
                "booking_data": {
                    "payment_tracking": _payment_tracking(
                        payment_status="partially_paid",
                        agreed=4500,
                        paid=1500,
                        final_due=date.today() - timedelta(days=3),
                    )
                },
            },
        )

        urgent_resp = session_client.get("/payments?sort=urgent&configured_only=true&limit=25")
        assert urgent_resp.status_code == 200
        urgent_body = urgent_resp.json()
        urgent_ids = [item["trip_id"] for item in urgent_body["items"]]
        assert trip_unconfigured not in urgent_ids
        assert trip_overdue in urgent_ids
        assert trip_due_later in urgent_ids
        assert urgent_ids.index(trip_overdue) < urgent_ids.index(trip_due_later)

        search_resp = session_client.get("/payments?sort=urgent&q=amalfi")
        assert search_resp.status_code == 200
        search_body = search_resp.json()
        assert search_body["pagination"]["total"] == 1
        assert search_body["items"][0]["trip_id"] == trip_overdue
        assert search_body["items"][0]["destination"] == "Amalfi"
        assert search_body["items"][0]["trip_name"] == "Amalfi trip"
