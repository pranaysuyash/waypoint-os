from __future__ import annotations

from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope


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

