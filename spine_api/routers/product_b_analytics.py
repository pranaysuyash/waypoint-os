"""Product-B analytics router for Phase 3 Slice F extraction."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from spine_api.product_b_events import ProductBEventStore

router = APIRouter()


@router.get("/analytics/product-b/kpis")
def get_product_b_kpis(
    window_days: int = Query(default=30, ge=1, le=365),
    qualified_only: bool = Query(default=False),
    agency: Agency = Depends(get_current_agency),
):
    _ = agency
    return ProductBEventStore.compute_kpis(window_days=window_days, qualified_only=qualified_only)
