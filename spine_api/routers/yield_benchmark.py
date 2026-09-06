"""
Multi-Property Yield Benchmark API Router.

Provides endpoints for running comprehensive bedbank vs GDS rate parity simulations
across luxury hotel properties.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from src.yield_arbitrage.multi_property_benchmark import MultiPropertyYieldBenchmark

router = APIRouter(prefix="/api/v1/yield-arbitrage", tags=["yield-benchmark"])


@router.get("/benchmark/simulate")
def run_yield_benchmark_simulation() -> Dict[str, Any]:
    """Runs a multi-property rate parity benchmark simulation across wholesale channels."""
    return MultiPropertyYieldBenchmark.run_100_property_benchmark()
