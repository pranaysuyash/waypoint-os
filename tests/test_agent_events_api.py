from __future__ import annotations

from spine_api.persistence import TEST_AGENCY_ID


def test_get_trip_agent_events_filters_and_returns_payload(session_client, monkeypatch):
    import server

    trip_id = "trip_agent_evt_1"
    agency_id = TEST_AGENCY_ID

    def _fake_get_trip(_trip_id: str):
        return {"id": trip_id, "agency_id": agency_id}

    def _fake_get_agent_events_for_trip(trip_id: str, limit: int = 100):
        assert trip_id == "trip_agent_evt_1"
        assert limit == 3
        return [
            {"type": "agent_event", "details": {"trip_id": trip_id, "event_type": "agent_decision"}},
            {"type": "agent_event", "details": {"trip_id": trip_id, "event_type": "agent_action"}},
        ]

    monkeypatch.setattr(server.TripStore, "get_trip", _fake_get_trip)
    monkeypatch.setattr(server.AuditStore, "get_agent_events_for_trip", _fake_get_agent_events_for_trip)

    resp = session_client.get(f"/trips/{trip_id}/agent-events?limit=3")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["trip_id"] == trip_id
    assert data["total"] == 2
    assert len(data["events"]) == 2
    assert data["events"][0]["details"]["event_type"] == "agent_decision"


def test_get_trip_agent_events_enforces_agency_scope(session_client, monkeypatch):
    import server

    def _fake_get_trip(_trip_id: str):
        return {"id": "trip_x", "agency_id": "other_agency"}

    monkeypatch.setattr(server.TripStore, "get_trip", _fake_get_trip)

    resp = session_client.get("/trips/trip_x/agent-events")
    assert resp.status_code == 404, resp.text


def test_get_agent_runtime_returns_registry_and_health(session_client, monkeypatch):
    from routers import agent_runtime

    class _Registry:
        def definitions(self):
            return [{"name": "follow_up_agent", "trigger_contract": "due follow-up"}]

    class _Recovery:
        is_running = True

    class _Supervisor:
        registry = _Registry()

        def health(self):
            return {"running": True, "registered_agents": ["follow_up_agent"]}

    monkeypatch.setattr(agent_runtime, "_agent_supervisor", _Supervisor())
    monkeypatch.setattr(agent_runtime, "_recovery_agent", _Recovery())

    resp = session_client.get("/agents/runtime")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["registry"][0]["name"] == "follow_up_agent"
    assert data["supervisor"]["running"] is True
    assert data["recovery_agent"]["name"] == "recovery_agent"


def test_run_agent_runtime_once_returns_results(session_client, monkeypatch):
    from routers import agent_runtime

    class _Result:
        def to_dict(self):
            return {"agent_name": "follow_up_agent", "status": "completed"}

    class _Supervisor:
        def health(self):
            return {"registered_agents": ["follow_up_agent"], "running": True}

        def run_once(self, agent_name=None):
            assert agent_name == "follow_up_agent"
            return [_Result()]

    monkeypatch.setattr(agent_runtime, "_agent_supervisor", _Supervisor())

    resp = session_client.post("/agents/runtime/run-once?agent_name=follow_up_agent")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["status"] == "completed"


def test_get_agent_runtime_events_filters_agent_events(session_client, monkeypatch):
    from routers import agent_runtime

    def _fake_get_agent_events(limit: int = 100, agent_name: str | None = None, correlation_id: str | None = None):
        assert limit == 5
        assert agent_name == "follow_up_agent"
        assert correlation_id == "corr_123"
        return [{"type": "agent_event", "details": {"agent_name": agent_name, "correlation_id": correlation_id}}]

    monkeypatch.setattr(agent_runtime.AuditStore, "get_agent_events", _fake_get_agent_events)

    resp = session_client.get("/agents/runtime/events?limit=5&agent_name=follow_up_agent&correlation_id=corr_123")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
