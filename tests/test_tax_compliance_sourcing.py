import os

import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    # /api/v1/tax-compliance routes are agency-scoped (PT-09: explicit
    # _auth_or_skip at the include site). These API tests exercise engine
    # behavior, not auth, and send no JWT — run with the dev auth bypass.
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")


from src.fees.tax_compliance import (  # noqa: E402
    GSTTaxScheme,
    SourcingChannel,
    SourcingLineItem,
    TaxComplianceEngine,
)


def test_tcs_under_threshold_with_pan():
    """Regime-explicit TCS (R2-C 2026-11-04): the historical 5%-up-to-₹7L
    behavior belongs to the budget2024 window and is pinned via ``as_of``;
    the default (today) is the current flat-2% regime."""
    from datetime import date

    # Historical window: 5% under ₹7L.
    tcs = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=100000.0,
        as_of=date(2025, 1, 15),
    )
    assert tcs.is_applicable is True
    assert tcs.pan_provided is True
    assert tcs.regime_name == "budget2024"
    assert tcs.tier_5pct_taxable_amount_inr == 300000.0
    assert tcs.tier_5pct_tcs_amount_inr == 15000.0  # 5% of 3L
    assert tcs.tier_20pct_tcs_amount_inr == 0.0
    assert tcs.total_tcs_amount_inr == 15000.0
    assert tcs.effective_tcs_rate_pct == 5.0

    # Current law (Budget 2026): flat 2% from the first rupee.
    tcs_now = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=100000.0,
    )
    assert tcs_now.regime_name == "budget2026"
    assert tcs_now.total_tcs_amount_inr == 6000.0
    assert tcs_now.effective_tcs_rate_pct == 2.0


def test_tcs_crossing_threshold():
    """Regime-explicit tiered split: 5% up to 7L, 20% above (budget2024)."""
    from datetime import date

    # Prior spend = 5,00,000. Current tx = 4,00,000 (total = 9,00,000).
    # Remaining in 5% tier = 2,00,000 -> TCS = 10,000
    # Spilling into 20% tier = 2,00,000 -> TCS = 40,000
    # Total TCS = 50,000
    tcs = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=400000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=500000.0,
        as_of=date(2025, 1, 15),
    )
    assert tcs.is_applicable is True
    assert tcs.regime_name == "budget2024"
    assert tcs.tier_5pct_taxable_amount_inr == 200000.0
    assert tcs.tier_5pct_tcs_amount_inr == 10000.0
    assert tcs.tier_20pct_taxable_amount_inr == 200000.0
    assert tcs.tier_20pct_tcs_amount_inr == 40000.0
    assert tcs.total_tcs_amount_inr == 50000.0
    assert tcs.effective_tcs_rate_pct == 12.5


def test_tcs_non_pan_penalty():
    """Regime-explicit no-PAN handling: budget2024/25 declare a statutory 20%
    penalty; the CURRENT budget2026 regime has no stated penalty in the
    fetched sources — standard rate + advisory note (never fabricated)."""
    from datetime import date

    tcs_legacy = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=200000.0,
        is_overseas_trip=True,
        pan_number=None,
        as_of=date(2025, 12, 1),
    )
    assert tcs_legacy.is_applicable is True
    assert tcs_legacy.pan_provided is False
    assert tcs_legacy.total_tcs_amount_inr == 40000.0  # 20% of 2L
    assert tcs_legacy.effective_tcs_rate_pct == 20.0

    tcs_now = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=200000.0,
        is_overseas_trip=True,
        pan_number=None,
    )
    assert tcs_now.regime_name == "budget2026"
    assert tcs_now.effective_tcs_rate_pct == 2.0
    assert tcs_now.total_tcs_amount_inr == 4000.0
    assert "verify" in tcs_now.no_pan_note.lower()


def test_tcs_malformed_pan_penalty():
    """Regime-explicit malformed-PAN handling (same policy as absent PAN)."""
    from datetime import date

    for bad_pan in ["ABCDEFGHIJ", "1234567890", "ABCDE12345", "ABC1234D", "ABCD12345E"]:
        tcs = TaxComplianceEngine.calculate_tcs(
            current_amount_inr=100000.0,
            is_overseas_trip=True,
            pan_number=bad_pan,
            as_of=date(2025, 1, 15),
        )
        assert tcs.is_applicable is True
        assert tcs.pan_provided is False
        assert tcs.total_tcs_amount_inr == 20000.0  # budget2024 statutory 20%
        assert tcs.effective_tcs_rate_pct == 20.0


def test_gst_tour_package_intra_state():
    """Verify 5% GST split into CGST (2.5%) + SGST (2.5%) for intra-state package."""
    gst = TaxComplianceEngine.calculate_gst(
        taxable_base_inr=100000.0,
        scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
        is_inter_state=False,
    )
    assert gst.gst_rate_pct == 5.0
    assert gst.cgst_amount_inr == 2500.0
    assert gst.sgst_amount_inr == 2500.0
    assert gst.igst_amount_inr == 0.0
    assert gst.total_gst_amount_inr == 5000.0
    assert gst.itc_eligible is False


