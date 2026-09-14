"""
spine_api.services.fee_matrix — Dynamic agency fee matrix and tiered markup engine.

Supports:
- Percentage markups on wholesale net inventory.
- Flat booking & planning fee schedules.
- Margin threshold guards per destination and product category (Flights, Hotels, Custom FIT).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(slots=True)
class FeeTierRule:
    rule_id: str
    category: str  # "flights" | "hotels" | "custom_tour" | "rail"
    min_package_value_usd: float
    max_package_value_usd: float
    markup_percentage: float  # e.g. 0.12 for 12%
    flat_planning_fee_usd: float = 0.0
    minimum_margin_floor_usd: float = 50.0


@dataclass(slots=True)
class PricingBreakdown:
    wholesale_cost_usd: float
    markup_amount_usd: float
    flat_planning_fee_usd: float
    client_retail_price_usd: float
    effective_agency_margin_pct: float
    applied_rule_id: str


def default_fee_tier_rules() -> List[FeeTierRule]:
    """Derive the default ruleset from MarginPolicy PLATFORM_DEFAULT_RULES —
    single source of truth (supersession, Addendum 12). The policy seed is a
    strict superset of the retired inline literals: identical numbers plus
    the floor_pct/vendor/location/agency dimensions this checker consumes as
    floor_pct when a resolved rule drives pricing."""
    from src.fees.margin_policy import PLATFORM_DEFAULT_RULES

    return [
        FeeTierRule(
            rule_id=r.rule_id,
            category=r.category,
            min_package_value_usd=r.min_package_value_usd,
            max_package_value_usd=(
                r.max_package_value_usd
                if r.max_package_value_usd != float("inf")
                else 10**9
            ),
            markup_percentage=r.markup_pct,
            flat_planning_fee_usd=r.flat_planning_fee_usd,
            minimum_margin_floor_usd=r.min_margin_floor_usd,
        )
        for r in PLATFORM_DEFAULT_RULES
    ]


def calculate_package_pricing(
    wholesale_cost_usd: float,
    category: str = "custom_tour",
    custom_rules: Optional[List[FeeTierRule]] = None,
    margin_policy_rule: Optional[Any] = None,
) -> PricingBreakdown:
    """
    Calculate retail price and agency margin applying fee matrix rules.

    ADR-008 / Addendum 12: a resolved MarginPolicyRule (dimensioned,
    versioned) takes precedence over the legacy literals — its numbers drive
    the computation and its id + ruleset version become the applied_rule_id
    provenance. Pricing authority stays with MarginOptimizer; this function
    is the floor/markup checker.
    """
    if margin_policy_rule is not None:
        mpr = margin_policy_rule
        markup_amt = round(wholesale_cost_usd * mpr.markup_pct, 2)
        total_margin = markup_amt + mpr.flat_planning_fee_usd
        if total_margin < mpr.min_margin_floor_usd:
            markup_amt = mpr.min_margin_floor_usd - mpr.flat_planning_fee_usd
        retail_price = round(wholesale_cost_usd + markup_amt + mpr.flat_planning_fee_usd, 2)
        effective_margin_pct = round(((retail_price - wholesale_cost_usd) / retail_price) * 100, 2)
        return PricingBreakdown(
            wholesale_cost_usd=wholesale_cost_usd,
            markup_amount_usd=round(markup_amt, 2),
            flat_planning_fee_usd=mpr.flat_planning_fee_usd,
            client_retail_price_usd=retail_price,
            effective_agency_margin_pct=effective_margin_pct,
            applied_rule_id=f"{mpr.rule_id}@{mpr.ruleset_version}",
        )
    rules = custom_rules or default_fee_tier_rules()

    # Find matching rule
    matched_rule = next(
        (
            r for r in rules
            if r.category == category and r.min_package_value_usd <= wholesale_cost_usd <= r.max_package_value_usd
        ),
        rules[0],
    )

    markup_amt = round(wholesale_cost_usd * matched_rule.markup_percentage, 2)
    # Ensure minimum margin floor
    total_margin = markup_amt + matched_rule.flat_planning_fee_usd
    if total_margin < matched_rule.minimum_margin_floor_usd:
        markup_amt = matched_rule.minimum_margin_floor_usd - matched_rule.flat_planning_fee_usd

    retail_price = round(wholesale_cost_usd + markup_amt + matched_rule.flat_planning_fee_usd, 2)
    effective_margin_pct = round(((retail_price - wholesale_cost_usd) / retail_price) * 100, 2)

    return PricingBreakdown(
        wholesale_cost_usd=wholesale_cost_usd,
        markup_amount_usd=round(markup_amt, 2),
        flat_planning_fee_usd=matched_rule.flat_planning_fee_usd,
        client_retail_price_usd=retail_price,
        effective_agency_margin_pct=effective_margin_pct,
        applied_rule_id=matched_rule.rule_id,
    )
