"""
FND-0330 (Sim #4): capability-token share surfaces must be reachable WITHOUT a
session — the middleware allowlist carries them, or the invitee/traveler is
401'd before the (deliberately unauthenticated) route runs.
"""

from spine_api.core.middleware import _is_public_path


def test_group_share_portal_is_public_by_token():
    assert _is_public_path("/api/v1/group/token/grp_abc123")
    assert _is_public_path("/api/v1/group/token/grp_abc123/pay-share")


def test_advisor_group_routes_stay_protected():
    assert not _is_public_path("/api/v1/group/trip_123/invites")
    assert not _is_public_path("/api/v1/group/trip_123/manual-override")


def test_precedent_capability_surfaces_still_public():
    assert _is_public_path("/api/v1/proposals/token/prop_abc")
    assert _is_public_path("/api/public/asks/ask_abc")
