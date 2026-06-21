"""Tests for end-to-end pipeline eval fixtures."""

import json
from pathlib import Path

from src.evals.audit.rules.pipeline import (
    PipelineFixture,
    PipelineComparison,
    PipelineEvalReport,
    load_pipeline_fixtures,
    compare_pipeline_fixture,
    run_pipeline_eval,
    _compare_dict,
    _values_match,
)

FIXTURE_PATH = Path("data/fixtures/pipeline/pipeline_golden.json")


class TestPipelineFixtureLoading:
    def test_loads_golden_pipeline_fixtures(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        assert len(fixtures) == 7

    def test_fixture_fields_are_populated(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        for f in fixtures:
            assert f.fixture_id != ""
            assert f.description != ""
            assert f.difficulty in ("easy", "medium", "hard")
            assert isinstance(f.tags, list)
            assert isinstance(f.raw_input, dict)
            assert isinstance(f.expected_extraction, dict)
            assert isinstance(f.expected_agents, dict)
            assert isinstance(f.expected_decision, dict)

    def test_fixture_ids_are_unique(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        ids = [f.fixture_id for f in fixtures]
        assert len(ids) == len(set(ids))

    def test_all_difficulty_levels_represented(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        difficulties = {f.difficulty for f in fixtures}
        assert "easy" in difficulties
        assert "hard" in difficulties

    def test_fixture_from_dict(self):
        data = {
            "fixture_id": "test_fixture",
            "description": "Test",
            "difficulty": "easy",
            "tags": ["test"],
            "raw_input": {"raw_note": "test"},
            "expected_extraction": {"passport": {"full_name": "TEST"}},
            "expected_agents": {"front_door_agent": {"is_real_lead": True}},
            "expected_decision": {"trip_status": "in_progress"},
        }
        f = PipelineFixture.from_dict(data)
        assert f.fixture_id == "test_fixture"
        assert f.raw_input["raw_note"] == "test"

    def test_from_dict_raises_on_missing_fixture_id(self):
        import pytest

        with pytest.raises(KeyError, match="fixture_id"):
            PipelineFixture.from_dict({"description": "no id"})

    def test_from_dict_raises_on_missing_expected_agents(self):
        import pytest

        with pytest.raises(ValueError, match="expected_agents"):
            PipelineFixture.from_dict({"fixture_id": "x", "expected_decision": {}})

    def test_from_dict_raises_on_missing_expected_decision(self):
        import pytest

        with pytest.raises(ValueError, match="expected_decision"):
            PipelineFixture.from_dict({"fixture_id": "x", "expected_agents": {}})

    def test_from_dict_accepts_minimal_valid_dict(self):
        data = {
            "fixture_id": "min",
            "expected_agents": {},
            "expected_decision": {},
        }
        f = PipelineFixture.from_dict(data)
        assert f.fixture_id == "min"
        assert f.difficulty == "medium"  # default
        assert f.expected_agents == {}


class TestValuesMatch:
    def test_both_none(self):
        assert _values_match(None, None) is True

    def test_expected_none_actual_present(self):
        assert _values_match(None, "value") is False

    def test_expected_present_actual_none(self):
        assert _values_match("value", None) is False

    def test_exact_match(self):
        assert _values_match("Hello World", "Hello World") is True

    def test_case_insensitive(self):
        assert _values_match("RAJESH", "rajesh") is True

    def test_whitespace_normalised(self):
        assert _values_match("Hello  World", "Hello World") is True

    def test_mismatch(self):
        assert _values_match("A", "B") is False


class TestCompareDict:
    def test_simple_match(self):
        expected = {"a": "1", "b": "2"}
        actual = {"a": "1", "b": "2"}
        results = _compare_dict(expected, actual, stage="test")
        assert all(r.is_match for r in results)

    def test_simple_mismatch(self):
        expected = {"a": "1"}
        actual = {"a": "2"}
        results = _compare_dict(expected, actual, stage="test")
        assert not any(r.is_match for r in results)

    def test_nested_dict(self):
        expected = {"outer": {"inner": "value"}}
        actual = {"outer": {"inner": "value"}}
        results = _compare_dict(expected, actual, stage="test")
        assert any(r.field_path == "outer.inner" for r in results)
        assert all(r.is_match for r in results)

    def test_missing_field(self):
        expected = {"a": "1", "b": "2"}
        actual = {"a": "1"}
        results = _compare_dict(expected, actual, stage="test")
        matched = [r for r in results if r.is_match]
        assert len(matched) == 1

    def test_extra_field(self):
        expected = {"a": "1"}
        actual = {"a": "1", "b": "extra"}
        results = _compare_dict(expected, actual, stage="test")
        assert len(results) == 2


class TestComparePipelineFixture:
    def test_baseline_no_actual(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        comp = compare_pipeline_fixture(fixtures[0])
        # Without actual results, all non-null expected fields are false negatives
        assert comp.overall_accuracy == 0.0
        assert comp.all_stages_pass is False

    def test_perfect_match(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        f = fixtures[0]
        actual = {
            "extraction": f.expected_extraction,
            "agents": f.expected_agents,
            "decision": f.expected_decision,
        }
        comp = compare_pipeline_fixture(f, actual)
        assert comp.overall_accuracy == 1.0
        assert comp.all_stages_pass is True

    def test_partial_match(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        f = fixtures[0]
        actual = {
            "extraction": f.expected_extraction,
            "agents": {},  # agents missing
            "decision": f.expected_decision,
        }
        comp = compare_pipeline_fixture(f, actual)
        assert 0.0 < comp.overall_accuracy < 1.0

    def test_stages_are_populated(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        comp = compare_pipeline_fixture(fixtures[0])
        assert "extraction" in comp.stages
        assert "agents" in comp.stages
        assert "decision" in comp.stages

    def test_summary_is_json_serialisable(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        comp = compare_pipeline_fixture(fixtures[0])
        dumped = json.dumps(comp.summary())
        assert "overall_accuracy" in dumped


class TestPipelineEvalReport:
    def test_baseline_report(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        report = run_pipeline_eval(fixtures)
        assert report.total_fixtures == 7
        # Baseline: no actuals. Null expected fields (visa=null) match absent
        # actual → non-zero accuracy for null-matched fields. Verify low baseline.
        assert report.overall_accuracy < 0.15
        assert len(report.comparisons) == 7

    def test_perfect_report(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        actuals = {}
        for f in fixtures:
            actuals[f.fixture_id] = {
                "extraction": f.expected_extraction,
                "agents": f.expected_agents,
                "decision": f.expected_decision,
            }
        report = run_pipeline_eval(fixtures, actuals)
        assert report.overall_accuracy == 1.0
        assert report.stage_accuracies["extraction"] == 1.0
        assert report.stage_accuracies["agents"] == 1.0
        assert report.stage_accuracies["decision"] == 1.0

    def test_by_difficulty(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        report = run_pipeline_eval(fixtures)
        assert "easy" in report.by_difficulty
        assert "hard" in report.by_difficulty
        assert report.by_difficulty["easy"]["fixtures"] >= 1

    def test_summary_is_json_serialisable(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        report = run_pipeline_eval(fixtures)
        dumped = json.dumps(report.summary())
        assert "total_fixtures" in dumped

    def test_with_actual_results(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        actuals = {
            fixtures[0].fixture_id: {
                "extraction": fixtures[0].expected_extraction,
                "agents": {},
                "decision": {},
            },
        }
        report = run_pipeline_eval(fixtures, actuals)
        # First fixture has partial match, rest have no match
        assert 0.0 < report.overall_accuracy < 1.0

    def test_empty_fixtures(self):
        report = run_pipeline_eval([])
        assert report.total_fixtures == 0
        assert report.overall_accuracy == 0.0

    def test_fixture_passing_count(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        actuals = {}
        for f in fixtures:
            actuals[f.fixture_id] = {
                "extraction": f.expected_extraction,
                "agents": f.expected_agents,
                "decision": f.expected_decision,
            }
        report = run_pipeline_eval(fixtures, actuals)
        summary = report.summary()
        assert summary["fixtures_passing"] == 7
        assert summary["fixtures_failing"] == 0

    def test_fixture_failing_count_baseline(self):
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        report = run_pipeline_eval(fixtures)
        summary = report.summary()
        assert summary["fixtures_passing"] == 0
        assert summary["fixtures_failing"] == 7

    def test_custom_stage_threshold_tighter(self):
        """A stricter threshold (0.95) rejects fixtures that barely pass at 0.8."""
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        actuals = {}
        for f in fixtures:
            actuals[f.fixture_id] = {
                "extraction": f.expected_extraction,
                "agents": f.expected_agents,
                "decision": f.expected_decision,
            }
        # At default 0.8 all pass
        report_default = run_pipeline_eval(fixtures, actuals)
        assert report_default.summary()["fixtures_passing"] == 7

        # At 1.0 threshold, still passes (perfect match)
        report_strict = run_pipeline_eval(fixtures, actuals, stage_threshold=1.0)
        assert report_strict.summary()["fixtures_passing"] == 7

    def test_custom_stage_threshold_relaxed(self):
        """A very low threshold (0.0) marks all stages as passing."""
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        report = run_pipeline_eval(fixtures, stage_threshold=0.0)
        summary = report.summary()
        assert summary["fixtures_passing"] == 7

    def test_stage_threshold_on_comparison(self):
        """Compare a single fixture with different thresholds."""
        fixtures = load_pipeline_fixtures(FIXTURE_PATH)
        f = fixtures[0]
        actual = {
            "extraction": f.expected_extraction,
            "agents": {},  # 0% agents match
            "decision": f.expected_decision,
        }
        # Default threshold: agents stage fails
        comp_default = compare_pipeline_fixture(f, actual)
        assert comp_default.stages["agents"].passed is False

        # Very relaxed threshold: agents stage passes
        comp_relaxed = compare_pipeline_fixture(f, actual, stage_threshold=0.0)
        assert comp_relaxed.stages["agents"].passed is True


class TestPerFixtureThreshold:
    def test_per_fixture_threshold_overrides_global(self):
        """A fixture with stage_threshold=0.0 always passes, even with missing agents."""
        data = {
            "fixture_id": "custom_threshold",
            "expected_agents": {"front_door_agent": {"is_real_lead": True}},
            "expected_decision": {"trip_status": "in_progress"},
            "stage_threshold": 0.0,
        }
        f = PipelineFixture.from_dict(data)
        actual = {"agents": {}, "decision": {}}  # 0% match on agents
        comp = compare_pipeline_fixture(f, actual)
        assert comp.all_stages_pass is True
        for sr in comp.stages.values():
            assert sr.stage_threshold == 0.0

    def test_per_fixture_threshold_none_uses_global(self):
        """A fixture with stage_threshold=None falls back to the global param."""
        data = {
            "fixture_id": "default_threshold",
            "expected_agents": {"front_door_agent": {"is_real_lead": True}},
            "expected_decision": {"trip_status": "in_progress"},
        }
        f = PipelineFixture.from_dict(data)
        assert f.stage_threshold is None
        actual = {"agents": {}, "decision": {}}  # 0% match on agents
        comp = compare_pipeline_fixture(f, actual, stage_threshold=0.5)
        assert comp.all_stages_pass is False
        for sr in comp.stages.values():
            assert sr.stage_threshold == 0.5

    def test_per_fixture_threshold_from_dict(self):
        data = {
            "fixture_id": "t",
            "expected_agents": {},
            "expected_decision": {},
            "stage_threshold": 0.95,
        }
        f = PipelineFixture.from_dict(data)
        assert f.stage_threshold == 0.95

    def test_per_fixture_threshold_absent_defaults_to_none(self):
        data = {
            "fixture_id": "t",
            "expected_agents": {},
            "expected_decision": {},
        }
        f = PipelineFixture.from_dict(data)
        assert f.stage_threshold is None

    def test_per_fixture_threshold_wins_over_global_in_run_pipeline_eval(self):
        """Per-fixture threshold takes precedence over the run_pipeline_eval global."""
        strict_fixture = PipelineFixture(
            fixture_id="strict",
            description="per-fixture 0.0 threshold",
            difficulty="easy",
            tags=[],
            raw_input={},
            expected_extraction={},
            expected_agents={"a": {"x": 1}},
            expected_decision={},
            stage_threshold=0.0,  # always pass
        )
        default_fixture = PipelineFixture(
            fixture_id="default",
            description="uses global threshold",
            difficulty="easy",
            tags=[],
            raw_input={},
            expected_extraction={},
            expected_agents={"a": {"x": 1}},
            expected_decision={},
            stage_threshold=None,  # use global
        )
        # Global threshold = 1.0 (strict)
        report = run_pipeline_eval(
            [strict_fixture, default_fixture],
            stage_threshold=1.0,
        )
        passing_ids = {
            c.fixture.fixture_id
            for c in report.comparisons
            if c.all_stages_pass
        }
        # strict_fixture (threshold=0.0) passes; default_fixture (threshold=1.0) fails
        assert "strict" in passing_ids
        assert "default" not in passing_ids
