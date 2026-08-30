"""
spine_api.services.tenant_branding — Multi-tenant white-label branding & domain resolver.

Resolves custom domains/subdomains (e.g. trips.wanderlustluxury.com) to:
- Agency logos, favicons, brand name, and custom theme hex palettes.
- Outbound email DKIM/SPF identities and support hotline phone numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class TenantBrandConfig:
    agency_id: str
    brand_name: str
    custom_domain: str
    logo_url: str
    favicon_url: str
    primary_color_hex: str = "#58a6ff"
    accent_color_hex: str = "#3fb950"
    background_dark_hex: str = "#080a0c"
    support_email: str = "concierge@waypointos.com"
    support_phone: str = "+1 (800) 555-9297"
    email_sender_name: str = "Waypoint Luxury Travel"


_TENANT_REGISTRY: Dict[str, TenantBrandConfig] = {
    "default": TenantBrandConfig(
        agency_id="agency_waypoint_core",
        brand_name="Waypoint OS",
        custom_domain="app.waypointos.com",
        logo_url="https://assets.waypointos.com/logo-light.svg",
        favicon_url="https://assets.waypointos.com/favicon.ico",
        primary_color_hex="#58a6ff",
        accent_color_hex="#3fb950",
        background_dark_hex="#080a0c",
        support_email="concierge@waypointos.com",
        support_phone="+1 (800) 555-WAYPOINT",
        email_sender_name="Waypoint Concierge",
    ),
    "wanderlust": TenantBrandConfig(
        agency_id="agency_wanderlust_luxury",
        brand_name="Wanderlust Bespoke Journeys",
        custom_domain="trips.wanderlustluxury.com",
        logo_url="https://wanderlustluxury.com/brand/logo.svg",
        favicon_url="https://wanderlustluxury.com/brand/favicon.ico",
        primary_color_hex="#d4af37",  # Gold
        accent_color_hex="#2e8b57",  # SeaGreen
        background_dark_hex="#0b0f19",
        support_email="vip@wanderlustluxury.com",
        support_phone="+1 (212) 555-0192",
        email_sender_name="Wanderlust Concierge",
    ),
}


def resolve_tenant_branding(hostname: str) -> TenantBrandConfig:
    """
    Resolve tenant branding configuration based on incoming request Host header.
    """
    host_clean = hostname.split(":")[0].lower().strip()
    
    for _, config in _TENANT_REGISTRY.items():
        if config.custom_domain in host_clean or host_clean in config.custom_domain:
            return config

    if "wanderlust" in host_clean:
        return _TENANT_REGISTRY["wanderlust"]

    return _TENANT_REGISTRY["default"]
