"""
spine_api/routers/quotes.py — Trip-scoped real quote read model (T4, FND-0303).

Replaces the fabricated /quotes page data with quotes DERIVED from what the
spine actually persisted for a trip:

- Net cost:      ``strategy.recommended_option.cost`` (persisted modeled cost)
- Cost basis:    ``decision.budget_breakdown`` bucket estimates when present
- Margin:        ``MarginPolicy`` resolution (FND-0268) with applied-rule
                 provenance — preview basis until a live wholesale-cost
                 producer exists (never presented as a vendor price)
- Status:        real trip state — review queue status / proposal link existence
- Dates:         trip/review timestamps, never invented

Trust boundaries (honesty taxonomy):
- Every monetary field carries an explicit ``basis`` label.
- Absent persisted inputs → ``quote_ready: false`` + ``missing: [...]``.
  This endpoint never fabricates prices, tiers, or dates.
- Branch prompts (``decision.branch_options``) are surfaced as unpriced
  branches — they are contradiction groups, not alternatives, and are never
  assigned prices here.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from spine_api.contract import TripQuoteBranch, TripQuoteView, TripQuotesResponse
from spine_api.core.auth import get_current_agency, get_current_membership, get_current_user
from spine_api.models.tenant import Agency, Membership, User
from spine_api.persistence import TripStore
from spine_api.services.commercial_agreement import finite_money, project_commercial_pricing

logger = logging.getLogger("spine_api.quotes")

router = APIRouter(prefix="/api/v1/trips", tags=["quotes"])

# Schengen-standard planning buffer used only for the readiness *diagnosis*
# text; the risk level itself is not fabricated here — it mirrors the trip's
# persisted review state.
_REVIEW_STATUS_TO_QUOTE_STATUS = {
    "pending": "draft",
    "approved": "approved",
    "rejected": "rejected",
    "revision_needed": "revision_needed",
    "escalated": "under_review",
    "recovery": "under_review",
    "resolved": "approved",
}


def _finite_positive(value: Any) -> Optional[float]:
    return finite_money(value)


def _review_status(trip: dict) -> str:
    analytics = trip.get("analytics") or {}
    return str(analytics.get("review_status") or "pending")


def _derive_quote(trip: dict, agency_id: str) -> Optional[TripQuoteView]:
    """Derive the real quote from persisted strategy + decision data, or None."""
    strategy = trip.get("strategy") or {}
    recommendation = strategy.get("recommended_option") or {}
    commercial = project_commercial_pricing(trip, agency_id)
    if commercial is None:
        return None

    review_status = _review_status(trip)
    status = _REVIEW_STATUS_TO_QUOTE_STATUS.get(review_status, "draft")
    if status == "draft" and trip.get("proposal_link_token"):
        status = "sent"

    # Real timestamps only.
    created_at = trip.get("created_at") or ""
    review_meta = (trip.get("analytics") or {}).get("review_metadata") or {}
    updated_at = review_meta.get("reviewed_at") or None

    highlights = [
        str(h)
        for h in (recommendation.get("highlights") or [])
        if isinstance(h, (str, int, float)) and str(h).strip()
    ]

    return TripQuoteView(
        trip_id=trip.get("id") or "",
        title=str(recommendation.get("name") or "Proposed itinerary"),
        currency=commercial.currency,
        net_cost=commercial.net_cost,
        net_cost_basis="persisted_modeled_cost",
        margin_percent=commercial.margin_percent,
        margin_basis=commercial.margin_basis,
        margin_provenance=commercial.provenance,
        tax_percent=None,
        rack_price=commercial.retail_price,
        rack_price_basis=commercial.retail_basis,
        status=status if commercial.ready else "pricing_review",
        pricing_status="priced" if commercial.ready else "pricing_review",
        missing=list(commercial.missing),
        created_at=created_at,
        updated_at=updated_at,
        highlights=highlights,
        summary=str(recommendation.get("summary") or "") or None,
    )


def _derive_branches(trip: dict) -> List[TripQuoteBranch]:
    decision = trip.get("decision") or {}
    branches: List[TripQuoteBranch] = []
    for branch in decision.get("branch_options") or []:
        if not isinstance(branch, dict):
            continue
        label = str(branch.get("label") or "").strip()
        if not label:
            continue
        branches.append(
            TripQuoteBranch(
                label=label,
                description=str(branch.get("description") or "") or None,
                priced=False,
            )
        )
    return branches


def _missing_inputs(trip: dict) -> List[str]:
    strategy = trip.get("strategy") or {}
    recommendation = strategy.get("recommended_option") or {}
    missing: List[str] = []
    if not recommendation:
        missing.append("strategy.recommended_option (run the spine to produce a recommended itinerary)")
    elif _finite_positive(recommendation.get("cost")) is None:
        missing.append("strategy.recommended_option.cost (recommended option has no modeled cost yet)")
    return missing


@router.get("/{trip_id}/quotes", response_model=TripQuotesResponse)
def get_trip_quotes(
    trip_id: str,
    agency: Agency = Depends(get_current_agency),
) -> TripQuotesResponse:
    """Real, spine-derived quote read model for a trip (T4)."""
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    quote = _derive_quote(trip, agency.id)
    missing = _missing_inputs(trip)
    if quote is not None:
        missing.extend(quote.missing)
    budget_breakdown = (trip.get("decision") or {}).get("budget_breakdown") or None
    if not isinstance(budget_breakdown, dict) or not budget_breakdown:
        budget_breakdown = None
        if "decision.budget_breakdown (cost bucket estimates)" not in missing and quote is None:
            missing.append("decision.budget_breakdown (cost bucket estimates)")

    return TripQuotesResponse(
        trip_id=trip_id,
        quote_ready=quote is not None and quote.pricing_status == "priced",
        quotes=[quote] if quote else [],
        branches=_derive_branches(trip),
        budget_breakdown=budget_breakdown,
        missing=missing,
    )


class ApproveRetailPriceRequest(BaseModel):
    retail_amount: Decimal = Field(gt=0, allow_inf_nan=False)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    evidence_ref: str = Field(min_length=1, max_length=500)
    expected_updated_at: str = Field(min_length=1, max_length=100)


def _audit_retail_approval(trip_id: str, agency_id: str, user_id: str, approval: dict) -> None:
    from spine_api.persistence import AuditStore

    AuditStore.log_event("commercial_retail_approved", user_id, {
        "trip_id": trip_id, "agency_id": agency_id, **approval,
        "basis": "operator_approved_retail",
    })


@router.post("/{trip_id}/quotes/retail", response_model=TripQuotesResponse)
def approve_trip_retail(
    trip_id: str,
    request: ApproveRetailPriceRequest,
    agency: Agency = Depends(get_current_agency),
    user: User = Depends(get_current_user),
    membership: Membership = Depends(get_current_membership),
) -> TripQuotesResponse:
    """Record a native retail decision with server-owned approval evidence.

    This is an operator commercial decision, not a supplier-price receipt.
    Saving it changes the material agreement digest, so old customer consent
    cannot authorize the new price without renewed acceptance.
    """
    if membership.agency_id != agency.id or membership.role.lower() not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only an agency owner or admin can approve a customer retail price.")
    trip = TripStore.get_trip_for_agency(trip_id, agency.id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    commercial = project_commercial_pricing(trip, agency.id)
    if commercial is None or commercial.currency != request.currency:
        raise HTTPException(status_code=409, detail="Retail currency must match the trip's persisted supplier-cost currency.")
    if trip.get("updated_at") != request.expected_updated_at:
        raise HTTPException(status_code=409, detail="The trip changed. Reload its quote before approving a retail price.")
    amount = finite_money(request.retail_amount)
    if amount is None or not request.evidence_ref.strip():
        raise HTTPException(status_code=422, detail="A finite positive retail price and source evidence are required.")
    approval = {
        "retail_amount": amount, "currency": request.currency,
        "evidence_ref": request.evidence_ref.strip(),
        "approved_by": f"user:{user.id}",
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    result = TripStore.update_trip_if_version_for_agency(
        trip_id, agency.id, {"commercial_pricing": approval}, request.expected_updated_at
    )
    if not result:
        raise HTTPException(status_code=409, detail="The trip changed while approving this retail price. Reload and review it again.")
    _audit_retail_approval(trip_id, agency.id, user.id, approval)
    return get_trip_quotes(trip_id=trip_id, agency=agency)
