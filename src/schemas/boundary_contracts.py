"""
src/schemas/boundary_contracts.py — Trust zones, boundary contracts, and capability tokens.

Grounding doctrine:
- PER-0933 (Boundary Systems Architect): Explicit interface contracts, trust zones, ownership boundaries.
- PER-0927 (Human-AI Authority Architect): Multi-tier authority matrix and decision delegation rights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TrustZone(str, Enum):
    """Explicit trust zones demarcating boundary surfaces in Waypoint OS."""
    PUBLIC_UNTRUSTED = "PUBLIC_UNTRUSTED"        # Inbound webhooks, public landing pages, public itinerary checker
    CLIENT_DELEGATED = "CLIENT_DELEGATED"        # Authenticated travelers with scoped capability tokens
    AGENCY_INTERNAL = "AGENCY_INTERNAL"          # Authenticated agency agents, managers, and agency owners
    EXTERNAL_SUPPLIER = "EXTERNAL_SUPPLIER"      # Outbound NDC/GDS APIs, hotel suppliers, payment gateways
    AUTONOMOUS_AGENT = "AUTONOMOUS_AGENT"        # AI agent background workers and optimization tasks


class AuthorityTier(str, Enum):
    """5-Tier Human-AI Authority Matrix governing system actions."""
    TIER_0_AUTONOMOUS = "TIER_0_AUTONOMOUS"              # Deterministic check / draft generation (AI autonomous)
    TIER_1_RECOMMENDATION = "TIER_1_RECOMMENDATION"      # AI proposes; operator reviews before presentation
    TIER_2_OPERATOR_SIGNOFF = "TIER_2_OPERATOR_SIGNOFF"  # Operator must explicitly sign off before supplier/client action
    TIER_3_CLIENT_AUTHORIZATION = "TIER_3_CLIENT_AUTHORIZATION"  # Traveler must explicitly sign / authorize payment
    TIER_4_DUAL_CONTROL = "TIER_4_DUAL_CONTROL"          # Consequential actions requiring dual human approval


class CapabilityScope(str, Enum):
    """Granular permissions granted to delegated tokens and service callers."""
    VIEW_ONLY = "VIEW_ONLY"                    # Read proposal / itinerary details
    PROPOSE_EDIT = "PROPOSE_EDIT"              # Suggest changes or leave notes on draft
    ACCEPT_QUOTE = "ACCEPT_QUOTE"              # Legally sign off and accept proposal terms
    AUTHORIZE_PAYMENT = "AUTHORIZE_PAYMENT"    # Authorize deposit / full balance payment
    OVERRIDE_SUPPLIER = "OVERRIDE_SUPPLIER"    # Manual rate override or supplier swap
    ISSUE_REFUND = "ISSUE_REFUND"              # Initiate commercial refund or credit memo


@dataclass(slots=True)
class BoundaryContract:
    """Formal interface contract governing transitions between trust zones."""
    contract_id: str
    source_zone: TrustZone
    destination_zone: TrustZone
    required_scopes: list[CapabilityScope] = field(default_factory=list)
    authority_tier: AuthorityTier = AuthorityTier.TIER_0_AUTONOMOUS
    sanitization_required: bool = True
    audit_event_type: str = "boundary_crossing_evaluated"


@dataclass(slots=True)
class ScopedCapabilityToken:
    """Cryptographically signed capability token binding a traveler/client to specific actions."""
    token_id: str
    token_string: str
    trip_id: str
    agency_id: str
    traveler_id: Optional[str] = None
    traveler_role: str = "primary_booker"  # primary_booker | companion | guest
    allowed_scopes: list[CapabilityScope] = field(default_factory=list)
    expires_at: str = ""
    revoked: bool = False
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
