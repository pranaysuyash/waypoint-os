from __future__ import annotations

import pytest
from pydantic import ValidationError

from spine_api.contract import SpineRunRequest, TripPatchRequest


def test_spine_run_request_defaults_strict_leakage_false() -> None:
    request = SpineRunRequest()
    assert request.strict_leakage is False


def test_spine_run_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SpineRunRequest(unknown_field="nope")


@pytest.mark.parametrize("stage", ["discovery", "shortlist", "proposal", "booking"])
def test_spine_run_request_accepts_canonical_stages(stage: str) -> None:
    """FND-0400: the run-request stage must accept the canonical trip-stage
    vocabulary, including the booking gate used by declared-booked travelers
    (RDA_EX07 rec-3)."""
    assert SpineRunRequest(stage=stage).stage == stage


def test_spine_run_request_rejects_unknown_stage() -> None:
    """Unknown stages previously degraded silently to discovery-like
    semantics (FND-0400); they must now fail loudly at the contract."""
    with pytest.raises(ValidationError, match="Invalid stage"):
        SpineRunRequest(stage="intake")


def test_trip_patch_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TripPatchRequest(unknown_field="nope")
