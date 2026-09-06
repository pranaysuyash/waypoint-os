"""
Financial Settlement & Virtual Card Engine Tests (PER-FIN, FIN-01..12).
"""

from datetime import date, timedelta
from src.fees.settlement_engine import FinancialSettlementEngine
from spine_api.routers.financial_settlement import (
    FXQuoteRequest,
    IssueVCCRequest,
    PaymentScheduleRequest,
    calculate_fx_quote,
    build_payment_schedule,
    issue_virtual_credit_card,
)


def test_fx_quote_with_volatility_buffer():
    # Base: 1,000 USD to EUR at raw rate 0.92 with 2% buffer
    # Buffered rate = 0.92 * 1.02 = 0.9384
    # Quoted = 1000 * 0.9384 = 938.40 EUR
    # Gateway fee = 938.40 * 0.029 + 0.30 = 27.21 + 0.30 = 27.51 EUR
    # Net settled = 938.40 - 27.51 = 910.89 EUR
    quote = FinancialSettlementEngine.calculate_fx_quote(
        base_amount=1000.0,
        from_currency="USD",
        to_currency="EUR",
        raw_exchange_rate=0.92,
        volatility_buffer_pct=2.0,
    )
    assert quote["customer_quoted_total"] == 938.40
    assert quote["buffered_exchange_rate"] == 0.9384
    assert quote["net_settled_amount"] > 900.0
    assert quote["fx_cushion_amount"] == 18.40


def test_issue_supplier_vcc():
    vcc = FinancialSettlementEngine.issue_supplier_vcc(
        trip_id="TRIP-441",
        supplier_name="Four Seasons George V",
        authorized_amount=4500.0,
        currency="EUR",
    )
    assert vcc.card_id.startswith("VCC-")
    assert vcc.currency == "EUR"
    assert vcc.authorized_amount == 4500.0
    assert "XXXX" in vcc.card_number_masked
    assert vcc.status == "ACTIVE"


def test_staged_payment_schedule():
    dep_date = date.today() + timedelta(days=90)
    schedule = FinancialSettlementEngine.build_payment_schedule(
        total_amount=5000.0,
        currency="USD",
        departure_date=dep_date,
        deposit_pct=20.0,
        balance_due_days_prior=45,
    )
    assert len(schedule) == 2
    assert schedule[0].amount == 1000.0  # 20%
    assert schedule[1].amount == 4000.0  # 80%


def test_commission_split_calculation():
    split = FinancialSettlementEngine.calculate_commission_split(
        gross_commission=1000.0,
        contractor_split_pct=70.0,
    )
    assert split["contractor_payout"] == 700.0
    assert split["host_agency_payout"] == 300.0


def _assert_preview_envelope(response: dict, *, status: str) -> None:
    assert response["status"] == status
    assert response["reality_tier"] == "deterministic_preview"
    assert response["provider_connected"] is False
    assert response["external_reference"] is None
    assert response["effects"] == []
    assert response["metadata"]["source"] == "local_deterministic_preview"
    assert response["metadata"]["simulation"] is True
    assert response["metadata"]["external_action"] is False
    assert response["metadata"]["operational_write"] is False


def test_settlement_fx_route_preserves_arithmetic_as_computed_preview() -> None:
    response = calculate_fx_quote(
        FXQuoteRequest(
            base_amount=1000.0,
            from_currency="USD",
            to_currency="EUR",
            raw_exchange_rate=0.92,
        )
    )

    _assert_preview_envelope(response, status="COMPUTED_PREVIEW")
    assert response["customer_quoted_total"] == 938.40
    assert response["net_settled_amount"] > 900.0


def test_vcc_route_is_non_operational_and_does_not_call_card_generator(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("VCC preview must not generate a card object")

    monkeypatch.setattr(FinancialSettlementEngine, "issue_supplier_vcc", fail_if_called)
    response = issue_virtual_credit_card(
        IssueVCCRequest(
            trip_id="TRIP-VCC-PREVIEW",
            supplier_name="Sample Supplier",
            authorized_amount=4500.0,
            currency="EUR",
        )
    )

    _assert_preview_envelope(response, status="PREVIEW_ONLY")
    assert response["issuance_status"] == "NOT_ISSUED"
    assert response["virtual_card"] is None
    assert response["requested_amount"] == 4500.0
    assert response["requested_currency"] == "EUR"
    assert "credential" in response["notice"].lower()
    assert all(key not in response for key in ("card_id", "card_number_masked", "cvv"))


def test_schedule_route_is_computed_preview_not_scheduled_invoice() -> None:
    response = build_payment_schedule(
        PaymentScheduleRequest(
            total_amount=5000.0,
            currency="USD",
            departure_date=date.today() + timedelta(days=90),
        )
    )

    _assert_preview_envelope(response, status="COMPUTED_PREVIEW")
    assert len(response["milestones"]) == 2
    assert response["milestones"][0]["amount"] == 1000.0
    assert response["milestones"][1]["amount"] == 4000.0
