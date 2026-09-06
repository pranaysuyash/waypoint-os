"""Product-B analytics router for Phase 3 Slice F extraction."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from starlette.requests import Request
from starlette.responses import Response

from spine_api.core.auth import get_current_agency
from spine_api.core.audit import AuditAction, AuditContext, audit_logger
from spine_api.core.platform_auth import require_platform_role
from spine_api.core.rate_limiter import limiter
from spine_api.models.product_b_analytics import ProductBKpiResponse
from spine_api.models.tenant import Agency
from spine_api.models.tenant import User
from spine_api.product_b_events import ProductBEventStore

router = APIRouter()
logger = logging.getLogger("spine_api.product_b_analytics")


@router.get("/analytics/product-b/kpis", response_model=ProductBKpiResponse)
def get_product_b_kpis(
    window_days: int = Query(default=30, ge=1, le=365),
    qualified_only: bool = Query(default=False),
    agency: Agency = Depends(get_current_agency),
):
    return ProductBEventStore.compute_kpis(
        window_days=window_days,
        qualified_only=qualified_only,
        workspace_id=agency.id,
    )


@router.get(
    "/platform/admin/analytics/product-b/kpis",
    response_model=ProductBKpiResponse,
    tags=["platform-admin"],
)
@limiter.limit("60/minute")
async def get_platform_product_b_kpis(
    request: Request,
    response: Response,
    window_days: int = Query(default=30, ge=1, le=365),
    qualified_only: bool = Query(default=False),
    platform_admin: User = require_platform_role("super_admin"),
    audit: AuditContext = Depends(audit_logger()),
):
    """Return global Product-B KPIs to an explicitly authorized platform admin."""

    logger.info(
        "Product-B global KPI read user=%s platform_role=%s window_days=%s qualified_only=%s",
        platform_admin.id,
        platform_admin.platform_role,
        window_days,
        qualified_only,
    )
    _ = (request, response)
    result = ProductBEventStore.compute_kpis(
        window_days=window_days,
        qualified_only=qualified_only,
    )
    await audit.log(
        AuditAction.READ,
        resource_type="platform_product_b_kpis",
        changes={
            "metric": "product_b_kpis",
            "scope": "global",
            "platform_role": platform_admin.platform_role,
            "workspace_count": result.get("scope", {}).get("workspace_count", 0),
            "window_days": window_days,
            "qualified_only": qualified_only,
        },
    )
    await audit.commit()
    return result
