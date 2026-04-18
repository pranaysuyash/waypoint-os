import pytest
from src.intake.config.agency_settings import AgencySettings
from src.intake.decision import check_budget_feasibility, DecisionResult
from src.intake.strategy import build_session_strategy
from src.intake.packet_models import CanonicalPacket, Slot, AuthorityLevel

def test_settings_affect_budget_margin():
    # Setup a packet with a fixed budget
    # Destination: Goa (min_per_person usually ~15000 in heuristic table)
    # Party size: 2
    # Base cost: 30000
    packet = CanonicalPacket(
        packet_id="test-packet",
        operating_mode="normal_intake",
        facts={
            "resolved_destination": Slot(value="Goa", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "party_size": Slot(value=2, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "budget_min": Slot(value=33000, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
        }
    )
    
    # 1. Test with 5% margin (Expected: Feasible, as 30000 * 1.05 = 31500 < 33000)
    settings_low = AgencySettings(agency_id="low", target_margin_pct=5.0)
    result_low = check_budget_feasibility(packet, agency_settings=settings_low)
    assert result_low["status"] == "feasible"
    
    # 2. Test with 20% margin (Expected: Infeasible, as 30000 * 1.20 = 36000 > 33000)
    # Actually, with 20%, status might be 'tight' or 'infeasible'. 
    # 33000 - 36000 = -3000.
    # -0.3 * 36000 = -10800.
    # -3000 > -10800, so it's 'tight', not 'infeasible'.
    
    # Let's use 30% margin. 30000 * 1.30 = 39000.
    # 33000 - 39000 = -6000.
    # -0.3 * 39000 = -11700.
    # Still tight.
    
    # Let's use a very high margin to force 'infeasible'.
    # 50% margin. 30000 * 1.50 = 45000.
    # 33000 - 45000 = -12000.
    # -0.3 * 45000 = -13500.
    # Still tight. Wow the threshold is generous.
    
    # Let's reduce budget to force infeasible.
    packet_low_budget = CanonicalPacket(
        packet_id="test-packet-2",
        operating_mode="normal_intake",
        facts={
            "resolved_destination": Slot(value="Goa", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "party_size": Slot(value=2, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "budget_min": Slot(value=20000, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
        }
    )
    # With 5% margin, 20000 - 31500 = -11500. -0.3 * 31500 = -9450. -11500 < -9450 => infeasible.
    
    # Let's adjust the test to be simpler:
    # Budget 25000. Base cost 30000.
    # Margin 0% => estimated 30000. gap -5000. threshold -0.3*30000 = -9000. status 'tight'.
    # Margin 100% => estimated 60000. gap -35000. threshold -0.3*60000 = -18000. status 'infeasible'.
    
    packet_simple = CanonicalPacket(
        packet_id="test-packet-simple",
        operating_mode="normal_intake",
        facts={
            "resolved_destination": Slot(value="Goa", confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "party_size": Slot(value=2, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
            "budget_min": Slot(value=25000, confidence=1.0, authority_level=AuthorityLevel.EXPLICIT_USER),
        }
    )
    settings_0 = AgencySettings(agency_id="0", target_margin_pct=0.0)
    result_0 = check_budget_feasibility(packet_simple, agency_settings=settings_0)
    assert result_0["status"] == "tight"
    
    settings_100 = AgencySettings(agency_id="100", target_margin_pct=100.0)
    result_100 = check_budget_feasibility(packet_simple, agency_settings=settings_100)
    assert result_100["status"] == "infeasible"

def test_settings_affect_brand_tone():
    # Setup a decision result
    decision = DecisionResult(
        packet_id="test-packet",
        current_stage="discovery",
        operating_mode="normal_intake",
        decision_state="PROCEED_INTERNAL_DRAFT",
        confidence_score=0.9
    )
    
    settings_direct = AgencySettings(agency_id="direct", brand_tone="direct")
    strategy_direct = build_session_strategy(decision, agency_settings=settings_direct)
    assert strategy_direct.suggested_tone == "direct"
    
    settings_cautious = AgencySettings(agency_id="cautious", brand_tone="cautious")
    strategy_cautious = build_session_strategy(decision, agency_settings=settings_cautious)
    assert strategy_cautious.suggested_tone == "cautious"
