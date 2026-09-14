"""MarginPolicy resolution — dimensioned, versioned, fail-safe (Addendum 12).

Agency margin policy is configurable by agency → vendor (id/class) →
location → category → value band, longest-prefix wins, platform defaults
fail-safe. Default behavior is UNCHANGED from fee_matrix's literals
(platform seed is 1:1).
"""


from src.fees.margin_policy import (
    MarginPolicyRule,
    PLATFORM_DEFAULT_RULES,
    resolve_margin_policy,
    rules_from_dicts,
)


def test_platform_defaults_seed_matches_fee_matrix_literals():
    by_id = {r.rule_id: r for r in PLATFORM_DEFAULT_RULES}
    assert by_id["platform.custom_tour.0-10k"].markup_pct == 0.14
    assert by_id["platform.custom_tour.0-10k"].min_margin_floor_usd == 250.0
    assert by_id["platform.custom_tour.10k-100k"].markup_pct == 0.11
    assert by_id["platform.custom_tour.10k-100k"].min_margin_floor_usd == 1200.0
    assert by_id["platform.flights.standalone"].markup_pct == 0.03


def test_category_and_value_band_resolution():
    rule = resolve_margin_policy(category="custom_tour", package_value_usd=5000)
    assert rule.rule_id == "platform.custom_tour.0-10k"
    rule = resolve_margin_policy(category="custom_tour", package_value_usd=50000)
    assert rule.rule_id == "platform.custom_tour.10k-100k"


def test_vendor_specific_override_beats_platform_default():
    negotiated = MarginPolicyRule(
        rule_id="agency-x.hotelbeds.negotiated",
        agency_id="agency-x",
        vendor_id="hotelbeds",
        vendor_class="bedbank",
        location="maldives",
        category="lodging",
        markup_pct=0.09,
        min_margin_floor_pct=0.05,
        min_margin_floor_usd=100.0,
    )
    rule = resolve_margin_policy(
        category="lodging", package_value_usd=20000,
        agency_id="agency-x", vendor_id="hotelbeds",
        vendor_class="bedbank", location="maldives",
        override_rules=[negotiated],
    )
    assert rule.rule_id == "agency-x.hotelbeds.negotiated"
    assert rule.markup_pct == 0.09


def test_specificity_ordering_vendor_class_vs_id():
    class_rule = MarginPolicyRule(
        rule_id="r-class", agency_id="a1", vendor_class="bedbank", markup_pct=0.12)
    id_rule = MarginPolicyRule(
        rule_id="r-id", agency_id="a1", vendor_id="hotelbeds",
        vendor_class="bedbank", markup_pct=0.07)
    rule = resolve_margin_policy(
        category="lodging", package_value_usd=5000,
        agency_id="a1", vendor_id="hotelbeds", vendor_class="bedbank",
        override_rules=[class_rule, id_rule],
    )
    assert rule.rule_id == "r-id"  # vendor id (3) beats class (2)


def test_fail_safe_unknown_vendor_falls_to_platform():
    rule = resolve_margin_policy(
        category="custom_tour", package_value_usd=5000,
        agency_id="agency-x", vendor_id="unknown-vendor",
        override_rules=[
            MarginPolicyRule(rule_id="x", agency_id="agency-x",
                             vendor_id="hotelbeds", markup_pct=0.20),
        ],
    )
    assert rule.rule_id == "platform.custom_tour.0-10k"  # platform default


def test_agency_scoping_isolation():
    rule = resolve_margin_policy(
        category="custom_tour", package_value_usd=5000,
        agency_id="agency-other",
        override_rules=[
            MarginPolicyRule(rule_id="x", agency_id="agency-x", markup_pct=0.20),
        ],
    )
    # another agency's override must never leak
    assert rule.rule_id == "platform.custom_tour.0-10k"


def test_rules_from_dicts_scopes_agency():
    rules = rules_from_dicts(
        [{"rule_id": "o1", "markup_pct": 0.20}], "agency-x"
    )
    assert rules[0].agency_id == "agency-x"
    assert rules[0].markup_pct == 0.20


def test_floor_outside_value_band_falls_through():
    rule = resolve_margin_policy(
        category="custom_tour", package_value_usd=250000,  # beyond all bands
    )
    # fail-safe: platform defaults as a whole, never a guess
    assert rule in PLATFORM_DEFAULT_RULES or rule.rule_id.startswith("platform.")
