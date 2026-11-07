"""Commission-statement ingest breadth (R2-B / Travefy bar, 2026-11-03).

Acceptance spec per the 2026-10-30 adjudication: CSV/email/image ingest,
fuzzy supplier match, manual-link fallback. S2 evidence: the parser and
matcher are deterministic; every acceptance row below pins behavior the
previous engine (booking-total-only reconcile) could not express.
"""

from __future__ import annotations

import pytest

from spine_api.services.commission_ingest import (
    create_ingest_batch,
    get_batch,
    link_row,
    record_row_payout,
    match_rows,
    parse_csv_statement,
    parse_line_statement,
    fuzzy_supplier_score,
)
from spine_api.routers.commission import IngestStatementRequest


TRIPS = [
    {
        "id": "trip_bali",
        "destination": "Bali",
        "booking_confirmation": {
            "total_charged_usd": 2400.00,
            "supplier_name": "Bali Villas Direct",
            "booking_ref": "BVD-88231",
        },
    },
    {
        "id": "trip_kerala",
        "destination": "Kerala",
        "booking_confirmation": {
            "total_charged_usd": 1180.50,
            "supplier_name": "Kerala Houseboats Co",
            "booking_ref": "KH-1104",
        },
    },
]


def test_csv_statement_parses_with_and_without_header():
    with_header = (
        "supplier,booking_ref,amount,currency,date\n"
        "Bali Villas Direct,BVD-88231,2400.00,USD,2026-10-12\n"
    )
    rows = parse_csv_statement(with_header)
    assert len(rows) == 1
    assert rows[0].supplier_name == "Bali Villas Direct"
    assert rows[0].booking_ref == "BVD-88231"
    assert rows[0].amount == 2400.00

    headerless = "Kerala Houseboats Co,KH-1104,1180.50,USD,2026-10-14\n"
    rows = parse_csv_statement(headerless)
    assert len(rows) == 1
    assert rows[0].booking_ref == "KH-1104"


def test_email_statement_parses_line_rows():
    body = (
        "Dear partner,\n\n"
        "Commission statement October 2026\n"
        "Bali Villas Direct BVD-88231 2400.00 USD 2026-10-12\n"
        "Kerala Houseboats Co KH-1104 1180.50 USD 2026-10-14\n"
        "Regards,\nAccounts\n"
    )
    rows = parse_line_statement(body, "email")
    assert len(rows) == 2
    assert {r.booking_ref for r in rows} == {"BVD-88231", "KH-1104"}


def test_unrecognizable_lines_are_never_fabricated_into_rows():
    body = "Hello\nHow are you\nPlease find the statement attached\n"
    assert parse_line_statement(body, "email") == []


def test_match_booking_ref_exact():
    rows = parse_csv_statement(
        "Bali Villas Direct,BVD-88231,2400.00,USD,2026-10-12\n"
    )
    match_rows(rows, TRIPS)
    assert rows[0].match_status == "matched"
    assert rows[0].match_trip_id == "trip_bali"
    assert rows[0].match_method == "booking_ref"


def test_match_amount_tolerance_plus_fuzzy_supplier():
    # Sim-pass money-safety fix (2026-11-07): a fuzzy match is a SUGGESTION
    # attached to a manual_candidate row — recording requires the operator to
    # explicitly link (confirm) first, so a difflib similarity can never
    # one-click a durable payout against a possibly-wrong trip.
    rows = parse_csv_statement(
        "Kerala Houseboat Co,STMT-77112,1181.20,USD,2026-10-14\n",
    )
    match_rows(rows, TRIPS)
    assert rows[0].match_status == "manual_candidate"
    assert rows[0].match_trip_id is None  # suggestion, not a binding
    assert rows[0].match_method == "fuzzy_suggestion"
    assert rows[0].match_confidence >= 0.6
    assert "trip_kerala" in rows[0].raw_text  # suggestion surfaced for review


def test_recognizable_row_without_match_is_manual_candidate():
    rows = parse_csv_statement(
        "Unknown Tours,XT-99999,500.00,USD,2026-10-15\n",
    )
    match_rows(rows, TRIPS)
    assert rows[0].match_status == "manual_candidate"
    assert rows[0].match_trip_id is None


def test_fuzzy_supplier_score_threshold():
    assert fuzzy_supplier_score("Kerala Houseboats Co", "Kerala Houseboat Co") >= 0.85
    assert fuzzy_supplier_score("Bali Villas Direct", "Totally Different Ltd") < 0.6


def test_batch_lifecycle_parse_match_link():
    batch = create_ingest_batch(
        source_format="csv",
        content=(
            "Bali Villas Direct,BVD-88231,2400.00,USD,2026-10-12\n"
            "Unknown Tours,XT-99999,500.00,USD,2026-10-15\n"
        ),
        agency_id="agency_ci",
        trips=TRIPS,
    )
    state = batch.to_dict()
    assert state["durable"] is False  # preview-grade until payout recorded
    assert state["matched_count"] == 1
    assert state["manual_candidate_count"] == 1

    # Manual-link fallback: operator asserts the row↔trip binding.
    manual_row_index = next(
        r.row_index for r in batch.rows if r.match_status == "manual_candidate"
    )
    updated = link_row(batch.batch_id, "agency_ci", manual_row_index, "trip_kerala")
    assert updated is not None
    assert updated.rows[manual_row_index].match_method == "manual_link"
    assert updated.rows[manual_row_index].match_trip_id == "trip_kerala"

    # Tenant scoping: another agency cannot see or link the batch.
    assert get_batch(batch.batch_id, "agency_other") is None
    assert link_row(batch.batch_id, "agency_other", manual_row_index, "trip_kerala") is None


