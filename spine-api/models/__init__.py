"""
Model registry for SQLAlchemy and Alembic.

Import all models here so Alembic autogenerate can discover them.
"""

from core.database import Base
from models.tenant import Agency, User, Membership, WorkspaceCode

__all__ = ["Base", "Agency", "User", "Membership", "WorkspaceCode"]
