"""
spine_api/services/commission_reconciliation.py — IC Advisor Commission Ledger & Payout Portal Service (IDEA-131).

Manages per-advisor commission ledgers, split percentage tiers (70/30, 80/20, 90/10),
calculates monthly cleared payouts, and processes payout authorizations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic import BaseModel, Field

# In-memory advisor payout ledger store
ADVISOR_LEDGERS: Dict[str, Dict[str, Any]] = {}


class AdvisorPayoutLedger(BaseModel):
    advisor_id: str
    advisor_name: str
    split_tier_pct: float = 80.0
    gross_sales_cents: int
    total_commission_earned_cents: int
    pending_payout_cents: int
    cleared_payout_cents: int
    payout_history: List[Dict[str, Any]] = Field(default_factory=list)


def get_or_create_advisor_ledger(advisor_id: str, advisor_name: str = "Independent Advisor") -> AdvisorPayoutLedger:
    """Retrieve or initialize advisor commission payout ledger."""
    if advisor_id not in ADVISOR_LEDGERS:
        now_iso = datetime.now(timezone.utc).isoformat()
        ADVISOR_LEDGERS[advisor_id] = {
            "advisor_id": advisor_id,
            "advisor_name": advisor_name,
            "split_tier_pct": 80.0,
            "gross_sales_cents": 2500000,  # $25,000 baseline sales
            "total_commission_earned_cents": 200000,  # $2,000 earned (80% of $2,500)
            "pending_payout_cents": 50000,  # $500 pending
            "cleared_payout_cents": 150000,  # $1,500 cleared
            "payout_history": [
                {
                    "payout_id": f"pay_{advisor_id[:6]}_01",
                    "amount_cents": 150000,
                    "cleared_at": now_iso,
                    "method": "DIRECT_DEPOSIT",
                }
            ],
        }

    return AdvisorPayoutLedger(**ADVISOR_LEDGERS[advisor_id])


def process_advisor_payout_authorization(advisor_id: str, amount_cents: int, method: str = "DIRECT_DEPOSIT") -> AdvisorPayoutLedger:
    """Authorize and clear pending commission payout to an independent contractor advisor."""
    ledger = get_or_create_advisor_ledger(advisor_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    clear_amt = min(amount_cents, ledger.pending_payout_cents) if ledger.pending_payout_cents > 0 else amount_cents

    data = ADVISOR_LEDGERS[advisor_id]
    data["pending_payout_cents"] = max(0, data["pending_payout_cents"] - clear_amt)
    data["cleared_payout_cents"] += clear_amt
    data["payout_history"].append(
        {
            "payout_id": f"pay_{advisor_id[:6]}_{datetime.now().strftime('%M%S')}",
            "amount_cents": clear_amt,
            "cleared_at": now_iso,
            "method": method,
        }
    )

    return AdvisorPayoutLedger(**data)
