"""
Model registry for SQLAlchemy and Alembic.

Import all models here so Alembic autogenerate can discover them.
"""

from core.database import Base
from models.tenant import Agency, User, Membership, WorkspaceCode
from models.frontier import GhostWorkflow, EmotionalStateLog, IntelligencePoolRecord, LegacyAspiration

__all__ = [
    "Base", 
    "Agency", 
    "User", 
    "Membership", 
    "WorkspaceCode",
    "GhostWorkflow",
    "EmotionalStateLog",
    "IntelligencePoolRecord",
    "LegacyAspiration"
]
