"""
tests/test_pa_payout_ledger_honesty.py — PA-23: payout ledger honesty.

Before PA-23 the commission payout ledger used clock-derived collision-prone
payout ids (``%M%S``), always seeded fabricated balances ($25k sales / $2k
commission) regardless of environment, and presented in-memory state without
any provenance metadata.
"""

import pytest

from spine_api.services import commission_reconciliation as cr


@pytest.fixture(autouse=True)
def _isolated_ledger(monkeypatch):
    monkeypatch.delenv("TRIPSTORE_BACKEND", raising=False)
    monkeypatch.setattr(cr, "ADVISOR_LEDGERS", {})
    yield
    cr.ADVISOR_LEDGERS.clear()


def test_payout_ids_are_unique_within_the_same_minute():
    """The old clock-derived f"%M%S" ids collided for payouts in the same
    minute; uuid-derived ids must not."""
    first = cr.process_advisor_payout_authorization("adv_ids_1", 1000)
    second = cr.process_advisor_payout_authorization("adv_ids_1", 1000)
    first_id = first.payout_history[-1]["payout_id"]
    second_id = second.payout_history[-1]["payout_id"]
    assert first_id != second_id
    assert first_id.startswith("pay_")
    assert second_id.startswith("pay_")


def test_seed_balances_present_outside_production(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=None)
    ledger = cr.get_or_create_advisor_ledger("adv_seed_dev")
    assert ledger.gross_sales_cents == 2500000
    assert ledger.cleared_payout_cents == 150000


@pytest.mark.parametrize("production_env", ["production", "prod"])
def test_production_starts_at_zero_no_fabricated_seed(monkeypatch, production_env):
    """PA-23: production must never present the fake-seeded money.

    FND-0290: production-mode durable ledger access is agency-attributed —
    the call now passes an explicit agency_id instead of relying on the
    removed TEST_AGENCY_ID fallback. _sql_ledger is read-only, so a fresh
    advisor id yields true zero balances with no fabricated seed.
    """
    monkeypatch.setenv("ENVIRONMENT", production_env)
    ledger = cr.get_or_create_advisor_ledger(
        f"adv_seed_{production_env}", agency_id="agency_ledger_honesty"
    )
    assert ledger.gross_sales_cents == 0
    assert ledger.total_commission_earned_cents == 0
    assert ledger.pending_payout_cents == 0
    assert ledger.cleared_payout_cents == 0
    assert ledger.payout_history == []


def test_ledger_response_carries_truthful_provenance_metadata():
    ledger = cr.get_or_create_advisor_ledger("adv_meta_1")
    assert ledger.reality_tier == "deterministic_preview"
    assert ledger.provider_connected is False
    assert ledger.storage_backend == "in_memory_preview"
    assert ledger.durable is False
