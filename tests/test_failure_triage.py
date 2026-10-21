"""Tests for Run-Failure Triage Second Opinion (Lane A5)."""

import pytest
from unittest.mock import MagicMock
from spine_api.failure_taxonomy import FailureClass
from src.decision.failure_triage import FailureTriageEngine
from src.llm.typesafe_client import TypesafeJevClient


def test_heuristic_triage_policy_block():
    engine = FailureTriageEngine()
    opinion = engine.evaluate_failure(
        error_message="Leakage detected in proposal output: phone number leaked",
        traceback_text="Traceback: File validation.py line 42 in check_pii_leakage",
        stage="enrichment",
    )

    assert opinion.recommended_class == FailureClass.POLICY_BLOCK
    assert opinion.is_requeueable is False
    assert opinion.requires_human_escalation is True
    assert opinion.model == "heuristic"


def test_heuristic_triage_tool_network_timeout():
    engine = FailureTriageEngine()
    opinion = engine.evaluate_failure(
        error_message="HTTPError: connection timeout after 30s",
        traceback_text="Traceback: File httpx.py line 100 in send",
        stage="flight_search",
    )

    assert opinion.recommended_class == FailureClass.TOOL
    assert opinion.is_requeueable is True
    assert opinion.requires_human_escalation is False


def test_jev_triage_mocked():
    mock_jev = MagicMock(spec=TypesafeJevClient)
    mock_jev.is_available.return_value = True
    mock_jev.model = "jev-1.13.0"
    mock_jev.raw_query.return_value = {
        "model": "jev-1.13.0",
        "answers": {
            "failure_class": {
                "type": "choice",
                "choice": "state",
                "confidence": 0.92,
                "probabilities": {"state": 0.88, "tool": 0.08, "verification": 0.04},
            },
            "severity": {
                "type": "score",
                "score": 2.8,  # out of 3 -> normalized ~9.33
            },
        },
    }

    engine = FailureTriageEngine(jev_client=mock_jev)
    opinion = engine.evaluate_failure(
        error_message="DatabaseIntegrityError: foreign key violation on trip_ledger",
        traceback_text="Traceback: File sqlite.py line 88 in commit",
        stage="persistence",
    )

    assert opinion.recommended_class == FailureClass.STATE
    assert opinion.is_requeueable is False
    assert opinion.requires_human_escalation is True
    assert opinion.confidence == 0.92
    assert opinion.severity_score == pytest.approx(9.33, abs=0.1)
    assert opinion.model == "jev-1.13.0"
