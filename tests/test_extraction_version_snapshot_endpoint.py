"""Tests for the extraction version snapshot API endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# VersionSnapshot unit tests (already in test_version_snapshot.py, but
# these verify the service integration path)
# ---------------------------------------------------------------------------

class TestVersionSnapshotService:
    """Tests for get_version_snapshot_for_attempt service function."""

    @pytest.mark.asyncio
    async def test_returns_snapshot_when_attempt_exists(self):
        """When the attempt exists and belongs to the agency, return the snapshot."""
        mock_attempt = MagicMock()
        mock_attempt.id = "att_001"
        mock_attempt.extraction_id = "ext_001"
        mock_attempt.trip_id = "trip_001"
        mock_attempt.provider_name = "openai"
        mock_attempt.model_name = "gpt-4o"
        mock_attempt.status = "success"
        mock_attempt.version_snapshot = {
            "prompt_version": "v2",
            "schema_version": "v1",
            "routing_version": "v1",
            "dictionary_version": "v1",
            "normalization_version": "v1",
            "captured_at": "2026-06-20T12:00:00Z",
        }
        mock_attempt.created_at = datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_attempt

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        from spine_api.services.extraction_service import get_version_snapshot_for_attempt
        result = await get_version_snapshot_for_attempt(mock_db, "att_001", "agency_001")

        assert result is not None
        assert result["attempt_id"] == "att_001"
        assert result["extraction_id"] == "ext_001"
        assert result["trip_id"] == "trip_001"
        assert result["provider_name"] == "openai"
        assert result["model_name"] == "gpt-4o"
        assert result["status"] == "success"
        assert result["version_snapshot"]["prompt_version"] == "v2"
        assert result["created_at"] == "2026-06-20T12:00:00+00:00"

    @pytest.mark.asyncio
    async def test_returns_none_when_attempt_not_found(self):
        """When the attempt doesn't exist, return None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        from spine_api.services.extraction_service import get_version_snapshot_for_attempt
        result = await get_version_snapshot_for_attempt(mock_db, "nonexistent", "agency_001")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_wrong_agency(self):
        """When the attempt belongs to a different agency, return None (RLS)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        from spine_api.services.extraction_service import get_version_snapshot_for_attempt
        result = await get_version_snapshot_for_attempt(mock_db, "att_001", "wrong_agency")

        assert result is None


class TestExtractionRouter:
    """Tests for the extraction router endpoints."""

    @staticmethod
    def _setup_app():
        """Build a test app with auth dependencies overridden."""
        from fastapi import FastAPI
        from spine_api.routers.extraction import router
        from spine_api.core.auth import get_current_membership
        from spine_api.core.rls import get_rls_db

        app = FastAPI()
        app.include_router(router)

        # Override get_current_membership — this is the single dependency that
        # both get_current_agency_id and require_permission chain through.
        # Returning a mock Membership with role="owner" grants all permissions.
        mock_membership = MagicMock()
        mock_membership.agency_id = "agency_001"
        mock_membership.role = "owner"
        mock_membership.user_id = "user_001"

        async def _fake_membership():
            return mock_membership

        async def _fake_db():
            return AsyncMock()

        app.dependency_overrides[get_current_membership] = _fake_membership
        app.dependency_overrides[get_rls_db] = _fake_db
        return app

    def test_version_snapshot_endpoint_returns_200(self):
        """GET /api/extractions/{attempt_id}/version-snapshot returns 200 with snapshot."""
        from fastapi.testclient import TestClient

        app = self._setup_app()

        mock_attempt = {
            "attempt_id": "att_001",
            "extraction_id": "ext_001",
            "trip_id": "trip_001",
            "provider_name": "openai",
            "model_name": "gpt-4o",
            "status": "success",
            "version_snapshot": {"prompt_version": "v2", "schema_version": "v1"},
            "created_at": "2026-06-20T12:00:00+00:00",
        }

        with patch("spine_api.services.extraction_service.get_version_snapshot_for_attempt", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_attempt

            client = TestClient(app)
            response = client.get("/api/extractions/att_001/version-snapshot")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["attempt"]["attempt_id"] == "att_001"
        assert data["attempt"]["version_snapshot"]["prompt_version"] == "v2"

    def test_version_snapshot_endpoint_returns_404(self):
        """GET /api/extractions/{attempt_id}/version-snapshot returns 404 when not found."""
        from fastapi.testclient import TestClient

        app = self._setup_app()

        with patch("spine_api.services.extraction_service.get_version_snapshot_for_attempt", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            client = TestClient(app)
            response = client.get("/api/extractions/nonexistent/version-snapshot")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
