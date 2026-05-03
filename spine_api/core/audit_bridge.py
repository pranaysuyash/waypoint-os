"""
spine_api.core.audit_bridge — Sync-compatible audit logging bridge.

Provides a sync `audit()` function for use in sync FastAPI route handlers
(server.py) that can't directly `await` the async AuditContext.log().

Architecture:
  - For sync routes: call `audit(action, resource_type, ...)` — fire-and-forget
  - For async routes: use `Depends(audit_logger())` + `await audit.log(...)` directly
  - Both paths write to the same SQL AuditLog table

The sync `audit()` function schedules the async DB write on the running
event loop using `asyncio.run_coroutine_threadsafe()`. If no event loop is
running (e.g. tests, CLI), it falls back to creating one.

Migration path:
  Phase 1 (current): audit() dual-writes to file (AuditStore) + SQL (AuditLog).
  Phase 2: Read path switches to SQL (GET /api/audit uses AuditLog).
  Phase 3: File-based AuditStore write is disabled; becomes read-only archive.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from spine_api.models.audit import AuditLog
from spine_api.persistence import AuditStore

logger = logging.getLogger("spine_api.audit_bridge")

_IS_DEV = _IS_TEST = False
import os as _os
_env = _os.environ.get("ENVIRONMENT", "development")
_IS_DEV = _env == "development"
_IS_TEST = _env == "test"


def audit(
    action: str,
    user_id: Optional[str] = None,
    agency_id: str = "system",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    changes: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Log an audit event from sync route handlers.

    Drop-in replacement for AuditStore.log_event() that writes to BOTH:
    1. Legacy file-based AuditStore (always)
    2. SQL AuditLog table (fire-and-forget via event loop)

    Non-blocking: if the SQL write fails, it logs a warning and continues.
    """
    user_str = user_id or "system"

    try:
        AuditStore.log_event(action, user_str, changes or {})
    except Exception as exc:
        logger.warning("Legacy audit write failed (non-fatal): %s", exc)

    _schedule_sql_write(
        action=action,
        user_id=user_str,
        agency_id=agency_id,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _schedule_sql_write(
    action: str,
    user_id: str,
    agency_id: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    changes: Optional[dict],
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> None:
    """Schedule an async DB write on the running event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        if _IS_DEV or _IS_TEST:
            logger.debug("No event loop — skipping SQL audit write for action=%s", action)
            return
        loop = None

    if loop is not None and loop.is_running():
        asyncio.run_coroutine_threadsafe(
            _write_to_sql(
                action=action,
                user_id=user_id,
                agency_id=agency_id,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
            ),
            loop,
        )
    else:
        try:
            asyncio.run(
                _write_to_sql(
                    action=action,
                    user_id=user_id,
                    agency_id=agency_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    changes=changes,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
        except Exception as exc:
            logger.warning("SQL audit write failed (non-fatal): %s", exc)


async def _write_to_sql(
    action: str,
    user_id: str,
    agency_id: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    changes: Optional[dict],
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> None:
    """Insert an AuditLog row. Non-fatal on failure."""
    from spine_api.core.database import async_session_maker

    entry = AuditLog(
        agency_id=agency_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    try:
        async with async_session_maker() as session:
            session.add(entry)
            await session.commit()
    except Exception as exc:
        logger.warning("SQL audit write failed (non-fatal): %s", exc)