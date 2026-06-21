"""End-to-end pipeline eval — raw input → expected extraction → expected decision.

This module evaluates the full pipeline by comparing actual outputs at each
stage against expected values defined in golden pipeline fixtures.

Fixture format
--------------
Each fixture represents a single trip scenario with:

- ``raw_input``: The raw user note and metadata that enters the pipeline.
- ``extraction``: Expected extracted fields (passport, visa, insurance).
- ``agents``: Expected agent outputs at each pipeline stage.
- ``decision``: Expected final trip state after all agents have run.

The runner compares actual outputs (when provided) against expected values
and produces per-stage and per-field accuracy metrics.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Fixture model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PipelineFixture:
    """One end-to-end pipeline test case."""

    fixture_id: str
    description: str
    difficulty: str  # easy | medium | hard
    tags: list[str]
    raw_input: dict[str, Any]
    expected_extraction: dict[str, Any]
    expected_agents: dict[str, dict[str, Any]]
    expected_decision: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineFixture":
        return cls(
            fixture_id=data["fixture_id"],
            description=data.get("description", ""),
            difficulty=data.get("difficulty", "medium"),
            tags=data.get("tags", []),
            raw_input=data.get("raw_input", {}),
            expected_extraction=data.get("expected_extraction", {}),
            expected_agents=data.get("expected_agents", {}),
            expected_decision=data.get("expected_decision", {}),
        )


def load_pipeline_fixtures(path: Path | str) -> list[PipelineFixture]:
    """Load pipeline fixtures from a JSON file or directory of JSON files."""
    p = Path(path)
    if p.is_file():
        candidates = [p]
    else:
        candidates = sorted(p.rglob("*.json"))
    fixtures: list[PipelineFixture] = []
    for candidate in candidates:
        data = json.loads(candidate.read_text())
        if isinstance(data, list):
            fixtures.extend(PipelineFixture.from_dict(item) for item in data)
        else:
            fixtures.append(PipelineFixture.from_dict(data))
    return fixtures


# ---------------------------------------------------------------------------
# Per-field comparison (uses shared utilities)
# ---------------------------------------------------------------------------

from src.evals.audit.comparison import normalise as _normalise, values_match as _values_match


@dataclass(slots=True)
class FieldResult:
    """Result of comparing one field at one stage."""

    stage: str
    field_path: str
    expected: Any
    actual: Any
    is_match: bool


@dataclass(slots=True)
class StageResult:
    """Aggregated results for one pipeline stage."""

    stage: str
    total_fields: int = 0
    matched_fields: int = 0
    field_results: list[FieldResult] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.matched_fields / self.total_fields if self.total_fields > 0 else 0.0

    @property
    def passed(self) -> bool:
        return self.accuracy >= 0.8  # 80% threshold for stage pass


@dataclass(slots=True)
class PipelineComparison:
    """Full comparison result for one pipeline fixture."""

    fixture: PipelineFixture
    stages: dict[str, StageResult] = field(default_factory=dict)

    @property
    def overall_accuracy(self) -> float:
        total = sum(s.total_fields for s in self.stages.values())
        matched = sum(s.matched_fields for s in self.stages.values())
        return matched / total if total > 0 else 0.0

    @property
    def all_stages_pass(self) -> bool:
        return all(s.passed for s in self.stages.values()) if self.stages else False

    def summary(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture.fixture_id,
            "overall_accuracy": round(self.overall_accuracy, 4),
            "all_stages_pass": self.all_stages_pass,
            "stages": {
                name: {
                    "accuracy": round(s.accuracy, 4),
                    "passed": s.passed,
                    "total_fields": s.total_fields,
                    "matched_fields": s.matched_fields,
                }
                for name, s in self.stages.items()
            },
        }


# ---------------------------------------------------------------------------
# Comparison runner
# ---------------------------------------------------------------------------

def _compare_dict(
    expected: dict[str, Any],
    actual: dict[str, Any],
    stage: str,
    prefix: str = "",
) -> list[FieldResult]:
    """Recursively compare two dicts, producing FieldResult per leaf."""
    results: list[FieldResult] = []
    all_keys = set(expected) | set(actual)
    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        exp_val = expected.get(key)
        act_val = actual.get(key)

        if isinstance(exp_val, dict) and isinstance(act_val, dict):
            results.extend(_compare_dict(exp_val, act_val, stage, path))
        elif isinstance(exp_val, list) and isinstance(act_val, list):
            # Compare list lengths and elements positionally
            results.append(FieldResult(
                stage=stage, field_path=f"{path}.length",
                expected=len(exp_val), actual=len(act_val),
                is_match=len(exp_val) == len(act_val),
            ))
            for i, (e, a) in enumerate(zip(exp_val, act_val)):
                if isinstance(e, dict) and isinstance(a, dict):
                    results.extend(_compare_dict(e, a, stage, f"{path}[{i}]"))
                else:
                    results.append(FieldResult(
                        stage=stage, field_path=f"{path}[{i}]",
                        expected=e, actual=a,
                        is_match=_values_match(e, a),
                    ))
        else:
            results.append(FieldResult(
                stage=stage, field_path=path,
                expected=exp_val, actual=act_val,
                is_match=_values_match(exp_val, act_val),
            ))
    return results


def compare_pipeline_fixture(
    fixture: PipelineFixture,
    actual: dict[str, Any] | None = None,
) -> PipelineComparison:
    """Compare a pipeline fixture's expected outputs against actuals.

    When ``actual`` is None, all fields are treated as missing (false negatives
    for non-null expected values).  This establishes a baseline worst-case.
    """
    comp = PipelineComparison(fixture=fixture)

    if actual is None:
        actual = {}

    stage_map = {
        "extraction": (fixture.expected_extraction, actual.get("extraction", {})),
        "agents": (fixture.expected_agents, actual.get("agents", {})),
        "decision": (fixture.expected_decision, actual.get("decision", {})),
    }

    for stage_name, (expected, actual_stage) in stage_map.items():
        field_results = _compare_dict(
            expected if isinstance(expected, dict) else {"_root": expected},
            actual_stage if isinstance(actual_stage, dict) else {"_root": actual_stage},
            stage=stage_name,
        )
        matched = sum(1 for fr in field_results if fr.is_match)
        comp.stages[stage_name] = StageResult(
            stage=stage_name,
            total_fields=len(field_results),
            matched_fields=matched,
            field_results=field_results,
        )

    return comp


# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PipelineEvalReport:
    """Aggregate report across all pipeline fixtures."""

    total_fixtures: int = 0
    comparisons: list[PipelineComparison] = field(default_factory=list)
    by_difficulty: dict[str, dict[str, float]] = field(default_factory=dict)
    overall_accuracy: float = 0.0
    stage_accuracies: dict[str, float] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "total_fixtures": self.total_fixtures,
            "overall_accuracy": round(self.overall_accuracy, 4),
            "stage_accuracies": {
                k: round(v, 4) for k, v in self.stage_accuracies.items()
            },
            "by_difficulty": self.by_difficulty,
            "fixtures_passing": sum(
                1 for c in self.comparisons if c.all_stages_pass
            ),
            "fixtures_failing": sum(
                1 for c in self.comparisons if not c.all_stages_pass
            ),
        }


def run_pipeline_eval(
    fixtures: list[PipelineFixture],
    actual_results: dict[str, dict[str, Any]] | None = None,
) -> PipelineEvalReport:
    """Run the pipeline eval over a set of fixtures.

    Parameters
    ----------
    fixtures
        Golden pipeline fixtures with expected outputs at each stage.
    actual_results
        Pre-computed actual outputs keyed by fixture_id.  When None,
        all fields are treated as missing (baseline worst-case).
    """
    if actual_results is None:
        actual_results = {}

    comparisons: list[PipelineComparison] = []
    for fixture in fixtures:
        actual = actual_results.get(fixture.fixture_id)
        comp = compare_pipeline_fixture(fixture, actual)
        comparisons.append(comp)

    # Overall accuracy
    total_fields = sum(
        s.total_fields
        for c in comparisons
        for s in c.stages.values()
    )
    matched_fields = sum(
        s.matched_fields
        for c in comparisons
        for s in c.stages.values()
    )
    overall = matched_fields / total_fields if total_fields > 0 else 0.0

    # Per-stage accuracy
    stage_totals: dict[str, int] = defaultdict(int)
    stage_matched: dict[str, int] = defaultdict(int)
    for c in comparisons:
        for name, s in c.stages.items():
            stage_totals[name] += s.total_fields
            stage_matched[name] += s.matched_fields
    stage_acc = {
        name: stage_matched[name] / stage_totals[name]
        if stage_totals[name] > 0 else 0.0
        for name in stage_totals
    }

    # By difficulty
    by_diff_totals: dict[str, int] = defaultdict(int)
    by_diff_matched: dict[str, int] = defaultdict(int)
    for c in comparisons:
        d = c.fixture.difficulty
        for s in c.stages.values():
            by_diff_totals[d] += s.total_fields
            by_diff_matched[d] += s.matched_fields
    by_diff = {
        diff: {
            "accuracy": round(by_diff_matched[diff] / by_diff_totals[diff], 4)
            if by_diff_totals[diff] > 0 else 0.0,
            "fixtures": sum(
                1 for c in comparisons if c.fixture.difficulty == diff
            ),
        }
        for diff in sorted(by_diff_totals)
    }

    return PipelineEvalReport(
        total_fixtures=len(fixtures),
        comparisons=comparisons,
        by_difficulty=by_diff,
        overall_accuracy=overall,
        stage_accuracies=stage_acc,
    )
