#!/usr/bin/env python3
"""
E2E observability runner for travel_agency_agent.

Produces per-scenario evidence:
- input payloads
- intermediate state (packet/decision internals)
- outputs
- requirements/external dependencies
- runtime
- unknowns and correction hooks for FE/BE
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
import textwrap
import time
import traceback
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _json_safe(value: Any, max_string: int = 1200) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value), max_string=max_string)
    if isinstance(value, dict):
        return {str(k): _json_safe(v, max_string=max_string) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v, max_string=max_string) for v in value]
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str) and len(value) > max_string:
            return value[: max_string - 3] + "..."
        return value
    return repr(value)


def _slot_map(slot_dict: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in slot_dict.items():
        if hasattr(v, "to_dict"):
            out[k] = _json_safe(v.to_dict())
        else:
            out[k] = _json_safe(v)
    return out


def _summarize_packet(packet: Any) -> Dict[str, Any]:
    packet_dict = _json_safe(packet)
    if not isinstance(packet_dict, dict):
        return {"raw": packet_dict}
    out = {
        "packet_id": packet_dict.get("packet_id"),
        "schema_version": packet_dict.get("schema_version"),
        "stage": packet_dict.get("stage"),
        "operating_mode": packet_dict.get("operating_mode"),
        "source_envelope_ids": packet_dict.get("source_envelope_ids", []),
        "facts": _slot_map(getattr(packet, "facts", {})),
        "derived_signals": _slot_map(getattr(packet, "derived_signals", {})),
        "hypotheses": _slot_map(getattr(packet, "hypotheses", {})),
        "ambiguities": _json_safe(getattr(packet, "ambiguities", [])),
        "contradictions": _json_safe(getattr(packet, "contradictions", [])),
        "unknowns": _json_safe(getattr(packet, "unknowns", [])),
        "event_count": len(getattr(packet, "events", []) or []),
    }
    return out


def _summarize_decision(decision: Any) -> Dict[str, Any]:
    d = _json_safe(decision)
    if not isinstance(d, dict):
        return {"raw": d}
    confidence = d.get("confidence", {}) if isinstance(d.get("confidence", {}), dict) else {}
    return {
        "packet_id": d.get("packet_id"),
        "current_stage": d.get("current_stage"),
        "operating_mode": d.get("operating_mode"),
        "decision_state": d.get("decision_state"),
        "hard_blockers": d.get("hard_blockers", []),
        "soft_blockers": d.get("soft_blockers", []),
        "ambiguities": d.get("ambiguities", []),
        "contradictions": d.get("contradictions", []),
        "follow_up_questions": d.get("follow_up_questions", []),
        "branch_options": d.get("branch_options", []),
        "risk_flags": d.get("risk_flags", []),
        "rationale": d.get("rationale", {}),
        "commercial_decision": d.get("commercial_decision"),
        "next_best_action": d.get("next_best_action"),
        "confidence": {
            "data_quality": confidence.get("data_quality"),
            "judgment_confidence": confidence.get("judgment_confidence"),
            "commercial_confidence": confidence.get("commercial_confidence"),
            "overall": confidence.get("overall"),
        },
    }


def _suite_entry(
    suite: str,
    scenario_id: str,
    scenario_name: str,
    input_payload: Any,
    runtime_ms: float,
    status: str,
    packet: Optional[Dict[str, Any]] = None,
    decision: Optional[Dict[str, Any]] = None,
    output: Optional[Dict[str, Any]] = None,
    requirements: Optional[List[str]] = None,
    external_dependencies: Optional[List[str]] = None,
    unknowns: Optional[List[str]] = None,
    notes: Optional[List[str]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "suite": suite,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "input": _json_safe(input_payload),
        "intermediate": {
            "packet": packet,
            "decision": decision,
        },
        "output": output or {},
        "requirements": requirements or [],
        "external_dependencies": external_dependencies or [],
        "unknowns": unknowns or [],
        "notes": notes or [],
        "status": status,
        "runtime_ms": round(runtime_ms, 3),
        "error": error,
    }


def run_freeze_pack_scenarios() -> List[Dict[str, Any]]:
    mod = importlib.import_module("tests.test_e2e_freeze_pack")
    scenario_classes = [
        ("F1", "TestScenario1_MessyFamilyDiscovery"),
        ("F2", "TestScenario2_PastCustomerPastTripMention"),
        ("F3", "TestScenario3_AuditModeSelfBooked"),
        ("F4", "TestScenario4_CoordinatorGroup"),
        ("F5", "TestScenario5_EmergencyCancellation"),
    ]
    results: List[Dict[str, Any]] = []
    for sid, class_name in scenario_classes:
        klass = getattr(mod, class_name)
        scenario_name = class_name.replace("TestScenario", "Scenario ")
        text = getattr(klass, "TEXT")
        t0 = time.perf_counter()
        try:
            flow = mod.e2e_pipeline(text)
            runtime_ms = (time.perf_counter() - t0) * 1000
            packet = _summarize_packet(flow["packet"])
            decision = _summarize_decision(flow["decision"])
            validation = _json_safe(flow["report"])
            strategy = _json_safe(flow["strategy"])
            traveler_bundle = _json_safe(flow["traveler_bundle"])
            internal_bundle = _json_safe(flow["internal_bundle"])
            sanitized = _summarize_packet(flow["sanitized"])
            leak_results = _json_safe(mod.check_no_leakage(flow["traveler_bundle"]))
            results.append(
                _suite_entry(
                    suite="test_e2e_freeze_pack",
                    scenario_id=sid,
                    scenario_name=scenario_name,
                    input_payload={"text": text, "source": "agency_notes", "actor": "agent"},
                    runtime_ms=runtime_ms,
                    status="passed",
                    packet=packet,
                    decision=decision,
                    output={
                        "validation_report": validation,
                        "strategy": strategy,
                        "traveler_bundle": traveler_bundle,
                        "internal_bundle": internal_bundle,
                        "sanitized_packet_view": sanitized,
                        "leakage_checks": leak_results,
                    },
                    requirements=[
                        "Python env with src imports enabled",
                        "NB01 extraction + NB02 decision + NB03 strategy modules",
                    ],
                    external_dependencies=[
                        "No network calls required for these scenarios",
                        "Local rules/hybrid decision configuration may influence risk flags",
                    ],
                    unknowns=[
                        "Hybrid decision feature flags can affect risk output if environment changes",
                    ],
                )
            )
        except Exception as exc:
            runtime_ms = (time.perf_counter() - t0) * 1000
            results.append(
                _suite_entry(
                    suite="test_e2e_freeze_pack",
                    scenario_id=sid,
                    scenario_name=scenario_name,
                    input_payload={"text": text, "source": "agency_notes", "actor": "agent"},
                    runtime_ms=runtime_ms,
                    status="failed",
                    error=f"{exc}\n{traceback.format_exc()}",
                )
            )
    return results


def run_realworld_scenarios() -> List[Dict[str, Any]]:
    mod = importlib.import_module("tests.test_realworld_scenarios_v02")
    scenario_methods: List[Tuple[str, str, str]] = [
        ("R1", "TestVagueLead", "test_vague_lead_asks_followup_with_missing_blockers"),
        ("R2", "TestConfusedCouple", "test_confused_couple_stops_on_date_conflict"),
        ("R3", "TestDreamer", "test_dreamer_detects_budget_vs_luxury_tension"),
        ("R4", "TestReadyToBuy", "test_ready_to_buy_proceeds_safely"),
        ("R5", "TestWhatsAppDump", "test_whatsapp_dump_reveals_ambiguity_gap"),
        ("R6", "TestCRMReturn", "test_crm_return_proceeds_with_new_data"),
        ("R7", "TestElderlyPilgrimage", "test_elderly_pilgrimage_proceeds_with_medical_risk_flag"),
        ("R8", "TestLastMinuteBooker", "test_last_minute_booker_reveals_soft_blocker_gap"),
        ("R9", "TestStageProgressionScenarios", "test_shortlist_asks_for_selected_destination"),
        ("R10", "TestStageProgressionScenarios", "test_proposal_asks_for_selected_itinerary"),
        ("R11", "TestBudgetFlexibility", "test_budget_stretch_proceeds_but_not_structurally_recognized"),
        ("R12", "TestInferredDestination", "test_inferred_destination_fills_blocker_with_lower_confidence"),
        ("R13", "TestMultiEnvelopeAccumulation", "test_multi_envelope_accumulation_merges_seamlessly"),
    ]

    orig_run = mod.run_gap_and_decision
    results: List[Dict[str, Any]] = []
    for sid, class_name, method_name in scenario_methods:
        captured: Dict[str, Any] = {"packet": None, "decision": None}

        def wrapper(pkt: Any, *args: Any, **kwargs: Any) -> Any:
            captured["packet"] = deepcopy(pkt)
            out = orig_run(pkt, *args, **kwargs)
            captured["decision"] = deepcopy(out)
            return out

        mod.run_gap_and_decision = wrapper

        klass = getattr(mod, class_name)
        method = getattr(klass(), method_name)
        t0 = time.perf_counter()
        status = "passed"
        err = None
        try:
            method()
        except Exception as exc:
            status = "failed"
            err = f"{exc}\n{traceback.format_exc()}"
        runtime_ms = (time.perf_counter() - t0) * 1000

        packet_summary = _summarize_packet(captured["packet"]) if captured["packet"] is not None else None
        decision_summary = _summarize_decision(captured["decision"]) if captured["decision"] is not None else None

        doc = inspect.getdoc(method) or inspect.getdoc(klass) or ""
        results.append(
            _suite_entry(
                suite="test_realworld_scenarios_v02",
                scenario_id=sid,
                scenario_name=f"{class_name}.{method_name}",
                input_payload={"scenario_doc": doc},
                runtime_ms=runtime_ms,
                status=status,
                packet=packet_summary,
                decision=decision_summary,
                output={
                    "assertion_result": status,
                    "decision_state": decision_summary.get("decision_state") if decision_summary else None,
                    "follow_up_count": len((decision_summary or {}).get("follow_up_questions", [])),
                },
                requirements=[
                    "CanonicalPacket + Slot builders",
                    "Decision engine (`run_gap_and_decision`)",
                ],
                external_dependencies=[
                    "No network calls in scenario logic",
                ],
                unknowns=[
                    "Decision behavior can drift if rule tables or thresholds change",
                ],
                error=err,
            )
        )

    mod.run_gap_and_decision = orig_run
    return results


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            events.append(json.loads(s))
    return events


def run_timeline_scenarios() -> List[Dict[str, Any]]:
    from src.intake.orchestration import run_spine_once
    from src.intake.packet_models import SourceEnvelope

    logs_dir = REPO_ROOT / "data" / "logs" / "trips"
    logs_dir.mkdir(parents=True, exist_ok=True)
    flows = [
        (
            "T1",
            "spine_run_emits_timeline_events",
            """
            Trip Details:
            - Destination: Paris, France
            - Duration: 7 days
            - Travelers: 2 adults
            - Budget: €4000
            - Dates: May 2025
            - Interests: Museums, food, walking tours
            """.strip(),
        ),
        (
            "T2",
            "timeline_events_are_valid_json",
            """
            Trip: 10 days Bangkok, Thailand
            Budget: $3000 USD
            Travelers: 2
            """.strip(),
        ),
        (
            "T3",
            "timeline_file_append_behavior",
            """
            Quick trip: 3 days in Barcelona
            Budget: €2000
            """.strip(),
        ),
    ]
    results: List[Dict[str, Any]] = []
    for sid, name, text in flows:
        t0 = time.perf_counter()
        trip_id = None
        log_file = None
        try:
            envelopes = [SourceEnvelope.from_freeform(text, "agency_notes", "agent")]
            first = run_spine_once(envelopes=envelopes, stage="discovery")
            trip_id = first.packet.packet_id
            log_file = logs_dir / f"{trip_id}.jsonl"
            events_before = _read_jsonl(log_file)

            events_after = events_before
            if sid == "T3":
                second_env = [SourceEnvelope.from_freeform("Different trip data", "agency_notes", "agent")]
                run_spine_once(envelopes=second_env, stage="discovery")
                events_after = _read_jsonl(log_file)

            runtime_ms = (time.perf_counter() - t0) * 1000
            results.append(
                _suite_entry(
                    suite="test_timeline_e2e",
                    scenario_id=sid,
                    scenario_name=name,
                    input_payload={"text": text, "stage": "discovery"},
                    runtime_ms=runtime_ms,
                    status="passed",
                    packet={"packet_id": trip_id, "stage": "discovery"},
                    decision=None,
                    output={
                        "trip_id": trip_id,
                        "timeline_file": str(log_file) if log_file else None,
                        "events_before": events_before,
                        "events_after": events_after,
                        "event_count_before": len(events_before),
                        "event_count_after": len(events_after),
                    },
                    requirements=[
                        "Writable filesystem under data/logs/trips",
                        "orchestration.run_spine_once",
                    ],
                    external_dependencies=[
                        "Timeline persistence to local JSONL file",
                    ],
                    unknowns=[
                        "Append-only semantics rely on orchestrator behavior not asserted here with file locks",
                    ],
                )
            )
        except Exception as exc:
            runtime_ms = (time.perf_counter() - t0) * 1000
            results.append(
                _suite_entry(
                    suite="test_timeline_e2e",
                    scenario_id=sid,
                    scenario_name=name,
                    input_payload={"text": text, "stage": "discovery"},
                    runtime_ms=runtime_ms,
                    status="failed",
                    error=f"{exc}\n{traceback.format_exc()}",
                )
            )
        finally:
            if log_file and log_file.exists():
                log_file.unlink()
    return results


def run_override_scenarios() -> List[Dict[str, Any]]:
    mod = importlib.import_module("tests.test_override_e2e")
    results: List[Dict[str, Any]] = []
    for idx, name in enumerate(
        [
            "test_e2e_override_critical_flag_workflow",
            "test_e2e_override_validation_errors",
            "test_e2e_override_stale_severity_conflict",
        ],
        start=1,
    ):
        fn = getattr(mod, name)
        doc = inspect.getdoc(fn) or ""
        t0 = time.perf_counter()
        status = "passed"
        err = None
        try:
            fn()
        except Exception as exc:
            status = "failed"
            err = f"{exc}\n{traceback.format_exc()}"
        runtime_ms = (time.perf_counter() - t0) * 1000
        is_placeholder = "pass" in (inspect.getsource(fn) or "")
        unknowns = []
        notes = []
        if is_placeholder:
            unknowns.append("Test is placeholder-only; no assertions executed.")
            notes.append("This flow is documented but not actually validated at runtime.")
        results.append(
            _suite_entry(
                suite="test_override_e2e",
                scenario_id=f"O{idx}",
                scenario_name=name,
                input_payload={"docstring_steps": doc},
                runtime_ms=runtime_ms,
                status=status,
                packet=None,
                decision=None,
                output={
                    "runtime_behavior": "no-op placeholder function" if is_placeholder else "executed",
                    "assertions_executed": False if is_placeholder else True,
                },
                requirements=[
                    "Frontend UI override modal and API integration",
                    "POST /api/trips/{trip_id}/override endpoint",
                ],
                external_dependencies=[
                    "Would require running FE app + backend API + test trip data once implemented",
                ],
                unknowns=unknowns,
                notes=notes,
                error=err,
            )
        )
    return results


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# E2E Flow Observability Report")
    lines.append("")
    lines.append(f"- Generated: {report['generated_at']}")
    lines.append(f"- Repo: `{report['repo']}`")
    lines.append(f"- Total scenarios: {report['summary']['total_scenarios']}")
    lines.append(f"- Passed: {report['summary']['passed']}")
    lines.append(f"- Failed: {report['summary']['failed']}")
    lines.append(f"- Placeholder/no-op scenarios: {report['summary']['placeholder_or_noop']}")
    lines.append(f"- Total runtime (ms): {report['summary']['total_runtime_ms']}")
    lines.append("")
    lines.append("## Suite Summary")
    lines.append("")
    lines.append("| Suite | Scenario Count | Passed | Failed | Runtime (ms) |")
    lines.append("|---|---:|---:|---:|---:|")
    for suite_name, suite_data in report["suite_summary"].items():
        lines.append(
            f"| {suite_name} | {suite_data['count']} | {suite_data['passed']} | "
            f"{suite_data['failed']} | {suite_data['runtime_ms']} |"
        )
    lines.append("")
    lines.append("## Detailed Flows")
    lines.append("")

    for sc in report["scenarios"]:
        lines.append(f"### {sc['scenario_id']} - {sc['scenario_name']}")
        lines.append("")
        lines.append(f"- Suite: `{sc['suite']}`")
        lines.append(f"- Status: `{sc['status']}`")
        lines.append(f"- Runtime: `{sc['runtime_ms']} ms`")
        lines.append("")
        lines.append("#### Input")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(sc["input"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
        lines.append("#### Intermediate")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(sc["intermediate"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
        lines.append("#### Output")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(sc["output"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")

        if sc.get("requirements"):
            lines.append("#### Requirements")
            lines.append("")
            for req in sc["requirements"]:
                lines.append(f"- {req}")
            lines.append("")
        if sc.get("external_dependencies"):
            lines.append("#### External Dependencies")
            lines.append("")
            for dep in sc["external_dependencies"]:
                lines.append(f"- {dep}")
            lines.append("")
        if sc.get("unknowns"):
            lines.append("#### Unknowns / Risk Surface")
            lines.append("")
            for u in sc["unknowns"]:
                lines.append(f"- {u}")
            lines.append("")
        if sc.get("notes"):
            lines.append("#### Notes")
            lines.append("")
            for n in sc["notes"]:
                lines.append(f"- {n}")
            lines.append("")
        if sc.get("error"):
            lines.append("#### Error")
            lines.append("")
            lines.append("```text")
            lines.append(sc["error"])
            lines.append("```")
            lines.append("")

    lines.append("## FE/BE Correction Hooks")
    lines.append("")
    lines.extend(f"- {item}" for item in report["correction_hooks"])
    lines.append("")
    return "\n".join(lines)


def build_report() -> Dict[str, Any]:
    scenarios: List[Dict[str, Any]] = []
    scenarios.extend(run_freeze_pack_scenarios())
    scenarios.extend(run_realworld_scenarios())
    scenarios.extend(run_timeline_scenarios())
    scenarios.extend(run_override_scenarios())

    passed = sum(1 for s in scenarios if s["status"] == "passed")
    failed = sum(1 for s in scenarios if s["status"] == "failed")
    placeholder = sum(
        1
        for s in scenarios
        if "placeholder" in " ".join(s.get("unknowns", [])).lower()
        or s.get("output", {}).get("runtime_behavior") == "no-op placeholder function"
    )
    total_runtime = round(sum(float(s["runtime_ms"]) for s in scenarios), 3)

    suite_summary: Dict[str, Dict[str, Any]] = {}
    for s in scenarios:
        bucket = suite_summary.setdefault(
            s["suite"], {"count": 0, "passed": 0, "failed": 0, "runtime_ms": 0.0}
        )
        bucket["count"] += 1
        bucket["passed"] += 1 if s["status"] == "passed" else 0
        bucket["failed"] += 1 if s["status"] == "failed" else 0
        bucket["runtime_ms"] += float(s["runtime_ms"])
    for v in suite_summary.values():
        v["runtime_ms"] = round(v["runtime_ms"], 3)

    correction_hooks = [
        "Implement real assertions for `tests/test_override_e2e.py` (currently no-op).",
        "Promote scenario-level observability (packet + decision snapshots) into CI artifacts.",
        "For timeline flows, validate append-only behavior with concurrent writes and lock strategy.",
        "Track environment-sensitive decision drift (hybrid engine flags/thresholds) across runs.",
        "Add frontend-to-backend trace IDs so a UI flow can be linked to packet/decision timeline events.",
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(REPO_ROOT),
        "summary": {
            "total_scenarios": len(scenarios),
            "passed": passed,
            "failed": failed,
            "placeholder_or_noop": placeholder,
            "total_runtime_ms": total_runtime,
        },
        "suite_summary": suite_summary,
        "scenarios": scenarios,
        "correction_hooks": correction_hooks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deep E2E observability report")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=REPO_ROOT / "Docs" / "reports" / f"e2e_observability_{datetime.now().strftime('%Y-%m-%d')}.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=REPO_ROOT / "Docs" / "reports" / f"E2E_FLOW_OBSERVABILITY_{datetime.now().strftime('%Y-%m-%d')}.md",
    )
    args = parser.parse_args()

    report = build_report()

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)

    args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote JSON: {args.json_out}")
    print(f"Wrote Markdown: {args.md_out}")
    print(
        f"Scenarios={report['summary']['total_scenarios']} "
        f"passed={report['summary']['passed']} failed={report['summary']['failed']} "
        f"placeholder={report['summary']['placeholder_or_noop']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
