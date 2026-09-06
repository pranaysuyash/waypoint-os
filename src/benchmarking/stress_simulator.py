"""
Autonomous Multi-Agent Load & Stress Benchmarking Engine.

Simulates massive hub irregular operations (IROPS) with 500+ concurrent
traveler disruptions to evaluate P99 latency, VCC issuance throughput, and memory bounds.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.orchestration.irops_healer import IROPSAutoHealerEngine


@dataclass(slots=True)
class StressBenchmarkResult:
    """Aggregated telemetry from high-concurrency simulation."""
    concurrency_level: int
    total_disruptions_processed: int
    successful_heals: int
    failed_heals: int
    p50_latency_ms: float
    p90_latency_ms: float
    p99_latency_ms: float
    throughput_ops_per_sec: float
    total_vcc_cards_issued: int
    total_statutory_claims_eur: float
    total_fee_waivers_filed: int
    execution_duration_sec: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concurrency_level": self.concurrency_level,
            "total_disruptions_processed": self.total_disruptions_processed,
            "successful_heals": self.successful_heals,
            "failed_heals": self.failed_heals,
            "latency_percentiles_ms": {
                "p50": self.p50_latency_ms,
                "p90": self.p90_latency_ms,
                "p99": self.p99_latency_ms,
            },
            "throughput_ops_per_sec": self.throughput_ops_per_sec,
            "total_vcc_cards_issued": self.total_vcc_cards_issued,
            "total_statutory_claims_eur": self.total_statutory_claims_eur,
            "total_fee_waivers_filed": self.total_fee_waivers_filed,
            "execution_duration_sec": self.execution_duration_sec,
            "timestamp": self.timestamp,
        }


class MultiAgentStressSimulator:
    """Executes high-throughput concurrent IROPS auto-healing simulations."""

    @classmethod
    async def run_concurrent_irops_benchmark(
        cls,
        concurrency: int = 100,
    ) -> StressBenchmarkResult:
        """Runs concurrent IROPS auto-healing passes and calculates exact percentiles."""
        hub_pairs = [
            ("LHR", "JFK", "BA178", 240, 5500),
            ("CDG", "NRT", "AF276", 320, 9700),
            ("FRA", "SIN", "LH778", 195, 10200),
            ("DXB", "LAX", "EK215", 420, 13400),
            ("SFO", "SYD", "UA863", 210, 11900),
        ]

        latencies_ms: List[float] = []
        vcc_count = 0
        statutory_claims_eur = 0.0
        fee_waivers_count = 0
        success_count = 0
        fail_count = 0

        async def _heal_task(idx: int):
            nonlocal vcc_count, statutory_claims_eur, fee_waivers_count, success_count, fail_count
            _, _, flight, delay, dist = hub_pairs[idx % len(hub_pairs)]
            t0 = time.perf_counter()
            try:
                # Run synchronous engine in async threadpool to simulate concurrent I/O
                plan = await asyncio.to_thread(
                    IROPSAutoHealerEngine.execute_healing_protocol,
                    trip_id=f"TRIP-BENCH-{idx:04d}",
                    delayed_node_id="N_FLT_178",
                    delay_minutes=delay,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies_ms.append(elapsed_ms)
                success_count += 1
                if plan.emergency_lodging_vcc:
                    vcc_count += 1
                if plan.statutory_compensation_amount_eur:
                    statutory_claims_eur += plan.statutory_compensation_amount_eur
                if plan.waiver_dispute_letter:
                    fee_waivers_count += 1
            except Exception:
                fail_count += 1

        start_time = time.perf_counter()
        tasks = [_heal_task(i) for i in range(concurrency)]
        await asyncio.gather(*tasks)
        total_duration = time.perf_counter() - start_time

        latencies_ms.sort()
        n = len(latencies_ms)
        p50 = latencies_ms[int(n * 0.50)] if n > 0 else 0.0
        p90 = latencies_ms[int(n * 0.90)] if n > 0 else 0.0
        p99 = latencies_ms[int(n * 0.99)] if n > 0 else 0.0
        throughput = round(success_count / total_duration, 1) if total_duration > 0 else 0.0

        return StressBenchmarkResult(
            concurrency_level=concurrency,
            total_disruptions_processed=concurrency,
            successful_heals=success_count,
            failed_heals=fail_count,
            p50_latency_ms=round(p50, 2),
            p90_latency_ms=round(p90, 2),
            p99_latency_ms=round(p99, 2),
            throughput_ops_per_sec=throughput,
            total_vcc_cards_issued=vcc_count,
            total_statutory_claims_eur=statutory_claims_eur,
            total_fee_waivers_filed=fee_waivers_count,
            execution_duration_sec=round(total_duration, 3),
        )
