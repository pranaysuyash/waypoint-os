"""
tests/conftest — Pytest configuration and shared fixtures.

- `session_client`: A single FastAPI TestClient used by every test that calls
  the live app, scoped to the whole session so the underlying asyncpg
  connection pool stays tied to one event loop.  Without this, each test's
  `TestClient` creates/destroys its own loop and asyncpg later throws
  `RuntimeError: attached to a different loop`.
"""

import sys
from pathlib import Path

import pytest

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
