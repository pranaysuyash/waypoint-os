"""Sim #3 extraction truthfulness — failure-becomes-fixture (FND-0308/0309/0314/0318).

The four notes below are VERBATIM traveler language that produced wrong packets
in Sim #3. Hinglish is real customer language; every string here is embedded
exactly as the traveler wrote it. Each test pins the truthful extraction
contract: gazetteer-collision sweep tokens never become destination
candidates, a follow-up pass never evicts a confirmed destination, ordinals
never fabricate party_size, and currency-symbol budgets / cap cues parse.
"""

import pytest

from src.intake.extractors import (
    ExtractionPipeline,
    _extract_budget_flexibility,
    _extract_destination_candidates,
    _extract_party,
)
from src.intake.packet_models import SourceEnvelope

# --- Verbatim Sim #3 traveler notes (DO NOT paraphrase — Hinglish is real) ---

NOTE_1 = (
    "bhai bohot ho gaya cube ki life. main bangalore se hoon, diwali pe ghar "
    "jaana hai — jaipur side, mummy-papa ke saath 4 din. aur haan unke liye ek "
    "chhota sa varanasi add karna chahta hoon, 2 din. budget: ₹45,000 se zyada "
    "nahi total, flights included. dates flexible hain diwali ke aas paas."
)

NOTE_2 = (
    "arre ek correction — diwali nahi, chhath ke baad karte hain trip, around "
    "nov last week..."
)

NOTE_3 = (
    "ananya.rao.sim3@waypointtest.dev here. planned japan last year, vietnam "
    "this time — 10 days in march, 2 people, around $2400 excluding "
    "international flights"
)

NOTE_4 = (
    "col. arvind sen, 72, uses a wheelchair. kamala sen, 68. 45th anniversary "
    "on november 18th, 3 nights, pure veg meals only. budget around ₹90,000 "
    "total."
)

# Tokens GeoNames collides with — none of these may ever become a candidate.
FORBIDDEN_CANDIDATES = {
    "Gaya", "Din", "Aur", "Haan", "Add", "Aas", "Baad",
    "Rao", "Sim", "Sen", "Uses", "Kamala", "Manage", "Plan", "Pace", "Pure",
}


def _packet_for(text: str) -> "object":
    env = SourceEnvelope.from_freeform(text)
    return ExtractionPipeline().extract([env])


class TestFND0308DestinationFabrication:
    def test_note1_candidates_are_gazetteer_context_only(self):
        candidates, status, _raw = _extract_destination_candidates(NOTE_1)
        assert not (set(candidates) & FORBIDDEN_CANDIDATES), candidates
        assert set(candidates) <= {"Varanasi", "Jaipur"}, candidates
        assert "Varanasi" in candidates

    def test_note1_origin_fact_unchanged(self):
        packet = _packet_for(NOTE_1)
        origin = packet.facts.get("origin_city")
        assert origin is not None
        assert origin.value == "Bangalore"
        assert origin.confidence == pytest.approx(0.85)

    def test_note2_garbage_only_yields_no_candidates(self):
        candidates, status, _raw = _extract_destination_candidates(NOTE_2)
        assert "Baad" not in candidates
        assert candidates == []

    def test_note2_status_never_definite_on_garbage(self):
        packet = _packet_for(NOTE_2)
        status_slot = packet.facts.get("destination_status")
        if status_slot is not None:
            assert status_slot.value != "definite"

    def test_note3_names_and_email_tokens_not_candidates(self):
        candidates, _status, _raw = _extract_destination_candidates(NOTE_3)
        assert not ({"Rao", "Sim"} & set(candidates)), candidates
        assert "Japan" in candidates and "Vietnam" in candidates

    def test_note4_prose_tokens_not_candidates(self):
        candidates, _status, _raw = _extract_destination_candidates(NOTE_4)
        assert not ({"Sen", "Uses", "Kamala", "Manage", "Plan", "Pace", "Pure"} & set(candidates)), candidates

    def test_pipeline_note1_candidates_filtered(self):
        packet = _packet_for(NOTE_1)
        slot = packet.facts.get("destination_candidates")
        assert slot is not None
        assert not (set(slot.value) & FORBIDDEN_CANDIDATES), slot.value


