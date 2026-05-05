from src.agents.risk_contracts import feasibility_constraint_to_structured, to_structured_risk


def test_to_structured_risk_normalizes_fields():
    risk = to_structured_risk(
        flag="weather_monsoon",
        severity="medium",
        category="weather",
        message="Monsoon window risk",
        details={"risk_type": "monsoon"},
        detected_by="unit_test",
    )
    assert risk["flag"] == "weather_monsoon"
    assert risk["severity"] == "medium"
    assert risk["category"] == "weather"
    assert risk["detected_by"] == "unit_test"
    assert risk["details"]["risk_type"] == "monsoon"


def test_feasibility_constraint_to_structured_maps_hard_to_high():
    constraint = {
        "category": "routing",
        "severity": "hard",
        "message": "Tight connections detected",
        "recommendation": "Add layover buffer",
    }
    risk = feasibility_constraint_to_structured(constraint, "constraint_feasibility_agent")
    assert risk["severity"] == "high"
    assert risk["category"] == "routing"
    assert risk["flag"] == "routing_risk"

