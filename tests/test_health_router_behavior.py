from __future__ import annotations

import pytest

from spine_api.routers import health


def test_health_success_path_uses_health_check_dict(monkeypatch):
    monkeypatch.setattr(
        "src.decision.health.health_check_dict",
        lambda: {
            "components": {"decision": {"status": "ok"}},
            "issues": ["warning-1"],
        },
    )

    response = health.health()

    assert response.status == "ok"
    assert response.version == "1.0.0"
    assert response.components == {"decision": {"status": "ok"}}
    assert response.issues == ["warning-1"]


def test_health_fallback_when_health_check_dict_raises(monkeypatch):
    def _raise() -> dict:
        raise RuntimeError("health check unavailable")

    monkeypatch.setattr("src.decision.health.health_check_dict", _raise)

    response = health.health()

    assert response.status == "ok"
    assert response.version == "1.0.0"
    assert response.components is None
    assert response.issues is None
