"""Phase 3b regression tests — travelers[] attribution binding (FND-0275 /
IDEA-134, Sim #2 Family Summit).

Contract: a delegation thread produces a `travelers` packet fact with one
entry per identified speaker, each carrying that speaker's own constraints/
meals/occasion. Group facts (budget scope, party size) stay packet-level and
are never copied into a traveler.
"""

import json

from src.intake.attribution import (
    extract_speaker_segments,
)
from src.intake.extractors import ExtractionPipeline, SourceEnvelope

THREAD = (
    "hi! i'm organising a japan trip for me and 3 friends — 2 couples. "
    "budget 3.5 lakhs total including flights, hard cap.\n\n"
    "[forwarded voice note from Arjun]:\nyo it's arjun. we NEED a scuba day "
    "and osaka nightlife. budget whatever.\n\n"
    "[forwarded voice note from Meera]:\nhello, meera here. i'm jain, no "
    "onion and no garlic. terrified of heights so no cable cars. 10th "
    "anniversary (april 14th).\n\n"
    "[group chat dump]:\n[priya]: total 3.5L MAX\n[arjun]: DECEMBER skiing\n"
    "[meera]: NO HEIGHTS\n[dev]: april works, 14th covered"
)


class TestSpeakerSegmentation:
    def test_forwarded_header_binds_name(self):
        segments = extract_speaker_segments(THREAD)
        arjun = [s for s in segments if s["speaker"] == "Arjun"]
        assert arjun, "Arjun's forwarded segment missing"
        assert all("forwarded voice note from Arjun" not in s["text"].lower()
                   for s in arjun), "header text leaked into segment body"

    def test_no_bogus_speaker_names(self):
        segments = extract_speaker_segments(THREAD)
        speakers = {s["speaker"] for s in segments if s["speaker"]}
        assert not any("forwarded" in (sp or "").lower() or "chat" in (sp or "").lower()
                       for sp in speakers), f"bogus speakers: {speakers}"

    def test_chat_lines_bind_to_speakers(self):
        segments = extract_speaker_segments(THREAD)
        chat_speakers = {s["speaker"] for s in segments if s["kind"] == "chat"}
        assert {"Priya", "Arjun", "Meera", "Dev"} <= chat_speakers


class TestTravelerBinding:
    def test_travelers_fact_emitted(self):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        assert packet.facts.get("travelers") is not None

    def test_meera_gets_her_constraints(self):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        travelers = packet.facts["travelers"].value
        meera = next(t for t in travelers if t["name"] == "Meera")
        joined = " ".join(meera["constraints"]).lower()
        assert "heights" in joined
        assert meera["meal_preferences"] == "jain"
        assert meera["occasion"]["type"] == "anniversary"
        assert "14" in meera["occasion"]["date"]

    def test_four_travelers_identified(self):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        travelers = packet.facts["travelers"].value
        names = {t["name"] for t in travelers}
        assert {"Arjun", "Meera", "Priya", "Dev"} <= names

    def test_group_facts_stay_packet_level(self):
        """Budget scope/party must NOT appear inside any traveler bundle —
        they are delegation-level facts (FND-0275 attribution contract)."""
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        travelers = packet.facts["travelers"].value
        for t in travelers:
            bundle = json.dumps(t)
            assert "budget" not in bundle.lower(), "budget leaked into traveler"
            assert "party" not in bundle.lower(), "party leaked into traveler"


class TestDecisionDownstream:
    """Phase 3b downstream: per-traveler constraints surface as decision
    risk flags (advisor-visible), and occasion anchors become coverage
    requirements."""

    def test_safety_constraint_becomes_risk_flag(self):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        from src.intake.decision import generate_risk_flags
        risks = generate_risk_flags(packet, "discovery", None)
        safety = [r for r in risks if r.get("flag") == "traveler_safety_constraint"]
        assert safety, f"no traveler_safety_constraint in {[r.get('flag') for r in risks]}"
        assert "Meera" in safety[0]["message"]
        assert safety[0]["severity"] == "high"

    def test_occasion_becomes_coverage_requirement(self):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        from src.intake.decision import generate_risk_flags
        risks = generate_risk_flags(packet, "discovery", None)
        occasion = [r for r in risks if r.get("flag") == "traveler_occasion_anchor"]
        assert occasion, "no traveler_occasion_anchor risk flag"
        assert "Meera" in occasion[0]["message"]
        assert "april 14" in occasion[0]["message"]

    def test_group_facts_not_double_flagged(self):
        """Budget scope stays a packet fact — no traveler-safety flag may
        reference the group budget (attribution contract)."""
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(THREAD)])
        from src.intake.decision import generate_risk_flags
        risks = generate_risk_flags(packet, "discovery", None)
        for r in risks:
            if r.get("flag") == "traveler_safety_constraint":
                assert "3.5" not in r["message"] and "budget" not in r["message"].lower()

