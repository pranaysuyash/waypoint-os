"""
System + dashboard router for Phase 3 Slice C extraction.

Scope: move only:
- GET /api/system/unified-state
- GET /api/system/integrity/issues
- GET /api/dashboard/stats
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from spine_api.contract import DashboardStatsResponse, IntegrityIssuesResponse
from spine_api.core.auth import get_current_agency
from spine_api.models.tenant import Agency
from src.services.dashboard_aggregator import DashboardAggregator
from src.services.integrity_service import IntegrityService

logger = logging.getLogger("spine_api")

router = APIRouter()


@router.get("/api/system/unified-state")
async def get_unified_state(agency: Agency = Depends(get_current_agency)):
    """
    Return unified state. Scoped to the current user's agency.
    """
    try:
        return DashboardAggregator.get_unified_state(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to aggregate unified state: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal integrity error"
        )


@router.get("/api/system/integrity/issues", response_model=IntegrityIssuesResponse)
async def get_integrity_issues(agency: Agency = Depends(get_current_agency)):
    """
    Return typed integrity issues. Scoped to the current user's agency.
    """
    try:
        return IntegrityService.list_integrity_issues(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to aggregate integrity issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal integrity error",
        )


@router.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(agency: Agency = Depends(get_current_agency)):
    """
    Dashboard stat cards — computed entirely by the backend aggregator.
    Scopes all metrics to the current user's agency.
    """
    try:
        return DashboardAggregator.get_dashboard_stats(agency_id=agency.id)
    except Exception as e:
        logger.error(f"Failed to compute dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to compute dashboard stats"
        )
