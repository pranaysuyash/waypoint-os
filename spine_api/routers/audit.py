"""
spine_api.routers.audit — Audit trail query endpoints.

Provides:
- GET /api/audit — List audit log entries with filtering
  Query params: resource_type, user_id, action, since (ISO timestamp), limit (max 200)

Access control:
- Owner/admin roles can view audit logs for their agency
- Junior agents and viewers cannot access audit logs
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.auth import get_current_membership
from spine_api.core.database import get_db
from spine_api.models.audit import AuditLog
from spine_api.models.tenant import Membership

logger = logging.getLogger("spine_api.audit_router")

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogEntry(BaseModel):
    id: str
    agency_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    changes: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None


class AuditListResponse(BaseModel):
    ok: bool = True
    entries: list[AuditLogEntry]
    total: int


@router.get("", response_model=AuditListResponse)
async def list_audit_logs(
    resource_type: Optional[str] = Query(default=None, max_length=100),
    user_id: Optional[str] = Query(default=None, max_length=36),
    action: Optional[str] = Query(default=None, max_length=50),
    since: Optional[str] = Query(default=None, description="ISO timestamp for filtering logs after this date"),
    limit: int = Query(default=50, ge=1, le=200),
    membership: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
):
    """List audit log entries for the current agency.

    Requires owner or admin role (audit:read permission).
    Results are scoped to the requesting user's agency.
    """
    from spine_api.core.auth import ROLE_PERMISSIONS

    role = membership.role.lower()
    permissions = ROLE_PERMISSIONS.get(role, [])
    if "*" not in permissions and "audit:read" not in permissions:
        raise HTTPException(
            status_code=403,
            detail="Permission denied: audit:read",
        )

    filters = [AuditLog.agency_id == membership.agency_id]

    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if action:
        filters.append(AuditLog.action == action)
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            filters.append(AuditLog.created_at >= since_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid since timestamp: {since}")

    stmt = (
        select(AuditLog)
        .where(and_(*filters))
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    return AuditListResponse(
        ok=True,
        entries=[
            AuditLogEntry(
                id=e.id,
                agency_id=e.agency_id,
                user_id=e.user_id,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                changes=e.changes,
                ip_address=e.ip_address,
                user_agent=e.user_agent,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
            for e in entries
        ],
        total=len(entries),
    )