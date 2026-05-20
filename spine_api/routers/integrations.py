"""
Integrations router — read-only agency integration status.

Endpoints:
  GET /api/integrations           — list all supported providers with agency status
  GET /api/integrations/{provider} — single provider status or 404

Auth model:
  All routes require JWT auth (registered with _auth_or_skip in server.py).
  Agency scoping: agency_id from JWT membership, never from request body or path.

Security contract:
  Responses are built from IntegrationStatusOut which excludes credential_ref
  and config_json by construction. Raw credentials must never appear here.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.core.database import get_db
from spine_api.core.auth import get_current_agency_id
from spine_api.services.integration_registry import (
    get_agency_integrations,
    get_agency_integration,
)

logger = logging.getLogger("spine_api.integrations")

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


async def _agency_scoped_db(
    agency_id: str = Depends(get_current_agency_id),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, AsyncSession]:
    """
    Resolve the current agency_id and explicitly set the RLS session context.

    This avoids relying on the ContextVar from get_current_membership, which may
    not be populated when the dependency chain is partially overridden in tests.
    Using set_config directly mirrors the _rls_session_for_agency pattern.
    """
    await db.execute(
        text("SELECT set_config('app.current_agency_id', :agency_id, false)"),
        {"agency_id": agency_id},
    )
    return agency_id, db


@router.get("")
async def list_integrations(
    ctx: tuple = Depends(_agency_scoped_db),
) -> dict:
    """List integration status for all supported providers for the current agency."""
    agency_id, db = ctx
    integrations = await get_agency_integrations(agency_id=agency_id, session=db)
    return {
        "integrations": [i.to_dict() for i in integrations],
        "total": len(integrations),
    }


@router.get("/{provider}")
async def get_integration(
    provider: str,
    ctx: tuple = Depends(_agency_scoped_db),
) -> dict:
    """Get integration status for a single provider. Returns 404 for unsupported providers."""
    agency_id, db = ctx
    status = await get_agency_integration(
        agency_id=agency_id, provider=provider, session=db
    )
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' is not supported.",
        )
    return status.to_dict()
