"""Tests for spine_api.core.audit_bridge — sync-compatible dual-write audit logging."""

import pytest
from unittest.mock import patch, MagicMock

from spine_api.core.audit_bridge import audit, _schedule_sql_write, _write_to_sql


class FakeAsyncSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, traceback):
        return None


class AsyncCallRecorder:
    def __init__(self, side_effect=None):
        self.side_effect = side_effect
        self.call_count = 0

    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        if self.side_effect:
            raise self.side_effect

    def assert_awaited_once(self):
        assert self.call_count == 1


class TestAuditBridgeFunction:
    """Test the audit() function writes to file store and schedules SQL write."""

    def test_audit_writes_to_legacy_store(self):
        """audit() should always call AuditStore.log_event()."""
        with patch("spine_api.core.audit_bridge.AuditStore") as mock_store:
            audit("draft_created", user_id="user1", agency_id="agency1", changes={"key": "val"})

        mock_store.log_event.assert_called_once_with("draft_created", "user1", {"key": "val"})

    def test_audit_defaults_user_to_system(self):
        """audit() should default user_id to 'system' if not provided."""
        with patch("spine_api.core.audit_bridge.AuditStore"):
            with patch("spine_api.core.audit_bridge._schedule_sql_write") as mock_schedule:
                audit("test_event")

        mock_schedule.assert_called_once()
        call_kwargs = mock_schedule.call_args[1]
        assert call_kwargs["user_id"] == "system"
        assert call_kwargs["agency_id"] == "system"

    def test_audit_schedules_sql_write(self):
        """audit() should schedule a SQL write in addition to legacy write."""
        with patch("spine_api.core.audit_bridge.AuditStore"):
            with patch("spine_api.core.audit_bridge._schedule_sql_write") as mock_schedule:
                audit(
                    "draft_promoted",
                    user_id="user1",
                    agency_id="agency1",
                    resource_type="draft",
                    resource_id="d1",
                    changes={"status": "promoted"},
                )

        mock_schedule.assert_called_once()
        call_kwargs = mock_schedule.call_args[1]
        assert call_kwargs["action"] == "draft_promoted"
        assert call_kwargs["user_id"] == "user1"
        assert call_kwargs["agency_id"] == "agency1"
        assert call_kwargs["resource_type"] == "draft"
        assert call_kwargs["resource_id"] == "d1"
        assert call_kwargs["changes"] == {"status": "promoted"}

    def test_audit_legacy_failure_is_non_fatal(self):
        """audit() should not raise if AuditStore.log_event() fails."""
        with patch("spine_api.core.audit_bridge.AuditStore") as mock_store:
            mock_store.log_event.side_effect = RuntimeError("file store down")
            with patch("spine_api.core.audit_bridge._schedule_sql_write"):
                # Should not raise
                audit("test_event")

    def test_audit_passes_all_fields(self):
        """audit() should pass ip_address and user_agent to _schedule_sql_write."""
        with patch("spine_api.core.audit_bridge.AuditStore"):
            with patch("spine_api.core.audit_bridge._schedule_sql_write") as mock_schedule:
                audit(
                    "login",
                    user_id="u1",
                    agency_id="a1",
                    resource_type="session",
                    resource_id="s1",
                    changes={"method": "password"},
                    ip_address="10.0.0.1",
                    user_agent="Mozilla/5.0",
                )

        call_kwargs = mock_schedule.call_args[1]
        assert call_kwargs["ip_address"] == "10.0.0.1"
        assert call_kwargs["user_agent"] == "Mozilla/5.0"


class TestScheduleSQLWrite:
    """Test _schedule_sql_write handles event loop availability."""

    def test_schedule_with_running_loop(self):
        """When an event loop is running, schedules via run_coroutine_threadsafe."""
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        with patch("spine_api.core.audit_bridge.asyncio.get_running_loop", return_value=mock_loop), \
             patch("spine_api.core.audit_bridge.asyncio.run_coroutine_threadsafe") as mock_run_threadsafe, \
             patch("spine_api.core.audit_bridge._write_to_sql", new=MagicMock(return_value=object())):

            _schedule_sql_write(
                action="test",
                user_id="u1",
                agency_id="a1",
                resource_type=None,
                resource_id=None,
                changes=None,
                ip_address=None,
                user_agent=None,
            )

        mock_run_threadsafe.assert_called_once()
        scheduled_payload = mock_run_threadsafe.call_args[0][0]
        assert scheduled_payload is not None

    def test_schedule_without_running_loop_in_dev(self):
        """In dev/test, missing event loop is silently skipped."""
        with patch("spine_api.core.audit_bridge.asyncio.get_running_loop", side_effect=RuntimeError("no loop")), \
             patch("spine_api.core.audit_bridge.asyncio.run_coroutine_threadsafe") as mock_run_threadsafe:
            # _IS_DEV or _IS_TEST should be True in test env
            _schedule_sql_write(
                action="test",
                user_id="u1",
                agency_id="a1",
                resource_type=None,
                resource_id=None,
                changes=None,
                ip_address=None,
                user_agent=None,
            )
        mock_run_threadsafe.assert_not_called()

    def test_schedule_fallback_creates_loop(self, monkeypatch):
        """If no running loop and not dev/test, creates one via asyncio.run."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        with patch("spine_api.core.audit_bridge.asyncio.get_running_loop", side_effect=RuntimeError("no loop")), \
             patch("spine_api.core.audit_bridge.asyncio.run") as mock_run, \
             patch("spine_api.core.audit_bridge._write_to_sql", new=MagicMock(return_value=object())):
            _schedule_sql_write(
                action="test",
                user_id="u1",
                agency_id="a1",
                resource_type=None,
                resource_id=None,
                changes=None,
                ip_address=None,
                user_agent=None,
            )
            mock_run.assert_called_once()


class TestWriteToSQL:
    """Test _write_to_sql creates an AuditLog entry."""

    @pytest.mark.asyncio
    async def test_write_creates_audit_log_entry(self):
        """_write_to_sql should create and commit an AuditLog entry."""
        with patch("spine_api.core.database.async_session_maker") as mock_session_maker:
            mock_session = MagicMock()
            mock_session.commit = AsyncCallRecorder()
            mock_session_maker.return_value = FakeAsyncSessionContext(mock_session)

            await _write_to_sql(
                action="draft_created",
                user_id="u1",
                agency_id="a1",
                resource_type="draft",
                resource_id="d1",
                changes={"key": "val"},
                ip_address="10.0.0.1",
                user_agent="TestAgent",
            )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_write_failure_is_non_fatal(self):
        """_write_to_sql should not raise if DB commit fails."""
        with patch("spine_api.core.database.async_session_maker") as mock_session_maker:
            mock_session = MagicMock()
            mock_session.commit = AsyncCallRecorder(side_effect=RuntimeError("DB down"))
            mock_session_maker.return_value = FakeAsyncSessionContext(mock_session)

            # Should not raise
            await _write_to_sql(
                action="test",
                user_id="u1",
                agency_id="a1",
                resource_type=None,
                resource_id=None,
                changes=None,
                ip_address=None,
                user_agent=None,
            )
