"""
Workspace router — workspace detail and update endpoints.

A workspace is the authenticated user's agency. These endpoints
read the agency_id from the JWT token, so no explicit agency_id
param is needed.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.database import get_db
from spine_api.core.auth import get_current_agency_id, get_current_membership
from spine_api.services.workspace_service import get_workspace, update_workspace, generate_workspace_code

logger = logging.getLogger("spine_api.workspace")

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)


@router.get("")
async def get_current_workspace(
    agency_id: str = Depends(get_current_agency_id),
    db: AsyncSession = Depends(get_db),
):
    workspace = await get_workspace(db, agency_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"ok": True, "workspace": workspace}


@router.patch("")
async def patch_current_workspace(
    request: WorkspaceUpdateRequest,
    agency_id: str = Depends(get_current_agency_id),
    db: AsyncSession = Depends(get_db),
):
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    workspace = await update_workspace(db, agency_id, updates)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"ok": True, "workspace": workspace}


class GenerateCodeRequest(BaseModel):
    code_type: str = Field(default="internal", pattern="^(internal|external)$")


@router.post("/codes")
async def post_generate_workspace_code(
    request: GenerateCodeRequest,
    membership=Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new workspace invitation code. Marks the old code inactive."""
    new_code = await generate_workspace_code(
        db,
        agency_id=membership.agency_id,
        created_by=membership.user_id,
        code_type=request.code_type,
    )
    return {"ok": True, "code": new_code}
