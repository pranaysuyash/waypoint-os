from fastapi import FastAPI
from fastapi.testclient import TestClient
from spine_api.core.rate_limiter import SlowAPIMiddleware, limiter
from spine_api.services.agency_marketplace import (
    AgencyMarketplaceProfile,
    AgencyMarketplaceStore,
    slugify,
)
from spine_api.routers.public_checker import router


def test_slugify():
    assert slugify("Waypoint Trips Desk") == "waypoint-trips-desk"
    assert slugify("Celestial Journeys & Safaris!") == "celestial-journeys-safaris"
    assert slugify("  Extra   Spaces  ") == "extra-spaces"


def test_get_profile_by_slug_or_id_matching(monkeypatch):
    mock_profiles = [
        AgencyMarketplaceProfile(
            agency_id="agency-123",
            display_name="Apex Luxury Travel",
            blurb="Bespoke luxury itineraries and private aviation.",
            response_sla_hours=24,
            places_covered=["France", "Italy", "Japan"],
            customer_types=["HNW", "Couples"],
            services=["Luxury Hotels", "Private Aviation"],
            languages=["English", "French"],
        ),
        AgencyMarketplaceProfile(
            agency_id="agency-456",
            display_name="Himalayan Expeditions",
            blurb="High altitude trekking and cultural immersion.",
            response_sla_hours=48,
            places_covered=["Nepal", "Bhutan", "India"],
        ),
    ]

    monkeypatch.setattr(AgencyMarketplaceStore, "list_profiles", classmethod(lambda cls: mock_profiles))

    # Match by ID
    p1 = AgencyMarketplaceStore.get_profile_by_slug_or_id("agency-123")
    assert p1 is not None
    assert p1.display_name == "Apex Luxury Travel"

    # Match by Slug
    p2 = AgencyMarketplaceStore.get_profile_by_slug_or_id("apex-luxury-travel")
    assert p2 is not None
    assert p2.agency_id == "agency-123"

    # Match by case-insensitive name/slug
    p3 = AgencyMarketplaceStore.get_profile_by_slug_or_id("Himalayan-Expeditions")
    assert p3 is not None
    assert p3.agency_id == "agency-456"

    # Non-existent
    assert AgencyMarketplaceStore.get_profile_by_slug_or_id("unknown-agency") is None


def test_get_public_checker_agency_endpoint(monkeypatch):
    mock_profile = AgencyMarketplaceProfile(
        agency_id="agency-999",
        display_name="Solstice Private Journeys",
        blurb="Curated private journeys worldwide.",
        response_sla_hours=12,
        places_covered=["Switzerland", "Norway"],
        customer_types=["Luxury"],
        services=["Private Guides"],
        languages=["English"],
    )

    monkeypatch.setattr(
        AgencyMarketplaceStore,
        "get_profile_by_slug_or_id",
        classmethod(lambda cls, identifier: mock_profile if identifier == "solstice" else None),
    )

    monkeypatch.setenv("PUBLIC_CHECKER_ENABLED", "1")
    app = FastAPI()
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/public-checker/agency/solstice")
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "30"
        data = response.json()
        assert data["ok"] is True
        assert data["agency"]["agency_id"] == "agency-999"
        assert data["agency"]["display_name"] == "Solstice Private Journeys"
        assert data["agency"]["response_sla_hours"] == 12

        assert client.get("/api/public-checker/agency/nonexistent").status_code == 404
