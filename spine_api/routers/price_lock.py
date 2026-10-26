"""
spine_api/routers/price_lock.py — Autonomous Price-Lock Sentinel & Re-Shopping Alert Engine.

Monitors GDS, NDC, and bedbank rate holds during the 72-hour quote window (price_lock_expires_at).
Audits rate drops, calculates potential margin gains, and PREVIEWS advisor re-lock plans.

PA-06 (2026-09-06): the rate source is still simulated (in-memory supplier
contract rows with hardcoded fallbacks), so the re-lock endpoint is
PREVIEW-ONLY — it never mutates the trip of record. See ReLockResponse and the
re_lock_lower_rate docstring.

Topic 49 (2026-10-21): this router also hosts the POST-booking fare-drop
disposition ledger (``/{trip_id}/fare-drop/disposition``) so all re-shopping
surfaces live in one place. Unlike the preview endpoints above, the ledger IS
persisted — it records the advisor's decision, never a payment.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.auth import get_current_agency_id
from spine_api.persistence import AuditStore, TripStore
from spine_api.routers.supplier import CONTRACTS_STORE
from spine_api.services import fare_drop_disposition

router = APIRouter(prefix="/api/v1/price-lock", tags=["Price Lock Sentinel"])


class PriceLockOpportunity(BaseModel):
    trip_id: str
    destination: str
    supplier_name: str
    original_net_rate_cents: int
    current_net_rate_cents: int
    potential_margin_gain_cents: int
    margin_gain_pct: float
    price_lock_expires_at: str
    hours_remaining: float
    is_expired: bool


class RateAuditResponse(BaseModel):
    ok: bool = True
    trip_id: str
    supplier_name: str
    original_net_rate_cents: int
    current_net_rate_cents: int
    potential_margin_gain_cents: int
    margin_gain_pct: float
    rate_drop_detected: bool
    price_lock_expires_at: str


class ReLockRequest(BaseModel):
    trip_id: str
    new_net_rate_cents: int
    supplier_name: Optional[str] = None
    advisor_note: Optional[str] = None
    # PA-06: both guards are now REQUIRED (422 when absent) so the future
    # real-rate-source path inherits optimistic concurrency + replay protection.
    expected_version: int
    idempotency_key: str

class ReLockResponse(BaseModel):
    """PA-06 preview-only re-lock response.

    The rate source is still simulated (in-memory supplier contract row with
    hardcoded fallbacks), so the endpoint is PREVIEW-ONLY: it computes what a
    re-lock WOULD change and persists nothing. ``effects`` is always empty,
    ``would_persist`` is always False with reason ``simulated_rate_source``,
    and ``version`` echoes the trip's CURRENT version (unchanged). When a real
    rate source lands, this endpoint may gain a persist path guarded by the
    (now mandatory) optimistic-version and idempotency-key fields.
    """

    ok: bool = True
    trip_id: str
    preview: bool = True
    previous_net_rate_cents: int
    new_net_rate_cents: int
    margin_saved_cents: int
    updated_at: str
    version: int = 1
    # Preview / reality metadata (repo pattern: financial_settlement, distribution)
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    effects: List[str] = []
    would_persist: bool = False
    not_persisted_reason: str = "simulated_rate_source"


# FND-0119 (legacy F-32): single source of truth for WHERE the persisted
# price-lock expiry lives on a trip record. Writers MUST store the value under
# ``strategy[PRICE_LOCK_EXPIRES_AT_KEY]`` (canonical). The trip top-level key
# is a LEGACY write location (written by social_inbound.py before 2026-09-14)
# and is kept ONLY as a backward-compatible read fallback for existing rows.
PRICE_LOCK_EXPIRES_AT_KEY = "price_lock_expires_at"


def get_price_lock_expires_at_raw(trip: dict) -> Optional[str]:
    """Read the persisted price-lock expiry: canonical strategy location first,
    legacy trip top-level second (FND-0119 canonical-then-legacy contract).

    Returns the raw stored string, or ``None`` when neither location holds a
    value. Callers that need a ``datetime`` with the 72-hour recompute fallback
    should use :func:`_get_price_lock_expires_at`.
    """
    strategy = trip.get("strategy") or {}
    canonical = strategy.get(PRICE_LOCK_EXPIRES_AT_KEY)
    if canonical:
        return str(canonical)
    legacy = trip.get(PRICE_LOCK_EXPIRES_AT_KEY)
    return str(legacy) if legacy else None


def _get_price_lock_expires_at(trip: dict) -> datetime:
    """Calculate price lock expiration timestamp (default 72 hours from saved_at or created_at).

    Reads BOTH locations (FND-0119 / F-32): the canonical
    ``strategy.price_lock_expires_at`` (where all writers persist since
    2026-09-14) and the legacy trip top-level key for rows persisted before
    the canonical write convention. Either source wins over the recomputed
    fallback so the sentinel sees what was written.
    """
    raw_candidates = []
    strategy = trip.get("strategy", {}) or {}
    if strategy.get(PRICE_LOCK_EXPIRES_AT_KEY):
        raw_candidates.append(strategy[PRICE_LOCK_EXPIRES_AT_KEY])
    if trip.get(PRICE_LOCK_EXPIRES_AT_KEY):
        raw_candidates.append(trip[PRICE_LOCK_EXPIRES_AT_KEY])

    for raw_exp in raw_candidates:
        try:
            return datetime.fromisoformat(str(raw_exp).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

    base_time_str = trip.get("saved_at") or trip.get("created_at")
    if base_time_str:
        try:
            base_dt = datetime.fromisoformat(base_time_str.replace("Z", "+00:00"))
            return base_dt + timedelta(hours=72)
        except (ValueError, TypeError):
            pass

    return datetime.now(timezone.utc) + timedelta(hours=72)


@router.get("/opportunities", response_model=List[PriceLockOpportunity])
async def list_price_lock_opportunities(
    agency_id: str = Depends(get_current_agency_id),
):
    """Scan active agency trips for price lock countdowns and margin re-shopping opportunities.

    Paginates through ALL agency trips: TripStore.list_trips defaults to a
    100-row window, which silently dropped opportunities for agencies past
    that cap (surfaced by the FND-0119 sentinel test once the shared test
    agency accumulated 100 file-store trips).
    """
    trips: list = []
    offset = 0
    page_size = 100
    while True:
        page = TripStore.list_trips(agency_id=agency_id, offset=offset, limit=page_size)
        if not page:
            break
        trips.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    now = datetime.now(timezone.utc)
    opportunities: List[PriceLockOpportunity] = []

    for trip in trips:
        strategy = trip.get("strategy", {}) or {}
        rec_option = strategy.get("recommended_option", {}) or {}
        cost = rec_option.get("cost") or 0
        original_net_cents = int(cost * 100) if cost > 0 else 0

        exp_dt = _get_price_lock_expires_at(trip)
        hours_remaining = max(0.0, round((exp_dt - now).total_seconds() / 3600.0, 1))
        is_expired = now > exp_dt

        # Check contracts store or rate table for current rate
        contracts = CONTRACTS_STORE.get(agency_id, {})
        current_net_cents = original_net_cents
        supplier_name = rec_option.get("name") or "Primary Supplier Contract"

        if contracts:
            first_contract: dict = next(iter(contracts.values()), {})
            supplier_name = first_contract.get("supplier_name", supplier_name)
            rate_table = first_contract.get("rate_table", [])
            if rate_table and isinstance(rate_table, list) and len(rate_table) > 0:
                net_per_night = rate_table[0].get("net_rate_per_night", 300.0)
                current_net_cents = int(net_per_night * 100 * 5)  # 5 nights

        # Calculate margin delta
        gain_cents = max(0, original_net_cents - current_net_cents)
        gain_pct = round((gain_cents / original_net_cents) * 100.0, 2) if original_net_cents > 0 else 0.0

        opportunities.append(
            PriceLockOpportunity(
                trip_id=trip["id"],
                destination=trip.get("destination") or "Destination",
                supplier_name=supplier_name,
                original_net_rate_cents=original_net_cents,
                current_net_rate_cents=current_net_cents,
                potential_margin_gain_cents=gain_cents,
                margin_gain_pct=gain_pct,
                price_lock_expires_at=exp_dt.isoformat(),
                hours_remaining=hours_remaining,
                is_expired=is_expired,
            )
        )

    return opportunities


@router.post("/{trip_id}/audit-rate", response_model=RateAuditResponse)
async def audit_trip_price_lock_rate(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Audit supplier rate feed for a specific trip to detect rate drops and margin savings."""
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    strategy = trip.get("strategy") or {}
    rec_option = strategy.get("recommended_option") or {}
    cost = rec_option.get("cost") or 0
    if cost <= 0:
        cost = 3000.0
    original_net_cents = int(cost * 100)

    exp_dt = _get_price_lock_expires_at(trip)
    contracts = CONTRACTS_STORE.get(agency_id, {})
    current_net_cents = original_net_cents
    supplier_name = rec_option.get("name") or "Primary Supplier Contract"

    if contracts:
        first_contract: dict = next(iter(contracts.values()), {})
        supplier_name = first_contract.get("supplier_name", supplier_name)
        rate_table = first_contract.get("rate_table", [])
        if rate_table and isinstance(rate_table, list) and len(rate_table) > 0:
            net_per_night = rate_table[0].get("net_rate_per_night", 250.0)
            current_net_cents = int(net_per_night * 100 * 5)

    gain_cents = max(0, original_net_cents - current_net_cents)
    gain_pct = round((gain_cents / original_net_cents) * 100.0, 2) if original_net_cents > 0 else 0.0
    rate_drop = gain_cents > 0

    return RateAuditResponse(
        ok=True,
        trip_id=trip_id,
        supplier_name=supplier_name,
        original_net_rate_cents=original_net_cents,
        current_net_rate_cents=current_net_cents,
        potential_margin_gain_cents=gain_cents,
        margin_gain_pct=gain_pct,
        rate_drop_detected=rate_drop,
        price_lock_expires_at=exp_dt.isoformat(),
    )


