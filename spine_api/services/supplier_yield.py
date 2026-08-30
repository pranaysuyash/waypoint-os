"""
spine_api.services.supplier_yield — Multi-supplier rate comparison and yield arbitrage engine.

Compares inventory quotes across GDS and bedbanks (Amadeus, Sabre, Hotelbeds, RateHawk, Expedia TAAP)
to optimize agency profit margins and cancellation risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class SupplierQuote:
    supplier_name: str  # e.g. "Hotelbeds", "RateHawk", "Amadeus", "ExpediaTAAP"
    rate_plan_name: str
    net_cost_usd: float
    client_retail_price_usd: float
    commission_rate: float  # e.g. 0.12 (12%)
    refundable_until: Optional[str] = None  # ISO date string
    instant_confirmation: bool = True
    cancellation_flexibility_score: float = 1.0  # 0.0 (non-ref) to 1.0 (free cancel until day-of)


@dataclass(slots=True)
class YieldArbitrageItem:
    supplier_name: str
    rate_plan_name: str
    net_cost_usd: float
    client_retail_price_usd: float
    gross_margin_usd: float
    margin_percentage: float
    cancellation_flexibility_score: float
    yield_rank: int
    is_recommended: bool
    rationale: str


@dataclass(slots=True)
class YieldArbitrageReport:
    inventory_title: str
    destination: str
    quotes_evaluated_count: int
    highest_margin_supplier: str
    recommended_supplier: str
    max_margin_usd: float
    items: List[YieldArbitrageItem] = field(default_factory=list)


def evaluate_supplier_yield_arbitrage(
    inventory_title: str,
    destination: str,
    quotes: List[SupplierQuote],
) -> YieldArbitrageReport:
    """
    Compare multiple supplier quotes, compute gross margin and net profit, and rank by optimal yield.
    """
    if not quotes:
        return YieldArbitrageReport(
            inventory_title=inventory_title,
            destination=destination,
            quotes_evaluated_count=0,
            highest_margin_supplier="None",
            recommended_supplier="None",
            max_margin_usd=0.0,
            items=[],
        )

    evaluated_items = []
    for q in quotes:
        gross_margin = round(q.client_retail_price_usd - q.net_cost_usd, 2)
        margin_pct = round((gross_margin / q.client_retail_price_usd) * 100, 2) if q.client_retail_price_usd > 0 else 0.0

        # Score balancing margin (70% weight) and cancellation flexibility (30% weight)
        normalized_margin = min(1.0, max(0.0, margin_pct / 30.0))  # 30% margin = 1.0
        composite_score = (0.7 * normalized_margin) + (0.3 * q.cancellation_flexibility_score)

        evaluated_items.append({
            "quote": q,
            "gross_margin": gross_margin,
            "margin_pct": margin_pct,
            "composite_score": composite_score,
        })

    # Sort by composite score descending
    evaluated_items.sort(key=lambda x: x["composite_score"], reverse=True)

    items: List[YieldArbitrageItem] = []
    for rank, entry in enumerate(evaluated_items, start=1):
        q: SupplierQuote = entry["quote"]
        is_rec = rank == 1
        rationale = (
            f"Top yield recommendation: generates ${entry['gross_margin']} ({entry['margin_pct']}%) with "
            f"{int(q.cancellation_flexibility_score * 100)}% cancellation flexibility."
            if is_rec
            else f"Alternative option with ${entry['gross_margin']} margin ({entry['margin_pct']}%)."
        )

        items.append(
            YieldArbitrageItem(
                supplier_name=q.supplier_name,
                rate_plan_name=q.rate_plan_name,
                net_cost_usd=q.net_cost_usd,
                client_retail_price_usd=q.client_retail_price_usd,
                gross_margin_usd=entry["gross_margin"],
                margin_percentage=entry["margin_pct"],
                cancellation_flexibility_score=q.cancellation_flexibility_score,
                yield_rank=rank,
                is_recommended=is_rec,
                rationale=rationale,
            )
        )

    highest_margin_item = max(items, key=lambda x: x.gross_margin_usd)

    return YieldArbitrageReport(
        inventory_title=inventory_title,
        destination=destination,
        quotes_evaluated_count=len(quotes),
        highest_margin_supplier=highest_margin_item.supplier_name,
        recommended_supplier=items[0].supplier_name,
        max_margin_usd=highest_margin_item.gross_margin_usd,
        items=items,
    )
