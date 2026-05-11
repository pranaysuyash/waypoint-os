"""
intake.traveler_proposal — Boundary contract for Build Proposal artifacts.

This module defines the first safe surface for the semantic `traveler_proposal`
stage. It is intentionally not a generator: proposal generation should depend on
these public/internal projections instead of serializing raw dataclasses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from .constants import GateIdentifier, PipelineStage


TRAVELER_PROPOSAL_STAGE = PipelineStage.TRAVELER_PROPOSAL.value
PROPOSAL_QUALITY_GATE = GateIdentifier.PROPOSAL_QUALITY.value

TRAVELER_PROPOSAL_SCHEMA_VERSION = "0.1"

RESTRICTED_TRAVELER_KEYS = frozenset(
    {
        "agency_notes",
        "booking_ref",
        "contact_name",
        "data_sources_used",
        "internal_notes",
        "internal_quote_sheet",
        "margin_amount",
        "margin_by_component",
        "margin_percent",
        "net_rate",
        "phone",
        "email",
        "raw_customer_history",
        "raw_research_sources",
        "supplier_name",
        "vendor_contacts",
        "vendors",
    }
)


@dataclass(slots=True)
class TravelerActivity:
    name: str
    description: str = ""
    duration: str = ""
    included: bool = True
    price_per_person: float | None = None
    why_included: str = ""


@dataclass(slots=True)
class TravelerPriceComponent:
    category: str
    description: str
    price: float


@dataclass(slots=True)
class TravelerPricing:
    currency: str
    total_per_person: float | None = None
    total_for_group: float | None = None
    components: list[TravelerPriceComponent] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    payment_schedule: list[dict[str, Any]] = field(default_factory=list)
    cancellation_policy: str = ""


@dataclass(slots=True)
class TravelerProposal:
    proposal_id: str
    packet_id: str
    title: str
    summary: str
    highlights: list[str] = field(default_factory=list)
    activities: list[TravelerActivity] = field(default_factory=list)
    pricing: TravelerPricing | None = None
    why_this_fits: str = ""
    next_steps: list[str] = field(default_factory=list)
    expiry_date: str | None = None
    assumptions_made: list[str] = field(default_factory=list)
    schema_version: str = TRAVELER_PROPOSAL_SCHEMA_VERSION

    def to_traveler_dict(self) -> dict[str, Any]:
        payload = _to_plain_data(self)
        assert_traveler_payload_safe(payload)
        return payload


@dataclass(slots=True)
class VendorContact:
    supplier_type: str
    supplier_name: str
    contact_name: str
    phone: str
    email: str
    booking_ref: str
    net_rate: float
    margin_percent: float
    reliability_score: float | None = None
    notes: str = ""


@dataclass(slots=True)
class InternalQuoteSheet:
    proposal_id: str
    vendors: list[VendorContact] = field(default_factory=list)
    cost_breakdown: dict[str, Any] = field(default_factory=dict)
    total_margin_amount: float | None = None
    total_margin_percent: float | None = None
    margin_by_component: dict[str, float] = field(default_factory=dict)
    booking_checklist: list[dict[str, Any]] = field(default_factory=list)
    follow_up_tasks: list[dict[str, Any]] = field(default_factory=list)

    def to_internal_dict(self) -> dict[str, Any]:
        return _to_plain_data(self)


@dataclass(slots=True)
class TravelerProposalBoundaryResult:
    traveler_proposal: TravelerProposal
    internal_quote_sheet: InternalQuoteSheet | None = None
    data_sources_used: list[str] = field(default_factory=list)
    assumptions_documented: list[str] = field(default_factory=list)
    completeness_score: float | None = None
    personalization_score: float | None = None
    stage: str = TRAVELER_PROPOSAL_STAGE
    gate: str = PROPOSAL_QUALITY_GATE

    def to_traveler_dict(self) -> dict[str, Any]:
        payload = {
            "stage": self.stage,
            "gate": self.gate,
            "traveler_proposal": self.traveler_proposal.to_traveler_dict(),
            "quality_metrics": {
                "completeness": self.completeness_score,
                "personalization": self.personalization_score,
            },
            "assumptions": list(self.assumptions_documented),
        }
        assert_traveler_payload_safe(payload)
        return payload

    def to_internal_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "gate": self.gate,
            "traveler_proposal": self.traveler_proposal.to_traveler_dict(),
            "internal_quote_sheet": (
                self.internal_quote_sheet.to_internal_dict()
                if self.internal_quote_sheet is not None
                else None
            ),
            "quality_metrics": {
                "completeness": self.completeness_score,
                "personalization": self.personalization_score,
            },
            "audit": {
                "sources": list(self.data_sources_used),
                "assumptions": list(self.assumptions_documented),
            },
        }


def assert_traveler_payload_safe(payload: Any) -> None:
    restricted_paths = _find_restricted_paths(payload)
    if restricted_paths:
        joined = ", ".join(restricted_paths[:8])
        raise ValueError(
            "traveler_proposal payload includes internal-only fields: "
            f"{joined}. Use the internal projection for margin, vendor, booking, "
            "raw source, or contact data."
        )


def _find_restricted_paths(value: Any, path: str = "") -> list[str]:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            key_str = str(key)
            current = f"{path}.{key_str}" if path else key_str
            if key_str in RESTRICTED_TRAVELER_KEYS:
                paths.append(current)
            paths.extend(_find_restricted_paths(nested, current))
        return paths
    if isinstance(value, (list, tuple)):
        paths = []
        for index, nested in enumerate(value):
            current = f"{path}[{index}]" if path else f"[{index}]"
            paths.extend(_find_restricted_paths(nested, current))
        return paths
    return []


def _to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_plain_data(nested) for key, nested in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_plain_data(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain_data(nested) for nested in value]
    return value
