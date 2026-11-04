"""
src/fees/tax_compliance.py — Indian Tax (TCS/GST) & Sourcing Cost Ledger Engine (Gap #01, #04, #15).

Implements:
1. TCS (Tax Collected at Source) on overseas tour packages — EFFECTIVE-DATED
   regimes (rates changed via Budget 2024/2025/2026; research record:
   Docs/research/INDIA_COMPLIANCE_RATES_TCS_GST_2026-11-03.md):
   - budget2024 (2024-10-01→2025-03-31): 5% up to ₹7,00,000; 20% above; no-PAN 20%.
   - budget2025 (2025-04-01→2026-03-31): 5% up to ₹10,00,000; 20% above; no-PAN 20%.
   - budget2026 (from 2026-04-01, CURRENT): flat 2% from the first rupee
     (IT Act 2025 s.394(1) Table 8.D); no-PAN handling is an explicit config
     (default: standard rate + advisory note — the fetched sources are silent
     on a no-PAN penalty under the new table, and none is fabricated here).
2. GST — scheme-based calculation (tour package 5% no-ITC / service fee 18%)
   PLUS an effective-dated service-type matrix implementing GST 2.0
   (effective 2025-09-22): hotel rooms ≤ ₹7,500/night → 5% without ITC
   (transaction-value basis), > ₹7,500 → 18% with ITC; economy/premium-economy
   air 5%, business class 12%; restaurants 5% without ITC.
   - Automatic CGST/SGST (Intra-state) vs IGST (Inter-state) split.
3. Sourcing Cost Ledger:
   - Line-item tracking of supplier net cost, agency markup, gross price, taxes, and net margin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from enum import Enum
import re
from typing import List, Optional

_PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class GSTTaxScheme(str, Enum):
    TOUR_PACKAGE_5PCT = "TOUR_PACKAGE_5PCT"  # 5% GST on gross package price, no ITC
    SERVICE_FEE_18PCT = "SERVICE_FEE_18PCT"  # 18% GST on agency commission/fee only, with ITC


@dataclass(slots=True)
class TCSRegime:
    """One statutory TCS regime, effective-dated and source-cited.

    ``no_pan_rate_pct`` of ``None`` means the fetched sources are silent on a
    no-PAN penalty for this regime: the standard rate applies and the caller
    is told to verify (never silently fabricate a penalty)."""

    name: str
    effective_from: date_cls
    effective_to: Optional[date_cls]
    threshold_inr: Optional[float]  # None = no threshold (flat from first rupee)
    below_rate_pct: float
    above_rate_pct: float
    no_pan_rate_pct: Optional[float]
    source_url: str


# Sorted by effective_from; select_tcs_regime picks the row containing as_of.
TCS_REGIMES: List[TCSRegime] = [
    TCSRegime(
        name="budget2024",
        effective_from=date_cls(2024, 10, 1),
        effective_to=date_cls(2025, 3, 31),
        threshold_inr=700_000.0,
        below_rate_pct=5.0,
        above_rate_pct=20.0,
        no_pan_rate_pct=20.0,
        source_url="https://incometaxindia.gov.in (s.206C(1G), FY2024-25)",
    ),
    TCSRegime(
        name="budget2025",
        effective_from=date_cls(2025, 4, 1),
        effective_to=date_cls(2026, 3, 31),
        threshold_inr=1_000_000.0,
        below_rate_pct=5.0,
        above_rate_pct=20.0,
        no_pan_rate_pct=20.0,
        source_url="https://incometaxindia.gov.in/documents/20117/42998/Tax-Collection-at-Source-TCS_2026-01-19_06-07-07_032f98_en.pdf",
    ),
    TCSRegime(
        name="budget2026",
        effective_from=date_cls(2026, 4, 1),
        effective_to=None,
        threshold_inr=None,
        below_rate_pct=2.0,
        above_rate_pct=2.0,
        no_pan_rate_pct=None,  # sources silent — standard rate + advisory note
        source_url="https://blog.tdsman.com/2026/09/tcs-on-foreign-remittances-and-overseas-tour-packages-section-3941-206c1g/",
    ),
]


def select_tcs_regime(as_of: Optional[date_cls] = None) -> TCSRegime:
    """Pick the TCS regime covering ``as_of`` (default: today).

    A date before the earliest regime falls back to the earliest row and the
    rationale carries the window explicitly — dates are never silently
    matched against the wrong statute."""
    target = as_of or date_cls.today()
    for regime in TCS_REGIMES:
        end = regime.effective_to or date_cls.max
        if regime.effective_from <= target <= end:
            return regime
    return TCS_REGIMES[0]


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
    # Effective-dating provenance (inv-3 basis discipline): which statute
    # produced these numbers and for which date window. Defaults keep the
    # pre-existing constructor call sites valid; the engine always sets them.
    regime_name: str = ""
    source_url: str = ""
    no_pan_note: str = ""


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
    # Matrix provenance (inv-3 basis discipline) — set by estimate_service_gst.
    rate_basis: str = ""
    source_url: str = ""


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
    TCS is regime-dispatched by date (see ``TCS_REGIMES``); the legacy
    ``TCS_LRS_THRESHOLD_INR`` constant is kept for backward compatibility of
    readers but is superseded by the effective-dated regime rows.
    """

    TCS_LRS_THRESHOLD_INR = 700000.0  # legacy ₹7,00,000 threshold (budget2024)

    @classmethod
    def calculate_tcs(
        cls,
        current_amount_inr: float,
        is_overseas_trip: bool = True,
        pan_number: Optional[str] = None,
        cumulative_fy_spend_inr: float = 0.0,
        as_of: Optional[date_cls] = None,
        no_pan_rate_override_pct: Optional[float] = None,
    ) -> TCSBreakdown:
        """
        Calculate TCS for overseas tour packages under the regime covering
        ``as_of`` (default: today).

        ``no_pan_rate_override_pct`` lets an agency config pin a no-PAN rate
        for regimes where the sources are silent (budget2026 default: None →
        standard rate + advisory note, never a fabricated penalty).
        """
        regime = select_tcs_regime(as_of)
        not_applicable = TCSBreakdown(
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
            regime_name=regime.name,
            source_url=regime.source_url,
        )
        if not is_overseas_trip or current_amount_inr <= 0:
            return not_applicable

        clean_pan = (pan_number or "").strip().upper()
        has_valid_pan = bool(_PAN_REGEX.match(clean_pan))

        # No-PAN handling per regime: explicit statutory rate when the regime
        # declares one; otherwise the standard rate plus an advisory note.
        if not has_valid_pan:
            if regime.no_pan_rate_pct is not None:
                rate = regime.no_pan_rate_pct
                no_pan_note = ""
            elif no_pan_rate_override_pct is not None:
                rate = float(no_pan_rate_override_pct)
                no_pan_note = (
                    f"No-PAN rate {rate:.1f}% applied via agency config override "
                    f"(statutory no-PAN rate for regime {regime.name} unverified)."
                )
            else:
                rate = regime.below_rate_pct
                no_pan_note = (
                    "PAN not furnished; the standard rate was applied because this "
                    "regime's sources do not state a no-PAN penalty. Verify the "
                    "no-PAN provision with a tax advisor before invoicing."
                )
            tcs_amt = round(current_amount_inr * (rate / 100.0), 2)
            flat = regime.threshold_inr is None
            return TCSBreakdown(
                is_applicable=True,
                pan_provided=False,
                pan_number=None,
                cumulative_spend_prior_inr=cumulative_fy_spend_inr,
                current_tx_amount_inr=current_amount_inr,
                tier_5pct_taxable_amount_inr=current_amount_inr if flat else 0.0,
                tier_5pct_tcs_amount_inr=tcs_amt if flat else 0.0,
                tier_20pct_taxable_amount_inr=0.0 if flat else current_amount_inr,
                tier_20pct_tcs_amount_inr=0.0 if flat else tcs_amt,
                total_tcs_amount_inr=tcs_amt,
                effective_tcs_rate_pct=rate,
                rationale=(
                    f"PAN not furnished or invalid; {rate:.0f}% rate applied under regime "
                    f"{regime.name}. {no_pan_note}".strip()
                ),
                regime_name=regime.name,
                source_url=regime.source_url,
                no_pan_note=no_pan_note,
            )

        prior_spend = max(0.0, float(cumulative_fy_spend_inr))

        if regime.threshold_inr is None:
            # Flat regime (budget2026): 2% from the first rupee, no threshold.
            tcs_amt = round(current_amount_inr * (regime.below_rate_pct / 100.0), 2)
            return TCSBreakdown(
                is_applicable=True,
                pan_provided=True,
                pan_number=clean_pan,
                cumulative_spend_prior_inr=prior_spend,
                current_tx_amount_inr=current_amount_inr,
                tier_5pct_taxable_amount_inr=current_amount_inr,
                tier_5pct_tcs_amount_inr=tcs_amt,
                tier_20pct_taxable_amount_inr=0.0,
                tier_20pct_tcs_amount_inr=0.0,
                total_tcs_amount_inr=tcs_amt,
                effective_tcs_rate_pct=regime.below_rate_pct,
                rationale=(
                    f"Overseas tour package (regime {regime.name}): flat "
                    f"{regime.below_rate_pct:.0f}% from the first rupee — "
                    f"₹{current_amount_inr:,.2f} @ {regime.below_rate_pct:.0f}% = ₹{tcs_amt:,.2f}."
                ),
                regime_name=regime.name,
                source_url=regime.source_url,
            )

        # Tiered LRS calculation (threshold regimes).
        threshold = regime.threshold_inr
        new_total = prior_spend + current_amount_inr

        if prior_spend >= threshold:
            # Entire current amount is in the above-threshold bracket.
            taxable_below = 0.0
            taxable_above = current_amount_inr
        elif new_total <= threshold:
            # Entire current amount is in the below-threshold bracket.
            taxable_below = current_amount_inr
            taxable_above = 0.0
        else:
            # Splits across the threshold.
            taxable_below = threshold - prior_spend
            taxable_above = current_amount_inr - taxable_below

        tcs_below = round(taxable_below * (regime.below_rate_pct / 100.0), 2)
        tcs_above = round(taxable_above * (regime.above_rate_pct / 100.0), 2)
        total_tcs = round(tcs_below + tcs_above, 2)
        effective_rate = round((total_tcs / current_amount_inr) * 100.0, 2) if current_amount_inr > 0 else 0.0

        rationale = (
            f"Overseas tour package (regime {regime.name}): "
            f"₹{taxable_below:,.2f} @ {regime.below_rate_pct:.0f}% = ₹{tcs_below:,.2f}; "
            f"₹{taxable_above:,.2f} @ {regime.above_rate_pct:.0f}% = ₹{tcs_above:,.2f}."
        )

        return TCSBreakdown(
            is_applicable=True,
            pan_provided=True,
            pan_number=clean_pan,
            cumulative_spend_prior_inr=prior_spend,
            current_tx_amount_inr=current_amount_inr,
            tier_5pct_taxable_amount_inr=taxable_below,
            tier_5pct_tcs_amount_inr=tcs_below,
            tier_20pct_taxable_amount_inr=taxable_above,
            tier_20pct_tcs_amount_inr=tcs_above,
            total_tcs_amount_inr=total_tcs,
            effective_tcs_rate_pct=effective_rate,
            rationale=rationale,
            regime_name=regime.name,
            source_url=regime.source_url,
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

    # Effective-dated GST 2.0 service matrix (research record:
    # Docs/research/INDIA_COMPLIANCE_RATES_TCS_GST_2026-11-03.md).
    # Rows: (service_type, effective_from, effective_to, condition, rate, itc, source).
    # ``condition`` is a callable over per-night rate (hotels only, transaction
    # value basis from 2025). ``None`` effective_to = current.
    GST_7500_NIGHT_THRESHOLD_INR = 7500.0

    @classmethod
    def estimate_service_gst(
        cls,
        service_type: str,
        amount_inr: float,
        is_inter_state: bool = False,
        per_night_rate_inr: Optional[float] = None,
        as_of: Optional[date_cls] = None,
    ) -> GSTBreakdown:
        """GST for a specific service line under the effective-dated matrix.

        service_type: hotel | flight_economy | flight_business | restaurant.
        Unknown service types raise — a rate is never guessed."""
        target = as_of or date_cls.today()
        svc = (service_type or "").strip().lower()
        gst2 = date_cls(2025, 9, 22)

        if svc == "hotel":
            if target >= gst2:
                if per_night_rate_inr is None:
                    raise ValueError(
                        "hotel GST under GST 2.0 needs per_night_rate_inr "
                        "(transaction-value basis; ₹7,500/night threshold)"
                    )
                low_band = per_night_rate_inr <= cls.GST_7500_NIGHT_THRESHOLD_INR
                rate, itc, basis = (5.0, False, "gst2_hotel_le_7500") if low_band else (
                    18.0, True, "gst2_hotel_gt_7500")
                source = "https://gstcouncil.gov.in/sites/default/files/2025-09/faq_0.pdf"
            else:
                low_band = (per_night_rate_inr or 0) <= cls.GST_7500_NIGHT_THRESHOLD_INR
                rate, itc, basis = (12.0, True, "pre_gst2_hotel_le_7500") if low_band else (
                    18.0, True, "pre_gst2_hotel_gt_7500")
                source = "https://blog.axisrooms.com/hotel-gst/ (pre-2.0 corridor)"
        elif svc in ("flight_economy", "flight_premium_economy"):
            rate, itc, basis, source = 5.0, True, "air_economy", "https://gstcouncil.gov.in (56th meeting, unchanged)"
        elif svc == "flight_business":
            rate, itc, basis, source = 12.0, True, "air_business", "https://gstcouncil.gov.in (56th meeting, unchanged)"
        elif svc == "restaurant":
            rate, itc, basis, source = 5.0, False, "restaurant_no_itc", "https://gstcouncil.gov.in (56th meeting)"
        else:
            raise ValueError(
                f"Unknown service_type '{service_type}' for GST matrix "
                "(expected hotel | flight_economy | flight_premium_economy | flight_business | restaurant)"
            )

        return cls._gst_at_rate(amount_inr, rate, itc, is_inter_state, basis, source)

    @classmethod
    def _gst_at_rate(
        cls,
        amount_inr: float,
        rate: float,
        itc: bool,
        is_inter_state: bool,
        basis: str,
        source: str,
    ) -> GSTBreakdown:
        """Rate-resolved GST breakdown with basis + source provenance."""
        scheme = GSTTaxScheme.SERVICE_FEE_18PCT if itc else GSTTaxScheme.TOUR_PACKAGE_5PCT
        if amount_inr <= 0:
            breakdown = cls.calculate_gst(0.0, scheme=scheme, is_inter_state=is_inter_state)
            breakdown.rate_basis = basis
            breakdown.source_url = source
            return breakdown
        breakdown = cls.calculate_gst(amount_inr, scheme=scheme, is_inter_state=is_inter_state)
        # calculate_gst derives the rate from the scheme enum; overlay the
        # matrix-resolved rate explicitly (12% air / 5-18% hotel are not
        # expressible as the two legacy schemes).
        breakdown.gst_rate_pct = rate
        if is_inter_state:
            breakdown.igst_rate_pct = rate
            breakdown.igst_amount_inr = round(amount_inr * (rate / 100.0), 2)
            breakdown.cgst_rate_pct = 0.0
            breakdown.cgst_amount_inr = 0.0
            breakdown.sgst_rate_pct = 0.0
            breakdown.sgst_amount_inr = 0.0
            breakdown.total_gst_amount_inr = breakdown.igst_amount_inr
        else:
            breakdown.igst_rate_pct = 0.0
            breakdown.igst_amount_inr = 0.0
            breakdown.cgst_rate_pct = rate / 2.0
            breakdown.cgst_amount_inr = round(amount_inr * (rate / 200.0), 2)
            breakdown.sgst_rate_pct = rate / 2.0
            breakdown.sgst_amount_inr = round(amount_inr * (rate / 200.0), 2)
            breakdown.total_gst_amount_inr = round(breakdown.cgst_amount_inr + breakdown.sgst_amount_inr, 2)
        breakdown.itc_eligible = itc
        breakdown.rate_basis = basis
        breakdown.source_url = source
        return breakdown

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
