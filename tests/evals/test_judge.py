"""Tests for the LLM-as-judge module."""

from unittest.mock import MagicMock

from src.evals.judge import (
    AgentRubric,
    RubricDimension,
    build_default_rubrics,
    DimensionScore,
    JudgeScore,
    judge_agent_output,
    build_judge_report,
)
from src.evals.judge.scorer import (
    _build_dimension_prompt,
    _llm_score_dimension,
)


class TestRubrics:
    def test_build_default_rubrics_covers_known_agents(self):
        rubrics = build_default_rubrics()
        assert "front_door_agent" in rubrics
        assert "document_readiness_agent" in rubrics
        assert "destination_intelligence_agent" in rubrics
        assert "constraint_feasibility_agent" in rubrics
        assert "quality_escalation_agent" in rubrics
        assert "sales_activation_agent" in rubrics
        assert "activity_analyzer" in rubrics

    def test_rubric_has_dimensions(self):
        rubrics = build_default_rubrics()
        for name, rubric in rubrics.items():
            assert isinstance(rubric, AgentRubric)
            assert rubric.agent_name == name
            assert len(rubric.dimensions) >= 2
            for dim in rubric.dimensions:
                assert isinstance(dim, RubricDimension)
                assert dim.weight > 0

    def test_rubric_to_dict(self):
        rubrics = build_default_rubrics()
        fd = rubrics["front_door_agent"]
        d = fd.to_dict()
        assert d["agent_name"] == "front_door_agent"
        assert len(d["dimensions"]) == 4


class TestJudgeAgentOutput:
    def test_front_door_agent_with_full_output(self):
        output = {
            "front_door_assessment": {"assessed_at": "2026-06-21T00:00:00Z"},
            "priority": "high",
            "missing_fields": ["destination", "budget"],
            "acknowledgment_draft": "Thanks for the inquiry. We need a few details: destination and budget.",
        }
        score = judge_agent_output("front_door_agent", "trip_1", output)
        assert score.agent_name == "front_door_agent"
        assert score.trip_id == "trip_1"
        assert score.overall_score > 5.0
        assert len(score.dimension_scores) == 4
        assert score.scored_at != ""

    def test_front_door_agent_with_empty_output(self):
        score = judge_agent_output("front_door_agent", "trip_2", {})
        assert score.overall_score < 7.0
        assert score.passed is False
        assert score.verdict == "fail"

    def test_unknown_agent_returns_needs_review(self):
        score = judge_agent_output("unknown_agent", "trip_3", {})
        assert score.verdict == "needs_review"
        assert score.overall_score == 0.0

    def test_document_readiness_agent(self):
        output = {
            "risk_level": "medium",
            "items": [
                {"category": "visa", "status": "review", "message": "Check visa"},
                {"category": "passport", "status": "ok", "message": "Passport valid"},
                {"category": "insurance", "status": "review", "message": "Check insurance"},
            ],
            "must_confirm": ["visa for destination"],
        }
        score = judge_agent_output("document_readiness_agent", "trip_4", output)
        assert score.overall_score > 5.0
        assert len(score.dimension_scores) == 4

    def test_constraint_feasibility_agent(self):
        output = {
            "hard_blockers": [{"category": "budget", "message": "Below minimum"}],
            "soft_constraints": [{"category": "pace", "message": "Tight schedule"}],
            "missing_facts": ["date_window"],
            "feasibility_status": "blocked",
        }
        score = judge_agent_output("constraint_feasibility_agent", "trip_5", output)
        assert score.overall_score > 5.0
        assert len(score.dimension_scores) == 4

    def test_destination_intelligence_agent(self):
        output = {
            "risk_level": "medium",
            "destinations": [{"destination": "Bali", "status": "fresh"}],
            "recommendations": ["Prepare rain alternatives"],
        }
        score = judge_agent_output("destination_intelligence_agent", "trip_6", output)
        assert score.overall_score > 5.0

    def test_sales_activation_agent(self):
        output = {
            "follow_up_due_date": "2026-06-22T00:00:00Z",
            "follow_up_draft": "Hi, following up on your trip plan.",
        }
        score = judge_agent_output("sales_activation_agent", "trip_7", output)
        assert score.overall_score > 5.0

    def test_quality_escalation_agent(self):
        output = {
            "review_status": "escalated",
            "escalation_reason": "hard_blockers_present",
        }
        score = judge_agent_output("quality_escalation_agent", "trip_8", output)
        assert score.overall_score > 5.0

    def test_score_is_json_serialisable(self):
        import json

        score = judge_agent_output("front_door_agent", "trip_9", {"priority": "normal"})
        dumped = json.dumps(score.to_dict())
        assert "front_door_agent" in dumped


