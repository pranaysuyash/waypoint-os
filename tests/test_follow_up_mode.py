import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from intake.decision import run_gap_and_decision
from intake.packet_models import CanonicalPacket, Slot


def test_follow_up_mode_does_not_reference_undefined_hard_blockers():
    """
    Regression test for a previously flagged bug:
    apply_operating_mode() referenced `hard_blockers` without receiving it.
    """
    packet = CanonicalPacket(
        packet_id="followup_regression",
        stage="discovery",
        operating_mode="follow_up",
        facts={
            "destination_city": Slot(value="Singapore", confidence=0.9, authority_level="explicit_user"),
            "origin_city": Slot(value="Bangalore", confidence=0.9, authority_level="explicit_user"),
            "travel_dates": Slot(value="2026-10-10 to 2026-10-15", confidence=0.9, authority_level="explicit_user"),
            "traveler_count": Slot(value=2, confidence=0.9, authority_level="explicit_user"),
        },
        # intentionally leave soft blockers unresolved in discovery
    )

    result = run_gap_and_decision(packet)

    # follow_up mode should not re-open soft-blocker interrogation if hard blockers are filled
    assert result.hard_blockers == []
    assert result.soft_blockers == []
    assert result.decision_state in {"PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"}
