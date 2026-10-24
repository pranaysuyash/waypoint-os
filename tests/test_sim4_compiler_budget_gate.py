"""
FND-0337 (Sim #4): the proposal compiler must judge its economics against the
customer's budget — a compile that never saw the budget could (and did) pass
"feasibility" at 2x the customer's number, and an INR budget vs USD components
must be REPORTED (BUDGET_CURRENCY_UNVERIFIED), never silently compared.
"""

from __future__ import annotations

from datetime import date

from src.orchestration.proposal_compiler import AutonomousProposalCompiler

ARGS = dict(
    trip_id="trip_0337",
    raw_intake_text="honeymoon in bali, 7 nights, private pool villa if possible.",
    destination="Bali",
    departure_date=date(2026, 12, 8),
    return_date=date(2026, 12, 15),
    traveler_count=2,
)


def _compile(**over):
    return AutonomousProposalCompiler.compile_from_intake(**ARGS, **over)


def test_no_budget_means_no_claim():
    pkg = _compile()
    assert pkg.budget_check["within_budget"] is None
    assert pkg.budget_check["basis"] == "no_budget_provided"


def test_over_budget_usd_is_flagged():
    # same currency (USD) as the component costs — bound is enforced
    pkg = _compile(budget_amount=100.0, budget_currency="USD")
    assert pkg.budget_check["within_budget"] is False
    assert pkg.budget_check["basis"] == "same_currency_comparison"
    assert pkg.budget_check["gross_customer_price_usd"] > 100.0


def test_within_budget_usd_passes():
    pkg = _compile(budget_amount=1_000_000.0, budget_currency="USD")
    assert pkg.budget_check["within_budget"] is True


def test_currency_mismatch_is_reported_not_compared():
    pkg = _compile(budget_amount=350000.0, budget_currency="INR")
    assert pkg.budget_check["within_budget"] is None
    assert pkg.budget_check["basis"] == "currency_unverified_reported"
    assert pkg.budget_check["component_currency"] == "USD"


def test_budget_violation_suppresses_feasibility_or_is_distinct():
    # The budget gate must be VISIBLE in the package either as a hard
    # violation (is_feasibility_passed False) or as budget_check within_budget
    # False — never silently absent.
    pkg = _compile(budget_amount=1.0, budget_currency="USD")
    seen = (
        pkg.budget_check["within_budget"] is False
        or not pkg.is_feasibility_passed
    )
    assert seen
