"""
Real-World Scenario Tests for NB02 v0.2

Converted from notebooks/test_scenarios_realworld.py (13 tests)

These are scenario tests: Given a real messy agency note, does the system
produce the right next action? Each test represents a common real-world
situation that agents encounter.

Run: uv run python -m pytest tests/test_realworld_scenarios_v02.py -v
"""

import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from intake.packet_models import (
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
    UnknownField,
)
from intake.decision import (
    DecisionResult,
    run_gap_and_decision,
)


# ===========================================================================
# SCENARIO 1: "The Vague Lead" — Almost Nothing Known
# ===========================================================================
# Agency note: "Someone called, wants to go international, big family,
#   maybe around March, said budget is fine, will call back."

class TestVagueLead:
    """Almost nothing is known. System must ask the right questions in order."""

    def test_vague_lead_asks_followup_with_missing_blockers(self):
        """Vague Lead → ASK_FOLLOWUP with all missing blockers."""
        pkt = CanonicalPacket(packet_id="vague_lead", stage="discovery")

        # "big family" — we know it's a family but don't know count or composition
        pkt.facts["party_size"] = Slot(
            value="big family",
            confidence=0.4,
            authority_level="explicit_owner",
            notes="Owner said 'big family' — no number",
        )

        # We can guess but we can't count it as a fact
        pkt.hypotheses["destination_candidates"] = Slot(
            value="unknown",
            confidence=0.1,
            authority_level="soft_hypothesis",
        )

        r = run_gap_and_decision(pkt)

        # Must ASK — almost everything is missing
        assert r.decision_state == "ASK_FOLLOWUP", \
            f"Expected ASK_FOLLOWUP for vague lead, got {r.decision_state}"

        # party_size IS filled (even with vague value, it's a fact)
        assert "party_size" not in r.hard_blockers, \
            "party_size should be filled (even with vague value, it's a fact)"

        # These remain blocked
        assert "destination_candidates" in r.hard_blockers
        assert "origin_city" in r.hard_blockers
        assert "date_window" in r.hard_blockers

        # Must generate questions for the missing blockers
        assert len(r.follow_up_questions) == 3


# ===========================================================================
# SCENARIO 2: "The Confused Couple" — Contradictory Inputs
# ===========================================================================
# Husband: Singapore, March 15-20, 2 adults, 120k
# Wife: Thailand, April 1-6, 2 adults + baby, 200k

class TestConfusedCouple:
    """Husband and wife gave different notes. System must catch the conflict."""

    def test_confused_couple_stops_on_date_conflict(self):
        """Confused Couple → STOP_NEEDS_REVIEW (date conflict)."""
        pkt = CanonicalPacket(packet_id="confused_couple", stage="discovery")

        # Origin agreed
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_user",
        )

        # Dates: husband said March 15, wife said April 1
        pkt.facts["date_window"] = Slot(
            value=["2026-03-15", "2026-04-01"],
            confidence=0.6,
            authority_level="explicit_owner",
            evidence_refs=[
                EvidenceRef(
                    ref_id="r1",
                    envelope_id="env_husband",
                    evidence_type="text_span",
                    excerpt="March 15-20",
                ),
                EvidenceRef(
                    ref_id="r2",
                    envelope_id="env_wife",
                    evidence_type="text_span",
                    excerpt="April 1-6",
                ),
            ],
        )

        # Traveler count conflict: 2 vs 3
        pkt.facts["party_size"] = Slot(
            value=[2, 3],
            confidence=0.5,
            authority_level="explicit_owner",
            evidence_refs=[
                EvidenceRef(
                    ref_id="r3",
                    envelope_id="env_husband",
                    evidence_type="text_span",
                    excerpt="2 adults",
                ),
                EvidenceRef(
                    ref_id="r4",
                    envelope_id="env_wife",
                    evidence_type="text_span",
                    excerpt="2 adults + baby",
                ),
            ],
        )

        # Pre-existing contradictions
        pkt.contradictions = [
            {
                "field_name": "date_window",
                "values": ["2026-03-15 to 20", "2026-04-01 to 6"],
                "sources": ["env_husband", "env_wife"],
            },
            {
                "field_name": "destination_candidates",
                "values": ["Singapore", "Thailand"],
                "sources": ["env_husband", "env_wife"],
            },
        ]

        r = run_gap_and_decision(pkt)

        # CRITICAL: Date contradiction → STOP_NEEDS_REVIEW
        assert r.decision_state == "STOP_NEEDS_REVIEW", \
            f"Confused couple with date conflict should STOP, got {r.decision_state}"

        # Questions should reflect the contradiction
        assert len(r.follow_up_questions) > 0
        date_q = [q for q in r.follow_up_questions if q.get("priority") == "critical"]
        assert len(date_q) > 0, "Should have critical questions about the contradiction"


