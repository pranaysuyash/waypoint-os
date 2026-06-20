"""Tests for the ClosedLoopLearningAgent — fix candidate generation and shadow testing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.agents.closed_loop_learning import (
    FixCandidate,
    ShadowTestResult,
    build_fix_candidate,
    run_shadow_test,
    ClosedLoopLearningAgent,
    PROCEED_CONFIDENCE_THRESHOLD,
    MAX_REGRESSIONS_BEFORE_REJECT,
)
from src.agents.runtime import WorkItem, WorkStatus, AgentExecutionResult
from src.evals.agentic_feedback import AgenticEvalWorkItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime(2026, 6, 20, 12, 0, 0, tzinfo=timezone.utc)


def _make_work_item(**overrides: Any) -> AgenticEvalWorkItem:
    defaults = dict(
        failure_signature="destination_missing|openai|gpt-4|extraction_failed|1|0",
        failure_layer="extraction",
        next_fix_layer="prompt",
        occurrences=5,
        first_seen=NOW - timedelta(days=7),
        last_seen=NOW,
        sample_events=["evt_001", "evt_002", "evt_003"],
        severity="medium",
        proposed_change="Version prompts and add schema-aware guidance at constrained fields.",
        expected_improvement="Increase extraction completeness and reduce downstream manual fixups.",
        regression_risk="Prompt edits may overfit to one artifact subset.",
        rerun_subset="Re-run the last 10 failed signatures in shadow mode.",
        owner="prompt-engineering",
    )
    defaults.update(overrides)
    return AgenticEvalWorkItem(**defaults)


def _make_eval_event(
    failure_layer: str = "extraction",
    failure_signature: str = "destination_missing|openai|gpt-4|extraction_failed|1|0",
    review_outcome: str | None = None,
    fallback_result: str | None = None,
) -> dict[str, Any]:
    return {
        "id": f"evt_{failure_layer}_001",
        "trip_id": "trip_test_001",
        "event_category": "extraction",
        "event_type": "extraction_run_failed",
        "subject_type": "trip",
        "subject_id": "trip_test_001",
        "created_at": NOW.isoformat(),
        "event_metadata": {
            "failure_signature": failure_signature,
            "failure_layer": failure_layer,
            "next_fix_layer": "prompt",
            "review_outcome": review_outcome,
            "fallback_result": fallback_result,
            "provider": "openai",
            "model": "gpt-4",
        },
    }


def _make_trip(
    trip_id: str = "trip_test_001",
    status: str = "discovery",
    eval_events: list[dict[str, Any]] | None = None,
    existing_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trip: dict[str, Any] = {
        "id": trip_id,
        "status": status,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    if eval_events is not None:
        trip["execution_events"] = eval_events
    if existing_candidate is not None:
        trip["closed_loop_fix_candidate"] = existing_candidate
    return trip


# ---------------------------------------------------------------------------
# Fake TripRepository
# ---------------------------------------------------------------------------

class FakeTripRepo:
    def __init__(self, trips: list[dict[str, Any]] | None = None):
        self._trips = {t["id"]: dict(t) for t in (trips or [])}
        self._updates: list[tuple[str, dict[str, Any]]] = []

    def list_active(self) -> list[dict[str, Any]]:
        return list(self._trips.values())

    def update_trip(self, trip_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        self._updates.append((trip_id, updates))
        if trip_id in self._trips:
            self._trips[trip_id].update(updates)
            return dict(self._trips[trip_id])
        return None


# ---------------------------------------------------------------------------
# FixCandidate tests
# ---------------------------------------------------------------------------

class TestFixCandidate:
    def test_builds_candidate_from_work_item(self):
        work_item = _make_work_item()
        candidate = build_fix_candidate(work_item)

        assert isinstance(candidate, FixCandidate)
        assert candidate.failure_signature == work_item.failure_signature
        assert candidate.failure_layer == "extraction"
        assert candidate.next_fix_layer == "prompt"
        assert candidate.occurrences == 5
        assert candidate.owner == "prompt-engineering"
        assert candidate.candidate_id.startswith("fix_")
        assert candidate.created_at  # auto-populated

    def test_candidate_to_dict_roundtrips(self):
        work_item = _make_work_item()
        candidate = build_fix_candidate(work_item)
        d = candidate.to_dict()

        assert d["failure_signature"] == work_item.failure_signature
        assert d["occurrences"] == 5
        assert "candidate_id" in d
        assert "created_at" in d

    def test_unknown_layer_uses_fallback_recommendations(self):
        work_item = _make_work_item(
            failure_layer="mystery_layer",
            next_fix_layer="mystery_layer",
            proposed_change=None,
            expected_improvement=None,
            regression_risk=None,
            rerun_subset=None,
            owner=None,
        )
        candidate = build_fix_candidate(work_item)

        # Should fall back to "unknown" layer recommendations
        assert candidate.owner == "agentic-eval-loop"
        assert "observability" in candidate.proposed_change.lower()

    def test_candidate_id_is_deterministic(self):
        work_item = _make_work_item()
        c1 = build_fix_candidate(work_item)
        c2 = build_fix_candidate(work_item)
        assert c1.candidate_id == c2.candidate_id


# ---------------------------------------------------------------------------
# ShadowTestResult tests
# ---------------------------------------------------------------------------

class TestShadowTest:
    def test_proceed_when_high_fix_rate(self):
        """When the proposed fix targets the right layer, expect proceed."""
        work_item = _make_work_item()
        candidate = build_fix_candidate(work_item)

        # All sample events fail at the next_fix_layer (prompt)
        sample_events = [
            _make_eval_event(failure_layer="prompt") for _ in range(5)
        ]

        result = run_shadow_test(candidate, sample_events)

        assert result.verdict == "proceed"
        assert result.simulated_fixes == 5
        assert result.simulated_regressions == 0
        assert result.confidence_delta > 0

    def test_reject_when_regressions_exceed_threshold(self):
        """When too many regressions, expect reject."""
        work_item = _make_work_item(regression_risk="Prompt edits may overfit to one artifact subset.")
        candidate = build_fix_candidate(work_item)

        # Events that fail at the failure_layer (not next_fix_layer)
        # With overfit risk, these become regressions
        sample_events = [
            _make_eval_event(failure_layer="extraction") for _ in range(5)
        ]

        result = run_shadow_test(candidate, sample_events)

        assert result.verdict == "reject"
        assert result.simulated_regressions >= MAX_REGRESSIONS_BEFORE_REJECT

    def test_defer_when_marginal(self):
        """When improvement is marginal, expect defer."""
        work_item = _make_work_item(regression_risk="Low regression risk; changes are isolated to prompt layer.")
        candidate = build_fix_candidate(work_item)

        # Mix: some at next_fix_layer, some at failure_layer (no overfit risk → unchanged)
        sample_events = [
            _make_eval_event(failure_layer="prompt"),       # fix
            _make_eval_event(failure_layer="extraction"),   # unchanged (no overfit)
            _make_eval_event(failure_layer="extraction"),   # unchanged
            _make_eval_event(failure_layer="timeout"),      # different layer → unchanged
        ]

        result = run_shadow_test(candidate, sample_events)

        assert result.verdict in ("proceed", "defer")
        assert result.simulated_fixes == 1
        assert result.simulated_regressions == 0
        assert result.simulated_unchanged == 3
        assert result.confidence_delta == pytest.approx(0.25, abs=0.01)

    def test_reject_when_no_improvement(self):
        """When no fixes and regressions, expect reject."""
        work_item = _make_work_item(regression_risk="High overfit risk.")
        candidate = build_fix_candidate(work_item)

        sample_events = [
            _make_eval_event(failure_layer="parser"),
            _make_eval_event(failure_layer="parser"),
        ]

        result = run_shadow_test(candidate, sample_events)

        assert result.verdict == "reject"
        assert result.simulated_fixes == 0

    def test_empty_samples_gets_safe_defaults(self):
        work_item = _make_work_item()
        candidate = build_fix_candidate(work_item)

        result = run_shadow_test(candidate, [])

        assert result.sample_count == 0
        assert result.verdict in ("proceed", "defer", "reject")
        assert result.rationale  # should have some text

    def test_shadow_result_to_dict(self):
        work_item = _make_work_item()
        candidate = build_fix_candidate(work_item)
        result = run_shadow_test(candidate, [_make_eval_event()])

        d = result.to_dict()
        assert "candidate_id" in d
        assert "verdict" in d
        assert "confidence_delta" in d
        assert "run_at" in d


# ---------------------------------------------------------------------------
# ClosedLoopLearningAgent scan tests
# ---------------------------------------------------------------------------

class TestClosedLoopLearningAgentScan:
    def test_scans_trips_with_eval_events(self):
        """Agent should yield WorkItems for trips with repeated failure signatures."""
        events = [_make_eval_event() for _ in range(5)]
        trip = _make_trip(eval_events=events)
        repo = FakeTripRepo([trip])

        agent = ClosedLoopLearningAgent(min_occurrences=3)
        work_items = list(agent.scan(repo))

        # Should produce at least one work item for the repeated failure
        assert len(work_items) >= 1
        assert work_items[0].agent_name == "closed_loop_learning_agent"

    def test_skips_terminal_trips(self):
        trip = _make_trip(status="closed", eval_events=[_make_eval_event()])
        repo = FakeTripRepo([trip])

        agent = ClosedLoopLearningAgent(min_occurrences=3)
        work_items = list(agent.scan(repo))

        assert len(work_items) == 0

    def test_skips_trips_with_existing_candidate(self):
        events = [_make_eval_event() for _ in range(5)]
        existing = {"candidate_id": "fix_abc", "failure_signature": "some_sig"}
        trip = _make_trip(eval_events=events, existing_candidate=existing)
        repo = FakeTripRepo([trip])

        agent = ClosedLoopLearningAgent(min_occurrences=3)
        work_items = list(agent.scan(repo))

        # Should skip because a candidate already exists
        assert len(work_items) == 0

    def test_no_events_means_no_work_items(self):
        trip = _make_trip(eval_events=[])
        repo = FakeTripRepo([trip])

        agent = ClosedLoopLearningAgent(min_occurrences=3)
        work_items = list(agent.scan(repo))

        assert len(work_items) == 0

    def test_events_below_threshold_yield_no_work_items(self):
        """Fewer than min_occurrences events should not generate a work item."""
        events = [_make_eval_event() for _ in range(2)]
        trip = _make_trip(eval_events=events)
        repo = FakeTripRepo([trip])

        agent = ClosedLoopLearningAgent(min_occurrences=3)
        work_items = list(agent.scan(repo))

        assert len(work_items) == 0


# ---------------------------------------------------------------------------
# ClosedLoopLearningAgent execute tests
# ---------------------------------------------------------------------------

class TestClosedLoopLearningAgentExecute:
    def _make_work_item(self, trip_id: str = "trip_test_001") -> WorkItem:
        return WorkItem(
            agent_name="closed_loop_learning_agent",
            trip_id=trip_id,
            action="generate_fix_candidate",
            idempotency_key=f"closed_loop_learning_agent:{trip_id}:test_marker",
            payload={
                "failure_signature": "dest_missing|openai|gpt-4|extraction_failed|1|0",
                "failure_layer": "extraction",
                "next_fix_layer": "prompt",
                "occurrences": 5,
                "first_seen": (NOW - timedelta(days=7)).isoformat(),
                "last_seen": NOW.isoformat(),
                "sample_events": ["evt_001", "evt_002", "evt_003"],
                "severity": "medium",
                "proposed_change": "Version prompts and add schema-aware guidance.",
                "expected_improvement": "Increase extraction completeness.",
                "regression_risk": "Prompt edits may overfit.",
                "rerun_subset": "Re-run the last 10 failed signatures.",
                "owner": "prompt-engineering",
            },
        )

    def test_execute_produces_fix_candidate_and_shadow(self):
        trip = _make_trip()
        repo = FakeTripRepo([trip])
        agent = ClosedLoopLearningAgent()
        work_item = self._make_work_item()

        result = agent.execute(work_item, repo)

        assert result.success is True
        assert result.status == WorkStatus.COMPLETED
        assert "fix_candidate" in result.output
        assert "shadow_test" in result.output
        assert "verdict" in result.output
        assert result.output["verdict"] in ("proceed", "defer", "reject")

    def test_execute_updates_trip(self):
        trip = _make_trip()
        repo = FakeTripRepo([trip])
        agent = ClosedLoopLearningAgent()
        work_item = self._make_work_item()

        agent.execute(work_item, repo)

        updated_trip = repo._trips["trip_test_001"]
        assert "closed_loop_fix_candidate" in updated_trip
        assert "closed_loop_shadow_test" in updated_trip
        assert "closed_loop_verdict" in updated_trip
        assert updated_trip["last_agent_action"] == "closed_loop_learning_agent"

    def test_execute_fails_on_missing_signature(self):
        trip = _make_trip()
        repo = FakeTripRepo([trip])
        agent = ClosedLoopLearningAgent()
        work_item = WorkItem(
            agent_name="closed_loop_learning_agent",
            trip_id="trip_test_001",
            action="generate_fix_candidate",
            idempotency_key="test",
            payload={},  # Missing failure_signature
        )

        result = agent.execute(work_item, repo)

        assert result.success is False
        assert "failure_signature" in result.reason.lower() or "missing" in result.reason.lower()

    def test_execute_handles_trip_not_found(self):
        repo = FakeTripRepo([])  # No trips
        agent = ClosedLoopLearningAgent()
        work_item = self._make_work_item(trip_id="nonexistent")

        result = agent.execute(work_item, repo)

        # Should still succeed — the agent generates the candidate even if trip isn't in repo
        # The update_trip will return None → RETRY_PENDING
        assert result.success is False

    def test_execute_shadow_test_result_includes_metrics(self):
        trip = _make_trip()
        repo = FakeTripRepo([trip])
        agent = ClosedLoopLearningAgent()
        work_item = self._make_work_item()

        result = agent.execute(work_item, repo)

        shadow = result.output.get("shadow_test", {})
        assert "sample_count" in shadow
        assert "simulated_fixes" in shadow
        assert "simulated_regressions" in shadow
        assert "confidence_delta" in shadow
        assert "verdict" in shadow
        assert "rationale" in shadow


# ---------------------------------------------------------------------------
# AgentDefinition tests
# ---------------------------------------------------------------------------

class TestAgentDefinition:
    def test_definition_is_complete(self):
        defn = ClosedLoopLearningAgent.definition
        assert defn.name == "closed_loop_learning_agent"
        assert defn.trigger_contract
        assert defn.input_contract
        assert defn.output_contract
        assert defn.idempotency_contract
        assert defn.failure_contract
        assert defn.retry_policy.max_attempts == 3

    def test_definition_to_dict(self):
        d = ClosedLoopLearningAgent.definition.to_dict()
        assert "name" in d
        assert "retry_policy" in d
        assert d["retry_policy"]["max_attempts"] == 3
