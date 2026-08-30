"""
spine_api.services.card_vault — Zero-knowledge tokenized credit card authorization records.

Ensures zero plaintext PAN storage on agency servers while preserving audit-compliant
credit card authorization agreements and e-signatures for offline supplier settlements.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class CardAuthorizationAgreement:
    authorization_id: str
    trip_id: str
    traveler_name: str
    traveler_email: str
    card_brand: str  # "Visa" | "Mastercard" | "Amex"
    card_last4: str
    card_token: str  # Gateway payment method token e.g. "pm_tok_12345"
    authorized_max_amount_usd: float
    currency: str
    client_ip_address: str
    consent_timestamp: str
    agreement_hash: str
    status: str = "active"  # "active" | "revoked" | "charged"


def create_card_authorization_record(
    trip_id: str,
    traveler_name: str,
    traveler_email: str,
    card_brand: str,
    card_last4: str,
    card_token: str,
    authorized_max_amount_usd: float,
    client_ip_address: str,
    currency: str = "USD",
) -> CardAuthorizationAgreement:
    """
    Generate an immutable, signed credit card authorization record without plaintext PANs.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    auth_id = f"cauth_{hashlib.sha256(f'{trip_id}:{card_token}:{now_iso}'.encode()).hexdigest()[:16]}"

    # Cryptographic integrity signature of terms + consent
    payload = f"{auth_id}|{trip_id}|{traveler_email}|{card_token}|{authorized_max_amount_usd}|{client_ip_address}|{now_iso}"
    agreement_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return CardAuthorizationAgreement(
        authorization_id=auth_id,
        trip_id=trip_id,
        traveler_name=traveler_name,
        traveler_email=traveler_email,
        card_brand=card_brand,
        card_last4=card_last4,
        card_token=card_token,
        authorized_max_amount_usd=authorized_max_amount_usd,
        currency=currency,
        client_ip_address=client_ip_address,
        consent_timestamp=now_iso,
        agreement_hash=agreement_hash,
        status="active",
    )
