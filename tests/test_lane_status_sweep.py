"""Lane-status sweep — FND-0352 semantics across ALL model-backed lanes.

The intake ambiguity lane carried the unconfigured-vs-failed distinction
first; this module pins the same contract on every sibling lane so an
operator can always tell "the model lane is deliberately off" from "the
model lane broke":

  model_lane_unconfigured — no credentials (ADR-008 posture; heuristic by design)
  model_call_failed       — configured lane errored (ops should see degradation)
  jev / None              — the model lane served

No provider calls: clients are stubbed at the seam.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock


os.environ.setdefault("RUNNING_TESTS", "1")

MODEL_LANE_UNCONFIGURED = "model_lane_unconfigured"
MODEL_CALL_FAILED = "model_call_failed"


def _available_client(raw_query=None, decide=None):
    client = MagicMock()
    client.is_available.return_value = True
    if raw_query is not None:
        client.raw_query.side_effect = raw_query
    if decide is not None:
        client.decide.side_effect = decide
    return client


class TestLiveTriageLaneStatus:
    def _service(self, client):
        from src.decision.live_triage import LiveMessageTriageService

        svc = LiveMessageTriageService.__new__(LiveMessageTriageService)
        svc.client = client
        return svc

    def test_unconfigured_lane_records_posture(self):
        """No credentials → is_available False → heuristic with the posture
        recorded. (The suite must never fire a live call, so availability is
        stubbed rather than relying on the ambient env.)"""
        unavailable = MagicMock()
        unavailable.is_available.return_value = False
        result = self._service(unavailable).triage("book bali next week")
        assert result.source == "heuristic_fallback"
        assert result.lane_status == MODEL_LANE_UNCONFIGURED
        assert result.to_dict()["lane_status"] == MODEL_LANE_UNCONFIGURED

    def test_failed_lane_records_degradation(self):
        def _boom(**kw):
            raise RuntimeError("down")

        client = MagicMock()
        client.is_available.return_value = True
        client.decide.side_effect = _boom
        result = self._service(client).triage("book bali next week")
        assert result.source == "heuristic_fallback"
        assert result.lane_status == MODEL_CALL_FAILED

    def test_empty_input_records_empty_input(self):
        from src.llm.typesafe_client import TypesafeJevClient

        result = self._service(TypesafeJevClient()).triage("   ")
        assert result.lane_status == "empty_input"


class TestNLPolicyLaneStatus:
    def _clauses(self):
        from src.corporate_policy.nl_evaluator import PolicyClause

        return [PolicyClause(clause_id="c1", description="economy class only flights")]

    def test_unconfigured_lane_records_posture(self):
        from src.corporate_policy.nl_evaluator import NaturalLanguagePolicyEngine

        engine = NaturalLanguagePolicyEngine(jev_client=None)
        result = engine.audit("economy class flights booked", self._clauses())
        assert result.model == "heuristic"
        assert result.lane_status == MODEL_LANE_UNCONFIGURED

    def test_failed_lane_records_degradation(self):
        from src.corporate_policy.nl_evaluator import NaturalLanguagePolicyEngine

        client = _available_client(raw_query=lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
        engine = NaturalLanguagePolicyEngine(jev_client=client)
        result = engine.audit("economy class flights booked", self._clauses())
        assert result.lane_status == MODEL_CALL_FAILED

    def test_jev_lane_records_jev(self):
        from src.corporate_policy.nl_evaluator import NaturalLanguagePolicyEngine

        client = _available_client(
            raw_query=lambda **kw: {
                "model": "jev-test",
                "answers": {"c1": {"noul": 0.95, "confidence": 0.9}},
            }
        )
        engine = NaturalLanguagePolicyEngine(jev_client=client)
        result = engine.audit("economy class flights booked", self._clauses())
        assert result.lane_status == "jev"


class TestFailureTriageLaneStatus:
    def test_unconfigured_lane_records_posture(self):
        from src.decision.failure_triage import FailureTriageEngine

        engine = FailureTriageEngine(jev_client=None)
        opinion = engine.evaluate_failure("KeyError: x", "", stage="strategy")
        assert opinion.model == "heuristic"
        assert opinion.lane_status == MODEL_LANE_UNCONFIGURED

    def test_failed_lane_records_degradation(self):
        from src.decision.failure_triage import FailureTriageEngine

        client = _available_client(raw_query=lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
        engine = FailureTriageEngine(jev_client=client)
        opinion = engine.evaluate_failure("boom", "tb", stage="x")
        assert opinion.lane_status == MODEL_CALL_FAILED

    def test_jev_lane_records_jev(self):
        from src.decision.failure_triage import FailureTriageEngine

        client = _available_client(
            raw_query=lambda **kw: {
                "model": "jev-test",
                "answers": {
                    "failure_class": {"choice": "tool", "confidence": 0.9, "probabilities": {"tool": 0.9}},
                    "severity": {"score": 1.0},
                },
            }
        )
        opinion = FailureTriageEngine(jev_client=client).evaluate_failure("boom", "tb", stage="x")
        assert opinion.lane_status == "jev"
        assert opinion.model == "jev-test"


class TestAskReplyRouterLaneStatus:
    def test_call_failed_is_distinct_from_unavailable(self, monkeypatch):
        """A configured lane that THROWS must record model_call_failed — not
        collapse into 'unavailable' (no credentials) — and always set
        needs_review so the proposal is never auto-applied. The ask-loop env
        gate must be ON to reach the client path."""
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        from src.intake.ask_reply_router import AskReplyRouter

        def _boom(**kw):
            raise RuntimeError("down")

        client = MagicMock()
        client.is_available.return_value = True
        client.raw_query.side_effect = _boom
        router = AskReplyRouter(client=client)
        proposal = router.route("Which city?", "Mumbai")
        assert proposal.source == MODEL_CALL_FAILED
        assert proposal.unparsed is True
        assert proposal.needs_review is True

    def test_unavailable_lane_records_posture(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        from src.intake.ask_reply_router import AskReplyRouter

        unavailable = MagicMock()
        unavailable.is_available.return_value = False
        router = AskReplyRouter(client=unavailable)
        proposal = router.route("Which city?", "Mumbai")
        assert proposal.source == "unavailable"
        assert proposal.needs_review is True
