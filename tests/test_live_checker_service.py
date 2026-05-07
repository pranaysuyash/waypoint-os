from spine_api.services.live_checker_service import (
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
    assert validation["public_checker_live_checks"] == live_checker
    assert decision["public_checker_live_checks"] == live_checker
    assert decision["hard_blockers"] == ["A", "C"]
    assert decision["soft_blockers"] == ["B", "D"]


def test_apply_live_checker_adjustments_uses_decision_baseline_fallback() -> None:
    packet, validation, decision = apply_live_checker_adjustments(
        packet_payload={},
        validation_payload={},
        decision_payload={"decision_state": "ASK_FOLLOWUP"},
        live_checker={"score_penalty": 4},
    )
    assert validation["overall_score"] == 60
    assert packet["score"] == 60
    assert decision["public_checker_live_checks"] == {"score_penalty": 4}
