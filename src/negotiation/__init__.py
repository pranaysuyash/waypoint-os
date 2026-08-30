"""
Negotiation & Dynamic Margin Package (PER-950888, PER-20690, PER-0482).
"""

from src.negotiation.models import (
    NegotiationSession,
    NegotiationStatus,
    ConcessionItem,
    ConcessionType,
    VolumeTier,
    MarginOptimizationResult,
)
from src.negotiation.bargaining_engine import BargainingEngine
from src.negotiation.margin_optimizer import MarginOptimizer
from src.negotiation.fee_waiver_bot import FeeWaiverBot

__all__ = [
    "NegotiationSession",
    "NegotiationStatus",
    "ConcessionItem",
    "ConcessionType",
    "VolumeTier",
    "MarginOptimizationResult",
    "BargainingEngine",
    "MarginOptimizer",
    "FeeWaiverBot",
]
