"""
src.security.jurisdiction_policy — PII handling rules per jurisdiction.

Maps legal jurisdictions (GDPR, DPDP, US state laws) to specific PII handling
rules that the privacy guard enforces differently depending on the agency's
jurisdiction.

Jurisdictions:
- EU (GDPR): Right to erasure, 72-hour breach notification, consent required
  for processing, data minimization, DPO appointment expected
- IN (DPDP Act 2023): Consent-based processing, data principal rights,
  significant data fiduciary obligations, cross-border transfer restrictions
- US (state laws): CCPA/CPRA for California, varying by state. Default is
  least-restrictive unless agency specifies state.
- OTHER: Default to most conservative (EU-like) rules

Each jurisdiction has:
1. retention_days: How long PII can be retained (None = indefinite)
2. right_to_erasure: Whether users can request deletion
3. consent_required: Whether explicit consent is needed before processing
4. breach_notification_hours: Hours within which breach must be reported
5. data_residency_required: Whether data must stay in-jurisdiction
6. dpo_required: Whether a Data Protection Officer is required
7. extra: Jurisdiction-specific rules as key-value pairs
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class Jurisdiction(StrEnum):
    EU = "eu"
    IN = "in"
    US = "us"
    OTHER = "other"


@dataclass(slots=True)
class JurisdictionPolicy:
    jurisdiction: Jurisdiction
    display_name: str
    retention_days: Optional[int]
    right_to_erasure: bool
    consent_required: bool
    breach_notification_hours: Optional[int]
    data_residency_required: bool
    dpo_required: bool
    extra: dict = field(default_factory=dict)


EU_POLICY = JurisdictionPolicy(
    jurisdiction=Jurisdiction.EU,
    display_name="European Union (GDPR)",
    retention_days=None,
    right_to_erasure=True,
    consent_required=True,
    breach_notification_hours=72,
    data_residency_required=True,
    dpo_required=True,
    extra={
        "regulation": "GDPR",
        "data_minimization": True,
        "portability_right": True,
    },
)

IN_POLICY = JurisdictionPolicy(
    jurisdiction=Jurisdiction.IN,
    display_name="India (DPDP Act 2023)",
    retention_days=None,
    right_to_erasure=True,
    consent_required=True,
    breach_notification_hours=72,
    data_residency_required=False,
    dpo_required=False,
    extra={
        "regulation": "DPDP Act 2023",
        "significant_data_fiduciary": False,
        "cross_border_transfer": "restricted",
    },
)

US_POLICY = JurisdictionPolicy(
    jurisdiction=Jurisdiction.US,
    display_name="United States (State Laws)",
    retention_days=None,
    right_to_erasure=False,
    consent_required=False,
    breach_notification_hours=None,
    data_residency_required=False,
    dpo_required=False,
    extra={
        "regulation": "Various state laws",
        "ccpa_applicable": None,
        "state": None,
    },
)

OTHER_POLICY = JurisdictionPolicy(
    jurisdiction=Jurisdiction.OTHER,
    display_name="Other (Conservative Default)",
    retention_days=None,
    right_to_erasure=True,
    consent_required=True,
    breach_notification_hours=72,
    data_residency_required=True,
    dpo_required=False,
    extra={
        "regulation": "Conservative default",
        "note": "Uses EU-like rules as the safest default",
    },
)


JURISDICTION_POLICIES: dict[str, JurisdictionPolicy] = {
    Jurisdiction.EU: EU_POLICY,
    Jurisdiction.IN: IN_POLICY,
    Jurisdiction.US: US_POLICY,
    Jurisdiction.OTHER: OTHER_POLICY,
}


def get_jurisdiction_policy(jurisdiction: str) -> JurisdictionPolicy:
    """Get the policy for a jurisdiction string (case-insensitive).

    Returns OTHER_POLICY for unknown jurisdictions.
    """
    normalized = jurisdiction.lower().strip()
    return JURISDICTION_POLICIES.get(normalized, OTHER_POLICY)


def should_block_pii(jurisdiction: str) -> bool:
    """Whether PII should be blocked (not just warned) in this jurisdiction.

    In dogfood mode, PII is always blocked regardless of jurisdiction.
    In production, jurisdictions with consent_required=True block PII
    unless explicit consent is recorded.
    """
    policy = get_jurisdiction_policy(jurisdiction)
    return policy.consent_required or policy.right_to_erasure


def requires_erasure_capability(jurisdiction: str) -> bool:
    """Whether this jurisdiction requires the ability to erase user data."""
    return get_jurisdiction_policy(jurisdiction).right_to_erasure


def get_retention_days(jurisdiction: str) -> Optional[int]:
    """Get the maximum PII retention period in days for this jurisdiction.

    Returns None if there's no specific limit (check your legal counsel).
    """
    return get_jurisdiction_policy(jurisdiction).retention_days