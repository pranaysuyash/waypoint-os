from src.intake.regional_risk import assess_regional_disruption


def test_regional_risk_conflict_zone_high():
    result = assess_regional_disruption(
        destinations=["Israel"],
        month=7,
        route_hubs=["TLV"],
        flight_legs=2,
    )
    assert result.risk_level == "high"
    assert "active_regional_security_advisory" in result.signals


def test_regional_risk_europe_summer_hub_pressure_medium():
    result = assess_regional_disruption(
        destinations=["France", "Italy", "Switzerland"],
        month=8,
        route_hubs=["CDG", "FRA"],
        flight_legs=4,
    )
    assert result.risk_level in {"medium", "high"}
    assert "europe_summer_hub_pressure" in result.signals

