#!/usr/bin/env python3
"""
stress_test_multi_agent_workforce.py — Async Multi-Agent High-Concurrency Stress Benchmark.

Architecture Decision: ADR 16
Usage:
    python3 tools/benchmarks/stress_test_multi_agent_workforce.py --agents 50 --duration 10 --base-url http://127.0.0.1:8000
"""

import argparse
import asyncio
import time
import logging
from typing import Dict, Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stress_test")

SAMPLE_INQUIRIES = [
    "Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals.",
    "Family of 4 traveling to Singapore for 5 nights, 4-star hotel near Marina Bay, USD 5000 budget.",
    "Honeymoon trip to Maldives for 7 nights, overwater bungalow, all-inclusive, budget $8,000.",
    "Corporate team retreat to Goa for 20 adults, 3 nights, conference room required, INR 10L budget.",
]

async def simulate_agent_worker(
    agent_id: int,
    base_url: str,
    duration_sec: float,
    metrics: Dict[str, Any],
) -> None:
    """Simulate a single active agency planner agent continuously processing inquiries."""
    start_time = time.monotonic()
    inquiry_idx = agent_id % len(SAMPLE_INQUIRIES)

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        while time.monotonic() - start_time < duration_sec:
            req_start = time.monotonic()
            inquiry_text = SAMPLE_INQUIRIES[inquiry_idx % len(SAMPLE_INQUIRIES)]

            payload = {
                "agency_id": "default_agency",
                "channel": "whatsapp",
                "customer_message": f"[Agent #{agent_id}] {inquiry_text}",
                "agent_notes": "High priority test lead",
                "operating_mode": "normal_intake",
            }

            try:
                # 1. Dispatch inbound inquiry
                res = await client.post("/api/v1/inbound/process", json=payload)
                elapsed = (time.monotonic() - req_start) * 1000.0

                if res.status_code == 200:
                    metrics["success_count"] += 1
                    metrics["latencies"].append(elapsed)
                else:
                    metrics["error_count"] += 1
                    metrics["error_details"].append(f"HTTP {res.status_code}: {res.text[:100]}")
            except Exception as exc:
                metrics["error_count"] += 1
                metrics["error_details"].append(str(exc))

            inquiry_idx += 1
            await asyncio.sleep(0.1) # brief pacing interval

async def run_stress_test(num_agents: int, duration: float, base_url: str) -> Dict[str, Any]:
    logger.info(f"Starting multi-agent stress benchmark with {num_agents} concurrent agents for {duration}s against {base_url}...")

    metrics: Dict[str, Any] = {
        "success_count": 0,
        "error_count": 0,
        "latencies": [],
        "error_details": [],
    }

    tasks = [
        simulate_agent_worker(i, base_url, duration, metrics)
        for i in range(num_agents)
    ]

    start_bench = time.monotonic()
    await asyncio.gather(*tasks)
    total_time = time.monotonic() - start_bench

    latencies = metrics["latencies"]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    sorted_lat = sorted(latencies) if latencies else [0.0]
    p95_index = int(len(sorted_lat) * 0.95)
    p95_latency = sorted_lat[min(p95_index, len(sorted_lat) - 1)]

    throughput_rps = metrics["success_count"] / total_time if total_time > 0 else 0.0

    report = {
        "num_agents": num_agents,
        "duration_sec": total_time,
        "total_requests": metrics["success_count"] + metrics["error_count"],
        "success_count": metrics["success_count"],
        "error_count": metrics["error_count"],
        "throughput_rps": round(throughput_rps, 2),
        "inquiries_per_min": round(throughput_rps * 60.0, 1),
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
    }

    logger.info("=== BENCHMARK REPORT ===")
    for k, v in report.items():
        logger.info(f"  {k}: {v}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Stress Test Benchmark")
    parser.add_argument("--agents", type=int, default=50, help="Number of concurrent agents")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration in seconds")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000", help="Spine API base URL")
    args = parser.parse_args()

    asyncio.run(run_stress_test(args.agents, args.duration, args.base_url))

if __name__ == "__main__":
    main()
