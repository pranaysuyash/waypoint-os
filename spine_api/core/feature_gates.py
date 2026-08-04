"""
spine_api/core/feature_gates.py — Central feature registry with reality tiers.

Every product feature is registered here with its current reality tier.
This is the single source of truth for what the system can honestly claim.

Usage in routers:
    from spine_api.core.feature_gates import FEATURE_REGISTRY, get_feature_tier

    tier = get_feature_tier("trust_scorecard")
    # Include tier metadata in response:
    response["_meta"] = TierMetadata.for_response(tier, "trust_scorecard")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from spine_api.core.reality_tier import RealityTier

logger = logging.getLogger("spine_api.core.feature_gates")


@dataclass(slots=True)
class FeatureRegistryEntry:
    """Registration of a single product feature with its reality tier."""

    name: str
    tier: RealityTier
    description: str
    honest_status: str  # What we tell users about this feature's state
    requires_integration: Optional[str] = None  # What external integration is needed for upgrade
    data_source: Optional[str] = None  # Where the feature's data comes from


# ─────────────────────────────────────────────────────────────
# Central Feature Registry
# ─────────────────────────────────────────────────────────────
# Update this registry whenever a feature's implementation status changes.
# Every feature must be registered here before it can serve responses.

FEATURE_REGISTRY: Dict[str, FeatureRegistryEntry] = {
    # ── Core workflow (REAL) ──
    "intake_extraction": FeatureRegistryEntry(
        name="intake_extraction",
        tier=RealityTier.REAL,
        description="Extract structured trip data from raw enquiry text",
        honest_status="Deterministic extraction pipeline with LLM fallback",
        data_source="User-provided enquiry text + extraction pipeline",
    ),
    "gap_detection": FeatureRegistryEntry(
        name="gap_detection",
        tier=RealityTier.REAL,
        description="Detect missing information in trip packets",
        honest_status="Deterministic field presence + validation checks",
        data_source="Packet field analysis",
    ),
    "decision_pipeline": FeatureRegistryEntry(
        name="decision_pipeline",
        tier=RealityTier.REAL,
        description="Suitability scoring and decision logic",
        honest_status="Deterministic scoring from packet data",
        data_source="Packet fields + validation rules",
    ),
    "trip_persistence": FeatureRegistryEntry(
        name="trip_persistence",
        tier=RealityTier.REAL,
        description="Store and retrieve trip records",
        honest_status="PostgreSQL with agency-scoped access",
        data_source="Database",
    ),
    "operator_review": FeatureRegistryEntry(
        name="operator_review",
        tier=RealityTier.REAL,
        description="Owner review workflow for trip briefs",
        honest_status="Full review cycle with audit trail",
        data_source="Trip store + audit events",
    ),

    # ── Trust & transparency (DETERMINISTIC_PREVIEW) ──
    "trust_scorecard": FeatureRegistryEntry(
        name="trust_scorecard",
        tier=RealityTier.DETERMINISTIC_PREVIEW,
        description="Trust/confidence scorecard computed from real packet data",
        honest_status="Scores computed from packet completeness, budget alignment, and review status. Not supplier-verified.",
        data_source="Packet fields + review status",
        requires_integration="Supplier verification APIs for tier upgrade to REAL",
    ),

    # ── Proposal lifecycle (DATA_DEPENDENT) ──
    "proposal_lifecycle": FeatureRegistryEntry(
        name="proposal_lifecycle",
        tier=RealityTier.DATA_DEPENDENT,
        description="Token-based proposal sharing and acceptance",
        honest_status="Proposal generation, sharing, and acceptance. No payment processing.",
        data_source="Trip store + proposal tokens",
        requires_integration="Payment gateway for booking confirmation",
    ),

    # ── Social inbound (DATA_DEPENDENT) ──
    "social_inbound": FeatureRegistryEntry(
        name="social_inbound",
        tier=RealityTier.DATA_DEPENDENT,
        description="Intake from social/messaging channels",
        honest_status="Routes through real extraction pipeline. Quality depends on input text quality.",
        data_source="Raw text + extraction pipeline",
    ),

    # ── Corporate duty-of-care (DATA_DEPENDENT) ──
    "corporate_duty_of_care": FeatureRegistryEntry(
        name="corporate_duty_of_care",
        tier=RealityTier.DATA_DEPENDENT,
        description="Corporate traveler tracking and policy compliance",
        honest_status="Tracks travelers and trips from real data. Live flight tracking not available.",
        data_source="Trip store + agency corporate client config",
        requires_integration="Flight tracking API, corporate travel policy engine",
    ),

    # ── Supplier management (DATA_DEPENDENT) ──
    "supplier_management": FeatureRegistryEntry(
        name="supplier_management",
        tier=RealityTier.DATA_DEPENDENT,
        description="Supplier contract and inventory management",
        honest_status="Store and manage supplier contracts. Inventory holds tracked but require manual confirmation.",
        data_source="Supplier contract database",
        requires_integration="Supplier booking APIs for automated holds",
    ),

    # ── Concierge (DATA_DEPENDENT) ──
    "concierge": FeatureRegistryEntry(
        name="concierge",
        tier=RealityTier.DATA_DEPENDENT,
        description="Trip disruption detection and resolution proposals",
        honest_status="Detects issues from trip data. Proposes resolutions for operator review. No automated rebooking.",
        data_source="Trip store + traveler data",
        requires_integration="Airline/hotel booking APIs for automated rebooking",
    ),

    # ── Yield arbitrage (DATA_DEPENDENT) ──
    "yield_arbitrage": FeatureRegistryEntry(
        name="yield_arbitrage",
        tier=RealityTier.DATA_DEPENDENT,
        description="Rate comparison across supplier channels",
        honest_status="Compares rates from stored supplier contracts. No live GDS/wholesaler queries.",
        data_source="Supplier contract database",
        requires_integration="GDS API, wholesaler APIs for live rate comparison",
    ),

    # ── Agent system (REAL) ──
    "agent_registry": FeatureRegistryEntry(
        name="agent_registry",
        tier=RealityTier.REAL,
        description="Product-agent registration and lifecycle",
        honest_status="Registry, supervisor, health checks, recovery",
        data_source="In-process agent registry",
    ),
}


def get_feature_tier(feature_name: str) -> RealityTier:
    """Get the current reality tier for a named feature."""
    entry = FEATURE_REGISTRY.get(feature_name)
    if entry is None:
        logger.warning("Feature '%s' not found in registry, defaulting to PLANNED", feature_name)
        return RealityTier.PLANNED
    return entry.tier


def get_feature_entry(feature_name: str) -> Optional[FeatureRegistryEntry]:
    """Get the full registry entry for a feature."""
    return FEATURE_REGISTRY.get(feature_name)


def get_all_features() -> Dict[str, FeatureRegistryEntry]:
    """Return the complete feature registry."""
    return FEATURE_REGISTRY.copy()


def log_feature_status() -> None:
    """Log the reality tier status of all registered features at startup."""
    logger.info("═══ Feature Reality Tier Status ═══")
    for name, entry in sorted(FEATURE_REGISTRY.items()):
        logger.info(
            "  %-30s  tier=%-25s  status=%s",
            name,
            entry.tier.value,
            entry.honest_status[:80],
        )
    logger.info("═══ End Feature Status ═══")
