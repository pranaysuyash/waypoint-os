"""A6: sample defaults must remain disclosed on partial export requests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from spine_api.routers.itinerary_export import router


def test_partial_itinerary_remains_sample_labeled():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post("/api/v1/trips/test-trip/export/html", json={"days": [{
            "day_number": 1, "date_str": "2026-10-04", "title": "Arrival",
            "location": "Tokyo", "description": "Caller supplied this day",
        }]})
    assert response.status_code == 200
    assert response.headers["X-Itinerary-Data-Source"] == "sample-payload"
    assert response.headers["X-Reality-Tier"] == "deterministic_preview"


def test_fully_supplied_itinerary_is_caller_labeled():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post("/api/v1/trips/test-trip/export/html", json={
            "client_name": "Test Traveler", "destination_title": "Test itinerary",
            "travel_dates": "2026-10-04", "total_cost_usd": 0,
            "allergies": [], "emergency_contact": "Operator contact",
            "days": [], "vouchers": {},
        })
    assert response.status_code == 200
    assert response.headers["X-Itinerary-Data-Source"] == "caller-provided"
    assert response.headers["X-Reality-Tier"] == "real"
