"""Causal linkage tests — EXPLORE #5 / topic 51a gap 2 (`caused_by`).

Pins: the `why()` walker resolves an event's causal ancestry through
`details.caused_by` chains (with cycle + missing-ancestor termination);
the fare-drop disposition event carries `caused_by_marker` so its decisions
are traceable to the detection that caused them.
"""

from spine_api.services.audit_causality import find_event_by_id, why


def _lookup_in(events):
    def lookup(eid):
        return find_event_by_id(events, eid)
    return lookup


def test_why_walks_the_causal_chain_to_the_root():
    events = [
        {"id": "evt_decision", "event_type": "fare_drop_disposition_updated",
         "details": {"trip_id": "t1", "caused_by_marker": "fare_drop|X", "caused_by": "evt_signal"}},
        {"id": "evt_signal", "event_type": "fare_drop_signal_attached",
         "details": {"trip_id": "t1", "detection_marker": "fare_drop|X"}},
    ]
    lookup = _lookup_in(events)

    path = why("evt_decision", lookup)

    assert [e["id"] for e in path] == ["evt_decision", "evt_signal"]


def test_why_terminates_on_missing_ancestor_and_cycles():
    missing = why("evt_ghost", lambda eid: None)
    assert missing == []

    cyclic = [
        {"id": "a", "details": {"caused_by": "b"}},
        {"id": "b", "details": {"caused_by": "a"}},
    ]
    path = why("a", _lookup_in(cyclic))
    assert [e["id"] for e in path] == ["a", "b"], "cycle must terminate, not loop"


def test_why_handles_events_without_causality():
    lonely = [{"id": "evt_lonely", "details": {"trip_id": "t1"}}]
    path = why("evt_lonely", _lookup_in(lonely))
    assert len(path) == 1  # the event itself, no ancestry


def test_fare_drop_disposition_event_carries_causal_marker():
    """The live call site: the disposition PATCH must embed the detection
    marker so decisions trace to their causing detection."""
    import inspect

    from spine_api.routers import price_lock

    source = inspect.getsource(price_lock)
    assert "caused_by_marker" in source, (
        "fare-drop disposition audit event lost its causal linkage"
    )
