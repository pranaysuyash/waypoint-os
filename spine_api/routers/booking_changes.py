"""
spine_api/routers/booking_changes.py — Booking-change ledger + traveler visibility (FND-0410).

Durable ledger of supplier-side changes to CONFIRMED bookings (hotel/airline
cancellation, overbook, schedule change, rate change) with honest provenance
and traveler-visible exposure through the public proposal payload.

Doctrine alignment:

- Interim signal source = operator-reported (D6 precedent, mirrored from the
  R2-H disruption door). Live provider feeds are DP-04a-gated; when one
  lands, provider-observed rows supersede by authority precedence — the
  ``source`` field is the precedence key and ``provider_observed`` is a
  reserved value from day one so nothing needs to be re-shaped later.
- Flight IRROPS keeps its own door (disruption_radar + IRROPS severity
  semantics); hotel/overbook/rate changes are booking-domain facts and do
  not masquerade as flight disruptions.
- Storage = trip JSONB (``booking_changes`` / ``booking_change_history``),
  the same pattern as ``active_disruption``/``disruption_history`` — no new
  table, dual-store behavior inherited from TripStore.
- Clara constraint: the traveler-visible shape carries kind/supplier/time/
  notes with explicit advisor-reported labeling — never rendered as a
  provider-confirmed fact while ``source`` is ``operator_reported``.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Booking Changes"])

CHANGE_KINDS = ("cancellation", "overbook", "schedule_change", "rate_change")
SUPPLIERS = ("hotel", "airline", "rail", "transfer", "activity", "other")
BASIS_CHANNELS = ("email", "phone", "portal", "supplier_dashboard", "other")

# Authority precedence (ascending). ``provider_observed`` outranks operator
# reports so a future DP-04a feed supersedes without reshaping the ledger.
SOURCE_PRECEDENCE = {"operator_reported": 10, "provider_observed": 20}


class ReportBookingChangeRequest(BaseModel):
    change_kind: str  # cancellation | overbook | schedule_change | rate_change
    supplier: str  # hotel | airline | rail | transfer | activity | other
    supplier_ref: Optional[str] = None  # booking/hotel confirmation ref
    basis_channel: str = "email"  # how the operator learned about it
    basis_reference: Optional[str] = None  # email subject, call log, portal ref
    notes: str = ""
    affected_travelers: List[str] = Field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _change_id(marker: str) -> str:
    return f"bkchg_{abs(hash(marker)) % 100000:05d}_{hashlib.sha256(marker.encode()).hexdigest()[:8]}"


def _validate_report(body: ReportBookingChangeRequest) -> None:
    if body.change_kind not in CHANGE_KINDS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown change kind '{body.change_kind}' — expected one of {sorted(CHANGE_KINDS)}",
        )
    if body.supplier not in SUPPLIERS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown supplier '{body.supplier}' — expected one of {sorted(SUPPLIERS)}",
        )
    if body.basis_channel not in BASIS_CHANNELS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown basis channel '{body.basis_channel}' — expected one of {sorted(BASIS_CHANNELS)}",
        )
    if body.change_kind == "cancellation" and not body.notes.strip():
        # A cancellation with no basis text is not a reportable fact — refuse
        # instead of storing an empty claim (truth-taxonomy posture).
        raise HTTPException(
            status_code=422,
            detail="A cancellation report requires notes describing the basis (what the supplier said, where).",
        )


def _traveler_shape(row: Dict[str, Any]) -> Dict[str, Any]:
    """The traveler-visible projection of a booking change (FND-0410).

    Honest provenance: while ``source`` is ``operator_reported`` the row is
    explicitly labeled as advisor-reported — never as a provider-confirmed
    fact. Minimum surface: kind/supplier/time/notes; no internal refs,
    no operator identities.
    """
    return {
        "change_id": row.get("change_id"),
        "change_kind": row.get("change_kind"),
        "supplier": row.get("supplier"),
        "supplier_ref": row.get("supplier_ref"),
        "reported_at": row.get("reported_at"),
        "notes": row.get("notes", ""),
        "affected_travelers": row.get("affected_travelers") or [],
        "source": row.get("source"),
        "source_label": (
            "Reported by your travel advisor"
            if row.get("source") == "operator_reported"
            else "Confirmed by supplier feed"
        ),
    }


@router.post("/trips/{trip_id}/booking-changes")
def report_booking_change(
    trip_id: str,
    body: ReportBookingChangeRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Operator-reported booking change → trip ``booking_changes`` ledger
    (FND-0410). Idempotency marker (trip + supplier + kind + ref + hour) so a
    duplicate report in the same window is detectable by callers."""
    _validate_report(body)

    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    now = _now_iso()
    report_hour = now[:13]
    marker = f"bkchg:{trip_id}:{body.supplier}:{body.change_kind}:{body.supplier_ref or ''}:{report_hour}"

    ledger = trip.get("booking_changes") or []
    if any(row.get("idempotency_marker") == marker for row in ledger):
        raise HTTPException(
            status_code=409,
            detail="This booking change was already reported in the current window (idempotent duplicate).",
        )

    row = {
        "change_id": _change_id(marker),
        "trip_id": trip_id,
        "change_kind": body.change_kind,
        "supplier": body.supplier,
        "supplier_ref": body.supplier_ref,
        "basis_channel": body.basis_channel,
        "basis_reference": body.basis_reference,
        "notes": (body.notes or "")[:500],
        "affected_travelers": body.affected_travelers[:20],
        "source": "operator_reported",  # D6: interim signal source
        "source_basis": f"{body.basis_channel}:{body.basis_reference or 'unspecified'}",
        "reported_by": agency_id,
        "idempotency_marker": marker,
        "reported_at": now,
        "status": "ACTIVE",
    }
    ledger.append(row)
    updated = TripStore.update_trip_for_agency(trip_id, agency_id, {"booking_changes": ledger})
    if updated is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    AuditStore.log_event(
        event_type="booking_change_reported",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "change_kind": body.change_kind,
            "supplier": body.supplier,
            "supplier_ref": body.supplier_ref,
            "source": row["source"],
            "idempotency_marker": marker,
        },
    )
    return {"ok": True, "trip_id": trip_id, "booking_change": row}


