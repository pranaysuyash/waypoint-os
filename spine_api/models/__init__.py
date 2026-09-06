"""
Model registry for SQLAlchemy and Alembic.

Import all models here so Alembic autogenerate can discover them.
"""

from spine_api.core.database import Base
from spine_api.models.tenant import Agency, User, Membership, WorkspaceCode, AgencyIntegration
from spine_api.models.frontier import GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration
from spine_api.models.trips import Trip
from spine_api.models.agent_work import AgentWorkLease
from spine_api.models.idempotency import IdempotencyKey
from spine_api.models.audit import AuditLog
from spine_api.models.routing import TripRoutingState

__all__ = [
    "Base", 
    "Agency",
    "User",
    "Membership",
    "WorkspaceCode",
    "AgencyIntegration",
    "GhostWorkflow",
    "EmotionalStateLog",
    "IntelligencePoolRecord",
    "LegacyAspiration",
    "Trip",
    "AgentWorkLease",
    "IdempotencyKey",
    "AuditLog",
    "TripRoutingState",
]
