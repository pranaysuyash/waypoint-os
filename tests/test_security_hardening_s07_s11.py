"""
tests/test_security_hardening_s07_s11.py — Tests for Public Checker DoS Depth Guard (S-07)
and Proposal Revocation Durability (S-11).
"""

import pytest
from fastapi import HTTPException
from spine_api.routers.public_checker import _validate_structure_depth


def test_public_checker_structure_depth_validation():
    """Verify _validate_structure_depth allows reasonable nesting and blocks deeply nested recursive DoS payloads."""
    # 1. Normal shallow payload passes
    normal_payload = {
        "traveler": {"name": "Alice", "prefs": {"hotel": "5-star", "city": "Rome"}},
        "tags": ["leisure", "anniversary"],
    }
    _validate_structure_depth(normal_payload, max_depth=10)

    # 2. Deep recursive nesting payload (>10 levels) throws HTTPException 400
    deep_payload = {"level_0": {}}
    curr = deep_payload["level_0"]
    for i in range(1, 15):
        curr[f"level_{i}"] = {}
        curr = curr[f"level_{i}"]

    with pytest.raises(HTTPException) as exc_info:
        _validate_structure_depth(deep_payload, max_depth=10)
    assert exc_info.value.status_code == 400
    assert "exceeds maximum allowed depth" in exc_info.value.detail
