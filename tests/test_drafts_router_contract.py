from __future__ import annotations


def test_drafts_router_lists_frontend_consumed_summary_shape(session_client):
    response = session_client.get("/api/drafts?limit=1")

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["items"], list)
    assert isinstance(payload["total"], int)
    if payload["items"]:
        assert set(payload["items"][0]) >= {
            "draft_id",
            "name",
            "status",
            "stage",
            "operating_mode",
            "last_run_state",
            "promoted_trip_id",
            "created_at",
            "updated_at",
            "created_by",
        }
