"""P-3 regression tests — occasion anchor seeds a date-window hypothesis.

Decision record: Docs/adr/DECISION_REC_P3_OCCASION_WINDOW_2026-10-25.md
An occasion anchor is a coverage constraint, not the travel window: seed
date_window as a soft hypothesis, keep the unknown blocking, never override
a real extracted window.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from intake.orchestration import run_spine_once
from intake.packet_models import SourceEnvelope

SEN_NOTE = (
    "hello, i'm booking for my parents — they don't use apps much so i manage "
    "everything. col. arvind sen, 72, uses a wheelchair and needs step-free "
    "access everywhere; my mother kamala sen, 68, has knee trouble so please "
    "plan a slow pace for her. they want varanasi for their 45th anniversary on "
    "november 18th, 3 nights, pure veg meals only. budget around ₹90,000 total."
)


def _extract(note):
    out = run_spine_once([SourceEnvelope.from_freeform(note)])
    return out.packet


def test_occasion_seeds_date_window_hypothesis():
    pkt = _extract(SEN_NOTE)
    facts = getattr(pkt, "facts", {})
    hyp = getattr(pkt, "hypotheses", {})
    assert "occasion" in facts
    dw = hyp.get("date_window") if isinstance(hyp, dict) else None
    assert dw is not None, "occasion anchor must seed a date_window hypothesis"
    assert "november 18th" in str(dw)
    assert getattr(dw, "authority_level", None) is not None
    # Unknown stays blocking — the traveler still owes exact dates.
    assert "date_window" in {u.field_name for u in (getattr(pkt, "unknowns", None) or [])}


def test_real_date_window_wins_no_seeding():
    note = (
        "we want a honeymoon in goa for our anniversary on november 18th, "
        "november 15 to november 21, beach resort."
    )
    pkt = _extract(note)
    facts = getattr(pkt, "facts", {})
    hyp = getattr(pkt, "hypotheses", {})
    assert "date_window" in facts, "real extracted window must be a FACT"
    dw_hyp = hyp.get("date_window") if isinstance(hyp, dict) else None
    assert dw_hyp is None, "hypothesis seeding must be skipped when a real window exists"
