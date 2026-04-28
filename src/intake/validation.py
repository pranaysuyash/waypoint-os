"""
intake.validation — Schema validation and packet validation reporting.

Every NB01 run should end with a validation check.
Severity: structural errors make is_valid=False, softer issues are warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .packet_models import CanonicalPacket, AuthorityLevel


# v0.1 legacy names that should NOT appear in a v0.2 packet
LEGACY_FIELD_NAMES = frozenset({
    "destination_city",
    "travel_dates",
    "budget_range",
    "traveler_count",
    "traveler_details",
    "traveler_preferences",
})

# Fields that should ONLY be derived signals, NEVER facts
DERIVED_ONLY_FIELDS = frozenset({
    "is_repeat_customer",
    "domestic_or_international",
    "urgency",
    "budget_feasibility",
    "sourcing_path",
    "preferred_supplier_available",
    "estimated_minimum_cost",
    "composition_risk",
    "document_risk",
    "operational_complexity",
    "value_gap",
    "internal_data_present",
    "booking_readiness",
    "budget_breakdown",
    "budget_verdict",
})

# Fields that MUST be present to even save an intake trip
INTAKE_MINIMUM = [
    "destination_candidates",
    "date_window",
]

# Fields required before a quote can be generated (full MVB)
QUOTE_READY = [
    "destination_candidates",
    "origin_city",
    "date_window",
    "party_size",
    "budget_raw_text",
    "trip_purpose",
]

# Backward-compat alias: the original 6-field MVB used before intake/quote split
DISCOVERY_MVB = QUOTE_READY

# Operating modes that require numeric budget
NUMERIC_BUDGET_MODES = frozenset({"audit", "coordinator_group"})


@dataclass
class ValidationIssue:
    """A single validation finding with severity."""
    severity: str  # "error" | "warning"
    code: str      # Machine-readable code
    message: str   # Human-readable description
    field: str = ""


@dataclass
class PacketValidationReport:
    """Result of validating a CanonicalPacket against v0.2 schema."""
    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    ambiguity_report: List[Dict[str, Any]] = field(default_factory=list)
    evidence_coverage: Dict[str, int] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate_packet(packet: CanonicalPacket, stage: str = "discovery") -> PacketValidationReport:
    """
    Validate a CanonicalPacket against v0.2 schema.

    Entry point: ``validate_packet(packet)`` → PacketValidationReport.

    Every NB01 run should end with this check.
    is_valid is False if ANY errors exist (structural violations).
    Warnings do NOT affect is_valid but are still reported.
    """
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    # ------------------------------------------------------------------
    # ERROR-LEVEL CHECKS (structural, block is_valid)
    # ------------------------------------------------------------------

    # 1. Missing discovery MVB fields — stage-aware (intake minimum vs quote-ready)
    if stage == "discovery":
        # Intake stage: INTAKE_MINIMUM fields are errors, QUOTE_READY extras are warnings
        required = INTAKE_MINIMUM
        quote_extra = [f for f in QUOTE_READY if f not in INTAKE_MINIMUM]
        for field_name in quote_extra:
            if field_name not in packet.facts:
                warnings.append(ValidationIssue(
                    severity="warning",
                    code="QUOTE_READY_INCOMPLETE",
                    message=f"Field '{field_name}' missing — needed to generate a quote, "
                            f"but trip can still be saved",
                    field=field_name,
                ))
    else:
        # Shortlist and later: full QUOTE_READY required
        required = QUOTE_READY

    for field_name in required:
        if field_name not in packet.facts:
            errors.append(ValidationIssue(
                severity="error",
                code="MVB_MISSING",
                message=f"Required field '{field_name}' not present",
                field=field_name,
            ))

    # 2. For specific operating modes, require numeric budget
    if packet.operating_mode in NUMERIC_BUDGET_MODES:
        if "budget_min" not in packet.facts:
            errors.append(ValidationIssue(
                severity="error",
                code="NUMERIC_BUDGET_REQUIRED",
                message=f"Numeric budget_min required for {packet.operating_mode} mode",
                field="budget_min",
            ))

    # 3. Derived-only fields must NOT appear in facts
    for name in DERIVED_ONLY_FIELDS:
        if name in packet.facts:
            errors.append(ValidationIssue(
                severity="error",
                code="DERIVED_IN_FACTS",
                message=f"Field '{name}' should be a derived signal, not a fact",
                field=name,
            ))

    # 4. Facts must have fact-level authority
    for name, slot in packet.facts.items():
        if not AuthorityLevel.is_fact(slot.authority_level):
            errors.append(ValidationIssue(
                severity="error",
                code="FACT_BAD_AUTHORITY",
                message=f"Field '{name}' has authority_level='{slot.authority_level}' "
                        f"but is in facts (requires fact-level authority)",
                field=name,
            ))

    # 5. Derived signals must have derived_signal authority
    for name, slot in packet.derived_signals.items():
        if slot.authority_level != AuthorityLevel.DERIVED_SIGNAL:
            errors.append(ValidationIssue(
                severity="error",
                code="DERIVED_BAD_AUTHORITY",
                message=f"Derived signal '{name}' has authority_level='{slot.authority_level}' "
                        f"(expected 'derived_signal')",
                field=name,
            ))

    # 6. Derived signals must have maturity tag
    for name, slot in packet.derived_signals.items():
        if slot.maturity is None:
            errors.append(ValidationIssue(
                severity="error",
                code="MISSING_MATURITY",
                message=f"Derived signal '{name}' has no maturity tag (must be stub/heuristic/verified)",
                field=name,
            ))
        elif slot.maturity not in ("stub", "heuristic", "verified"):
            errors.append(ValidationIssue(
                severity="error",
                code="INVALID_MATURITY",
                message=f"Derived signal '{name}' has invalid maturity: '{slot.maturity}'",
                field=name,
            ))

    # 7. Legacy field names (migration guard) — ERROR level
    for name in LEGACY_FIELD_NAMES:
        if name in packet.facts:
            errors.append(ValidationIssue(
                severity="error",
                code="LEGACY_FIELD",
                message=f"Legacy v0.1 field '{name}' found — migrate to v0.2 name",
                field=name,
            ))

    # ------------------------------------------------------------------
    # WARNING-LEVEL CHECKS (informational, don't block is_valid)
    # ------------------------------------------------------------------

    # 8. Facts with low confidence
    for name, slot in packet.facts.items():
        if slot.confidence < 0.5 and AuthorityLevel.is_fact(slot.authority_level):
            warnings.append(ValidationIssue(
                severity="warning",
                code="LOW_CONFIDENCE_FACT",
                message=f"Fact '{name}' has low confidence ({slot.confidence})",
                field=name,
            ))

    # 9. High number of ambiguities
    if len(packet.ambiguities) > 5:
        warnings.append(ValidationIssue(
            severity="warning",
            code="HIGH_AMBIGUITY",
            message=f"Packet has {len(packet.ambiguities)} ambiguities — review extraction quality",
        ))

    # 10. Stub signals in derived
    stub_count = sum(1 for s in packet.derived_signals.values() if s.maturity == "stub")
    if stub_count > 3:
        warnings.append(ValidationIssue(
            severity="warning",
            code="MANY_STUBS",
            message=f"Packet has {stub_count} stub signals — downstream logic should respect maturity",
        ))

    # ------------------------------------------------------------------
    # Collect reports (not errors, just data)
    # ------------------------------------------------------------------

    ambiguity_report = [
        {"field": a.field_name, "type": a.ambiguity_type, "raw_value": a.raw_value}
        for a in packet.ambiguities
    ]

    evidence_coverage = {k: len(v.evidence_refs) for k, v in packet.facts.items()}

    is_valid = len(errors) == 0

    return PacketValidationReport(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        ambiguity_report=ambiguity_report,
        evidence_coverage=evidence_coverage,
    )
