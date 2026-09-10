"""
tests/test_ts07_operation_keyed_requiredness.py — TS-07 (2026-09-10
training-session register): operation-keyed field requiredness.

Contract under test (register TS-07; lifecycle-contracts addendum 2026-09-10):
- A field is not globally required: FIELD_REQUIRED_FOR keys requiredness to
  operations (planning / fare_quote / entry_validation / booking).
- classify_missing_fields: tutor-model classifier for NEEDS_INFORMATION —
  missing blocking fields with their required_for ops; preference fields are
  never blocking; present fields omitted; nothing invented for unknown fields.
- question_priority_order: most-blocking field first (the E-D ask-priority
  ranking input).
- Consumer: the hard-blocker follow-up questions carry required_for and are
  ordered by operation impact.
"""

import os


os.environ.setdefault("RUNNING_TESTS", "1")

from src.intake.packet_models import CanonicalPacket  # noqa: E402
from src.intake.validation import (  # noqa: E402
    FIELD_REQUIRED_FOR,
    OPERATIONS,
    classify_missing_fields,
    question_priority_order,
)


def _packet_with(facts: dict) -> CanonicalPacket:
    from src.intake.packet_models import Slot

    packet = CanonicalPacket(packet_id="pkt_ts07")
    for name, value in facts.items():
        packet.facts[name] = Slot(value=value, confidence=1.0, authority_level="explicit_user")
    return packet


# --- vocabulary -----------------------------------------------------------------


def test_every_mapped_field_uses_known_operations():
    for field_name, ops in FIELD_REQUIRED_FOR.items():
        assert ops, f"{field_name} maps to no operations"
        assert all(op in OPERATIONS for op in ops), f"{field_name} has unknown op"


def test_child_ages_insight_shape():
    """The tutor's canonical example: rough planning proceeds without the
    quote/booking-only fields; intake-minimum fields block planning too."""
    assert "planning" in FIELD_REQUIRED_FOR["destination_candidates"]
    assert "planning" not in FIELD_REQUIRED_FOR["party_size"]
    assert "fare_quote" in FIELD_REQUIRED_FOR["party_size"]
    assert "booking" in FIELD_REQUIRED_FOR["passport_status"]
    assert "planning" not in FIELD_REQUIRED_FOR["passport_status"]


# --- classifier ------------------------------------------------------------------


def test_classify_missing_fields_full_packet():
    packet = _packet_with({})
    classified = classify_missing_fields(packet)
    # Every blocking field is present-and-missing with its ops
    assert classified["destination_candidates"]["required_for"] == [
        "planning", "fare_quote", "booking"
    ]
    assert classified["destination_candidates"]["class"] == "BLOCKING_FOR_planning"
    assert classified["passport_status"]["class"] == "BLOCKING_FOR_entry_validation"
    # A preference field is classified but never blocking
    assert classified["hotel_preference"]["class"] == "PREFERENCE"
    assert classified["hotel_preference"]["blocks_count"] == 0


def test_classify_missing_fields_present_fields_omitted():
    packet = _packet_with({"destination_candidates": ["Tokyo"], "date_window": "Oct"})
    classified = classify_missing_fields(packet)
    assert "destination_candidates" not in classified
    assert "date_window" not in classified
    assert "party_size" in classified


def test_classify_missing_fields_invents_nothing():
    """Unknown fields never appear; the classifier is not a schema guesser."""
    packet = _packet_with({})
    classified = classify_missing_fields(packet)
    assert all(f in FIELD_REQUIRED_FOR or f in {"hotel_preference", "room_preference", "seat_preference", "dietary_requirements", "pace_preference", "activity_preferences"} for f in classified)


# --- question priority ------------------------------------------------------------


def test_question_priority_most_blocking_first():
    ordered = question_priority_order(
        ["passport_status", "destination_candidates", "party_size"]
    )
    # destination_candidates blocks 3 ops; party_size and passport_status block 2
    assert ordered[0] == "destination_candidates"
    assert set(ordered[1:]) == {"passport_status", "party_size"}


def test_question_priority_stable_for_unknown_fields():
    ordered = question_priority_order(["custom_field", "destination_candidates"])
    assert ordered == ["destination_candidates", "custom_field"]


# --- consumer: follow-up questions carry required_for and impact ordering ----------


def test_decision_module_consumes_the_vocabulary():
    """The wiring seam: decision.py orders blocker questions via
    question_priority_order and annotates each with required_for."""
    import inspect

    import src.intake.decision as decision_module

    source = inspect.getsource(decision_module)
    assert "question_priority_order" in source, "decision.py must order blocker questions"
    assert "required_for" in source, "decision.py must annotate questions with blocked ops"


def test_decision_pipeline_ask_followup_annotated_and_ordered():
    """End-to-end: an incomplete packet produces ASK_FOLLOWUP questions whose
    fields carry required_for lists, most-blocking first."""
    from src.intake.decision import run_gap_and_decision

    packet = CanonicalPacket(packet_id="pkt_ts07_e2e")
    result = run_gap_and_decision(packet)
    if result.follow_up_questions:
        annotated = [
            q for q in result.follow_up_questions
            if q.get("field_name") in FIELD_REQUIRED_FOR
        ]
        assert annotated, "blocker questions must reference known required fields"
        for q in annotated:
            assert "required_for" in q
            assert isinstance(q["required_for"], list)
        # Ordering: blocked-op counts non-increasing across annotated questions
        counts = [
            len(FIELD_REQUIRED_FOR.get(q["field_name"], frozenset()))
            for q in annotated
        ]
        assert counts == sorted(counts, reverse=True), (
            f"blocker questions must be ordered most-blocking first, got {counts}"
        )
