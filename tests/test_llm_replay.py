"""Record/Replay LLM client tests — exploration topic 48 next-step #3 (2026-10-22).

Pins the OrcaReplay-pattern invariants on Waypoint's LLM seam:
  * recording captures every decide() call with verifiable hashes;
  * replay serves responses byte-identically by prompt+schema hash, offline,
    with zero cost;
  * mismatch and exhaustion FAIL CLOSED (LLMError, never silent substitution);
  * corrupted traces are refused at construction;
  * the pair implements the BaseLLMClient protocol faithfully.
"""

import json

import pytest

from src.llm.base import LLMError
from src.llm.replay import (
    RecordingLLMClient,
    ReplayLLMClient,
    trace_integrity_report,
)


class _FakeInnerClient:
    """Minimal inner standing in for a real provider client."""

    model = "fake-model-1"
    temperature = 0.3
    max_tokens = 512

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def decide(self, prompt, schema, temperature=None):
        self.calls += 1
        return self.responses.pop(0)

    def is_available(self):
        return True

    def ping(self):
        return True

    def estimate_cost(self, prompt_tokens, completion_tokens):
        return 0.42


SCHEMA = {"type": "object", "properties": {"verdict": {"type": "string"}}}


def _record(tmp_path, responses, prompts):
    inner = _FakeInnerClient(responses)
    trace = tmp_path / "trace.jsonl"
    client = RecordingLLMClient(inner=inner, trace_path=trace)
    out = [client.decide(p, SCHEMA) for p in prompts]
    return out, trace, inner


def test_recording_captures_calls_with_verifiable_hashes(tmp_path):
    responses = [{"verdict": "go"}, {"verdict": "stop"}]
    out, trace, inner = _record(tmp_path, responses, ["prompt A", "prompt B"])

    assert out == responses
    assert inner.calls == 2
    report = trace_integrity_report(trace)
    assert report["ok"] is True and report["entries"] == 2


def test_replay_serves_identical_responses_offline(tmp_path):
    responses = [{"verdict": "go"}, {"verdict": "stop"}]
    _, trace, _ = _record(tmp_path, responses, ["prompt A", "prompt B"])

    replay = ReplayLLMClient(trace)
    assert replay.is_available() is True
    assert replay.decide("prompt A", SCHEMA) == {"verdict": "go"}
    assert replay.decide("prompt B", SCHEMA) == {"verdict": "stop"}
    assert replay.replayed_calls == 2
    assert replay.is_available() is False  # every entry consumed
    assert replay.estimate_cost(1000, 1000) == 0.0  # replay moves no money
    assert replay.model == "fake-model-1"  # the recorded model, honestly named


def test_replay_duplicate_prompts_consume_entries_in_order(tmp_path):
    responses = [{"verdict": "first"}, {"verdict": "second"}]
    _, trace, _ = _record(tmp_path, responses, ["same prompt", "same prompt"])

    replay = ReplayLLMClient(trace)
    assert replay.decide("same prompt", SCHEMA) == {"verdict": "first"}
    assert replay.decide("same prompt", SCHEMA) == {"verdict": "second"}
    with pytest.raises(LLMError, match="no unconsumed trace entry"):
        replay.decide("same prompt", SCHEMA)


def test_replay_unknown_prompt_fails_closed(tmp_path):
    _, trace, _ = _record(tmp_path, [{"verdict": "go"}], ["recorded prompt"])

    replay = ReplayLLMClient(trace)
    with pytest.raises(LLMError, match="replay mismatch.*Re-record"):
        replay.decide("a prompt the run never made", SCHEMA)


def test_replay_refuses_corrupted_trace(tmp_path):
    _, trace, _ = _record(tmp_path, [{"verdict": "go"}], ["prompt"])
    lines = trace.read_text().splitlines()
    entry = json.loads(lines[0])
    entry["response"] = {"verdict": "TAMPERED"}
    trace.write_text(json.dumps(entry))

    with pytest.raises(LLMError, match="failed integrity check|response hash mismatch"):
        ReplayLLMClient(trace)


def test_recording_delegates_protocol_semantics(tmp_path):
    inner = _FakeInnerClient([{"verdict": "go"}])
    client = RecordingLLMClient(inner=inner, trace_path=tmp_path / "t.jsonl")

    assert client.is_available() is True
    assert client.ping() is True
    assert client.estimate_cost(10, 10) == 0.42  # the provider's own estimator
    assert client.count_tokens("abcd") == 1  # base-class ~4 chars/token estimate
