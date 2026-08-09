"""
spine_api/routers/commission.py — Automated Supplier Commission Reconciliation & Split Settlement Engine (IDEA-124).

Tracks expected supplier commissions (GDS, bedbank, cruise, hotel), reconciles actual supplier payouts against expectations,
detects commission variance discrepancies, and calculates advisor/agency split settlements.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/commission", tags=["Supplier Commission & Split Settlement"])


class ExpectedCommissionRecord(BaseModel):
    trip_id: str
    destination: str
    supplier_name: str
    gross_booking_amount_cents: int
    expected_commission_pct: float
    expected_commission_cents: int
    advisor_split_pct: float = 70.0
    expected_advisor_payout_cents: int
    expected_agency_net_cents: int
    actual_payout_cents: Optional[int] = None
    actual_advisor_payout_cents: Optional[int] = None
    variance_cents: Optional[int] = None
    status: str = "PENDING"  # PENDING, RECONCILED, UNDERPAID, OVERDUE
    last_updated_at: str


class RecordCommissionRequest(BaseModel):
    trip_id: str
    supplier_name: Optional[str] = "Supplier Partner"
    gross_booking_amount_cents: int
    expected_commission_pct: float = 10.0
    advisor_split_pct: float = 70.0


class ReconcileCommissionRequest(BaseModel):
    trip_id: str
    actual_payout_cents: int
    supplier_reference: Optional[str] = None
    notes: Optional[str] = None


class CommissionSummaryResponse(BaseModel):
    total_expected_cents: int
    total_collected_cents: int
    total_advisor_payout_cents: int
    total_agency_net_cents: int
    pending_count: int
    underpaid_count: int
    reconciled_count: int
    records: List[ExpectedCommissionRecord] = Field(default_factory=list)


@router.get("/summary", response_model=CommissionSummaryResponse)
def get_commission_summary(
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """List and summarize supplier commissions and advisor splits across agency trips."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trips = TripStore.list_trips(agency_id=agency_id)

    records: List[ExpectedCommissionRecord] = []
    total_expected = 0
    total_collected = 0
    total_advisor = 0
    total_agency = 0
    pending_cnt = 0
    underpaid_cnt = 0
    reconciled_cnt = 0

    now_iso = datetime.now(timezone.utc).isoformat()

    for trip in trips:
        comm_data = trip.get("commission")
        rec_option = trip.get("strategy", {}).get("recommended_option", {}) or {}
        supplier_name = rec_option.get("name") or "Primary Supplier"
        gross_cents = int((rec_option.get("cost") or 3000) * 100)

        if not comm_data:
            # Default 10% commission, 70% advisor split
            exp_pct = 10.0
            split_pct = 70.0
            exp_comm = int(gross_cents * (exp_pct / 100.0))
            exp_adv = int(exp_comm * (split_pct / 100.0))
            exp_net = exp_comm - exp_adv
            rec = ExpectedCommissionRecord(
                trip_id=trip["id"],
                destination=trip.get("destination") or "Destination",
                supplier_name=supplier_name,
                gross_booking_amount_cents=gross_cents,
                expected_commission_pct=exp_pct,
                expected_commission_cents=exp_comm,
                advisor_split_pct=split_pct,
                expected_advisor_payout_cents=exp_adv,
                expected_agency_net_cents=exp_net,
                status="PENDING",
                last_updated_at=now_iso,
            )
        else:
            rec = ExpectedCommissionRecord(**comm_data)

        records.append(rec)
        total_expected += rec.expected_commission_cents
        if rec.actual_payout_cents is not None:
            total_collected += rec.actual_payout_cents
            total_advisor += rec.actual_advisor_payout_cents or 0
            total_agency += (rec.actual_payout_cents - (rec.actual_advisor_payout_cents or 0))

        if rec.status == "PENDING":
            pending_cnt += 1
        elif rec.status == "UNDERPAID":
            underpaid_cnt += 1
        elif rec.status == "RECONCILED":
            reconciled_cnt += 1

    return CommissionSummaryResponse(
        total_expected_cents=total_expected,
        total_collected_cents=total_collected,
        total_advisor_payout_cents=total_advisor,
        total_agency_net_cents=total_agency,
        pending_count=pending_cnt,
        underpaid_count=underpaid_cnt,
        reconciled_count=reconciled_cnt,
        records=records,
    )