class TestJudgeReport:
    def test_empty_report(self):
        report = build_judge_report([])
        assert report["total_scored"] == 0
        assert report["pass_rate"] == 0.0

    def test_report_with_mixed_scores(self):
        scores = [
            judge_agent_output("front_door_agent", "t1", {
                "front_door_assessment": {"assessed_at": "x"},
                "priority": "high",
                "missing_fields": ["dest"],
                "acknowledgment_draft": "Thanks for the inquiry. We need details.",
            }),
            judge_agent_output("front_door_agent", "t2", {}),
        ]
        report = build_judge_report(scores)
        assert report["total_scored"] == 2
        assert 0.0 <= report["pass_rate"] <= 1.0
        assert "front_door_agent" in report["agents"]
        assert report["agents"]["front_door_agent"]["total_scored"] == 2

    def test_report_is_json_serialisable(self):
        import json

        scores = [
            judge_agent_output("front_door_agent", "t1", {"priority": "high"}),
            judge_agent_output("document_readiness_agent", "t2", {"risk_level": "low", "items": [{"category": "visa", "status": "ok", "message": "ok"}]}),
        ]
        report = build_judge_report(scores)
        dumped = json.dumps(report)
        assert "pass_rate" in dumped

    def test_scoring_method_defaults_to_heuristic(self):
        score = judge_agent_output("front_door_agent", "t_h", {"priority": "high"})
        assert score.scoring_method == "heuristic"


# ---------------------------------------------------------------------------
# Mock LLM client for testing LLM-assisted scoring
# ---------------------------------------------------------------------------


class _MockLLMClient:
    """In-memory mock that satisfies the BaseLLMClient interface."""

    def __init__(self, responses: dict | None = None, available: bool = True):
        self._responses = responses or {}
        self._available = available
        self._calls: list[dict] = []

    def decide(self, prompt: str, schema: dict, temperature: float | None = None) -> dict:
        self._calls.append({"prompt": prompt, "schema": schema, "temperature": temperature})
        # Return matching response if keyed, otherwise default good score
        for key, resp in self._responses.items():
            if key in prompt:
                return resp
        return {"score": 8.5, "reasoning": "Mock LLM: looks good"}

    def is_available(self) -> bool:
        return self._available

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.001

    def ping(self) -> bool:
        return self._available


# ---------------------------------------------------------------------------
# LLM-assisted scoring tests
# ---------------------------------------------------------------------------


