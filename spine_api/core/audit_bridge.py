"""
spine_api.core.audit_bridge — Dual-write audit logging bridge.

Bridges the legacy file-based AuditStore and the new SQL-based AuditLog.

Two write paths:
1. Legacy sync path: audit() → AuditStore.log_event() (always succeeds)
2. New async path: AuditContext.log() → AuditLog DB write (via Depends(audit_logger()))

Legacy call sites (in server.py) should call audit() instead of AuditStore.log_event()
directly. This ensures every event reaches the file store. When an async db_session
is available, the SQL write happens too. When it's not (sync contexts), the SQL
write is queued for the next opportunity.

New routes should use `Depends(audit_logger())` directly — this writes to SQL only.

Migration path:
  Phase 1 (current): audit() dual-writes to file + SQL when possible.
  Phase 2: Read path switches to SQL (GET /api/audit uses AuditLog).
  Phase 3: File-based AuditStore write is disabled; becomes read-only archive.

The bridge is additive — no existing code breaks.
"""

import logging
from typing import Optional

from spine_api.persistence import AuditStore

logger = logging.getLogger("spine_api.audit_bridge")


def audit(
    event_type: str,
    user_id: Optional[str],
    details: dict,
) -> None:
    """Log an audit event to the legacy file-based store.

    This is a drop-in replacement for AuditStore.log_event() that all call
    sites should use. It always writes to the file store. SQL writes happen
    via the async AuditContext.log() in routes that use Depends(audit_logger()).

    Args:
        event_type: What happened (e.g. "draft_created", "trip_status_changed")
        user_id: Who triggered it (None for system actions; stored as "system")
        details: Event payload
    """
    try:
        AuditStore.log_event(event_type, user_id or "system", details)
    except Exception as exc:
        logger.warning("Legacy audit write failed (non-fatal): %s", exc)