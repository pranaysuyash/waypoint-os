"""
tests/test_memory_slot_review.py — E-D slot 1 shadow-review logic.

`src/memory/slot_review.py` turns `memory_slot_promotion` audit events into
the shadow-window verdict (INSUFFICIENT_DATA / GUARDRAIL_VIOLATION /
REVIEW_READY) against the pre-registered criteria in
Docs/architecture/MEMORY_SLOT_WIRING_2026-09-15.md.
"""

import contextlib
import io
import json
from pathlib import Path

from src.memory.slot_review import load_events, main, review


def _event(asked, promoted, trust_class="explicit_user", memory="mem_1"):
    return {
        "event_type": "memory_slot_promotion",
        "user_id": "agency-1",
        "details": {
            "asked": asked,
            "promoted": [
                {
                    "field_name": name,
                    "rationale": f"memory:preference:traveler_direct:{memory}",
                    "trust_class": trust_class,
                    "score": 0.9,
                }
                for name in promoted
            ],
        },
    }


def _write_events(tmp_path: Path, events):
    audit = tmp_path / "events.jsonl"
    with open(audit, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return audit


def _run_main(argv):
    """Runs main() in-process; returns (exit_code, stdout)."""
    buffer = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(buffer):
        try:
            code = main(argv) or 0
        except SystemExit as exit_exc:
            code = exit_exc.code if isinstance(exit_exc.code, int) else 0
    return code, buffer.getvalue()


ASK = ["budget_min", "seat_preference"]


def test_insufficient_data_below_sample_floor(tmp_path):
    audit = _write_events(tmp_path, [_event(ASK, []) for _ in range(5)])
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "INSUFFICIENT_DATA"


def test_review_ready_when_floor_met_and_guardrails_hold(tmp_path):
    events = []
    for i in range(30):
        promoted = [ASK[0]] if i % 3 == 0 else []
        events.append(_event(ASK, promoted, memory=f"mem_{i}"))
    audit = _write_events(tmp_path, events)
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "REVIEW_READY"
    assert report["metrics"]["asks_recorded"] == 30
    assert report["metrics"]["promotion_rate"] == round(10 / 30, 4)


def test_g1_invariant_violation_promoted_outside_asked(tmp_path):
    events = [_event(ASK, ["destination_candidates"]) for _ in range(30)]
    audit = _write_events(tmp_path, events)
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "GUARDRAIL_VIOLATION"
    assert any("G1" in reason for reason in report["reasons"])


def test_g2_low_trust_promotions_violate_trust_floor(tmp_path):
    events = [_event(ASK, [ASK[0]], trust_class="agent_inferred") for _ in range(30)]
    audit = _write_events(tmp_path, events)
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "GUARDRAIL_VIOLATION"
    assert any("G2" in reason for reason in report["reasons"])


def test_g3_single_memory_degeneracy(tmp_path):
    events = [_event(ASK, [ASK[0]], memory="mem_stale") for _ in range(30)]
    audit = _write_events(tmp_path, events)
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "GUARDRAIL_VIOLATION"
    assert any("G3" in reason for reason in report["reasons"])


def test_g4_promote_on_every_ask_is_noise(tmp_path):
    events = [_event(ASK, [ASK[0]], memory=f"mem_{i}") for i in range(30)]
    audit = _write_events(tmp_path, events)
    report = review(load_events(audit, None, None))
    assert report["verdict"] == "GUARDRAIL_VIOLATION"
    assert any("G4" in reason for reason in report["reasons"])


def test_missing_audit_file_is_clean_empty(tmp_path):
    report = review(load_events(tmp_path / "none.jsonl", None, None))
    assert report["verdict"] == "INSUFFICIENT_DATA"
    assert report["metrics"]["asks_recorded"] == 0


def test_agency_filter_scopes_events(tmp_path):
    events = [_event(ASK, []) for _ in range(10)]
    events[0]["user_id"] = "agency-other"
    audit = _write_events(tmp_path, events)
    scoped = load_events(audit, "agency-1", None)
    assert len(scoped) == 9


def test_cli_exit_codes_in_process(tmp_path):
    empty = _write_events(tmp_path, [])
    code, _out = _run_main(["--audit-file", str(empty), "--json"])
    assert code == 2  # INSUFFICIENT_DATA

    violating = _write_events(
        tmp_path, [_event(ASK, [ASK[0]], trust_class="agent_inferred") for _ in range(30)]
    )
    code, out = _run_main(["--audit-file", str(violating)])
    assert code == 3  # GUARDRAIL_VIOLATION
    assert "GUARDRAIL_VIOLATION" in out
