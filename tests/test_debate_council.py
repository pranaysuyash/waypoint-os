"""
tests/test_debate_council.py — Tests for Multi-Persona Autonomous Debate Council.
"""

from src.agents.debate_council import MultiPersonaDebateCouncil


def test_debate_council_pareto_optimal_itinerary():
    """Verify well-balanced itinerary achieves Pareto optimality across all 4 personas."""
    itinerary = {
        "pax_count": 2,
        "budget_usd": 6000.0,
        "has_children": False,
        "daily_activity_hours": 5.5,
        "min_layover_minutes": 110,
    }

    result = MultiPersonaDebateCouncil.evaluate_itinerary("itin_luxury_rome", itinerary)
    assert result.overall_consensus_score >= 80.0
    assert result.is_pareto_optimal is True
    assert len(result.persona_critiques) == 4


def test_debate_council_rejects_tight_layover():
    """Verify safety auditor rejects unsafe 40-minute connection preventing false consensus."""
    itinerary = {
        "pax_count": 2,
        "budget_usd": 3000.0,
        "has_children": False,
        "daily_activity_hours": 6.0,
        "min_layover_minutes": 40,  # Unsafe MCT
    }

    result = MultiPersonaDebateCouncil.evaluate_itinerary("itin_tight_hazard", itinerary)
    assert result.is_pareto_optimal is False
    safety_critique = next(c for c in result.persona_critiques if c.persona_name == "Safety & Logistics Auditor")
    assert safety_critique.verdict == "REJECTED"
    assert "extreme misconnection risk" in safety_critique.primary_arguments[0]