@router.get("/trips/{trip_id}/booking-changes")
def list_booking_changes(trip_id: str, agency_id: str = Depends(get_current_agency_id)):
    """Full operator ledger: active changes + resolved history."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {
        "ok": True,
        "trip_id": trip_id,
        "active": trip.get("booking_changes") or [],
        "history": trip.get("booking_change_history") or [],
    }


@router.get("/trips/{trip_id}/booking-changes/traveler-view")
def traveler_view_booking_changes(trip_id: str, agency_id: str = Depends(get_current_agency_id)):
    """Operator-preview of exactly what travelers see (Clara: honest labels,
    minimum surface) — used by the ops page to check the traveler-facing
    rendering without opening the public portal."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    active = trip.get("booking_changes") or []
    return {"ok": True, "trip_id": trip_id, "changes": [_traveler_shape(row) for row in active]}


@router.post("/trips/{trip_id}/booking-changes/{change_id}/resolve")
def resolve_booking_change(trip_id: str, change_id: str, agency_id: str = Depends(get_current_agency_id)):
    """Resolve a booking change (FND-0410): archive the full provenance row to
    ``booking_change_history`` and remove it from the active ledger — mirrors
    the disruption resolve contract (FND-0405). Nothing is deleted."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    ledger = trip.get("booking_changes") or []
    matched = next((row for row in ledger if row.get("change_id") == change_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail="Booking change not found in active ledger")

    resolved = dict(matched)
    resolved["status"] = "RESOLVED"
    resolved["resolved_at"] = _now_iso()

    remaining = [row for row in ledger if row.get("change_id") != change_id]
    history = (trip.get("booking_change_history") or []) + [resolved]
    updated = TripStore.update_trip_for_agency(
        trip_id, agency_id, {"booking_changes": remaining, "booking_change_history": history}
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    AuditStore.log_event(
        event_type="booking_change_resolved",
        user_id=agency_id,
        details={"trip_id": trip_id, "change_id": change_id, "change_kind": resolved.get("change_kind")},
    )
    return {"ok": True, "trip_id": trip_id, "resolved": resolved, "active_count": len(remaining)}


def traveler_visible_changes(trip: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public-payload projection hook — used by the public proposal router to
    expose active booking changes on the traveler portal (FND-0410). Kept in
    this module so the traveler shape has exactly one definition."""
    active = trip.get("booking_changes") or []
    return [_traveler_shape(row) for row in active if row.get("status") == "ACTIVE"]
