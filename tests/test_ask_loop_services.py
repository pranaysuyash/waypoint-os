"""Tests for the E2 ask-loop production services (2026-10-13)."""

import pytest
from unittest.mock import MagicMock

from src.intake.ask_reply_router import (
    ACT_CONFIDENCE_GATE,
    AskReplyRouter,
)
from src.intake.question_render_selector import (
    QuestionRenderSelector,
    RenderingCandidate,
)
from src.llm.typesafe_client import TypesafeJevClient


@pytest.fixture(autouse=True)
def _flag_env(monkeypatch):
    monkeypatch.delenv("JEV_ASK_LOOP_ENABLED", raising=False)


def _mock_client(raw_response: dict) -> MagicMock:
    client = MagicMock(spec=TypesafeJevClient)
    client.is_available.return_value = True
    client.model = "jev-1.13.0"
    client.raw_query.return_value = raw_response
    return client


# ---------- AskReplyRouter ----------


class TestAskReplyRouterFlagOff:
    def test_disabled_flag_never_routes(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "")
        router = AskReplyRouter(client=_mock_client({}))
        p = router.route("Which city would you fly out from?", "delhi se hi")
        assert p.source == "disabled"
        assert p.needs_review is True
        assert p.routed is False

    def test_unavailable_client_never_routes(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = MagicMock(spec=TypesafeJevClient)
        client.is_available.return_value = False
        router = AskReplyRouter(client=client)
        p = router.route("Which city would you fly out from?", "delhi se hi")
        assert p.source == "unavailable"
        assert p.needs_review is True


class TestAskReplyRouterJev:
    def test_direct_answer_routes_to_field(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client({
            "model": "jev-1.13.0",
            "answers": {
                "answered_field": {
                    "type": "choice", "choice": "origin_city",
                    "probabilities": {"origin_city": 0.98}, "confidence": 1.0,
                },
                "reply_contains_answer": {"type": "noul", "noul": 0.98},
            },
        })
        p = AskReplyRouter(client=client).route("Which city would you fly out from?", "delhi se hi")
        assert p.routed and p.field_name == "origin_city"
        assert not p.unparsed
        assert p.confidence == 1.0
        assert p.needs_review is False
        assert p.source == "jev"

    def test_nonanswer_routes_explicit_unparsed(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client({
            "model": "jev-1.13.0",
            "answers": {
                "answered_field": {
                    "type": "choice", "choice": "unparsed",
                    "probabilities": {"unparsed": 0.99}, "confidence": 0.99,
                },
                "reply_contains_answer": {"type": "noul", "noul": 0.05},
            },
        })
        p = AskReplyRouter(client=client).route("How many travellers?", "Sounds good, will confirm!")
        assert p.unparsed and p.field_name is None
        assert not p.routed

    def test_low_confidence_routes_to_review(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client({
            "model": "jev-1.13.0",
            "answers": {
                "answered_field": {
                    "type": "choice", "choice": "visa_status",
                    "probabilities": {"visa_status": 0.51}, "confidence": 0.51,
                },
                "reply_contains_answer": {"type": "noul", "noul": 0.23},
            },
        })
        p = AskReplyRouter(client=client).route(
            "Do all travellers have valid passports?", "One of us is applying, not sure about the rest."
        )
        assert p.routed  # routed somewhere...
        assert p.needs_review is True  # ...but below the act gate
        assert p.confidence < ACT_CONFIDENCE_GATE

    def test_missing_native_confidence_derives_from_probability(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client({
            "model": "jev-1.13.0",
            "answers": {
                "answered_field": {
                    "type": "choice", "choice": "budget_raw_text",
                    "probabilities": {"budget_raw_text": 0.97},  # no confidence key
                },
                "reply_contains_answer": {"type": "noul", "noul": 0.9},
            },
        })
        p = AskReplyRouter(client=client).route("What is your budget?", "around 150000 total")
        assert p.confidence == pytest.approx(abs(0.97 - 0.5) * 2.0)
        assert p.needs_review is False

    def test_act_gate_constant_matches_e2_validation(self):
        assert ACT_CONFIDENCE_GATE == 0.60


# ---------- QuestionRenderSelector ----------


def _grade_response(intent: float, facts: float, naturalness: float) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {
            "preserves_field_intent": {"type": "noul", "noul": intent},
            "introduces_no_new_facts": {"type": "noul", "noul": facts},
            "traveler_naturalness": {"type": "score", "score": naturalness, "confidence": 0.8},
        },
    }


class TestQuestionRenderSelector:
    def test_flag_off_returns_verbatim(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "")
        sel = QuestionRenderSelector(client=_mock_client({}))
        r = sel.select("origin_city", "Which city would you fly out from?",
                       [RenderingCandidate("Which city will you be flying out from?")])
        assert r.selected == "Which city would you fly out from?"
        assert r.selected_origin == "disabled"
        assert r.source == "disabled"

    def test_best_passing_candidate_selected(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client(None)
        client.raw_query.side_effect = [
            _grade_response(0.95, 0.92, 3.0),  # good: passes
            _grade_response(0.01, 0.90, 5.0),  # drift: fails intent
            _grade_response(0.90, 0.02, 4.0),  # fabricated: fails facts
        ]
        sel = QuestionRenderSelector(client=client)
        r = sel.select("origin_city", "Which city would you fly out from?", [
            RenderingCandidate("Which city will you be flying out from?", origin="template"),
            RenderingCandidate("When would you like to travel?", origin="template"),
            RenderingCandidate("Are you flying out of Mumbai?", origin="ladder"),
        ])
        assert r.selected == "Which city will you be flying out from?"
        assert r.selected_origin == "jev_graded:template"
        assert [g.passes for g in r.grades] == [True, False, False]

    def test_all_fail_falls_back_to_verbatim(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client(None)
        client.raw_query.side_effect = [
            _grade_response(0.01, 0.10, 4.0),
            _grade_response(0.95, 0.02, 4.5),
        ]
        r = QuestionRenderSelector(client=client).select(
            "party_size", "How many travellers will be on this trip?",
            [RenderingCandidate("What is your budget?"), RenderingCandidate("Is it just the two of you?")],
        )
        assert r.selected == "How many travellers will be on this trip?"
        assert r.selected_origin == "verbatim_fallback"

    def test_unavailable_client_falls_back(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = MagicMock(spec=TypesafeJevClient)
        client.is_available.return_value = False
        r = QuestionRenderSelector(client=client).select(
            "origin_city", "Verbatim?", [RenderingCandidate("Fancy?")]
        )
        assert r.selected == "Verbatim?"
        assert r.source == "unavailable"

    def test_grading_exception_rejects_candidate_not_raises(self, monkeypatch):
        monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")
        client = _mock_client(None)
        client.raw_query.side_effect = RuntimeError("typesafe: HTTP 500")
        r = QuestionRenderSelector(client=client).select(
            "origin_city", "Verbatim?", [RenderingCandidate("Fancy?")]
        )
        assert r.selected == "Verbatim?"
        assert r.grades[0].passes is False
