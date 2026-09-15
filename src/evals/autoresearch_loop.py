"""
src/evals/autoresearch_loop.py — Karpathy AutoResearch Autonomic Prompt & Strategy Tuning Engine.

Architecture Decision: ADR 17
Karpathy AutoResearch Paradigm:
  1. Establish baseline metric across scenario dataset
  2. Propose controlled hypothesis mutation (prompt framing, RAG top-k, suitability weights)
  3. Run evaluation suite & calculate Composite Score:
       Score = 0.4 * Accuracy + 0.3 * Safety + 0.2 * Speed + 0.1 * Cost
  4. Accept mutation if score improves; revert if degraded — gated by evidence
     tier (FND-0156): only real-evidence runs enter "accepted" lineage.
     Simulation-tier runs may inform research (the loop still tracks its best
     candidate) but are recorded as blocked from acceptance until an operator
     explicitly promotes them via :meth:`AutoResearchRunner.promote_experiment`
     (audited, append-only promotion record).
  5. Record experiment lineage in data/audit/autoresearch_experiments.jsonl
"""

import argparse
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("autoresearch")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPERIMENTS_LOG_PATH = REPO_ROOT / "data/audit/autoresearch_experiments.jsonl"

# FND-0156: lineage reality tiers — mirror the ADR-008 RealityTier +
# TierMetadata honesty vocabulary (spine_api/core/reality_tier.py). A lineage
# record declares the provenance of the evidence that produced it, and the
# tier governs what the record may claim: exactly as TIER_CAPABILITIES gates
# "can_write_success_events" for features, the tier here gates "accepted".
TIER_SIMULATED = "simulated"
TIER_REAL = "real"

# Promotion states for lineage records.
PROMOTION_STATE_NONE = "none"
PROMOTION_STATE_BLOCKED = "blocked_simulation_tier"

PROMOTION_BLOCK_REASON = (
    "simulation-tier evidence cannot enter accepted lineage; "
    "requires explicit operator promotion (FND-0156)"
)

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
    # FND-0156: provenance of the evidence that produced these metrics.
    reality_tier: str = ""       # TIER_SIMULATED | TIER_REAL
    evaluation_source: str = ""  # e.g. "hardcoded_simulation" | "live_eval_lane"

class EvalSuite(Protocol):
    """Evidence-producing evaluation suite.

    Provenance is bound to the metric producer: an eval suite declares its own
    reality tier, so lineage provenance cannot be detached from (or flipped on)
    the code that actually computed the metrics. Any suite wired into
    :class:`AutoResearchRunner` must expose:

      reality_tier: str          — TIER_SIMULATED or TIER_REAL
      evaluation_source: str     — stable identifier of the grading source
      simulated_runtime_ms: float — constant added to measured wall time
      evaluate(config) -> (accuracy, safety, cost_tokens)
    """

    reality_tier: str
    evaluation_source: str
    simulated_runtime_ms: float

    def evaluate(self, config: ExperimentConfig) -> Tuple[float, float, int]:
        ...

