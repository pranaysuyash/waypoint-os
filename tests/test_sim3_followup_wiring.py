"""SIM3 regression tests — FND-0313 ask-floor + FND-0316 JEV coherence.

FND-0313: packets whose only missing-data signal is BLOCKING_FOR unknowns
completed the pipeline with ``decision.follow_up_questions == []``, which
409s the T1 ask-traveler loop (``POST /followups/{trip_id}/send`` reads
``trip.decision.follow_up_questions`` via ``public_asks._open_questions``).
The decision stage must guarantee: every blocking unknown ⇒ a question.

FND-0316: the JEV ``semantic_ambiguity`` report could say PROCEED on the
same packet that carried blocking unknowns and an ESCALATED validation
verdict — two opposite epistemic verdicts on one operator surface.

Run: .venv/bin/python -m pytest tests/test_sim3_followup_wiring.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


from intake.packet_models import (
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
    SourceEnvelope,
)
from intake.validation import (
    FIELD_REQUIRED_FOR,
    blocking_unknowns,
)
from intake.decision import run_gap_and_decision
from intake.orchestration import run_spine_once


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Live-evidence note shape from _identify_unknowns (extractors.py).
def blocking_note(required_for):
    return (
        f"required_for: {', '.join(required_for)} "
        f"[BLOCKING_FOR_{required_for[0]}]"
    )


def _fact(pkt, name, value, confidence=0.9):
    pkt.facts[name] = Slot(
        value=value,
        confidence=confidence,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=[
            EvidenceRef(
                envelope_id="test", evidence_type="text_span", excerpt="test",
            )
        ],
    )


def make_fully_filled_packet(packet_id="fnd0313_full"):
    """Packet with every discovery hard + soft blocker filled.

    Phase 9 produces zero questions for this packet shape (the state machine
    routes to PROCEED_TRAVELER_SAFE modulo legacy soft_preferences), so any
    question for a blocking unknown must come from the Phase 9b floor.
    """
    pkt = CanonicalPacket(packet_id=packet_id)
    pkt.stage = "discovery"
    pkt.operating_mode = "normal_intake"
    _fact(pkt, "destination_candidates", ["Goa"])
    _fact(pkt, "origin_city", "Bangalore")
    _fact(pkt, "date_window", "March 2026")
    _fact(pkt, "party_size", 4)
    _fact(pkt, "budget_raw_text", "5 lakh")
    _fact(pkt, "budget_min", 500000)
    _fact(pkt, "trip_purpose", "family vacation")
    return pkt


def add_live_unknowns(pkt):
    """Reproduce the SIM3 evidence: 3 blocking unknowns on a clean packet."""
    pkt.add_unknown(
        "date_window", "not_present_in_source",
        notes=blocking_note(["planning", "fare_quote", "booking"]),
    )
    pkt.add_unknown(
        "trip_purpose", "not_present_in_source",
        notes=blocking_note(["fare_quote", "booking"]),
    )
    pkt.add_unknown(
        "party_size", "not_present_in_source",
        notes=blocking_note(["fare_quote", "booking"]),
    )
    return pkt


# ---------------------------------------------------------------------------
# FND-0313: decision ask-floor
# ---------------------------------------------------------------------------

class TestFollowUpQuestionFloor:
    def test_blocking_unknowns_get_questions_even_when_branches_dont_fire(self):
        """Fail-before: Phase 9 emitted [] for the unknown fields; floor fills."""
        pkt = add_live_unknowns(make_fully_filled_packet())
        result = run_gap_and_decision(pkt)

        names = [q["field_name"] for q in result.follow_up_questions]
        assert {"date_window", "trip_purpose", "party_size"} <= set(names), (
            f"Blocking unknowns must each get a question; got {names}"
        )
        # No duplicate asks: one question per field.
        assert len(names) == len(set(names))

    def test_floor_is_data_only_and_matches_primary_question_shape(self):
        pkt = add_live_unknowns(make_fully_filled_packet())
        result = run_gap_and_decision(pkt)

        by_name = {q["field_name"]: q for q in result.follow_up_questions}
        q = by_name["date_window"]
        # Exact key set of the primary hard-blocker append site (decision.py).
        assert set(q.keys()) == {
            "field_name", "question", "priority", "can_infer",
            "inference_confidence", "suggested_values", "required_for",
        }
        assert q["question"], "question text must be non-empty"
        # Floor never flips the decision state.
        assert result.decision_state != "STOP_NEEDS_REVIEW"

    def test_priorities_mapped_and_high_asks_first(self):
        pkt = make_fully_filled_packet(packet_id="fnd0313_priority")
        pkt.add_unknown(
            "date_window", "not_present_in_source",
            notes=blocking_note(["planning", "fare_quote", "booking"]),
        )
        # Notes-only planning blocker → medium priority.
        pkt.add_unknown(
            "activity_preferences", "not_present_in_source",
            notes=blocking_note(["planning"]),
        )
        result = run_gap_and_decision(pkt)

        by_name = {q["field_name"]: q for q in result.follow_up_questions}
        assert by_name["date_window"]["priority"] == "high"
        assert by_name["activity_preferences"]["priority"] == "medium"
        names = [q["field_name"] for q in result.follow_up_questions]
        assert names.index("date_window") < names.index("activity_preferences"), (
            "high-priority asks must precede medium-priority asks"
        )

    def test_floor_capped_at_six_questions(self):
        pkt = make_fully_filled_packet(packet_id="fnd0313_cap")
        vocab = sorted(FIELD_REQUIRED_FOR)  # 8 decision-required fields
        for field_name in vocab:
            pkt.add_unknown(
                field_name, "not_present_in_source",
                notes=blocking_note(sorted(FIELD_REQUIRED_FOR[field_name]) or ["planning"]),
            )
        result = run_gap_and_decision(pkt)

        names = [q["field_name"] for q in result.follow_up_questions]
        floor_names = [n for n in names if n in FIELD_REQUIRED_FOR]
        assert len(floor_names) <= 6, f"cap violated: {len(floor_names)} questions"
        # Stable order: the first 6 vocabulary fields survive the cap.
        assert floor_names == vocab[:6]
        assert "trip_purpose" not in names
        assert "visa_status" not in names

    def test_floor_does_not_duplicate_primary_branch_questions(self):
        """Bare packet: hard-blocker branch already asks; floor must dedupe."""
        pkt = CanonicalPacket(packet_id="fnd0313_dedupe")
        pkt.stage = "discovery"
        pkt.operating_mode = "normal_intake"
        pkt.add_unknown(
            "date_window", "not_present_in_source",
            notes=blocking_note(["planning", "fare_quote", "booking"]),
        )
        pkt.add_unknown(
            "origin_city", "not_present_in_source",
            notes=blocking_note(["fare_quote", "booking"]),
        )
        result = run_gap_and_decision(pkt)

        names = [q["field_name"] for q in result.follow_up_questions]
        assert names.count("date_window") == 1
        assert names.count("origin_city") == 1

    def test_detector_matches_decision_stage_detection(self):
        pkt = add_live_unknowns(make_fully_filled_packet())
        detected = blocking_unknowns(pkt)
        assert {d["field_name"] for d in detected} == {
            "date_window", "trip_purpose", "party_size",
        }
        assert all(d["priority"] == "high" for d in detected)
        # A clean packet (facts only) detects nothing.
        assert blocking_unknowns(make_fully_filled_packet("fnd0313_clean")) == []


# ---------------------------------------------------------------------------
# FND-0316: JEV coherence guard
# ---------------------------------------------------------------------------

class TestJevCoherenceGuard:
    def _spine_run(self, monkeypatch, action, text):
        # Patch the module object orchestration actually imports
        # (absolute `src.intake...` import inside run_spine_once).
        from src.intake import ambiguity_classifier as ac

        report = ac.AmbiguityReport(
            action=action,
            confidence=0.79,
            source="jev",
            reasoning="[jev] destination_clarity=True",
        )
        monkeypatch.setattr(
            ac.IntakeAmbiguityClassifier, "evaluate", lambda self, text: report,
        )
        envelope = SourceEnvelope.from_freeform(text)
        return run_spine_once([envelope])

    def test_jev_proceed_downgraded_when_blocking_unknowns_present(self, monkeypatch):
        text = (
            "Trip to Goa in March 2026 for 4 people, budget 5 lakh."
        )
        result = self._spine_run(monkeypatch, "PROCEED", text)
        meta = result.packet.metadata.get("semantic_ambiguity")

        blocking = blocking_unknowns(result.packet)
        assert blocking, "test precondition: run must carry blocking unknowns"
        assert meta["action"] != "PROCEED"
        assert meta["action"] == "PROCEED_WITH_ASKS"
        assert "coherence_override=blocking_unknowns:[" in meta["reasoning"]
        assert "origin_city" in meta["reasoning"] or any(
            d["field_name"] in meta["reasoning"] for d in blocking
        )
        # Confidence is never touched by the override.
        assert meta["confidence"] == 0.79

    def test_jev_proceed_unchanged_on_clean_packet(self, monkeypatch):
        text = (
            "Family of 4 from Bangalore going to Goa in March 2026 for a "
            "family vacation, budget 5 lakh, planning a trip."
        )
        result = self._spine_run(monkeypatch, "PROCEED", text)
        meta = result.packet.metadata.get("semantic_ambiguity")

        assert blocking_unknowns(result.packet) == [], (
            "test precondition: packet must be clean"
        )
        assert meta["action"] == "PROCEED"
        assert "coherence_override" not in (meta.get("reasoning") or "")

    def test_jev_ask_followup_never_upgraded(self, monkeypatch):
        text = "Trip to Goa in March 2026 for 4 people, budget 5 lakh."
        result = self._spine_run(monkeypatch, "ASK_FOLLOWUP", text)
        meta = result.packet.metadata.get("semantic_ambiguity")

        assert meta["action"] == "ASK_FOLLOWUP"
        assert "coherence_override" not in (meta.get("reasoning") or "")
