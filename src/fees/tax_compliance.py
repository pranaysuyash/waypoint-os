"""
src/fees/tax_compliance.py — Indian Tax (TCS/GST) & Sourcing Cost Ledger Engine (Gap #01, #04, #15).

Implements:
1. RBI / Income Tax Act TCS (Tax Collected at Source) under LRS Section 206C(1G):
   - Overseas tour package baseline: 5% up to ₹7,00,000 threshold per financial year.
   - 20% on the amount exceeding ₹7,00,000.
   - Non-PAN penalty rate: 20% flat.
2. GST (Goods & Services Tax) calculation:
   - Tour operator package: 5% GST without ITC (Input Tax Credit).
   - Agency service fee / standalone ticketing: 18% GST on agency margin.
   - Automatic CGST/SGST (Intra-state) vs IGST (Inter-state) split.
3. Sourcing Cost Ledger:
   - Line-item tracking of supplier net cost, agency markup, gross price, taxes, and net margin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class GSTTaxScheme(str, Enum):
    TOUR_PACKAGE_5PCT = "TOUR_PACKAGE_5PCT"  # 5% GST on gross package price, no ITC
    SERVICE_FEE_18PCT = "SERVICE_FEE_18PCT"  # 18% GST on agency commission/fee only, with ITC


class SourcingChannel(str, Enum):
    GDS_SABRE = "GDS_SABRE"
    GDS_AMADEUS = "GDS_AMADEUS"
    NDC_DIRECT = "NDC_DIRECT"
    BEDBANK_HOTELBEDS = "BEDBANK_HOTELBEDS"
    DIRECT_DMC = "DIRECT_DMC"
    LOCAL_OPERATOR = "LOCAL_OPERATOR"


@dataclass(slots=True)
class TCSBreakdown:
    is_applicable: bool
    pan_provided: bool
    pan_number: Optional[str]
    cumulative_spend_prior_inr: float
    current_tx_amount_inr: float
    tier_5pct_taxable_amount_inr: float
    tier_5pct_tcs_amount_inr: float
    tier_20pct_taxable_amount_inr: float
    tier_20pct_tcs_amount_inr: float
    total_tcs_amount_inr: float
    effective_tcs_rate_pct: float
    rationale: str


@dataclass(slots=True)
class GSTBreakdown:
    tax_scheme: GSTTaxScheme
    taxable_base_inr: float
    gst_rate_pct: float
    is_inter_state: bool  # True -> IGST, False -> CGST + SGST
    cgst_rate_pct: float
    cgst_amount_inr: float
    sgst_rate_pct: float
    sgst_amount_inr: float
    igst_rate_pct: float
    igst_amount_inr: float
    total_gst_amount_inr: float
    itc_eligible: bool


@dataclass(slots=True)
class SourcingLineItem:
    item_id: str
    service_type: str  # flight, hotel, transfer, activity, visa, insurance
    title: str
    supplier_name: str
    sourcing_channel: SourcingChannel
    currency: str
    supplier_net_amount: float
    fx_rate_to_inr: float
    supplier_net_inr: float
    agency_markup_pct: float
    agency_markup_inr: float
    gross_client_price_inr: float
    gst_scheme: GSTTaxScheme
    gst_breakdown: Optional[GSTBreakdown] = None


@dataclass(slots=True)
class CommercialInvoiceSummary:
    trip_id: str
    total_supplier_net_inr: float
    total_agency_margin_inr: float
    gross_package_price_inr: float
    total_gst_inr: float
    total_tcs_inr: float
    grand_total_payable_inr: float
    tcs_breakdown: TCSBreakdown
    line_items: List[SourcingLineItem] = field(default_factory=list)


class TaxComplianceEngine:
    """
    Computes statutory TCS and GST liability for Indian travel operations.
    """

    TCS_LRS_THRESHOLD_INR = 700000.0  # ₹7,00,000 threshold

    @classmethod
    def calculate_tcs(
        cls,
        current_amount_inr: float,
        is_overseas_trip: bool = True,
        pan_number: Optional[str] = None,
        cumulative_fy_spend_inr: float = 0.0,
    ) -> TCSBreakdown:
        """
        Calculate TCS under Section 206C(1G) for overseas tour packages.
        """
        if not is_overseas_trip or current_amount_inr <= 0:
            return TCSBreakdown(
                is_applicable=False,
                pan_provided=bool(pan_number),
                pan_number=pan_number,
                cumulative_spend_prior_inr=cumulative_fy_spend_inr,
                current_tx_amount_inr=current_amount_inr,
                tier_5pct_taxable_amount_inr=0.0,
                tier_5pct_tcs_amount_inr=0.0,
                tier_20pct_taxable_amount_inr=0.0,
                tier_20pct_tcs_amount_inr=0.0,
                total_tcs_amount_inr=0.0,
                effective_tcs_rate_pct=0.0,
                rationale="Domestic journey or zero invoice amount; TCS not applicable.",
            )

        clean_pan = (pan_number or "").strip().upper()
        has_valid_pan = len(clean_pan) == 10

        # Non-PAN penalty rule: 20% flat on entire transaction
        if not has_valid_pan:
            tcs_amt = round(current_amount_inr * 0.20, 2)
            return TCSBreakdown(
                is_applicable=True,
                pan_provided=False,
                pan_number=None,
                cumulative_spend_prior_inr=cumulative_fy_spend_inr,
                current_tx_amount_inr=current_amount_inr,
                tier_5pct_taxable_amount_inr=0.0,
                tier_5pct_tcs_amount_inr=0.0,
                tier_20pct_taxable_amount_inr=current_amount_inr,
                tier_20pct_tcs_amount_inr=tcs_amt,
                total_tcs_amount_inr=tcs_amt,
                effective_tcs_rate_pct=20.0,
                rationale="PAN not furnished or invalid; standard 20% statutory withholding applied.",
            )

        # Tiered LRS calculation
        prior_spend = max(0.0, float(cumulative_fy_spend_inr))
        new_total = prior_spend + current_amount_inr

        if prior_spend >= cls.TCS_LRS_THRESHOLD_INR:
            # Entire current amount is in 20% bracket
            taxable_5 = 0.0
            taxable_20 = current_amount_inr
        elif new_total <= cls.TCS_LRS_THRESHOLD_INR:
            # Entire current amount is in 5% bracket
            taxable_5 = current_amount_inr
            taxable_20 = 0.0
        else:
            # Splits across ₹7L threshold
            taxable_5 = cls.TCS_LRS_THRESHOLD_INR - prior_spend
            taxable_20 = current_amount_inr - taxable_5

        tcs_5 = round(taxable_5 * 0.05, 2)
        tcs_20 = round(taxable_20 * 0.20, 2)
        total_tcs = round(tcs_5 + tcs_20, 2)
        effective_rate = round((total_tcs / current_amount_inr) * 100.0, 2) if current_amount_inr > 0 else 0.0

        rationale = (
            f"LRS Overseas Package: ₹{taxable_5:,.2f} @ 5% = ₹{tcs_5:,.2f}; "
            f"₹{taxable_20:,.2f} @ 20% = ₹{tcs_20:,.2f}."
        )

        return TCSBreakdown(
            is_applicable=True,
            pan_provided=True,
            pan_number=clean_pan,
            cumulative_spend_prior_inr=prior_spend,
            current_tx_amount_inr=current_amount_inr,
            tier_5pct_taxable_amount_inr=taxable_5,
            tier_5pct_tcs_amount_inr=tcs_5,
            tier_20pct_taxable_amount_inr=taxable_20,
            tier_20pct_tcs_amount_inr=tcs_20,
            total_tcs_amount_inr=total_tcs,
            effective_tcs_rate_pct=effective_rate,
            rationale=rationale,
        )

    @classmethod
    def calculate_gst(
        cls,
        taxable_base_inr: float,
        scheme: GSTTaxScheme = GSTTaxScheme.TOUR_PACKAGE_5PCT,
        is_inter_state: bool = False,
    ) -> GSTBreakdown:
        """
        Calculate GST liability based on chosen scheme and jurisdiction.
        """
        if taxable_base_inr <= 0:
            return GSTBreakdown(
                tax_scheme=scheme,
                taxable_base_inr=0.0,
                gst_rate_pct=0.0,
                is_inter_state=is_inter_state,
                cgst_rate_pct=0.0,
                cgst_amount_inr=0.0,
                sgst_rate_pct=0.0,
                sgst_amount_inr=0.0,
                igst_rate_pct=0.0,
                igst_amount_inr=0.0,
                total_gst_amount_inr=0.0,
                itc_eligible=scheme == GSTTaxScheme.SERVICE_FEE_18PCT,
            )

        if scheme == GSTTaxScheme.TOUR_PACKAGE_5PCT:
            rate = 5.0
            itc = False
        else:
            rate = 18.0
            itc = True

        if is_inter_state:
            igst_rate = rate
            cgst_rate = 0.0
            sgst_rate = 0.0
            igst_amt = round(taxable_base_inr * (igst_rate / 100.0), 2)
            cgst_amt = 0.0
            sgst_amt = 0.0
            total_gst = igst_amt
        else:
            igst_rate = 0.0
            cgst_rate = rate / 2.0
            sgst_rate = rate / 2.0
            cgst_amt = round(taxable_base_inr * (cgst_rate / 100.0), 2)
            sgst_amt = round(taxable_base_inr * (sgst_rate / 100.0), 2)
            igst_amt = 0.0
            total_gst = round(cgst_amt + sgst_amt, 2)

        return GSTBreakdown(
            tax_scheme=scheme,
            taxable_base_inr=taxable_base_inr,
            gst_rate_pct=rate,
            is_inter_state=is_inter_state,
            cgst_rate_pct=cgst_rate,
            cgst_amount_inr=cgst_amt,
            sgst_rate_pct=sgst_rate,
            sgst_amount_inr=sgst_amt,
            igst_rate_pct=igst_rate,
            igst_amount_inr=igst_amt,
            total_gst_amount_inr=total_gst,
            itc_eligible=itc,
        )

    @classmethod
    def compile_commercial_invoice(
        cls,
        trip_id: str,
        line_items: List[SourcingLineItem],
        is_overseas_trip: bool = True,
        pan_number: Optional[str] = None,
        cumulative_fy_spend_inr: float = 0.0,
        is_inter_state: bool = False,
    ) -> CommercialInvoiceSummary:
        """
        Compile complete commercial invoice with itemized sourcing costs, GST, and TCS.
        """
        total_supplier_net = 0.0
        total_agency_margin = 0.0
        total_gross_price = 0.0
        total_gst = 0.0

        for item in line_items:
            # Convert supplier net to INR
            item.supplier_net_inr = round(item.supplier_net_amount * item.fx_rate_to_inr, 2)
            # Calculate markup
            item.agency_markup_inr = round(item.supplier_net_inr * (item.agency_markup_pct / 100.0), 2)
            item.gross_client_price_inr = round(item.supplier_net_inr + item.agency_markup_inr, 2)

            # Calculate line item GST
            taxable_base = (
                item.gross_client_price_inr
                if item.gst_scheme == GSTTaxScheme.TOUR_PACKAGE_5PCT
                else item.agency_markup_inr
            )
            item.gst_breakdown = cls.calculate_gst(
                taxable_base_inr=taxable_base,
                scheme=item.gst_scheme,
                is_inter_state=is_inter_state,
            )

            total_supplier_net += item.supplier_net_inr
            total_agency_margin += item.agency_markup_inr
            total_gross_price += item.gross_client_price_inr
            total_gst += item.gst_breakdown.total_gst_amount_inr

        # TCS applies on total invoice package value (gross + GST)
        invoice_value_before_tcs = total_gross_price + total_gst
        tcs_breakdown = cls.calculate_tcs(
            current_amount_inr=invoice_value_before_tcs,
            is_overseas_trip=is_overseas_trip,
            pan_number=pan_number,
            cumulative_fy_spend_inr=cumulative_fy_spend_inr,
        )

        grand_total = round(invoice_value_before_tcs + tcs_breakdown.total_tcs_amount_inr, 2)

        return CommercialInvoiceSummary(
            trip_id=trip_id,
            total_supplier_net_inr=round(total_supplier_net, 2),
            total_agency_margin_inr=round(total_agency_margin, 2),
            gross_package_price_inr=round(total_gross_price, 2),
            total_gst_inr=round(total_gst, 2),
            total_tcs_inr=tcs_breakdown.total_tcs_amount_inr,
            grand_total_payable_inr=grand_total,
            tcs_breakdown=tcs_breakdown,
            line_items=line_items,
        )
