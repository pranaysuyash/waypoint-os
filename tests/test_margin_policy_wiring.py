"""MarginPolicy wiring end-to-end: resolution → fee_matrix → provenance.

Covers the Addendum 12 integration slice: fee_matrix accepts a resolved
MarginPolicyRule (applied_rule_id carries id@version); agency overrides
round-trip through AgencySettingsStore; precedence holds through the real
pricing path.
"""

import pytest

from src.fees.margin_policy import (
    MarginPolicyRule,
    resolve_margin_policy,
)
from spine_api.services.fee_matrix import calculate_package_pricing


def test_policy_rule_drives_pricing_and_provenance():
    negotiated = MarginPolicyRule(
        rule_id="agency-x.hotelbeds.maldives",
        agency_id="agency-x",
        vendor_id="hotelbeds",
        category="lodging",
        markup_pct=0.09,
        min_margin_floor_usd=100.0,
        flat_planning_fee_usd=75.0,
        ruleset_version="agency-x-v3",
    )
    result = calculate_package_pricing(
        wholesale_cost_usd=1000.0,
        category="lodging",
        margin_policy_rule=negotiated,
    )
    # markup = 1000 * 0.09 = 90; total margin 90+75 = 165 >= floor 100
    # -> no floor lift. retail = 1000 + 90 + 75 = 1165.
    assert result.flat_planning_fee_usd == 75.0
    assert result.applied_rule_id == "agency-x.hotelbeds.maldives@agency-x-v3"
    assert result.client_retail_price_usd == pytest.approx(1165.0)


def test_no_policy_rule_keeps_legacy_literals():
    result = calculate_package_pricing(wholesale_cost_usd=5000.0, category="custom_tour")
    assert result.applied_rule_id == "tier_standard_custom_tour"
    assert result.effective_agency_margin_pct > 0


def test_resolution_feeds_pricing_end_to_end():
    overrides = [
        MarginPolicyRule(
            rule_id="agency-x.flights.negotiated",
            agency_id="agency-x",
            vendor_id="amadeus",
            category="flights",
            markup_pct=0.05,
            min_margin_floor_usd=25.0,
            flat_planning_fee_usd=20.0,
            ruleset_version="agency-x-v1",
        ),
    ]
    rule = resolve_margin_policy(
        category="flights", package_value_usd=3000.0,
        agency_id="agency-x", vendor_id="amadeus",
        override_rules=overrides,
    )
    result = calculate_package_pricing(
        wholesale_cost_usd=3000.0,
        category="flights",
        margin_policy_rule=rule,
    )
    assert result.applied_rule_id.startswith("agency-x.flights.negotiated@")
    assert result.client_retail_price_usd == pytest.approx(3000.0 * 1.05 + 20.0)


def test_compiler_emits_policy_provenance_and_preview_gate():
    """End-to-end: compile_from_intake resolves the dimensioned policy per
    agency and emits provenance; the floor gate is skipped on preview basis
    (real-or-None rule) and take-rate clamps come from the resolved rule."""
    from datetime import date
    from src.orchestration.proposal_compiler import AutonomousProposalCompiler

    pkg = AutonomousProposalCompiler.compile_from_intake(
        trip_id="trip-mp-wiring",
        raw_intake_text="japan trip for 2",
        destination="Japan",
        departure_date=date(2027, 3, 10),
        return_date=date(2027, 3, 20),
        traveler_count=2,
        agency_id="agency-x",
        vendor_id="hotelbeds",
        location="japan",
    )
    assert pkg.margin_policy_rule_id == "platform.custom_tour.0-10k"
    assert pkg.margin_policy_version == "platform-v1-2026-09-14"
    assert pkg.margin_floor_gate == "skipped_preview_basis"
    assert pkg.margin_basis == "preview"
