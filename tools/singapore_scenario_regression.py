#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from spine_api.core.security import create_access_token

SCENARIO_PATH = REPO_ROOT / "data/fixtures/scenarios/SC-901_ravi_singapore_messy_call.json"
REPORTS_DIR = REPO_ROOT / "Docs/reports"


def _http_json(method: str, url: str, body: dict[str, Any] | None = None, timeout: int = 30, auth_token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"{method} {url} -> HTTP {e.code}: {payload}") from e


def _poll_status(base_url: str, run_id: str, poll_path_tmpl: str, timeout_s: int, auth_token: str) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    started = time.perf_counter()
    snapshots: list[dict[str, Any]] = []
    while time.perf_counter() - started < timeout_s:
        status = _http_json("GET", f"{base_url}{poll_path_tmpl.format(run_id=run_id)}", timeout=20, auth_token=auth_token)
        snapshots.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "state": status.get("state"),
            "stage": status.get("stage"),
            "execution_ms": status.get("execution_ms"),
            "trip_id": status.get("trip_id"),
            "error_message": status.get("error_message"),
            "block_reason": status.get("block_reason"),
        })
        if status.get("state") in {"completed", "failed", "blocked"}:
            return status, snapshots, (time.perf_counter() - started) * 1000
        time.sleep(2)
    raise TimeoutError(f"Run {run_id} did not reach terminal state in {timeout_s}s")


def _extract_quality_flags(status: dict[str, Any]) -> dict[str, Any]:
    steps = status.get("step_payloads") or {}
    packet = steps.get("packet", {}) if isinstance(steps, dict) else {}
    decision = steps.get("decision", {}) if isinstance(steps, dict) else {}
    facts = packet.get("facts", {}) if isinstance(packet, dict) else {}
    soft = (facts.get("soft_preferences") or {}).get("value") or []
    hard = (facts.get("hard_constraints") or {}).get("value") or []
    followups = (decision.get("follow_up_questions") or status.get("follow_up_questions") or [])
    decision_state = decision.get("decision_state") or status.get("decision_state")
    destination_status = (facts.get("destination_status") or {}).get("value")
    return {
        "has_negation_leak_it_rushed": "it rushed" in [str(x).lower() for x in soft],
        "soft_preferences": soft,
        "hard_constraints": hard,
        "decision_state": decision_state,
        "follow_up_questions": followups,
        "destination_status": destination_status,
    }


def run_flow(flow_name: str, base_url: str, post_path: str, poll_path_tmpl: str, payload: dict[str, Any], timeout_s: int, auth_token: str) -> dict[str, Any]:
    started = time.perf_counter()
    accepted = _http_json("POST", f"{base_url}{post_path}", payload, timeout=30, auth_token=auth_token)
    run_id = accepted.get("run_id")
    if not run_id:
        raise RuntimeError(f"{flow_name} did not return run_id: {accepted}")
    final_status, snapshots, poll_runtime_ms = _poll_status(base_url, run_id, poll_path_tmpl, timeout_s, auth_token)
    step_payloads: dict[str, Any] = {}
    for step in ("packet", "validation", "decision", "strategy", "blocked_result"):
        try:
            step_resp = _http_json(
                "GET",
                f"{base_url}{poll_path_tmpl.format(run_id=run_id)}/steps/{step}",
                timeout=20,
                auth_token=auth_token,
            )
            step_payloads[step] = step_resp.get("data")
        except Exception:
            continue
    final_status["step_payloads"] = step_payloads
    try:
        events = _http_json("GET", f"{base_url}{poll_path_tmpl.format(run_id=run_id)}/events", timeout=20, auth_token=auth_token)
    except Exception as e:
        events = {"error": str(e)}
    return {
        "flow_name": flow_name,
        "base_url": base_url,
        "post_path": post_path,
        "poll_path_template": poll_path_tmpl,
        "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
        "poll_runtime_ms": round(poll_runtime_ms, 2),
        "accepted": accepted,
        "snapshots": snapshots,
        "final_status": final_status,
        "events": events,
        "quality": _extract_quality_flags(final_status),
    }


def _to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Canonical Singapore Regression Flow",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Scenario: {report['scenario']['scenario_id']} - {report['scenario']['title']}",
        "",
        "## Input (Exact)",
        "",
        "```text",
        report["scenario"]["inputs"]["raw_note"],
        "```",
        "",
        "## Flow Results",
        "",
    ]
    for flow in report["flows"]:
        status = flow["final_status"]
        quality = flow["quality"]
        lines += [
            f"### {flow['flow_name']}",
            "",
            f"- Endpoint path: `{flow['post_path']}` via `{flow['base_url']}`",
            f"- run_id: `{flow['accepted'].get('run_id')}`",
            f"- Terminal state: `{status.get('state')}`",
            f"- trip_id: `{status.get('trip_id')}`",
            f"- Runtime (ms): `{flow['runtime_ms']}`",
            f"- Decision state: `{quality.get('decision_state')}`",
            f"- Hard constraints: `{quality.get('hard_constraints')}`",
            f"- Soft preferences: `{quality.get('soft_preferences')}`",
            f"- Negation leak (`it rushed`) present: `{quality.get('has_negation_leak_it_rushed')}`",
            f"- Follow-up questions: `{quality.get('follow_up_questions')}`",
            f"- Destination status: `{quality.get('destination_status')}`",
            "",
        ]
        breaks = []
        if status.get("state") == "failed":
            breaks.append(f"state=failed: {status.get('error_message')}")
        if status.get("state") == "blocked":
            breaks.append(f"state=blocked: {status.get('block_reason')}")
        if quality.get("has_negation_leak_it_rushed"):
            breaks.append("soft preference includes malformed phrase 'it rushed'")
        if quality.get("destination_status") == "undecided":
            breaks.append("destination_status unresolved despite explicit Singapore mention")
        if breaks:
            lines.append("Observed breaks/stalls/wrong behavior:")
            lines.extend([f"- {b}" for b in breaks])
        else:
            lines.append("Observed stable behavior:")
            lines.append("- Run reached terminal state with persisted output and no timeout stall.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--frontend-base", default="http://localhost:3000")
    p.add_argument("--backend-base", default="http://localhost:8000")
    p.add_argument("--timeout-seconds", type=int, default=180)
    p.add_argument("--json-out")
    p.add_argument("--md-out")
    args = p.parse_args()

    scenario = json.loads(SCENARIO_PATH.read_text())
    payload = scenario["inputs"]
    auth_token = create_access_token(
        user_id="323468de-ba3d-437b-aa10-35b281a0c6a6",
        agency_id="d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b",
        role="owner",
    )

    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "scenario": scenario, "flows": []}
    report["flows"].append(run_flow("frontend_proxy_async_path", args.frontend_base, "/api/spine/run", "/api/runs/{run_id}", payload, args.timeout_seconds, auth_token))
    report["flows"].append(run_flow("backend_direct_async_path", args.backend_base, "/run", "/runs/{run_id}", payload, args.timeout_seconds, auth_token))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_out = Path(args.json_out) if args.json_out else REPORTS_DIR / f"singapore_canonical_regression_{stamp}.json"
    md_out = Path(args.md_out) if args.md_out else REPORTS_DIR / f"singapore_canonical_regression_{stamp}.md"
    json_out.write_text(json.dumps(report, indent=2))
    md_out.write_text(_to_markdown(report) + "\n")
    print(json.dumps({"json_out": str(json_out), "md_out": str(md_out)}, indent=2))


if __name__ == "__main__":
    main()
