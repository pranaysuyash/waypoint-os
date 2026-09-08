"""
Stress & Load Benchmarking API Router.

Provides endpoints to trigger high-concurrency simulation of multi-agent IROPS healing.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.benchmarking.stress_simulator import MultiAgentStressSimulator
from spine_api.core.feature_gates import get_feature_tier
from spine_api.core.reality_tier import TierMetadata

router = APIRouter(prefix="/api/v1/benchmarking", tags=["benchmarking"])


class StressTestRequest(BaseModel):
    concurrency: int = Field(50, ge=1, le=1000, description="Number of concurrent disruption tasks to execute")


@router.post("/stress-test")
async def execute_stress_test(payload: StressTestRequest) -> Dict[str, Any]:
    """Runs concurrent IROPS auto-healing passes and returns latency percentiles and throughput."""
    result = await MultiAgentStressSimulator.run_concurrent_irops_benchmark(concurrency=payload.concurrency)
    return {
        "status": "success",
        "benchmark_metrics": result.to_dict(),
        "_meta": TierMetadata.for_response(
            get_feature_tier("stress_benchmark"),
            "stress_benchmark",
            computation_method="simulated concurrency over in-process fixtures; measures engine throughput, not provider capacity",
        ),
    }
