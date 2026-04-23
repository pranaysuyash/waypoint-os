"""
Workspace service — workspace CRUD and code generation.

In Waypoint OS, a "workspace" is synonymous with an Agency.
This service handles workspace detail retrieval and updates.
"""

import secrets
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Agency, WorkspaceCode

logger = logging.getLogger("spine-api.workspace_service")


async def get_workspace(db: AsyncSession, agency_id: str) -> Optional[dict]:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        return None

    code_result = await db.execute(
        select(WorkspaceCode)
        .where(WorkspaceCode.agency_id == agency.id)
        .where(WorkspaceCode.status == "active")
        .order_by(WorkspaceCode.created_at.desc())
        .limit(1)
    )
    active_code = code_result.scalar_one_or_none()

    return {
        "id": agency.id,
        "name": agency.name,
        "slug": agency.slug,
        "email": agency.email,
        "phone": agency.phone,
        "logo_url": agency.logo_url,
        "plan": agency.plan,
        "settings": agency.settings or {},
        "workspace_code": active_code.code if active_code else None,
    }


async def update_workspace(
    db: AsyncSession,
    agency_id: str,
    updates: dict,
) -> Optional[dict]:
    result = await db.execute(select(Agency).where(Agency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        return None

    allowed_fields = {"name", "email", "phone", "logo_url"}
    changed = []
    for field, value in updates.items():
        if field in allowed_fields and value is not None:
            setattr(agency, field, value)
            changed.append(field)

    if changed:
        await db.commit()
        await db.refresh(agency)
        logger.info("Workspace updated: agency=%s fields=%s", agency_id, changed)

    return await get_workspace(db, agency_id)


async def generate_workspace_code(
    db: AsyncSession,
    agency_id: str,
    created_by: str,
    code_type: str = "internal",
) -> str:
    code = WorkspaceCode(
        agency_id=agency_id,
        code=f"WP-{secrets.token_urlsafe(8)}",
        code_type=code_type,
        status="active",
        created_by=created_by,
    )
    db.add(code)
    await db.commit()
    await db.refresh(code)

    logger.info("Workspace code generated: agency=%s code=%s", agency_id, code.code)
    return code.code
