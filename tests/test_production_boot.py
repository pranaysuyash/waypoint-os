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
        "TRIPSTORE_BACKEND": "sql",
        "PUBLIC_CHECKER_AGENCY_ID": "agency_prod_01",
    }
    with patch.dict(os.environ, prod_env):
        run_startup_assertions(strict=True)
        assert TripStore._backend() is SQLTripStore


def test_production_boot_assertions_pass_with_postgres_alias():
    prod_env = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/waypoint_prod",
        "JWT_SECRET": "production_super_secret_jwt_key_32chars_min_abcdef",
        "TRIPSTORE_BACKEND": "postgres",
        "PUBLIC_CHECKER_AGENCY_ID": "agency_prod_01",
    }
    with patch.dict(os.environ, prod_env):
        run_startup_assertions(strict=True)
        assert TripStore._backend() is SQLTripStore
