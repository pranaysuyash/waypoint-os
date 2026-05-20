"""
Backend tests for the read-only integrations API and registry service.

The tests intentionally avoid direct writes/deletes against the shared
waypoint_os database. API tests override the FastAPI dependencies; service
tests use tiny fake sessions so the integration contract remains additive.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import server
from server import app
from spine_api.core.auth import get_current_agency_id
from spine_api.core.database import get_db
from spine_api.routers import integrations as integrations_router
from spine_api.services import integration_registry
from spine_api.services.integration_registry import SUPPORTED_PROVIDERS


TEST_AGENCY_ID = "agency_test_integrations"
OTHER_AGENCY_ID = "agency_other_integrations"


class _FakeScalars:
    def __init__(self, rows: list[SimpleNamespace]):
        self._rows = rows

    def all(self) -> list[SimpleNamespace]:
        return list(self._rows)


class _FakeResult:
    def __init__(self, rows: list[SimpleNamespace]):
        self._rows = rows

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._rows)

    def scalar_one_or_none(self) -> SimpleNamespace | None:
        return self._rows[0] if self._rows else None


class _FakeSession:
    """Small async session double for set_config plus select-style queries."""

    def __init__(self, rows_by_agency: dict[str, list[SimpleNamespace]] | None = None):
        self.rows_by_agency = rows_by_agency or {}
        self.current_agency_id: str | None = None

    async def execute(self, statement, params=None):  # noqa: ANN001 - SQLAlchemy accepts many shapes
        if params and "agency_id" in params:
            self.current_agency_id = params["agency_id"]
            return _FakeResult([])

        agency_id = self.current_agency_id or _extract_agency_id(statement)
        rows = list(self.rows_by_agency.get(agency_id or "", []))
        provider = _extract_provider(statement)
        if provider is not None:
            rows = [row for row in rows if row.provider == provider]
        return _FakeResult(rows)


def _extract_provider(statement) -> str | None:  # noqa: ANN001 - SQLAlchemy expression internals
    """Pull the bound provider value out of the SQLAlchemy where criteria."""
    return _extract_where_value(statement, "provider")


def _extract_agency_id(statement) -> str | None:  # noqa: ANN001 - SQLAlchemy expression internals
    """Pull the bound agency id out of the SQLAlchemy where criteria."""
    return _extract_where_value(statement, "agency_id")


def _extract_where_value(statement, column_name: str) -> str | None:  # noqa: ANN001
    for criterion in getattr(statement, "_where_criteria", ()):
        left = getattr(criterion, "left", None)
        if getattr(left, "name", None) != column_name:
            continue
        right = getattr(criterion, "right", None)
        value = getattr(right, "value", None)
        if isinstance(value, str):
            return value
    return None


def _integration_row(
    *,
    agency_id: str = TEST_AGENCY_ID,
    provider: str = "gmail",
    enabled: bool = True,
    status: str = "connected",
) -> SimpleNamespace:
    return SimpleNamespace(
        agency_id=agency_id,
        provider=provider,
        enabled=enabled,
        status=status,
        config_json={"safe_region": "in"},
        credential_ref="secret/ref/that/must/not/leak",
        last_health_check_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        last_success_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        last_error_code=None,
        last_error_message_safe=None,
        updated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
    )


@pytest.fixture()
def fake_db():
    return _FakeSession()


@pytest.fixture(autouse=True)
def override_integration_dependencies(fake_db):
    original = dict(app.dependency_overrides)

    async def _db_override():
        yield fake_db

    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[get_current_agency_id] = lambda: TEST_AGENCY_ID
    app.dependency_overrides[server._auth_or_skip] = lambda: None
    try:
        yield
    finally:
        app.dependency_overrides = original


class TestIntegrationsApi:
    def test_list_requires_valid_auth(self, session_client):
        app.dependency_overrides.pop(server._auth_or_skip, None)
        resp = session_client.get(
            "/api/integrations",
            headers={"Authorization": "Bearer definitely-invalid"},
        )
        assert resp.status_code == 401

    def test_list_returns_all_supported_providers_with_default_disabled_status(
        self, session_client
    ):
        resp = session_client.get("/api/integrations")

        assert resp.status_code == 200
        data = resp.json()
        returned_providers = {item["provider"] for item in data["integrations"]}
        assert returned_providers == set(SUPPORTED_PROVIDERS)
        assert data["total"] == len(SUPPORTED_PROVIDERS)
        assert all(item["enabled"] is False for item in data["integrations"])
        assert all(item["status"] == "disabled" for item in data["integrations"])

    def test_list_response_shape_has_no_secret_fields(self, session_client):
        resp = session_client.get("/api/integrations")

        assert resp.status_code == 200
        expected_fields = {
            "provider",
            "display_name",
            "enabled",
            "status",
            "capabilities",
            "category",
            "last_health_check_at",
            "last_success_at",
            "last_error_code",
            "last_error_message_safe",
            "updated_at",
        }
        for item in resp.json()["integrations"]:
            assert expected_fields <= set(item)
            assert "credential_ref" not in item
            assert "config_json" not in item
            assert isinstance(item["capabilities"], list)
            assert item["category"]

    def test_detail_returns_known_provider_default(self, session_client):
        resp = session_client.get("/api/integrations/whatsapp")

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "whatsapp"
        assert data["enabled"] is False
        assert data["status"] == "disabled"
        assert "outbound_messages" in data["capabilities"]
        assert "credential_ref" not in data
        assert "config_json" not in data

    def test_detail_unknown_provider_returns_404(self, session_client):
        resp = session_client.get("/api/integrations/unsupported_xyz")

        assert resp.status_code == 404

    def test_route_uses_authenticated_agency_scope(
        self, session_client, monkeypatch, fake_db
    ):
        seen: dict[str, str] = {}

        async def fake_list(*, agency_id: str, session):
            seen["agency_id"] = agency_id
            seen["session_is_fake"] = str(session is fake_db)
            return [integration_registry._default_status("gmail")]

        monkeypatch.setattr(integrations_router, "get_agency_integrations", fake_list)

        resp = session_client.get("/api/integrations")

        assert resp.status_code == 200
        assert seen == {"agency_id": TEST_AGENCY_ID, "session_is_fake": "True"}


class TestIntegrationRegistryService:
    @pytest.mark.asyncio
    async def test_service_list_returns_complete_supported_catalog(self):
        session = _FakeSession()

        result = await integration_registry.get_agency_integrations(
            agency_id=TEST_AGENCY_ID,
            session=session,
        )

        assert {item.provider for item in result} == set(SUPPORTED_PROVIDERS)
        assert all(item.status == "disabled" for item in result)

    @pytest.mark.asyncio
    async def test_service_db_record_overrides_default_without_leaking_secrets(self):
        session = _FakeSession(
            {TEST_AGENCY_ID: [_integration_row(provider="gmail", status="degraded")]}
        )

        result = await integration_registry.get_agency_integrations(
            agency_id=TEST_AGENCY_ID,
            session=session,
        )

        gmail = next(item for item in result if item.provider == "gmail")
        payload = gmail.to_dict()
        assert payload["enabled"] is True
        assert payload["status"] == "degraded"
        assert "credential_ref" not in payload
        assert "config_json" not in payload

    @pytest.mark.asyncio
    async def test_service_tenant_isolation_uses_requested_agency(self):
        session = _FakeSession(
            {
                TEST_AGENCY_ID: [_integration_row(provider="telegram", enabled=True)],
                OTHER_AGENCY_ID: [
                    _integration_row(
                        agency_id=OTHER_AGENCY_ID,
                        provider="telegram",
                        enabled=False,
                        status="disabled",
                    )
                ],
            }
        )

        result = await integration_registry.get_agency_integrations(
            agency_id=OTHER_AGENCY_ID,
            session=session,
        )

        telegram = next(item for item in result if item.provider == "telegram")
        assert telegram.enabled is False
        assert telegram.status == "disabled"

    @pytest.mark.asyncio
    async def test_service_detail_returns_none_for_unsupported_provider(self):
        session = _FakeSession()

        result = await integration_registry.get_agency_integration(
            agency_id=TEST_AGENCY_ID,
            provider="unsupported_xyz",
            session=session,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_service_detail_uses_record_for_known_provider(self):
        session = _FakeSession({TEST_AGENCY_ID: [_integration_row(provider="sms")]})

        result = await integration_registry.get_agency_integration(
            agency_id=TEST_AGENCY_ID,
            provider="sms",
            session=session,
        )

        assert result is not None
        assert result.provider == "sms"
        assert result.enabled is True
        assert result.status == "connected"

    @pytest.mark.asyncio
    async def test_service_malformed_status_is_safe_misconfigured_response(self):
        session = _FakeSession(
            {
                TEST_AGENCY_ID: [
                    _integration_row(provider="gmail", status="plaintext_token_leak")
                ]
            }
        )

        result = await integration_registry.get_agency_integration(
            agency_id=TEST_AGENCY_ID,
            provider="gmail",
            session=session,
        )

        assert result is not None
        payload = result.to_dict()
        assert payload["status"] == "misconfigured"
        assert payload["last_error_code"] == "invalid_integration_status"
        assert "plaintext_token_leak" not in str(payload)
