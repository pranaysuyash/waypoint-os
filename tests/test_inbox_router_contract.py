from __future__ import annotations

from datetime import datetime, timezone

from spine_api.services.inbox_projection import InboxProjectionService


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
            "tripPurpose",
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

    assert set(payload) >= {
        "total",
        "unassigned",
        "critical",
        "atRisk",
        "breached",
        "incomplete",
        "missingCustomer",
        "missingTripBasics",
        "oldestWaitingDays",
        "oldestUnassignedWaitingDays",
        "statsCoverage",
    }
    for key in (
        "total",
        "unassigned",
        "critical",
        "atRisk",
        "breached",
        "incomplete",
        "missingCustomer",
        "missingTripBasics",
        "statsCoverage",
    ):
        assert isinstance(payload[key], int)


def test_inbox_projection_promotes_business_trip_type_from_purpose():
    service = InboxProjectionService(now=datetime(2026, 6, 23, tzinfo=timezone.utc))
    projected = service.project_all([
        {
            "id": "trip_business_001",
            "status": "new",
            "created_at": "2026-06-23T00:00:00Z",
            "updated_at": "2026-06-23T00:00:00Z",
            "extracted": {
                "facts": {
                    "destination_candidates": {"value": ["Singapore"]},
                    "trip_purpose": {"value": "business", "confidence": 1.0},
                    "origin_city": {"value": "Mumbai"},
                    "party_size": {"value": 18},
                    "date_window": {"value": "in October 2026"},
                    "budget": {"value": 42000},
                }
            },
        }
    ])

    assert projected[0]["tripType"] == "business"
    assert projected[0]["tripPurpose"] == "business"