@router.post("/record", response_model=ExpectedCommissionRecord)
def record_expected_commission(
    body: RecordCommissionRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Set or update expected supplier commission and advisor split on a trip booking."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    exp_comm_cents = int(body.gross_booking_amount_cents * (body.expected_commission_pct / 100.0))
    exp_advisor_cents = int(exp_comm_cents * (body.advisor_split_pct / 100.0))
    exp_agency_net = exp_comm_cents - exp_advisor_cents
    now_iso = datetime.now(timezone.utc).isoformat()

    rec = ExpectedCommissionRecord(
        trip_id=body.trip_id,
        destination=trip.get("destination") or "Destination",
        supplier_name=body.supplier_name or "Supplier Partner",
        gross_booking_amount_cents=body.gross_booking_amount_cents,
        expected_commission_pct=body.expected_commission_pct,
        expected_commission_cents=exp_comm_cents,
        advisor_split_pct=body.advisor_split_pct,
        expected_advisor_payout_cents=exp_advisor_cents,
        expected_agency_net_cents=exp_agency_net,
        status="PENDING",
        last_updated_at=now_iso,
    )

    trip["commission"] = rec.model_dump()
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="commission_recorded",
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "expected_commission_cents": exp_comm_cents,
            "advisor_split_pct": body.advisor_split_pct,
        },
    )

    return rec


@router.post("/reconcile", response_model=ExpectedCommissionRecord)
def reconcile_supplier_commission(
    body: ReconcileCommissionRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Reconcile actual supplier payout against expected commission, detecting variances and calculating splits."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    comm_data = trip.get("commission")
    now_iso = datetime.now(timezone.utc).isoformat()

    if not comm_data:
        rec_option = trip.get("strategy", {}).get("recommended_option", {}) or {}
        gross_cents = int((rec_option.get("cost") or 3000) * 100)
        exp_comm = int(gross_cents * 0.10)
        exp_adv = int(exp_comm * 0.70)
        exp_net = exp_comm - exp_adv
        rec = ExpectedCommissionRecord(
            trip_id=body.trip_id,
            destination=trip.get("destination") or "Destination",
            supplier_name="Primary Supplier",
            gross_booking_amount_cents=gross_cents,
            expected_commission_pct=10.0,
            expected_commission_cents=exp_comm,
            advisor_split_pct=70.0,
            expected_advisor_payout_cents=exp_adv,
            expected_agency_net_cents=exp_net,
            status="PENDING",
            last_updated_at=now_iso,
        )
    else:
        rec = ExpectedCommissionRecord(**comm_data)

    rec.actual_payout_cents = body.actual_payout_cents
    variance = body.actual_payout_cents - rec.expected_commission_cents
    rec.variance_cents = variance

    # Calculate actual advisor payout based on agreed split pct
    rec.actual_advisor_payout_cents = int(body.actual_payout_cents * (rec.advisor_split_pct / 100.0))

    if variance >= 0:
        rec.status = "RECONCILED"
        event_type = "commission_reconciled"
    else:
        rec.status = "UNDERPAID"
        event_type = "commission_variance_detected"

    rec.last_updated_at = now_iso
    trip["commission"] = rec.model_dump()
    TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type=event_type,
        user_id=agency_id,
        details={
            "trip_id": body.trip_id,
            "expected_commission_cents": rec.expected_commission_cents,
            "actual_payout_cents": body.actual_payout_cents,
            "variance_cents": variance,
            "status": rec.status,
            "supplier_reference": body.supplier_reference,
            "notes": body.notes,
        },
    )

    return rec
