"""
src/llm/replay.py — Record/Replay client pair for BaseLLMClient (exploration topic 48, next-step #3).

The OrcaReplay pattern (recorded 2026-10-18 sweep) applied to Waypoint's LLM
seam: **record** a live run's `decide()` calls to an append-only JSONL trace,
then **replay** the same run offline — byte-identical responses, zero API
calls, zero cost. The pair implements the exact `BaseLLMClient` protocol, so
any consumer that injects a client (`HybridDecisionEngine(llm_client=...)`,
agent runtimes) gains replay without a parallel pipeline:

    # record
    engine = HybridDecisionEngine(llm_client=RecordingLLMClient(inner=create_llm_client(), trace_path=t))
    # replay (offline — no network is possible; there is no inner client)
    engine = HybridDecisionEngine(llm_client=ReplayLLMClient(trace_path=t))

Design invariants (doctrine: honesty, fail-closed, no fabrication):

* **Hash-matched replay.** A recorded entry is served only when the incoming
  prompt+schema hashes match the entry. A prompt the trace never saw raises
  `LLMError` naming the mismatch — never a silent substitution from a
  neighboring entry.
* **Duplicate-safe, order-honest.** Identical (prompt, schema) pairs consume
  trace entries in recorded order; exhausting them raises rather than reusing
  a stale answer.
* **No network by construction.** `ReplayLLMClient` holds no inner client.
* **Fork-to-another-model is already owned by the KDD lane**
  (`scripts/run_hybrid_kdd_experiment.py --models` runs the same fixtures
  across models and grades with the KDD grader); this module deliberately does
  not duplicate that — its recorded prompts are the KDD lane's input.

PII boundary: prompts may carry customer text. Default trace home is
`data/llm_traces/` (gitignored); traces are session-local evidence, never
committable artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.llm.base import BaseLLMClient, LLMError, content_sha256

DEFAULT_TRACE_DIR = Path("data/llm_traces")

TRACE_FORMAT_VERSION = 1


def _pair_key(prompt: Any, schema: Any) -> str:
    """Stable key for one decide() call — the same construction used for the
    stored trace keys: prompt hash + ':' + schema hash (no extra hashing)."""
    return content_sha256(prompt) + ":" + content_sha256(schema)


def trace_integrity_report(trace_path: Path) -> Dict[str, Any]:
    """Verify a trace file parses and its recorded hashes match its payloads.

    Returns `{"ok": bool, "entries": int, "errors": [..]}` — used by the
    `--check` path and by tests. Never mutates the trace.
    """
    errors: List[str] = []
    entries: List[Dict[str, Any]] = []
    try:
        lines = Path(trace_path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"ok": False, "entries": 0, "errors": [f"unreadable trace: {exc}"]}
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON ({exc})")
            continue
        entries.append(entry)
        if entry.get("format_version") != TRACE_FORMAT_VERSION:
            errors.append(f"line {line_no}: unsupported format_version {entry.get('format_version')}")
            continue
        if content_sha256(entry.get("prompt")) != entry.get("prompt_sha256"):
            errors.append(f"line {line_no}: prompt_sha256 mismatch")
        if content_sha256(entry.get("response")) != entry.get("response_sha256"):
            errors.append(f"line {line_no}: response_sha256 mismatch")
    return {"ok": not errors, "entries": len(entries), "errors": errors}


class RecordingLLMClient(BaseLLMClient):
    """Wraps a real client and appends one JSONL trace entry per decide() call."""

    def __init__(self, inner: BaseLLMClient, trace_path: Path):
        super().__init__(model=inner.model, temperature=inner.temperature, max_tokens=inner.max_tokens)
        self.inner = inner
        self.trace_path = Path(trace_path)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.call_index = 0

    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        response = self.inner.decide(prompt, schema, temperature)
        entry = {
            "format_version": TRACE_FORMAT_VERSION,
            "index": self.call_index,
            "model": self.inner.model,
            "temperature_requested": temperature,
            "temperature_effective": temperature if temperature is not None else self.temperature,
            "prompt": prompt,
            "schema": schema,
            "prompt_sha256": content_sha256(prompt),
            "schema_sha256": content_sha256(schema),
            "response_sha256": content_sha256(response),
            "response": response,
            "recorded_at_source": "live-client",
        }
        with self.trace_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        self.call_index += 1
        return response

    def is_available(self) -> bool:
        return self.inner.is_available()

    def ping(self) -> bool:
        return self.inner.ping()

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return self.inner.estimate_cost(prompt_tokens, completion_tokens)


class ReplayLLMClient(BaseLLMClient):
    """Serves decide() from a recorded trace. Holds no network client at all."""

    def __init__(self, trace_path: Path):
        self.trace_path = Path(trace_path)
        report = trace_integrity_report(self.trace_path)
        if not report["ok"]:
            raise LLMError(
                f"trace {self.trace_path} failed integrity check: {report['errors'][:3]}"
            )
        entries = [json.loads(line) for line in self.trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not entries:
            raise LLMError(f"trace {self.trace_path} contains no entries")
        first = entries[0]
        super().__init__(model=str(first.get("model") or "replayed"), temperature=0.0, max_tokens=1024)
        self._remaining: Dict[str, List[Dict[str, Any]]] = {}
        self.replayed_calls = 0
        for entry in entries:
            self._remaining.setdefault(str(entry["prompt_sha256"]) + ":" + str(entry["schema_sha256"]), []).append(entry)

    def is_available(self) -> bool:
        """Honest offline availability: usable while unconsumed entries remain."""
        return any(self._remaining.values())

    def decide(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        key = _pair_key(prompt, schema)
        queue = self._remaining.get(key)
        if not queue:
            unconsumed = sum(len(v) for v in self._remaining.values())
            raise LLMError(
                "replay mismatch: no unconsumed trace entry matches this "
                f"prompt+schema (prompt_sha256={content_sha256(prompt)}); "
                f"trace {self.trace_path} has {unconsumed} unconsumed entry(ies) under other keys. "
                "Re-record the run before replaying divergent inputs — silent substitution is not allowed."
            )
        entry = queue.pop(0)
        self.replayed_calls += 1
        response = entry["response"]
        if content_sha256(response) != entry.get("response_sha256"):
            raise LLMError(f"replay corruption: response hash mismatch on trace entry {entry.get('index')}")
        return response

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Replay moves no money and spends no tokens: cost is structurally zero."""
        return 0.0
