"""
End-to-End Autonomous Proposal Compiler Tests (PER-INT-E2E).
"""

from datetime import date, timedelta
from src.orchestration.proposal_compiler import AutonomousProposalCompiler


def test_autonomous_proposal_compilation():
    dep_date = date.today() + timedelta(days=60)
    ret_date = dep_date + timedelta(days=7)

    package = AutonomousProposalCompiler.compile_from_intake(
        trip_id="TRIP-COMPILER-001",
        raw_intake_text="We want a luxury 7-day trip to Paris with private chauffeur transfers. No ground floor rooms.",
        destination="Paris",
        departure_date=dep_date,
        return_date=ret_date,
        traveler_count=2,
        price_sensitivity=0.1,  # Luxury
        peak_season=True,
    )

    assert package.trip_id == "TRIP-COMPILER-001"
    assert package.destination == "Paris"
    assert package.is_feasibility_passed is True
    assert package.journey_graph_node_count >= 3
    assert package.net_supplier_cost_usd > 0
    assert package.gross_customer_price_usd > package.net_supplier_cost_usd
    assert package.gross_margin_usd > 0
    assert "https://proposals.waypointos.com/view/" in package.proposal_share_url
