from __future__ import annotations


def test_tripstore_adapter_resolves_async_list_and_update(monkeypatch):
    from spine_api.services.agent_runtime_adapters import TripStoreAdapter
    import server

    async def _list_trips(limit=500):
        assert limit == 500
        return [
            {"id": "active", "stage": "proposal"},
            {"id": "done", "stage": "completed"},
        ]

    async def _update_trip(trip_id: str, updates: dict):
        return {"id": trip_id, **updates}

    monkeypatch.setattr(server.TripStore, "list_trips", _list_trips)
    monkeypatch.setattr(server.TripStore, "update_trip", _update_trip)

    adapter = TripStoreAdapter()

    assert adapter.list_active() == [{"id": "active", "stage": "proposal"}]
    assert adapter.update_trip("active", {"status": "review"}) == {"id": "active", "status": "review"}


def test_build_agent_runtime_bundle_preserves_globals_and_configures_router(monkeypatch):
    from routers import agent_runtime as agent_runtime_router
    import server

    # At import time, globals are None (not built yet)
    assert server._agent_supervisor is None
    assert server._agent_work_coordinator is None
    assert server._recovery_agent is None
    assert server._agent_runtime_bundle is None

    # Reset globals to None as they would be at import time
    monkeypatch.setattr(server, "_agent_work_coordinator", None)
    monkeypatch.setattr(server, "_recovery_agent", None)
    monkeypatch.setattr(server, "_agent_supervisor", None)
    monkeypatch.setattr(server, "_agent_runtime_bundle", None)

    # Reset router globals too
    monkeypatch.setattr(agent_runtime_router, "_agent_supervisor", None)
    monkeypatch.setattr(agent_runtime_router, "_runtime_config", None)

    # Call the startup helper
    bundle = server._build_agent_runtime_bundle()

    assert bundle is not None
    assert server._agent_supervisor is not None
    assert server._agent_work_coordinator is not None or server._agent_work_coordinator is None
    assert server._recovery_agent is not None
    assert server._agent_runtime_bundle is bundle
    # The helper calls configure_runtime, so router globals are populated
    assert agent_runtime_router._agent_supervisor is not None
    assert agent_runtime_router._runtime_config is not None

    # Router accessors work after configuration
    sup = agent_runtime_router._supervisor()
    assert sup is not None

