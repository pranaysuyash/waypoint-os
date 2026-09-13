#!/usr/bin/env python3
"""
run_hybrid_kdd_experiment.py — KDD experiment harness for the hybrid decision engine.

Ratified posture (owner, 2026-09-11): flag OFF in prod; this harness runs the
evidence experiment that any future flip must be justified by.

Arms:
  A      USE_HYBRID_DECISION_ENGINE=0            deterministic rules (baseline)
  B(m)   USE_HYBRID_DECISION_ENGINE=1            hybrid, model m (cold + warm pass)

Models (run 1, OpenAI-first per owner): openai/gpt-4o-mini, openai/gpt-4o.
Later arms: gemini/*, local SLMs (see C04_SLM_BENCHMARK_PROTOCOL).

Per record per arm the harness records: risks, decision source, llm_used,
llm_model, cost_inr, wall ms, cache provenance, and every LLM call's
prompt/response archived verbatim (KDD mining phase).

Usage:
  .venv/bin/python scripts/run_hybrid_kdd_experiment.py --smoke          # 2 records, 4o-mini
  .venv/bin/python scripts/run_hybrid_kdd_experiment.py                  # full matrix
  .venv/bin/python scripts/run_hybrid_kdd_experiment.py --models "openai/gpt-4o-mini"

Outputs: data/experiments/hybrid_kdd_v1/{records.jsonl, summary.json, prompts/}
No DB writes. No trips created. In-process only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def _load_env_file() -> None:
    """Fill missing API keys from the repo .env (2026-09-13: a dead shell
    key silently 401-fallbacked a whole run — LLM arms fell back in ~3ms).
    Precedence: explicit shell env wins; .env only fills gaps."""
    env_path = REPO / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and value:
            os.environ.setdefault(key, value)


_load_env_file()

os.environ.setdefault("TRIPSTORE_BACKEND", "file")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///")

OUT_DIR = REPO / "data" / "experiments" / "hybrid_kdd_v1"
PROMPT_DIR = OUT_DIR / "prompts"


def load_records() -> List[Dict[str, Any]]:
    """Load the graded corpora as uniform records (KDD selection phase)."""
    records: List[Dict[str, Any]] = []

    budget = json.loads((REPO / "data/fixtures/budget/golden_dataset.json").read_text())
    for i, fx in enumerate(_as_list(budget)):
        text = _input_text(fx)
        if text:
            records.append({"corpus": "budget", "record_id": fx.get("fixture_id", f"budget_{i}"), "raw_text": text})

    coll = json.loads((REPO / "data/fixtures/extraction/colloquial_golden.json").read_text())
    for i, fx in enumerate(_as_list(coll)):
        text = _input_text(fx)
        if text:
            records.append({"corpus": "colloquial", "record_id": fx.get("fixture_id", f"coll_{i}"), "raw_text": text})

    for i, fx in enumerate(_as_list(json.loads((REPO / "data/fixtures/adversarial/adversarial_golden.json").read_text()))):
        text = _input_text(fx)
        if text:
            records.append({"corpus": "adversarial", "record_id": fx.get("record_id", fx.get("fixture_id", f"adv_{i}")), "raw_text": text})

    try:
        from data.fixtures import test_scenarios as scenario_mod

        for i, sc in enumerate(getattr(scenario_mod, "SCENARIOS", []) or []):
            text = sc.get("raw_note") or sc.get("note") or sc.get("input") or ""
            if text:
                records.append({"corpus": "scenario", "record_id": sc.get("id", f"scenario_{i}"), "raw_text": text})
    except Exception as exc:  # corpus loader is best-effort; report in summary
        print(f"[warn] scenario corpus unavailable: {exc}")

    return records


def _as_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("fixtures", "records", "scenarios"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _input_text(fx: Dict[str, Any]) -> str:
    for key in ("raw_input", "input", "raw_note", "note", "text"):
        val = fx.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


class InstrumentedLLMClient:
    """Delegating wrapper that archives every LLM call (KDD mining phase)."""

    def __init__(self, inner: Any, log: List[Dict[str, Any]], arm: str, record_id: str):
        self._inner = inner
        self._log = log
        self._arm = arm
        self._record_id = record_id
        self.model = getattr(inner, "model", "unknown")

    def __getattr__(self, name):  # delegate everything else
        return getattr(self._inner, name)

    def decide(self, prompt: str, schema: Dict[str, Any], temperature: Optional[float] = None) -> Dict[str, Any]:
        start = time.time()
        error = None
        result = None
        try:
            result = self._inner.decide(prompt, schema, temperature=temperature)
            return result
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            latency_ms = (time.time() - start) * 1000
            entry = {
                "arm": self._arm,
                "record_id": self._record_id,
                "latency_ms": round(latency_ms, 1),
                "prompt_chars": len(prompt),
                "response_chars": len(json.dumps(result)) if result is not None else 0,
                "error": error,
            }
            self._log.append(entry)
            PROMPT_DIR.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(f"{self._record_id}:{self._arm}:{len(self._log)}".encode()).hexdigest()[:12]
            # Sanitize: arm ids like "openai/gpt-oss-20b:fastest" contain "/" and
            # ":" — a raw "/" makes the archive path nested and the finally-block
            # write raise, masking the successful LLM result (found 2026-09-12).
            safe_arm = self._arm.replace("/", "_").replace(":", "_")
            archive = PROMPT_DIR / f"{self._record_id}-{safe_arm}-{digest}.json"
            archive.write_text(json.dumps({
                "arm": self._arm, "record_id": self._record_id,
                "prompt": prompt, "response": result, "error": error,
            }, indent=2, default=str), encoding="utf-8")


_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class _PatternClientBase:
    """Common contract the HybridDecisionEngine expects from an LLM client."""

    def is_available(self) -> bool:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        raise NotImplementedError

    def decide(self, prompt: str, schema: Dict[str, Any], temperature: Optional[float] = None) -> Dict[str, Any]:
        raise NotImplementedError


class VotingClient(_PatternClientBase):
    """Ensemble pattern: two models decide; flag survives only on agreement.

    Risk level emitted is the higher of the two when both agree; disagreement
    is downgraded to low (conservative).
    """

    def __init__(self, a: Any, b: Any):
        self._a = a
        self._b = b
        self.model = f"{a.model}+{b.model}"

    def is_available(self) -> bool:
        return self._a.is_available() and self._b.is_available()

    def count_tokens(self, text: str) -> int:
        return self._a.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            self._a.estimate_cost(prompt_tokens, completion_tokens)
            + self._b.estimate_cost(prompt_tokens, completion_tokens)
        )

    def decide(self, prompt: str, schema: Dict[str, Any], temperature: Optional[float] = None) -> Dict[str, Any]:
        ra = self._a.decide(prompt, schema, temperature=temperature)
        rb = self._b.decide(prompt, schema, temperature=temperature)
        a_risk = str(ra.get("risk_level", "low")).lower()
        b_risk = str(rb.get("risk_level", "low")).lower()
        if a_risk != "low" and a_risk == b_risk:
            return ra
        if a_risk != "low" and b_risk != "low":
            # both flag, levels differ -> keep the higher severity decision
            return ra if _SEVERITY_RANK.get(a_risk, 0) >= _SEVERITY_RANK.get(b_risk, 0) else rb
        merged = dict(ra)
        merged["risk_level"] = "low"
        merged["reasoning"] = f"ensemble disagreement: A={a_risk}, B={b_risk}"
        return merged


class CriticClient(_PatternClientBase):
    """Creator-critic pattern: creator decides; a second model validates.

    Non-low creator decisions are only kept when the critic agrees.
    """

    def __init__(self, creator: Any, critic: Any):
        self._creator = creator
        self._critic = critic
        self.model = f"{creator.model}>{critic.model}"

    def is_available(self) -> bool:
        return self._creator.is_available() and self._critic.is_available()

    def count_tokens(self, text: str) -> int:
        return self._creator.count_tokens(text)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # creator pays full prompt+completion; critic pays prompt+short verdict
        return self._creator.estimate_cost(
            prompt_tokens, completion_tokens
        ) + self._critic.estimate_cost(prompt_tokens, 64)

    def decide(self, prompt: str, schema: Dict[str, Any], temperature: Optional[float] = None) -> Dict[str, Any]:
        proposal = self._creator.decide(prompt, schema, temperature=temperature)
        if str(proposal.get("risk_level", "low")).lower() == "low":
            return proposal
        critic_schema = {
            "type": "object",
            "properties": {"agree": {"type": "boolean"}, "reasoning": {"type": "string"}},
            "required": ["agree"],
        }
        critic_prompt = (
            f"{prompt}\n\nProposed decision (JSON):\n{json.dumps(proposal)}\n\n"
            "Review the proposed decision against the travel context above. "
            "Agree only if the proposed risk assessment is justified by the "
            "actual facts in the context. Respond with JSON."
        )
        verdict = self._critic.decide(critic_prompt, critic_schema, temperature=temperature)
        if verdict.get("agree") is True:
            return proposal
        merged = dict(proposal)
        merged["risk_level"] = "low"
        merged["reasoning"] = (
            f"critic rejected: {verdict.get('reasoning', 'no reason given')}"
        )
        return merged


def _safe_name(model_id: str) -> str:
    """Filesystem-safe dir name for a model spec (slashes/colons allowed in ids)."""
    return (
        model_id.replace("/", "_").replace(":", "_").replace("-", "_").replace(".", "_")
    )


def _build_client(provider: str, model: str) -> Any:
    """Build an LLM client for an arm spec.

    Supported providers: standard src.llm providers (openai/gemini/local),
    local-ollama (OpenAI-compatible local server), and hf-router (Hugging
    Face Inference Providers — OpenAI-compatible endpoint with
    :fastest/:cheapest/:preferred routing policies; needs HF_TOKEN env).
    """
    from src.llm import create_llm_client

    if provider == "local-ollama":
        from src.llm.openai_client import OpenAIClient

        return OpenAIClient(
            model=model,
            api_key="ollama",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        )
    if provider == "openrouter":
        from src.llm.openai_client import OpenAIClient

        token = os.environ.get("OPENROUTER_API_KEY")
        if not token:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        return OpenAIClient(
            model=model,
            api_key=token,
            base_url=os.environ.get(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
        )
    if provider == "hf-router":
        from src.llm.openai_client import OpenAIClient

        token = os.environ.get("HF_TOKEN")
        if not token:
            raise RuntimeError("HF_TOKEN not set (export from keychain or .env)")
        return OpenAIClient(
            model=model,
            api_key=token,
            # Reasoning models (gpt-oss, DeepSeek, Qwen3.5) burn completion
            # budget on reasoning; 1024 left content empty (2026-09-12).
            max_tokens=int(os.environ.get("HF_ROUTER_MAX_TOKENS", "4096")),
            base_url=os.environ.get(
                "HF_ROUTER_BASE_URL", "https://router.huggingface.co/v1"
            ),
        )
    return create_llm_client(provider=provider, model=model)


def _has_destination(packet: Any) -> bool:
    """Deterministic validator input: does the packet carry any destination fact?"""
    fact = getattr(packet, "facts", {}).get("destination_candidates")
    if fact is None:
        return False
    value = getattr(fact, "value", None)
    return bool(value)


def run_record(
    record: Dict[str, Any],
    packet: Any,
    arm: str,
    hybrid_on: bool,
    model_spec: Optional[Tuple[str, str]],
    call_log: List[Dict[str, Any]],
    cache_dir: Optional[Path] = None,
    pattern: str = "single",
) -> Dict[str, Any]:
    """Run the risk-flag decision stage for one record under one arm.

    Both arms call the same top-level generator with the env flag toggled —
    symmetric by construction (the flag is read per-call at decision.py:40).
    """
    import src.intake.decision as decision_mod

    os.environ["USE_HYBRID_DECISION_ENGINE"] = "1" if hybrid_on else "0"
    # The env flag is lru_cached in decision.py; per-arm flips are invisible
    # unless the cache is cleared. Reset flag cache + engine singleton each arm.
    if hasattr(decision_mod, "_reset_hybrid_engine"):
        decision_mod._reset_hybrid_engine()

    decide_log: List[Dict[str, Any]] = []
    engine = None
    if hybrid_on:
        provider, model = model_spec
        os.environ["LLM_PROVIDER"] = provider
        if model:
            os.environ["OPENAI_MODEL"] = model
        from src.decision.cache_storage import DecisionCacheStorage
        from src.decision.hybrid_engine import HybridDecisionEngine

        # Architecture patterns compose clients; 'single' uses one client.
        if pattern == "vote":
            spec_b = (provider, os.environ.get("KDD_VOTE_PARTNER", "gpt-4o-mini"))
            if spec_b[1] == model:  # never pair a model with itself
                spec_b = (provider, "gpt-5.6-luna")
            inner_a = _build_client(provider, model)
            inner_b = _build_client(spec_b[0], spec_b[1])
            composed = VotingClient(inner_a, inner_b)
        elif pattern == "critic":
            creator = _build_client(provider, model)
            critic_spec = os.environ.get("KDD_CRITIC_MODEL", "gpt-5.6-terra")
            inner_critic = _build_client("openai", critic_spec)
            composed = CriticClient(creator, inner_critic)
        else:
            composed = _build_client(provider, model)
        instrumented = InstrumentedLLMClient(composed, call_log, arm, record["record_id"])
        # Run-scoped cache: cold pass starts empty, warm pass reuses the same
        # dir — cache-hit rate is then attributable to THIS run's cold entries.
        # Pattern arms get their own dir: their decisions differ from 'single'
        # and must not inherit its cached answers.
        cache_storage = DecisionCacheStorage(cache_dir=cache_dir) if cache_dir else None
        engine = HybridDecisionEngine(
            llm_client=instrumented,
            cache_storage=cache_storage,
            enable_cache=cache_storage is not None,
            enable_rules=(pattern != "llm_first"),
            enable_llm=True,
        )

        original_get = getattr(decision_mod, "_get_hybrid_engine", None)
        decision_mod._get_hybrid_engine = lambda: engine

        # Per-decision-type visibility: wrap engine.decide to log each
        # DecisionResult (source: cache|rule|llm) for slice analysis.
        real_decide = engine.decide

        def logged_decide(decision_type: str, packet: Any, schema=None, context=None):
            t0 = time.time()
            res = real_decide(decision_type, packet, schema=schema, context=context)
            decide_log.append({
                "decision_type": decision_type,
                "source": getattr(res, "source", None),
                "decision": str(getattr(res, "decision", None)),
                "llm_used": bool(getattr(res, "llm_used", False)),
                "llm_model": getattr(res, "llm_model", None),
                "cost_inr": getattr(res, "cost_inr", 0.0) or 0.0,
                "latency_ms": round((time.time() - t0) * 1000, 1),
            })
            return res

        engine.decide = logged_decide

    start = time.time()
    try:
        risks = decision_mod.generate_risk_flags(packet, "discovery", None)
        if pattern == "guard" and hybrid_on and not _has_destination(packet):
            # LLM+regex guard: the deterministic validator drops LLM/cache-sourced
            # visa-timeline flags on destination-less packets (the §6.4 Q2
            # spurious-flag class) — LLM proposes, fact-gate disposes.
            risks = [
                r for r in risks
                if not (
                    r.get("source") in ("llm", "cache")
                    and r.get("flag") == "visa_timeline_risk"
                )
            ]
    except Exception as exc:
        risks = []
        call_log.append({"arm": arm, "record_id": record["record_id"], "risk_error": str(exc)})
    wall_ms = (time.time() - start) * 1000

    if hybrid_on:
        decision_mod._get_hybrid_engine = original_get

    return {
        "arm": arm,
        "pattern": pattern,
        "model": f"{model_spec[0]}/{model_spec[1]}" if (model_spec and model_spec[1]) else ("deterministic" if not hybrid_on else "default"),
        "risks": risks,
        "risk_count": len(risks),
        "wall_ms": round(wall_ms, 1),
        "llm_calls": len(call_log),
        "decide_log": decide_log if hybrid_on else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="openai/gpt-4o-mini,openai/gpt-4o")
    parser.add_argument("--smoke", type=int, default=0, help="Limit to first N records")
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument(
        "--patterns",
        default="single",
        help="Comma list: single,llm_first,guard,vote,critic. Non-single "
        "patterns run against --pattern-models only.",
    )
    parser.add_argument(
        "--pattern-models",
        default="openai/gpt-4o-mini,openai/gpt-5.6-luna",
        help="Models the non-single patterns run against (cost bound).",
    )
    parser.add_argument(
        "--tag",
        default="",
        help="Output tag: records<tag>.jsonl (default 'records.jsonl').",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Independent cold passes per hybrid arm (variance measurement; "
        "LLM arms are nondeterministic at temperature>0 — KDD §8). Run 0 "
        "keeps the plain arm name, runs 1+ get -rN suffixes with their own "
        "cache dirs.",
    )
    args = parser.parse_args()

    model_specs = [tuple(m.split("/", 1)) for m in args.models.split(",") if "/" in m]
    pattern_specs = [tuple(m.split("/", 1)) for m in args.pattern_models.split(",") if "/" in m]
    patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]

    records = load_records()
    if args.smoke:
        records = records[: args.smoke]
    print(f"[kdd] records: {len(records)} | models: {model_specs}")

    from src.intake.extractors import ExtractionPipeline, SourceEnvelope

    pipeline = ExtractionPipeline()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records_path = OUT_DIR / f"records{args.tag}.jsonl"

    # Preprocessing phase: tier-0 extraction once per record (shared substrate)
    packets: List[Tuple[Dict[str, Any], Any]] = []
    for rec in records:
        try:
            envelope = SourceEnvelope.from_freeform(rec["raw_text"])
            packet = pipeline.extract([envelope], stage="discovery")
            packets.append((rec, packet))
        except Exception as exc:
            print(f"[warn] extraction failed for {rec['record_id']}: {exc}")
            packets.append((rec, None))

    arm_defs: List[Tuple[str, bool, Optional[Tuple[str, str]], Optional[Path], str]] = []
    if not args.skip_baseline:
        arm_defs.append(("A", False, None, None, "single"))
    for spec in model_specs:
        # Per-model run-scoped cache: wiped before the cold pass, reused for
        # the warm pass so warm measures THIS cold pass's cache entries only.
        for run_i in range(max(1, args.runs)):
            suffix = "" if run_i == 0 else f"-r{run_i}"
            model_cache_dir = OUT_DIR / f"cache_{_safe_name(spec[1])}{suffix}"
            if model_cache_dir.exists():
                shutil.rmtree(model_cache_dir)
            arm_defs.append((f"B-{spec[1]}{suffix}", True, spec, model_cache_dir, "single"))
            if run_i == 0:
                arm_defs.append((f"B-{spec[1]}-warm", True, spec, model_cache_dir, "single"))
    for pattern in patterns:
        if pattern == "single":
            continue
        for spec in pattern_specs:
            pat_cache_dir = OUT_DIR / f"cache_{_safe_name(spec[1])}_{pattern}"
            if pat_cache_dir.exists():
                shutil.rmtree(pat_cache_dir)
            arm_defs.append((f"P-{pattern}-{spec[1]}", True, spec, pat_cache_dir, pattern))

    with records_path.open("w", encoding="utf-8") as out:
        for rec, packet in packets:
            if packet is None:
                continue
            for arm_name, hybrid_on, spec, cache_dir, pattern in arm_defs:
                call_log: List[Dict[str, Any]] = []
                model_used = "deterministic"
                res = run_record(rec, packet, arm_name, hybrid_on, spec, call_log, cache_dir, pattern)
                model_used = res.pop("model")
                row = {
                    "corpus": rec["corpus"],
                    "record_id": rec["record_id"],
                    "arm": arm_name,
                    "pattern": pattern,
                    "model": model_used,
                    "risk_count": res["risk_count"],
                    "risks": res["risks"],
                    "wall_ms": res["wall_ms"],
                    "llm_calls": res["llm_calls"] if hybrid_on else 0,
                    "telemetry": call_log if hybrid_on else [],
                    "decide_log": res.get("decide_log", []) if hybrid_on else [],
                }
                out.write(json.dumps(row, default=str) + "\n")
                print(f"  {rec['record_id']:<28} arm={arm_name:<12} risks={res['risk_count']} wall={res['wall_ms']}ms")

    print(f"[kdd] wrote {records_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
