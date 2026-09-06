"""
Yield Arbitrage & Rate Parity Models (PER-YLD-ARB).

Defines typed schemas for multi-bedbank rate parity comparison,
cancellation penalty window tracking, and automated re-ticketing executions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass(slots=True)
class SupplierRateOffer:
    """Live rate quote from a specific wholesaler or channel."""
    supplier_name: str  # e.g., Hotelbeds, WebBeds, Sabre GDS, Direct CRS
    room_category: str
    net_cost_usd: float
    cancellation_deadline: str
    is_instant_confirmation: bool = True
    amenities_included: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supplier_name": self.supplier_name,
            "room_category": self.room_category,
            "net_cost_usd": self.net_cost_usd,
            "cancellation_deadline": self.cancellation_deadline,
            "is_instant_confirmation": self.is_instant_confirmation,
            "amenities_included": self.amenities_included,
        }


@dataclass(slots=True)
class ArbitrageOpportunity:
    """Identified price delta between current booking and alternative channels."""
    opportunity_id: str
    hotel_name: str
    booking_id: str
    current_supplier: str
    current_cost_usd: float
    target_supplier: str
    target_cost_usd: float
    gross_savings_usd: float
    spread_percent: float
    can_auto_reticket: bool
    cancellation_deadline: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "hotel_name": self.hotel_name,
            "booking_id": self.booking_id,
            "current_supplier": self.current_supplier,
            "current_cost_usd": self.current_cost_usd,
            "target_supplier": self.target_supplier,
            "target_cost_usd": self.target_cost_usd,
            "gross_savings_usd": self.gross_savings_usd,
            "spread_percent": self.spread_percent,
            "can_auto_reticket": self.can_auto_reticket,
            "cancellation_deadline": self.cancellation_deadline,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class ReTicketingExecutionResult:
    """Result of automated re-booking and voucher swap."""
    execution_id: str
    booking_id: str
    old_confirmation_code: str
    new_confirmation_code: str
    supplier_from: str
    supplier_to: str
    net_savings_captured_usd: float
    status: str = "SUCCESS_CONFIRMED"
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "booking_id": self.booking_id,
            "old_confirmation_code": self.old_confirmation_code,
            "new_confirmation_code": self.new_confirmation_code,
            "supplier_from": self.supplier_from,
            "supplier_to": self.supplier_to,
            "net_savings_captured_usd": self.net_savings_captured_usd,
            "status": self.status,
            "executed_at": self.executed_at,
        }
