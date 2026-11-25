from __future__ import annotations

import json
from types import SimpleNamespace


def _fake_result(decision_payload: dict, validation_payload: dict | None = None):
    return SimpleNamespace(
        packet={"destination": "Bali"},
        validation=validation_payload or {"overall_score": 80, "is_valid": True},
        decision=decision_payload,
        strategy={},
        follow_up_questions=[],
        early_exit=False,
        early_exit_reason=None,
        partial_intake=False,
    )


def _make_live_checker_mock(**signals):
    """
    Build a mock run_spine_once that calls the result_finalizer, so
    build_live_checker_signals is actually invoked and the decision
    payload gets hard_blockers/advisory_hard_blockers set.
    """
    def _mock(**kwargs):
        result = _fake_result({"decision_state": "ASK_FOLLOWUP"})
        finalizer = kwargs.get("result_finalizer")
        if finalizer:
            finalizer(result)
        return result
    return _mock


def test_public_checker_contract_keeps_advisory_weather_out_of_canonical_blockers(session_client, monkeypatch):
    import server
    import spine_api.services.public_checker_service as public_checker_service

    captured: dict[str, object] = {}

    monkeypatch.setattr(server, "build_envelopes", lambda payload: payload)
    monkeypatch.setattr(server, "load_fixture_expectations", lambda _: None)
    monkeypatch.setattr(server, "_to_dict", lambda value: value)
    def _save_trip(payload, **kwargs):
        _ = kwargs
        captured["saved"] = payload
        return "trip_test_1"

    monkeypatch.setattr(server, "save_processed_trip", _save_trip)
    monkeypatch.setattr(public_checker_service, "run_spine_once", _make_live_checker_mock())
    monkeypatch.setattr(
        public_checker_service,
        "build_live_checker_signals",
        lambda packet, text: {
            "score_penalty": 6,
            "hard_blockers": ["Heavy rain risk"],
            "soft_blockers": [],
            "structured_risks": [
                {"flag": "weather_monsoon", "severity": "high", "category": "weather", "message": "Heavy rain risk"},
            ],
        },
    )

    resp = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "Trip to Bali in December", "retention_consent": True},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()

    assert payload["hard_blockers"] == []
    assert payload["soft_blockers"] == []

    saved = captured["saved"]
    assert isinstance(saved, dict)
    decision = saved["decision"]
    assert decision["hard_blockers"] == []
    assert decision["advisory_hard_blockers"] == ["Heavy rain risk"]


def test_public_checker_contract_promotes_weather_when_snapshot_marks_authoritative(session_client, monkeypatch, tmp_path):
    import server
    import spine_api.services.public_checker_service as public_checker_service

    snapshot_path = tmp_path / "d6_gate_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "categories": {
                    "weather": {
                        "status": "shadow",
                        "authoritative_for_public_surface": True,
                        "reasons": ["manual_override_for_validation"],
                    }
                }
            }
        )
    )
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", str(snapshot_path))

    captured: dict[str, object] = {}

    monkeypatch.setattr(server, "build_envelopes", lambda payload: payload)
    monkeypatch.setattr(server, "load_fixture_expectations", lambda _: None)
    monkeypatch.setattr(server, "_to_dict", lambda value: value)
    def _save_trip(payload, **kwargs):
        _ = kwargs
        captured["saved"] = payload
        return "trip_test_2"

    monkeypatch.setattr(server, "save_processed_trip", _save_trip)
    monkeypatch.setattr(public_checker_service, "run_spine_once", _make_live_checker_mock())
    monkeypatch.setattr(
        public_checker_service,
        "build_live_checker_signals",
        lambda packet, text: {
            "score_penalty": 6,
            "hard_blockers": ["Heavy rain risk"],
            "soft_blockers": [],
            "structured_risks": [
                {"flag": "weather_monsoon", "severity": "high", "category": "weather", "message": "Heavy rain risk"},
            ],
        },
    )

    resp = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "Trip to Bali in December", "retention_consent": True},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()

    assert payload["hard_blockers"] == ["Heavy rain risk"]
    saved = captured["saved"]
    assert isinstance(saved, dict)
    decision = saved["decision"]
    assert decision["hard_blockers"] == ["Heavy rain risk"]
    assert decision["advisory_hard_blockers"] == []


def test_public_contract_preserves_unavailable_place_lookup_reason(session_client, monkeypatch):
    import server
    from spine_api.services import public_checker_service
    from src.public_checker import entity_checks

    monkeypatch.setenv("ENTITY_CHECK_ENABLED", "1")
    monkeypatch.setattr(server, "build_envelopes", lambda payload: payload)
    monkeypatch.setattr(server, "load_fixture_expectations", lambda _: None)
    monkeypatch.setattr(server, "_to_dict", lambda value: value)
    monkeypatch.setattr(server, "save_processed_trip", lambda *_, **__: "trip_place_fixture")
    monkeypatch.setattr(public_checker_service, "run_spine_once", _make_live_checker_mock())
    monkeypatch.setattr(public_checker_service, "build_live_checker_signals", lambda *_: None)
    monkeypatch.setattr(entity_checks, "_cache", {})
    monkeypatch.setattr(entity_checks, "_last_request_at", 0.0)

    def unavailable(_url):
        raise TimeoutError("Synthetic provider timeout")

    monkeypatch.setattr(entity_checks, "_http_get_json", unavailable)
    response = session_client.post(
        "/api/public-checker/run",
        json={"raw_note": "We are staying at Hotel Alpha in Bali for three nights."},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    check, = result["packet"]["public_checker_entity_checks"]
    assert check["status"] == "unverified"
    assert check["reason"] == "source_unavailable"
    assert result["hard_blockers"] == []
