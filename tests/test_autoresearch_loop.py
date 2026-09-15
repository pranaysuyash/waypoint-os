"""
test_autoresearch_loop.py — Unit test suite for Karpathy AutoResearch Tuning Engine.

Architecture Decision: ADR 17
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.evals.autoresearch_loop import (
    PROMOTION_STATE_BLOCKED,
    PROMOTION_STATE_NONE,
    TIER_REAL,
    TIER_SIMULATED,
    AutoResearchRunner,
    calculate_composite_score,
)

def test_calculate_composite_score_bounds():
    """Verify composite score calculation stays strictly bounded between 0.0 and 1.0."""
    high_score = calculate_composite_score(accuracy=1.0, safety=1.0, speed_ms=100.0, cost_tokens=400)
    assert 0.0 <= high_score <= 1.0
    assert high_score > 0.85

    low_score = calculate_composite_score(accuracy=0.5, safety=0.5, speed_ms=2500.0, cost_tokens=6000)
    assert 0.0 <= low_score <= 1.0
    assert low_score < 0.60

def test_autoresearch_runner_execution():
    """Verify AutoResearch loop executes iterations, computes scores, and logs lineage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "autoresearch_experiments.jsonl"
        runner = AutoResearchRunner(log_path=log_file)

        winning_config = runner.run_autoresearch(iterations=2)
        assert winning_config is not None
        assert log_file.exists()

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 2  # Baseline + at least 1 iteration log
        import json
        for line in lines:
            record = json.loads(line)
            assert record.get("simulated") is True
            assert record.get("evaluation_source") == "hardcoded_simulation"


# ---------------------------------------------------------------------------
# FND-0156: lineage reality tiers — simulation evidence never enters
# "accepted" lineage without an audited operator promotion.
# ---------------------------------------------------------------------------

def _read_records(log_file: Path) -> list[dict]:
    return [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().splitlines()]


def test_simulated_fixture_run_lands_in_simulation_tier_not_accepted():
    """A hardcoded-fixture run must be simulation-tier lineage, never accepted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "autoresearch_experiments.jsonl"
        runner = AutoResearchRunner(log_path=log_file)
        runner.run_autoresearch(iterations=3)

        records = _read_records(log_file)
        assert len(records) >= 4  # baseline + 3 iterations
        for record in records:
            assert record["record_type"] == "experiment"
            assert record["reality_tier"] == TIER_SIMULATED
            assert record["evaluation_source"] == "hardcoded_simulation"
            # Gate: simulated evidence can never be recorded as accepted.
            assert record["accepted"] is False
            assert record["promotion_state"] == PROMOTION_STATE_BLOCKED
            assert "operator promotion" in record["promotion_blocked_reason"]
            # Research signal preserved: proposed verdict still recorded.
            assert record["proposed_verdict"] in {"accepted", "rejected"}

        # The loop still tracked an improved candidate (research signal works).
        assert any(r["proposed_verdict"] == "accepted" for r in records[1:])


def test_real_evidence_run_can_be_accepted():
    """A real-evidence suite may enter accepted lineage directly."""
    @dataclass(slots=True)
    class _LiveLaneSuite:
        reality_tier: str = TIER_REAL
        evaluation_source: str = "live_eval_lane"
        simulated_runtime_ms: float = 0.0

        def evaluate(self, config) -> tuple:
            accuracy = 0.9 if config.rag_top_k >= 5 else 0.8
            return accuracy, 0.97, 1500 + (config.rag_top_k * 100)

    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "autoresearch_experiments.jsonl"
        runner = AutoResearchRunner(log_path=log_file, eval_suite=_LiveLaneSuite())
        assert runner.evidence_tier == TIER_REAL
        runner.run_autoresearch(iterations=1)

        records = _read_records(log_file)
        baseline = records[0]
        assert baseline["reality_tier"] == TIER_REAL
        assert baseline["evaluation_source"] == "live_eval_lane"
        assert baseline["simulated"] is False
        # Real-tier evidence passes the gate: accepted verdict honored.
        assert baseline["accepted"] is True
        assert baseline["promotion_state"] == PROMOTION_STATE_NONE
        assert baseline["promotion_blocked_reason"] is None


def test_promotion_gate_blocks_and_operator_promotion_is_audited():
    """Simulation→accepted is blocked without operator action; promotion appends an audited record."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "autoresearch_experiments.jsonl"
        runner = AutoResearchRunner(log_path=log_file)
        runner.run_autoresearch(iterations=3)

        records = _read_records(log_file)
        improved_but_blocked = [
            r for r in records if r["proposed_verdict"] == "accepted" and r["accepted"] is False
        ]
        assert improved_but_blocked, "expected at least one tier-blocked improved candidate"
        target_id = improved_but_blocked[0]["experiment_id"]

        # Gate: unknown experiment, missing operator, missing reason all blocked.
        with pytest.raises(ValueError):
            runner.promote_experiment("no_such_experiment", operator="ops", reason="r")
        with pytest.raises(ValueError):
            runner.promote_experiment(target_id, operator="", reason="r")
        with pytest.raises(ValueError):
            runner.promote_experiment(target_id, operator="ops", reason="   ")

        # Explicit operator promotion appends an audited record.
        promotion = runner.promote_experiment(
            target_id,
            operator="ops_lead",
            reason="candidate validated against live eval lane manually",
            evidence_reference="runbook://autoresearch/promote-2026-09-14",
        )
        assert promotion["record_type"] == "operator_promotion"
        assert promotion["accepted"] is True
        assert promotion["operator"] == "ops_lead"
        assert promotion["promoted_from_reality_tier"] == TIER_SIMULATED

        records_after = _read_records(log_file)
        promotion_records = [r for r in records_after if r["record_type"] == "operator_promotion"]
        assert len(promotion_records) == 1
        assert promotion_records[0]["experiment_id"] == target_id

        # Append-only honesty: the original experiment record is NOT mutated.
        original = next(
            r
            for r in records_after
            if r["record_type"] == "experiment" and r["experiment_id"] == target_id
        )
        assert original["accepted"] is False
        assert original["promotion_state"] == PROMOTION_STATE_BLOCKED

        # Double promotion rejected.
        with pytest.raises(ValueError):
            runner.promote_experiment(target_id, operator="ops_lead", reason="again")


def test_lineage_records_evidence_source_on_every_record():
    """Every lineage record carries its evidence source and tier provenance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "autoresearch_experiments.jsonl"
        runner = AutoResearchRunner(log_path=log_file)
        best = runner.run_autoresearch(iterations=1)

        for record in _read_records(log_file):
            assert record["reality_tier"] == record["result"]["reality_tier"]
            assert record["evaluation_source"] == record["result"]["evaluation_source"]
            assert record["experiment_id"] == record["config"]["experiment_id"]
        # Runner contract preserved: winning config still returned.
        assert best.experiment_id in {r["experiment_id"] for r in _read_records(log_file)}
