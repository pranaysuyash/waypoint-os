"""
Live IROPS Auto-Healer Simulator Tests (PER-IROPS-SIM).
"""

from src.orchestration.irops_healer import IROPSAutoHealerEngine


def test_irops_auto_healing_execution():
    plan = IROPSAutoHealerEngine.execute_healing_protocol(
        trip_id="TRIP-HEAL-889",
        delayed_node_id="N_FLT_178",
        delay_minutes=180,
    )

    assert plan.trip_id == "TRIP-HEAL-889"
    assert plan.delay_minutes == 180
    assert plan.statutory_compensation_amount_eur == 600.0
    assert "EU261" in plan.statutory_law_cited
    assert len(plan.counterfactual_options) == 3
    assert plan.counterfactual_options[0]["tier"] == "OPTION_A_MIN_DELAY"
    assert plan.emergency_lodging_vcc is not None
    assert "Request for Full Penalty Waiver" in plan.waiver_dispute_letter