def test_gst_service_fee_inter_state():
    """Verify 18% IGST with ITC eligibility on pure agency service margin."""
    gst = TaxComplianceEngine.calculate_gst(
        taxable_base_inr=20000.0,
        scheme=GSTTaxScheme.SERVICE_FEE_18PCT,
        is_inter_state=True,
    )
    assert gst.gst_rate_pct == 18.0
    assert gst.igst_amount_inr == 3600.0
    assert gst.total_gst_amount_inr == 3600.0
    assert gst.itc_eligible is True


def test_commercial_invoice_compilation():
    """Verify end-to-end commercial invoice compilation with sourcing line items."""
    items = [
        SourcingLineItem(
            item_id="flight_01",
            service_type="flight",
            title="BOM to FCO Emirates",
            supplier_name="Emirates GDS",
            sourcing_channel=SourcingChannel.GDS_SABRE,
            currency="USD",
            supplier_net_amount=1000.0,
            fx_rate_to_inr=85.0,
            supplier_net_inr=0.0,
            agency_markup_pct=10.0,
            agency_markup_inr=0.0,
            gross_client_price_inr=0.0,
            gst_scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
        ),
        SourcingLineItem(
            item_id="hotel_01",
            service_type="hotel",
            title="Rome Cavalieri Waldorf",
            supplier_name="Hotelbeds",
            sourcing_channel=SourcingChannel.BEDBANK_HOTELBEDS,
            currency="USD",
            supplier_net_amount=2000.0,
            fx_rate_to_inr=85.0,
            supplier_net_inr=0.0,
            agency_markup_pct=15.0,
            agency_markup_inr=0.0,
            gross_client_price_inr=0.0,
            gst_scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
        ),
    ]

    invoice = TaxComplianceEngine.compile_commercial_invoice(
        trip_id="trip_invoice_1",
        line_items=items,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=0.0,
        is_inter_state=True,
    )

    # Flight: Net = 85,000, Markup = 8,500 -> Gross = 93,500. GST (5%) = 4,675
    # Hotel: Net = 170,000, Markup = 25,500 -> Gross = 195,500. GST (5%) = 9,775
    # Total Gross = 289,000. Total GST = 14,450.
    # Package before TCS = 303,450.
    # TCS (current budget2026 regime: flat 2% on 303,450) = 6,069.00.
    # Grand total = 309,519.00. (Historical 5% figures pinned regime-explicitly
    # in test_tax_compliance_effective_dated.py.)
    assert invoice.total_supplier_net_inr == 255000.0
    assert invoice.total_agency_margin_inr == 34000.0
    assert invoice.gross_package_price_inr == 289000.0
    assert invoice.total_gst_inr == 14450.0
    assert invoice.total_tcs_inr == 6069.0
    assert invoice.grand_total_payable_inr == 309519.0


def test_tax_compliance_api_endpoints():
    """Verify REST API endpoints for TCS, GST, and invoice compilation."""
    from fastapi.testclient import TestClient
    from spine_api.server import app

    headers = {"X-Agency-ID": "agency_tax_test"}
    with TestClient(app) as test_c:
        # Test TCS Endpoint
        tcs_resp = test_c.post(
            "/api/v1/tax-compliance/calculate-tcs",
            json={
                "current_amount_inr": 500000.0,
                "is_overseas_trip": True,
                "pan_number": "ABCDE1234F",
                "cumulative_fy_spend_inr": 0.0,
            },
            headers=headers,
        )
        assert tcs_resp.status_code == 200
        # Current budget2026 regime: flat 2% (500,000 × 2%).
        assert tcs_resp.json()["total_tcs_amount_inr"] == 10000.0

        # Test GST Endpoint
        gst_resp = test_c.post(
            "/api/v1/tax-compliance/calculate-gst",
            json={
                "taxable_base_inr": 50000.0,
                "scheme": "SERVICE_FEE_18PCT",
                "is_inter_state": True,
            },
            headers=headers,
        )
        assert gst_resp.status_code == 200
        assert gst_resp.json()["total_gst_amount_inr"] == 9000.0

        # Test Invoice Compilation Endpoint
        inv_resp = test_c.post(
            "/api/v1/tax-compliance/compile-invoice",
            json={
                "trip_id": "trip_api_test",
                "line_items": [
                    {
                        "item_id": "item_1",
                        "service_type": "transfer",
                        "title": "VIP Airport Chauffeur",
                        "supplier_name": "Rome Chauffeurs",
                        "sourcing_channel": "DIRECT_DMC",
                        "currency": "USD",
                        "supplier_net_amount": 200.0,
                        "fx_rate_to_inr": 85.0,
                        "agency_markup_pct": 20.0,
                        "gst_scheme": "TOUR_PACKAGE_5PCT",
                    }
                ],
                "is_overseas_trip": True,
                "pan_number": "ABCDE1234F",
            },
            headers=headers,
        )
        assert inv_resp.status_code == 200
        data = inv_resp.json()
        assert data["trip_id"] == "trip_api_test"
        assert data["item_count"] == 1
        assert data["grand_total_payable_inr"] > 0
