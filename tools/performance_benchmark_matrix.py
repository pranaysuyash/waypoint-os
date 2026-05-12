#!/usr/bin/env python3
"""Run repeatable local performance benchmarks across OTel runtime scenarios.

This script executes a benchmark matrix against the running local stack using:
- `tools/dev_server_manager.py` for deterministic server lifecycle
- authenticated requests through frontend routes for user-visible latency

Outputs:
- JSON report for machine comparison
- Markdown report for human handoff/review
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import http.cookiejar
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_SERVER_MANAGER = REPO_ROOT / "tools" / "dev_server_manager.py"
RUNTIME_SMOKE = REPO_ROOT / "tools" / "runtime_smoke_matrix.py"

DEFAULT_BASE_URL = "http://127.0.0.1:3000"
DEFAULT_EMAIL = "newuser@test.com"
DEFAULT_PASSWORD = "testpass123"

DEFAULT_ENDPOINTS = (
    "/api/auth/me",
    "/overview",
    "/trips",
    "/workbench?draft=new&tab=safety",
    "/api/inbox?page=1&limit=1",
    "/api/trips?view=workspace&limit=5",
    "/api/trips?view=workspace&limit=100",
    "/api/reviews?status=pending",
    "/api/inbox/stats",
    "/api/pipeline",
    "/settings",
    "/documents",
)


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    env: dict[str, str]


SCENARIOS: dict[str, Scenario] = {
    "otel_off": Scenario(
        name="otel_off",
        description="Tracing disabled for frontend + backend.",
        env={
            "OTEL_EXPORTER_OTLP_ENDPOINT": "",
            "SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT": "",
            "OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT": "",
        },
    ),
    "otel_unreachable": Scenario(
        name="otel_unreachable",
        description="Tracing enabled but collector endpoints unreachable.",
        env={
            "SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT": "http://127.0.0.1:4317",
            "OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT": "http://127.0.0.1:4318/v1/traces",
            "SPINE_OTEL_BSP_EXPORT_TIMEOUT_MS": "2000",
            "SPINE_OTEL_BSP_SCHEDULE_DELAY_MS": "1000",
            "SPINE_OTEL_BSP_MAX_QUEUE_SIZE": "256",
            "SPINE_OTEL_BSP_MAX_EXPORT_BATCH_SIZE": "64",
            "FRONTEND_OTEL_BSP_EXPORT_TIMEOUT_MS": "2000",
            "FRONTEND_OTEL_BSP_SCHEDULE_DELAY_MS": "1000",
            "FRONTEND_OTEL_BSP_MAX_QUEUE_SIZE": "256",
            "FRONTEND_OTEL_BSP_MAX_EXPORT_BATCH_SIZE": "64",
        },
    ),
    "otel_configured": Scenario(
        name="otel_configured",
        description="Tracing enabled with caller-provided collector endpoints.",
        env={
            "SPINE_OTEL_BSP_EXPORT_TIMEOUT_MS": "3000",
            "SPINE_OTEL_BSP_SCHEDULE_DELAY_MS": "1500",
            "SPINE_OTEL_BSP_MAX_QUEUE_SIZE": "512",
            "SPINE_OTEL_BSP_MAX_EXPORT_BATCH_SIZE": "128",
            "FRONTEND_OTEL_BSP_EXPORT_TIMEOUT_MS": "3000",
            "FRONTEND_OTEL_BSP_SCHEDULE_DELAY_MS": "1500",
            "FRONTEND_OTEL_BSP_MAX_QUEUE_SIZE": "512",
            "FRONTEND_OTEL_BSP_MAX_EXPORT_BATCH_SIZE": "128",
        },
    ),
}


def run_cmd(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    timeout_s: float = 120.0,
) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            env=env or os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, f"Command timed out after {timeout_s}s\n{out}"


def restart_stack_with_env(extra_env: dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(extra_env)
    code, out = run_cmd(
        [sys.executable, str(DEV_SERVER_MANAGER), "restart", "--service", "all"],
        env=env,
        timeout_s=180.0,
    )
    if code != 0:
        raise RuntimeError(f"Failed to restart stack:\n{out}")


def run_smoke(base_url: str, email: str, password: str, retries: int = 3) -> None:
    cmd = [
        sys.executable,
        str(RUNTIME_SMOKE),
        "--preflight-local-stack",
        "--base",
        base_url,
        "--email",
        email,
        "--password",
        password,
    ]
    last_out = ""
    for attempt in range(1, retries + 1):
        code, out = run_cmd(cmd, timeout_s=90.0)
        if code == 0:
            return
        last_out = out
        time.sleep(min(2 * attempt, 5))
    raise RuntimeError(f"Smoke matrix failed after {retries} attempts:\n{last_out}")


def build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request_json(opener: urllib.request.OpenerDirector, url: str, payload: dict[str, Any]) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=20) as res:
            return int(res.getcode()), res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")


def request_status(opener: urllib.request.OpenerDirector, url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with opener.open(req, timeout=8) as res:
            return int(res.getcode()), res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, str(e)


def percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    if len(samples) == 1:
        return samples[0]
    ordered = sorted(samples)
    idx = int((len(ordered) - 1) * pct)
    return ordered[idx]


def benchmark_endpoints(
    base_url: str,
    email: str,
    password: str,
    endpoints: list[str],
    iterations: int,
) -> dict[str, Any]:
    opener = build_opener()
    login_url = urllib.parse.urljoin(base_url, "/api/auth/login")
    status, body = request_json(opener, login_url, {"email": email, "password": password})
    if status != 200:
        raise RuntimeError(f"Login failed ({status}): {body[:500]}")

    result: dict[str, Any] = {}
    for endpoint in endpoints:
        print(f"  benchmarking {endpoint} x{iterations}")
        timings_ms: list[float] = []
        statuses: list[int] = []
        for _ in range(iterations):
            url = urllib.parse.urljoin(base_url, endpoint)
            started = time.perf_counter()
            code, _ = request_status(opener, url)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            timings_ms.append(elapsed_ms)
            statuses.append(code)
        ok_codes = all(code == 200 for code in statuses)
        result[endpoint] = {
            "ok": ok_codes,
            "statuses": statuses,
            "avg_ms": round(statistics.mean(timings_ms), 2),
            "p50_ms": round(statistics.median(timings_ms), 2),
            "p95_ms": round(percentile(timings_ms, 0.95), 2),
            "p99_ms": round(percentile(timings_ms, 0.99), 2),
            "max_ms": round(max(timings_ms), 2),
            "min_ms": round(min(timings_ms), 2),
            "samples_ms": [round(v, 2) for v in timings_ms],
        }
    return result


def require_collector_env() -> dict[str, str]:
    grpc_endpoint = os.environ.get("SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT", "").strip()
    http_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT", "").strip()
    if not grpc_endpoint or not http_endpoint:
        raise RuntimeError(
            "Scenario 'otel_configured' requires both "
            "SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT and "
            "OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT in environment."
        )
    return {
        "SPINE_OTEL_EXPORTER_OTLP_GRPC_ENDPOINT": grpc_endpoint,
        "OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT": http_endpoint,
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Performance Benchmark Matrix")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at_utc']}`")
    lines.append(f"- Base URL: `{report['base_url']}`")
    lines.append(f"- Iterations per endpoint: `{report['iterations']}`")
    lines.append("")
    for scenario in report["scenarios"]:
        lines.append(f"## Scenario: `{scenario['name']}`")
        lines.append("")
        lines.append(f"- Description: {scenario['description']}")
        lines.append(f"- Smoke pass: `{scenario['smoke_passed']}`")
        lines.append("")
        lines.append("| Endpoint | Avg (ms) | P50 | P95 | P99 | Max | Status OK |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for endpoint, stats in scenario["endpoint_stats"].items():
            lines.append(
                f"| `{endpoint}` | {stats['avg_ms']} | {stats['p50_ms']} | "
                f"{stats['p95_ms']} | {stats['p99_ms']} | {stats['max_ms']} | "
                f"{'yes' if stats['ok'] else 'no'} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local performance benchmark matrix.")
    parser.add_argument(
        "--scenarios",
        default="otel_off,otel_unreachable",
        help="Comma-separated scenarios: otel_off,otel_unreachable,otel_configured",
    )
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument(
        "--output-json",
        default=None,
        help="JSON output path. Default: Docs/reports/performance_benchmark_matrix_<date>.json",
    )
    parser.add_argument(
        "--output-md",
        default=None,
        help="Markdown output path. Default: Docs/reports/performance_benchmark_matrix_<date>.md",
    )
    parser.add_argument(
        "--endpoints",
        default=",".join(DEFAULT_ENDPOINTS),
        help="Comma-separated endpoint paths relative to frontend base URL.",
    )
    args = parser.parse_args()

    selected = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    invalid = [s for s in selected if s not in SCENARIOS]
    if invalid:
        raise SystemExit(f"Unknown scenarios: {', '.join(invalid)}")

    endpoints = [e.strip() for e in args.endpoints.split(",") if e.strip()]
    if not endpoints:
        raise SystemExit("No endpoints configured.")

    date_tag = dt.datetime.utcnow().strftime("%Y-%m-%d")
    reports_dir = REPO_ROOT / "Docs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_json = Path(args.output_json) if args.output_json else reports_dir / f"performance_benchmark_matrix_{date_tag}.json"
    output_md = Path(args.output_md) if args.output_md else reports_dir / f"performance_benchmark_matrix_{date_tag}.md"

    report: dict[str, Any] = {
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "base_url": args.base,
        "iterations": args.iterations,
        "scenarios": [],
    }

    for scenario_name in selected:
        scenario = SCENARIOS[scenario_name]
        print(f"[scenario] {scenario.name}: {scenario.description}")
        env = dict(scenario.env)
        if scenario_name == "otel_configured":
            env.update(require_collector_env())

        restart_stack_with_env(env)
        run_smoke(args.base, args.email, args.password)
        endpoint_stats = benchmark_endpoints(
            base_url=args.base,
            email=args.email,
            password=args.password,
            endpoints=endpoints,
            iterations=args.iterations,
        )
        report["scenarios"].append(
            {
                "name": scenario.name,
                "description": scenario.description,
                "env": env,
                "smoke_passed": True,
                "endpoint_stats": endpoint_stats,
            }
        )

    output_json.write_text(json.dumps(report, indent=2) + "\n")
    output_md.write_text(format_markdown(report) + "\n")

    print(f"Wrote JSON report: {output_json}")
    print(f"Wrote Markdown report: {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
