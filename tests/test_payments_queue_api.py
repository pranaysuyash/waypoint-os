"""
Backend tests for GET /payments read-model API.

Run:
  uv run pytest tests/test_payments_queue_api.py -q
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

import server
from server import app
from spine_api.persistence import TripStore, TEST_AGENCY_ID


def _resolve_agency_ids() -> tuple[str, str | None]:
    import json
    import subprocess
    import sys

    code = (
        "import asyncio, asyncpg, json\n"
        "async def run():\n"
        "  conn = await asyncpg.connect(host='localhost', port=5432, user='waypoint', password='waypoint_dev_password', database='waypoint_os')\n"
        "  row = await conn.fetchrow(\"SELECT agency_id FROM memberships WHERE user_id = $1 AND is_primary = TRUE\", '323468de-ba3d-437b-aa10-35b281a0c6a6')\n"
        "  primary = row['agency_id'] if row else None\n"
        "  row2 = await conn.fetchrow(\"SELECT id FROM agencies WHERE id <> $1 LIMIT 1\", primary if primary else '')\n"
        "  other = row2['id'] if row2 else None\n"
        "  print(json.dumps({'primary': primary, 'other': other}))\n"
        "  await conn.close()\n"
        "asyncio.run(run())\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        return TEST_AGENCY_ID, None
    data = json.loads(result.stdout.strip())
    return (data.get("primary") or TEST_AGENCY_ID, data.get("other"))


@pytest.fixture(scope="module")
def agency_ids():
    return _resolve_agency_ids()


@pytest.fixture()
def agency_id(agency_ids):
    return agency_ids[0]


@pytest.fixture(autouse=True)
def override_payments_agency_dependency(agency_id):
    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[server.get_current_agency] = lambda: SimpleNamespace(id=agency_id)
    try:
        yield
    finally:
        app.dependency_overrides = original_overrides


@pytest.fixture()
def trip_factory(agency_id):
    created_ids: list[str] = []

    def _create_trip(source: str = "payments_queue_api_test") -> str:
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
        created_ids.append(trip_id)
        return trip_id

    yield _create_trip

    for trip_id in created_ids:
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
    def test_full_tenant_scope_not_limited_to_initial_5000(self, session_client, monkeypatch, agency_id):
        total_trips = 5002

        def _trip_row(idx: int) -> dict:
            return {
                "id": f"trip_{idx}",
                "trip_name": f"Trip {idx}",
                "status": "assigned",
                "start_date": None,
                "updated_at": None,
            }

        call_offsets: list[int] = []

        def fake_list_trip_summaries_for_agency(*, agency_id: str, status=None, limit: int = 100, offset: int = 0):
            assert agency_id
            call_offsets.append(offset)
            if offset >= total_trips:
                return []
            end = min(offset + limit, total_trips)
            return [_trip_row(i) for i in range(offset, end)]

        def fake_get_booking_data_for_agency(trip_id: str, agency_id: str):
            idx = int(trip_id.split("_")[1])
            if idx >= 5000:
                return {
                    "payment_tracking": {
                        "payment_status": "partially_paid",
                        "refund_status": "not_applicable",
                        "agreed_amount": 1000,
                        "amount_paid": 200,
                        "final_payment_due": (date.today() + timedelta(days=2)).isoformat(),
                    }
                }
            return {
                "payment_tracking": {
                    "payment_status": "paid",
                    "refund_status": "not_applicable",
                    "agreed_amount": 1000,
                    "amount_paid": 1000,
                }
            }

        monkeypatch.setattr(server.TripStore, "list_trip_summaries_for_agency", fake_list_trip_summaries_for_agency)
        monkeypatch.setattr(server.TripStore, "get_booking_data_for_agency", fake_get_booking_data_for_agency)

        resp = session_client.get("/payments?queue_status=due_soon&limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()

        assert body["pagination"]["total"] == 2
        assert body["summary"]["total"] == 2
        assert body["summary"]["by_queue_status"]["due_soon"] == 2
        assert body["pagination"]["returned"] == 2
        assert [item["trip_id"] for item in body["items"]] == ["trip_5000", "trip_5001"]

        # Ensure backend iterated beyond the initial 5000 records.
        assert any(offset >= 5000 for offset in call_offsets)

    def test_tenant_isolation(self, session_client, agency_id, agency_ids, trip_factory):
        trip_id = trip_factory("payments_queue_tenant")
        _set_booking_data(
            trip_id,
            agency_id,
            {
                "payment_tracking": _payment_tracking(
                    payment_status="partially_paid",
                    agreed=1000,
                    paid=100,
                    final_due=date.today() + timedelta(days=3),
                )
            },
        )

        baseline = session_client.get("/payments")
        assert baseline.status_code == 200
        baseline_ids = {item["trip_id"] for item in baseline.json()["items"]}
        assert trip_id in baseline_ids

        other_agency_id = agency_ids[1]
        if not other_agency_id:
            pytest.skip("No second agency found for tenant isolation override")

        original_overrides = dict(app.dependency_overrides)
        app.dependency_overrides[server.get_current_agency] = lambda: SimpleNamespace(id=other_agency_id)
        try:
            isolated = session_client.get("/payments")
            assert isolated.status_code == 200
            isolated_ids = {item["trip_id"] for item in isolated.json()["items"]}
            assert trip_id not in isolated_ids
        finally:
            app.dependency_overrides = original_overrides

    def test_queue_derivation_missing_partial_overdue_paid_refund(self, session_client, agency_id, trip_factory):
        trip_missing = trip_factory("payments_queue_missing")
        trip_partial = trip_factory("payments_queue_partial")
        trip_overdue = trip_factory("payments_queue_overdue")
        trip_paid = trip_factory("payments_queue_paid")
        trip_refund = trip_factory("payments_queue_refund")

        _set_booking_data(trip_missing, agency_id, None)
        _set_booking_data(
            trip_partial,
            agency_id,
            {
                "payment_tracking": _payment_tracking(payment_status="unknown", notes="internal note should not leak"),
            },
        )
        _set_booking_data(
            trip_overdue,
            agency_id,
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
            agency_id,
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
            agency_id,
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

    def test_pagination_after_filtering_and_filtered_summary(self, session_client, agency_id, trip_factory):
        trip_due_old = trip_factory("payments_queue_due_old")
        trip_overdue = trip_factory("payments_queue_between")
        trip_due_new = trip_factory("payments_queue_due_new")

        _set_booking_data(
            trip_due_old,
            agency_id,
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
            agency_id,
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
            agency_id,
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
