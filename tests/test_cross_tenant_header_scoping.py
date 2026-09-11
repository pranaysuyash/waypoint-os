"""FND-0259 regression: routers must not trust a raw client ``X-Agency-ID`` header.

Waypoint OS derives tenant scope from the authenticated JWT membership via
``spine_api.core.auth.get_current_agency_id``. A raw
``Header(None, alias="X-Agency-ID")`` parameter in a router lets any
authenticated caller read another agency's trips by spoofing the header
(``x_agency_id or TEST_AGENCY_ID`` even granted an unscoped default).

The canonical dependency honors an explicit X-Agency-ID header ONLY under
pytest/auth-bypass, so the production path is enforced structurally. These
tests mirror the CI gate in ``scripts/check_unscoped_trip_access.sh`` so a
regression fails in the suite, not just in lint.
"""

import re
from pathlib import Path

ROUTERS_DIR = Path(__file__).resolve().parents[1] / "spine_api" / "routers"

# Routers remediated under FND-0259 (2026-09-11). Previously each declared a
# raw X-Agency-ID header (and most fell back to TEST_AGENCY_ID when absent).
FND0259_ROUTERS = [
    "visa_radar.py",
    "concierge_upsell.py",
    "fx_sentinel.py",
    "disruption_radar.py",
    "passenger_rights.py",
    "subagent_payouts.py",
]

_RAW_HEADER_RE = re.compile(r'alias="X-Agency-ID"')


def test_no_router_declares_raw_x_agency_id_header():
    """No router may take agency scope from a raw header parameter."""
    offenders = []
    for path in sorted(ROUTERS_DIR.glob("*.py")):
        if _RAW_HEADER_RE.search(path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert offenders == [], (
        "Raw X-Agency-ID header parameters must not appear in routers; "
        "use agency_id: str = Depends(get_current_agency_id) instead "
        f"(JWT-derived; header honored only under pytest/auth-bypass). Offenders: {offenders}"
    )


def test_fnd0259_routers_use_canonical_agency_dependency():
    """Each remediated router resolves agency scope via the canonical dependency."""
    for name in FND0259_ROUTERS:
        source = (ROUTERS_DIR / name).read_text(encoding="utf-8")
        assert "get_current_agency_id" in source, (
            f"{name} was remediated under FND-0259 to use get_current_agency_id; "
            "the canonical dependency reference has disappeared."
        )


def test_routers_do_not_fall_back_to_test_agency_id():
    """No router may default header-derived tenant scope to TEST_AGENCY_ID.

    An authenticated caller reaching such an endpoint without the header would
    silently receive another agency's (the test agency's) data. Note: a
    TEST_AGENCY_ID fallback on a *token-scoped public* endpoint (group_booking)
    is a different, accepted legacy-row case and is not this defect class.
    """
    offenders = []
    fallback_re = re.compile(r"x_agency_id\s+or\s+TEST_AGENCY_ID")
    for path in sorted(ROUTERS_DIR.glob("*.py")):
        if fallback_re.search(path.read_text(encoding="utf-8")):
            offenders.append(path.name)
    assert offenders == [], (
        "Routers must not default X-Agency-ID-derived scope to TEST_AGENCY_ID; "
        f"derive agency scope from the authenticated membership. Offenders: {offenders}"
    )


def test_fnd0259_router_modules_import_cleanly():
    """The remediated modules still import (catches signature/import breakage)."""
    from spine_api.routers import (  # noqa: F401
        concierge_upsell,
        disruption_radar,
        fx_sentinel,
        passenger_rights,
        subagent_payouts,
        visa_radar,
    )
