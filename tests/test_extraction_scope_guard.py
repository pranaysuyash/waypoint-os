"""Regression tests for the Sim #2 multi-voice extraction failures.

Thread = the verbatim Family Summit notes (Docs/sims/personas/
SIM2_DELEGATION_PERSONAS_2026-09-12.md). These pin the realignment Phase 1
contract: budget scope is amount-scoped and explicit-total-precedence
(FND-0273), so a number-free note can never flip the scope.
"""

import re

from src.intake.extractors import _extract_budget_scope, _budget_scope_sentences

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
