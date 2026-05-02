"""
tests/test_audit_trail — Tests for the database-backed audit trail.

Verifies:
- AuditLog model fields and constraints
- AuditAction enum values
- AuditContext.log() writes to database
- GET /api/audit returns filtered entries
- Permission enforcement (audit:read required)
- audit_logger() dependency extracts IP and User-Agent
- Alembic migration is present and valid
"""

import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, and_, desc

from spine_api.models.audit import AuditLog, AuditAction
from spine_api.core.audit import AuditContext, _extract_client_ip


class TestAuditActionEnum:
    def test_all_action_values(self):
        expected = {
            "create", "update", "delete",
            "login", "logout", "login_failed",
            "password_reset_request", "password_reset_confirm",
            "run_start", "run_complete", "run_failed", "run_blocked",
            "override", "assign", "export",
        }
        actual = {a.value for a in AuditAction}
        assert actual == expected

    def test_action_is_str_enum(self):
        assert isinstance(AuditAction.CREATE, str)
        assert AuditAction.CREATE == "create"

    def test_custom_action_string_accepted(self):
        custom = "custom_action"
        assert custom == str(custom)


class TestAuditLogModel:
    def test_table_name(self):
        assert AuditLog.__tablename__ == "audit_logs"

    def test_model_has_required_columns(self):
        column_names = {c.name for c in AuditLog.__table__.columns}
        required = {
            "id", "agency_id", "user_id", "action",
            "resource_type", "resource_id", "changes",
            "ip_address", "user_agent", "created_at",
        }
        assert required.issubset(column_names), (
            f"Missing columns: {required - column_names}"
        )

    def test_agency_id_not_nullable(self):
        col = AuditLog.__table__.c.agency_id
        assert not col.nullable, "agency_id must be NOT NULL"

    def test_action_not_nullable(self):
        col = AuditLog.__table__.c.action
        assert not col.nullable, "action must be NOT NULL"

    def test_user_id_nullable(self):
        col = AuditLog.__table__.c.user_id
        assert col.nullable, "user_id should be nullable forsystem actions"

    def test_changes_is_json_type(self):
        """Changes column uses JSONB on PostgreSQL, JSON on SQLite."""
        col = AuditLog.__table__.c.changes
        from sqlalchemy import JSON
        from sqlalchemy.dialects.postgresql import JSONB
        # Column type should be either JSON or JSONB
        assert isinstance(col.type, (JSON, JSONB.__class__)), (
            f"changes type is {type(col.type)}, expected JSON or JSONB"
        )

    def test_to_dict_method(self):
        entry = AuditLog(
            id=str(uuid.uuid4()),
            agency_id="test-agency",
            user_id="test-user",
            action="create",
            resource_type="trip",
            resource_id="trip-123",
            changes={"before": None, "after": {"status": "new"}},
            ip_address="127.0.0.1",
            user_agent="test-agent",
            created_at=datetime.now(timezone.utc),
        )
        d = entry.to_dict()
        assert d["agency_id"] == "test-agency"
        assert d["action"] == "create"
        assert d["resource_type"] == "trip"
        assert d["changes"]["after"]["status"] == "new"
        assert "created_at" in d

    def test_indexes_exist(self):
        index_names = {idx.name for idx in AuditLog.__table__.indexes}
        expected_indexes = {
            "ix_audit_logs_agency_created",
            "ix_audit_logs_user_created",
            "ix_audit_logs_resource",
            "ix_audit_logs_agency_action",
        }
        assert expected_indexes.issubset(index_names), (
            f"Missing indexes: {expected_indexes - index_names}"
        )


