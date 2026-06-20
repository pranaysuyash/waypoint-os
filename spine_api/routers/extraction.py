"""
Extraction router — version snapshot and attempt metadata.

Endpoints:
  GET  /api/extractions/{attempt_id}/version-snapshot — immutable version snapshot for an extraction attempt

Auth model:
  All routes require JWT auth (router-level Depends).
  Tenant scoping: agency_id from JWT membership, never from request body.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from spine_api.core.rls import get_rls_db
from spine_api.core.auth import get_current_agency_id, require_permission
from spine_api.services import extraction_service

logger = logging.getLogger("spine_api.extraction")

router = APIRouter(prefix="/api/extractions", tags=["extraction"])


@router.get("/{attempt_id}/version-snapshot")
async def get_version_snapshot(
    attempt_id: str,
    agency_id: str = Depends(get_current_agency_id),
    _membership=require_permission("trips:read"),
    db=Depends(get_rls_db),
):
    """Return the immutable version snapshot captured at extraction attempt creation.

    The snapshot records which prompt/schema/routing/dictionary/normalization
    versions were active when this extraction attempt was made, enabling
    deterministic replay and rollout tracking.
    """
    result = await extraction_service.get_version_snapshot_for_attempt(
        db, attempt_id, agency_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Extraction attempt {attempt_id} not found")
    return {"ok": True, "attempt": result}
