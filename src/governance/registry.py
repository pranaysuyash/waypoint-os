"""
src/governance/registry.py — AI Workforce Governance Registry for Waypoint OS.

Provides canonical registration, capability scoping, policy validation,
and execution limits for specialist AI workforce agents per AI_WORKFORCE_REGISTRY_CONTRACT.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class AgentTier(str, Enum):
    DETERMINISTIC_GATED = "deterministic_gated"
    AUTONOMOUS_BOUNDED = "autonomous_bounded"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


@dataclass
class AgentRegistration:
    agent_id: str
    role_name: str
    tier: AgentTier
    allowed_actions: List[str]
    max_budget_impact: float = 0.0
    is_active: bool = True
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AIWorkforceRegistry:
    """Central governance registry managing AI worker agent activations and policies."""

    def __init__(self):
        self._registry: Dict[str, AgentRegistration] = {}
        self._bootstrap_default_agents()

    def _bootstrap_default_agents(self):
        """Bootstrap default system agent roles."""
        self.register(AgentRegistration(
            agent_id="agent_intake_01",
            role_name="Intake Parsing Specialist",
            tier=AgentTier.DETERMINISTIC_GATED,
            allowed_actions=["parse_freeform_text", "extract_traveler_facts", "score_confidence"],
            max_budget_impact=0.0,
        ))
        self.register(AgentRegistration(
            agent_id="agent_strategy_01",
            role_name="Itinerary Strategy Generator",
            tier=AgentTier.AUTONOMOUS_BOUNDED,
            allowed_actions=["build_session_strategy", "rank_supplier_options", "compute_suitability"],
            max_budget_impact=10000.0,
        ))
        self.register(AgentRegistration(
            agent_id="agent_concierge_01",
            role_name="Autonomic Ghost Concierge",
            tier=AgentTier.HUMAN_APPROVAL_REQUIRED,
            allowed_actions=["monitor_disruptions", "propose_rebooking"],
            max_budget_impact=50000.0,
        ))

    def register(self, agent: AgentRegistration) -> None:
        """Register or update an AI worker agent."""
        self._registry[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Retrieve agent registration by ID."""
        return self._registry.get(agent_id)

    def validate_action(self, agent_id: str, action: str, budget_impact: float = 0.0) -> bool:
        """Validate if an agent is authorized to perform an action under policy constraints."""
        agent = self.get_agent(agent_id)
        if not agent or not agent.is_active:
            return False
        if action not in agent.allowed_actions:
            return False
        if budget_impact > agent.max_budget_impact and agent.tier != AgentTier.HUMAN_APPROVAL_REQUIRED:
            return False
        return True


# Global registry singleton
governance_registry = AIWorkforceRegistry()