@router.post("/{trip_id}/re-lock", response_model=ReLockResponse)
async def re_lock_lower_rate(
    trip_id: str,
    body: ReLockRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """PREVIEW-ONLY re-lock computation (PA-06, 2026-09-06).

    Doctrine: simulated data must never mutate real state. The current rate
    source is simulated (first in-memory supplier contract row with hardcoded
    fallbacks), so the previous behavior — overwriting the live trip's
    ``strategy.recommended_option.cost`` and bumping the version — is removed.

    What this endpoint does now:
    1. Loads the agency-scoped trip (404 when missing/foreign).
    2. Enforces the REQUIRED optimistic-version guard (409 on stale version)
       and accepts the REQUIRED idempotency key (422 when absent) so the
       future real-source persist path inherits both guards.
    3. Computes exactly what WOULD change and returns it as a preview with
       ``effects: []``, ``provider_connected: false``, ``would_persist: false``
       and reason ``simulated_rate_source``. The trip record is never written
       and no audit event is logged (a ``price_lock_arbitrage_saved`` audit
       entry would claim a persist that did not happen).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    current_version = int(trip.get("version") or 1)

    # Optimistic locking guard (F-01) — mandatory since PA-06.
    if body.expected_version != current_version:
        raise HTTPException(
            status_code=409,
            detail=f"Conflict: trip version mismatch (expected {body.expected_version}, current {current_version}). Re-lock aborted to prevent race condition.",
        )

    strategy = trip.get("strategy") or {}
    rec_option = strategy.get("recommended_option") or {}

    cost = rec_option.get("cost") or 0
    if cost <= 0:
        cost = 3000.0
    prev_net_cents = int(cost * 100)
    new_net_cents = body.new_net_rate_cents
    margin_saved_cents = max(0, prev_net_cents - new_net_cents)

    now_iso = datetime.now(timezone.utc).isoformat()

    # PA-06: NO trip mutation, NO TripStore.save_trip, NO AuditStore write.
    # Replay note: because nothing is persisted, an idempotency-key re-entry
    # deterministically recomputes the identical preview; the key is accepted
    # (and required) so the future real-source path inherits replay protection.

    return ReLockResponse(
        ok=True,
        trip_id=trip_id,
        preview=True,
        previous_net_rate_cents=prev_net_cents,
        new_net_rate_cents=new_net_cents,
        margin_saved_cents=margin_saved_cents,
        updated_at=now_iso,
        version=current_version,
        reality_tier="deterministic_preview",
        provider_connected=False,
        effects=[],
        would_persist=False,
        not_persisted_reason="simulated_rate_source",
    )


# ---------------------------------------------------------------------------
# Post-booking fare-drop disposition (exploration topic 49, 2026-10-21)
#
# The sentinel above watches the PRE-booking quote window. Once a trip is
# booked, ``TicketPriceWatchAgent`` (post-booking branch) attaches
# ``fare_drop_signal`` when the live fare falls below the booked price. These
# endpoints let the advisor see the two practitioner options with numbers and
# record what they decided. Tracking-only: the system never reprices, never
# contacts the supplier, never moves money — the advisor does, and records it.
# ---------------------------------------------------------------------------


class FareDropDispositionUpdateRequest(BaseModel):
    new_state: str
    note: str = ""
    # Recorded outcome for REPRICED / UPGRADED: option chosen, client delta,
    # supplier reference, who executed it. Informational only — no money moves here.
    outcome: Optional[Dict[str, Any]] = None
    # Compare-and-set guard on the disposition itself (trips carry no version
    # counter; the resource's own state is the honest optimistic lock).
    expected_state: Optional[str] = None
    # Accepted for replay protection parity with ReLockRequest; a transition
    # re-sent after success is already rejected by the state machine (409).
    idempotency_key: str


class FareDropDispositionResponse(BaseModel):
    ok: bool = True
    trip_id: str
    signal: Dict[str, Any]
    disposition: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None
    options_unavailable_reason: Optional[str] = None
    observations: List[Dict[str, Any]] = []
    # Practitioner-framed client message, DRAFT_AWAITING_OPERATOR. Computed at
    # read time from verified options only; never sent by the system.
    traveler_draft: Optional[Dict[str, Any]] = None


def _fare_drop_options_for(trip: dict, signal: dict) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Compute options at read time so the numbers always carry a current basis label."""
    try:
        pct, source = fare_drop_disposition.resolve_trip_commission(trip)
        return (
            fare_drop_disposition.compute_fare_drop_options(
                booked_price=float(signal.get("booked_price") or 0),
                current_price=float(signal.get("current_price") or 0),
                commission_pct=pct,
                commission_source=source,
            ),
            None,
        )
    except (TypeError, ValueError) as exc:
        return None, str(exc)


def _fare_drop_response(trip_id: str, trip: dict, signal: dict, disposition: dict) -> FareDropDispositionResponse:
    from spine_api.services.inbox_projection import _derive_customer_name, resolve_trip_field

    options, reason = _fare_drop_options_for(trip, signal)
    observations = [o for o in (trip.get("price_observations") or []) if isinstance(o, dict)]
    traveler_name = _derive_customer_name(trip, trip_id) or None
    # The projection helper synthesizes "Client XXXXXX" when no real name is on
    # file; a draft must never be addressed to a fabricated placeholder.
    if traveler_name and traveler_name == f"Client {trip_id[-6:].upper()}":
        traveler_name = None
    draft = fare_drop_disposition.compose_traveler_draft(
        signal,
        options,
        traveler_name=traveler_name,
        destination=(resolve_trip_field(trip, "destination") or None),
    )
    return FareDropDispositionResponse(
        trip_id=trip_id,
        signal=signal,
        disposition=disposition,
        options=options,
        options_unavailable_reason=reason,
        observations=observations[-10:],
        traveler_draft=draft,
    )


@router.get("/{trip_id}/fare-drop/disposition", response_model=FareDropDispositionResponse)
def get_fare_drop_disposition(
    trip_id: str,
    agency_id: str = Depends(get_current_agency_id),
):
    """Operator view of a detected post-booking fare drop: signal, the two
    quantified options (with commission basis label), and the decision ledger.

    Read-only. A signal without a ledger yet is surfaced as ``DETECTED``
    without persisting anything; the first PATCH creates the ledger.
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    signal = trip.get("fare_drop_signal")
    if not isinstance(signal, dict) or not signal:
        raise HTTPException(status_code=404, detail="No fare-drop signal on this trip")
    disposition = dict(trip.get("fare_drop_disposition") or {})
    if not disposition or disposition.get("detection_marker") != signal.get("detection_marker"):
        disposition = fare_drop_disposition.new_disposition(str(signal.get("detection_marker") or ""))
    return _fare_drop_response(trip_id, trip, signal, disposition)


@router.patch("/{trip_id}/fare-drop/disposition", response_model=FareDropDispositionResponse)
def update_fare_drop_disposition(
    trip_id: str,
    body: FareDropDispositionUpdateRequest,
    agency_id: str = Depends(get_current_agency_id),
):
    """Advance the fare-drop decision one legal step (operator-entered).

    The advisor records what they presented and what the supplier and client
    then did. Illegal transitions, a stale ``expected_state``, or a decision
    state without its recorded outcome are rejected with 409. This endpoint
    moves a STATUS, never money (owner invariant).
    """
    trip = TripStore.get_trip_for_agency(trip_id, agency_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    signal = trip.get("fare_drop_signal")
    if not isinstance(signal, dict) or not signal:
        raise HTTPException(status_code=404, detail="No fare-drop signal on this trip")

    disposition = trip.get("fare_drop_disposition")
    marker = str(signal.get("detection_marker") or "")
    if not isinstance(disposition, dict) or disposition.get("detection_marker") != marker:
        # First decision on this signal (or the signal was re-detected at a new
        # booked price): start a fresh ledger for the current marker.
        disposition = fare_drop_disposition.new_disposition(marker)

    try:
        fare_drop_disposition.apply_transition(
            disposition,
            body.new_state,
            by=agency_id,
            note=body.note,
            outcome=body.outcome,
            expected_state=body.expected_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Targeted CAS persist (expected_updated_at guard inside the store): the
    # ledger is the only key written, so a supervisor appending price
    # observations between our read and write cannot be clobbered, and an
    # audit event is only recorded after the write actually landed.
    persisted = TripStore.update_trip_if_version(
        trip_id,
        {"fare_drop_disposition": disposition},
        expected_updated_at=(trip.get("updated_at") or None),
    )
    if persisted is None:
        raise HTTPException(status_code=409, detail="Trip changed concurrently; retry the transition")
    trip = persisted
    AuditStore.log_event(
        event_type="fare_drop_disposition_updated",
        user_id=agency_id,
        details={
            "trip_id": trip_id,
            "detection_marker": marker,
            "new_state": body.new_state,
            "idempotency_key": body.idempotency_key,
            # Causal linkage (topic 51a gap 2): the marker IS the causal
            # identity of the detection that caused this decision — resolvable
            # via the trip's fare_drop_signal/price_observations records.
            # (The detection agent's own audit event id will be added when
            # signal attachment emits one; the marker remains stable either way.)
            "caused_by_marker": marker,
        },
    )
    return _fare_drop_response(trip_id, trip, signal, disposition)
