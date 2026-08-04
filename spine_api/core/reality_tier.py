"""
spine_api/core/reality_tier.py — Reality Tier classification system.

Every feature in Waypoint OS declares its reality tier:
  - REAL: Production-verified behavior backed by real data and integrations
  - CONNECTED_SANDBOX: Real integration in sandbox/test mode
  - DETERMINISTIC_PREVIEW: Deterministic logic computing from real packet data,
    but without supplier verification or external confirmation
  - DATA_DEPENDENT: Feature works properly when data is available,
    returns honest "data insufficient" when it's not
  - PLANNED: Architecture and contracts built, but core capability
    requires external integration not yet connected

The tier governs:
  - What the feature may claim in responses
  - Whether it can write operational success events
  - Whether it can appear as a paid feature
  - Whether it can make safety, supplier, or financial claims
  - Whether it can mutate booking state

Design: Every response from a tiered endpoint includes a `reality_tier` metadata
field so consumers (UI, API clients, tests) know the provenance of the data.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException

logger = logging.getLogger("spine_api.core.reality_tier")


class RealityTier(str, Enum):
    """Classification of feature implementation completeness and data provenance."""

    REAL = "real"
    CONNECTED_SANDBOX = "connected_sandbox"
    DETERMINISTIC_PREVIEW = "deterministic_preview"
    DATA_DEPENDENT = "data_dependent"
    PLANNED = "planned"


# Capabilities gated by tier
TIER_CAPABILITIES: Dict[RealityTier, Dict[str, bool]] = {
    RealityTier.REAL: {
        "can_write_success_events": True,
        "can_appear_as_paid": True,
        "can_make_safety_claims": True,
        "can_make_financial_claims": True,
        "can_mutate_booking_state": True,
    },
    RealityTier.CONNECTED_SANDBOX: {
        "can_write_success_events": True,
        "can_appear_as_paid": False,
        "can_make_safety_claims": False,
        "can_make_financial_claims": False,
        "can_mutate_booking_state": False,
    },
    RealityTier.DETERMINISTIC_PREVIEW: {
        "can_write_success_events": False,
        "can_appear_as_paid": False,
        "can_make_safety_claims": False,
        "can_make_financial_claims": False,
        "can_mutate_booking_state": False,
    },
    RealityTier.DATA_DEPENDENT: {
        "can_write_success_events": False,
        "can_appear_as_paid": False,
        "can_make_safety_claims": False,
        "can_make_financial_claims": False,
        "can_mutate_booking_state": False,
    },
    RealityTier.PLANNED: {
        "can_write_success_events": False,
        "can_appear_as_paid": False,
        "can_make_safety_claims": False,
        "can_make_financial_claims": False,
        "can_mutate_booking_state": False,
    },
}


class TierMetadata:
    """Response metadata for reality-tier-aware endpoints."""

    @staticmethod
    def for_response(
        tier: RealityTier,
        feature_name: str,
        data_sufficient: bool = True,
        computation_method: Optional[str] = None,
        missing_for_upgrade: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Generate standard tier metadata to include in API responses."""
        capabilities = TIER_CAPABILITIES[tier]
        meta: Dict[str, Any] = {
            "reality_tier": tier.value,
            "feature": feature_name,
            "data_sufficient": data_sufficient,
            "capabilities": capabilities,
        }
        if computation_method:
            meta["computation_method"] = computation_method
        if missing_for_upgrade:
            meta["missing_for_upgrade"] = missing_for_upgrade
        return meta


def assert_tier_capability(
    tier: RealityTier,
    capability: str,
    feature_name: str,
) -> None:
    """
    Assert that a tier grants a specific capability.
    Raises HTTPException 403 if the tier does not grant the capability.
    """
    caps = TIER_CAPABILITIES.get(tier, {})
    if not caps.get(capability, False):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Feature '{feature_name}' at tier '{tier.value}' "
                f"does not have capability '{capability}'. "
                f"This operation requires a higher reality tier."
            ),
        )
