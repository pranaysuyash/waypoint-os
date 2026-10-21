"""
Unit tests for IntakeAmbiguityClassifier.
"""

from __future__ import annotations

from unittest.mock import MagicMock


from src.intake.ambiguity_classifier import (
    IntakeAmbiguityClassifier,
)
from src.llm.typesafe_client import TypesafeJevClient


def test_empty_input_escalates():
    classifier = IntakeAmbiguityClassifier(client=None)
    report = classifier.evaluate("")
    assert report.is_escalate is True
    assert report.source == "deterministic_fallback"
    assert len(report.missing_dimensions) == 4


def test_deterministic_fallback_complete_inquiry():
    classifier = IntakeAmbiguityClassifier(client=None)
    text = "We are planning a trip to Paris in June 2027 for a family of 4 with a budget of 10,000 EUR."
    report = classifier.evaluate(text)

    assert report.source == "deterministic_fallback"
    assert report.is_proceed is True
    assert report.dimensions["destination"].is_clear is True
    assert report.dimensions["dates"].is_clear is True
    assert report.dimensions["party"].is_clear is True
    assert report.dimensions["budget"].is_clear is True


def test_deterministic_fallback_missing_destination():
    classifier = IntakeAmbiguityClassifier(client=None)
    text = "Looking for a beach holiday next week for 2 adults, budget 2000 USD."
    report = classifier.evaluate(text)

    assert report.is_proceed is False
    assert report.needs_followup is True
    assert "destination" in report.missing_dimensions


def test_jev_evaluation_mocked_proceed():
    mock_client = MagicMock(spec=TypesafeJevClient)
    mock_client.is_available.return_value = True
    mock_client.decide.return_value = {
        "destination_clarity": True,
        "dates_clarity": True,
        "party_clarity": True,
        "budget_clarity": True,
        "intake_action": "PROCEED",
        "jev_confidence": 0.92,
        "jev_probabilities": {"intake_action": {"PROCEED": 0.92, "ASK_FOLLOWUP": 0.08}},
        "reasoning": "[jev] high clarity across all dimensions",
    }

    classifier = IntakeAmbiguityClassifier(client=mock_client)
    report = classifier.evaluate("Family trip to Tokyo in October for 3 people, budget 500k JPY.")

    assert report.source == "jev"
    assert report.is_proceed is True
    assert report.confidence == 0.92
    assert len(report.missing_dimensions) == 0


def test_jev_evaluation_low_confidence_forces_followup():
    mock_client = MagicMock(spec=TypesafeJevClient)
    mock_client.is_available.return_value = True
    mock_client.decide.return_value = {
        "destination_clarity": True,
        "dates_clarity": False,
        "party_clarity": True,
        "budget_clarity": False,
        "intake_action": "PROCEED",  # Model said proceed but confidence is low
        "jev_confidence": 0.45,       # Below 0.60 threshold
        "jev_probabilities": {"intake_action": {"PROCEED": 0.45, "ASK_FOLLOWUP": 0.55}},
        "reasoning": "[jev] uncertain dates",
    }

    classifier = IntakeAmbiguityClassifier(client=mock_client)
    report = classifier.evaluate("Trip to Rome sometime next year.")

    # Invariant guard overrides PROCEED to ASK_FOLLOWUP when confidence < 0.60
    assert report.action == "ASK_FOLLOWUP"
    assert "dates" in report.missing_dimensions
