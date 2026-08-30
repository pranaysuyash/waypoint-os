import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


from src.fees.tax_compliance import (  # noqa: E402
    GSTTaxScheme,
    SourcingChannel,
    SourcingLineItem,
    TaxComplianceEngine,
)


def test_tcs_under_threshold_with_pan():
    """Verify 5% TCS on overseas travel when total remittance is under ₹7,00,000."""
    tcs = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=100000.0,
    )
    assert tcs.is_applicable is True
    assert tcs.pan_provided is True
    assert tcs.tier_5pct_taxable_amount_inr == 300000.0
    assert tcs.tier_5pct_tcs_amount_inr == 15000.0  # 5% of 3L
    assert tcs.tier_20pct_tcs_amount_inr == 0.0
    assert tcs.total_tcs_amount_inr == 15000.0
    assert tcs.effective_tcs_rate_pct == 5.0


def test_tcs_crossing_threshold():
    """Verify tiered split (5% on portion up to 7L, 20% on portion exceeding 7L)."""
    # Prior spend = 5,00,000. Current tx = 4,00,000 (total = 9,00,000).
    # Remaining in 5% tier = 2,00,000 -> TCS = 10,000
    # Spilling into 20% tier = 2,00,000 -> TCS = 40,000
    # Total TCS = 50,000
    tcs = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=400000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=500000.0,
    )
    assert tcs.is_applicable is True
    assert tcs.tier_5pct_taxable_amount_inr == 200000.0
    assert tcs.tier_5pct_tcs_amount_inr == 10000.0
    assert tcs.tier_20pct_taxable_amount_inr == 200000.0
    assert tcs.tier_20pct_tcs_amount_inr == 40000.0
    assert tcs.total_tcs_amount_inr == 50000.0
    assert tcs.effective_tcs_rate_pct == 12.5


def test_tcs_non_pan_penalty():
    """Verify 20% flat withholding when valid PAN is not furnished."""
    tcs = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=200000.0,
        is_overseas_trip=True,
        pan_number=None,
    )
    assert tcs.is_applicable is True
    assert tcs.pan_provided is False
    assert tcs.total_tcs_amount_inr == 40000.0  # 20% of 2L
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
    # TCS (5% on 303,450) = 15,172.50.
    # Grand total = 318,622.50.
    assert invoice.total_supplier_net_inr == 255000.0
    assert invoice.total_agency_margin_inr == 34000.0
    assert invoice.gross_package_price_inr == 289000.0
    assert invoice.total_gst_inr == 14450.0
    assert invoice.total_tcs_inr == 15172.50
    assert invoice.grand_total_payable_inr == 318622.50


def test_tax_compliance_api_endpoints(session_client):
    """Verify REST API endpoints for TCS, GST, and invoice compilation."""
    headers = {"X-Agency-ID": "agency_tax_test"}

    # Test TCS Endpoint
    tcs_resp = session_client.post(
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
    assert tcs_resp.json()["total_tcs_amount_inr"] == 25000.0

    # Test GST Endpoint
    gst_resp = session_client.post(
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
    inv_resp = session_client.post(
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
