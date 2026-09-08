"""
tests/test_pa_wave2_payout_ledger_sql.py — PA-23 wave 2: durable payout ledger + settlement reconciliation.

Pins:
1. AdvisorPayoutStore contract (memory): uuid payout ids, unique payout_ref,
   agency scoping, CAS void, trip-linked listing.
2. SQL store shape (durable backend): identical interface behind the
   ``require_postgres`` skip pattern — skips gracefully without live Postgres.
3. Backend detection precedence: explicit env var > production default >
   memory (tests never silently flip to SQL).
4. ``reconcile_trip_commission``: real delta math between the trip's
   booking_confirmation.total_charged_usd and recorded payouts — matched /
   mismatch / no_booking / no_payouts, honestly labeled (reported, never
   auto-fixed).

S2 notes (failed-before / passes-after):
- FAILED BEFORE: nothing linked booking totals to the payout ledger —
  payouts were memory-only preview rows with no settlement reconciliation.
- PASSES AFTER: payouts are durably recordable (SQL) and
  ``GET /api/v1/subagent-payouts/reconciliation/{trip_id}`` reports expected
  vs recorded with exact delta math.
"""

import uuid

import pytest

from spine_api.services import commission_reconciliation as cr
from spine_api.services.advisor_payout_store import AdvisorPayoutStore, backend
from spine_api.persistence import TripStore


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("SPINE_API_ADVISOR_PAYOUT_BACKEND", "memory")
    monkeypatch.delenv("ENVIRONMENT", raising=False)


@pytest.fixture(autouse=True)
def _isolated_ledger(monkeypatch):
    monkeypatch.setattr(cr, "ADVISOR_LEDGERS", {})
    AdvisorPayoutStore._MEMORY_STORE.clear()
    yield
    cr.ADVISOR_LEDGERS.clear()
    AdvisorPayoutStore._MEMORY_STORE.clear()


# ---------------------------------------------------------------------------
# Store contract (memory)
# ---------------------------------------------------------------------------


def test_record_payout_shape_and_agency_scoping():
    agency = f"agency_{uuid.uuid4().hex[:8]}"
    record = AdvisorPayoutStore.record_payout(
        agency_id=agency,
        advisor_id="adv_1",
        amount_usd=250.0,
        recorded_by="req_1",
        trip_id="trip_abc",
    )
    assert record.payout_id.startswith("pay_")
    assert record.payout_ref.startswith("PO-")
    assert record.status == "recorded"
    assert record.method == "DIRECT_DEPOSIT"
    d = record.to_dict()
    assert d["storage_backend"] == "memory"

    fetched = AdvisorPayoutStore.get_payout(agency_id=agency, payout_id=record.payout_id)
    assert fetched is not None
    assert fetched["amount_usd"] == 250.0
    # Cross-agency read is refused.
    assert AdvisorPayoutStore.get_payout(agency_id="agency_other", payout_id=record.payout_id) is None


def test_payout_ids_and_refs_are_unique_within_the_same_instant():
    agency = f"agency_{uuid.uuid4().hex[:8]}"
    first = AdvisorPayoutStore.record_payout(
        agency_id=agency, advisor_id="adv_u", amount_usd=10.0, recorded_by="r"
    )
    second = AdvisorPayoutStore.record_payout(
        agency_id=agency, advisor_id="adv_u", amount_usd=10.0, recorded_by="r"
    )
    assert first.payout_id != second.payout_id
    assert first.payout_ref != second.payout_ref


def test_void_is_cas():
    agency = f"agency_{uuid.uuid4().hex[:8]}"
    record = AdvisorPayoutStore.record_payout(
        agency_id=agency, advisor_id="adv_v", amount_usd=50.0, recorded_by="r"
    )
    assert AdvisorPayoutStore.void_payout(agency_id=agency, payout_id=record.payout_id, note="oops")
    # Second void is refused (status no longer recorded) — CAS, not idempotent overwrite.
    assert not AdvisorPayoutStore.void_payout(agency_id=agency, payout_id=record.payout_id)
    # Default listing only shows recorded payouts.
    assert AdvisorPayoutStore.list_payouts(agency_id=agency, advisor_id="adv_v") == []


def test_memory_payouts_also_flow_through_process_authorization():
    """process_advisor_payout_authorization mirrors movements into the store so
    trip-linked reconciliation sees memory-backend payouts too."""
    cr.process_advisor_payout_authorization(
        "adv_mirror", 8000, agency_id="system", trip_id="trip_mirror", recorded_by="req_m"
    )
    rows = AdvisorPayoutStore.list_payouts(agency_id="system", trip_id="trip_mirror")
    assert len(rows) == 1
    assert rows[0]["amount_usd"] == 80.0


# ---------------------------------------------------------------------------
# Backend detection precedence
# ---------------------------------------------------------------------------


def test_backend_detection_precedence(monkeypatch):
    monkeypatch.setenv("SPINE_API_ADVISOR_PAYOUT_BACKEND", "memory")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    assert backend() == "memory"  # explicit env var wins over production default

    monkeypatch.setenv("SPINE_API_ADVISOR_PAYOUT_BACKEND", "postgres")
    assert backend() == "sql"

    monkeypatch.delenv("SPINE_API_ADVISOR_PAYOUT_BACKEND")
    monkeypatch.delenv("DATABASE_URL")
    assert backend() == "memory"  # production without a DB URL cannot go SQL

    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    assert backend() == "sql"  # production default

    monkeypatch.setenv("ENVIRONMENT", "development")
    assert backend() == "memory"  # dev/test default


