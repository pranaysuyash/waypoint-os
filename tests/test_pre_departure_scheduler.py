"""T12: pre-departure briefing scheduler — D-7/D-3/D-1 triggers.

Covers: stage-window computation (due/idempotent/past-departure), generation
via the canonical cadence engine, trip artifact write-back, feature gating
(off by default), and honest delivery labeling.
"""

from datetime import date, timedelta


from spine_api.services import pre_departure_scheduler as sched
from spine_api.services.pre_departure_scheduler import stages_due


def _trip(departure_iso: str, fired=None):
    return {
        "id": "trip_sched_1",
        "agency_id": "agency_sched",
        "traveler_name": "Meera Sharma",
        "status": "active",
        "start_date": departure_iso,
        "packet": {"destination_country_code": "IT"},
        "pre_departure_briefings": ({"stages_fired": fired} if fired else None),
    }


def test_stages_due_windows():
    today = date(2026, 10, 25)
    # D-7 window: exactly 7 days out
    assert stages_due(_trip((today + timedelta(days=7)).isoformat()), today) == ["D_MINUS_7"]
    # 5 days out: D-7 already due, D-3 not yet
    assert stages_due(_trip((today + timedelta(days=5)).isoformat()), today) == ["D_MINUS_7"]
    # 2 days out: D-7 and D-3
    assert stages_due(_trip((today + timedelta(days=2)).isoformat()), today) == ["D_MINUS_7", "D_MINUS_3"]
    # departure day: all three
    assert stages_due(_trip(today.isoformat()), today) == ["D_MINUS_7", "D_MINUS_3", "D_MINUS_1"]
    # beyond the window
    assert stages_due(_trip((today + timedelta(days=30)).isoformat()), today) == []


def test_idempotent_per_stage():
    today = date(2026, 10, 25)
    trip = _trip((today + timedelta(days=1)).isoformat(), fired=["D_MINUS_7", "D_MINUS_3"])
    assert stages_due(trip, today) == ["D_MINUS_1"]


def test_past_departure_never_fires():
    today = date(2026, 10, 25)
    assert stages_due(_trip((today - timedelta(days=1)).isoformat()), today) == []


def test_unknown_departure_never_fires():
    assert stages_due(_trip("TBD"), date(2026, 10, 25)) == []


def test_fire_writes_artifact(monkeypatch):
    today = date.today()
    trip = _trip((today + timedelta(days=1)).isoformat())
    updates = {}

    import spine_api.services.pre_departure_scheduler as sched

    import spine_api.persistence as P

    monkeypatch.setattr(
        P.TripStore,
        "update_trip_for_agency",
        lambda trip_id, agency_id, fields: updates.update(fields) or trip,
    )
    monkeypatch.setattr(sched, "_fired_state", {})

    artifact = sched.fire_due_briefings(trip, "agency_sched")
    assert artifact is not None
    assert set(artifact["stages_fired"]) == {"D_MINUS_7", "D_MINUS_3", "D_MINUS_1"}
    # Honest delivery label: nothing was sent.
    assert artifact["delivery"] == "advisor_manual"
    # Artifact persisted to the trip.
    assert updates["pre_departure_briefings"]["stages_fired"] == artifact["stages_fired"]
    # Second fire on the same trip: nothing due.
    assert sched.fire_due_briefings(trip, "agency_sched") is None


def test_generation_failure_is_contained(monkeypatch):
    today = date.today()
    trip = _trip((today + timedelta(days=1)).isoformat())

    import spine_api.services.pre_departure_scheduler as sched

    class _Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("engine down")

    monkeypatch.setattr(sched, "_fired_state", {})
    import src.briefing.pre_departure_cadence as cadence

    monkeypatch.setattr(cadence.PreDepartureCadenceEngine, "generate_briefing", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("engine down")))

    # Returns None (nothing recorded), never raises.
    assert sched.fire_due_briefings(trip, "agency_sched") is None


def test_scheduler_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PRE_DEPARTURE_SCHEDULER", raising=False)
    assert sched.scheduler_enabled() is False
    monkeypatch.setenv("PRE_DEPARTURE_SCHEDULER", "1")
    assert sched.scheduler_enabled() is True
