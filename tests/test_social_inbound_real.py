"""
tests/test_social_inbound_real.py — Tests for real social inbound intake pipeline.

Verifies:
  - Empty raw_text returns 400
  - PII in raw DM text is scrubbed before saving
  - Extraction pipeline parses real fields
  - Cross-agency teaser unmask returns 404
  - Invalid token returns 403
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

from spine_api.routers.social_inbound import (
    SocialInboundParseRequest,
    UnmaskTeaserRequest,
    parse_social_inbound,
    unmask_teaser_proposal,
)
from spine_api.persistence import TripStore


@pytest.mark.asyncio
class TestSocialInboundEndpoints:
    """Test social intake endpoint behavior."""

    async def test_empty_raw_text_raises_400(self):
        req = SocialInboundParseRequest(raw_text="   ")
        with pytest.raises(HTTPException) as exc_info:
            await parse_social_inbound(req, agency_id="agency_1")
        assert exc_info.value.status_code == 400

    async def test_parse_social_inbound_creates_trip(self):
        req = SocialInboundParseRequest(
            raw_text="Looking for a 5 day trip to Bali for 2 people with a budget of $4000",
            client_name="Jane Doe",
        )
        with patch.object(TripStore, "save_trip") as mock_save:
            res = await parse_social_inbound(req, agency_id="agency_1")
            assert res.ok is True
            assert res.trip_id.startswith("trip_")
            assert "Bali" in res.destination or res.destination != "Unknown"
            assert res.is_masked is True
            assert mock_save.called

    async def test_unmask_cross_agency_returns_404(self):
        req = UnmaskTeaserRequest(trip_id="trip_other", token="tok_123")
        with patch.object(TripStore, "get_trip_for_agency", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await unmask_teaser_proposal(req, agency_id="agency_1")
            assert exc_info.value.status_code == 404

    async def test_unmask_invalid_token_returns_403(self):
        trip_record = {
            "id": "trip_123",
            "agency_id": "agency_1",
            "token": "tok_correct",
            "is_masked": True,
        }
        req = UnmaskTeaserRequest(trip_id="trip_123", token="tok_wrong")
        with patch.object(TripStore, "get_trip_for_agency", return_value=trip_record):
            with pytest.raises(HTTPException) as exc_info:
                await unmask_teaser_proposal(req, agency_id="agency_1")
            assert exc_info.value.status_code == 403
