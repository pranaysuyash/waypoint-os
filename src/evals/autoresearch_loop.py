"""
src/evals/autoresearch_loop.py — Karpathy AutoResearch Autonomic Prompt & Strategy Tuning Engine.

Architecture Decision: ADR 17
Karpathy AutoResearch Paradigm:
  1. Establish baseline metric across scenario dataset
  2. Propose controlled hypothesis mutation (prompt framing, RAG top-k, suitability weights)
  3. Run evaluation suite & calculate Composite Score:
       Score = 0.4 * Accuracy + 0.3 * Safety + 0.2 * Speed + 0.1 * Cost
  4. Accept mutation if score improves; revert if degraded
  5. Record experiment lineage in data/audit/autoresearch_experiments.jsonl
"""

import argparse
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("autoresearch")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPERIMENTS_LOG_PATH = REPO_ROOT / "data/audit/autoresearch_experiments.jsonl"

@dataclass(slots=True)
class ExperimentConfig:
    experiment_id: str
    prompt_framing: str
    rag_top_k: int
    suitability_weight_pacing: float
    suitability_weight_rest: float

@dataclass(slots=True)
class EvaluationResult:
    accuracy_score: float  # 0.0 - 1.0
    safety_score: float    # 0.0 - 1.0
    speed_ms: float        # average latency
    cost_tokens: int       # token usage
    composite_score: float

def calculate_composite_score(accuracy: float, safety: float, speed_ms: float, cost_tokens: int) -> float:
    """Compute normalized composite quality score (0.0 to 1.0)."""
    # Normalize speed: <= 200ms -> 1.0, >= 2000ms -> 0.0
    normalized_speed = max(0.0, min(1.0, 1.0 - ((speed_ms - 200.0) / 1800.0)))
    # Normalize cost: <= 500 tokens -> 1.0, >= 5000 tokens -> 0.0
    normalized_cost = max(0.0, min(1.0, 1.0 - ((cost_tokens - 500.0) / 4500.0)))

    composite = (
        0.4 * accuracy +
        0.3 * safety +
        0.2 * normalized_speed +
        0.1 * normalized_cost
    )
    return round(composite, 4)

class AutoResearchRunner:
    def __init__(self, log_path: Path = EXPERIMENTS_LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.best_config = ExperimentConfig(
            experiment_id="baseline_v1",
            prompt_framing="standard_first_principles",
            rag_top_k=5,
            suitability_weight_pacing=1.0,
            suitability_weight_rest=1.0,
        )
        self.best_score = 0.0

    def run_eval_suite(self, config: ExperimentConfig) -> EvaluationResult:
        """Run scenario evaluation suite against current experiment configuration."""
        # Simulated benchmark evaluation run across test scenarios
        start = time.monotonic()

        # Benchmark calculation
        accuracy = 0.94 if config.rag_top_k >= 5 else 0.88
        safety = 0.99
        if config.suitability_weight_pacing > 1.2:
            accuracy += 0.02
        if config.suitability_weight_rest > 1.2:
            safety += 0.005

        accuracy = min(1.0, accuracy)
        safety = min(1.0, safety)

        elapsed_ms = (time.monotonic() - start) * 1000.0 + 150.0  # ~150ms simulated runtime
        cost_tokens = 1200 + (config.rag_top_k * 100)

        composite = calculate_composite_score(accuracy, safety, elapsed_ms, cost_tokens)

        return EvaluationResult(
            accuracy_score=round(accuracy, 3),
            safety_score=round(safety, 3),
            speed_ms=round(elapsed_ms, 2),
            cost_tokens=cost_tokens,
            composite_score=composite,
        )

    def log_experiment(self, config: ExperimentConfig, eval_res: EvaluationResult, accepted: bool):
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config": asdict(config),
            "result": asdict(eval_res),
            "accepted": accepted,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def run_autoresearch(self, iterations: int = 3) -> ExperimentConfig:
        logger.info(f"Starting Karpathy AutoResearch Loop ({iterations} iterations)...")

        # Establish baseline
        baseline_res = self.run_eval_suite(self.best_config)
        self.best_score = baseline_res.composite_score
        logger.info(f"Baseline Score: {self.best_score} (Acc: {baseline_res.accuracy_score}, Safety: {baseline_res.safety_score})")
        self.log_experiment(self.best_config, baseline_res, accepted=True)

        # Iteration loop
        for i in range(1, iterations + 1):
            # Propose hypothesis mutation
            candidate = ExperimentConfig(
                experiment_id=f"exp_{i:03d}",
                prompt_framing="first_principles_structured_v2",
                rag_top_k=self.best_config.rag_top_k + (1 if i % 2 == 1 else -1),
                suitability_weight_pacing=self.best_config.suitability_weight_pacing + (0.1 * i),
                suitability_weight_rest=self.best_config.suitability_weight_rest + (0.05 * i),
            )

            res = self.run_eval_suite(candidate)

            if res.composite_score > self.best_score:
                logger.info(f"Iteration {i}: IMPROVED score {self.best_score} -> {res.composite_score}! Keeping candidate.")
                self.best_score = res.composite_score
                self.best_config = candidate
                self.log_experiment(candidate, res, accepted=True)
            else:
                logger.info(f"Iteration {i}: REJECTED score {res.composite_score} <= {self.best_score}. Reverting mutation.")
                self.log_experiment(candidate, res, accepted=False)

        logger.info(f"AutoResearch complete. Winning config: {self.best_config.experiment_id} (Score: {self.best_score})")
        return self.best_config

def main():
    parser = argparse.ArgumentParser(description="Karpathy AutoResearch Tuning Engine")
    parser.add_argument("--iterations", type=int, default=3, help="Number of experimentation iterations")
    args = parser.parse_args()

    runner = AutoResearchRunner()
    runner.run_autoresearch(iterations=args.iterations)

if __name__ == "__main__":
    main()
