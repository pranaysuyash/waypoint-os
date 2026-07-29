from __future__ import annotations

from unittest.mock import patch

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope
from src.intake.strategy import PromptBundle


def test_stage_callback_emits_entered_before_completed_for_core_stages():
    events: list[tuple[str, str]] = []

    def _cb(stage_name: str, payload):
        event = payload.get("event") if isinstance(payload, dict) else "completed"
        events.append((stage_name, event))

    envelopes = [
        SourceEnvelope.from_freeform(
            "We are planning a family leisure trip from Bangalore to Singapore around 9th to 14th Feb 2025. "
            "We are 2 adults with budget around 3L and do not want a rushed itinerary."
        )
    ]

    result = run_spine_once(
        envelopes=envelopes,
        stage="discovery",
        operating_mode="normal_intake",
        stage_callback=_cb,
    )

    assert result is not None

    stage_events: dict[str, list[str]] = {}
    for stage_name, event in events:
        stage_events.setdefault(stage_name, []).append(event)

    for stage in ("packet", "validation", "decision", "strategy", "safety"):
        if stage not in stage_events:
            continue
        stage_list = stage_events[stage]
        assert "entered" in stage_list
        assert "completed" in stage_list
        assert stage_list.index("entered") < stage_list.index("completed")


def test_run_spine_once_forwards_request_scoped_strictness_and_finalizer() -> None:
    envelopes = [
        SourceEnvelope.from_freeform(
            "We are planning a family leisure trip from Bangalore to Singapore around 9th to 14th Feb 2025. "
            "We are 2 adults with budget around 3L and do not want a rushed itinerary."
        )
    ]
    finalizer_calls: list[object] = []
    captured: dict[str, object] = {}

    def _fake_bundle(strategy, decision, strict_leakage=None):
        captured["strict_leakage"] = strict_leakage
        return PromptBundle(
            system_context="",
            user_message="",
            follow_up_sequence=[],
            branch_prompts=[],
            internal_notes="",
            constraints=[],
        )

    def _finalizer(result):
        finalizer_calls.append(result)

    with patch("src.intake.orchestration.build_traveler_safe_bundle", side_effect=_fake_bundle):
        result = run_spine_once(
            envelopes=envelopes,
            stage="discovery",
            operating_mode="normal_intake",
            strict_leakage=True,
            result_finalizer=_finalizer,
        )

    assert result is not None
    assert captured["strict_leakage"] is True
    assert len(finalizer_calls) == 1
