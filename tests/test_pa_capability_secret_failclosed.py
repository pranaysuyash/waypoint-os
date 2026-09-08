"""
tests/test_pa_capability_secret_failclosed.py — PA-24: capability secret fails closed.

Before PA-24, ``boundary_engine`` shipped a committed default
(``waypoint_capability_secret_key_2026``) so any deployment that forgot
CAPABILITY_TOKEN_SECRET silently signed forgeable capability tokens with a
public secret. Mirroring PROPOSAL_SIGNING_KEY (PT-01), construction must fail
loudly instead.
"""

import pytest

from src.services.boundary_engine import BoundaryEngine


@pytest.fixture(autouse=True)
def _fresh_singleton(monkeypatch):
    """Keep the module singleton and env isolated per test."""
    monkeypatch.delenv("CAPABILITY_TOKEN_SECRET", raising=False)
    original = BoundaryEngine._instance
    BoundaryEngine._instance = None
    yield
    BoundaryEngine._instance = original


def test_missing_secret_raises_on_first_use():
    with pytest.raises(RuntimeError, match="CAPABILITY_TOKEN_SECRET is not set"):
        BoundaryEngine()


def test_placeholder_or_short_secret_raises(monkeypatch):
    for weak in ("test", "dev", "changeme", "short"):
        monkeypatch.setenv("CAPABILITY_TOKEN_SECRET", weak)
        with pytest.raises(RuntimeError, match="too weak"):
            BoundaryEngine()


def test_legacy_committed_default_is_rejected(monkeypatch):
    monkeypatch.setenv("CAPABILITY_TOKEN_SECRET", "waypoint_capability_secret_key_2026")
    with pytest.raises(RuntimeError, match="too weak"):
        BoundaryEngine()


def test_strong_env_secret_constructs(monkeypatch):
    monkeypatch.setenv("CAPABILITY_TOKEN_SECRET", "pytest-strong-capability-secret-0123456789abcdef")
    engine = BoundaryEngine()
    token = engine.issue_token(
        trip_id="trip_secret_check",
        agency_id="agency_x",
        scopes=[],
    )
    is_valid, _, msg = engine.verify_token(token.token_string)
    assert is_valid is True
    assert msg == "Token valid"


def test_get_instance_fails_closed_when_env_unset():
    with pytest.raises(RuntimeError, match="CAPABILITY_TOKEN_SECRET"):
        BoundaryEngine.get_instance()
