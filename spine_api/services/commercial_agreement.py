"""Canonical commercial meaning shared by quotes, consent and fulfillment.

TripStore remains the durable authority. This module projects current pricing
and creates verifiable, traveler-safe historical snapshots; it owns no cache or
second store. Existing USD fee policy remains the calculation authority.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def finite_money(value: Any, *, positive: bool = True) -> float | None:
    """Reject booleans and non-finite values before money crosses a contract."""
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or (amount <= 0 if positive else amount < 0):
            return None
        number = float(amount)
        return number if Decimal(str(number)).is_finite() else None
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        return None


@dataclass(frozen=True, slots=True)
class CommercialPricing:
    net_cost: float
    currency: str
    retail_price: float | None = None
    margin_percent: float | None = None
    retail_basis: str = "unpriced"
    margin_basis: str = "unpriced"
    provenance: dict[str, Any] = field(default_factory=dict)
    missing: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.retail_price is not None and not self.missing


def project_commercial_pricing(trip: dict, agency_id: str) -> CommercialPricing | None:
    """Separate supplier cost from retail, without treating native money as USD.

    An explicit native retail must have operator approval and source evidence.
    Without that record only the existing USD-denominated policy may compute a
    preview. Known non-USD costs remain useful as an explicitly partial quote.
    """
    recommendation = (trip.get("strategy") or {}).get("recommended_option") or {}
    net_cost = finite_money(recommendation.get("cost"))
    if net_cost is None:
        return None
    raw_currency = recommendation.get("currency")
    currency = str(raw_currency or "USD").strip().upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        return CommercialPricing(net_cost=net_cost, currency=currency, missing=("A valid quote currency is required.",))

    approved = trip.get("commercial_pricing") or {}
    retail = finite_money(approved.get("retail_amount")) if isinstance(approved, dict) else None
    approved_at = approved.get("approved_at") if isinstance(approved, dict) else None
    try:
        approval_time = datetime.fromisoformat(str(approved_at).replace("Z", "+00:00"))
        dated_approval = approval_time.tzinfo is not None
    except (ValueError, TypeError):
        dated_approval = False
    if (
        retail is not None and str(approved.get("currency") or "").upper() == currency
        and str(approved.get("approved_by") or "").startswith("user:")
        and dated_approval and approved.get("evidence_ref")
    ):
        return CommercialPricing(
            net_cost=net_cost, currency=currency, retail_price=retail,
            margin_percent=round((retail - net_cost) / retail * 100, 2),
            retail_basis="operator_approved_retail", margin_basis="operator_approved_retail",
            provenance={
                "evidence_ref": approved["evidence_ref"],
                "approved_by": approved["approved_by"], "approved_at": approved_at,
            },
        )

    if currency != "USD":
        return CommercialPricing(
            net_cost=net_cost, currency=currency,
            missing=(f"Customer retail in {currency} requires same-currency operator approval and evidence; USD fee policy cannot price this currency.",),
        )

    from spine_api.services.fee_matrix import calculate_package_pricing
    from src.fees.margin_policy import resolve_margin_policy

    policy = resolve_margin_policy(category="custom_tour", package_value_usd=net_cost, agency_id=agency_id)
    pricing = calculate_package_pricing(wholesale_cost_usd=net_cost, category="custom_tour", margin_policy_rule=policy)
    retail = finite_money(pricing.client_retail_price_usd)
    if retail is None:
        return CommercialPricing(net_cost=net_cost, currency=currency, missing=("Margin policy did not produce a finite customer retail price.",))
    return CommercialPricing(
        net_cost=net_cost, currency=currency, retail_price=retail,
        margin_percent=pricing.effective_agency_margin_pct,
        retail_basis="computed_preview", margin_basis="policy_preview",
        provenance={
            "applied_rule_id": pricing.applied_rule_id,
            "markup_amount_usd": pricing.markup_amount_usd,
            "flat_planning_fee_usd": pricing.flat_planning_fee_usd,
            "currency_basis": "persisted" if raw_currency else "legacy_default_usd",
        },
    )


# Explicit allowlist keeps signer PII, internal supplier costs, bearer tokens,
# policy internals and unrelated trip state outside the public historical view.
_SNAPSHOT_FIELDS = (
    "trip_id", "title", "destination", "duration_days", "start_date", "end_date",
    "party_size", "summary", "highlights", "stated_requirements", "days",
    "available_options", "base_price", "selected_total_price", "currency",
    "pricing_basis", "selected_option_ids",
)


def agreement_snapshot(content: dict) -> dict:
    snapshot = {name: deepcopy(content[name]) for name in _SNAPSHOT_FIELDS if name in content}
    snapshot["schema_version"] = 1
    serialized = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    snapshot["revision_id"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return snapshot


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verified_accepted_agreement(trip: dict) -> dict | None:
    """Validate historical content before allowing it to authorize execution."""
    saved = trip.get("proposal_accepted_agreement")
    if not isinstance(saved, dict) or saved.get("schema_version") != 1:
        return None
    try:
        expected = agreement_snapshot(saved)
    except (TypeError, ValueError):
        return None
    if saved.get("revision_id") != expected["revision_id"]:
        return None
    if not saved.get("accepted_at") or saved.get("e_signature_consent") is not True:
        return None
    if saved.get("trip_id") != trip.get("id") or saved.get("agency_id") != trip.get("agency_id"):
        return None
    if finite_money(saved.get("selected_total_price")) is None:
        return None
    return deepcopy(saved)


def public_accepted_agreement(trip: dict) -> dict | None:
    saved = verified_accepted_agreement(trip)
    if saved is None:
        return None
    return {**agreement_snapshot(saved), "accepted_at": saved["accepted_at"]}
