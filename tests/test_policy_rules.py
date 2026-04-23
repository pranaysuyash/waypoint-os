from src.analytics.policy_rules import (
    apply_owner_escalation_policy,
    compute_send_policy,
    ready_gate_failures,
)


def test_ready_gate_fails_without_traveler_bundle():
    trip = {
        "raw_input": {"raw_note": "Need trip ideas"},
        "decision": {"decision_state": "PROCEED_TRAVELER_SAFE", "suitability_flags": []},
        "traveler_bundle": None,
        "analytics": {"requires_review": False},
    }

    failures = ready_gate_failures(trip, overrides_by_flag={})
    assert "Traveler-safe output is missing." in failures


def test_ready_gate_allows_critical_flag_with_ack_override():
    trip = {
        "raw_input": {"raw_note": "Need family itinerary"},
        "decision": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "suitability_flags": [
                {"flag": "elderly_mobility_risk", "severity": "critical"},
            ],
        },
        "traveler_bundle": {"user_message": "Draft"},
        "analytics": {"requires_review": False},
    }
    overrides = {
        "elderly_mobility_risk": [
            {"action": "acknowledge", "reason": "Confirmed with traveler"},
        ]
    }

    failures = ready_gate_failures(trip, overrides_by_flag=overrides)
    assert failures == []


def test_escalation_policy_for_stop_needs_review():
    trip = {
        "decision": {"decision_state": "STOP_NEEDS_REVIEW", "suitability_flags": []},
        "analytics": {},
    }
    analytics = {"margin_pct": 14.0, "requires_review": False, "revision_count": 0}

    out = apply_owner_escalation_policy(trip, analytics)
    assert out["requires_review"] is True
    assert out["is_escalated"] is True
    assert out["review_status"] == "escalated"
    assert out["escalation_severity"] == "critical"
    assert out.get("owner_review_deadline")


def test_send_policy_blocks_junior_on_critical_flag():
    trip = {
        "decision": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "confidence": {"overall": 0.9},
            "suitability_flags": [{"flag": "elderly_mobility_risk", "severity": "critical"}],
        },
        "analytics": {"requires_review": False},
    }

    policy = compute_send_policy(trip, role="junior_agent")
    assert policy["owner_approval_required"] is True
    assert policy["send_allowed"] is False


def test_send_policy_allows_junior_high_confidence_no_critical():
    trip = {
        "decision": {
            "decision_state": "PROCEED_TRAVELER_SAFE",
            "confidence": {"overall": 0.92},
            "suitability_flags": [],
        },
        "analytics": {"requires_review": False},
    }

    policy = compute_send_policy(trip, role="junior_agent")
    assert policy["owner_approval_required"] is False
    assert policy["send_allowed"] is True
