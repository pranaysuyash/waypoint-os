"""FND-0376 regression tests — precedence + operator tombstones.

Decision record: Docs/adr/DECISION_REC_FND0376_DESTINATION_TOMBSTONES_2026-10-25.md

A reprocess's fresh re-extraction must not resurrect destination candidates
an operator removed/displaced, UNLESS the traveler's own new note re-asserts
that candidate (customer > operator).

Run: .venv/bin/python -m pytest tests/test_fnd0376_destination_tombstones.py -v
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spine_api.persistence import _preserve_authoritative_facts


def _slot(value, authority="explicit_user"):
    return {"value": value, "confidence": 1.0, "authority_level": authority}


def _existing(dest_value, tombstones=None):
    return {
        "extracted": {"facts": {"destination_candidates": _slot(dest_value)}},
        "destination_tombstones": tombstones or [],
    }


def _serializable(new_candidates, note=None):
    trip = {"extracted": {"facts": {"destination_candidates": _slot(new_candidates)}}}
    if note:
        trip["raw_input"] = {"submission": {"raw_note": note}}
    return trip


def test_tombstoned_candidate_filtered_from_reextraction():
    existing = _existing(["Varanasi"], tombstones=["Baad"])
    fresh = _serializable(["Baad", "Varanasi"])
    _preserve_authoritative_facts(fresh, existing)
    assert fresh["extracted"]["facts"]["destination_candidates"]["value"] == ["Varanasi"]


def test_traveller_reassertion_voids_tombstone():
    existing = _existing(["Varanasi"], tombstones=["Baad"])
    fresh = _serializable(["Baad", "Varanasi"], note="actually baad also works for us")
    _preserve_authoritative_facts(fresh, existing)
    assert "Baad" in fresh["extracted"]["facts"]["destination_candidates"]["value"]
    assert existing["destination_tombstones"] == []


def test_no_tombstones_leaves_fnd0309_behavior_untouched():
    existing = _existing(["Varanasi"])
    fresh = _serializable(["Baad", "Varanasi"])
    _preserve_authoritative_facts(fresh, existing)
    assert fresh["extracted"]["facts"]["destination_candidates"]["value"] == ["Baad", "Varanasi"]


def test_case_insensitive_tombstone_match():
    existing = _existing(["Varanasi"], tombstones=["BAAD"])
    fresh = _serializable(["baad", "Varanasi"])
    _preserve_authoritative_facts(fresh, existing)
    assert fresh["extracted"]["facts"]["destination_candidates"]["value"] == ["Varanasi"]


def test_carried_forward_slot_also_tombstone_filtered():
    # Re-extraction lacks destination_candidates entirely; the operator slot
    # carries forward — tombstones must not break that path (no candidates in
    # fresh extraction means nothing to filter; carry-forward runs as before).
    existing = {
        "extracted": {
            "facts": {
                "destination_candidates": _slot(["Varanasi"], authority="operator"),
            }
        },
        "destination_tombstones": ["Baad"],
    }
    fresh = {"extracted": {"facts": {}}}
    _preserve_authoritative_facts(fresh, existing)
    assert fresh["extracted"]["facts"]["destination_candidates"]["value"] == ["Varanasi"]
