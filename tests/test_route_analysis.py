from src.intake.route_analysis import analyze_route_complexity, parse_itinerary_text


def test_route_analysis_scores_multi_leg_and_transfer_density():
    result = analyze_route_complexity(
        flight_legs=4,
        transfer_like_items=3,
        activity_count=6,
        elderly_count=2,
        toddler_count=1,
    )
    assert result.total_legs == 4
    assert result.complexity_score > 0.7
    assert "multi_leg_flight_fatigue" in result.fatigue_indicators
    assert "elderly_route_tolerance_exceeded" in result.fatigue_indicators
    assert "toddler_route_pacing_pressure" in result.fatigue_indicators


def test_route_analysis_low_complexity_stays_low():
    result = analyze_route_complexity(
        flight_legs=1,
        transfer_like_items=0,
        activity_count=2,
        elderly_count=0,
        toddler_count=0,
    )
    assert result.total_legs == 1
    assert result.complexity_score < 0.2
    assert result.fatigue_indicators == []


def test_parse_itinerary_text_infers_hops_transfers_and_activities():
    parsed = parse_itinerary_text(
        "Fly Paris to Zurich, then to Milan. Airport transfer on arrival. Next day city tour and museum."
    )
    assert parsed["inferred_flight_legs"] >= 2
    assert parsed["inferred_transfer_like_items"] >= 1
    assert parsed["inferred_activity_count"] >= 2
