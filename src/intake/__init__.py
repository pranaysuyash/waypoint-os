"""
intake — Agency-OS intake engine (NB01 v0.2).

Core modules:
- packet_models: CanonicalPacket, Slot, EvidenceRef, Ambiguity, OwnerConstraint, SubGroup
- normalizer: Normalizer with ambiguity detection, budget/date parsing
- extractors: ExtractionPipeline with pattern-based extraction
- validation: validate_packet + PacketValidationReport
"""

from .packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    ExtractionMode,
    OwnerConstraint,
    Slot,
    SourceEnvelope,
    SubGroup,
    UnknownField,
    higher_authority,
)
from .normalizer import Normalizer
from .extractors import ExtractionPipeline
from .validation import PacketValidationReport, validate_packet

__version__ = "0.2.1"

from .decision import (
    DecisionResult,
    AmbiguityRef,
    run_gap_and_decision,
    check_budget_feasibility,
    classify_ambiguity_severity,
)
