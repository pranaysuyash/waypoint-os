"""
agents.events — Canonical event envelope for backend product-agent actions.

This keeps agent observability structured and queryable across agents.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class AgentEventType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_DECISION = "agent_decision"
    AGENT_ACTION = "agent_action"
    AGENT_FAILED = "agent_failed"
    AGENT_RETRY = "agent_retry"
    AGENT_ESCALATED = "agent_escalated"


@dataclass(slots=True)
class AgentEvent:
    agent_name: str
    event_type: AgentEventType
    trip_id: Optional[str] = None
    run_id: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: f"agt_{uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return data
