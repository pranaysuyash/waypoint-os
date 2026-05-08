"""
Tests for spine_api.scoring — urgency, importance, and combined priority.
"""
from datetime import datetime, timezone
from spine_api.scoring import (
    compute_urgency,
    compute_importance,
    priority_level,
    combined_score,
    score_trip,
    PriorityResult,
)


FIXED_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


def _base_trip(**overrides):
    trip = {
        "id": "trip-001",
        "status": "new",
        "created_at": "2026-06-10T00:00:00Z",
        "destination": "Paris",
        "value": 5000,
        "dateWindow": "August 2026",
        "lead_source": "Referral through Divya",
        "trip_priorities": "",
        "extracted": {"facts": {}},
        "analytics": {},
        "decision": {},
        "validation": {},
    }
    trip.update(overrides)
    return trip


# ---- Urgency ----

def test_urgency_breached_sla_scores_high():
    """Breached SLA should produce high urgency."""
    source = _base_trip(created_at="2026-06-01T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert urgency > 30


def test_urgency_at_risk_sla_scores_medium():
    """At-risk SLA should produce some urgency."""
    source = _base_trip(created_at="2026-06-10T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert 10 <= urgency <= 40


def test_urgency_fresh_trip_scores_low():
    """Trip created today should have low urgency."""
    source = _base_trip(created_at="2026-06-15T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert urgency < 20


def test_urgency_departure_soon_scores_high():
    """Trip departing within days scores high."""
    source = _base_trip(dateWindow="June 2026", created_at="2026-06-01T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert urgency > 35


def test_urgency_tbd_date_window_scores_medium():
    """Unknown departure date should default to medium."""
    source = _base_trip(dateWindow="TBD", created_at="2026-06-10T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert 25 <= urgency <= 60


def test_urgency_needs_followup_scores_high():
    """Trip waiting on followup has high urgency."""
    source = _base_trip(status="needs_followup", created_at="2026-05-01T00:00:00Z")
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert urgency > 35


def test_urgency_critical_escalation_scores_high():
    """Critical escalation raises urgency."""
    source = _base_trip(
        created_at="2026-05-01T00:00:00Z",
        analytics={"escalation_severity": "critical"},
        status="needs_followup",
    )
    urgency, _ = compute_urgency(source, now=FIXED_NOW)
    assert urgency > 35


def test_urgency_handles_missing_fields():
    """Empty trip dict should not crash."""
    urgency, _ = compute_urgency({"id": "bare"}, now=FIXED_NOW)
    assert 0 <= urgency <= 100


def test_urgency_breakdown_sums_components():
    """Components should contribute proportionally to total."""
    source = _base_trip(created_at="2026-05-01T00:00:00Z", status="needs_followup")
    urgency, bd = compute_urgency(source, now=FIXED_NOW)
    assert bd["sla_breach"] == 100.0
    assert bd["client_initiated"] == 80.0
    assert urgency > 40


# ---- Importance ----

def test_importance_high_value_scores_high():
    """High value trip should score high importance."""
    source = _base_trip(value=40000)
    importance, _ = compute_importance(source)
    assert importance > 40


def test_importance_low_value_scores_low():
    """Low value trip should score low importance."""
    source = _base_trip(value=500)
    importance, _ = compute_importance(source)
    assert importance < 30


def test_importance_referral_scores_high():
    """Referral lead source = high importance."""
    source = _base_trip(value=5000, lead_source="Referral through Divya")
    importance, _ = compute_importance(source)
    assert importance > 25


def test_importance_web_lead_scores_lower():
    """Web search lead scores lower importance."""
    source = _base_trip(value=5000, lead_source="Web Search")
    importance, _ = compute_importance(source)
    assert importance <= 35


def test_importance_vip_signal():
    """VIP/urgent signals in trip_priorities should boost."""
    source = _base_trip(value=5000, trip_priorities="URGENT - VIP client")
    importance, _ = compute_importance(source)
    assert importance > 40


def test_importance_handles_missing_fields():
    """Empty trip dict should not crash."""
    importance, _ = compute_importance({"id": "bare"})
    assert 0 <= importance <= 100


def test_importance_complexity_boosts():
    """Multi-city + flights + hotels should raise complexity."""
    source = _base_trip(value=5000, extracted={
        "facts": {
            "is_multi_city": True,
            "flight_requirements": ["JFK-CDG"],
            "accommodation": ["Hotel Bristol"],
            "activities": ["Eiffel Tower tour"],
        }
    })
    importance, _ = compute_importance(source)
    assert importance > 25


# ---- Combined ----

def test_priority_critical_high_urgency_high_importance():
    assert priority_level(85, 80) == "critical"


def test_priority_high_urgency_only():
    assert priority_level(70, 30) == "high"


def test_priority_high_importance_only():
    assert priority_level(40, 70) == "high"


def test_priority_medium_both_moderate():
    assert priority_level(30, 40) == "medium"


def test_priority_low_both_low():
    assert priority_level(10, 5) == "low"


def test_priority_low_accessible():
    """Low priority IS reachable (was a bug: old code never assigned 'low')."""
    assert priority_level(10, 5) == "low"


def test_combined_score_computation():
    assert combined_score(80, 20) == 50
    assert combined_score(40, 60) == 50


# ---- Top-level ----

def test_score_trip_returns_result():
    source = _base_trip(created_at="2026-06-10T00:00:00Z")
    result = score_trip(source, now=FIXED_NOW)
    assert isinstance(result, PriorityResult)
    assert 0 <= result.urgency <= 100
    assert 0 <= result.importance <= 100
    assert result.label in ("low", "medium", "high", "critical")


def test_score_trip_to_dict():
    source = _base_trip(created_at="2026-06-01T00:00:00Z", value=20000)
    result = score_trip(source, now=FIXED_NOW)
    d = result.to_dict()
    assert isinstance(d["urgency"], int)
    assert isinstance(d["importance"], int)
    assert "priority" in d
    assert "priorityScore" in d
    assert isinstance(d["urgencyBreakdown"], dict)


def test_score_trip_critical_scenario():
    """Breached SLA + high value + escalation = critical."""
    source = _base_trip(
        created_at="2026-04-01T00:00:00Z",
        value=50000,
        status="needs_followup",
        trip_priorities="URGENT VIP",
        analytics={"escalation_severity": "critical"},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.label == "critical"
    assert result.urgency > 60
    assert result.importance > 60


def test_score_trip_low_priority_scenario():
    """Long lead time + low value + no urgency signals = low priority."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        value=1,
        dateWindow="December 2026",
        lead_source="Other",
        trip_priorities="",
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.label == "low"


# ---- Operational risk ----

def test_operational_risk_emergency_mode():
    """operating_mode=emergency should push urgency to critical levels."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        value=5000,
        operating_mode="emergency",
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0
    assert result.urgency > 20


def test_operational_risk_passport_blocker():
    """hard_blockers containing passport/visa keywords = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["passport_expired", "visa_denied"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0


def test_operational_risk_medical_emergency():
    """Medical/evacuation keywords in hard_blockers = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["traveler hospitalized", "medical evacuation needed"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0


def test_operational_risk_natural_disaster():
    """Natural disaster keywords = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["earthquake at destination", "flood warning"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0


def test_operational_risk_safety_critical_flags():
    """Safety panel critical/emergency severity = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        safety={"safety_flags": ["life threatening", "evacuation_required"], "severity": "critical"},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0


def test_operational_risk_escalation_critical():
    """Critical escalation severity = high operational risk."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        analytics={"escalation_severity": "critical"},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 80.0


def test_operational_risk_risk_flags():
    """risk_flags containing emergency keywords = high risk."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"risk_flags": ["passport_expiry_soon", "visa_gap"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 80.0


def test_operational_risk_no_signals():
    """No emergency signals = zero operational risk."""
    source = _base_trip(created_at="2026-06-14T00:00:00Z")
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 0.0


def test_operational_risk_benign_hard_blocker():
    """Non-emergency hard_blockers should not trigger."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["missing_phone_number", "incomplete_address"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 0.0


def test_operational_risk_trumps_temporal():
    """Emergency mode should dominate temporal urgency signals."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",  # fresh, low temporal urgency
        value=500,
        operating_mode="emergency",
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.label in ("high", "critical")


def test_operational_risk_death_notification():
    """Death/accident keywords = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["death_in_family", "traveler_accident"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0


def test_operational_risk_theft_stranded():
    """Stranded traveler / theft = emergency."""
    source = _base_trip(
        created_at="2026-06-14T00:00:00Z",
        decision={"hard_blockers": ["passport_theft", "traveler_stranded"]},
    )
    result = score_trip(source, now=FIXED_NOW)
    assert result.urgency_breakdown["operational_risk"] == 100.0
