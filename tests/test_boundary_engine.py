"""
tests/test_boundary_engine.py — Unit tests for PER-0933 / PER-0927 Boundary Engine & Authority Matrix.
"""

from datetime import datetime, timedelta, timezone
from src.schemas.boundary_contracts import (
    AuthorityTier,
    CapabilityScope,
)
from src.services.boundary_engine import (
    AuthorityGateKeeper,
    BoundaryEngine,
)


def test_issue_and_verify_capability_token():
    """Verify issuing a signed HMAC capability token and verifying its validity and scopes."""
    engine = BoundaryEngine(secret_key="test_boundary_key_123")

    token_obj = engine.issue_token(
        trip_id="trip_tok_001",
        agency_id="agency_alpha",
        scopes=[CapabilityScope.VIEW_ONLY, CapabilityScope.PROPOSE_EDIT],
        traveler_id="trav_991",
        traveler_role="companion",
        ttl_hours=24,
    )

    assert token_obj.token_id.startswith("cap_")
    assert len(token_obj.token_string.split(".")) == 3

    # Verify without scope filter
    is_valid, verified, msg = engine.verify_token(token_obj.token_string)
    assert is_valid is True
    assert verified.trip_id == "trip_tok_001"
    assert verified.agency_id == "agency_alpha"
    assert verified.traveler_role == "companion"
    assert CapabilityScope.VIEW_ONLY in verified.allowed_scopes
    assert CapabilityScope.PROPOSE_EDIT in verified.allowed_scopes

    # Verify with matching scope filter
    is_valid_view, _, _ = engine.verify_token(token_obj.token_string, required_scope=CapabilityScope.VIEW_ONLY)
    assert is_valid_view is True

    # Verify with disallowed scope filter
    is_valid_pay, _, msg_pay = engine.verify_token(token_obj.token_string, required_scope=CapabilityScope.AUTHORIZE_PAYMENT)
    assert is_valid_pay is False
    assert "lacks required scope" in msg_pay


def test_verify_token_tampered_signature():
    """Verify that altering token payload or signature fails validation."""
    engine = BoundaryEngine(secret_key="test_boundary_key_123")
    token_obj = engine.issue_token(
        trip_id="trip_tok_002",
        agency_id="agency_alpha",
        scopes=[CapabilityScope.VIEW_ONLY],
    )

    parts = token_obj.token_string.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.bad_signature_here"

    is_valid, _, msg = engine.verify_token(tampered_token)
    assert is_valid is False
    assert "Invalid cryptographic signature" in msg


def test_verify_token_expiration():
    """Verify expired capability tokens are rejected."""
    engine = BoundaryEngine(secret_key="test_boundary_key_123")
    token_obj = engine.issue_token(
        trip_id="trip_tok_003",
        agency_id="agency_alpha",
        scopes=[CapabilityScope.VIEW_ONLY],
    )

    # Force expiration in past
    past = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    token_obj.expires_at = past

    is_valid, _, msg = engine.verify_token(token_obj.token_string)
    assert is_valid is False
    assert "Token has expired" in msg


def test_revoke_token():
    """Verify explicit token revocation."""
    engine = BoundaryEngine(secret_key="test_boundary_key_123")
    token_obj = engine.issue_token(
        trip_id="trip_tok_004",
        agency_id="agency_alpha",
        scopes=[CapabilityScope.ACCEPT_QUOTE],
    )

    is_valid, _, _ = engine.verify_token(token_obj.token_string)
    assert is_valid is True

    # Revoke
    revoked = engine.revoke_token(token_obj.token_id)
    assert revoked is True

    is_valid_after, _, msg = engine.verify_token(token_obj.token_string)
    assert is_valid_after is False
    assert "Token has been revoked" in msg


def test_authority_gatekeeper_evaluation():
    """Verify Human-AI Authority Matrix enforcement across tiers."""
    # Tier 0: Autonomous draft generation
    allowed_t0, tier_t0, _ = AuthorityGateKeeper.evaluate_action_authority(
        action_name="generate_draft_itinerary",
        actor_role="agent",
    )
    assert allowed_t0 is True
    assert tier_t0 == AuthorityTier.TIER_0_AUTONOMOUS

    # Tier 2: Operator sign-off for client dispatch (agent not allowed, operator allowed)
    disallowed_t2, tier_t2, _ = AuthorityGateKeeper.evaluate_action_authority(
        action_name="dispatch_proposal_to_client",
        actor_role="agent",
    )
    assert disallowed_t2 is False
    assert tier_t2 == AuthorityTier.TIER_2_OPERATOR_SIGNOFF

    allowed_t2, _, _ = AuthorityGateKeeper.evaluate_action_authority(
        action_name="dispatch_proposal_to_client",
        actor_role="operator",
    )
    assert allowed_t2 is True

    # Tier 4: Dual control for high-value refund (requires distinct secondary manager)
    single_t4, tier_t4, msg_t4 = AuthorityGateKeeper.evaluate_action_authority(
        action_name="issue_refund_above_threshold",
        actor_role="admin",
        dual_approver_role=None,
    )
    assert single_t4 is False
    assert tier_t4 == AuthorityTier.TIER_4_DUAL_CONTROL
    assert "Dual Control" in msg_t4

    dual_t4, _, _ = AuthorityGateKeeper.evaluate_action_authority(
        action_name="issue_refund_above_threshold",
        actor_role="admin",
        dual_approver_role="owner",
    )
    assert dual_t4 is True
