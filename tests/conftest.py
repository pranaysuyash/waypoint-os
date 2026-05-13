"""
tests/conftest — Pytest configuration and shared fixtures.

- `session_client`: A single FastAPI TestClient used by every test that calls
  the live app, scoped to the whole session so the underlying asyncpg
  connection pool stays tied to one event loop.  Without this, each test's
  `TestClient` creates/destroys its own loop and asyncpg later throws
  `RuntimeError: attached to a different loop`.
"""

import os
import sys
import warnings
from datetime import timedelta
from pathlib import Path

import pytest

# Suppress SWIG-generated C extension warnings from sentencepiece/grpcio
# (upstream bug — their SWIG bindings don't set __module__ on C types)
warnings.filterwarnings(
    "ignore",
    message="builtin type.*has no __module__",
    category=DeprecationWarning,
)

# ---------------------------------------------------------------------------
# JWT_SECRET — must be set before *any* spine_api module is imported,
# because security.py raises at import time if the var is missing.
# ---------------------------------------------------------------------------
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

# Tell the app we are inside a test run so the lifespan skips background
# agents that would create the TripStore SQL bridge (agent_work_coordinator
# always uses _run_async_blocking, bypassing TRIPSTORE_BACKEND=file).
os.environ["RUNNING_TESTS"] = "1"

# Ensure startup public-checker agency validation resolves to the canonical
# seeded test agency used across auth fixtures and JWTs.
os.environ.setdefault("PUBLIC_CHECKER_AGENCY_ID", "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b")

# Disable OpenTelemetry in tests — the BatchSpanProcessor background thread
# outlives the TestClient event loop and corrupts the asyncpg pool. OTel would
# try to export to localhost:4317 (the collector) which isn't running in tests.
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""

# ---------------------------------------------------------------------------
# Module paths (needed before app import)
# ---------------------------------------------------------------------------
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

spine_api_dir = Path(__file__).parent.parent / "spine_api"
if str(spine_api_dir) not in sys.path:
    sys.path.insert(0, str(spine_api_dir))

# ---------------------------------------------------------------------------
# Module alias: canonicalise persistence module identity
# ---------------------------------------------------------------------------
# Canonicalise the persistence module so that ``import persistence`` and
# ``from spine_api import persistence`` always resolve to the *same* module
# object.  Without this, server.py's ``import persistence`` fallback creates
# a second copy of the module, and monkey-patching one copy does not affect
# the other → test isolation bugs (11 ghost failures on 2026-05-04).
#
# We MUST do this at module level (not inside a fixture) because test files
# import OverrideStore etc. at module import time, before any fixture runs.
#
# NOTE: forced assignment (not setdefault) because
# spine_api/core/audit_bridge.py may have already imported
# spine_api.persistence, creating a separate sys.modules entry.
# We also set spine_api.persistence as a package attribute because
# ``from spine_api import persistence`` uses the package's __dict__,
# not sys.modules, when resolving the submodule.
try:
    import persistence as _persistence
    sys.modules["spine_api.persistence"] = _persistence
    import spine_api as _spine_api
    _spine_api.persistence = _persistence
except ImportError:
    # Running in a context where spine_api is not yet importable
    pass

# ---------------------------------------------------------------------------
# Shared session-scoped TestClient (prevents asyncpg loop mismatches)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def session_client():
    """Return a single TestClient instance for the whole test session.

    WHY:  `TestClient` wraps an ASGI app inside a synchronous interface by
    spawning an event loop internally.  When that loop is torn down, the
    attached asyncpg connection pool becomes invalid.  A second `TestClient`
    then starts a *new* loop and tries to reuse the same pool → crash.

    USE: In any test file, import `session_client` instead of creating a
    local `TestClient` fixture:

        def test_xyz(session_client):
            resp = session_client.get("/api/items")
            ...
    """
    from fastapi.testclient import TestClient
    from server import app
    from spine_api.core.security import create_access_token

    token = create_access_token(
        user_id="323468de-ba3d-437b-aa10-35b281a0c6a6",
        agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
        role="owner",
        expires_delta=timedelta(hours=12),
    )
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------


def pytest_configure(config):
    """Register custom marks to avoid PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require a live spine_api instance (skip with -m 'not integration')",
    )
    config.addinivalue_line(
        "markers",
        "require_postgres: marks tests that require a running PostgreSQL instance",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests when the API server is not fully ready."""
    integration_items = [item for item in items if item.get_closest_marker("integration")]
    if not integration_items:
        return
    try:
        import requests
        # Verify the auth endpoint returns expected behavior (422 for missing body, not 401)
        resp = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            json={"email": "", "password": ""},
            timeout=3,
        )
        # A properly configured auth router returns 422 (validation error)
        # A 401 means the middleware is intercepting (server not fully configured)
        if resp.status_code == 422:
            return  # Server is fully ready for integration tests
    except Exception:
        pass
    skip_reason = "spine_api integration server not fully ready (start with 'uv run uvicorn spine_api.server:app --port 8000' or use -m 'not integration')"
    for item in integration_items:
        item.add_marker(pytest.mark.skip(reason=skip_reason))


