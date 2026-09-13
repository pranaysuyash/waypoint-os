"""Regression tests for the Sim #2 multi-voice extraction failures.

Thread = the verbatim Family Summit notes (Docs/sims/personas/
SIM2_DELEGATION_PERSONAS_2026-09-12.md). These pin the realignment Phase 1
contract: budget scope is amount-scoped and explicit-total-precedence
(FND-0273), so a number-free note can never flip the scope.
"""

import re

from src.intake.extractors import (
    ExtractionPipeline,
    SourceEnvelope,
    _extract_budget_scope,
    _budget_scope_sentences,
    _side_is_trip_compound,
    _is_likely_origin,
)

_AMOUNT_PROBE = re.compile(r"[$€£₹]|\d")


PRIYA = (
    "hi! i'm organising a japan trip for me and 3 friends — 2 couples. we're "
    "thinking spring next year for cherry blossoms but dates are flexible. "
    "budget is 3.5 lakhs total for everyone INCLUDING flights, that's my hard "
    "cap. we want to do tokyo + kyoto, maybe osaka. one cooking class "
    "somewhere would be amazing."
)
ARJUN = (
    "yo it's arjun — priya's forwarding this. honestly spring is overrated and "
    "everyone goes. december = cheaper flights AND we can ski in hakuba. also "
    "we NEED a scuba day (okinawa side trip?) and osaka nightlife is "
    "non-negotiable, dotonbori till 3am. let's pack the schedule, we can sleep "
    "when we're dead. budget whatever, we'll manage."
)
MEERA = (
    "hello, meera here. i'm jain, so strictly no onion and no garlic. i'm "
    "terrified of heights so no cable cars. quiet ryokan — it's our 10th "
    "anniversary (april 14th)."
)
DEV = (
    "we can shift the dates by a week either side if it saves 40k or more; "
    "meera's anniversary is april 14 so the trip needs to COVER that date. "
    "2 separate double rooms please. one slow mid-week."
)
DUMP = (
    "[priya]: ok updates — total is still 3.5L MAX\n"
    "[arjun]: DECEMBER. skiing. just saying\n"
    "[meera]: NO HEIGHTS, jain food\n"
    "[dev]: april works, 14th covered\n"
    "[priya]: what does each of us owe??"
)


class TestBudgetScopeAmountScoping:
    def test_full_thread_keeps_explicit_total(self):
        """The exact Sim #2 failure: accumulated thread must stay total."""
        thread = "\n\n".join([PRIYA, ARJUN, MEERA, DEV, DUMP])
        assert _extract_budget_scope(thread) == "total"

    def test_number_free_note_cannot_flip_scope(self):
        assert _extract_budget_scope(PRIYA) == "total"
        assert _extract_budget_scope(PRIYA + "\n\n" + ARJUN) == "total"

    def test_explicit_total_outranks_later_per_person(self):
        thread = (
            "budget is 2 lakhs total for the trip.\n"
            "later thought: 500 usd per person sounds right for activities."
        )
        assert _extract_budget_scope(thread) == "total"

    def test_per_person_with_amount_still_works(self):
        assert _extract_budget_scope("budget around 3.5k USD each") == "per_person"

    def test_per_night_with_amount_still_works(self):
        assert _extract_budget_scope("hotel is 5000 INR per night for 4 nights") == "per_night"

    def test_no_amount_anywhere_is_unknown(self):
        assert _extract_budget_scope("budget whatever, we'll manage") == "unknown"

    def test_sentence_splitter_keeps_only_amount_segments(self):
        segments = _budget_scope_sentences(PRIYA + "\n\n" + ARJUN)
        # Pure-chatter segments (no digit/currency at all) are dropped —
        # "budget whatever, we'll manage" must never reach scope evaluation.
        assert all(_AMOUNT_PROBE.search(s) for s in segments)
        assert not any("budget whatever" in s for s in segments)

    def test_lakhs_marker_counts_as_amount(self):
        segments = _budget_scope_sentences("budget is 3.5 lakhs total including flights")
        assert len(segments) == 1


