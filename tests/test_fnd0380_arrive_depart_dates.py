"""FND-0380 regression tests — arrive/depart date phrasing.

"arriving november 15 leaving november 21" (and its abbreviated,
comma-crossed, check-in/out, and departure-first variants) is the dominant
REPLY shape when travelers answer exact dates. All must parse to an ordered
(tentative) window; pre-existing range lanes must be unaffected.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from intake.extractors import _extract_dates


def test_full_month_arrive_depart():
    assert _extract_dates("arriving november 15 leaving november 21") == (
        "arriving november 15 leaving november 21", "2026-11-15", "2026-11-21", "tentative",
    )


def test_abbreviated_comma_crossed_reply():
    # The exact SIM3-D traveler-answer shape.
    assert _extract_dates("arriving nov 16 evening, leaving nov 19 morning") == (
        "arriving nov 16 evening, leaving nov 19", "2026-11-16", "2026-11-19", "tentative",
    )


def test_check_in_out_variant():
    assert _extract_dates("check in november 15, check out november 19") == (
        "check in november 15, check out november 19", "2026-11-15", "2026-11-19", "tentative",
    )


def test_departure_first_is_calendar_ordered():
    assert _extract_dates("arriving november 21 leaving november 15")[1:] == (
        "2026-11-15", "2026-11-21", "tentative",
    )


def test_preexisting_lanes_unaffected():
    assert _extract_dates("november 15 to november 21")[1:] == (
        "2026-11-15", "2026-11-21", "tentative",
    )
    assert _extract_dates("dates around 9th to 14th feb")[1:] == (
        "2026-02-09", "2026-02-14", "tentative",
    )
    assert _extract_dates("july 10 to july 16")[1:] == (
        "2026-07-10", "2026-07-16", "tentative",
    )
    assert _extract_dates("arriving sept 5 leaving sept 9")[1:] == (
        "2026-09-05", "2026-09-09", "tentative",
    )
