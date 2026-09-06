"""
src/security/retention_enforcer.py — Retention/erasure contract prototype (Finding F-05).

IMPORTANT RUNTIME BOUNDARY
--------------------------
This module is a shadow, in-process registry used by tests and experiments. It
does *not* enforce retention in a running product and it does not erase data
from TripStore, BookingDocument storage, MemoryStore, audit persistence, or an
external provider. ``execute_erasure`` only marks a registry object and emits
an in-memory certificate-shaped record. The certificate is not proof that any
backing data was deleted.

The category schedules and certificate shape are retained as a design probe.
They must not be described as GDPR/DPDP enforcement until a canonical,
tenant-scoped, durable deletion workflow covers every data store and has an
operator-controlled audit, retry, reconciliation, and recovery contract.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional


class RetentionCategory(str, Enum):
    PASSPORT_MRZ = "PASSPORT_MRZ"                # SLA: 30 days post trip completion
    PAYMENT_TOKEN = "PAYMENT_TOKEN"              # SLA: 120 days post settlement (chargeback window)
    COMMUNICATION_LOGS = "COMMUNICATION_LOGS"    # SLA: 180 days post inquiry
    FINANCIAL_INVOICE = "FINANCIAL_INVOICE"      # SLA: 2555 days (7 years statutory tax compliance)


@dataclass(slots=True)
class RetainedDataAsset:
    asset_id: str
    trip_id: str
    customer_id: str
    category: RetentionCategory
    created_at_iso: str
    sla_days: int
    is_erased: bool = False
    erasure_certificate_id: Optional[str] = None


@dataclass(slots=True)
class ErasureCertificate:
    certificate_id: str
    asset_id: str
    category: RetentionCategory
    erased_at_iso: str
    tombstone_sha256: str
    reason: str


class RetentionEnforcer:
    """
    Evaluates a retention prototype over an in-memory registry.

    ``RUNTIME_STATUS`` is deliberately explicit so callers and documentation
    tooling cannot mistake this class for a live compliance control. A future
    production implementation must replace this registry with a durable
    workflow rather than silently extending these class-level dictionaries.
    """

    RUNTIME_STATUS = "shadow"
    EXTERNAL_ERASURE_ENABLED = False

    DEFAULT_SLA_DAYS: Dict[RetentionCategory, int] = {
        RetentionCategory.PASSPORT_MRZ: 30,
        RetentionCategory.PAYMENT_TOKEN: 120,
        RetentionCategory.COMMUNICATION_LOGS: 180,
        RetentionCategory.FINANCIAL_INVOICE: 2555,
    }

    _ASSET_REGISTRY: Dict[str, RetainedDataAsset] = {}
    _CERTIFICATE_STORE: Dict[str, ErasureCertificate] = {}

    @classmethod
    def register_asset(
        cls,
        asset_id: str,
        trip_id: str,
        customer_id: str,
        category: RetentionCategory,
        created_at_iso: Optional[str] = None,
        custom_sla_days: Optional[int] = None,
    ) -> RetainedDataAsset:
        sla = custom_sla_days or cls.DEFAULT_SLA_DAYS[category]
        created = created_at_iso or datetime.now(timezone.utc).isoformat()
        asset = RetainedDataAsset(
            asset_id=asset_id,
            trip_id=trip_id,
            customer_id=customer_id,
            category=category,
            created_at_iso=created,
            sla_days=sla,
        )
        cls._ASSET_REGISTRY[asset_id] = asset
        return asset

    @classmethod
    def sweep_and_enforce_erasure(
        cls,
        now_dt: Optional[datetime] = None,
    ) -> List[ErasureCertificate]:
        """Mark expired registry assets and return prototype certificates.

        This does not purge any backing store. The expiry schedule is a
        design-probe convention until a versioned, jurisdiction-approved
        policy supplies the correct lifecycle anchor and legal hold rules.
        """
        now = now_dt or datetime.now(timezone.utc)
        certificates: List[ErasureCertificate] = []

        for asset_id, asset in list(cls._ASSET_REGISTRY.items()):
            if asset.is_erased:
                continue

            created = datetime.fromisoformat(asset.created_at_iso.replace("Z", "+00:00"))
            exp_date = created + timedelta(days=asset.sla_days)

            if now >= exp_date:
                cert = cls.execute_erasure(
                    asset_id=asset_id,
                    reason=f"Statutory {asset.category.value} retention SLA ({asset.sla_days} days) elapsed.",
                    now_dt=now,
                )
                certificates.append(cert)

        return certificates

    @classmethod
    def execute_erasure(
        cls,
        asset_id: str,
        reason: str = "Customer Right-to-Erasure Request (GDPR Art 17)",
        now_dt: Optional[datetime] = None,
    ) -> ErasureCertificate:
        """Mark one registry asset and issue a prototype certificate record.

        No external or durable data is erased by this method.
        """
        asset = cls._ASSET_REGISTRY.get(asset_id)
        if not asset:
            raise KeyError(f"Asset {asset_id} not found in retention registry")

        now_iso = (now_dt or datetime.now(timezone.utc)).isoformat()
        cert_id = f"CERT-ERASE-{uuid.uuid4().hex[:8].upper()}"

        tombstone_raw = f"{asset.asset_id}:{asset.category.value}:{now_iso}:{reason}"
        tombstone_hash = hashlib.sha256(tombstone_raw.encode("utf-8")).hexdigest()

        cert = ErasureCertificate(
            certificate_id=cert_id,
            asset_id=asset.asset_id,
            category=asset.category,
            erased_at_iso=now_iso,
            tombstone_sha256=tombstone_hash,
            reason=reason,
        )

        asset.is_erased = True
        asset.erasure_certificate_id = cert_id
        cls._CERTIFICATE_STORE[cert_id] = cert
        return cert

    @classmethod
    def get_certificate(cls, certificate_id: str) -> Optional[ErasureCertificate]:
        return cls._CERTIFICATE_STORE.get(certificate_id)
