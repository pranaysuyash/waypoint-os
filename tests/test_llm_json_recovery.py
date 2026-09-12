"""Tests for _recover_json_object — multi-vendor reasoning-model JSON repair.

Commissioned by the HF-router serving experiments (2026-09-12): DeepSeek via
the HF router emitted '{\\n{...}' — a stray bare "{" before the payload —
which made strict json.loads fail and silenced an entire graded arm.
"""


from src.llm.openai_client import _recover_json_object


def test_recovers_doubled_brace_preamble():
    """The exact DeepSeek failure shape: bare '{' ahead of a valid object."""
    text = '{\n{\n  "risk_level": "low",\n  "reasoning": "ok"\n}\n}'
    assert _recover_json_object(text) == {"risk_level": "low", "reasoning": "ok"}


def test_recovers_prose_preamble():
    text = 'Here is my answer:\n{"risk_level": "high"}'
    assert _recover_json_object(text) == {"risk_level": "high"}


def test_recovers_clean_json_fallback():
    assert _recover_json_object('{"risk_level": "medium"}') == {"risk_level": "medium"}


def test_returns_none_for_garbage():
    assert _recover_json_object("no json at all") is None
    assert _recover_json_object("{ unbalanced") is None


def test_prefers_first_parseable_candidate():
    text = '{"bad": Tru} {"risk_level": "low"}'
    assert _recover_json_object(text) == {"risk_level": "low"}


def test_unbalanced_outer_brace_still_salvages_inner_object():
    """'{ { "x" }' — outer brace has no closer, but the inner object is
    well-formed; the try-each-brace design recovers the payload (this is what
    rescued the DeepSeek arm)."""
    text = '{\n{\n  "risk_level": "low"\n}'
    assert _recover_json_object(text) == {"risk_level": "low"}


def test_returns_none_when_no_object_recovers():
    text = '{ "key": Tru, { broken'
    assert _recover_json_object(text) is None
