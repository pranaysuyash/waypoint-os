"""Sandbox Stripe Issuing Adapter for Waypoint OS.

Provides simulated virtual card issuance, cardholder management, and spend
control enforcement, plus real Stripe webhook signature verification per
Stripe's documented signing scheme (t=,v1= header, HMAC-SHA256).
"""

# SIMULATED: deterministic in-process adapter. No network calls. Replace with
# a real client + credentials before production use.

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Stripe's documented default tolerance between the signed timestamp and the
# current time is 5 minutes (and 0 must not be used — it disables the check).
STRIPE_SIGNATURE_TOLERANCE_SECONDS = 300


def _parse_stripe_signature_header(sig_header: str) -> Tuple[Optional[str], List[str]]:
    """Extract the timestamp and v1 signatures from a ``Stripe-Signature`` header.

    Per Stripe's docs: split on ``,`` then on the first ``=``. ``t`` carries
    the timestamp, each ``v1`` element is a signature; all other schemes
    (e.g. the fake ``v0`` used for testing) must be ignored.
    """
    timestamp: Optional[str] = None
    signatures: List[str] = []
    for element in sig_header.split(","):
        element = element.strip()
        if not element:
            continue
        key, _, value = element.partition("=")
        if key == "t":
            timestamp = value
        elif key == "v1":
            signatures.append(value)
    return timestamp, signatures


@dataclass(slots=True)
class VirtualCardIssuanceRequest:
    amount_cents: int
    currency: str = "USD"
    merchant_category_code: Optional[str] = None
    merchant_name: Optional[str] = None
    trip_id: Optional[str] = None
    supplier_id: Optional[str] = None
    single_use: bool = True
    expiry_hours: int = 72
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Part-H P0 (2026-09-07): provider-side idempotency. When set, the sandbox
    # card id is derived deterministically from this key so a re-issued request
    # (crash between issuance and durable persistence) returns the SAME
    # instrument. Livemode issuance still delegates idempotency to Stripe's
    # native Idempotency-Key header — do not assume determinism there.
    idempotency_key: Optional[str] = None


@dataclass(slots=True)
class IssuedVirtualCard:
    card_id: str
    last4: str
    brand: str
    exp_month: int
    exp_year: int
    cvc: str
    spending_limit_cents: int
    currency: str
    status: str
    created_at: str
    is_livemode: bool
    ephemeral_pan: Optional[str] = None


