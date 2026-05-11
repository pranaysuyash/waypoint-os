"""
intake.packet_models — CanonicalPacket v0.3 and all supporting dataclasses.

This is the single source of truth for the packet shape.
The JSON schema (specs/canonical_packet.schema.json) must mirror these classes.

v0.3 improvements:
- _EventTrackingDict: all dict mutations on facts/derived_signals/hypotheses
  automatically emit events — no more silent mutations.
- ContradictionState: contradiction lifecycle (detected → open → resolved).
- HypothesisState: hypothesis lifecycle (proposed → active → validated/rejected → stale).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Literal, Optional, Union

from .constants import DecisionState


# =============================================================================
# SECTION 0: SUITABILITY MODELS
# =============================================================================

@dataclass(slots=True)
class SuitabilityFlag:
    """Activity suitability assessment flag for a packet."""
    flag_type: str
    severity: Literal["low", "medium", "high", "critical"]
    reason: str
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    affected_travelers: List[str] = field(default_factory=list)


# =============================================================================
# SECTION 1: AUTHORITY & EXTRACTION MODELS
# =============================================================================

class AuthorityLevel:
    """Ordered authority levels — lower number = higher authority.

    CORRECT ORDER (per spec):
    manual_override > explicit_user > imported_structured > explicit_owner >
    derived_signal > soft_hypothesis > unknown
    """
    RANK = {
        "manual_override": 1,
        "explicit_user": 2,
        "imported_structured": 3,
        "explicit_owner": 4,
        "derived_signal": 5,
        "soft_hypothesis": 6,
        "unknown": 7,
    }

    MANUAL_OVERRIDE = "manual_override"
    EXPLICIT_USER = "explicit_user"
    IMPORTED_STRUCTURED = "imported_structured"
    EXPLICIT_OWNER = "explicit_owner"
    DERIVED_SIGNAL = "derived_signal"
    SOFT_HYPOTHESIS = "soft_hypothesis"
    UNKNOWN = "unknown"

    FACT_LEVELS = frozenset({
        MANUAL_OVERRIDE, EXPLICIT_USER, IMPORTED_STRUCTURED, EXPLICIT_OWNER,
    })

    @classmethod
    def rank(cls, level: str) -> int:
        return cls.RANK.get(level, 7)

    @classmethod
    def is_fact(cls, level: str) -> bool:
        return level in cls.FACT_LEVELS


def higher_authority(auth1: str, auth2: str) -> str:
    """Return the higher authority (lower rank number = higher authority)."""
    return auth1 if AuthorityLevel.rank(auth1) <= AuthorityLevel.rank(auth2) else auth2


# =============================================================================
# SECTION 2: EVIDENCE & SLOT MODELS
# =============================================================================

@dataclass(slots=True)
class EvidenceRef:
    """Provenance reference — links a value to its source."""
    envelope_id: str
    evidence_type: Literal[
        "text_span", "structured_field", "attachment_extract", "derived", "manual_entry"
    ]
    excerpt: str
    ref_id: str = field(default_factory=lambda: f"ref_{uuid.uuid4().hex[:6]}")
    field_path: Optional[str] = None
    offset: Optional[Dict[str, int]] = None  # {"start": 42, "end": 51}
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtractionMode:
    """Valid extraction modes — semantic meaning matters."""
    DIRECT_EXTRACT = "direct_extract"
    IMPORTED = "imported"
    NORMALIZED = "normalized"
    DERIVED = "derived"
    MANUAL_ENTRY = "manual_entry"


@dataclass(slots=True)
class Slot:
    """A field container with full provenance and authority tracking."""
    value: Any = None
    confidence: float = 0.0
    authority_level: str = AuthorityLevel.UNKNOWN
    extraction_mode: str = "unknown"
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    derived_from: List[str] = field(default_factory=list)  # Lineage: IDs of upstream slots/envelopes
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: Optional[str] = None
    # Maturity tag for derived signals: stub | heuristic | verified
    maturity: Optional[Literal["stub", "heuristic", "verified"]] = None

    def to_dict(self) -> dict:
        d = {
            "value": self.value,
            "confidence": self.confidence,
            "authority_level": self.authority_level,
            "extraction_mode": self.extraction_mode,
            "evidence_refs": [asdict(r) for r in self.evidence_refs],
            "derived_from": list(self.derived_from),
            "updated_at": self.updated_at,
            "notes": self.notes,
        }
        if self.maturity is not None:
            d["maturity"] = self.maturity
        return d


@dataclass(slots=True)
class UnknownField:
    """Explicit representation of unknown/missing fields."""
    field_name: str
    reason: Literal["not_present_in_source", "not_extracted_yet", "extraction_failed", "intentionally_unknown"]
    attempted_at: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# SECTION 3: AMBIGUITY, OWNER CONSTRAINT, SUBGROUP
# =============================================================================

@dataclass(slots=True)
class ContradictionValue:
    """A single value in a contradiction with its source attribution."""
    value: Any
    source: str  # envelope_id or source identifier
    authority: str  # AuthorityLevel value
    timestamp: Optional[str] = None  # ISO-8601 when this value was captured


@dataclass(slots=True)
class Ambiguity:
    """First-class ambiguity marker — not hidden under unknowns."""
    field_name: str
    ambiguity_type: Literal[
        "unresolved_alternatives",     # "Andaman or Sri Lanka"
        "value_vague",                  # "big family"
        "date_window_only",             # "March or April"
        "budget_unclear_scope",         # "around 2L" — total vs per-person?
        "budget_stretch_present",       # "can stretch if it's good"
        "composition_unclear",          # "3 of them I think"
        "destination_open",             # "somewhere with beaches"
    ]
    raw_value: str
    normalized_value: Optional[str] = None
    confidence: float = 0.0
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(slots=True)
class OwnerConstraint:
    """An owner constraint with explicit visibility semantics."""
    text: str
    visibility: Literal["internal_only", "traveler_safe_transformable"]
    evidence_refs: List[EvidenceRef] = field(default_factory=list)


@dataclass(slots=True)
class SubGroup:
    """A sub-group within a multi-party trip. Structural, not a loose dict."""
    group_id: str
    label: str
    size: int
    composition: Dict[str, int] = field(default_factory=dict)
    budget_share: Optional[int] = None
    payment_status: Literal["not_started", "partial", "paid", "emi_pending"] = "not_started"
    document_status: Literal["not_submitted", "partial", "complete"] = "not_submitted"
    constraints: List[str] = field(default_factory=list)
    contact: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# SECTION 4: LIFECYCLE & RETENTION MODELS
# =============================================================================

@dataclass(slots=True)
class LifecycleInfo:
    """Lead/customer lifecycle signals for retention and commercial decisions."""
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    trip_thread_id: Optional[str] = None
    status: Optional[Literal[
        "NEW_LEAD",
        "ACTIVE_DISCOVERY",
        "QUOTE_IN_PROGRESS",
        "QUOTE_SENT",
        "ENGAGED_AFTER_QUOTE",
        "GHOST_RISK",
        "WON",
        "BOOKING_IN_PROGRESS",
        "TRIP_CONFIRMED",
        "TRIP_ACTIVE",
        "TRIP_COMPLETED",
        "REVIEW_PENDING",
        "RETENTION_WINDOW",
        "REPEAT_BOOKED",
        "DORMANT",
        "LOST",
    ]] = None
    created_at: Optional[str] = None
    last_customer_message_at: Optional[str] = None
    last_agent_message_at: Optional[str] = None
    last_meaningful_engagement_at: Optional[str] = None
    quote_sent_at: Optional[str] = None
    quote_opened: bool = False
    quote_open_count: int = 0
    options_viewed_count: int = 0
    links_clicked_count: int = 0
    revision_count: int = 0
    days_since_last_reply: Optional[int] = None
    payment_stage: Literal["none", "token", "partial", "full"] = "none"
    commitment_signals: List[str] = field(default_factory=list)
    risk_signals: List[str] = field(default_factory=list)
    repeat_trip_count: int = 0
    last_trip_completed_at: Optional[str] = None
    loss_reason: Optional[str] = None
    win_reason: Optional[str] = None
    next_best_action: Optional[str] = None
    next_action_due_at: Optional[str] = None


# =============================================================================
# SECTION 5: SOURCE ENVELOPE
# =============================================================================

@dataclass(slots=True)
class SourceEnvelope:
    """The canonical input wrapper — preserves all source information."""
    envelope_id: str
    source_system: Literal["agency_notes", "traveler_form", "email_thread", "chat_history", "structured_import"]
    actor_type: Literal["agent", "traveler", "owner", "system"]
    received_at: str
    content: Any  # raw content (string or dict)
    content_type: Literal["freeform_text", "structured_json", "hybrid"]
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_freeform(cls, text: str, source: str = "agency_notes", actor: str = "agent") -> "SourceEnvelope":
        return cls(
            envelope_id=f"env_{uuid.uuid4().hex[:8]}",
            source_system=source,
            actor_type=actor,
            received_at=datetime.now().isoformat(),
            content=text,
            content_type="freeform_text",
        )

    @classmethod
    def from_structured(cls, data: dict, source: str = "structured_import", actor: str = "system") -> "SourceEnvelope":
        return cls(
            envelope_id=f"env_{uuid.uuid4().hex[:8]}",
            source_system=source,
            actor_type=actor,
            received_at=datetime.now().isoformat(),
            content=data,
            content_type="structured_json",
        )


# =============================================================================
# SECTION 5A: EVENT TRACKING DICT (enforces "no silent mutations")
# =============================================================================

class _EventTrackingDict(dict):
    """A dict whose mutations automatically emit events on the owning packet.

    When any code writes ``packet.facts["key"] = slot``, the dict intercepts
    ``__setitem__`` and emits an event BEFORE the value is stored.  This
    guarantees every visible state change is auditable — no convention needed.

    ``__delitem__`` is also intercepted to emit removal events.

    The owner/category kwargs are optional so that ``dataclasses.asdict()``
    (which calls ``type(obj)(items)``) can reconstruct the dict without
    a packet reference.
    """
    __slots__ = ("_owner", "_category")

    def __init__(self, *args, owner: "CanonicalPacket | None" = None, category: str = "", **kwargs):
        self._owner = owner
        self._category = category
        super().__init__(*args, **kwargs)

    @property
    def _has_owner(self) -> bool:
        return self._owner is not None and self._category

    def __setitem__(self, key, value):
        old = self.get(key) if key in self else None
        super().__setitem__(key, value)
        if self._has_owner:
            event_type = {
                "facts": "fact_set",
                "derived_signals": "derived_signal_set",
                "hypotheses": "hypothesis_set",
            }.get(self._category, f"{self._category}_set")
            new_val = value.value if hasattr(value, "value") else value
            old_val = old.value if hasattr(old, "value") else old if old else None
            self._owner._emit_event(event_type, {
                "field_name": key,
                "old_value": old_val,
                "new_value": new_val,
            })

    def __delitem__(self, key):
        if key in self:
            old = self[key]
            old_val = old.value if hasattr(old, "value") else old
            super().__delitem__(key)
            if self._has_owner:
                self._owner._emit_event(f"{self._category.rstrip('s')}_removed", {
                    "field_name": key,
                    "old_value": old_val,
                })


# =============================================================================
# SECTION 5B: CONTRADICTION & HYPOTHESIS STATE ENUMS
# =============================================================================

class ContradictionState(StrEnum):
    DETECTED = "detected"
    OPEN = "open"
    RESOLVED = "resolved"


class HypothesisState(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    VALIDATED = "validated"
    REJECTED = "rejected"
    STALE = "stale"


# =============================================================================
# SECTION 6: CANONICAL PACKET (v0.3)
# =============================================================================

@dataclass(slots=True)
class CanonicalPacket:
    """
    Agency-OS Packet v0.3 — the single source of truth for all intake data.

    CRITICAL: operating_mode is top-level (system routing), NOT inside facts.
    CRITICAL: facts vs derived_signals are strictly separated — no duplication.

    v0.3: _EventTrackingDict on facts/derived_signals/hypotheses guarantees
    every mutation emits an event. Contradictions and hypotheses have explicit
    lifecycle state tracking.
    """
    packet_id: str
    schema_version: str = "0.3"
    stage: Literal["discovery", "shortlist", "proposal", "booking"] = "discovery"
    operating_mode: Literal[
        "normal_intake", "audit", "emergency", "follow_up",
        "cancellation", "post_trip", "coordinator_group", "owner_review",
    ] = "normal_intake"
    decision_state: Optional[DecisionState] = None

    # Core data layers — STRICTLY SEPARATED, auto-tracking via _EventTrackingDict
    # These start as plain dicts (default_factory=dict) and are wrapped with
    # _EventTrackingDict in __post_init__ so every mutation emits an audit event.
    facts: Dict[str, Slot] = field(default_factory=dict)
    derived_signals: Dict[str, Slot] = field(default_factory=dict)
    hypotheses: Dict[str, Slot] = field(default_factory=dict)
    lifecycle: Optional[LifecycleInfo] = None
    feedback: Optional[Dict[str, Any]] = None
    raw_note: Optional[str] = None

    # Suitability assessment
    suitability_flags: List[SuitabilityFlag] = field(default_factory=list)

    # Explicit tracking
    ambiguities: List[Ambiguity] = field(default_factory=list)
    unknowns: List[UnknownField] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    source_envelope_ids: List[str] = field(default_factory=list)
    revision_count: int = 0

    # Audit trail
    event_cursor: int = 0
    events: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Initialisation — wrap raw dicts with _EventTrackingDict
    # ------------------------------------------------------------------

    def __post_init__(self):
        # Wrap the plain dicts with _EventTrackingDict so every mutation
        # (including direct ``packet.facts["key"] = slot``) is audited.
        # Existing items are copied via _EventTrackingDict.__init__.
        self.facts = _EventTrackingDict(self.facts, owner=self, category="facts")
        self.derived_signals = _EventTrackingDict(self.derived_signals, owner=self, category="derived_signals")
        self.hypotheses = _EventTrackingDict(self.hypotheses, owner=self, category="hypotheses")

    # ------------------------------------------------------------------
    # Mutation methods (all go through _emit_event for audit trail)
    # ------------------------------------------------------------------

    def _emit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        self.event_cursor += 1
        self.events.append({
            "event_id": self.event_cursor,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        })

    def set_fact(self, field_name: str, slot: Slot) -> None:
        """Set a fact. CRITICAL: only accepts slots with fact-level authority.

        Merge policy: never overwrite a non-empty value with an empty one.
        Lists (e.g. destination candidates) are appended, not replaced.
        Scalars are kept if the existing value has higher confidence.

        Event emission is automatic — _EventTrackingDict.__setitem__ fires
        on every assignment.
        """
        if slot.authority_level not in AuthorityLevel.FACT_LEVELS:
            raise ValueError(
                f"Cannot set_fact with authority_level='{slot.authority_level}'. "
                f"Facts require: {sorted(AuthorityLevel.FACT_LEVELS)}"
            )

        existing = self.facts.get(field_name)
        if existing is not None:
            new_val = slot.value
            old_val = existing.value

            if new_val is None or new_val == [] or new_val == "":
                return
            if old_val is None or old_val == [] or old_val == "":
                pass
            elif isinstance(new_val, list) and isinstance(old_val, list):
                merged = list(dict.fromkeys(old_val + new_val))
                slot = Slot(
                    value=merged,
                    confidence=max(existing.confidence, slot.confidence),
                    authority_level="explicit_user",
                    extraction_mode="merged",
                    evidence_refs=existing.evidence_refs + slot.evidence_refs,
                )
            elif slot.confidence < existing.confidence:
                return

        self.facts[field_name] = slot

    def set_derived_signal(self, field_name: str, slot: Slot) -> None:
        """Set a derived signal. CRITICAL: only accepts derived_signal authority."""
        if slot.authority_level != AuthorityLevel.DERIVED_SIGNAL:
            raise ValueError(
                f"set_derived_signal requires authority_level='derived_signal', "
                f"got '{slot.authority_level}'"
            )
        self.derived_signals[field_name] = slot

    def set_hypothesis(self, field_name: str, slot: Slot) -> None:
        """Set a soft hypothesis. Initial state is PROPOSED (lifecycle tracking)."""
        if slot.authority_level != AuthorityLevel.SOFT_HYPOTHESIS:
            raise ValueError(
                f"set_hypothesis requires authority_level='soft_hypothesis', "
                f"got '{slot.authority_level}'"
            )
        if not isinstance(slot.value, dict):
            slot.value = {"value": slot.value}
        slot.value["_hypothesis_state"] = HypothesisState.PROPOSED
        self.hypotheses[field_name] = slot

    def add_ambiguity(self, ambiguity: Ambiguity) -> None:
        self.ambiguities.append(ambiguity)
        self._emit_event("ambiguity_added", {
            "field_name": ambiguity.field_name,
            "ambiguity_type": ambiguity.ambiguity_type,
        })

    def add_unknown(self, field_name: str, reason: str) -> None:
        self.unknowns.append(UnknownField(field_name=field_name, reason=reason))
        self._emit_event("unknown_added", {"field_name": field_name, "reason": reason})

    def add_contradiction(
        self,
        field_name: str,
        values: Union[List[Any], List[ContradictionValue]],
        sources: Optional[List[str]] = None,
    ) -> None:
        """Add a contradiction. Supports both legacy and new structured formats.

        Lifecycle: starts in ContradictionState.DETECTED.  Caller should call
        ``open_contradiction()`` after presenting to the operator, then
        ``resolve_contradiction()`` once a resolution is chosen.

        Legacy: add_contradiction("budget", ["3L", "4L"], ["email", "chat"])
        New: add_contradiction("budget", [
            ContradictionValue("3L", "email", "explicit_user"),
            ContradictionValue("4L", "chat", "explicit_user"),
        ])
        """
        detected_at = datetime.now().isoformat()

        if values and isinstance(values[0], ContradictionValue):
            structured_values = values
            sources_list = [v.source for v in structured_values]
        else:
            structured_values = []
            sources_list = sources or []
            for i, val in enumerate(values):
                source = sources_list[i] if i < len(sources_list) else "unknown"
                structured_values.append(
                    ContradictionValue(value=val, source=source, authority="explicit_user")
                )
            while len(sources_list) < len(values):
                sources_list.append("unknown")

        entry = {
            "field_name": field_name,
            "values": structured_values,
            "values_legacy": [v.value for v in structured_values],
            "sources": sources_list,
            "detected_at": detected_at,
            "state": ContradictionState.DETECTED,
            "resolved_at": None,
            "resolution": None,
            "resolved_by": None,
        }
        self.contradictions.append(entry)
        self._emit_event("contradiction_detected", {
            "field_name": field_name,
            "state": ContradictionState.DETECTED,
        })

    # ------------------------------------------------------------------
    # Contradiction lifecycle (v0.3)
    # ------------------------------------------------------------------

    def _find_contradiction_index(self, field_name: str) -> int:
        for i, c in enumerate(self.contradictions):
            if c.get("field_name") == field_name:
                return i
        return -1

    def open_contradiction(self, field_name: str) -> bool:
        """Transition a DETECTED contradiction to OPEN (shown to operator)."""
        idx = self._find_contradiction_index(field_name)
        if idx < 0:
            return False
        if self.contradictions[idx]["state"] not in (ContradictionState.DETECTED, ContradictionState.RESOLVED):
            return False
        self.contradictions[idx]["state"] = ContradictionState.OPEN
        self._emit_event("contradiction_opened", {"field_name": field_name})
        return True

    def resolve_contradiction(
        self,
        field_name: str,
        resolution: str,
        resolved_by: str = "operator",
    ) -> bool:
        """Transition an OPEN contradiction to RESOLVED.

        Args:
            field_name: The field with the contradiction.
            resolution: Description of how it was resolved (e.g. "chose value A").
            resolved_by: Actor identifier (operator id).
        """
        idx = self._find_contradiction_index(field_name)
        if idx < 0:
            return False
        if self.contradictions[idx]["state"] != ContradictionState.OPEN:
            return False
        self.contradictions[idx]["state"] = ContradictionState.RESOLVED
        self.contradictions[idx]["resolved_at"] = datetime.now().isoformat()
        self.contradictions[idx]["resolution"] = resolution
        self.contradictions[idx]["resolved_by"] = resolved_by
        self._emit_event("contradiction_resolved", {
            "field_name": field_name,
            "resolution": resolution,
            "resolved_by": resolved_by,
        })
        return True

    def reopen_contradiction(self, field_name: str) -> bool:
        """Reopen a previously RESOLVED contradiction."""
        idx = self._find_contradiction_index(field_name)
        if idx < 0:
            return False
        if self.contradictions[idx]["state"] != ContradictionState.RESOLVED:
            return False
        self.contradictions[idx]["state"] = ContradictionState.OPEN
        self.contradictions[idx]["resolved_at"] = None
        self.contradictions[idx]["resolution"] = None
        self.contradictions[idx]["resolved_by"] = None
        self._emit_event("contradiction_reopened", {"field_name": field_name})
        return True

    # ------------------------------------------------------------------
    # Hypothesis lifecycle (v0.3)
    # ------------------------------------------------------------------

    def activate_hypothesis(self, field_name: str) -> bool:
        """Transition a PROPOSED hypothesis to ACTIVE (in use by decision engine)."""
        slot = self.hypotheses.get(field_name)
        if slot is None:
            return False
        if not isinstance(slot.value, dict):
            return False
        if slot.value.get("_hypothesis_state") != HypothesisState.PROPOSED:
            return False
        slot.value["_hypothesis_state"] = HypothesisState.ACTIVE
        self._emit_event("hypothesis_activated", {"field_name": field_name})
        return True

    def validate_hypothesis(self, field_name: str, confidence: float = 1.0) -> bool:
        """Transition an ACTIVE hypothesis to VALIDATED (confirmed correct)."""
        slot = self.hypotheses.get(field_name)
        if slot is None:
            return False
        if not isinstance(slot.value, dict):
            return False
        current = slot.value.get("_hypothesis_state")
        if current not in (HypothesisState.ACTIVE, HypothesisState.PROPOSED):
            return False
        slot.value["_hypothesis_state"] = HypothesisState.VALIDATED
        slot.confidence = confidence
        self._emit_event("hypothesis_validated", {
            "field_name": field_name,
            "confidence": confidence,
        })
        return True

    def reject_hypothesis(self, field_name: str, reason: str = "") -> bool:
        """Transition an ACTIVE hypothesis to REJECTED (found incorrect)."""
        slot = self.hypotheses.get(field_name)
        if slot is None:
            return False
        if not isinstance(slot.value, dict):
            return False
        current = slot.value.get("_hypothesis_state")
        if current not in (HypothesisState.ACTIVE, HypothesisState.PROPOSED):
            return False
        slot.value["_hypothesis_state"] = HypothesisState.REJECTED
        slot.value["_rejection_reason"] = reason
        slot.confidence = 0.0
        self._emit_event("hypothesis_rejected", {
            "field_name": field_name,
            "reason": reason,
        })
        return True

    def mark_hypothesis_stale(self, field_name: str) -> bool:
        """Mark a validated or rejected hypothesis as STALE (superseded)."""
        slot = self.hypotheses.get(field_name)
        if slot is None:
            return False
        if not isinstance(slot.value, dict):
            return False
        current = slot.value.get("_hypothesis_state")
        if current not in (HypothesisState.VALIDATED, HypothesisState.REJECTED):
            return False
        slot.value["_hypothesis_state"] = HypothesisState.STALE
        self._emit_event("hypothesis_staled", {"field_name": field_name})
        return True

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        contradictions_out = []
        for c in self.contradictions:
            entry = dict(c)
            if "values" in entry and entry["values"]:
                entry["values"] = [
                    asdict(v) if isinstance(v, ContradictionValue) else v
                    for v in entry["values"]
                ]
            contradictions_out.append(entry)

        return {
            "packet_id": self.packet_id,
            "schema_version": self.schema_version,
            "stage": self.stage,
            "operating_mode": self.operating_mode,
            "decision_state": self.decision_state,
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "derived_signals": {k: v.to_dict() for k, v in self.derived_signals.items()},
            "hypotheses": {k: v.to_dict() for k, v in self.hypotheses.items()},
            "lifecycle": asdict(self.lifecycle) if self.lifecycle else None,
            "ambiguities": [asdict(a) for a in self.ambiguities],
            "unknowns": [asdict(u) for u in self.unknowns],
            "contradictions": contradictions_out,
            "source_envelope_ids": self.source_envelope_ids,
            "revision_count": self.revision_count,
            "event_cursor": self.event_cursor,
            "events": self.events,
        }
