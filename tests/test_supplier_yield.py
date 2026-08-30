"""Tests for supplier yield arbitrage and advisor commission ledger.

The commission-reconciliation service was refactored from an older
`reconcile_commission_ledger` interface to a per-advisor ledger API
(`AdvisorPayoutLedger`, `get_or_create_advisor_ledger`,
`process_advisor_payout_authorization`). These tests exercise the current
contract while preserving the original intent: rank supplier quotes by yield,
and verify advisor commission-clearing behavior.
"""

from datetime import date

from spine_api.services.supplier_yield import (
    SupplierQuote,
    YieldArbitrageReport,
    evaluate_supplier_yield_arbitrage,
)
from spine_api.services.commission_reconciliation import (
    get_or_create_advisor_ledger,
    process_advisor_payout_authorization,
)


def test_supplier_yield_arbitrage_ranking():
    quotes = [
        SupplierQuote(
            supplier_name="AmadeusGDS",
            rate_plan_name="Standard GDS Rate",
            net_cost_usd=1000.0,
            client_retail_price_usd=1100.0,
            commission_rate=0.10,
            cancellation_flexibility_score=0.9,
        ),
        SupplierQuote(
            supplier_name="Hotelbeds",
            rate_plan_name="Direct Wholesale Net",
            net_cost_usd=820.0,
            client_retail_price_usd=1100.0,
            commission_rate=0.25,
            cancellation_flexibility_score=0.8,
        ),
        SupplierQuote(
            supplier_name="ExpediaTAAP",
            rate_plan_name="Expedia Premium Margin",
            net_cost_usd=900.0,
            client_retail_price_usd=1100.0,
            commission_rate=0.18,
            cancellation_flexibility_score=0.5,
        ),
    ]

    report: YieldArbitrageReport = evaluate_supplier_yield_arbitrage(
        inventory_title="Grand Hotel Excelsior",
        destination="Rome",
        quotes=quotes,
    )

    assert report.quotes_evaluated_count == 3
    assert report.recommended_supplier == "Hotelbeds"
    assert report.max_margin_usd == 280.0
    assert report.items[0].is_recommended is True
    assert report.items[0].supplier_name == "Hotelbeds"


def test_advisor_commission_ledger_payout_clearing():
    # Create a fresh advisor ledger, then authorize clearing a pending payout.
    # The ledger initializes with a baseline $500 pending; clearing it moves
    # amount to cleared and reduces pending. This mirrors the old
    # "overdue detection" concern (unsettled commission) at the advisor level.
    advisor_id = f"adv_{date.today().strftime('%Y%m%d')}_payout"
    ledger = get_or_create_advisor_ledger(advisor_id, advisor_name="Independent Advisor")

    assert ledger.advisor_id == advisor_id
    assert ledger.split_tier_pct == 80.0
    assert ledger.total_commission_earned_cents == 200000
    assert ledger.pending_payout_cents == 50000

    # Authorize clearing the full pending amount.
    cleared = process_advisor_payout_authorization(advisor_id, 50000)

    assert cleared.pending_payout_cents == 0
    assert cleared.cleared_payout_cents == 200000  # 150000 baseline + 50000 cleared
    assert len(cleared.payout_history) >= 2
    assert cleared.payout_history[-1]["amount_cents"] == 50000