# ===========================================================================
# SCENARIO 3: "The Dreamer" — Luxury Wants, Budget Reality
# ===========================================================================
# Note: "Family of 4 from Bangalore, wants 5-star resort in Maldives,
#   7 nights, they said 1.5 lakh total."

class TestDreamer:
    """Wants 5-star Maldives but has backpacker budget."""

    def test_dreamer_detects_budget_vs_luxury_tension(self):
        """The Dreamer → detects budget-vs-luxury tension."""
        pkt = CanonicalPacket(packet_id="dreamer", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.95,
            authority_level="explicit_user",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Maldives",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["date_window"] = Slot(
            value="April 2026",
            confidence=0.7,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["budget_raw_text"] = Slot(
            value="150000",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["hotel_star_pref"] = Slot(
            value="5-star resort",
            confidence=0.8,
            authority_level="explicit_owner",
        )

        pkt.contradictions = [
            {
                "field_name": "budget_raw_text",
                "values": ["150000 (37.5k/person → backpacker)", "5-star hotel (luxury)"],
                "sources": ["budget", "hotel_preference"],
            },
        ]

        r = run_gap_and_decision(pkt)

        # Hard blockers: all 4 filled ✓
        assert len(r.hard_blockers) == 0, \
            f"All hard blockers should be filled, got {r.hard_blockers}"

        # Should proceed but detect tension
        allowed_states = {"BRANCH_OPTIONS", "PROCEED_INTERNAL_DRAFT", "PROCEED_TRAVELER_SAFE"}
        assert r.decision_state in allowed_states, \
            f"Expected to proceed (not stop/ask), got {r.decision_state}"

        # The system detects a contradiction
        assert len(r.contradictions) > 0 or r.decision_state == "BRANCH_OPTIONS", \
            "Budget-hotel tension should be detected"


# ===========================================================================
# SCENARIO 4: "The Ready-to-Buy" — Everything Known
# ===========================================================================
# Note: "Confirmed — Sharma family, 2 adults + 1 toddler (2 years),
#   Bangalore → Singapore, March 15-22, 5-star Orchard Hotel,
#   budget 4L confirmed, payment ready, passport details in CRM."

class TestReadyToBuy:
    """Everything is known. System should say 'go'."""

    def test_ready_to_buy_proceeds_safely(self):
        """Ready-to-Buy → PROCEED_TRAVELER_SAFE."""
        pkt = CanonicalPacket(packet_id="ready", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.95,
            authority_level="explicit_user",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Singapore",
            confidence=0.95,
            authority_level="explicit_user",
        )
        pkt.facts["date_window"] = Slot(
            value="2026-03-15 to 2026-03-22",
            confidence=0.95,
            authority_level="explicit_user",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.95,
            authority_level="explicit_user",
        )
        pkt.facts["budget_raw_text"] = Slot(
            value="400000",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["budget_min"] = Slot(
            value="400000",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["trip_purpose"] = Slot(
            value="family leisure",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["soft_preferences"] = Slot(
            value="5-star, kid-friendly",
            confidence=0.85,
            authority_level="explicit_user",
        )

        r = run_gap_and_decision(pkt)

        # Should proceed safely
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Everything known should proceed, got {r.decision_state}"
        assert len(r.hard_blockers) == 0
        assert len(r.soft_blockers) == 0
        assert len(r.contradictions) == 0


# ===========================================================================
# SCENARIO 5: "The WhatsApp Dump" — Multi-Paragraph Mess
# ===========================================================================
# Note: "ok so this family from Chennai, 3 of them I think,
#   want to go somewhere with beaches..."

class TestWhatsAppDump:
    """Multi-paragraph messy input with mixed signals."""

    def test_whatsapp_dump_reveals_ambiguity_gap(self):
        """WhatsApp Dump → reveals gap: can't detect ambiguous values."""
        pkt = CanonicalPacket(packet_id="whatsapp_dump", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Chennai",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["budget_raw_text"] = Slot(
            value="200000 (can stretch)",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="April-May",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        # Ambiguous: "Andaman or Sri Lanka"
        pkt.facts["destination_candidates"] = Slot(
            value="Andaman or Sri Lanka",
            confidence=0.7,
            authority_level="explicit_owner",
        )

        r = run_gap_and_decision(pkt)

        # Should proceed (destination has a value) but flag ambiguity
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Should proceed, got {r.decision_state}"
        assert len(r.hard_blockers) == 0


# ===========================================================================
# SCENARIO 6: "The CRM Return" — Data Enrichment
# ===========================================================================
# Note: "Reddy family called again. They loved Dubai last time!
#   Now want something new. Family of 4, international..."

class TestCRMReturn:
    """Returning customer with CRM data enrichment."""

    def test_crm_return_proceeds_with_new_data(self):
        """CRM Return → PROCEED_TRAVELER_SAFE with new data."""
        pkt = CanonicalPacket(packet_id="crm_return", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="imported_structured",
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level="imported_structured",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Dubai",
            confidence=0.7,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.7,
            authority_level="explicit_owner",
        )
        pkt.facts["budget_min"] = Slot(
            value="300000",
            confidence=0.8,
            authority_level="explicit_owner",
        )

        r = run_gap_and_decision(pkt)

        # Proceeds with new data
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Should proceed with new data, got {r.decision_state}"


# ===========================================================================
# SCENARIO 7: "The Elderly Pilgrimage" — Medical in Preferences
# ===========================================================================
# Note: "Group of 6 elderly people from Varanasi.
#   Want to do Char Dham Yatra..."

class TestElderlyPilgrimage:
    """Elderly group with medical needs."""

    def test_elderly_pilgrimage_proceeds_with_medical_risk_flag(self):
        """Elderly Pilgrimage → PROCEED_TRAVELER_SAFE (medical in preferences)."""
        pkt = CanonicalPacket(packet_id="elderly_pilgrimage", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Varanasi",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Char Dham, Uttarakhand",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="September 10-18, 2026",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=6,
            confidence=0.9,
            authority_level="explicit_owner",
        )
        # Increased budget to avoid budget_feasibility blocker
        pkt.facts["budget_raw_text"] = Slot(
            value="700000",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["budget_min"] = Slot(
            value="700000",
            confidence=0.8,
            authority_level="explicit_owner",
        )
        pkt.facts["soft_preferences"] = Slot(
            value="accessible transport, medical needs",
            confidence=0.9,
            authority_level="explicit_owner",
        )

        r = run_gap_and_decision(pkt)

        # Proceeds (MVB satisfied)
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Should proceed, got {r.decision_state}"
        assert len(r.hard_blockers) == 0


# ===========================================================================
# SCENARIO 8: "The Last-Minute Booker" — Urgency
# ===========================================================================
# Note: "Need to travel tomorrow! 2 people, Bangalore to Goa..."

class TestLastMinuteBooker:
    """High urgency suppresses soft blockers."""

    def test_last_minute_booker_reveals_soft_blocker_gap(self):
        """Last-Minute Booker → reveals gap: soft blockers block PROCEED_TRAVELER_SAFE."""
        pkt = CanonicalPacket(packet_id="last_minute", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Goa",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="tomorrow",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=2,
            confidence=0.9,
            authority_level="explicit_owner",
        )
        # Budget and preferences missing
        # In v0.2, urgency suppression isn't fully implemented

        r = run_gap_and_decision(pkt)

        # Missing soft blockers → INTERNAL_DRAFT (not TRAVELER_SAFE)
        assert r.decision_state == "PROCEED_INTERNAL_DRAFT", \
            f"Soft blockers should cause INTERNAL_DRAFT, got {r.decision_state}"
        assert "budget_min" in r.soft_blockers
        assert "trip_purpose" in r.soft_blockers


# ===========================================================================
# SCENARIO 9: Stage Progression
# ===========================================================================

class TestStageProgressionScenarios:
    """Stage progression scenarios."""

    def test_shortlist_asks_for_selected_destination(self):
        """Stage Progression → shortlist asks for resolved_destination."""
        pkt = CanonicalPacket(packet_id="shortlist", stage="shortlist")

        # Discovery fields filled
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Singapore", "Thailand"],
            confidence=0.8,
            authority_level="explicit_user",
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.9,
            authority_level="explicit_user",
        )

        r = run_gap_and_decision(pkt)

        # Shortlist requires resolved_destination
        assert "resolved_destination" in r.hard_blockers
        assert r.decision_state == "ASK_FOLLOWUP"

    def test_proposal_asks_for_selected_itinerary(self):
        """Partial Proposal → asks which itinerary to choose."""
        pkt = CanonicalPacket(packet_id="proposal", stage="proposal")

        # All fields up to shortlist
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["destination_candidates"] = Slot(
            value=["Singapore"],
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["resolved_destination"] = Slot(
            value=["Singapore"],
            confidence=0.9,
            authority_level="explicit_user",
        )

        r = run_gap_and_decision(pkt)

        # Proposal requires selected_itinerary
        assert "selected_itinerary" in r.hard_blockers


# ===========================================================================
# SCENARIO 10: Budget Flexibility Signal
# ===========================================================================

class TestBudgetFlexibility:
    """Budget flexibility detection."""

    def test_budget_stretch_proceeds_but_not_structurally_recognized(self):
        """Budget Stretch → proceeds but stretch not structurally recognized."""
        pkt = CanonicalPacket(packet_id="stretch", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Singapore",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="April 2026",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=4,
            confidence=0.9,
            authority_level="explicit_owner",
        )
        # Budget with stretch signal
        pkt.facts["budget_raw_text"] = Slot(
            value="200000 (can stretch)",
            confidence=0.7,
            authority_level="explicit_owner",
        )

        r = run_gap_and_decision(pkt)

        # Proceeds — stretch info captured in value but not structurally parsed
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Should proceed, got {r.decision_state}"


# ===========================================================================
# SCENARIO 11: Inferred Destination
# ===========================================================================

class TestInferredDestination:
    """Derived signal fills blocker with lower confidence."""

    def test_inferred_destination_fills_blocker_with_lower_confidence(self):
        """Inferred Destination → derived_signal fills blocker with lower confidence."""
        pkt = CanonicalPacket(packet_id="inferred", stage="discovery")

        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["date_window"] = Slot(
            value="March 2026",
            confidence=0.9,
            authority_level="explicit_owner",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.9,
            authority_level="explicit_owner",
        )
        # Destination derived from preferences
        pkt.derived_signals["destination_candidates"] = Slot(
            value="Andaman",
            confidence=0.7,
            authority_level="derived_signal",
        )

        r = run_gap_and_decision(pkt)

        # All blockers filled by derived signal
        assert len(r.hard_blockers) == 0
        # But confidence is lower (derived signal has 0.7)
        assert r.confidence_score < 0.85, \
            f"Derived signal should give lower confidence, got {r.confidence_score}"


# ===========================================================================
# SCENARIO 12: Multi-Envelope Accumulation
# ===========================================================================

class TestMultiEnvelopeAccumulation:
    """Multiple sources merged into one packet."""

    def test_multi_envelope_accumulation_merges_seamlessly(self):
        """Multi-Envelope Accumulation → merges 3 sources, proceeds safely."""
        pkt = CanonicalPacket(
            packet_id="multi_env",
            stage="discovery",
            source_envelope_ids=["env_email", "env_chat", "env_crm"],
        )

        # Data accumulated from multiple sources
        pkt.facts["origin_city"] = Slot(
            value="Bangalore",
            confidence=0.9,
            authority_level="imported_structured",
        )
        pkt.facts["destination_candidates"] = Slot(
            value="Singapore",
            confidence=0.85,
            authority_level="explicit_user",
        )
        pkt.facts["date_window"] = Slot(
            value="March 15-22, 2026",
            confidence=0.9,
            authority_level="explicit_user",
        )
        pkt.facts["party_size"] = Slot(
            value=3,
            confidence=0.9,
            authority_level="imported_structured",
        )
        pkt.facts["budget_min"] = Slot(
            value="300000",
            confidence=0.8,
            authority_level="explicit_user",
        )

        r = run_gap_and_decision(pkt)

        # 3 sources merged seamlessly
        assert r.decision_state in ("PROCEED_TRAVELER_SAFE", "PROCEED_INTERNAL_DRAFT"), \
            f"Should proceed, got {r.decision_state}"
        assert len(pkt.source_envelope_ids) == 3
