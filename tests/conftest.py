"""
tests/conftest — Pytest configuration and shared fixtures.

- `session_client`: A single FastAPI TestClient used by every test that calls
  the live app, scoped to the whole session so the underlying asyncpg
  connection pool stays tied to one event loop.  Without this, each test's
  `TestClient` creates/destroys its own loop and asyncpg later throws
  `RuntimeError: attached to a different loop`.
"""

import sys
import warnings
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
import os

if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

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


# ---------------------------------------------------------------------------
# DATA_PRIVACY_MODE reset fixture
# Ensures that any test that changes DATA_PRIVACY_MODE is reset afterward.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_data_privacy_mode():
    """Reset DATA_PRIVACY_MODE to dogfood before and after each test."""
    import os

    original = os.environ.get("DATA_PRIVACY_MODE", "dogfood")
    os.environ["DATA_PRIVACY_MODE"] = "dogfood"
    yield
    os.environ["DATA_PRIVACY_MODE"] = original


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

    yield