def test_link_rejects_out_of_range_row():
    batch = create_ingest_batch(
        source_format="csv", content="A,B-1234,10.00\n", agency_id="agency_ci2", trips=TRIPS,
    )
    with pytest.raises(ValueError, match="out of range"):
        link_row(batch.batch_id, "agency_ci2", 99, "trip_bali")


def test_ingest_request_rejects_unknown_format():
    with pytest.raises((ValueError,)):  # service raises; router maps to 422
        create_ingest_batch(
            source_format="carrier_pigeon", content="x", agency_id="a", trips=[]
        )
    # The request model still accepts the field; validation is the service's.
    req = IngestStatementRequest(format="csv", content="a,b,c\n")
    assert req.format == "csv"


# ── record_row_payout: the R2-B money-truth closure ─────────────────────


def _matched_batch(agency_id="agency_rec", amount="2400.00", currency="USD"):
    return create_ingest_batch(
        source_format="csv",
        content=f"Bali Villas Direct,BVD-88231,{amount},{currency},2026-10-12\n",
        agency_id=agency_id,
        trips=TRIPS,
    )


def test_record_writes_durable_payout_and_marks_row(monkeypatch):
    import spine_api.services.commission_ingest as ci

    recorded = {}
    class _Payout:
        payout_id = "pay_rec_1"
        storage_backend = "sql"
    def _fake_record(**kwargs):
        recorded.update(kwargs)
        return _Payout()
    # The service imports AdvisorPayoutStore inside the function — patch the
    # source module attribute (the import resolves at call time).
    import spine_api.services.advisor_payout_store as aps
    monkeypatch.setattr(aps.AdvisorPayoutStore, "record_payout", staticmethod(_fake_record))

    batch = _matched_batch()
    updated, payout, error = ci.record_row_payout(
        batch.batch_id, "agency_rec", 0, advisor_id="adv_7", recorded_by="agency_rec",
    )
    assert error is None and payout is not None
    assert payout["payout_id"] == "pay_rec_1"
    assert payout["amount_usd"] == 2400.0
    assert payout["trip_id"] == "trip_bali"
    # Durable call carried the full provenance note + attribution.
    assert recorded["advisor_id"] == "adv_7"
    assert recorded["agency_id"] == "agency_rec"
    assert "batch" in recorded["note"] and "match" in recorded["note"]
    # Row marked; re-recording rejected (no double-count).
    assert updated.rows[0].recorded is True
    assert updated.rows[0].recorded_payout_id == "pay_rec_1"
    _, _, err2 = ci.record_row_payout(
        batch.batch_id, "agency_rec", 0, advisor_id="adv_7", recorded_by="agency_rec",
    )
    assert err2 is not None and "double-count" in err2


def test_record_rejects_unmatched_row():
    batch = create_ingest_batch(
        source_format="csv", content="Unknown Tours,XT-99999,500.00,USD,2026-10-15\n",
        agency_id="agency_rec2", trips=TRIPS,
    )
    _, _, error = record_row_payout(
        batch.batch_id, "agency_rec2", 0, advisor_id="adv_1", recorded_by="agency_rec2",
    )
    assert error is not None and "not matched" in error


def test_record_rejects_non_usd_row_no_silent_fx():
    batch = _matched_batch(agency_id="agency_rec3", amount="3000.00", currency="INR")
    _, _, error = record_row_payout(
        batch.batch_id, "agency_rec3", 0, advisor_id="adv_1", recorded_by="agency_rec3",
    )
    assert error is not None
    assert "INR" in error and "does not convert" in error


def test_record_rejects_missing_advisor():
    batch = _matched_batch(agency_id="agency_rec4")
    _, _, error = record_row_payout(
        batch.batch_id, "agency_rec4", 0, advisor_id="  ", recorded_by="agency_rec4",
    )
    assert error is not None and "advisor_id" in error


def test_record_rejects_already_recorded_row_idempotent(monkeypatch):
    import spine_api.services.advisor_payout_store as aps

    class _Payout:
        payout_id = "pay_rec_2"
        storage_backend = "sql"
    monkeypatch.setattr(
        aps.AdvisorPayoutStore, "record_payout",
        staticmethod(lambda **kw: _Payout()),
    )
    batch = _matched_batch(agency_id="agency_rec5")
    record_row_payout(batch.batch_id, "agency_rec5", 0, advisor_id="adv_1", recorded_by="agency_rec5")
    _, _, error = record_row_payout(
        batch.batch_id, "agency_rec5", 0, advisor_id="adv_1", recorded_by="agency_rec5",
    )
    assert error is not None and "already recorded" in error


def test_batches_persist_across_process_restart(monkeypatch, tmp_path):
    """FND-0404: batches survive a backend restart (disk store), so the
    operator's manual links are not orphaned mid-review."""
    import spine_api.services.commission_ingest as ci

    monkeypatch.setenv("WAYPOINT_COMMISSION_BATCHES_DIR", str(tmp_path))
    batch = create_ingest_batch(
        source_format="csv", content="Bali Villas Direct,BVD-88231,2400.00,USD\n",
        agency_id="agency_disk", trips=TRIPS,
    )
    # simulate restart: clear the in-process store
    ci._INGEST_BATCHES.clear()
    loaded = ci.get_batch(batch.batch_id, "agency_disk")
    assert loaded is not None
    assert loaded.rows[0].booking_ref == "BVD-88231"
    # tenant scoping still applies to disk-loaded batches
    assert ci.get_batch(batch.batch_id, "agency_other") is None
