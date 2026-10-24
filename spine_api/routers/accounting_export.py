"""
spine_api/routers/accounting_export.py — Trip-scoped accounting export (E08 un-orphan).

The AccountingExportBridge (Tally XML / QuickBooks JSON) previously had zero
serving-path callers — it was exercised only by hand-built fixtures. This
router derives a real ``CommercialInvoiceSummary`` from the trip's persisted
spine data and serves both formats.

Honesty boundaries (same taxonomy as the quotes read model):
- Net cost comes from ``strategy.recommended_option.cost`` — the persisted
  modeled cost, labeled preview basis (no live wholesale producer yet).
- Agency margin resolves through the dimensioned MarginPolicy via the
  canonical fee_matrix computation (applied-rule provenance echoed).
- Currency: the export is INR-native (Tally/GST/TCS are Indian tax
  constructs). Trips whose quote is not INR get an explicit not-available
  response — no invented FX rates.
- TCS: computed by the TaxComplianceEngine with an explicit ``pan_number``
  query param; absent PAN ⇒ the engine's own non-PAN rule applies and the
  rationale states it. GST: statutory scheme on the gross.
- No quote-cost trip ⇒ explicit not-available, never fabricated numbers.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.persistence import TripStore
from spine_api.services.commercial_agreement import finite_money, project_commercial_pricing
from src.accounting.export_bridge import AccountingExportBridge
from src.fees.tax_compliance import (
    CommercialInvoiceSummary,
    GSTTaxScheme,
    SourcingChannel,
    SourcingLineItem,
    TaxComplianceEngine,
    TCSBreakdown,
    GSTBreakdown,
)

logger = logging.getLogger("spine_api.accounting_export")

router = APIRouter(prefix="/api/v1/trips", tags=["accounting-export"])


def _finite_positive(value) -> Optional[float]:
    return finite_money(value)


def _is_overseas(trip: dict) -> bool:
    """A trip is overseas when its destination country is not India."""
    packet = trip.get("packet") or {}
    country = str(
        packet.get("destination_country")
        or packet.get("destination_country_code")
        or trip.get("destination_country")
        or ""
    ).strip().upper()
    if not country:
        return True  # conservative default: overseas (TCS applies)
    return country not in {"IN", "IND", "INDIA"}


@router.get("/{trip_id}/accounting-export")
def export_trip_accounting(
    trip_id: str,
    format: str = Query(default="tally", pattern="^(tally|quickbooks)$"),
    pan_number: Optional[str] = Query(default=None, max_length=20),
    agency: Agency = Depends(get_current_agency),
) -> dict:
    """Derive the commercial invoice from persisted trip data; export as
    Tally XML or QuickBooks JSON. Explicitly not available when the trip has
    no persisted quote cost or the quote is not INR."""
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    strategy = trip.get("strategy") or {}
    recommendation = strategy.get("recommended_option") or {}
    net_cost = _finite_positive(recommendation.get("cost"))
    if net_cost is None:
        raise HTTPException(
            status_code=409,
            detail="No persisted quote cost for this trip yet — run the spine to produce a recommended option before exporting.",
        )
    if str(recommendation.get("currency") or "USD").strip().upper() != "INR":
        raise HTTPException(
            status_code=409,
            detail="Accounting export is INR-native (Tally/GST/TCS). This trip's quote is not INR and no live FX producer exists — refusing to invent a conversion.",
        )

    commercial = project_commercial_pricing(trip, agency.id)
    if commercial is None or not commercial.ready or commercial.retail_price is None:
        raise HTTPException(status_code=409, detail="Accounting export requires an approved INR retail price with source evidence. USD policy fees cannot price INR amounts.")
    gross = commercial.retail_price
    margin_amount = round(gross - float(net_cost), 2)

    tcs: TCSBreakdown = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=gross,
        is_overseas_trip=_is_overseas(trip),
        pan_number=pan_number,
    )
    gst: GSTBreakdown = TaxComplianceEngine.calculate_gst(
        taxable_base_inr=gross,
        scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
    )

    line_items: list = []
    breakdown = (trip.get("decision") or {}).get("budget_breakdown") or {}
    bucket_count = len([b for b in breakdown.get("buckets") or [] if isinstance(b, dict)])
    if bucket_count:
        # Split the modeled net across buckets proportionally to their low
        # estimates; margin and GST follow the same split so the line items
        # reconcile to the invoice totals.
        bucket_lows = [
            _finite_positive(b.get("low")) or 0.0
            for b in breakdown.get("buckets")
            if isinstance(b, dict)
        ]
        total_low = sum(bucket_lows) or 1.0
        for bucket, low in zip([b for b in breakdown.get("buckets") if isinstance(b, dict)], bucket_lows):
            share = (low or 0.0) / total_low
            bucket_net = round(float(net_cost) * share, 2)
            bucket_gross = round(gross * share, 2)
            line_items.append(
                SourcingLineItem(
                    item_id=f"li_{bucket.get('bucket', 'item')}",
                    service_type=str(bucket.get("bucket") or "other"),
                    title=str(bucket.get("bucket") or "item").replace("_", " ").title(),
                    supplier_name=str(recommendation.get("name") or "trip package"),
                    sourcing_channel=SourcingChannel.DIRECT_DMC,
                    currency="INR",
                    supplier_net_amount=bucket_net,
                    fx_rate_to_inr=1.0,
                    supplier_net_inr=bucket_net,
                    agency_markup_pct=margin_amount / float(net_cost),
                    agency_markup_inr=round(bucket_gross - bucket_net, 2),
                    gross_client_price_inr=bucket_gross,
                    gst_scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
                )
            )

    invoice = CommercialInvoiceSummary(
        trip_id=trip_id,
        total_supplier_net_inr=round(float(net_cost), 2),
        total_agency_margin_inr=margin_amount,
        gross_package_price_inr=round(gross, 2),
        total_gst_inr=gst.total_gst_amount_inr,
        total_tcs_inr=tcs.total_tcs_amount_inr,
        grand_total_payable_inr=round(gross + gst.total_gst_amount_inr + tcs.total_tcs_amount_inr, 2),
        tcs_breakdown=tcs,
        line_items=line_items,
    )

    if format == "quickbooks":
        payload = AccountingExportBridge.export_quickbooks_json(
            invoice,
            customer_id=trip_id,
            customer_name=str((trip.get("packet") or {}).get("customer_name") or "Traveler"),
        )
        import json as _json

        body = _json.dumps(payload, indent=2)
    else:
        body = AccountingExportBridge.export_tally_xml(
            invoice, customer_name=str((trip.get("packet") or {}).get("customer_name") or "Traveler")
        )

    return {
        "ok": True,
        "trip_id": trip_id,
        "format": format,
        "basis": commercial.retail_basis,
        "provenance": {
            **commercial.provenance,
            "currency": commercial.currency,
            "net_cost": float(net_cost),
            "agency_margin": margin_amount,
            "gross_package_price": round(gross, 2),
            "gst_total": gst.total_gst_amount_inr,
            "tcs_total": tcs.total_tcs_amount_inr,
            "tcs_rationale": tcs.rationale,
            "grand_total_payable": invoice.grand_total_payable_inr,
        },
        "body": body,
    }
