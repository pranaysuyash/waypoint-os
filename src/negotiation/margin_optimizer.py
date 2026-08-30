"""
Dynamic Margin Optimizer (PER-950888, PER-20690, PER-0482).

Calculates dynamic agency take-rate margins based on departure lead-time,
trip urgency multiplier, customer price elasticity, and seasonality.
"""

from __future__ import annotations

from src.negotiation.models import MarginOptimizationResult


class MarginOptimizer:
    """Dynamic Revenue Management & Margin Curve Engine."""

    @staticmethod
    def calculate_optimal_margin(
        net_supplier_cost: float,
        lead_time_days: int,
        is_peak_season: bool = False,
        customer_price_sensitivity: float = 0.5,  # 0.0 (inelastic/luxury) to 1.0 (hyper-sensitive)
        min_margin_percent: float = 0.10,  # 10% floor
        max_margin_percent: float = 0.28,  # 28% ceiling
    ) -> MarginOptimizationResult:
        """
        Computes dynamic margin:
        M = M_base * (1 + Urgency_Factor) * Season_Factor * (1 - Sensitivity_Factor)
        """
        base_margin = 0.16  # 16% standard baseline

        # Urgency factor: Short lead times (< 7 days) have high willingness to pay
        if lead_time_days <= 3:
            urgency_multiplier = 1.35
        elif lead_time_days <= 7:
            urgency_multiplier = 1.20
        elif lead_time_days <= 21:
            urgency_multiplier = 1.05
        elif lead_time_days >= 90:
            urgency_multiplier = 0.90  # Early bird incentive
        else:
            urgency_multiplier = 1.00

        # Seasonality factor
        season_multiplier = 1.15 if is_peak_season else 0.95

        # Elasticity factor: Sensitivity (0.0 to 1.0) discounts margin by up to 30%
        elasticity_discount = customer_price_sensitivity * 0.30

        # Calculate raw dynamic margin
        raw_margin = (base_margin * urgency_multiplier * season_multiplier) - elasticity_discount
        clamped_margin = max(min_margin_percent, min(max_margin_percent, raw_margin))

        selling_price = net_supplier_cost / (1.0 - clamped_margin)
        gross_profit = selling_price - net_supplier_cost

        # Rationale string
        rationale = (
            f"Applied {clamped_margin * 100:.1f}% take-rate: "
            f"Lead-time ({lead_time_days}d -> {urgency_multiplier:.2f}x urgency), "
            f"Seasonality ({season_multiplier:.2f}x), "
            f"Elasticity sensitivity ({customer_price_sensitivity:.2f})."
        )

        return MarginOptimizationResult(
            net_supplier_cost=round(net_supplier_cost, 2),
            optimized_selling_price=round(selling_price, 2),
            effective_margin_percent=round(clamped_margin * 100, 2),
            gross_profit_usd=round(gross_profit, 2),
            urgency_multiplier=urgency_multiplier,
            lead_time_days=lead_time_days,
            elasticity_score=customer_price_sensitivity,
            recommendation_rationale=rationale,
        )
