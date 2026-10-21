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
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import TripQuoteBranch, TripQuoteView, TripQuotesResponse
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.persistence import TripStore

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
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return num if num > 0 else None


def _review_status(trip: dict) -> str:
    analytics = trip.get("analytics") or {}
    return str(analytics.get("review_status") or "pending")


def _derive_quote(trip: dict, agency_id: str) -> Optional[TripQuoteView]:
    """Derive the real quote from persisted strategy + decision data, or None."""
    strategy = trip.get("strategy") or {}
    recommendation = strategy.get("recommended_option") or {}
    net_cost = _finite_positive(recommendation.get("cost"))
    if net_cost is None:
        return None

    currency = recommendation.get("currency") or "USD"
    if not isinstance(currency, str) or not currency.strip():
        currency = "USD"

    # Margin via the canonical path: resolve the dimensioned MarginPolicyRule
    # (FND-0268), then let fee_matrix do the floor/markup math and emit
    # applied_rule_id provenance. Preview basis: the net cost itself is a
    # modeled estimate until a live wholesale-cost producer (B6/B7) lands;
    # the basis labels make that explicit rather than implying vendor truth.
    from src.fees.margin_policy import resolve_margin_policy
    from spine_api.services.fee_matrix import calculate_package_pricing

    margin_rule = resolve_margin_policy(
        category="custom_tour",
        package_value_usd=net_cost,
        agency_id=agency_id,
    )
    pricing = calculate_package_pricing(
        wholesale_cost_usd=net_cost,
        category="custom_tour",
        margin_policy_rule=margin_rule,
    )
    rack_price = pricing.client_retail_price_usd
    margin_percent = pricing.effective_agency_margin_pct

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
        currency=currency,
        net_cost=net_cost,
        net_cost_basis="persisted_modeled_cost",
        margin_percent=margin_percent,
        margin_basis="policy_preview",
        margin_provenance={
            "applied_rule_id": pricing.applied_rule_id,
            "markup_amount_usd": pricing.markup_amount_usd,
            "flat_planning_fee_usd": pricing.flat_planning_fee_usd,
        },
        tax_percent=None,
        rack_price=rack_price,
        rack_price_basis="computed_preview",
        status=status,
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
    budget_breakdown = (trip.get("decision") or {}).get("budget_breakdown") or None
    if not isinstance(budget_breakdown, dict) or not budget_breakdown:
        budget_breakdown = None
        if "decision.budget_breakdown (cost bucket estimates)" not in missing and quote is None:
            missing.append("decision.budget_breakdown (cost bucket estimates)")

    return TripQuotesResponse(
        trip_id=trip_id,
        quote_ready=quote is not None,
        quotes=[quote] if quote else [],
        branches=_derive_branches(trip),
        budget_breakdown=budget_breakdown,
        missing=missing,
    )
