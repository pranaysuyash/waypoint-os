from src.intake.risk_action_policy import build_risk_action_plan


def test_risk_action_plan_pre_trip_blocks_high_risk():
    plan = build_risk_action_plan(
        stage="proposal",
        structured_risks=[{"severity": "high", "category": "routing"}],
    )
    assert plan["mode"] == "pre_commit_block"
    assert plan["high_or_critical_count"] == 1
    assert any("Block confirmation" in action for action in plan["actions"])


def test_risk_action_plan_in_progress_incident_response():
    plan = build_risk_action_plan(
        stage="in_progress",
        structured_risks=[{"severity": "high", "category": "safety"}],
    )
    assert plan["mode"] == "incident_response"
    assert any("immediate human operations review" in action.lower() for action in plan["actions"])

