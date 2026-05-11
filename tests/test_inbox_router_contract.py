from __future__ import annotations


def test_inbox_router_returns_frontend_consumed_collection_shape(session_client):
    response = session_client.get("/inbox?limit=1")

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["items"], list)
    assert isinstance(payload["total"], int)
    assert isinstance(payload["hasMore"], bool)
    assert set(payload["filterCounts"]) >= {"all", "at_risk", "incomplete", "unassigned"}
    if payload["items"]:
        assert set(payload["items"][0]) >= {
            "id",
            "reference",
            "destination",
            "tripType",
            "partySize",
            "dateWindow",
            "value",
            "priority",
            "priorityScore",
            "urgency",
            "importance",
            "stage",
            "stageNumber",
            "submittedAt",
            "lastUpdated",
            "daysInCurrentStage",
            "slaStatus",
            "customerName",
            "flags",
        }


def test_inbox_router_returns_overview_stats_shape(session_client):
    response = session_client.get("/inbox/stats")

    assert response.status_code == 200
    payload = response.json()

    assert set(payload) == {"total", "unassigned", "critical", "atRisk"}
    assert all(isinstance(payload[key], int) for key in payload)