class TestFND0309ReprocessMerge:
    def test_second_pass_never_evicts_confirmed_varanasi(self):
        pipeline = ExtractionPipeline()
        packet = pipeline.extract([SourceEnvelope.from_freeform(NOTE_1)])
        first_candidates = list(packet.facts["destination_candidates"].value)
        assert "Varanasi" in first_candidates

        # Reprocess path: a later freeform envelope lands on the same packet
        # (the per-envelope merge path in _extract_from_freeform).
        pipeline._extract_from_freeform(
            SourceEnvelope.from_freeform(NOTE_2), packet, stage="discovery"
        )
        merged = packet.facts["destination_candidates"].value
        assert "Varanasi" in merged, merged
        assert not (set(merged) & FORBIDDEN_CANDIDATES), merged

        status_slot = packet.facts.get("destination_status")
        if status_slot is not None and status_slot.value == "definite":
            # The invariant: 'definite' is allowed ONLY when every surviving
            # candidate is gazetteer-confirmed. A definite over garbage-only
            # candidates is the FND-0308/0309 defect.
            from src.intake.geography import is_known_city, is_known_destination

            assert all(
                is_known_city(c) or is_known_destination(c) for c in merged
            ), (merged, status_slot.value)


class TestFND0314PartySize:
    def test_note4_ordinal_never_fabricates_party(self):
        party = _extract_party(NOTE_4)
        assert party["party_size"] != 4
        # "arvind sen, 72" + "kamala sen, 68" — two named age-bearing persons
        # is the only party evidence in the note; the "45th" ordinal must not
        # leak into the count.
        assert party["party_size"] == 2

    def test_note1_parents_saath_implies_three(self):
        party = _extract_party(NOTE_1)
        assert party["party_size"] == 3  # speaker + mummy + papa

    def test_note3_two_people(self):
        party = _extract_party(NOTE_3)
        assert party["party_size"] == 2

    def test_passengers_word_counts(self):
        party = _extract_party("2 passengers flying to tokyo")
        assert party["party_size"] == 2

    def test_nothing_stated_leaves_party_absent(self):
        packet = _packet_for("i want a beach vacation in goa")
        assert packet.facts.get("party_size") is None

    def test_ordinal_guard_in_count_tokens(self):
        party = _extract_party("45th anniversary trip for the two of us")
        assert party["party_size"] == 2


class TestFND0318Budget:
    def test_note1_cap_cue_is_firm(self):
        assert _extract_budget_flexibility(NOTE_1) == "firm"

    def test_note3_dollar_budget_parsed(self):
        packet = _packet_for(NOTE_3)
        assert packet.facts.get("budget_min") is not None
        assert packet.facts["budget_min"].value == 2400
        assert packet.facts.get("budget_max") is not None
        assert packet.facts["budget_max"].value == 2400
        assert packet.facts["budget_currency"].value == "USD"

    def test_euro_symbol_budget_parsed(self):
        packet = _packet_for("thinking portugal, around €2800 for everything")
        assert packet.facts["budget_min"].value == 2800
        assert packet.facts["budget_currency"].value == "EUR"

    def test_note4_rupee_budget_still_parses(self):
        packet = _packet_for(NOTE_4)
        assert packet.facts["budget_max"].value == 90000
        assert packet.facts["budget_currency"].value == "INR"

    def test_english_cap_cues_are_firm(self):
        assert _extract_budget_flexibility("up to $5000 for the whole trip") == "firm"
        assert _extract_budget_flexibility("hard cap at 6000 total") == "firm"
        assert _extract_budget_flexibility("45000 se zyada nahi") == "firm"