@dataclass(slots=True)
class HardcodedBenchmarkSuite:
    """Current ADR-17 benchmark: hardcoded synthetic accuracy/safety/cost.

    PROVENANCE (PA-11 / FND-0156): these are simulated fixture metrics, not
    D6 lane execution, so this suite is declared TIER_SIMULATED. Results
    produced by it can never be recorded as accepted evidence — only tracked
    as research signal pending operator promotion.
    """

    reality_tier: str = TIER_SIMULATED
    evaluation_source: str = "hardcoded_simulation"
    simulated_runtime_ms: float = 150.0

    def evaluate(self, config: ExperimentConfig) -> Tuple[float, float, int]:
        accuracy = 0.94 if config.rag_top_k >= 5 else 0.88
        safety = 0.99
        if config.suitability_weight_pacing > 1.2:
            accuracy += 0.02
        if config.suitability_weight_rest > 1.2:
            safety += 0.005

        accuracy = min(1.0, accuracy)
        safety = min(1.0, safety)
        cost_tokens = 1200 + (config.rag_top_k * 100)
        return accuracy, safety, cost_tokens

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
    def __init__(self, log_path: Path = EXPERIMENTS_LOG_PATH, eval_suite: EvalSuite | None = None):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # FND-0156: the evidence tier comes from the wired suite (producer-bound
        # provenance), not from a caller-flippable flag. Default is the honest
        # hardcoded simulation suite.
        self.eval_suite: EvalSuite = eval_suite if eval_suite is not None else HardcodedBenchmarkSuite()
        self.best_config = ExperimentConfig(
            experiment_id="baseline_v1",
            prompt_framing="standard_first_principles",
            rag_top_k=5,
            suitability_weight_pacing=1.0,
            suitability_weight_rest=1.0,
        )
        self.best_score = 0.0

    @property
    def evidence_tier(self) -> str:
        """Reality tier of the evidence this runner's suite produces."""
        return self.eval_suite.reality_tier

    def run_eval_suite(self, config: ExperimentConfig) -> EvaluationResult:
        """Run scenario evaluation suite against current experiment configuration.

        Provenance (reality_tier / evaluation_source) is stamped from the wired
        eval suite onto every result so lineage records the evidence source.
        """
        start = time.monotonic()
        accuracy, safety, cost_tokens = self.eval_suite.evaluate(config)
        elapsed_ms = (time.monotonic() - start) * 1000.0 + self.eval_suite.simulated_runtime_ms

        composite = calculate_composite_score(accuracy, safety, elapsed_ms, cost_tokens)

        return EvaluationResult(
            accuracy_score=round(accuracy, 3),
            safety_score=round(safety, 3),
            speed_ms=round(elapsed_ms, 2),
            cost_tokens=cost_tokens,
            composite_score=composite,
            reality_tier=self.eval_suite.reality_tier,
            evaluation_source=self.eval_suite.evaluation_source,
        )

    def log_experiment(self, config: ExperimentConfig, eval_res: EvaluationResult, accepted: bool):
        """Append an experiment lineage record (append-only).

        FND-0156 acceptance gate: ``accepted`` is the loop's *proposed* verdict
        (score improved). It is only honored when the result's evidence tier
        grants acceptance — simulation-tier results are downgraded to
        ``accepted=False`` with the research signal preserved in
        ``proposed_verdict`` and a blocked promotion state.
        """
        tier_allows_acceptance = eval_res.reality_tier == TIER_REAL
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "record_type": "experiment",
            "experiment_id": config.experiment_id,
            "config": asdict(config),
            "result": asdict(eval_res),
            # FND-0156: lineage tier reflects the evidence source (ADR-008
            # RealityTier + TierMetadata pattern). Only real-evidence runs may
            # count as accepted evidence.
            "reality_tier": eval_res.reality_tier,
            "evaluation_source": eval_res.evaluation_source,
            # PA-11 truth labels (preserved): run_eval_suite's default suite is
            # a hardcoded simulation, so non-real lineage stays truth-labeled.
            "simulated": eval_res.reality_tier != TIER_REAL,
            # Research signal: what the loop would have decided on score alone.
            "proposed_verdict": "accepted" if accepted else "rejected",
            # Tier-gated verdict: the actual lineage state.
            "accepted": bool(accepted and tier_allows_acceptance),
            "promotion_state": (
                PROMOTION_STATE_NONE if tier_allows_acceptance else PROMOTION_STATE_BLOCKED
            ),
            "promotion_blocked_reason": None if tier_allows_acceptance else PROMOTION_BLOCK_REASON,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def promote_experiment(
        self,
        experiment_id: str,
        operator: str,
        reason: str,
        evidence_reference: str | None = None,
    ) -> dict:
        """Explicit operator promotion of a simulation-tier experiment into
        accepted lineage (FND-0156 escape hatch with audit trail).

        Appends an ``operator_promotion`` record; the original experiment
        record is never mutated (append-only honesty — the promotion record is
        the audit trail that supersedes its blocked state). Only blocked
        simulation-tier experiments can be promoted; real-tier experiments are
        accepted by the loop directly.

        Raises ValueError for missing operator/reason, unknown experiments,
        already-accepted experiments, and double promotions.
        """
        if not operator or not operator.strip():
            raise ValueError("operator promotion requires a non-empty operator identity")
        if not reason or not reason.strip():
            raise ValueError("operator promotion requires a non-empty reason")

        target: dict | None = None
        already_promoted = False
        if self.log_path.exists():
            for line in self.log_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("experiment_id") != experiment_id:
                    continue
                if rec.get("record_type") == "operator_promotion":
                    already_promoted = True
                elif rec.get("record_type") == "experiment":
                    target = rec
        if target is None:
            raise ValueError(f"unknown experiment '{experiment_id}' in lineage log")
        if already_promoted:
            raise ValueError(
                f"experiment '{experiment_id}' already has an operator promotion record; "
                "double promotion is rejected"
            )
        if target.get("accepted"):
            raise ValueError(
                f"experiment '{experiment_id}' is already accepted; operator promotion not applicable"
            )
        if target.get("reality_tier") != TIER_SIMULATED:
            raise ValueError(
                f"experiment '{experiment_id}' is tier '{target.get('reality_tier')}'; "
                "operator promotion only applies to blocked simulation-tier lineage"
            )

        promotion = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "record_type": "operator_promotion",
            "experiment_id": experiment_id,
            "operator": operator.strip(),
            "reason": reason.strip(),
            "evidence_reference": evidence_reference,
            "promoted_from_reality_tier": target.get("reality_tier"),
            "accepted": True,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(promotion) + "\n")
        logger.info(
            f"Operator promotion recorded: experiment '{experiment_id}' accepted by "
            f"'{operator.strip()}' ({reason.strip()})"
        )
        return promotion

    def run_autoresearch(self, iterations: int = 3) -> ExperimentConfig:
        logger.info(f"Starting Karpathy AutoResearch Loop ({iterations} iterations)...")
        tier = self.evidence_tier
        if tier != TIER_REAL:
            logger.info(
                f"Evidence tier: '{tier}' — results will be tracked as research "
                "signal but cannot enter accepted lineage without operator promotion (FND-0156)."
            )

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
                if tier == TIER_REAL:
                    logger.info(f"Iteration {i}: IMPROVED score {self.best_score} -> {res.composite_score}! Keeping candidate (accepted).")
                else:
                    logger.info(
                        f"Iteration {i}: improved score {self.best_score} -> {res.composite_score} "
                        f"(PROVISIONAL — simulation-tier lineage, NOT accepted evidence; "
                        "operator promotion required per FND-0156). Keeping candidate as research signal."
                    )
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
