from spine_api.services.counterfactual_engine import (
    ItineraryBranch,
    ItineraryDiff,
    compute_branch_diff,
    create_counterfactual_branch,
)
from spine_api.services.voice_copilot import (
    ExtractedIntakePacket,
    parse_consultation_transcript,
)
from spine_api.services.autonomy_gates import (
    AutonomyGateDecision,
    evaluate_autonomy_dispatch_gate,
)


def test_counterfactual_branching_and_diff():
    canonical = {
        "total_price_usd": 5000.0,
        "duration_days": 7,
        "hotel_name": "Hotel Roma",
        "activity_titles": ["Colosseum Tour", "Vatican Tour"],
    }
    fork = {
        "total_price_usd": 6800.0,
        "duration_days": 9,
        "hotel_name": "Hotel Florence",
        "activity_titles": ["Colosseum Tour", "Vatican Tour", "Uffizi Gallery", "Tuscan Wine Tour"],
    }

    branch: ItineraryBranch = create_counterfactual_branch(
        parent_trip_id="trip_italy_01",
        branch_name="Florence & Tuscany Extension",
        hypothesis_notes="Client asked what an extra 2 days in Florence would cost.",
        base_manifest=fork,
    )
    assert branch.status == "draft"

    diff: ItineraryDiff = compute_branch_diff(canonical, fork)
    assert diff.price_delta_usd == 1800.0
    assert diff.duration_delta_days == 2
    assert len(diff.activities_added) == 2
    assert "Uffizi Gallery" in diff.activities_added


def test_voice_copilot_intake_parsing():
    transcript = (
        "Hi there, my wife and I are looking to take a trip to Italy, specifically Rome and the Amalfi Coast "
        "next September. We want something pretty relaxed, definitely not rushed. Our budget is around $12,000. "
        "My wife is vegetarian, and we would love a hotel with a swimming pool and an ocean view for our anniversary."
    )

    intake: ExtractedIntakePacket = parse_consultation_transcript(transcript)
    assert "Italy" in intake.destinations
    assert "Rome" in intake.destinations
    assert "Amalfi Coast" in intake.destinations
    assert intake.adults_count == 2
    assert intake.budget_max_usd == 12000.0
    assert intake.pace_preference == "relaxed"
    assert "Vegetarian" in intake.dietary_restrictions
    assert any("swimming pool" in s for s in intake.special_requirements)


def test_autonomy_gate_requires_human_for_high_value():
    # $15,000 package with non-refundable deposit
    decision: AutonomyGateDecision = evaluate_autonomy_dispatch_gate(
        total_package_usd=15000.0,
        has_non_refundable_deposit=True,
    )
    assert decision.can_auto_dispatch is False
    assert decision.requires_human_signoff is True
    assert decision.autonomy_level == "ADVISOR_REVIEW_REQUIRED"
    assert len(decision.risk_factors) >= 1

    # Low-value $1,500 package with fully refundable terms
    safe_decision: AutonomyGateDecision = evaluate_autonomy_dispatch_gate(
        total_package_usd=1500.0,
        has_non_refundable_deposit=False,
    )
    assert safe_decision.can_auto_dispatch is True
    assert safe_decision.requires_human_signoff is False
    assert safe_decision.autonomy_level == "AUTONOMOUS"
