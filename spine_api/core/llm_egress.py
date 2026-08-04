"""
spine_api/core/llm_egress.py — Single egress boundary for LLM provider calls.

All data sent to external LLM providers (OpenAI, Gemini, etc.) MUST pass through
this module. It enforces:

  1. Field allowlisting per decision type (extraction, classification, etc.)
  2. PII removal (emails, phones, passport numbers, credit cards)
  3. Prompt delimiters for untrusted customer content
  4. Audit logging of every egress event
  5. Hard-fail if egress policy is not defined for a decision type

Design rationale (motto_v4 §0.11, P0-7 from ChatGPT audit):
  A system handling traveler details cannot silently send PII to third-party
  model providers. Every LLM call must go through a defined egress policy.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("spine_api.core.llm_egress")


class DecisionType(str, Enum):
    """Types of LLM decisions that have defined egress policies."""
    EXTRACTION = "extraction"          # Document/text extraction
    CLASSIFICATION = "classification"  # Trip type classification
    GAP_ANALYSIS = "gap_analysis"      # Missing information detection
    SUMMARIZATION = "summarization"    # Trip summary generation
    SUGGESTION = "suggestion"          # Recommendation generation


@dataclass(slots=True)
class EgressPolicy:
    """Policy defining what data may be sent to an LLM for a specific decision type."""
    decision_type: DecisionType
    allowed_fields: Set[str]  # Fields from packet that may be sent
    strip_pii: bool = True
    add_delimiters: bool = True
    max_content_length: int = 50000  # Max chars sent to LLM
    require_audit: bool = True


# ─────────────────────────────────────────────────────────────
# PII Patterns (compiled once, reused)
# ─────────────────────────────────────────────────────────────

_EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)
_PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
)
_PASSPORT_PATTERN = re.compile(
    r'\b[A-Z]{1,2}\d{6,9}\b'
)
_CREDIT_CARD_PATTERN = re.compile(
    r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
)
_SSN_PATTERN = re.compile(
    r'\b\d{3}-\d{2}-\d{4}\b'
)
_AADHAAR_PATTERN = re.compile(
    r'\b\d{4}\s?\d{4}\s?\d{4}\b'
)
_PAN_PATTERN = re.compile(
    r'\b[A-Z]{5}\d{4}[A-Z]\b'
)

_PII_PATTERNS = [
    # Order matters: more specific patterns first to prevent false matches
    ("credit_card", _CREDIT_CARD_PATTERN, "[CARD_REDACTED]"),
    ("ssn", _SSN_PATTERN, "[SSN_REDACTED]"),
    ("email", _EMAIL_PATTERN, "[EMAIL_REDACTED]"),
    ("aadhaar", _AADHAAR_PATTERN, "[ID_REDACTED]"),
    ("phone", _PHONE_PATTERN, "[PHONE_REDACTED]"),
    ("passport", _PASSPORT_PATTERN, "[ID_REDACTED]"),
    ("pan", _PAN_PATTERN, "[ID_REDACTED]"),
]


# ─────────────────────────────────────────────────────────────
# Egress Policies per Decision Type
# ─────────────────────────────────────────────────────────────

_EGRESS_POLICIES: Dict[DecisionType, EgressPolicy] = {
    DecisionType.EXTRACTION: EgressPolicy(
        decision_type=DecisionType.EXTRACTION,
        allowed_fields={
            "raw_text", "document_text", "file_content",
            "source_type", "channel",
        },
        strip_pii=True,
        add_delimiters=True,
    ),
    DecisionType.CLASSIFICATION: EgressPolicy(
        decision_type=DecisionType.CLASSIFICATION,
        allowed_fields={
            "destination", "trip_type", "duration_days",
            "party_size", "budget_range", "special_requirements",
        },
        strip_pii=True,
        add_delimiters=True,
    ),
    DecisionType.GAP_ANALYSIS: EgressPolicy(
        decision_type=DecisionType.GAP_ANALYSIS,
        allowed_fields={
            "destination", "start_date", "end_date", "trip_type",
            "party_size", "budget_min", "budget_max",
            "special_requirements", "missing_fields",
        },
        strip_pii=True,
        add_delimiters=True,
    ),
    DecisionType.SUMMARIZATION: EgressPolicy(
        decision_type=DecisionType.SUMMARIZATION,
        allowed_fields={
            "destination", "start_date", "end_date", "trip_type",
            "party_size", "adults", "children", "budget_min", "budget_max",
            "special_requirements", "operator_notes",
        },
        strip_pii=True,
        add_delimiters=True,
    ),
    DecisionType.SUGGESTION: EgressPolicy(
        decision_type=DecisionType.SUGGESTION,
        allowed_fields={
            "destination", "trip_type", "duration_days",
            "party_size", "budget_range", "interests",
            "special_requirements",
        },
        strip_pii=True,
        add_delimiters=True,
    ),
}


# ─────────────────────────────────────────────────────────────
# Audit Log (in-process; production should write to DB/service)
# ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class EgressAuditEntry:
    """Audit record for a single LLM egress event."""
    timestamp: str
    decision_type: str
    provider: str
    content_hash: str  # SHA256 of sent content (not the content itself)
    content_length: int
    fields_sent: List[str]
    pii_redactions: int
    agency_id: Optional[str] = None
    trip_id: Optional[str] = None


_audit_log: List[EgressAuditEntry] = []


def get_audit_log() -> List[EgressAuditEntry]:
    """Return the in-process audit log. For testing and debugging."""
    return _audit_log.copy()


def clear_audit_log() -> None:
    """Clear the in-process audit log. For testing only."""
    _audit_log.clear()


# ─────────────────────────────────────────────────────────────
# Core Egress Functions
# ─────────────────────────────────────────────────────────────

def strip_pii(text: str) -> tuple[str, int]:
    """
    Remove PII patterns from text. Returns (cleaned_text, redaction_count).
    """
    redaction_count = 0
    for name, pattern, replacement in _PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            redaction_count += len(matches)
            text = pattern.sub(replacement, text)
    return text, redaction_count


def add_prompt_delimiters(content: str, source_label: str = "user_content") -> str:
    """
    Wrap untrusted user content in delimiters to reduce prompt injection risk.
    """
    return f"<{source_label}>\n{content}\n</{source_label}>"


def prepare_egress_payload(
    decision_type: DecisionType,
    content: str,
    provider: str,
    packet_fields: Optional[Dict[str, Any]] = None,
    agency_id: Optional[str] = None,
    trip_id: Optional[str] = None,
) -> str:
    """
    Prepare content for LLM egress through the defined policy.

    Args:
        decision_type: What type of LLM decision this is
        content: The raw content to be processed
        provider: LLM provider name (for audit)
        packet_fields: Optional dict of packet fields to filter
        agency_id: For audit logging
        trip_id: For audit logging

    Returns:
        Processed content safe for LLM egress

    Raises:
        ValueError: If no egress policy exists for the decision type
    """
    policy = _EGRESS_POLICIES.get(decision_type)
    if policy is None:
        dt_label = decision_type.value if isinstance(decision_type, DecisionType) else str(decision_type)
        raise ValueError(
            f"No egress policy defined for decision type '{dt_label}'. "
            f"Define a policy in llm_egress._EGRESS_POLICIES before sending data to LLM. "
            f"Available types: {[dt.value for dt in _EGRESS_POLICIES.keys()]}"
        )

    processed = content

    # 1. Filter packet fields if provided
    filtered_fields = {}
    if packet_fields is not None:
        filtered_fields = {
            k: v for k, v in packet_fields.items()
            if k in policy.allowed_fields
        }
        # Log filtered-out fields (not their values, just the names)
        filtered_out = set(packet_fields.keys()) - policy.allowed_fields
        if filtered_out:
            logger.info(
                "Egress filter: removed %d fields not in allowlist for %s: %s",
                len(filtered_out),
                decision_type.value,
                sorted(filtered_out),
            )

    # 2. Strip PII
    pii_redactions = 0
    if policy.strip_pii:
        processed, pii_redactions = strip_pii(processed)
        if pii_redactions > 0:
            logger.info(
                "Egress PII: redacted %d PII patterns from %s content",
                pii_redactions,
                decision_type.value,
            )

    # 3. Truncate if too long
    if len(processed) > policy.max_content_length:
        processed = processed[:policy.max_content_length]
        logger.warning(
            "Egress truncation: content for %s truncated from %d to %d chars",
            decision_type.value,
            len(content),
            policy.max_content_length,
        )

    # 4. Add delimiters
    if policy.add_delimiters:
        processed = add_prompt_delimiters(processed, source_label="user_content")

    # 5. Audit log
    if policy.require_audit:
        content_hash = hashlib.sha256(processed.encode()).hexdigest()[:16]
        entry = EgressAuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_type=decision_type.value,
            provider=provider,
            content_hash=content_hash,
            content_length=len(processed),
            fields_sent=sorted(filtered_fields.keys()) if packet_fields else [],
            pii_redactions=pii_redactions,
            agency_id=agency_id,
            trip_id=trip_id,
        )
        _audit_log.append(entry)
        logger.info(
            "Egress audit: %s → %s, %d chars, %d redactions, hash=%s",
            decision_type.value,
            provider,
            len(processed),
            pii_redactions,
            content_hash,
        )

    return processed


def get_egress_policy(decision_type: DecisionType) -> Optional[EgressPolicy]:
    """Get the egress policy for a decision type, or None if undefined."""
    return _EGRESS_POLICIES.get(decision_type)