class TestLLMAssistedScoring:
    def test_llm_scoring_path_when_client_available(self):
        client = _MockLLMClient()
        output = {
            "front_door_assessment": {"assessed_at": "2026-06-21"},
            "priority": "high",
            "missing_fields": ["destination"],
            "acknowledgment_draft": "Thanks for the inquiry.",
        }
        score = judge_agent_output("front_door_agent", "t1", output, llm_client=client)
        assert score.scoring_method == "llm"
        assert score.overall_score > 0
        assert len(score.dimension_scores) == 4
        # All dimensions should have LLM-generated reasoning
        for ds in score.dimension_scores:
            assert "Mock LLM" in ds.reasoning

    def test_fallback_when_llm_client_unavailable(self):
        client = _MockLLMClient(available=False)
        output = {"priority": "urgent"}
        score = judge_agent_output("front_door_agent", "t1", output, llm_client=client)
        assert score.scoring_method == "heuristic"

    def test_fallback_when_llm_raises_all_heuristic(self):
        class _BrokenClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                raise RuntimeError("API down")

        client = _BrokenClient()
        output = {"priority": "normal"}
        score = judge_agent_output("front_door_agent", "t1", output, llm_client=client)
        # All dimensions fell back → heuristic (no LLM successes)
        assert score.scoring_method == "heuristic"
        assert score.overall_score > 0  # heuristic still produces scores

    def test_fallback_when_llm_returns_invalid_score(self):
        class _BadScoreClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                return {"score": "not_a_number", "reasoning": "oops"}

        client = _BadScoreClient()
        score = judge_agent_output("front_door_agent", "t1", {}, llm_client=client)
        # Invalid score → all dimensions fell back → heuristic
        assert score.scoring_method == "heuristic"

    def test_fallback_when_llm_returns_missing_keys(self):
        class _IncompleteClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                return {"reasoning": "no score provided"}

        client = _IncompleteClient()
        score = judge_agent_output("front_door_agent", "t1", {}, llm_client=client)
        # Missing keys → all dimensions fell back → heuristic
        assert score.scoring_method == "heuristic"

    def test_score_clamping_from_llm(self):
        class _OvershootClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                return {"score": 99.0, "reasoning": "too high"}

        client = _OvershootClient()
        score = judge_agent_output("front_door_agent", "t1", {"priority": "high"}, llm_client=client)
        for ds in score.dimension_scores:
            assert ds.score <= 10.0

    def test_score_clamping_negative_from_llm(self):
        class _NegativeClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                return {"score": -5.0, "reasoning": "negative"}

        client = _NegativeClient()
        score = judge_agent_output("front_door_agent", "t1", {}, llm_client=client)
        for ds in score.dimension_scores:
            assert ds.score >= 0.0

    def test_no_llm_client_uses_heuristic(self):
        output = {"priority": "low"}
        score = judge_agent_output("front_door_agent", "t1", output, llm_client=None)
        assert score.scoring_method == "heuristic"

    def test_build_dimension_prompt_contains_key_elements(self):
        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        prompt = _build_dimension_prompt(
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={"priority": "high"},
            expected=None,
            agent_description="Classifies inquiries",
        )
        assert "front_door_agent" in prompt
        assert "classification_accuracy" in prompt
        assert "0 to 10" in prompt
        assert "priority" in prompt

    def test_build_dimension_prompt_with_expected(self):
        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        prompt = _build_dimension_prompt(
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={"front_door_assessment": {}},
            expected={"front_door_assessment": {"classification": "real_lead"}},
        )
        assert "Expected/reference output" in prompt

    def test_llm_score_dimension_returns_tuple(self):
        client = _MockLLMClient()
        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        result = _llm_score_dimension(
            llm_client=client,
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={"priority": "high"},
        )
        assert result is not None
        score_val, reasoning = result
        assert isinstance(score_val, float)
        assert isinstance(reasoning, str)
        assert 0.0 <= score_val <= 10.0

    def test_llm_score_dimension_returns_none_on_failure(self):
        class _Broken(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                raise ConnectionError("timeout")

        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        result = _llm_score_dimension(
            llm_client=_Broken(),
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={},
        )
        assert result is None

    def test_llm_client_receives_correct_schema(self):
        client = _MockLLMClient()
        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        _llm_score_dimension(
            llm_client=client,
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={"priority": "high"},
        )
        assert len(client._calls) == 1
        call = client._calls[0]
        assert "score" in call["schema"]["properties"]
        assert "reasoning" in call["schema"]["properties"]
        assert call["schema"]["required"] == ["score", "reasoning"]
        assert call["temperature"] == 0.2

    def test_llm_client_called_with_temperature_override(self):
        client = _MockLLMClient()
        rubrics = build_default_rubrics()
        dim = rubrics["front_door_agent"].dimensions[0]
        _llm_score_dimension(
            llm_client=client,
            agent_name="front_door_agent",
            dimension=dim,
            agent_output={},
        )
        assert client._calls[0]["temperature"] == 0.2

    def test_judge_report_includes_scoring_method(self):
        import json

        score = judge_agent_output("front_door_agent", "t1", {"priority": "high"})
        assert "scoring_method" in score.to_dict()
        dumped = json.dumps(score.to_dict())
        assert "scoring_method" in dumped

    def test_mixed_scoring_when_partial_llm_failure(self):
        call_count = 0

        class _PartialClient(_MockLLMClient):
            def decide(self, prompt, schema, temperature=None):
                nonlocal call_count
                call_count += 1
                # Fail on the first call only (classification_accuracy), succeed on rest
                if call_count == 1:
                    raise RuntimeError("transient failure")
                return {"score": 8.0, "reasoning": "Mock LLM"}

        client = _PartialClient()
        output = {"priority": "high", "front_door_assessment": {}}
        score = judge_agent_output("front_door_agent", "t1", output, llm_client=client)
        # 1 dimension fell back, 3 succeeded → mixed
        assert score.scoring_method == "mixed"
        assert score.overall_score > 0
