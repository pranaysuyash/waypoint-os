"""
src/services/boundary_engine.py — Boundary contracts, HMAC capability tokens, and Human-AI Authority enforcement.

Grounding doctrine:
- PER-0933 (Boundary Systems Architect): Boundary contracts, cryptographic token delegation.
- PER-0927 (Human-AI Authority Architect): Authority tier validation and dual-control signoffs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from src.schemas.boundary_contracts import (
    AuthorityTier,
    BoundaryContract,
    CapabilityScope,
    ScopedCapabilityToken,
    TrustZone,
)

logger = logging.getLogger("waypoint.boundaries")

# ---------------------------------------------------------------------------
# PA-24: CAPABILITY_TOKEN_SECRET is required — no committed fallback.
# Mirrors spine_api/routers/public_proposals.py `_require_signing_key`
# (PT-01): a hardcoded default would let anyone forge scoped capability
# tokens on any deployment that forgot to set the env var. Fail loudly at
# first construction (startup/first use) instead.
# ---------------------------------------------------------------------------
_KNOWN_SECRET_PLACEHOLDERS = frozenset(
    {
        "waypoint_capability_secret_key_2026",
        "change-me-to-a-random-secret",
        "secret",
        "changeme",
        "password",
        "default",
        "test",
        "dev",
    }
)


def _require_capability_secret() -> str:
    value = (os.environ.get("CAPABILITY_TOKEN_SECRET") or "").strip()
    if not value:
        raise RuntimeError(
            "CAPABILITY_TOKEN_SECRET is not set. Boundary-engine capability "
            "tokens are signed with this secret, so shipping a default would "
            "let anyone forge tokens for arbitrary trips. Provide it via the "
            "environment or .env (see .env.example)."
        )
    if value.lower() in _KNOWN_SECRET_PLACEHOLDERS or len(value) < 32:
        raise RuntimeError(
            "CAPABILITY_TOKEN_SECRET is too weak or is a known placeholder. "
            "Use a randomly generated secret of at least 32 characters."
        )
    return value


class BoundaryEngine:
    """Singleton service managing capability token issuance, validation, and boundary contracts."""

    _instance: Optional[BoundaryEngine] = None

    def __init__(self, secret_key: Optional[str] = None) -> None:
        # PA-24: fail closed when neither an explicit key nor the env var is
        # provided. Callers that pass an explicit secret (tests, seeded
        # services) keep working; the process-wide default is env-only.
        self.secret_key = secret_key or _require_capability_secret()
        self._tokens: dict[str, ScopedCapabilityToken] = {}
        self._contracts: list[BoundaryContract] = []
        self._bootstrap_standard_contracts()

    @classmethod
    def get_instance(cls) -> BoundaryEngine:
        """Accessor for process-wide boundary engine."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _bootstrap_standard_contracts(self) -> None:
        """Register canonical boundary contracts between trust zones."""
        self._contracts = [
            BoundaryContract(
                contract_id="bc_public_to_internal",
                source_zone=TrustZone.PUBLIC_UNTRUSTED,
                destination_zone=TrustZone.AGENCY_INTERNAL,
                required_scopes=[],
                authority_tier=AuthorityTier.TIER_0_AUTONOMOUS,
                sanitization_required=True,
                audit_event_type="inbound_untrusted_intake_sanitized",
            ),
            BoundaryContract(
                contract_id="bc_client_to_proposal",
                source_zone=TrustZone.CLIENT_DELEGATED,
                destination_zone=TrustZone.AGENCY_INTERNAL,
                required_scopes=[CapabilityScope.VIEW_ONLY],
                authority_tier=AuthorityTier.TIER_0_AUTONOMOUS,
                sanitization_required=True,
                audit_event_type="client_proposal_viewed",
            ),
            BoundaryContract(
                contract_id="bc_client_accept_quote",
                source_zone=TrustZone.CLIENT_DELEGATED,
                destination_zone=TrustZone.AGENCY_INTERNAL,
                required_scopes=[CapabilityScope.ACCEPT_QUOTE],
                authority_tier=AuthorityTier.TIER_3_CLIENT_AUTHORIZATION,
                sanitization_required=True,
                audit_event_type="client_quote_accepted",
            ),
            BoundaryContract(
                contract_id="bc_client_payment",
                source_zone=TrustZone.CLIENT_DELEGATED,
                destination_zone=TrustZone.EXTERNAL_SUPPLIER,
                required_scopes=[CapabilityScope.AUTHORIZE_PAYMENT],
                authority_tier=AuthorityTier.TIER_3_CLIENT_AUTHORIZATION,
                sanitization_required=True,
                audit_event_type="client_payment_authorized",
            ),
            BoundaryContract(
                contract_id="bc_operator_refund_dual",
                source_zone=TrustZone.AGENCY_INTERNAL,
                destination_zone=TrustZone.EXTERNAL_SUPPLIER,
                required_scopes=[CapabilityScope.ISSUE_REFUND],
                authority_tier=AuthorityTier.TIER_4_DUAL_CONTROL,
                sanitization_required=False,
                audit_event_type="operator_refund_dual_signoff",
            ),
        ]

    def _sign_payload(self, payload_bytes: bytes) -> str:
        """Generate SHA-256 HMAC signature for a payload string."""
        return hmac.new(
            self.secret_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def issue_token(
        self,
        trip_id: str,
        agency_id: str,
        scopes: list[CapabilityScope],
        traveler_id: Optional[str] = None,
        traveler_role: str = "primary_booker",
        ttl_hours: int = 72,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ScopedCapabilityToken:
        """Issue a cryptographically signed, scoped capability token for client/companion access."""
        token_id = f"cap_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=ttl_hours)).isoformat()

        payload = {
            "token_id": token_id,
            "trip_id": trip_id,
            "agency_id": agency_id,
            "traveler_id": traveler_id,
            "traveler_role": traveler_role,
            "scopes": [s.value for s in scopes],
            "expires_at": expires_at,
            "issued_at": now.isoformat(),
        }

        raw_json = json.dumps(payload, sort_keys=True)
        b64_payload = base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("utf-8")
        signature = self._sign_payload(raw_json.encode("utf-8"))
        token_string = f"{token_id}.{b64_payload}.{signature}"

        token_obj = ScopedCapabilityToken(
            token_id=token_id,
            token_string=token_string,
            trip_id=trip_id,
            agency_id=agency_id,
            traveler_id=traveler_id,
            traveler_role=traveler_role,
            allowed_scopes=scopes,
            expires_at=expires_at,
            revoked=False,
            issued_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._tokens[token_id] = token_obj
        logger.info("BoundaryEngine: Issued capability token %s with scopes %s for trip %s", token_id, [s.value for s in scopes], trip_id)
        return token_obj

    def verify_token(
        self,
        token_string: str,
        required_scope: Optional[CapabilityScope] = None,
    ) -> tuple[bool, Optional[ScopedCapabilityToken], str]:
        """Verify token authenticity, expiration, revocation status, and scope permissions."""
        parts = token_string.strip().split(".")
        if len(parts) != 3:
            return False, None, "Malformed token structure"

        token_id, b64_payload, signature = parts

        try:
            raw_json = base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8")
            payload = json.loads(raw_json)
        except Exception:
            return False, None, "Invalid base64 payload"

        expected_sig = self._sign_payload(raw_json.encode("utf-8"))
        if not hmac.compare_digest(signature, expected_sig):
            return False, None, "Invalid cryptographic signature"

        # Check in-memory token store if available
        token_obj = self._tokens.get(token_id)
        if token_obj is None:
            # Reconstruct from verified payload
            token_obj = ScopedCapabilityToken(
                token_id=token_id,
                token_string=token_string,
                trip_id=payload["trip_id"],
                agency_id=payload["agency_id"],
                traveler_id=payload.get("traveler_id"),
                traveler_role=payload.get("traveler_role", "primary_booker"),
                allowed_scopes=[CapabilityScope(s) for s in payload.get("scopes", [])],
                expires_at=payload.get("expires_at", ""),
                revoked=False,
                issued_at=payload.get("issued_at", ""),
            )

        if token_obj.revoked:
            return False, token_obj, "Token has been revoked"

        # Check expiration
        if token_obj.expires_at:
            try:
                exp_dt = datetime.fromisoformat(token_obj.expires_at)
                if datetime.now(timezone.utc) > exp_dt:
                    return False, token_obj, "Token has expired"
            except ValueError:
                return False, token_obj, "Invalid expiration timestamp"

        # Check required scope permission
        if required_scope is not None and required_scope not in token_obj.allowed_scopes:
            return False, token_obj, f"Token lacks required scope: {required_scope.value}"

        return True, token_obj, "Token valid"

    def revoke_token(self, token_id_or_string: str) -> bool:
        """Mark a capability token as revoked."""
        token_id = token_id_or_string.split(".")[0] if "." in token_id_or_string else token_id_or_string
        if token_id in self._tokens:
            self._tokens[token_id].revoked = True
            logger.info("BoundaryEngine: Token %s successfully revoked", token_id)
            return True
        return False

    def list_contracts(self) -> list[BoundaryContract]:
        """List registered boundary contracts."""
        return list(self._contracts)


class AuthorityGateKeeper:
    """Evaluator for the 5-Tier Human-AI Authority Matrix."""

    AUTHORITY_CATALOG: dict[str, dict[str, Any]] = {
        "generate_draft_itinerary": {
            "tier": AuthorityTier.TIER_0_AUTONOMOUS,
            "description": "AI agent parses intake and synthesizes initial draft options.",
            "allowed_roles": ["agent", "supervisor", "operator"],
        },
        "evaluate_constraints": {
            "tier": AuthorityTier.TIER_0_AUTONOMOUS,
            "description": "Deterministic spatial-temporal and regulatory feasibility check.",
            "allowed_roles": ["agent", "supervisor", "operator"],
        },
        "propose_quote_discount": {
            "tier": AuthorityTier.TIER_1_RECOMMENDATION,
            "description": "AI suggests pricing / yield arbitrage discount for human review.",
            "allowed_roles": ["operator", "admin", "agent"],
        },
        "dispatch_proposal_to_client": {
            "tier": AuthorityTier.TIER_2_OPERATOR_SIGNOFF,
            "description": "Operator reviews and dispatches binding itinerary quote to traveler.",
            "allowed_roles": ["operator", "admin", "owner"],
        },
        "commit_supplier_price_lock": {
            "tier": AuthorityTier.TIER_2_OPERATOR_SIGNOFF,
            "description": "Commits non-refundable inventory hold with supplier.",
            "allowed_roles": ["operator", "admin", "owner"],
        },
        "accept_travel_agreement": {
            "tier": AuthorityTier.TIER_3_CLIENT_AUTHORIZATION,
            "description": "Traveler accepts terms, conditions, and cancellation policies.",
            "allowed_roles": ["client", "primary_booker"],
        },
        "authorize_credit_card_charge": {
            "tier": AuthorityTier.TIER_3_CLIENT_AUTHORIZATION,
            "description": "Traveler provides payment capture authorization.",
            "allowed_roles": ["client", "primary_booker"],
        },
        "issue_refund_above_threshold": {
            "tier": AuthorityTier.TIER_4_DUAL_CONTROL,
            "description": "Commercial refund > $5,000 requiring dual managerial sign-off.",
            "allowed_roles": ["admin", "owner"],
            "requires_dual_approval": True,
        },
        "override_safety_restriction": {
            "tier": AuthorityTier.TIER_4_DUAL_CONTROL,
            "description": "Overriding regulatory visa/passport minimum safety warnings.",
            "allowed_roles": ["owner"],
            "requires_dual_approval": True,
        },
    }

    @classmethod
    def evaluate_action_authority(
        cls,
        action_name: str,
        actor_role: str,
        dual_approver_role: Optional[str] = None,
    ) -> tuple[bool, AuthorityTier, str]:
        """Evaluate if an action is permitted under the Human-AI Authority Matrix."""
        spec = cls.AUTHORITY_CATALOG.get(action_name)
        if spec is None:
            return False, AuthorityTier.TIER_2_OPERATOR_SIGNOFF, f"Unknown action: '{action_name}'"

        tier: AuthorityTier = spec["tier"]
        allowed_roles: list[str] = spec["allowed_roles"]

        if actor_role not in allowed_roles:
            return False, tier, f"Actor role '{actor_role}' not permitted for {action_name} (requires one of {allowed_roles})"

        if spec.get("requires_dual_approval", False):
            if not dual_approver_role:
                return False, tier, f"Action {action_name} requires Tier 4 Dual Control approval"
            if dual_approver_role not in allowed_roles or dual_approver_role == actor_role:
                return False, tier, "Secondary approver must be an authorized distinct manager"

        return True, tier, f"Action permitted under {tier.value}"

    @classmethod
    def get_authority_catalog(cls) -> dict[str, Any]:
        """Return the complete Human-AI Authority Catalog."""
        return {
            action: {
                "tier": data["tier"].value,
                "description": data["description"],
                "allowed_roles": data["allowed_roles"],
                "requires_dual_approval": data.get("requires_dual_approval", False),
            }
            for action, data in cls.AUTHORITY_CATALOG.items()
        }
