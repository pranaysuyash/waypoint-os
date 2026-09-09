"""WOBS 2026-09-09 P2 — agency marketplace: profiles, matching, demand capture.

Matched choice (never single-routing, never a directory): scored overlap
between brief needs and structured agency profiles, capped set, and a demand-
capture waitlist so the interaction works at any supply level.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spine_api.services.agency_marketplace import (
    AgencyMarketplaceProfile,
    AgencyMarketplaceStore,
    derive_brief_needs,
    match_agencies_for_needs,
    valid_contact,
)


@pytest.fixture()
def isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "agency_marketplace"
    monkeypatch.setattr(AgencyMarketplaceStore, "DATA_DIR", data_dir)
    monkeypatch.setattr(AgencyMarketplaceStore, "PROFILES_FILE", data_dir / "profiles.json")
    monkeypatch.setattr(AgencyMarketplaceStore, "LEADS_FILE", data_dir / "route_leads.jsonl")
    return AgencyMarketplaceStore


def _profile(agency_id: str, **overrides) -> AgencyMarketplaceProfile:
    base = dict(
        agency_id=agency_id,
        display_name=agency_id.title(),
        places_covered=["Kerala", "Goa"],
        customer_types=["families", "seniors"],
        services=["visa assistance", "trip planning"],
        languages=["English", "Hindi"],
        response_sla_hours=48,
        blurb="",
    )
    base.update(overrides)
    return AgencyMarketplaceProfile(**base)


class TestProfiles:
    def test_upsert_and_list_roundtrip(self, isolated_store):
        isolated_store.upsert_profile(_profile("ravi"))
        isolated_store.upsert_profile(_profile("ravi", blurb="updated"))
        profiles = isolated_store.list_profiles()
        assert len(profiles) == 1
        assert profiles[0].blurb == "updated"

    def test_empty_store_returns_empty(self, isolated_store):
        assert isolated_store.list_profiles() == []


class TestMatching:
    def test_destination_overlap_scores_and_explains(self):
        needs = {"destination": "Kerala", "customer_types": [], "services": []}
        matches = match_agencies_for_needs(needs, [_profile("ravi")])
        assert len(matches) == 1
        assert matches[0].score >= 2
        assert any("Kerala" in reason for reason in matches[0].match_reasons)

    def test_no_overlap_returns_empty_not_best_guess(self):
        needs = {"destination": "Iceland", "customer_types": [], "services": []}
        assert match_agencies_for_needs(needs, [_profile("ravi")]) == []

    def test_customer_types_and_services_add_score(self):
        needs = {
            "destination": "Kerala",
            "customer_types": ["families"],
            "services": ["visa assistance"],
        }
        matches = match_agencies_for_needs(needs, [_profile("ravi")])
        assert matches[0].score >= 4

    def test_capped_at_limit(self):
        profiles = [_profile(f"agency-{i}") for i in range(6)]
        needs = {"destination": "Kerala", "customer_types": [], "services": []}
        assert len(match_agencies_for_needs(needs, profiles, limit=3)) == 3

    def test_higher_score_ranks_first(self):
        strong = _profile("strong", places_covered=["Kerala", "Goa", "Himalayas"])
        weak = _profile("weak", places_covered=["Goa"])
        needs = {"destination": "Kerala", "customer_types": [], "services": []}
        matches = match_agencies_for_needs(needs, [weak, strong])
        assert matches[0].profile.agency_id == "strong"


class TestDeriveNeeds:
    def test_extracts_destination_and_keywords(self):
        packet = {"resolved_destination": "Kerala"}
        needs = derive_brief_needs(
            packet,
            ["Traveling with toddler", "visa not arranged", "monsoon window risk"],
        )
        assert needs["destination"] == "Kerala"
        assert "families" in needs["customer_types"]
        assert "visa assistance" in needs["services"]
        assert "trip planning" in needs["services"]


class TestDemandCapture:
    def test_capture_without_agency_is_waitlist(self, isolated_store):
        isolated_store.upsert_profile(_profile("ravi"))
        record = AgencyMarketplaceStore.capture_route_lead(
            trip_id="trip_x", contact="a@b.com", agency_id=None,
            needs={"destination": "Kerala"},
        )
        assert record["status"] == "captured"
        assert record["agency_id"] is None
        assert len(isolated_store.list_route_leads()) == 1

    def test_capture_with_known_agency_is_routed(self, isolated_store):
        isolated_store.upsert_profile(_profile("ravi"))
        record = AgencyMarketplaceStore.capture_route_lead(
            trip_id="trip_x", contact="a@b.com", agency_id="ravi",
            needs={},
        )
        assert record["status"] == "routed"
        assert record["agency_id"] == "ravi"

    def test_unknown_agency_degrades_to_capture(self, isolated_store):
        record = AgencyMarketplaceStore.capture_route_lead(
            trip_id="trip_x", contact="a@b.com", agency_id="ghost-agency", needs={},
        )
        assert record["status"] == "captured"

    def test_leads_survive_reopen(self, isolated_store, tmp_path: Path):
        AgencyMarketplaceStore.capture_route_lead(trip_id="t", contact="a@b.com", agency_id=None, needs={})
        leads = AgencyMarketplaceStore.list_route_leads()
        assert len(leads) == 1


class TestContactValidation:
    @pytest.mark.parametrize("value", ["a@b.com", "+91 98765 43210", "9876543210"])
    def test_valid_contacts(self, value):
        assert valid_contact(value) is True

    @pytest.mark.parametrize("value", ["", "not-a-contact", "123", "@@"])
    def test_invalid_contacts(self, value):
        assert valid_contact(value) is False
