from spine_api.services.fee_matrix import (
    PricingBreakdown,
    calculate_package_pricing,
)
from spine_api.services.corporate_policy import (
    CorporatePolicyAuditResult,
    evaluate_corporate_travel_policy,
)
from spine_api.services.tenant_branding import (
    TenantBrandConfig,
    resolve_tenant_branding,
)


def test_fee_matrix_custom_tour_calculation():
    wholesale_cost = 5000.0  # 14% markup + $150 fee = $700 + $150 = $850 margin
    pricing: PricingBreakdown = calculate_package_pricing(wholesale_cost, category="custom_tour")
    assert pricing.wholesale_cost_usd == 5000.0
    assert pricing.markup_amount_usd == 700.0
    assert pricing.flat_planning_fee_usd == 150.0
    assert pricing.client_retail_price_usd == 5850.0
    assert pricing.effective_agency_margin_pct > 14.0


def test_corporate_policy_flags_business_class_on_short_flight():
    result: CorporatePolicyAuditResult = evaluate_corporate_travel_policy(
        flight_duration_hours=2.5,
        flight_cabin_class="Business",
        hotel_nightly_rate_usd=220.0,
        destination_city="Chicago",
        days_advance_booking=20,
    )
    assert result.is_compliant is False
    assert result.requires_manager_approval is True
    assert any("CABIN_CLASS" in v.rule_code for v in result.violations)


def test_tenant_branding_resolution():
    config: TenantBrandConfig = resolve_tenant_branding("trips.wanderlustluxury.com")
    assert config.brand_name == "Wanderlust Bespoke Journeys"
    assert config.primary_color_hex == "#d4af37"
    assert "wanderlustluxury.com" in config.support_email

    default_config: TenantBrandConfig = resolve_tenant_branding("unknown-agency.com")
    assert default_config.brand_name == "Waypoint OS"
