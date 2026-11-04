"""TripQuoteView statutory tax producer (R2-C tranche, 2026-11-03).

Pins: the paired tax_basis contract (inv-3 — a rate without its source is a
fabricated number) and the producer's honest gates (India-based agency +
known non-India destination only).
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from spine_api.contract import TripQuoteView
from spine_api.routers.quotes import _statutory_tax_preview


def _quote(**overrides):
    base = dict(
        trip_id="trip_tax_1",
        title="Proposed itinerary",
        net_cost=1200.0,
        net_cost_basis="persisted_modeled_cost",
        margin_percent=13.0,
        margin_basis="policy_preview",
        rack_price=1380.0,
        rack_price_basis="computed_preview",
    )
    base.update(overrides)
    return TripQuoteView(**base)


def test_tax_basis_required_when_tax_percent_set():
    with pytest.raises(ValidationError, match="tax_basis is required"):
        _quote(tax_percent=2.0)


def test_tax_basis_rejected_without_tax_percent():
    with pytest.raises(ValidationError, match="without the paired number"):
        _quote(tax_basis="india_tcs_statutory_preview")


def test_unknown_tax_basis_rejected():
    with pytest.raises(ValidationError, match="not a known basis"):
        _quote(tax_percent=2.0, tax_basis="made_up_basis")


def test_valid_pair_constructs():
    q = _quote(tax_percent=2.0, tax_basis="india_tcs_statutory_preview")
    assert q.tax_percent == 2.0
    assert q.tax_basis == "india_tcs_statutory_preview"


def test_producer_rate_is_current_regime(monkeypatch):
    # India-based agency (default currency INR) + known non-India destination.
    class _Settings:
        default_currency = "INR"

    import src.intake.config.agency_settings as agency_settings

    monkeypatch.setattr(agency_settings.AgencySettingsStore, "load", lambda aid: _Settings())

    trip = {"extracted": {"facts": {"destination_country": {"value": "Thailand"}}}}
    preview = _statutory_tax_preview(trip, "agency_x")
    assert preview is not None
    rate, basis = preview
    from src.fees.tax_compliance import select_tcs_regime

    assert rate == select_tcs_regime(date.today()).below_rate_pct
    assert basis == "india_tcs_statutory_preview"


def test_producer_skips_india_destination(monkeypatch):
    class _Settings:
        default_currency = "INR"

    import src.intake.config.agency_settings as agency_settings

    monkeypatch.setattr(agency_settings.AgencySettingsStore, "load", lambda aid: _Settings())
    trip = {"extracted": {"facts": {"destination_country": {"value": "India"}}}}
    assert _statutory_tax_preview(trip, "agency_x") is None


def test_producer_skips_unknown_destination(monkeypatch):
    class _Settings:
        default_currency = "INR"

    import src.intake.config.agency_settings as agency_settings

    monkeypatch.setattr(agency_settings.AgencySettingsStore, "load", lambda aid: _Settings())
    trip = {"destination": "somewhere sunny"}
    assert _statutory_tax_preview(trip, "agency_x") is None


def test_producer_skips_non_inr_agency(monkeypatch):
    class _Settings:
        default_currency = "USD"

    import src.intake.config.agency_settings as agency_settings

    monkeypatch.setattr(agency_settings.AgencySettingsStore, "load", lambda aid: _Settings())
    trip = {"extracted": {"facts": {"destination_country": {"value": "Thailand"}}}}
    assert _statutory_tax_preview(trip, "agency_x") is None
