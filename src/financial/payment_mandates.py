"""
src/financial/payment_mandates.py — Customer Payment Authorization Mandate Ledger (Finding F-04).

Provides audit-proof payment mandate records for split deposits, card-on-file holds, and ACH debits.
Enforces explicit consent artifacts, maximum authorization caps, cryptographic consent digests, and SLA expiration.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional


class MandateStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class MandatePurpose(str, Enum):
    INITIAL_DEPOSIT = "INITIAL_DEPOSIT"
    SPLIT_INSTALLMENT = "SPLIT_INSTALLMENT"
    FINAL_BALANCE = "FINAL_BALANCE"
    SUPPLIER_INCIDENTAL_HOLD = "SUPPLIER_INCIDENTAL_HOLD"


@dataclass(slots=True)
class PaymentMandateRecord:
    mandate_id: str
    trip_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    max_authorized_cents: int
    currency: str
    purpose: MandatePurpose
    consent_text: str
    consent_sha256: str
    client_ip_address: str
    signed_at: str
    expires_at: str
    status: MandateStatus = MandateStatus.ACTIVE
    consumed_amount_cents: int = 0
    revocation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mandate_id": self.mandate_id,
            "trip_id": self.trip_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "max_authorized_cents": self.max_authorized_cents,
            "currency": self.currency,
            "purpose": self.purpose.value,
            "consent_sha256": self.consent_sha256,
            "client_ip_address": self.client_ip_address,
            "signed_at": self.signed_at,
            "expires_at": self.expires_at,
            "status": self.status.value,
            "consumed_amount_cents": self.consumed_amount_cents,
            "revocation_reason": self.revocation_reason,
        }


class PaymentMandateEngine:
    """
    Manages payment consent authorization mandates and enforces authorization bounds.
    """

    _MANDATE_STORE: Dict[str, PaymentMandateRecord] = {}

    @classmethod
    def register_mandate(
        cls,
        trip_id: str,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        max_authorized_cents: int,
        purpose: MandatePurpose,
        consent_text: str,
        client_ip_address: str = "127.0.0.1",
        currency: str = "USD",
        validity_days: int = 60,
    ) -> PaymentMandateRecord:
        mandate_id = f"MAN-{uuid.uuid4().hex[:10].upper()}"
        now_dt = datetime.now(timezone.utc)
        exp_dt = now_dt + timedelta(days=validity_days)

        consent_digest = hashlib.sha256(consent_text.encode("utf-8")).hexdigest()

        record = PaymentMandateRecord(
            mandate_id=mandate_id,
            trip_id=trip_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            max_authorized_cents=max_authorized_cents,
            currency=currency.upper(),
            purpose=purpose,
            consent_text=consent_text,
            consent_sha256=consent_digest,
            client_ip_address=client_ip_address,
            signed_at=now_dt.isoformat(),
            expires_at=exp_dt.isoformat(),
            status=MandateStatus.ACTIVE,
        )

        cls._MANDATE_STORE[mandate_id] = record
        return record

    @classmethod
    def verify_and_charge(
        cls,
        mandate_id: str,
        charge_amount_cents: int,
    ) -> Dict[str, Any]:
        """Validates that requested charge is compliant with authorized mandate terms."""
        mandate = cls._MANDATE_STORE.get(mandate_id)
        if not mandate:
            return {"authorized": False, "reason": "Mandate not found in ledger"}

        now = datetime.now(timezone.utc)
        exp = datetime.fromisoformat(mandate.expires_at)
        if now > exp:
            mandate.status = MandateStatus.EXPIRED
            return {"authorized": False, "reason": "Payment mandate has expired"}

        if mandate.status != MandateStatus.ACTIVE:
            return {"authorized": False, "reason": f"Mandate is in {mandate.status.value} status"}

        remaining_authorized = mandate.max_authorized_cents - mandate.consumed_amount_cents
        if charge_amount_cents > remaining_authorized:
            return {
                "authorized": False,
                "reason": f"Charge of {charge_amount_cents} cents exceeds remaining mandate authorization of {remaining_authorized} cents",
            }

        # Apply charge against mandate
        mandate.consumed_amount_cents += charge_amount_cents
        if mandate.consumed_amount_cents >= mandate.max_authorized_cents:
            mandate.status = MandateStatus.CONSUMED

        return {
            "authorized": True,
            "mandate_id": mandate_id,
            "charged_cents": charge_amount_cents,
            "remaining_authorized_cents": mandate.max_authorized_cents - mandate.consumed_amount_cents,
            "consent_sha256": mandate.consent_sha256,
            "status": mandate.status.value,
        }

    @classmethod
    def revoke_mandate(cls, mandate_id: str, reason: str) -> bool:
        mandate = cls._MANDATE_STORE.get(mandate_id)
        if not mandate:
            return False
        mandate.status = MandateStatus.REVOKED
        mandate.revocation_reason = reason
        return True

    @classmethod
    def get_mandate(cls, mandate_id: str) -> Optional[PaymentMandateRecord]:
        return cls._MANDATE_STORE.get(mandate_id)
