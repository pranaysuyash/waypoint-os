"""
Integration registry and agency integration status service.

Design principles:
- Provider catalog is a code constant, not a DB table. Keeping it here
  makes the frontend and API deterministic without premature provider CRUD.
- AgencyIntegration DB rows store per-agency status/health only.
- Default records are synthesised for providers not yet in the DB so the
  API always returns the full supported set.
- Raw credentials are NEVER returned. credential_ref and config_json are
  internal fields that must never appear in public response shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from spine_api.models.tenant import AgencyIntegration, INTEGRATION_STATUSES

# ---------------------------------------------------------------------------
# Provider catalog — update here when adding or retiring provider support
# ---------------------------------------------------------------------------

SUPPORTED_PROVIDERS: dict[str, dict] = {
    "whatsapp": {
        "display_name": "WhatsApp",
        "capabilities": ["outbound_messages", "inbound_messages"],
        "category": "messaging",
    },
    "gmail": {
        "display_name": "Gmail",
        "capabilities": ["email_read", "email_send"],
        "category": "email",
    },
    "google_calendar": {
        "display_name": "Google Calendar",
        "capabilities": ["calendar_read", "calendar_write"],
        "category": "calendar",
    },
    "google_drive": {
        "display_name": "Google Drive",
        "capabilities": ["file_backup", "file_read"],
        "category": "storage",
    },
    "sms": {
        "display_name": "SMS",
        "capabilities": ["outbound_messages", "delivery_status"],
        "category": "messaging",
    },
    "telegram": {
        "display_name": "Telegram",
        "capabilities": ["outbound_messages", "inbound_messages"],
        "category": "messaging",
    },
}

# ---------------------------------------------------------------------------
# Output dataclass — safe for serialisation, no credentials
# ---------------------------------------------------------------------------

@dataclass
class IntegrationStatusOut:
    """Safe, credential-free integration status for API responses."""
    provider: str
    display_name: str
    enabled: bool
    status: str
    capabilities: list[str]
    category: str
    last_health_check_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_error_code: Optional[str]
    last_error_message_safe: Optional[str]
    updated_at: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "status": self.status,
            "capabilities": self.capabilities,
            "category": self.category,
            "last_health_check_at": (
                self.last_health_check_at.isoformat() if self.last_health_check_at else None
            ),
            "last_success_at": (
                self.last_success_at.isoformat() if self.last_success_at else None
            ),
            "last_error_code": self.last_error_code,
            "last_error_message_safe": self.last_error_message_safe,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _default_status(provider: str) -> IntegrationStatusOut:
    """Return a default disabled status for a provider with no DB record."""
    meta = SUPPORTED_PROVIDERS[provider]
    return IntegrationStatusOut(
        provider=provider,
        display_name=meta["display_name"],
        enabled=False,
        status="disabled",
        capabilities=list(meta["capabilities"]),
        category=meta["category"],
        last_health_check_at=None,
        last_success_at=None,
        last_error_code=None,
        last_error_message_safe=None,
        updated_at=None,
    )


def _row_to_status(row: AgencyIntegration) -> IntegrationStatusOut:
    """Convert a DB row to the safe output shape. credential_ref is excluded."""
    meta = SUPPORTED_PROVIDERS.get(row.provider, {})
    status = row.status if row.status in INTEGRATION_STATUSES else "misconfigured"
    return IntegrationStatusOut(
        provider=row.provider,
        display_name=meta.get("display_name", row.provider),
        enabled=row.enabled,
        status=status,
        capabilities=list(meta.get("capabilities", [])),
        category=meta.get("category", "other"),
        last_health_check_at=row.last_health_check_at,
        last_success_at=row.last_success_at,
        last_error_code=(
            row.last_error_code
            if row.status in INTEGRATION_STATUSES
            else "invalid_integration_status"
        ),
        last_error_message_safe=row.last_error_message_safe,
        updated_at=row.updated_at,
    )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def get_agency_integrations(
    agency_id: str,
    session: AsyncSession,
) -> list[IntegrationStatusOut]:
    """
    Return integration status for all supported providers for the given agency.

    Providers without a DB record get a default disabled status so the list
    is always complete and deterministic.
    """
    result = await session.execute(
        select(AgencyIntegration)
        .where(AgencyIntegration.agency_id == agency_id)
        .order_by(AgencyIntegration.provider)
    )
    rows = result.scalars().all()
    by_provider = {row.provider: row for row in rows}

    return [
        _row_to_status(by_provider[p]) if p in by_provider else _default_status(p)
        for p in sorted(SUPPORTED_PROVIDERS)
    ]


async def get_agency_integration(
    agency_id: str,
    provider: str,
    session: AsyncSession,
) -> Optional[IntegrationStatusOut]:
    """
    Return integration status for a single provider.

    Returns None if the provider is not in the supported catalog.
    Returns a default disabled status if no DB record exists yet.
    """
    if provider not in SUPPORTED_PROVIDERS:
        return None

    result = await session.execute(
        select(AgencyIntegration)
        .where(
            AgencyIntegration.agency_id == agency_id,
            AgencyIntegration.provider == provider,
        )
    )
    row = result.scalar_one_or_none()
    return _row_to_status(row) if row is not None else _default_status(provider)