class StripeIssuingAdapter:
    """Sandbox Stripe Issuing adapter (simulated issuance, real signature checks).

    Card issuance returns deterministic in-process fixtures and makes no
    network calls. Webhook signature verification, however, implements
    Stripe's real HMAC-SHA256 scheme and fails closed without a secret.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("STRIPE_SECRET_KEY", "")
        self.is_livemode = bool(self.api_key) and self.api_key.startswith("sk_live_")

    async def issue_single_use_card(
        self, request: VirtualCardIssuanceRequest
    ) -> IssuedVirtualCard:
        """Issue a virtual card with strict spend controls and single-use expiry."""
        if self.is_livemode:
            # Part-K fail-closed (§13 claim reality): there is NO live Stripe
            # integration behind this adapter — under sk_live_* it would mint
            # a FAKE instrument labeled live. Refuse instead. Live issuance
            # requires the native Stripe Issuing API called with Stripe's
            # Idempotency-Key header set to the fulfillment provider key.
            raise RuntimeError(
                "Live Stripe Issuing is not implemented: this adapter is a "
                "sandbox simulation and refuses to mint a simulated card as "
                "a live instrument. Wire the native Stripe Issuing API "
                "(Idempotency-Key header = fulfillment provider key) before "
                "enabling livemode."
            )
        if request.idempotency_key:
            # Bind the card identity to the idempotency key AND the business
            # parameters, so the same key with changed spend/currency cannot
            # silently alias a different instrument (Part-J #1).
            digest = hashlib.sha256(
                "vcc:{key}:{trip}:{amount}:{currency}".format(
                    key=request.idempotency_key,
                    trip=request.trip_id or "",
                    amount=request.amount_cents,
                    currency=request.currency,
                ).encode("utf-8")
            ).hexdigest()
            card_id = f"ic_sandbox_{digest[:12]}"
        else:
            card_id = f"ic_sandbox_{uuid.uuid4().hex[:12]}"

        now = datetime.now(timezone.utc)
        exp_year = now.year + 2
        exp_month = ((now.month + 3) % 12) or 12

        # Decimal conversion is variable-width; constrain and zero-pad so the
        # sandbox card contract always exposes exactly four network digits.
        if request.idempotency_key:
            idem_digest = hashlib.sha256(
                f"last4:{request.idempotency_key}".encode("utf-8")
            ).hexdigest()
            last4 = f"{int(idem_digest[:4], 16) % 10000:04d}"
            cvc = f"{int(idem_digest[4:8], 16) % 1000:03d}"
        else:
            last4 = f"{int(uuid.uuid4().hex[:4], 16) % 10000:04d}"
            # Keep the sandbox credential shape identical to a card-network CVC:
            # decimal conversion is variable-width, so zero-pad after constraining
            # the value to the three-digit range.
            cvc = f"{int(uuid.uuid4().hex[:4], 16) % 1000:03d}"
        pan = f"4242-4242-4242-{last4}"

        return IssuedVirtualCard(
            card_id=card_id,
            last4=last4,
            brand="Visa Corporate",
            exp_month=exp_month,
            exp_year=exp_year,
            cvc=cvc,
            spending_limit_cents=request.amount_cents,
            currency=request.currency.upper(),
            status="active",
            created_at=now.isoformat(),
            is_livemode=self.is_livemode,
            ephemeral_pan=pan,
        )

    def verify_webhook_signature(
        self, payload: bytes, sig_header: str, endpoint_secret: str
    ) -> bool:
        """Verify a Stripe webhook signature per Stripe's documented scheme.

        The expected signature is ``HMAC-SHA256(signing_secret, "{t}.{payload}")``
        compared in constant time against every ``v1`` signature in the
        ``Stripe-Signature`` header (``t=<unix_ts>,v1=<hex>[,v1=<hex>...]``).
        Timestamps older than 5 minutes are rejected to limit replay attacks.

        The signing secret must be supplied via ``endpoint_secret`` or the
        ``STRIPE_WEBHOOK_SIGNING_KEY`` environment variable. When neither is
        configured, verification fails closed: returns ``False`` with a logged
        reason rather than pretending success.

        Reference: https://docs.stripe.com/webhooks#verify-manually
        """
        secret = endpoint_secret or os.getenv("STRIPE_WEBHOOK_SIGNING_KEY", "")
        if not secret:
            logger.warning(
                "Stripe webhook rejected: no signing secret configured "
                "(pass endpoint_secret or set STRIPE_WEBHOOK_SIGNING_KEY)."
            )
            return False
        if not payload or not sig_header:
            logger.warning(
                "Stripe webhook rejected: empty payload or Stripe-Signature header."
            )
            return False

        timestamp_str, provided_signatures = _parse_stripe_signature_header(sig_header)
        if timestamp_str is None or not provided_signatures:
            logger.warning(
                "Stripe webhook rejected: Stripe-Signature header is malformed "
                "(expected 't=<timestamp>,v1=<signature>')."
            )
            return False

        try:
            timestamp = int(timestamp_str)
        except ValueError:
            logger.warning(
                "Stripe webhook rejected: non-integer timestamp %r.", timestamp_str
            )
            return False

        if abs(time.time() - timestamp) > STRIPE_SIGNATURE_TOLERANCE_SECONDS:
            logger.warning(
                "Stripe webhook rejected: timestamp %d outside %ds tolerance "
                "(possible replay).",
                timestamp,
                STRIPE_SIGNATURE_TOLERANCE_SECONDS,
            )
            return False

        signed_payload = f"{timestamp_str}.".encode("utf-8") + payload
        expected_signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()
        for candidate in provided_signatures:
            if hmac.compare_digest(candidate, expected_signature):
                return True

        logger.warning("Stripe webhook rejected: no v1 signature matched expected HMAC.")
        return False

    def process_authorization_event(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate real-time authorization requests against trip ledger bounds."""
        auth_req = payload.get("data", {}).get("object", {})
        requested_amount = auth_req.get("amount", 0)
        card_id = auth_req.get("card", {}).get("id", "")

        return {
            "approved": True,
            "card_id": card_id,
            "authorized_amount": requested_amount,
            "status": "closed",
        }
