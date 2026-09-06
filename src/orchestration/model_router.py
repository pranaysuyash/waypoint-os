"""
src/orchestration/model_router.py — Dynamic 3-Tier Model Capability Router (Task C-03).

Routes traveler inquiries, optimization tasks, and agent workflows to the optimal
capability tier:
- Tier 0: On-Device / Edge SLM (Gemma-2-2B / Llama-3.2-1B) for real-time drafting & PII sanitization.
- Tier 1: Fast Pipeline Spine (Gemini 1.5 Flash / Claude 3.5 Haiku) for structured extraction (<900ms).
- Tier 2: Frontier Reasoning (Gemini 1.5 Pro / Claude 3.7 Sonnet) for multi-party Pareto, IRROPS & disputes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ModelTier(str, Enum):
    TIER_0_EDGE_SLM = "TIER_0_EDGE_SLM"
    TIER_1_FLASH = "TIER_1_FLASH"
    TIER_2_PRO_REASONING = "TIER_2_PRO_REASONING"


@dataclass(slots=True)
class RoutingDecision:
    tier: ModelTier
    model_name: str
    target_latency_ms: int
    cost_per_1m_tokens_usd: float
    routing_reason: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tier"] = self.tier.value
        return d


class ModelCapabilityRouter:
    """Intelligent capability router matching workload complexity to model tier."""

    # Keywords triggering frontier reasoning
    _FRONTIER_REASONING_PATTERNS = [
        r"\b(?:dispute|compensation|eu\s*261|statutory|denied\s+boarding|cancelled\s+flight|claim)\b",
        r"\b(?:multi[-\s]?party|different\s+budgets|split\s+budget|pareto|conflicting\s+priorities)\b",
        r"\b(?:evacuation|crisis|embassy|security\s+threat|emergency\s+reroute)\b",
        r"\b(?:contract\s+negotiation|wholesale\s+arbitrage|override\s+margin)\b",
    ]

    _FRONTIER_COMPILED = [re.compile(p, re.IGNORECASE) for p in _FRONTIER_REASONING_PATTERNS]

    @classmethod
    def classify_and_route(
        cls,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        ctx = context or {}
        text_clean = text or ""

        # 1. Check if explicit task requires Tier 2 (Persona Council / Disputes / Multi-party)
        task_type = str(ctx.get("task_type") or "").lower()
        if task_type in ("group_pareto", "crisis_evacuation", "passenger_rights", "yield_arbitrage", "irops_healer"):
            return RoutingDecision(
                tier=ModelTier.TIER_2_PRO_REASONING,
                model_name="gemini-1.5-pro",
                target_latency_ms=3500,
                cost_per_1m_tokens_usd=1.25,
                routing_reason=f"Task type '{task_type}' requires frontier multi-constraint reasoning.",
            )

        # 2. Check group size and multi-party complexity
        pax_count = int(ctx.get("pax_count") or ctx.get("party_size") or 1)
        subgroups_count = int(ctx.get("subgroups_count") or len(ctx.get("subgroups") or []))
        if pax_count > 6 or subgroups_count > 1:
            return RoutingDecision(
                tier=ModelTier.TIER_2_PRO_REASONING,
                model_name="gemini-1.5-pro",
                target_latency_ms=3000,
                cost_per_1m_tokens_usd=1.25,
                routing_reason=f"Large multi-party group ({pax_count} pax, {subgroups_count} subgroups) requires Pareto consensus.",
            )

        # 3. Check for text complexity triggers (legal claims, crisis, complex dispute)
        for pattern in cls._FRONTIER_COMPILED:
            if pattern.search(text_clean):
                return RoutingDecision(
                    tier=ModelTier.TIER_2_PRO_REASONING,
                    model_name="gemini-1.5-pro",
                    target_latency_ms=3200,
                    cost_per_1m_tokens_usd=1.25,
                    routing_reason="Detected high-complexity semantic trigger (legal/dispute/crisis/negotiation).",
                )

        # 4. Check for client-side / edge SLM drafting task
        if task_type in ("pii_redaction", "client_pre_filter", "realtime_typeahead"):
            return RoutingDecision(
                tier=ModelTier.TIER_0_EDGE_SLM,
                model_name="gemma-2-2b-it",
                target_latency_ms=120,
                cost_per_1m_tokens_usd=0.0,
                routing_reason="Sub-second edge drafting or PII redaction suitable for on-device SLM.",
            )

        # 5. Default: Tier 1 High-Throughput Flash Pipeline (<900ms)
        return RoutingDecision(
            tier=ModelTier.TIER_1_FLASH,
            model_name="gemini-1.5-flash",
            target_latency_ms=650,
            cost_per_1m_tokens_usd=0.075,
            routing_reason="Standard conversational intake extraction routed to fast high-throughput pipeline.",
        )
