"""
test_autoresearch_loop.py — Unit test suite for Karpathy AutoResearch Tuning Engine.

Architecture Decision: ADR 17
"""

import tempfile
from pathlib import Path

from src.evals.autoresearch_loop import (
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
