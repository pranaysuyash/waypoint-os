"""
tests/test_draft_promote_invariant.py — PA-39: promotion is single-shot.

The store owns the invariant: an already-promoted draft is returned unchanged
when re-promoted to the SAME trip (idempotent) and refused with ValueError when
a second promote targets a DIFFERENT trip — the original draft → trip linkage
is never silently overwritten.
"""

import pytest

from spine_api.draft_store import DraftStore


def _make_draft(prefix: str) -> str:
    draft = DraftStore.create(
        agency_id="system",
        created_by="pa39_test",
        name=f"PA-39 invariant draft {prefix}",
        customer_message="test",
    )
    return draft.id


def test_first_promote_sets_linkage():
    draft_id = _make_draft("first")
    promoted = DraftStore.promote(draft_id, "trip_aaa")
    assert promoted.status == "promoted"
    assert promoted.promoted_trip_id == "trip_aaa"


def test_same_trip_repromote_is_idempotent():
    draft_id = _make_draft("idem")
    DraftStore.promote(draft_id, "trip_aaa")
    again = DraftStore.promote(draft_id, "trip_aaa")
    assert again.status == "promoted"
    assert again.promoted_trip_id == "trip_aaa"


def test_different_trip_repromote_is_refused_and_linkage_preserved():
    draft_id = _make_draft("refuse")
    DraftStore.promote(draft_id, "trip_aaa")
    with pytest.raises(ValueError, match="already promoted"):
        DraftStore.promote(draft_id, "trip_bbb")
    after = DraftStore.get(draft_id)
    assert after.promoted_trip_id == "trip_aaa", "original linkage must survive the refusal"
    assert after.status == "promoted"
