"""HTTP-level readiness/auth boundary regressions.

Direct ``health.ready`` tests prove the dependency checks themselves. These
tests prove the ASGI middleware lets a platform probe reach that handler while
continuing to reject a protected application route without a JWT.
"""

from __future__ import annotations


def test_unauthenticated_ready_reaches_readiness_handler(session_client):
    response = session_client.get("/ready", headers={})

    assert response.status_code in {200, 503}
    assert response.status_code != 401
    payload = response.json()
    assert payload["status"] in {"ready", "unready"}
    assert set(payload["checks"]) <= {"database", "migrations", "redis"}
    assert "password" not in response.text.lower()
    assert "connection refused" not in response.text.lower()


def test_protected_application_route_still_requires_auth(session_client):
    response = session_client.get("/api/workspace", headers={"Authorization": ""})

    assert response.status_code == 401
