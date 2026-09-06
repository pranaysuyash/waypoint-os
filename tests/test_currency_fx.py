"""
tests/test_currency_fx.py — Unit and router integration tests for dynamic FX slippage and fee netting.
"""

import os
import pytest

from src.fees.currency import CurrencyService

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_currency_conversion_with_slippage_and_gateway():
    """Verify EUR to USD conversion adding 2% FX buffer and 2.9% + $0.30 gateway fees."""
    # 1000 EUR in USD
    res = CurrencyService.convert_currency(
        amount_in_target=1000.0,
        target_currency="EUR",
        agency_base_currency="USD",
        custom_slippage_buffer_pct=0.02,
        gateway_fee_pct=0.029,
        gateway_fixed_fee=0.30,
    )

    # 1000 * 1.08 = $1,080 base unadjusted
    assert res.base_amount == 1080.0
    # 1080 * 1.02 = $1,101.60 with 2% buffer
    assert res.slippage_cost_base == 21.60
    # Gateway fee = (1101.60 * 0.029) + 0.30 = 31.95 + 0.30 = $32.25
    assert res.payment_gateway_fee_base == 32.25
    # Total cost = 1101.60 + 32.25 = $1,133.85
    assert res.total_cost_in_base_currency == 1133.85


def test_currency_conversion_api_endpoint(session_client):
    """Verify POST /api/v1/financial-ops/convert-currency endpoint."""
    res = session_client.post(
        "/api/v1/financial-ops/convert-currency",
        json={
            "amount_in_target": 500.0,
            "target_currency": "EUR",
            "agency_base_currency": "USD",
            "custom_slippage_buffer_pct": 0.02,
        },
        headers={"X-Agency-ID": "agency_fx_test"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["target_currency"] == "EUR"
    assert data["base_currency"] == "USD"
    assert data["base_amount"] == 540.0
    assert data["total_cost_in_base_currency"] > 540.0
    assert data["status"] == "COMPUTED_PREVIEW"
    assert data["reality_tier"] == "deterministic_preview"
    assert data["provider_connected"] is False
    assert data["external_reference"] is None
    assert data["effects"] == []
    assert data["metadata"]["source"] == "local_deterministic_preview"
    assert data["metadata"]["operational_write"] is False