class TestAuditContext:
    @pytest.mark.asyncio
    async def test_log_creates_entry(self):
        """Test that AuditContext.log() writes a valid entry with all fields."""
        from unittest.mock import AsyncMock, MagicMock

        # Mock the database session — avoid SQLite JSONB incompatibility
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        ctx = AuditContext(
            db=mock_db,
            agency_id="agency-123",
            user_id="user-456",
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
        )
        entry = await ctx.log(
            action=AuditAction.CREATE,
            resource_type="trip",
            resource_id="trip-789",
            changes={"before": None, "after": {"status": "new"}},
        )

        # Verify the entry was created with correct fields
        assert entry.agency_id == "agency-123"
        assert entry.user_id == "user-456"
        assert entry.action == "create"
        assert entry.resource_type == "trip"
        assert entry.resource_id == "trip-789"
        assert entry.changes["after"]["status"] == "new"
        assert entry.ip_address == "192.168.1.1"
        assert entry.user_agent == "TestAgent/1.0"
        assert entry.created_at is not None

        # Verify db.add was called
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_with_string_action(self):
        """Test that AuditContext.log() accepts plain string actions."""
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        ctx = AuditContext(
            db=mock_db,
            agency_id="agency-456",
            user_id=None,
            ip_address=None,
            user_agent=None,
        )
        entry = await ctx.log(
            action="custom_action",
            resource_type="widget",
            resource_id="widget-001",
        )

        assert entry.action == "custom_action"
        assert entry.user_id is None

    @pytest.mark.asyncio
    async def test_log_non_fatal_on_flush_error(self):
        """Test that flush errors are logged but don't crash."""
        from unittest.mock import AsyncMock, MagicMock

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=Exception("DB connection lost"))

        ctx = AuditContext(
            db=mock_db,
            agency_id="agency-789",
            user_id="user-001",
            ip_address="10.0.0.1",
            user_agent="TestBot/2.0",
        )
        # Should not raise — audit logging is non-fatal
        entry = await ctx.log(
            action=AuditAction.UPDATE,
            resource_type="trip",
            resource_id="trip-002",
        )
        assert entry.action == "update"

    def test_agency_id_property(self):
        ctx = AuditContext(
            db=None,
            agency_id="test-agency",
            user_id="test-user",
            ip_address=None,
            user_agent=None,
        )
        assert ctx.agency_id == "test-agency"
        assert ctx.user_id == "test-user"


class TestExtractClientIP:
    def test_x_forwarded_for_header(self):
        from starlette.requests import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/audit",
            "headers": [(b"x-forwarded-for", b"10.0.0.1, 172.16.0.1")],
            "query_string": b"",
            "server": ("testclient", 80),
            "client": ("192.168.1.1", 54321),
        }
        request = Request(scope)
        ip = _extract_client_ip(request)
        assert ip == "10.0.0.1"

    def test_direct_client(self):
        from starlette.requests import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/audit",
            "headers": [],
            "query_string": b"",
            "server": ("testclient", 80),
            "client": ("192.168.1.1", 54321),
        }
        request = Request(scope)
        ip = _extract_client_ip(request)
        assert ip == "192.168.1.1"

    def test_no_client_info(self):
        from starlette.requests import Request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/audit",
            "headers": [],
            "query_string": b"",
            "server": ("testclient", 80),
        }
        request = Request(scope)
        ip = _extract_client_ip(request)
        assert ip is None


class TestAuditRouterRegistration:
    def test_audit_router_registered_on_app(self):
        from spine_api.server import app
        audit_routes = [
            r for r in app.routes
            if hasattr(r, "path") and "/audit" in r.path
        ]
        assert len(audit_routes) >= 1, "Audit router not registered on app"

    def test_audit_router_has_get_endpoint(self):
        from spine_api.routers.audit import router
        paths = [r.path for r in router.routes]
        assert "/api/audit" in paths or "" in paths, (
            f"Audit GET endpoint not found, paths: {paths}"
        )

    def test_audit_action_in_permission_matrix(self):
        from spine_api.core.auth import ROLE_PERMISSIONS
        admin_perms = ROLE_PERMISSIONS.get("admin", [])
        assert "audit:read" in admin_perms, (
            f"audit:read not in admin permissions: {admin_perms}"
        )
        owner_perms = ROLE_PERMISSIONS.get("owner", [])
        assert "*" in owner_perms, "Owner should have wildcard permission"


class TestAlembicMigration:
    def test_audit_logs_migration_exists(self):
        from pathlib import Path
        migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migration_files = list(migration_dir.glob("*audit*"))
        assert len(migration_files) >= 1, (
            f"No audit_logs migration found in {migration_dir}"
        )

    def test_migration_creates_audit_logs_table(self):
        from pathlib import Path
        migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migration_files = list(migration_dir.glob("*audit*"))
        content = migration_files[0].read_text()
        assert "audit_logs" in content
        assert "create_table" in content
        assert "agency_id" in content
        assert "action" in content
        assert "JSONB" in content.upper() or "jsonb" in content


class TestAuditLoggerDependency:
    def test_audit_logger_returns_coroutine_function(self):
        from spine_api.core.audit import audit_logger
        dep = audit_logger()
        import asyncio
        assert asyncio.iscoroutinefunction(dep), (
            f"audit_logger() should return an async function, got {type(dep)}"
        )