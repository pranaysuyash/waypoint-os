"""
intake.sourcing_path — Sourcing path resolution for trip procurement.

Determines how the operator should source packages for a trip:
  - internal_package: Agency's own curated package (highest margin, most control)
  - preferred_supplier: Known supplier with negotiated rates
  - network: Partner network / DMC
  - open_market: Public booking platforms (lowest margin, highest availability)

Currently a stub implementation — no supplier/package database exists yet.
When real supplier data becomes available (preferred_supplier table, package
inventory, DMC contracts), this module is the single extension point.

Architecture:
    resolution → SourcingPathResolver.resolve(packet) → SourcingPathResult

    Resolution logic:
    1. If owner_constraints exist → "network" (operator has specific supplier
       relationships; formalize before upgrading to "preferred_supplier")
    2. Default → "open_market" (safest default — always available, lowest
       margin, no false promises to the customer)

Future extension: PLUG a future supplier/package database here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SourcingTier(str, Enum):
    """Sourcing tiers ordered by operator control (highest → lowest)."""
    INTERNAL_PACKAGE = "internal_package"
    PREFERRED_SUPPLIER = "preferred_supplier"
    NETWORK = "network"
    OPEN_MARKET = "open_market"


@dataclass(slots=True)
class SourcingPathResult:
    """Result of sourcing path resolution for a trip packet."""
    tier: SourcingTier
    confidence: float
    reason: str
    supplier_hints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourcingPathResolver:
    """
    Determines the sourcing path (procurement tier) for a trip.

    Single extension point for future supplier/package database integration.
    All sourcing path logic flows through this resolver so that when real
    supplier data becomes available, only this module needs to change.
    """

    # Future: plug in supplier database, package inventory, DMC contracts here
    # _supplier_store: Optional[SupplierStore] = None
    # _package_store: Optional[PackageStore] = None

    def resolve(self, packet: Any) -> SourcingPathResult:
        """
        Determine the sourcing tier for a trip packet.

        Args:
            packet: CanonicalPacket with extracted facts and derived signals

        Returns:
            SourcingPathResult with tier, confidence, and rationale
        """
        facts = getattr(packet, "facts", {})

        # Check for internal package signals (future: package inventory lookup)
        if self._has_internal_package(facts):
            return SourcingPathResult(
                tier=SourcingTier.INTERNAL_PACKAGE,
                confidence=0.95,
                reason="Trip matches an existing internal package",
            )

        # Check for preferred supplier signals (future: supplier DB lookup)
        preferred_hints = self._check_preferred_supplier(facts)
        if preferred_hints:
            return SourcingPathResult(
                tier=SourcingTier.PREFERRED_SUPPLIER,
                confidence=0.85,
                reason="Destination or constraints match known preferred suppliers",
                supplier_hints=preferred_hints,
            )

        # Check for owner-supplied constraints (operator has relationships)
        if self._has_owner_constraints(facts):
            return SourcingPathResult(
                tier=SourcingTier.NETWORK,
                confidence=0.50,
                reason="Owner constraints present — likely has network contacts",
                metadata={"stub": True, "note": "Formalize supplier relationships to upgrade tier"},
            )

        # Default: open market (always available, no false promises)
        return SourcingPathResult(
            tier=SourcingTier.OPEN_MARKET,
            confidence=0.90,
            reason="No internal or preferred supplier data available — defaulting to open market",
            metadata={"stub": True, "note": "Supplier database not yet integrated"},
        )

    def _has_internal_package(self, facts: Dict[str, Any]) -> bool:
        """Check if packet matches an internal package (stub — no package DB)."""
        return False

    def _check_preferred_supplier(self, facts: Dict[str, Any]) -> List[str]:
        """Check for known preferred supplier matches (stub — no supplier DB)."""
        return []

    def _has_owner_constraints(self, facts: Dict[str, Any]) -> bool:
        """Check if owner_constraints fact is present."""
        if "owner_constraints" not in facts:
            return False
        oc_slot = facts["owner_constraints"]
        value = getattr(oc_slot, "value", None)
        if value and isinstance(value, (list, tuple)):
            return len(value) > 0
        return bool(value)


# Module-level singleton
_default_resolver: Optional[SourcingPathResolver] = None


def get_sourcing_path_resolver() -> SourcingPathResolver:
    """Get the singleton sourcing path resolver."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = SourcingPathResolver()
    return _default_resolver


def resolve_sourcing_path(packet: Any) -> SourcingPathResult:
    """Convenience function: resolve sourcing path for a packet."""
    return get_sourcing_path_resolver().resolve(packet)
