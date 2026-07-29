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


def test_trip_patch_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TripPatchRequest(unknown_field="nope")
