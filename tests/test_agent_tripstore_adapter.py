from __future__ import annotations


def test_tripstore_adapter_resolves_async_list_and_update(monkeypatch):
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

    adapter = server._TripStoreAdapter()

    assert adapter.list_active() == [{"id": "active", "stage": "proposal"}]
    assert adapter.update_trip("active", {"status": "review"}) == {"id": "active", "status": "review"}
