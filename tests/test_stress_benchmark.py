"""
Unit & Integration Tests for Stress Simulator (Milestone 2).
"""

import pytest
from src.benchmarking.stress_simulator import MultiAgentStressSimulator


@pytest.mark.asyncio
async def test_concurrent_irops_benchmark_execution():
    result = await MultiAgentStressSimulator.run_concurrent_irops_benchmark(concurrency=25)

    assert result.concurrency_level == 25
    assert result.successful_heals == 25
    assert result.failed_heals == 0
    assert result.p50_latency_ms > 0
    assert result.p99_latency_ms >= result.p50_latency_ms
    assert result.throughput_ops_per_sec > 0
    assert result.total_vcc_cards_issued == 25
    assert result.total_statutory_claims_eur > 0
