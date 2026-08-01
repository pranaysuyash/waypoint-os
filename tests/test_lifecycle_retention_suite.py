"""
tests/test_lifecycle_retention_suite.py — Test suite for Lead Lifecycle & Retention State Machine.
"""

from src.intake.lifecycle import LeadLifecycleState, LeadStage, RetentionInterventionType


def test_lead_lifecycle_eval_new():
    state = LeadLifecycleState(
        trip_id="trip_123",
        agency_id="default_agency",
        stage=LeadStage.NEW_INQUIRY,
        days_since_last_interaction=1,
    )
    state.evaluate()
    assert state.ghosting_risk == 0.1
    assert state.recommended_interventions == []


def test_lead_lifecycle_eval_ghosted():
    state = LeadLifecycleState(
        trip_id="trip_456",
        agency_id="default_agency",
        stage=LeadStage.PROPOSAL_SENT,
        days_since_last_interaction=8,
        intent_score=0.85,
    )
    state.evaluate()
    assert state.stage == LeadStage.GHOSTED_STALE
    assert state.ghosting_risk > 0.5
    assert RetentionInterventionType.PERSONALIZED_WHATSAPP in state.recommended_interventions
    assert RetentionInterventionType.HUMAN_SENIOR_CALL in state.recommended_interventions