# ---------------------------------------------------------------------------
# SQL store shape (skips without live Postgres)
# ---------------------------------------------------------------------------


@pytest.mark.require_postgres
def test_sql_store_shape_and_roundtrip(monkeypatch):
    monkeypatch.setenv("SPINE_API_ADVISOR_PAYOUT_BACKEND", "sql")
    agency = f"agency_sql_{uuid.uuid4().hex[:10]}"
    advisor = f"adv_sql_{uuid.uuid4().hex[:8]}"

    record = AdvisorPayoutStore.record_payout(
        agency_id=agency,
        advisor_id=advisor,
        amount_usd=123.45,
        recorded_by="req_sql",
        trip_id=f"trip_sql_{uuid.uuid4().hex[:8]}",
        method="ACH",
    )
    d = record.to_dict()
    assert d["storage_backend"] == "sql"
    assert d["payout_id"].startswith("pay_")
    assert d["payout_ref"].startswith("PO-")
    assert d["method"] == "ACH"

    fetched = AdvisorPayoutStore.list_payouts(agency_id=agency, advisor_id=advisor)
    assert len(fetched) == 1
    assert fetched[0]["amount_usd"] == 123.45
    assert fetched[0]["status"] == "recorded"

    # CAS void through SQL.
    assert AdvisorPayoutStore.void_payout(agency_id=agency, payout_id=record.payout_id)
    assert not AdvisorPayoutStore.void_payout(agency_id=agency, payout_id=record.payout_id)
    assert AdvisorPayoutStore.list_payouts(agency_id=agency, advisor_id=advisor) == []


# ---------------------------------------------------------------------------
# Settlement reconciliation (memory backend; real delta math)
# ---------------------------------------------------------------------------


def _seed_confirmed_trip(total_charged_usd: float) -> str:
    trip_id = f"trip_recon_{uuid.uuid4().hex[:10]}"
    TripStore.save_trip(
        {
            "id": trip_id,
            "agency_id": "system",
            "status": "booked",
            "destination": "Paris",
            "packet": {"destination": "Paris", "start_date": "2026-10-15", "end_date": "2026-10-22"},
            "booking_confirmation": {
                "pnr_locator": "PNR123",
                "total_charged_usd": total_charged_usd,
            },
        },
        agency_id="system",
    )
    return trip_id


def test_reconciliation_matched_exact_delta_math():
    # Expected advisor commission: $1,000 * 10% pool * 80% split = $80.
    trip_id = _seed_confirmed_trip(1000.0)
    cr.process_advisor_payout_authorization(
        "adv_recon_1", 8000, agency_id="system", trip_id=trip_id, recorded_by="req"
    )
    result = cr.reconcile_trip_commission(trip_id=trip_id, agency_id="system")
    assert result["status"] == "matched"
    assert result["expected_usd"] == 80.0
    assert result["recorded_usd"] == 80.0
    assert result["delta_usd"] == 0.0


def test_reconciliation_mismatch_reports_delta_and_never_autofixes():
    trip_id = _seed_confirmed_trip(1000.0)
    cr.process_advisor_payout_authorization(
        "adv_recon_2", 5000, agency_id="system", trip_id=trip_id, recorded_by="req"
    )
    result = cr.reconcile_trip_commission(trip_id=trip_id, agency_id="system")
    assert result["status"] == "mismatch"
    assert result["expected_usd"] == 80.0
    assert result["recorded_usd"] == 50.0
    assert result["delta_usd"] == -30.0
    assert "never auto-fixed" in result["reason"]


def test_reconciliation_no_payouts():
    trip_id = _seed_confirmed_trip(2000.0)
    result = cr.reconcile_trip_commission(trip_id=trip_id, agency_id="system")
    assert result["status"] == "no_payouts"
    assert result["expected_usd"] == 160.0
    assert result["recorded_usd"] == 0.0
    assert result["delta_usd"] == -160.0


def test_reconciliation_no_booking_and_tenancy():
    # Missing trip entirely.
    result = cr.reconcile_trip_commission(trip_id="trip_missing_xyz", agency_id="system")
    assert result["status"] == "no_booking"
    # Trip without a confirmed booking total.
    trip_id = f"trip_recon_nb_{uuid.uuid4().hex[:8]}"
    TripStore.save_trip(
        {"id": trip_id, "agency_id": "system", "status": "assigned", "destination": "Paris"},
        agency_id="system",
    )
    result = cr.reconcile_trip_commission(trip_id=trip_id, agency_id="system")
    assert result["status"] == "no_booking"
    # Trip owned by another agency is not reconcilable under this agency.
    foreign_trip = f"trip_recon_foreign_{uuid.uuid4().hex[:8]}"
    TripStore.save_trip(
        {
            "id": foreign_trip,
            "agency_id": "agency_b",
            "status": "booked",
            "destination": "Rome",
            "booking_confirmation": {"pnr_locator": "PNR999", "total_charged_usd": 1000.0},
        },
        agency_id="agency_b",
    )
    result = cr.reconcile_trip_commission(trip_id=foreign_trip, agency_id="agency_not_owner")
    assert result["status"] == "no_booking"
