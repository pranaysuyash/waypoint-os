from spine_api.services.live_checker_service import (
    _attach_d6_public_authority,
    apply_live_checker_adjustments,
    build_consented_submission,
    collect_raw_text_sources,
)


def test_build_consented_submission_retention_true_returns_original() -> None:
    payload = {"raw_note": "a", "destination": "Tokyo"}
    assert build_consented_submission(payload, retention_consent=True) == payload


def test_build_consented_submission_retention_false_redacts_text_fields() -> None:
    payload = {
        "raw_note": "a",
        "owner_note": "b",
        "itinerary_text": "c",
        "structured_json": {"source_payload": {}},
        "destination": "Tokyo",
    }
    assert build_consented_submission(payload, retention_consent=False) == {"destination": "Tokyo"}


def test_collect_raw_text_sources_includes_uploaded_file_text() -> None:
    raw_text = collect_raw_text_sources(
        raw_note="raw",
        owner_note="owner",
        itinerary_text="itinerary",
        structured_json={
            "source_payload": {
                "uploaded_file": {
                    "extracted_text": "file text",
                }
            }
        },
    )
    assert raw_text == "raw\nowner\nitinerary\nfile text"


def test_apply_live_checker_adjustments_merges_blockers_and_adjusts_score() -> None:
    packet_payload = {"quality_score": 90}
    validation_payload = {"overall_score": 88}
    decision_payload = {"hard_blockers": ["A"], "soft_blockers": ["B"]}
    live_checker = {"score_penalty": 10, "hard_blockers": ["A", "C"], "soft_blockers": ["D"]}

    packet, validation, decision = apply_live_checker_adjustments(
        packet_payload=packet_payload,
        validation_payload=validation_payload,
        decision_payload=decision_payload,
        live_checker=live_checker,
    )

    assert validation["overall_score"] == 78
    assert packet["score"] == 78
    assert validation["public_checker_live_checks"]["score_penalty"] == 10
    assert decision["public_checker_live_checks"]["score_penalty"] == 10
    assert "d6_public_surface" in validation["public_checker_live_checks"]
    assert "d6_public_surface" in decision["public_checker_live_checks"]
    assert decision["hard_blockers"] == ["A"]
    assert decision["soft_blockers"] == ["B"]
    assert decision["advisory_hard_blockers"] == ["A", "C"]
    assert decision["advisory_soft_blockers"] == ["D"]


def test_apply_live_checker_adjustments_uses_decision_baseline_fallback() -> None:
    packet, validation, decision = apply_live_checker_adjustments(
        packet_payload={},
        validation_payload={},
        decision_payload={"decision_state": "ASK_FOLLOWUP"},
        live_checker={"score_penalty": 4},
    )
    assert validation["overall_score"] == 60
    assert packet["score"] == 60
    assert decision["public_checker_live_checks"]["score_penalty"] == 4
    assert "d6_public_surface" in decision["public_checker_live_checks"]


def test_attach_d6_public_authority_marks_untracked_weather_as_advisory() -> None:
    live_checker = {
        "hard_blockers": ["Heavy rain"],
        "soft_blockers": ["Regional advisory"],
        "structured_risks": [
            {"flag": "weather_monsoon", "severity": "high", "category": "weather", "message": "Heavy rain"},
            {"flag": "regional_safety_advisory", "severity": "high", "category": "safety", "message": "Regional advisory"},
        ],
    }

    enriched = _attach_d6_public_authority(live_checker)
    d6_meta = enriched["d6_public_surface"]

    assert d6_meta["category_status"]["weather"] == "shadow"
    assert d6_meta["category_authority"]["weather"] == "advisory"
    assert d6_meta["category_status"]["safety"] == "shadow"
    assert d6_meta["advisory_hard_blockers"] == ["Heavy rain"]
    assert d6_meta["advisory_soft_blockers"] == ["Regional advisory"]
    assert d6_meta["authoritative_hard_blockers"] == []
    assert d6_meta["authoritative_soft_blockers"] == []
    assert all(risk["public_surface_authority"] == "advisory" for risk in enriched["structured_risks"])


def test_apply_live_checker_adjustments_merges_authoritative_blockers(monkeypatch) -> None:
    monkeypatch.setenv("D6_AUDIT_GATE_SNAPSHOT_PATH", "/tmp/does-not-exist-d6-snapshot.json")
    live_checker = {
        "score_penalty": 5,
        "hard_blockers": ["budget mismatch found"],
        "soft_blockers": ["possible budget drift"],
        "structured_risks": [
            {
                "flag": "budget_overrun",
                "severity": "high",
                "category": "budget",
                "message": "budget mismatch found",
            },
            {
                "flag": "budget_warning",
                "severity": "medium",
                "category": "budget",
                "message": "possible budget drift",
            },
        ],
    }
    _, _, decision = apply_live_checker_adjustments(
        packet_payload={},
        validation_payload={},
        decision_payload={"hard_blockers": ["existing_hard"], "soft_blockers": ["existing_soft"]},
        live_checker=live_checker,
    )

    assert "budget mismatch found" in decision["hard_blockers"]
    assert "possible budget drift" in decision["soft_blockers"]
    assert decision["advisory_hard_blockers"] == []
    assert decision["advisory_soft_blockers"] == []
