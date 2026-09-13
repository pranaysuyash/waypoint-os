"""Phase 3 regression tests — per-voice constraint + occasion + speaker
capture (FND-0275 / Sim #2 Family Summit, 2026-09-13).

Meera's note previously produced: hard_constraints WITHOUT the safety-critical
fear of heights, no anniversary anchor, no speaker identity, and the garbage
soft preference 'that'. These tests pin the fixed contract.
"""

from src.intake.extractors import ExtractionPipeline, SourceEnvelope

MEERA_NOTE = (
    "hello, meera here (arjun's forwarding for me too). a few important things "
    "— i'm jain, so strictly no onion and no garlic, i'll need jain or at "
    "least pure veg meals everywhere. i'm also terrified of heights so please "
    "no cable cars, no observation decks, nothing like that. we'd love a "
    "quiet ryokan for a couple of nights — it's our 10th anniversary on the "
    "trip (april 14th), so a nice anniversary dinner that day would mean a "
    "lot. and definitely NOT a party hosthome 😄 please keep a kimono photo "
    "session if possible."
)


def _extract(text):
    return ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])


def _facts(text):
    return {k: slot.value for k, slot in _extract(text).facts.items()}


class TestFearConstraints:
    def test_fear_of_heights_captured(self):
        facts = _facts(MEERA_NOTE)
        hard = facts.get("hard_constraints") or []
        assert any("heights" in c for c in hard), f"missing fear-of-heights in {hard}"

    def test_fear_object_stops_at_terminator(self):
        facts = _facts(MEERA_NOTE)
        hard = facts.get("hard_constraints") or []
        height_entry = next(c for c in hard if "heights" in c)
        assert "cable" not in height_entry and "please" not in height_entry, (
            "fear object must stop at the fear itself, not swallow the clause"
        )

    def test_fear_of_water_generic(self):
        facts = _facts("my son is afraid of deep water. budget 1 lakh, goa.")
        hard = facts.get("hard_constraints") or []
        assert any("water" in c for c in hard)


class TestOccasionAnchor:
    def test_anniversary_month_day(self):
        facts = _facts(MEERA_NOTE)
        assert facts.get("occasion") == {"type": "anniversary", "date": "april 14th"}

    def test_anniversary_day_month_order(self):
        facts = _facts(
            "it's our anniversary on 14 april, japan trip for 2, budget 3 lakhs"
        )
        occasion = facts.get("occasion")
        assert occasion and occasion["date"] == "14 april"

    def test_birthday_occasion(self):
        facts = _facts("birthday trip for mom (march 3rd), 3 people, jaipur")
        assert facts.get("occasion") == {"type": "birthday", "date": "march 3rd"}


class TestSpeakerCapture:
    def test_meera_here_captured(self):
        facts = _facts(MEERA_NOTE)
        speakers = facts.get("speakers") or []
        assert "Meera" in speakers

    def test_forwarded_from_captured(self):
        facts = _facts(
            "[forwarded voice note from Arjun]:\nyo, osaka nightlife is "
            "non-negotiable and we want decemeber skiing. budget whatever."
        )
        speakers = facts.get("speakers") or []
        assert "Arjun" in speakers

    def test_multiple_speakers_deduped(self):
        facts = _facts(
            "meera here, no heights.\nit's arjun here — pack the schedule.\n"
            "meera again: jain food."
        )
        speakers = facts.get("speakers") or []
        assert speakers.count("Meera") == 1
        assert "Arjun" in speakers


class TestSoftPreferenceFragmentGuard:
    def test_single_word_fragment_rejected(self):
        facts = _facts(MEERA_NOTE)
        soft = facts.get("soft_preferences") or []
        assert "that" not in soft

    def test_real_two_word_preference_kept(self):
        facts = _facts("we prefer boutique hotels for this trip, 2 people, goa")
        soft = facts.get("soft_preferences") or []
        assert any("boutique" in s for s in soft)