class TestOriginCueGuard:
    """Phase 2 (FND-0273 residual / Sim #2 okinawa-origin): 'X side trip' is a
    noun compound proposing a DESTINATION, never an origin postposition. Both
    extraction paths (candidate classification + Hinglish slot setter) must
    respect the distinction. Real Hinglish postpositions must survive."""

    def test_side_trip_not_origin_candidate(self):
        assert _is_likely_origin(
            "we NEED a scuba day (okinawa side trip?)", "okinawa"
        ) is False

    def test_side_visit_not_origin_candidate(self):
        assert _is_likely_origin("maybe a goa side visit", "goa") is False

    def test_hinglish_side_postposition_still_origin(self):
        assert _is_likely_origin(
            "we are bangalore side, plan something", "bangalore"
        ) is True

    def test_from_phrase_still_origin(self):
        assert _is_likely_origin("flying from london", "london") is True

    def test_se_postposition_still_origin(self):
        assert _is_likely_origin("bangalore se niklenge", "bangalore") is True

    def test_side_is_trip_compound_helper(self):
        assert _side_is_trip_compound(" trip? and osaka")
        assert _side_is_trip_compound(" visit planned")
        assert not _side_is_trip_compound(", we'll manage")

    def test_pipeline_no_origin_from_side_trip_thread(self):
        """The exact Sim #2 thread shape must not fabricate Origin City."""
        thread = (
            "hi! i'm organising a japan trip for me and 3 friends — 2 couples. "
            "we want to do tokyo + kyoto. budget is 3.5 lakhs total including "
            "flights.\n\n[forwarded voice note from Arjun]:\nyo it's arjun. "
            "also we NEED a scuba day (okinawa side trip?) and osaka nightlife "
            "is non-negotiable."
        )
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(thread)])
        origin = packet.facts.get("origin_city")
        assert origin is None or not origin.value

    def test_pipeline_hinglish_origin_end_to_end(self):
        """Real Hinglish origin must survive the guard end-to-end."""
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(
            "bangalore se manali chahiye, 2 weeks, budget 1 lakh"
        )])
        origin = packet.facts.get("origin_city")
        assert origin is not None and str(origin.value).lower() == "bangalore"


class TestAmbiguityVerbatimInvariant:
    """Phase 4b (FND-0276): ambiguity raw quotes must be verbatim substrings
    of the input — the '5 lakhs' corruption class must stay dead."""

    def _amb_raws(self, text):
        packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])
        return [(a.ambiguity_type, str(getattr(a, "raw_value", ""))) for a in packet.ambiguities]

    def test_sim2_note1_ambiguities_verbatim_or_labeled(self):
        """FND-0276 invariant: an ambiguity raw is either a case-insensitive
        verbatim input substring or explicitly labeled as derived — never
        synthesized text presented as a quotation."""
        thread_lower = PRIYA.lower()
        for amb_type, raw in self._amb_raws(PRIYA):
            ok = raw == "" or raw.lower() in thread_lower or raw.startswith("derived from")
            assert ok, (
                f"unlabeled non-verbatim ambiguity raw for {amb_type}: {raw!r}"
            )

    def test_d02_does_not_fire_on_explicit_inclusion(self):
        ambs = self._amb_raws(PRIYA)
        assert not any(t == "flights_inclusiveness_unknown" for t, _ in ambs)

    def test_d02_fires_verbatim_on_unresolved(self):
        text = "budget around 3.5 lakhs, not sure if that includes flights, japan for 4"
        ambs = [
            (t, raw) for t, raw in self._amb_raws(text)
            if t == "flights_inclusiveness_unknown"
        ]
        assert ambs, "unresolved flights scope must fire the ambiguity"
        for _, raw in ambs:
            assert raw in text, f"raw not verbatim: {raw!r}"
