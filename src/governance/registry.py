"""
src/governance/registry.py — AI Workforce Governance Registry for Waypoint OS.

Provides canonical registration, capability scoping, policy validation,
and execution limits for specialist AI workforce agents per AI_WORKFORCE_REGISTRY_CONTRACT.md.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Iterator, List, Optional


class AgentTier(str, Enum):
    DETERMINISTIC_GATED = "deterministic_gated"
    AUTONOMOUS_BOUNDED = "autonomous_bounded"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


class AuthorityDenied(PermissionError):
    """Raised when an agent/action/amount combination is not authorized.

    PA-08: this exception exists so execution paths (fulfillment, payouts) can
    fail closed with an explicit, machine-readable denial instead of silently
    proceeding when the governance registry has no authority record.

    PA-08 wave 2: reserved for hard denials — unregistered/inactive agent or a
    forbidden action. An over-cap amount now raises
    :class:`AuthorityApprovalRequired` so the caller can resolve it through a
    ratified dual-control approval instead of failing outright.
    """

    def __init__(self, agent_id: str, action: str, reason: str) -> None:
        super().__init__(reason)
        self.agent_id = agent_id
        self.action = action
        self.reason = reason


class AuthorityApprovalRequired(PermissionError):
    """Raised when an amount exceeds the agent's budget cap (PA-08 wave 2).

    Distinct from :class:`AuthorityDenied` so callers can check for a
    ratified dual-control approval
    (``spine_api.services.authority_approval_service.AuthorityApprovalLedger.get_approved``)
    and proceed when one exists, instead of failing outright. Never a subclass
    of ``AuthorityDenied`` — the denial → 403 conversion in gated engines must
    not swallow it.
    """

    def __init__(
        self,
        agent_id: str,
        action: str,
        amount_usd: Optional[float],
        max_budget_impact: float,
        reason: str,
    ) -> None:
        super().__init__(reason)
        self.agent_id = agent_id
        self.action = action
        self.amount_usd = amount_usd
        self.max_budget_impact = max_budget_impact
        self.reason = reason


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
        # PA-08: execution agents that now call enforce_action_authority must
        # exist in the registry — an unregistered execution agent fails closed.
        self.register(AgentRegistration(
            agent_id="agent_fulfillment_01",
            role_name="Booking Fulfillment Specialist",
            tier=AgentTier.AUTONOMOUS_BOUNDED,
            allowed_actions=["fulfill_accepted_proposal"],
            max_budget_impact=50000.0,
        ))
        self.register(AgentRegistration(
            agent_id="advisor_payout",
            role_name="IC Advisor Payout Authorizer",
            tier=AgentTier.HUMAN_APPROVAL_REQUIRED,
            allowed_actions=["authorize_advisor_payout"],
            max_budget_impact=2000.0,
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


def enforce_action_authority(
    agent: str,
    action: str,
    amount_usd: Optional[float] = None,
) -> Dict[str, object]:
    """Enforce registry authority on an execution path (PA-08).

    Unlike ``validate_action`` (a passive boolean query), this is the gate that
    consequential paths MUST call before executing. It raises
    ``AuthorityDenied`` when the agent is unknown/inactive or the action is
    outside the agent's ``allowed_actions`` — hard denials with no approval
    remedy. When the dollar amount exceeds the agent's ``max_budget_impact``,
    it raises ``AuthorityApprovalRequired`` (PA-08 wave 2): the caller checks
    for a ratified dual-control approval
    (``AuthorityApprovalLedger.get_approved(agency_id, action, subject_id)``)
    and proceeds when one exists, or surfaces the escalation to a human
    operator. The budget check is applied regardless of tier — a registry row
    is an authorization boundary, not a catalog entry.

    Returns an evidence dict describing the granted check (for audit trails).
    Pass ``amount_usd=None`` when no amount is known to check action
    permission only.
    """
    registration = governance_registry.get_agent(agent)
    if registration is None or not registration.is_active:
        raise AuthorityDenied(
            agent,
            action,
            f"Agent '{agent}' is not registered in the governance registry (or is inactive). "
            f"Escalation to a human operator is required.",
        )
    if action not in registration.allowed_actions:
        raise AuthorityDenied(
            agent,
            action,
            f"Action '{action}' is not in the allowed_actions of agent '{agent}' "
            f"({registration.allowed_actions}). Escalation to a human operator is required.",
        )
    if amount_usd is not None and amount_usd > registration.max_budget_impact:
        # PA-08 wave 2: over-cap is an approval-remediable outcome, not a hard
        # denial — a ratified dual-control approval for this exact subject is
        # sufficient authority to proceed.
        raise AuthorityApprovalRequired(
            agent,
            action,
            amount_usd,
            registration.max_budget_impact,
            f"Amount ${amount_usd:,.2f} exceeds max_budget_impact "
            f"${registration.max_budget_impact:,.2f} for agent '{agent}'. "
            f"Escalation to a human operator is required.",
        )
    return {
        "agent": agent,
        "action": action,
        "tier": registration.tier.value,
        "max_budget_impact": registration.max_budget_impact,
        "checked_amount_usd": amount_usd,
        "granted": True,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


_SCOPE_LOCK = threading.Lock()


@contextmanager
def ratified_authority_scope(agent_id: str, action: str, amount_usd: float) -> Iterator[Dict[str, object]]:
    """Scoped elevation for an action already covered by a ratified approval.

    Callers use this ONLY after confirming a ratified dual-control approval
    exists for the exact (agency, action, subject) — the approval IS the
    authority; this context manager just lets the gated execution path pass
    the per-agent cap for the amounts involved. The agent's registration is
    elevated to ``max(current_cap, amount_usd)`` for the duration of the
    block and is ALWAYS restored afterwards (lock-guarded swap, restore in
    ``finally``). Action permission and agent registration are still enforced
    inside the scope — only the cap is raised.
    """
    registration = governance_registry.get_agent(agent_id)
    if registration is None or not registration.is_active:
        raise AuthorityDenied(
            agent_id,
            action,
            f"Agent '{agent_id}' is not registered in the governance registry (or is inactive).",
        )
    if action not in registration.allowed_actions:
        raise AuthorityDenied(
            agent_id,
            action,
            f"Action '{action}' is not in the allowed_actions of agent '{agent_id}'.",
        )
    elevated = AgentRegistration(
        agent_id=registration.agent_id,
        role_name=registration.role_name,
        tier=registration.tier,
        allowed_actions=list(registration.allowed_actions),
        max_budget_impact=max(registration.max_budget_impact, float(amount_usd)),
        is_active=True,
        registered_at=registration.registered_at,
    )
    with _SCOPE_LOCK:
        governance_registry.register(elevated)
        try:
            yield enforce_action_authority(agent_id, action, amount_usd)
        finally:
            governance_registry.register(registration)


# Global registry singleton
governance_registry = AIWorkforceRegistry()
