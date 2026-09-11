"""
tests/test_production_boot.py — Production Boot and Configuration Integration Tests.

Verifies:
  - Startup assertions pass with production environment variables (ENVIRONMENT, DATABASE_URL, JWT_SECRET, TRIPSTORE_BACKEND)
  - TripStore._backend() resolves sql/postgres backends to SQLTripStore
  - Both TRIPSTORE_BACKEND=sql and TRIPSTORE_BACKEND=postgres pass startup assertions AND persistence resolution
"""

import os
from unittest.mock import patch

from spine_api.core.startup_assertions import run_startup_assertions
from spine_api.persistence import TripStore, SQLTripStore


def test_production_boot_assertions_pass_with_sql_backend():
    prod_env = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/waypoint_prod",
        "JWT_SECRET": "production_super_secret_jwt_key_32chars_min_abcdef",
        "REDIS_URL": "redis://localhost:6379/0",
        "TRIPSTORE_BACKEND": "sql",
        "PUBLIC_CHECKER_AGENCY_ID": "agency_prod_01",
        # PT-08: cross-process intake idempotency is required in production
        # (mirrors docker-compose/fly/render which pin this).
        "SPINE_API_IDEMPOTENCY_BACKEND": "sql",
        # FND-0262: prod-like boots require the explicit encryption posture —
        # production privacy mode plus a real (non-committed) Fernet key.
        "DATA_PRIVACY_MODE": "production",
        "ENCRYPTION_KEY": "DoHtVQD_0aw4_pYhZlJTUHZYjHGZCI34Pbr4JFO6zIQ=",
    }
    with patch.dict(os.environ, prod_env):
        run_startup_assertions(strict=True)
        assert TripStore._backend() is SQLTripStore


def test_production_boot_assertions_pass_with_postgres_alias():
    prod_env = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/waypoint_prod",
        "JWT_SECRET": "production_super_secret_jwt_key_32chars_min_abcdef",
        "REDIS_URL": "redis://localhost:6379/0",
        "TRIPSTORE_BACKEND": "postgres",
        "PUBLIC_CHECKER_AGENCY_ID": "agency_prod_01",
        "SPINE_API_IDEMPOTENCY_BACKEND": "sql",
        # FND-0262: explicit encryption posture (see test above).
        "DATA_PRIVACY_MODE": "production",
        "ENCRYPTION_KEY": "DoHtVQD_0aw4_pYhZlJTUHZYjHGZCI34Pbr4JFO6zIQ=",
    }
    with patch.dict(os.environ, prod_env):
        run_startup_assertions(strict=True)
        assert TripStore._backend() is SQLTripStore


def test_server_get_tripstore_backend_normalizes_aliases():
    from spine_api.server import _get_tripstore_backend
    for alias in ("sql", "postgres", "postgresql"):
        with patch.dict(os.environ, {"TRIPSTORE_BACKEND": alias}):
            assert _get_tripstore_backend() == "sql"
    for alias in ("file", "json"):
        with patch.dict(os.environ, {"TRIPSTORE_BACKEND": alias}):
            assert _get_tripstore_backend() == "file"
