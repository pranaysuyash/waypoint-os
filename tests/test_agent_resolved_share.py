"""R2-F agent-resolved-share KPI (2026-11-03).

Resolved = decision produced AND left the decision stage (proposal link or
recorded review action). Agent-resolved = no operator review action ever
touched it. None (not 0%) when nothing has resolved yet — a share without
resolved trips is a fabricated number.
"""

from __future__ import annotations

import spine_api.routers.inbox as inbox_router


def _trip(trip_id: str, *, decision: bool, proposal: bool, reviewed: bool) -> dict:
    return {
        "id": trip_id,
        "destination": "Bali",
        "decision": {"rationale": {"confidence": 0.8}} if decision else None,
        "proposal_link_token": "tok" if proposal else None,
        "analytics": {
            "review_metadata": {"reviewed_at": "2026-11-04T00:00:00Z"} if reviewed else {},
        },
    }


def _wire(monkeypatch, trips):
    monkeypatch.setattr(inbox_router.TripStore, "count_trips", lambda *a, **k: len(trips))
    monkeypatch.setattr(
        inbox_router.TripStore,
        "list_trip_summaries",
        lambda *a, **k: trips,
    )
    monkeypatch.setattr(
        inbox_router.TripStore,
        "list_trips",
        lambda *a, **k: trips,
    )


def test_share_none_when_nothing_resolved(session_client, monkeypatch):
    _wire(monkeypatch, [_trip("t1", decision=False, proposal=False, reviewed=False)])
    payload = session_client.get("/inbox/stats").json()
    assert payload["resolvedCount"] == 0
    assert payload["agentResolvedShare"] is None


def test_agent_resolved_share_counts_unreviewed_progressed_trips(session_client, monkeypatch):
    _wire(
        monkeypatch,
        [
            _trip("a", decision=True, proposal=True, reviewed=False),   # agent-resolved
            _trip("b", decision=True, proposal=True, reviewed=True),    # operator-resolved
            _trip("c", decision=False, proposal=False, reviewed=False), # not resolved
            _trip("d", decision=True, proposal=False, reviewed=True),   # left stage via review action
        ],
    )
    payload = session_client.get("/inbox/stats").json()
    assert payload["resolvedCount"] == 3
    assert payload["agentResolvedCount"] == 1
    assert payload["agentResolvedShare"] == round(1 / 3, 4)
    assert payload["agentResolvedShareBasis"] == "paged_total"
