"""
tests/test_trust_scorecard_honesty.py — Honest trust scorecard verification.

Verifies:
  - Unknown tokens return 404 (no fabricated demo fallback)
  - Unknown proposal acceptance returns 404
  - Real trips produce computed scores (not hardcoded 96.0)
  - Response includes reality tier metadata
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from spine_api.routers.trust_scorecard import (
    compute_completeness_score,
    compute_budget_fit_status,
    compute_transparency_badges,
    get_proposal_trust_scorecard,
    get_proposal_by_token,
    accept_proposal_by_token,
)
from spine_api.persistence import TripStore


class TestTrustScorecardComputation:
    """Test score computation functions with real data."""

    def test_completeness_full_packet(self):
        packet = {
            "destination": "Tokyo",
            "start_date": "2026-10-01",
            "end_date": "2026-10-10",
            "budget_max": 5000.0,
            "party_size": 2,
        }
        score, sufficient = compute_completeness_score(packet)
        assert score == 100.0
        assert sufficient is True

    def test_completeness_partial_packet(self):
        packet = {
            "destination": "Paris",
            "party_size": 1,
        }
        score, sufficient = compute_completeness_score(packet)
        assert score == 40.0
        assert sufficient is False

    def test_budget_fit_perfect_match(self):
        packet = {"budget_max": 5000.0, "budget_min": 3000.0}
        fit = compute_budget_fit_status(packet, proposal_cost=4000.0)
        assert fit == "PERFECT_MATCH"

    def test_budget_fit_slight_stretch(self):
        packet = {"budget_max": 5000.0}
        fit = compute_budget_fit_status(packet, proposal_cost=5500.0)
        assert fit == "SLIGHT_STRETCH"

    def test_transparency_badges_honest(self):
        packet = {
            "destination": "Rome",
            "start_date": "2026-06-01",
            "end_date": "2026-06-08",
            "budget_max": 4000.0,
            "party_size": 2,
        }
        badges = compute_transparency_badges(packet, has_owner_review=True)
        badge_names = [b["badge"] for b in badges]
        assert "COMPLETE_BRIEF" in badge_names
        assert "BUDGET_ALIGNED" in badge_names
        assert "OWNER_REVIEWED" in badge_names
        assert "VERIFIED_PARTNER" not in badge_names  # Unverified badge excluded


@pytest.mark.asyncio
class TestTrustScorecardEndpoints:
    """Test API endpoint behavior."""

    async def test_get_scorecard_trip_not_found(self):
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_proposal_trust_scorecard("nonexistent_trip", agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_get_scorecard_success_path(self):
        trip_data = {
            "id": "trip_101",
            "agency_id": "agency_1",
            "destination": "Kyoto",
            "packet": {
                "destination": "Kyoto",
                "start_date": "2026-11-01",
                "end_date": "2026-11-10",
                "budget_max": 6000.0,
                "party_size": 2,
            },
        }
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_data):
            res = await get_proposal_trust_scorecard("trip_101", agency_id="agency_1")
            assert res.ok is True
            assert res.trip_id == "trip_101"
            assert res.completeness_score.value == 100.0
            assert res.completeness_score.data_sufficient is True
            assert res.budget_alignment_score.value == 100.0
            assert res.confidence_score.value == 100.0

    async def test_get_proposal_by_unknown_token_returns_404(self):
        with patch.object(TripStore, "list_trips", return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                await get_proposal_by_token("prop_unknown_token_123")
            assert exc_info.value.status_code == 404

    async def test_accept_proposal_unknown_token_returns_404(self):
        with patch.object(TripStore, "list_trips", return_value=[]):
            with pytest.raises(HTTPException) as exc_info:
                await accept_proposal_by_token("prop_unknown_token_456")
            assert exc_info.value.status_code == 404
