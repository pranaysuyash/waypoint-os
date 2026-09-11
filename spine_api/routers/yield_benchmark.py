"""
Multi-Property Yield Benchmark API Router.

Provides endpoints for running comprehensive bedbank vs GDS rate parity simulations
across luxury hotel properties.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

from spine_api.core.feature_gates import get_feature_tier
from spine_api.core.reality_tier import TierMetadata

from src.yield_arbitrage.multi_property_benchmark import MultiPropertyYieldBenchmark

router = APIRouter(prefix="/api/v1/yield-arbitrage", tags=["yield-benchmark"])


@router.get("/benchmark/simulate")
def run_yield_benchmark_simulation() -> Dict[str, Any]:
    """Runs a multi-property rate parity benchmark simulation across wholesale channels."""
    return {
        **MultiPropertyYieldBenchmark.run_100_property_benchmark(),
        # A6 Wave 1.4 (FND-0261 follow-up): the benchmark runs over synthesized
        # fixture properties — label it so the parity output cannot be read as
        # a live market observation.
        "_meta": TierMetadata.for_response(
            get_feature_tier("yield_benchmark"),
            "yield_benchmark",
            computation_method="synthesized 100-property fixture benchmark; no live rate sources",
        ),
    }
