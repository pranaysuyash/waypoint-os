"""Tests for the current Visa & Passport Validity Radar API.

The service was refactored from an older `check_visa_and_passport_compliance`
interface to the simpler `audit_visa_and_passport_validity(VisaCheckRequest)`.
These tests exercise the current contract while preserving the original intent:
passport validity threshold and visa-category correctness.
"""

from spine_api.services.visa_radar import (
    VisaCheckRequest,
    audit_visa_and_passport_validity,
)


def test_passport_valid_for_schengen():
    # US passport to France (Schengen) — requires 3 months validity remaining.
    req = VisaCheckRequest(
        passport_country="US",
        destination_country="FR",
        passport_expiry_date="2028-05-20",
        travel_date="2026-09-01",
    )
    report = audit_visa_and_passport_validity(req)

    assert report.ok is True
    assert report.passport_validity_compliant is True
    assert report.requires_visa is False
    assert report.visa_type_required == "NONE"


def test_passport_fails_validity_threshold():
    # US passport to France (Schengen) — passport expires in Oct 2026, only ~1
    # month after a Sep 2026 travel start, short of the 3-month minimum.
    req = VisaCheckRequest(
        passport_country="US",
        destination_country="FR",
        passport_expiry_date="2026-10-15",
        travel_date="2026-09-01",
    )
    report = audit_visa_and_passport_validity(req)

    assert report.ok is True
    assert report.passport_validity_compliant is False
    assert any("minimum" in w.lower() for w in report.warnings)


def test_visa_required_flagged():
    # Indian passport to Thailand requires an e-Visa.
    req = VisaCheckRequest(
        passport_country="IN",
        destination_country="TH",
        passport_expiry_date="2029-01-01",
        travel_date="2026-10-01",
    )
    report = audit_visa_and_passport_validity(req)

    assert report.ok is True
    assert report.requires_visa is True
    assert report.visa_type_required == "E_VISA"
    assert any("E_VISA" in w for w in report.warnings)


def test_unknown_destination_defaults_to_visa_required():
    # Unmapped destinations default to requiring an e-Visa with 6 months.
    req = VisaCheckRequest(
        passport_country="US",
        destination_country="XY",
        passport_expiry_date="2029-01-01",
        travel_date="2026-10-01",
    )
    report = audit_visa_and_passport_validity(req)

    assert report.requires_visa is True
    assert report.visa_type_required == "E_VISA"
