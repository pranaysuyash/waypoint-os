"""
FND-0351 (Sim #4): reassessment refresh must be lossless and must never
regress authoritative facts.

1. build_reassessment_request_from_trip falls back to the linked draft's
   customer_message when raw_input.submission.raw_note is absent (draft-flow
   trips carry the traveler's words only in the draft).
2. save_processed_trip's preserve path carries forward explicit_user/operator
   fact slots when a re-extraction lacks them (or produces a lower-authority
   value), so a refresh can never erase answered questions.
"""

from __future__ import annotations

from spine_api.persistence import _preserve_authoritative_facts
from spine_api.services.trip_lifecycle_service import build_reassessment_request_from_trip


def test_reassess_request_falls_back_to_linked_draft_note():
    trip = {
        "id": "trip_draft_flow",
        "agency_id": "ag_x",
        "raw_input": {},  # draft-flow: no submission record
        "extracted": {},
    }

    class _FakeDraft:
        id = "draft_1"
        promoted_trip_id = "trip_draft_flow"
        linked_trip_ids = []
        customer_message = "we want kerala in october, 6 nights, flying from pune."

    class _FakeDraftStore:
        @staticmethod
        def list_by_agency(agency_id, limit=500):
            assert agency_id == "ag_x"
            return [_FakeDraft()]

    import spine_api.draft_store as ds_mod

    original = getattr(ds_mod, "DraftStore", None)
    ds_mod.DraftStore = _FakeDraftStore
    try:
        req = build_reassessment_request_from_trip(trip)
    finally:
        if original is not None:
            ds_mod.DraftStore = original
    assert req["raw_note"] == "we want kerala in october, 6 nights, flying from pune."


def test_reassess_request_prefers_submission_note_over_draft():
    trip = {
        "id": "trip_with_note",
        "agency_id": "ag_x",
        "raw_input": {"submission": {"raw_note": "original note"}},
        "extracted": {},
    }
    req = build_reassessment_request_from_trip(trip)
    assert req["raw_note"] == "original note"


def test_preserve_path_keeps_answered_slot_when_reextraction_lacks_it():
    existing = {
        "extracted": {"facts": {
            "origin_city": {
                "value": "kolkata", "confidence": 1.0,
                "authority_level": "explicit_user",
                "extraction_mode": "traveler_ask_link",
            },
            "destination_candidates": {
                "value": ["Varanasi"], "confidence": 0.5,
                "authority_level": "system",
            },
        }},
    }
    fresh = {"extracted": {"facts": {
        # re-extraction reproduced destination but not the answered origin
        "destination_candidates": {
            "value": ["Varanasi"], "confidence": 0.5, "authority_level": "system",
        },
    }}}
    _preserve_authoritative_facts(fresh, existing)
    facts = fresh["extracted"]["facts"]
    assert facts["origin_city"]["value"] == "kolkata"
    assert facts["origin_city"]["authority_level"] == "explicit_user"
    assert facts["origin_city"]["carried_forward_from"] == "previous_assessment"
    assert facts["destination_candidates"]["authority_level"] == "system"


def test_preserve_path_lets_higher_authority_replacement_stand():
    existing = {
        "extracted": {"facts": {
            "origin_city": {"value": "guess", "authority_level": "system"},
        }},
    }
    fresh = {"extracted": {"facts": {
        "origin_city": {"value": "kolkata", "authority_level": "explicit_user"},
    }}}
    _preserve_authoritative_facts(fresh, existing)
    assert fresh["extracted"]["facts"]["origin_city"]["value"] == "kolkata"


def test_preserve_path_noop_without_existing_facts():
    fresh = {"extracted": {"facts": {"a": {"value": 1, "authority_level": "system"}}}}
    _preserve_authoritative_facts(fresh, {"extracted": {}})
    _preserve_authoritative_facts(fresh, None)
    assert fresh["extracted"]["facts"]["a"]["value"] == 1
