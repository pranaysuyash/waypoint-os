import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from intake.decision import compute_intent_scores, run_gap_and_decision
from intake.packet_models import CanonicalPacket, LifecycleInfo


def _base_packet() -> CanonicalPacket:
    pkt = CanonicalPacket(packet_id="lifecycle_test_packet")
    pkt.stage = "discovery"
    pkt.operating_mode = "normal_intake"
    return pkt


def test_packet_serializes_lifecycle_block():
    pkt = _base_packet()
    pkt.lifecycle = LifecycleInfo(
        status="QUOTE_SENT",
        quote_opened=True,
        quote_open_count=1,
        revision_count=2,
    )
    d = pkt.to_dict()
    assert d["lifecycle"] is not None
    assert d["lifecycle"]["status"] == "QUOTE_SENT"
    assert d["lifecycle"]["quote_opened"] is True


def test_ghost_risk_drives_followup_action():
    pkt = _base_packet()
    pkt.lifecycle = LifecycleInfo(
        status="GHOST_RISK",
        quote_opened=True,
        quote_open_count=3,
        options_viewed_count=1,
        links_clicked_count=1,
        days_since_last_reply=4,
        risk_signals=["follow_up_sent_no_reply_48h"],
    )

    scores = compute_intent_scores(pkt)
    assert scores["ghost_risk"] >= 0.7

    result = run_gap_and_decision(pkt)
    assert result.commercial_decision == "SEND_FOLLOWUP"
    assert result.next_best_action == "SEND_TARGETED_FOLLOWUP"


def test_window_shopper_requests_token():
    pkt = _base_packet()
    pkt.lifecycle = LifecycleInfo(
        status="ACTIVE_DISCOVERY",
        revision_count=6,
        options_viewed_count=6,
        payment_stage="none",
        days_since_last_reply=15,
        risk_signals=["destination_flipped_2plus", "budget_contradiction_unresolved"],
    )
    result = run_gap_and_decision(pkt)
    assert result.intent_scores["window_shopper_risk"] >= 0.75
    assert result.commercial_decision == "REQUEST_TOKEN"


def test_repeat_or_churn_triggers_reactivation():
    pkt = _base_packet()
    pkt.lifecycle = LifecycleInfo(
        status="RETENTION_WINDOW",
        repeat_trip_count=1,
        risk_signals=["no_engagement_next_trip_window", "no_reactivation_sent", "no_feedback_captured"],
    )
    result = run_gap_and_decision(pkt)
    assert result.commercial_decision == "REACTIVATE_REPEAT"
    assert result.next_best_action in {"CHURN_RECOVERY_REACHOUT", "PERSONALIZED_REACTIVATION"}


def test_lost_status_closes_lifecycle():
    pkt = _base_packet()
    pkt.lifecycle = LifecycleInfo(
        status="LOST",
        loss_reason="booked_elsewhere",
    )
    result = run_gap_and_decision(pkt)
    assert result.commercial_decision == "CLOSE_LOST"
    assert result.next_best_action == "CLOSE_LOST"
