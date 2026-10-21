"""
spine_api.services.confirmation_grader — deterministic content grading (T9, FND-0232).

The registration defect: supplier confirmations whose content references
segments or passengers were accepted ungraded — missing flight segments or
mismatched passenger names passed as valid and fed retry loops.

Design (first principles):
- **Grade-at-read, not stored**: the grade is derived from the confirmation's
  recorded content *and the trip's current persisted data*, so it stays
  truthful as the trip evolves and needs no schema migration. It is advisory
  metadata on the read model, never a mutation of the record.
- **Deterministic validators are the authority** (money/documents doctrine):
  string-normalized matching against persisted trip names and explicit
  structural presence checks. No LLM in this path.
- **Grades**: ``clean`` (content present and consistent), ``incomplete``
  (expected structural content absent — cannot confirm), ``defective``
  (present content contradicts the trip — must not be retried blindly).

Grading is advisory: it never blocks storage (an operator may deliberately
record a partial confirmation as draft); it informs the verify step and the
operator UI.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_NAME_SPLIT = re.compile(r"[^a-z0-9]+")


def _name_tokens(value: str) -> set[str]:
    """Lowercased alphabetic tokens of a person name (titles and single-letter
    initials stripped — initials do not discriminate identity)."""
    tokens = [t for t in _NAME_SPLIT.split((value or "").lower()) if t]
    return {t for t in tokens if len(t) > 1 and t not in {"mr", "mrs", "ms", "dr", "master"}}


def _name_matches(candidate: str, reference_names: List[str]) -> bool:
    """A candidate name matches if every token appears in some reference name
    (handles 'Meera Sharma' recorded as 'Sharma Meera M')."""
    cand = _name_tokens(candidate)
    if not cand:
        return False
    for reference in reference_names:
        ref = _name_tokens(reference)
        if cand and cand.issubset(ref):
            return True
    return False


@dataclass(slots=True)
class ContentIssue:
    code: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "detail": self.detail}


@dataclass(slots=True)
class ContentGrade:
    grade: str  # clean | incomplete | defective
    issues: List[ContentIssue] = field(default_factory=list)
    checked: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "issues": [i.to_dict() for i in self.issues],
            "checked": self.checked,
        }


def _trip_reference_names(trip: dict) -> List[str]:
    """Every persisted person name on the trip: traveler bundles, packet
    customer fields, and speaker-attributed travelers[] facts."""
    names: List[str] = []

    def _add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            names.append(value.strip())

    packet = trip.get("packet") or {}
    for key in ("customer_name", "contact_name", "lead_traveler_name", "traveler_name"):
        _add(packet.get(key) or trip.get(key))

    travelers = (packet.get("facts") or {}).get("travelers")
    travelers_value = travelers.get("value") if isinstance(travelers, dict) else travelers
    for traveler in travelers_value or []:
        if isinstance(traveler, dict):
            _add(traveler.get("name"))

    party = trip.get("party_composition")
    if isinstance(party, str):
        # "2 adults, 1 child" carries no names — only add if it looks like names.
        for part in party.split(","):
            if len(part.split()) <= 3 and part.strip() and part.strip()[0].isalpha():
                _add(part.strip())

    return names


def grade_confirmation_content(
    *,
    confirmation_type: str,
    content: Dict[str, Any],
    trip: Optional[dict],
) -> ContentGrade:
    """Grade one confirmation's content against the trip. Deterministic.

    ``content`` is the decoded confirmation payload: supplier_name,
    confirmation_number, notes, external_ref, plus optional structured blocks
    (``segments`` for flights, ``guests`` for hotels) when the supplier's
    confirmation includes them.
    """
    issues: List[ContentIssue] = []
    checked: List[str] = []

    # Universal completeness: a confirmation that names neither a supplier nor
    # a confirmation number cannot be verified against anything.
    has_supplier = bool((content.get("supplier_name") or "").strip())
    has_number = bool((content.get("confirmation_number") or "").strip())
    checked.append("supplier_or_number_present")
    if not has_supplier and not has_number:
        issues.append(
            ContentIssue(
                "missing_identity",
                "Confirmation records neither a supplier name nor a confirmation number — it cannot be verified.",
            )
        )

    reference_names = _trip_reference_names(trip or {})

    if confirmation_type == "flight":
        segments = content.get("segments")
        if segments is None:
            checked.append("flight_segments_present")
            issues.append(
                ContentIssue(
                    "missing_segments",
                    "Flight confirmation records no segments (flights) — cannot confirm the itinerary.",
                )
            )
        elif isinstance(segments, list):
            checked.append("flight_segments_present")
            checked.append("flight_segment_fields")
            for index, segment in enumerate(segments):
                if not isinstance(segment, dict):
                    continue
                for required in ("flight_number", "date"):
                    if not str(segment.get(required) or "").strip():
                        issues.append(
                            ContentIssue(
                                "segment_missing_field",
                                f"Segment {index + 1} is missing '{required}'.",
                            )
                        )
        passengers = content.get("passengers")
        if isinstance(passengers, list) and passengers:
            checked.append("passenger_names_match_trip")
            for passenger in passengers:
                name = str(passenger or "").strip()
                if name and reference_names and not _name_matches(name, reference_names):
                    issues.append(
                        ContentIssue(
                            "passenger_name_mismatch",
                            f"Passenger '{name}' does not match any traveler recorded on the trip.",
                        )
                    )
        elif passengers is not None:
            checked.append("passenger_names_match_trip")

    elif confirmation_type == "hotel":
        guests = content.get("guests")
        if guests is None:
            checked.append("hotel_guests_present")
            issues.append(
                ContentIssue(
                    "missing_guests",
                    "Hotel confirmation records no guest names — cannot confirm the booking party.",
                )
            )
        elif isinstance(guests, list):
            checked.append("hotel_guests_present")
            checked.append("guest_names_match_trip")
            for guest in guests:
                name = str(guest or "").strip()
                if name and reference_names and not _name_matches(name, reference_names):
                    issues.append(
                        ContentIssue(
                            "guest_name_mismatch",
                            f"Guest '{name}' does not match any traveler recorded on the trip.",
                        )
                    )

    if issues:
        defective_markers = {"passenger_name_mismatch", "guest_name_mismatch", "segment_missing_field"}
        grade = "defective" if any(i.code in defective_markers for i in issues) else "incomplete"
    else:
        grade = "clean"

    return ContentGrade(grade=grade, issues=issues, checked=checked)
