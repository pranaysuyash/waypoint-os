"""
spine_api/services/commission_reconciliation.py — IC Advisor Commission Ledger & Payout Portal Service (IDEA-131).

Manages per-advisor commission ledgers, split percentage tiers (70/30, 80/20, 90/10),
calculates monthly cleared payouts, and processes payout authorizations.

PA-23 honesty notes (wave 1):
- The ledger aggregates are IN-MEMORY and labeled as such on every response
  (``reality_tier="deterministic_preview"``, ``provider_connected=False``,
  ``storage_backend="in_memory_preview"``, ``durable=False``).
- The legacy fake-seeded balances ($25,000 sales / $2,000 commission / $1,500
  cleared) are gated to non-production environments only.
- Payout ids are ``uuid4``-derived (collision-resistant) instead of
  clock-derived ``%M%S`` strings.

PA-23 wave 2 (2026-09-07) — durable SQL payout ledger + settlement reconciliation:
- Payout movements write through ``spine_api.services.advisor_payout_store``.
  When the SQL backend is selected (production default; explicit env override),
  the ledger is durable (``storage_backend="sql"``, ``durable=True``) and
  starts at true zero — the fabricated seed NEVER reaches the SQL ledger.
- ``reconcile_trip_commission`` links booking totals to the payout ledger:
  expected advisor commission (module-documented math: 10% agency commission
  pool x advisor split tier) vs recorded payouts for the trip. A mismatch is
  REPORTED, never auto-fixed.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from spine_api.services.advisor_payout_store import AdvisorPayoutStore

# In-memory advisor payout ledger store (aggregate preview; memory backend)
ADVISOR_LEDGERS: Dict[str, Dict[str, Any]] = {}

_NON_PRODUCTION_ENVIRONMENTS_EXCLUDED = frozenset({"production", "prod"})

# Module-documented settlement math (matches the seeded ledger baseline:
# $25,000 sales -> $2,500 commission pool (10%) -> $2,000 advisor share (80% split)).
AGENCY_COMMISSION_RATE = 0.10
DEFAULT_ADVISOR_SPLIT_PCT = 80.0

# Reconciliation tolerance: sub-cent rounding differences are not mismatches.
_RECONCILIATION_TOLERANCE_USD = 0.01


def _seed_demo_balances_enabled() -> bool:
    """PA-23: seed the legacy demo balances only outside production.

    Mirrors the ENVIRONMENT conventions used by spine_api/core/startup_assertions.py
    and the TripStore facade: production/prod never receives the fabricated
    seed balances; development/test/staging (or unset) do, so existing local
    demo flows keep working.
    """
    environment = os.environ.get("ENVIRONMENT", "development").strip().lower()
    return environment not in _NON_PRODUCTION_ENVIRONMENTS_EXCLUDED


def _sql_ledger_enabled() -> bool:
    from spine_api.services.advisor_payout_store import backend

    return backend() == "sql"


class AdvisorPayoutLedger(BaseModel):
    advisor_id: str
    advisor_name: str
    split_tier_pct: float = 80.0
    gross_sales_cents: int
    total_commission_earned_cents: int
    pending_payout_cents: int
    cleared_payout_cents: int
    payout_history: List[Dict[str, Any]] = Field(default_factory=list)
    # PA-23: truthful provenance metadata on every ledger response.
    reality_tier: str = "deterministic_preview"
    provider_connected: bool = False
    storage_backend: str = "in_memory_preview"
    durable: bool = False


def _memory_ledger(advisor_id: str, advisor_name: str) -> AdvisorPayoutLedger:
    """Memory backend ledger (PA-23 wave-1 behavior, preserved)."""
    if advisor_id not in ADVISOR_LEDGERS:
        now_iso = datetime.now(timezone.utc).isoformat()
        if _seed_demo_balances_enabled():
            # Non-production only: legacy demo baseline balances.
            seed = {
                "gross_sales_cents": 2500000,  # $25,000 baseline sales
                "total_commission_earned_cents": 200000,  # $2,000 earned (80% of $2,500)
                "pending_payout_cents": 50000,  # $500 pending
                "cleared_payout_cents": 150000,  # $1,500 cleared
                "payout_history": [
                    {
                        "payout_id": f"pay_{uuid4().hex[:12]}",
                        "amount_cents": 150000,
                        "cleared_at": now_iso,
                        "method": "DIRECT_DEPOSIT",
                    }
                ],
            }
        else:
            # Production starts at real zero — no fabricated money.
            seed = {
                "gross_sales_cents": 0,
                "total_commission_earned_cents": 0,
                "pending_payout_cents": 0,
                "cleared_payout_cents": 0,
                "payout_history": [],
            }
        ADVISOR_LEDGERS[advisor_id] = {
            "advisor_id": advisor_id,
            "advisor_name": advisor_name,
            "split_tier_pct": 80.0,
            **seed,
        }

    return AdvisorPayoutLedger(**ADVISOR_LEDGERS[advisor_id])


def _store_history_to_ledger_entries(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "payout_id": row["payout_id"],
            "amount_cents": int(round(row["amount_usd"] * 100)),
            "cleared_at": row.get("created_at"),
            "method": row.get("method") or "DIRECT_DEPOSIT",
            "trip_id": row.get("trip_id"),
            "authority_approval_id": row.get("authority_approval_id"),
        }
        for row in rows
    ]


def _sql_ledger(advisor_id: str, advisor_name: str, agency_id: str) -> AdvisorPayoutLedger:
    """SQL backend ledger: aggregates start at true zero — never seeded; the
    cleared balance is the sum of durably recorded payouts."""
    rows = AdvisorPayoutStore.list_payouts(agency_id=agency_id, advisor_id=advisor_id, status=None)
    recorded_rows = [r for r in rows if r["status"] == "recorded"]
    cleared_cents = sum(int(round(r["amount_usd"] * 100)) for r in recorded_rows)
    return AdvisorPayoutLedger(
        advisor_id=advisor_id,
        advisor_name=advisor_name,
        split_tier_pct=80.0,
        gross_sales_cents=0,
        total_commission_earned_cents=0,
        pending_payout_cents=0,
        cleared_payout_cents=cleared_cents,
        payout_history=_store_history_to_ledger_entries(rows),
        reality_tier="deterministic_preview",
        provider_connected=False,
        storage_backend="sql",
        durable=True,
    )


def get_or_create_advisor_ledger(
    advisor_id: str,
    advisor_name: str = "Independent Advisor",
    agency_id: Optional[str] = None,
) -> AdvisorPayoutLedger:
    """Retrieve or initialize advisor commission payout ledger."""
    if _sql_ledger_enabled():
        from spine_api.persistence import TEST_AGENCY_ID

        return _sql_ledger(advisor_id, advisor_name, agency_id or TEST_AGENCY_ID)
    return _memory_ledger(advisor_id, advisor_name)


def process_advisor_payout_authorization(
    advisor_id: str,
    amount_cents: int,
    method: str = "DIRECT_DEPOSIT",
    *,
    agency_id: Optional[str] = None,
    recorded_by: Optional[str] = None,
    trip_id: Optional[str] = None,
    note: Optional[str] = None,
    authority_approval_id: Optional[str] = None,
) -> AdvisorPayoutLedger:
    """Authorize and clear pending commission payout to an independent contractor advisor.

    PA-23 wave 2: the movement is durably recorded through the payout store
    (SQL when the SQL backend is active; memory otherwise). ``trip_id`` links
    the payout to a booking for settlement reconciliation;
    ``authority_approval_id`` records the ratified dual-control approval that
    authorized an over-cap payout (PA-08).
    """
    if _sql_ledger_enabled():
        from spine_api.persistence import TEST_AGENCY_ID

        record = AdvisorPayoutStore.record_payout(
            agency_id=agency_id or TEST_AGENCY_ID,
            advisor_id=advisor_id,
            amount_usd=round(amount_cents / 100.0, 2),
            recorded_by=recorded_by or "system",
            method=method,
            trip_id=trip_id,
            authority_approval_id=authority_approval_id,
            note=note,
        )
        ledger = _sql_ledger(advisor_id, "Independent Advisor", record["agency_id"])
        return ledger

    ledger = get_or_create_advisor_ledger(advisor_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    clear_amt = min(amount_cents, ledger.pending_payout_cents) if ledger.pending_payout_cents > 0 else amount_cents

    data = ADVISOR_LEDGERS[advisor_id]
    data["pending_payout_cents"] = max(0, data["pending_payout_cents"] - clear_amt)
    data["cleared_payout_cents"] += clear_amt
    data["payout_history"].append(
        {
            # PA-23: uuid-derived id — the previous clock-derived
            # f"%M%S" suffix collided for payouts in the same minute.
            "payout_id": f"pay_{uuid4().hex[:12]}",
            "amount_cents": clear_amt,
            "cleared_at": now_iso,
            "method": method,
            "trip_id": trip_id,
            "authority_approval_id": authority_approval_id,
        }
    )
    # Mirror the movement into the payout store so trip-linked reconciliation
    # (reconcile_trip_commission) sees memory-backend payouts too.
    AdvisorPayoutStore.record_payout(
        agency_id=agency_id or "system",
        advisor_id=advisor_id,
        amount_usd=round(clear_amt / 100.0, 2),
        recorded_by=recorded_by or "system",
        method=method,
        trip_id=trip_id,
        authority_approval_id=authority_approval_id,
        note=note,
    )

    return AdvisorPayoutLedger(**data)


def reconcile_trip_commission(trip_id: str, agency_id: str) -> Dict[str, Any]:
    """Reconcile a trip's booking total against recorded advisor payouts (PA-23).

    Expected advisor commission uses the module-documented math:
    ``total_charged_usd * AGENCY_COMMISSION_RATE * (split_tier_pct / 100)``
    (10% commission pool x 80% advisor split = 8% of the charged total).

    Returns ``{trip_id, agency_id, expected_usd, recorded_usd, delta_usd,
    status}`` where status is one of ``matched`` | ``mismatch`` |
    ``no_booking`` | ``no_payouts``. A mismatch is REPORTED, never auto-fixed.
    """
    from spine_api.persistence import TripStore

    result: Dict[str, Any] = {
        "trip_id": trip_id,
        "agency_id": agency_id,
        "expected_usd": 0.0,
        "recorded_usd": 0.0,
        "delta_usd": 0.0,
        "status": "no_booking",
    }

    trip = TripStore.get_trip(trip_id)
    if not trip:
        result["reason"] = f"Trip '{trip_id}' not found."
        return result
    trip_agency = str(trip.get("agency_id") or "")
    if trip_agency and trip_agency != agency_id:
        result["reason"] = f"Trip belongs to agency '{trip_agency}', not '{agency_id}'."
        return result

    booking = trip.get("booking_confirmation") or {}
    total_charged_usd = booking.get("total_charged_usd")
    if total_charged_usd is None or float(total_charged_usd) <= 0:
        result["reason"] = "Trip has no confirmed booking total (booking_confirmation.total_charged_usd)."
        return result

    expected_usd = round(
        float(total_charged_usd) * AGENCY_COMMISSION_RATE * (DEFAULT_ADVISOR_SPLIT_PCT / 100.0), 2
    )
    payouts = AdvisorPayoutStore.list_payouts(
        agency_id=agency_id, trip_id=trip_id, status="recorded"
    )
    recorded_usd = round(sum(float(p["amount_usd"]) for p in payouts), 2)
    delta_usd = round(recorded_usd - expected_usd, 2)

    result.update(
        {
            "expected_usd": expected_usd,
            "recorded_usd": recorded_usd,
            "delta_usd": delta_usd,
            "booking_total_usd": round(float(total_charged_usd), 2),
            "payout_count": len(payouts),
            "math": (
                f"expected = total_charged_usd * {AGENCY_COMMISSION_RATE} commission pool "
                f"x {DEFAULT_ADVISOR_SPLIT_PCT}% advisor split"
            ),
        }
    )
    if not payouts:
        result["status"] = "no_payouts"
        result["reason"] = "No recorded payouts are linked to this trip."
    elif abs(delta_usd) <= _RECONCILIATION_TOLERANCE_USD:
        result["status"] = "matched"
    else:
        result["status"] = "mismatch"
        result["reason"] = (
            "Recorded payouts differ from the expected advisor commission. "
            "Reported for operator review — never auto-fixed."
        )
    return result
