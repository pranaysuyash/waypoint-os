"""Tests for Natural Language Corporate Policy Conformance Engine (Lane B1)."""

import pytest
from unittest.mock import MagicMock
from src.corporate_policy.nl_evaluator import (
    NaturalLanguagePolicyEngine,
    PolicyClause,
)
from src.llm.typesafe_client import TypesafeJevClient


def test_heuristic_compliant_trip():
    engine = NaturalLanguagePolicyEngine()
    clauses = [
        PolicyClause(
            clause_id="POL-01",
            description="No first class airfare permitted.",
            criticality="mandatory",
        ),
        PolicyClause(
            clause_id="POL-02",
            description="Bookings must not be last minute.",
            criticality="advisory",
        ),
    ]
    itinerary = "Standard economy flight from SFO to NYC departing in 3 weeks, stay at Marriott Courtyard."
    result = engine.audit(itinerary, clauses)

    assert result.ok is True
    assert result.is_compliant is True
    assert len(result.violations) == 0
    assert len(result.warnings) == 0
    assert result.evaluated_clauses_count == 2
    assert result.model == "heuristic"


def test_heuristic_violation_and_advisory():
    engine = NaturalLanguagePolicyEngine()
    clauses = [
        PolicyClause(
            clause_id="POL-01",
            description="No first class airfare permitted.",
            criticality="mandatory",
        ),
        PolicyClause(
            clause_id="POL-02",
            description="Bookings must not be last minute.",
            criticality="advisory",
        ),
    ]
    itinerary = "Booking a First Class seat on Flight 102 with same-day booking / last minute urgency."
    result = engine.audit(itinerary, clauses)

    assert result.ok is True
    assert result.is_compliant is False
    assert len(result.violations) == 1
    assert "POL-01" in result.violations[0]
    assert len(result.warnings) == 1
    assert "POL-02" in result.warnings[0]


def test_jev_policy_audit_mocked():
    mock_jev = MagicMock(spec=TypesafeJevClient)
    mock_jev.is_available.return_value = True
    mock_jev.model = "jev-1.13.0"
    mock_jev.raw_query.return_value = {
        "model": "jev-1.13.0",
        "answers": {
            "POL-01": {"type": "noul", "noul": 0.95, "confidence": 0.90},
            "POL-02": {"type": "noul", "noul": 0.10, "confidence": 0.85},
            "POL-03": {"type": "noul", "noul": 0.40, "confidence": 0.50},  # low confidence
        }
    }

    engine = NaturalLanguagePolicyEngine(jev_client=mock_jev, confidence_threshold=0.65)
    clauses = [
        PolicyClause(clause_id="POL-01", description="Hotel cost within reasonable limits", criticality="mandatory"),
        PolicyClause(clause_id="POL-02", description="Flight is economy", criticality="mandatory"),
        PolicyClause(clause_id="POL-03", description="Sustainability guidelines met", criticality="advisory"),
    ]

    result = engine.audit("Trip to Tokyo staying at Grand Hyatt with business class ticket", clauses)

    assert result.ok is True
    assert result.is_compliant is False
    assert len(result.violations) == 1
    assert "POL-02" in result.violations[0]
    assert len(result.warnings) == 1
    assert "POL-03" in result.warnings[0]
    assert "POL-03" in result.low_confidence_clauses
    assert result.model == "jev-1.13.0"
    assert result.average_confidence == pytest.approx(0.75, abs=0.01)


def test_heuristic_unevaluated_clause_never_false_clears():
    """Regression (2026-10-13 live sweep): the heuristic fallback used to assert
    compliant=True on clauses it had no pattern for — a false all-clear on a
    policy conformance surface. Un-evaluatable clauses must come back as
    unevaluated-for-review instead."""
    engine = NaturalLanguagePolicyEngine()
    clauses = [
        PolicyClause(
            clause_id="POL-01",
            description="Economy class only for flights under 4 hours",
            criticality="mandatory",
        ),
        PolicyClause(
            clause_id="POL-02",
            description="Hotel bookings must be at least 14 days before departure",
            criticality="mandatory",
        ),
        PolicyClause(
            clause_id="POL-99",
            description="Prefer properties with sustainability certification when available",
            criticality="advisory",
        ),
    ]
    violating = (
        "Itinerary: Delhi to Goa, 2h50m direct flight, business class seats. "
        "Hotel: unlisted guesthouse, booked 2 days before departure."
    )
    result = engine.audit(violating, clauses)

    # Business class on a class-restricted clause + 2 days vs 14-day lead are
    # both real violations the heuristic can now prove.
    assert result.is_compliant is False
    assert len(result.violations) == 2
    assert "POL-01" in result.violations[0]
    assert "POL-02" in result.violations[1]

    # The advisory sustainability clause has no deterministic pattern — it must
    # be marked unevaluated, never silently compliant.
    assert result.unevaluated_clauses == ["POL-99"]
    assert result.all_clauses_evaluated is False
    assert all(ev.evaluated for ev in result.evaluations if ev.clause_id != "POL-99")


def test_heuristic_numeric_lead_time_compliant():
    engine = NaturalLanguagePolicyEngine()
    clauses = [
        PolicyClause(
            clause_id="POL-02",
            description="Hotel bookings must be at least 14 days before departure",
            criticality="mandatory",
        ),
    ]
    result = engine.audit(
        "Itinerary: Delhi to Goa, economy seats. Hotel booked 21 days before departure.", clauses
    )
    assert result.is_compliant is True
    assert result.all_clauses_evaluated is True
    assert result.unevaluated_clauses == []


def test_audit_route_populates_violations_detail():
    """FND-0338 / roadmap invariant 3 pin (2026-10-25 audit wave): the route
    handler must populate the declared violations_detail field — machine-readable
    provenance (sourced vs estimated) must travel with each violation, not sit
    computed-but-unwired as the interrupted tranche left it."""
    from unittest.mock import patch

    from spine_api.persistence import TripStore
    from spine_api.routers.corporate_policy import audit_trip_corporate_policy

    trip = {
        "id": "trip_vd",
        "agency_id": "agency_vd",
        "strategy": {"recommended_option": {"name": "Kyoto Villa", "cost": 9000, "currency": "USD"}},
        "packet": {"destination": "Tokyo"},
        "corporate_policy_override": {},
    }
    with patch.object(TripStore, "get_trip_for_agency", return_value=trip):
        res = audit_trip_corporate_policy("trip_vd", "agency_vd")

    # Every nightly-rate and duty-of-care violation must carry its basis.
    for item in res.violations_detail:
        assert item["rule"] in ("nightly_rate_cap", "duty_of_care_high_risk")
        assert item["basis"] in ("sourced_trip_cost", "estimated_default", "sourced_destination")
        assert isinstance(item["enforceable"], bool)

    # A sourced cost must never be mislabeled as estimated (invariant 3).
    nightly = [d for d in res.violations_detail if d["rule"] == "nightly_rate_cap"]
    for d in nightly:
        assert d["basis"] == "sourced_trip_cost"
        assert d["enforceable"] is True
