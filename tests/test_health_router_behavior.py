from __future__ import annotations


from spine_api.routers import health
from spine_api.version import APP_VERSION


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
    assert response.version == APP_VERSION
    assert response.components == {"decision": {"status": "ok"}}
    assert response.issues == ["warning-1"]


def test_health_fallback_when_health_check_dict_raises(monkeypatch):
    def _raise() -> dict:
        raise RuntimeError("health check unavailable")

    monkeypatch.setattr("src.decision.health.health_check_dict", _raise)

    response = health.health()

    # A failing health probe must NOT report healthy (doctrine §13: no
    # fabricated success). The router degrades loudly and surfaces the probe
    # error. (This test previously asserted "ok" — a dishonest contract that
    # contradicted the router's own fail-loud fallback; corrected 2026-09-06
    # during the PER-0700 remediation wave, shared-tree drift fix.)
    assert response.status == "degraded"
    assert response.version == APP_VERSION
    assert response.components is None
    assert response.issues is not None
    assert response.issues and response.issues[0].startswith("health_probe_error:")
