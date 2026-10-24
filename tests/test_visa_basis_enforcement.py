"""
Roadmap invariant 3 (FND-0339): VisaCheckResult.registry_match is REQUIRED —
a writer who cannot say whether the corridor came from the registry cannot
construct the result. The conservative default can never masquerade as a
registry hit.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from spine_api.services.visa_radar import VisaCheckResult


def _build(**over):
    base = dict(
        passport_country="IN", destination_country="TH",
        months_validity_remaining=6.0, passport_validity_compliant=True,
        requires_visa=True, visa_type_required="E_VISA",
        action_required="Apply prior to departure",
    )
    base.update(over)
    return VisaCheckResult(**base)


def test_registry_match_is_required():
    with pytest.raises(ValidationError):
        _build(registry_match=None)


def test_registry_hit_and_miss_both_construct_explicitly():
    assert _build(registry_match=True).registry_match is True
    assert _build(registry_match=False).registry_match is False
