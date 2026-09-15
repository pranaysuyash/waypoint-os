"""Connectivity Tier and Provider Adapter Routing for Waypoint OS.

Defines the ConnectivityTier enum (MOCK, SANDBOX, LIVE) per LIVE_CONNECTIVITY_INTEGRATION_2026-08-29.md §3.
Enforces that RealityTier cannot exceed what the underlying connectivity tier supports.
Provides unified routing for agent tools (weather, flights, price watch, safety, radar, routing).
"""

from __future__ import annotations

import os
from enum import Enum


class ConnectivityTier(str, Enum):
    """Provider-level connectivity tier."""
    MOCK = "mock"        # Deterministic in-process adapter, no network
    SANDBOX = "sandbox"  # Real network integration against provider test/sandbox environment
    LIVE = "live"        # Production provider integration with real inventory and live transactions


# Mapping of ConnectivityTier to maximum permissible RealityTier string
MAX_PERMISSIBLE_REALITY_TIER = {
    ConnectivityTier.MOCK: "DETERMINISTIC_PREVIEW",
    ConnectivityTier.SANDBOX: "CONNECTED_SANDBOX",
    ConnectivityTier.LIVE: "REAL",
}


def get_global_connectivity_tier() -> ConnectivityTier:
    """Resolve the global default connectivity tier from environment settings."""
    raw = os.getenv("CONNECTIVITY_TIER", "").strip().lower()
    if raw in {"live", "prod", "production"}:
        return ConnectivityTier.LIVE
    if raw in {"sandbox", "test", "staging"}:
        return ConnectivityTier.SANDBOX
    
    # Fallback to legacy TRAVEL_AGENT_ENABLE_LIVE_TOOLS if present
    if os.getenv("TRAVEL_AGENT_ENABLE_LIVE_TOOLS", "").strip().lower() in {"1", "true", "yes"}:
        return ConnectivityTier.SANDBOX
        
    return ConnectivityTier.MOCK


def get_tool_connectivity_tier(tool_name: str) -> ConnectivityTier:
    """Resolve connectivity tier for a specific tool class with global fallback."""
    env_var = f"CONNECTIVITY_TIER_{tool_name.upper()}"
    raw = os.getenv(env_var, "").strip().lower()
    if raw in {"live", "prod", "production"}:
        return ConnectivityTier.LIVE
    if raw in {"sandbox", "test", "staging"}:
        return ConnectivityTier.SANDBOX
    if raw in {"mock", "local"}:
        return ConnectivityTier.MOCK
    return get_global_connectivity_tier()


def assert_tier_compatibility(connectivity_tier: ConnectivityTier, claimed_reality_tier: str) -> bool:
    """Verify that a claimed RealityTier does not exceed the capability of the ConnectivityTier.
    
    Returns True if compatible, raises ValueError if the reality tier overclaims.
    """
    tier_ranks = {
        "PLANNED": 0,
        "DATA_DEPENDENT": 1,
        "DETERMINISTIC_PREVIEW": 2,
        "CONNECTED_SANDBOX": 3,
        "REAL": 4,
    }
    max_allowed = MAX_PERMISSIBLE_REALITY_TIER.get(connectivity_tier, "DETERMINISTIC_PREVIEW")
    max_rank = tier_ranks.get(max_allowed, 2)
    claimed_rank = tier_ranks.get(claimed_reality_tier.upper(), 2)

    if claimed_rank > max_rank:
        raise ValueError(
            f"Honesty violation: claimed RealityTier {claimed_reality_tier} exceeds maximum allowed "
            f"{max_allowed} for ConnectivityTier {connectivity_tier.value}"
        )
    return True
