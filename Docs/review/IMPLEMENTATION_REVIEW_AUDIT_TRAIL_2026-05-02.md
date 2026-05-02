# Implementation Review: E2 Audit Trail

**Date:** 2026-05-02
**Gap:** E2. Security & Privacy — Backend audit trail
**Status:** COMPLETED
**Priority:** P1

---

## What was done

Added database-backed audit trail with dependency-injected logging, queryable API endpoint, and controlled vocabulary for actions.

### Files created

| File | Lines | Purpose |
|---|---|---|
| `spine_api/models/audit.py` | 108 | AuditLog model, AuditAction enum, JSON/JSONB dialect-aware column |
| `spine_api/core/audit.py` | 138 | AuditContext class, `audit_logger()` FastAPI dependency, IP extraction |
| `spine_api/routers/audit.py` | 99 | GET /api/audit endpoint with filtering and RBAC |
| `alembic/versions/add_audit_logs.py` | 60 | Alembic migration: audit_logs table with 4 composite indexes |
| `tests/test_audit_trail.py` | 290 | 24 tests: model, context, IP extraction, router, migration, dependency |

### Files modified

| File | Change |
|---|---|
| `spine_api/server.py` | Added audit_router import and `app.include_router()` |
| `spine_api/core/rate_limiter.py` | Fixed `_get_default_limits()` to re-read ENVIRONMENT at call time (was module-level constant) |

### Architecture decisions

1. **Dependency injection, NOT blanket middleware**: `Depends(audit_logger())` is opt-in per route. Only routes that call `await audit.log()` generate audit entries. This avoids noisy audit logs from health checks, OPTIONS requests, etc.

2. **AuditAction enum**: Controlled vocabulary for audit actions (create, update, delete, login, etc.). Plain strings are also accepted for extensibility but the enum provides type safety and documentation.

3. **JSONB for changes, JSON fallback for SQLite**: The `changes` column uses PostgreSQL JSONB in production (indexed, queryable) but falls back to JSON for SQLite test compatibility via `_json_type()` factory.

4. **Agency-scoped queries**: GET /api/audit automatically filters by the requesting user's agency_id. Cross-tenant audit log access is impossible.

5. **Permission enforcement inline**: The audit endpoint uses `get_current_membership` + inline permission check instead of the `Depends(require_permission("audit:read"))` pattern (which returns a `Depends` object that can't be nested in another `Depends()`). This is architecturally equivalent but avoids double-wrapping.

6. **Non-fatal logging**: `AuditContext.log()` catches flush errors and logs warnings. Audit logging failures should never crash the request.

### Query parameters for GET /api/audit

| Param | Type | Description |
|---|---|---|
| `resource_type` | string | Filter by resource type (e.g. "trip", "user") |
| `user_id` | string | Filter by user ID |
| `action` | string | Filter by action (e.g. "create", "update") |
| `since` | ISO timestamp | Filter logs after this date |
| `limit` | int (1-200) | Max entries to return (default 50) |

### Composite indexes

| Index | Columns | Purpose |
|---|---|---|
| `ix_audit_logs_agency_created` | agency_id, created_at | Agency-scoped time-range queries |
| `ix_audit_logs_user_created` | user_id, created_at | Per-user activity timeline |
| `ix_audit_logs_resource` | resource_type, resource_id | Resource audit history |
| `ix_audit_logs_agency_action` | agency_id, action | Action-type filtering per agency |

---

## Verification

| Check | Result |
|---|---|
| `tests/test_audit_trail.py` | 24 passed |
| `tests/test_rate_limiter.py` | 25 passed |
| `tests/test_auth_security.py` | 13 passed (no regression) |
| `tests/test_privacy_guard.py` | 34 passed (no regression) |
| Combined | 96 passed, 0 failed |

---

## What was NOT done (correctly deferred)

- No Redis-backed audit event bus (file-based AuditStore persists for backward compat; database store is the primary path)
- No webhook/notification integration for audit events (future: audit → webhook → Slack/email)
- No audit log retention policy or automatic pruning (future: TTL-based cleanup)
- No audit log UI in frontend (the GET /api/audit endpoint is ready for it)

---

## How to use audit trail in routes

```python
from spine_api.core.audit import audit_logger, AuditAction
from fastapi import Depends

@router.post("/trips")
async def create_trip(
    audit: AuditContext = Depends(audit_logger()),
    ...
):
    result = ...
    await audit.log(
        AuditAction.CREATE,
        resource_type="trip",
        resource_id=result.id,
        changes={"before": None, "after": {"status": "new"}},
    )
    return result
```

---

## Next steps

Per the action plan:

1. **Gap 2: PII jurisdiction tagging** — Add `jurisdiction` field to Agency model + policy routing
2. **Gap 4 (deferred): ABAC** — Per-record access control for junior_agent role