# ---------------------------------------------------------------------------
# DATA_PRIVACY_MODE reset fixture
# Ensures that any test that changes DATA_PRIVACY_MODE is reset afterward.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_data_privacy_mode():
    """Reset DATA_PRIVACY_MODE to dogfood before and after each test.

    Previously this saved and restored the *current* value, which meant a
    leaked DATA_PRIVACY_MODE from a buggy fixture would cascade to the next
    test (the restore re-applied the leaked value).  Always restore to
    dogfood so each test starts fresh regardless of what neighbours do.
    """
    import os

    os.environ["DATA_PRIVACY_MODE"] = "dogfood"
    yield
    os.environ["DATA_PRIVACY_MODE"] = "dogfood"


# ---------------------------------------------------------------------------
# Disable audit logging for call-capture E2E tests
# Prevents file lock contention during parallel test execution
# ---------------------------------------------------------------------------
@pytest.fixture
def disable_audit_logging(monkeypatch):
    """Disable audit logging for tests to prevent file lock timeouts."""
    from spine_api.persistence import AuditStore
    
    def noop_log_event(*args, **kwargs):
        pass
    
    monkeypatch.setattr(AuditStore, "log_event", noop_log_event)
    
    # Disable privacy guard for these tests
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    
    yield


# ---------------------------------------------------------------------------
# Reset global singletons and lru caches between tests
# Prevents state leakage from hybrid engine, telemetry, health check, etc.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_global_singletons():
    """Reset global state between tests for isolation."""
    # Reset hybrid decision engine
    try:
        from src.intake.decision import _reset_hybrid_engine
        _reset_hybrid_engine()
    except Exception:
        pass

    # Reset decision telemetry
    try:
        from src.decision.telemetry import reset_telemetry
        reset_telemetry()
    except Exception:
        pass

    # Reset health check singleton
    try:
        from src.decision.health import reset_health
        reset_health()
    except Exception:
        pass

    # Clear LLM guard cache
    try:
        from src.decision.hybrid_engine import _is_llm_guard_enabled
        _is_llm_guard_enabled.cache_clear()
    except Exception:
        pass

    # Clear Fernet cache (encryption key may vary between test modes)
    try:
        from src.security.encryption import _clear_fernet_cache
        _clear_fernet_cache()
    except Exception:
        pass

    # Reset persistence module state (monkeypatched paths leak between tests)
    try:
        import spine_api.persistence as _persistence
        _persistence._tripstore_instance = None
        _persistence._sql_tripstore_instance = None
        # Reset module-level path attributes to defaults so that ANY test
        # that monkeypatched them (or leaked state) starts fresh.
        # Without this, a leaked TRIPS_DIR from test A causes test B to fail.
        _default_data_dir = Path(_persistence.__file__).parent.parent / "data"
        _persistence.DATA_DIR = _default_data_dir
        _persistence.TRIPS_DIR = _default_data_dir / "trips"
        _persistence.ASSIGNMENTS_DIR = _default_data_dir / "assignments"
        _persistence.AUDIT_DIR = _default_data_dir / "audit"
        _persistence.PUBLIC_CHECKER_DIR = _default_data_dir / "public_checker"
        _persistence.PUBLIC_CHECKER_UPLOADS_DIR = _persistence.PUBLIC_CHECKER_DIR / "uploads"
        _persistence.PUBLIC_CHECKER_MANIFESTS_DIR = _persistence.PUBLIC_CHECKER_DIR / "manifests"
        _persistence.OVERRIDES_DIR = _default_data_dir / "overrides"
        _persistence.OVERRIDES_PER_TRIP_DIR = _persistence.OVERRIDES_DIR / "per_trip"
        _persistence.OVERRIDES_PATTERNS_DIR = _persistence.OVERRIDES_DIR / "patterns"
        _persistence.OVERRIDES_INDEX_FILE = _persistence.OVERRIDES_DIR / "index.json"
    except Exception:
        pass

    # Reset LLMUsageGuard singleton so env changes are picked up
    try:
        from src.llm.usage_guard import reset_usage_guard
        reset_usage_guard()
    except Exception:
        pass

    yield

# ---------------------------------------------------------------------------
# Async database session fixture for tests that need real PostgreSQL
# ---------------------------------------------------------------------------


import pytest_asyncio


@pytest_asyncio.fixture
async def db_session():
    """Yield a fresh AsyncSession tied to the app engine.

    Rolls back on exit to keep the database clean.
    Mark tests with @pytest.mark.require_postgres if they need
    a running PostgreSQL instance.
    """
    from spine_api.core.database import async_session_maker

    session = async_session_maker()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


# ---------------------------------------------------------------------------
# Postgres availability check
# Auto-skips tests requiring a running PostgreSQL when unavailable.
# ---------------------------------------------------------------------------


def _is_postgres_available() -> bool:
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 5432))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _skip_if_no_postgres(request):
    if request.node.get_closest_marker("require_postgres"):
        if not _is_postgres_available():
            pytest.skip("PostgreSQL not available (docker compose up -d postgres)")
