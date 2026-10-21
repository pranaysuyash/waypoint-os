"""
Unit tests for src.llm.typesafe_client.TypesafeJevClient.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.llm.typesafe_client import (
    TypesafeJevClient,
    _resolve_api_key,
)


def test_resolve_api_key_explicit():
    assert _resolve_api_key("custom_key") == "custom_key"


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "env_test_key")
    assert _resolve_api_key() == "env_test_key"


def test_resolve_api_key_from_jev_alias(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("JEV_API_KEY", "alias_key")
    assert _resolve_api_key() == "alias_key"


def test_client_initialization_defaults():
    client = TypesafeJevClient(api_key="test_key")
    assert client.model == "jev-1.13.0"
    assert client.is_available() is True
    assert client._timeout_s == 30.0


def test_count_tokens_and_estimate_cost():
    client = TypesafeJevClient(api_key="test_key")
    text = "Short prompt for token estimation"
    tokens = client.count_tokens(text)
    assert tokens == len(text) // 4
    cost = client.estimate_cost(prompt_tokens=1_000_000, completion_tokens=100)
    # 1M tokens * $0.042 / 1M * 83 INR/USD = 3.486 INR
    assert round(cost, 3) == 3.486


def test_criteria_from_prompt():
    prompt = (
        'Here is the context.\n'
        '- "low" risk: Plenty of lead time for visa processing\n'
        '- "medium" risk: Tight window requiring expedited processing\n'
        '- "high" risk: Impossible timeline, guaranteed to miss flight\n'
    )
    criteria = TypesafeJevClient._criteria_from_prompt(prompt)
    assert criteria["low"] == "Plenty of lead time for visa processing"
    assert criteria["medium"] == "Tight window requiring expedited processing"
    assert criteria["high"] == "Impossible timeline, guaranteed to miss flight"


def test_decide_maps_enum_and_boolean_schema():
    client = TypesafeJevClient(api_key="test_key")

    mock_response = {
        "model": "jev-1.13.0",
        "answers": {
            "q_risk_level": {
                "type": "choice",
                "choice": "medium",
                "probabilities": {"low": 0.1, "medium": 0.8, "high": 0.1},
                "confidence": 0.75,
            },
            "q_is_urgent": {
                "type": "noul",
                "noul": 0.85,
                "confidence": None,
            },
        },
    }

    schema = {
        "type": "object",
        "properties": {
            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "is_urgent": {"type": "boolean"},
        },
    }

    with patch.object(client, "_post", return_value=mock_response) as mock_post:
        result = client.decide(prompt="Test prompt", schema=schema)

        assert mock_post.called
        assert result["risk_level"] == "medium"
        assert result["is_urgent"] is True
        assert result["jev_confidence"] == 0.75
        assert "risk_level=medium" in result["reasoning"]
        assert "is_urgent=True" in result["reasoning"]


def test_decide_rejects_unmappable_schema():
    client = TypesafeJevClient(api_key="test_key")
    schema = {
        "type": "object",
        "properties": {
            "notes": {"type": "string"},
            "count": {"type": "integer"},
        },
    }
    with pytest.raises(ValueError, match="no enum/boolean properties"):
        client.decide(prompt="Test", schema=schema)


def test_decide_preserves_custom_instructions_and_aggregates_min_confidence():
    client = TypesafeJevClient(api_key="test_key")

    mock_response = {
        "model": "jev-1.13.0",
        "answers": {
            "q_category": {
                "type": "choice",
                "choice": "vendor_outage",
                "probabilities": {"vendor_outage": 0.9, "user_error": 0.1},
                "confidence": 0.95,
            },
            "q_needs_escalation": {
                "type": "noul",
                "noul": 0.9,
                "confidence": 0.80,
            },
        },
    }

    schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["vendor_outage", "user_error"],
                "instructions": "Determine the exact failure classification for operations triage.",
            },
            "needs_escalation": {
                "type": "boolean",
                "question": "Should this failure trigger immediate engineer page?",
            },
        },
    }

    with patch.object(client, "_post", return_value=mock_response) as mock_post:
        result = client.decide(prompt="System failed with 503 error", schema=schema)

        payload = mock_post.call_args[1]["payload"]
        assert payload["questions"]["q_category"]["instructions"] == "Determine the exact failure classification for operations triage."
        assert payload["questions"]["q_needs_escalation"]["instructions"] == "Should this failure trigger immediate engineer page?"

        # Conservative confidence aggregation: min(0.95, 0.80) == 0.80
        assert result["jev_confidence"] == 0.80
        assert result["jev_confidences"]["category"] == 0.95
        assert result["jev_confidences"]["needs_escalation"] == 0.80


def test_post_strips_pii_and_adds_delimiters():
    client = TypesafeJevClient(api_key="test_key")

    captured_payload = None

    def fake_post(url, json=None, headers=None):
        nonlocal captured_payload
        captured_payload = json
        from unittest.mock import MagicMock
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"answers": {}}
        return resp

    with patch("httpx.Client.post", side_effect=fake_post):
        client._post({"state": "User John Doe with email john@example.com and phone +1-555-123-4567 requested booking"})

        assert captured_payload is not None
        state = captured_payload["state"]
        assert "john@example.com" not in state
        assert "+1-555-123-4567" not in state
        assert "<user_content nonce=" in state
        assert "</user_content nonce=" in state

