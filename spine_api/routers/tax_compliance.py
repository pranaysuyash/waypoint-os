"""
spine_api/routers/tax_compliance.py — Statutory Indian Tax (TCS/GST) & Sourcing Cost Ledger Router (Gap #01, #04, #15).

Provides endpoints to:
1. Calculate statutory TCS liability under Section 206C(1G) LRS thresholds (5% / 20%).
2. Calculate GST under Tour Package (5%) or Service Fee (18%) schemes with state split.
3. Compile itemized commercial invoices with supplier net costs, markups, and tax liabilities.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.fees.tax_compliance import (
    GSTTaxScheme,
    SourcingChannel,
    SourcingLineItem,
    TaxComplianceEngine,
)

router = APIRouter(prefix="/api/v1/tax-compliance", tags=["Tax Compliance & Sourcing Ledger"])


class TCSCalculationRequest(BaseModel):
    current_amount_inr: float = Field(..., gt=0, description="Transaction invoice amount in INR")
    is_overseas_trip: bool = Field(True, description="Whether this is an outbound international trip")
    pan_number: Optional[str] = Field(None, description="10-character traveler PAN")
    cumulative_fy_spend_inr: float = Field(0.0, ge=0, description="Prior remittances in current financial year")


class GSTCalculationRequest(BaseModel):
    taxable_base_inr: float = Field(..., gt=0, description="Taxable base in INR")
    scheme: GSTTaxScheme = Field(GSTTaxScheme.TOUR_PACKAGE_5PCT, description="GST tax scheme")
    is_inter_state: bool = Field(False, description="Whether transaction crosses state boundaries (IGST vs CGST/SGST)")


class SourcingItemPayload(BaseModel):
    item_id: str
    service_type: str
    title: str
    supplier_name: str
    sourcing_channel: SourcingChannel = SourcingChannel.DIRECT_DMC
    currency: str = "USD"
    supplier_net_amount: float
    fx_rate_to_inr: float = 85.0
    agency_markup_pct: float = 15.0
    gst_scheme: GSTTaxScheme = GSTTaxScheme.TOUR_PACKAGE_5PCT


class CommercialInvoiceRequest(BaseModel):
    trip_id: str
    line_items: List[SourcingItemPayload]
    is_overseas_trip: bool = True
    pan_number: Optional[str] = None
    cumulative_fy_spend_inr: float = 0.0
    is_inter_state: bool = False


@router.post("/calculate-tcs")
def calculate_tcs_endpoint(payload: TCSCalculationRequest):
    """Calculate statutory TCS under Section 206C(1G) LRS rules."""
    res = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=payload.current_amount_inr,
        is_overseas_trip=payload.is_overseas_trip,
        pan_number=payload.pan_number,
        cumulative_fy_spend_inr=payload.cumulative_fy_spend_inr,
    )
    return {
        "is_applicable": res.is_applicable,
        "pan_provided": res.pan_provided,
        "pan_number": res.pan_number,
        "cumulative_spend_prior_inr": res.cumulative_spend_prior_inr,
        "current_tx_amount_inr": res.current_tx_amount_inr,
        "tier_5pct_taxable_amount_inr": res.tier_5pct_taxable_amount_inr,
        "tier_5pct_tcs_amount_inr": res.tier_5pct_tcs_amount_inr,
        "tier_20pct_taxable_amount_inr": res.tier_20pct_taxable_amount_inr,
        "tier_20pct_tcs_amount_inr": res.tier_20pct_tcs_amount_inr,
        "total_tcs_amount_inr": res.total_tcs_amount_inr,
        "effective_tcs_rate_pct": res.effective_tcs_rate_pct,
        "rationale": res.rationale,
    }


@router.post("/calculate-gst")
def calculate_gst_endpoint(payload: GSTCalculationRequest):
    """Calculate statutory GST with jurisdiction split."""
    res = TaxComplianceEngine.calculate_gst(
        taxable_base_inr=payload.taxable_base_inr,
        scheme=payload.scheme,
        is_inter_state=payload.is_inter_state,
    )
    return {
        "tax_scheme": res.tax_scheme.value,
        "taxable_base_inr": res.taxable_base_inr,
        "gst_rate_pct": res.gst_rate_pct,
        "is_inter_state": res.is_inter_state,
        "cgst_rate_pct": res.cgst_rate_pct,
        "cgst_amount_inr": res.cgst_amount_inr,
        "sgst_rate_pct": res.sgst_rate_pct,
        "sgst_amount_inr": res.sgst_amount_inr,
        "igst_rate_pct": res.igst_rate_pct,
        "igst_amount_inr": res.igst_amount_inr,
        "total_gst_amount_inr": res.total_gst_amount_inr,
        "itc_eligible": res.itc_eligible,
    }


@router.post("/compile-invoice")
def compile_invoice_endpoint(payload: CommercialInvoiceRequest):
    """Compile itemized commercial invoice with net sourcing costs, margins, GST, and TCS."""
    domain_items = [
        SourcingLineItem(
            item_id=it.item_id,
            service_type=it.service_type,
            title=it.title,
            supplier_name=it.supplier_name,
            sourcing_channel=it.sourcing_channel,
            currency=it.currency,
            supplier_net_amount=it.supplier_net_amount,
            fx_rate_to_inr=it.fx_rate_to_inr,
            supplier_net_inr=0.0,
            agency_markup_pct=it.agency_markup_pct,
            agency_markup_inr=0.0,
            gross_client_price_inr=0.0,
            gst_scheme=it.gst_scheme,
        )
        for it in payload.line_items
    ]

    summary = TaxComplianceEngine.compile_commercial_invoice(
        trip_id=payload.trip_id,
        line_items=domain_items,
        is_overseas_trip=payload.is_overseas_trip,
        pan_number=payload.pan_number,
        cumulative_fy_spend_inr=payload.cumulative_fy_spend_inr,
        is_inter_state=payload.is_inter_state,
    )

    return {
        "trip_id": summary.trip_id,
        "total_supplier_net_inr": summary.total_supplier_net_inr,
        "total_agency_margin_inr": summary.total_agency_margin_inr,
        "gross_package_price_inr": summary.gross_package_price_inr,
        "total_gst_inr": summary.total_gst_inr,
        "total_tcs_inr": summary.total_tcs_inr,
        "grand_total_payable_inr": summary.grand_total_payable_inr,
        "tcs_breakdown": {
            "total_tcs_amount_inr": summary.tcs_breakdown.total_tcs_amount_inr,
            "effective_tcs_rate_pct": summary.tcs_breakdown.effective_tcs_rate_pct,
            "rationale": summary.tcs_breakdown.rationale,
            "pan_provided": summary.tcs_breakdown.pan_provided,
        },
        "item_count": len(summary.line_items),
    }
