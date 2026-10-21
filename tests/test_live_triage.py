"""
Unit tests for LiveMessageTriageService and Spine API message triage endpoint.
"""

from __future__ import annotations

from unittest.mock import MagicMock


from src.decision.live_triage import (
    LiveMessageTriageService,
)
from src.llm.typesafe_client import TypesafeJevClient


def test_triage_empty_message():
    service = LiveMessageTriageService(client=None)
    result = service.triage("")
    assert result.source == "heuristic_fallback"
    assert "Empty message" in result.advisory_chips


def test_triage_fallback_urgent_cancellation():
    service = LiveMessageTriageService(client=None)
    text = "Emergency! I need to cancel my flight departing today immediately."
    result = service.triage(text)

    assert result.intent == "cancellation"
    assert result.is_urgent is True
    assert "URGENT: Imminent Travel" in result.advisory_chips
    assert "ACTION: Cancellation Request" in result.advisory_chips


def test_triage_fallback_complaint_and_frustration():
    service = LiveMessageTriageService(client=None)
    text = "This is unacceptable and terrible service! I have been waiting for hours."
    result = service.triage(text)

    assert result.intent == "complaint"
    assert result.frustration_level in ("frustrated", "angry")
    assert any("High Friction" in chip for chip in result.advisory_chips)


def test_triage_jev_mocked_success():
    mock_client = MagicMock(spec=TypesafeJevClient)
    mock_client.is_available.return_value = True
    mock_client.decide.return_value = {
        "intent": "new_booking",
        "is_urgent": False,
        "frustration_level": "calm",
        "policy_risk": False,
        "jev_confidence": 0.88,
        "jev_probabilities": {"intent": {"new_booking": 0.88, "price_quote": 0.12}},
        "reasoning": "[jev] new booking intent with calm tone",
    }

    service = LiveMessageTriageService(client=mock_client)
    result = service.triage("Hello, we would like to book a luxury trip to Switzerland in winter.")

    assert result.source == "jev"
    assert result.intent == "new_booking"
    assert result.is_urgent is False
    assert result.frustration_level == "calm"
    assert result.has_policy_risk is False
    assert result.confidence == 0.88


def test_api_triage_route_success(monkeypatch):
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from spine_api.server import app, _auth_or_skip
    from spine_api.routers import message_triage

    original = dict(app.dependency_overrides)
    app.dependency_overrides[_auth_or_skip] = lambda: None
    app.dependency_overrides[message_triage.get_current_agency] = lambda: SimpleNamespace(id="test_agency_123")

    try:
        client = TestClient(app)
        response = client.post(
            "/api/triage/message",
            json={"text": "I need to cancel my flight departing tomorrow morning urgently!", "channel": "whatsapp"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["intent"] == "cancellation"
        assert data["is_urgent"] is True
        assert data["routing_recommendation"] == "SENIOR_AGENT_DISPATCH"
        assert "URGENT" in data["advisory"]
        assert isinstance(data["latency_ms"], (int, float))
        assert "sentiment" in data
        assert "URGENT: Imminent Travel" in data["advisory_chips"]
    finally:
        app.dependency_overrides = original
