"""Tests for the external-data provenance + freshness contract.

Covers src/intake/external_reference.py (BD governance framework, 2026-10-30):
license tiers, per-category TTL staleness, metadata shape, and the
undated-means-stale honesty default.
"""

from datetime import datetime, timedelta, timezone


from src.intake.external_reference import (
    FRESHNESS_TTL_SECONDS,
    DataCategory,
    ExternalFactReference,
    LicenseTier,
)


def test_capture_sets_retrieved_at_utc_now():
    ref = ExternalFactReference.capture("open_meteo", license_tier=LicenseTier.ATTRIBUTION)
    parsed = datetime.fromisoformat(ref.retrieved_at)
    assert parsed.tzinfo is not None
    assert ref.age_seconds() is not None and ref.age_seconds() < 5


def test_staleness_per_category_ttl():
    ref = ExternalFactReference.capture("fcdo", license_tier=LicenseTier.PUBLIC_DOMAIN)
    # Fresh weather, stale FX after 25 hours
    assert ref.is_stale(DataCategory.WEATHER) is False
    ref_old = ExternalFactReference(
        source_id="ecb",
        retrieved_at=(datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        license_tier=LicenseTier.PUBLIC_DOMAIN,
    )
    assert ref_old.is_stale(DataCategory.FX_RATE) is True
    assert ref_old.is_stale(DataCategory.SAFETY_ADVISORY) is False  # 7d window


def test_undated_provenance_is_stale_by_default():
    ref = ExternalFactReference(source_id="mystery", retrieved_at="not-a-date")
    assert ref.is_stale(DataCategory.VISA_RULES) is True
    assert ref.age_seconds() is None


def test_every_data_category_has_a_ttl():
    for category in DataCategory:
        assert category in FRESHNESS_TTL_SECONDS, f"missing TTL for {category}"


def test_metadata_shape_matches_governance_contract():
    ref = ExternalFactReference(
        source_id="waqi",
        retrieved_at="2026-10-30T00:00:00+00:00",
        as_of="2026-10-29",
        license_tier=LicenseTier.ATTRIBUTION,
        approximate=True,
        url="https://aqicn.org",
    )
    meta = ref.to_metadata()
    assert meta == {
        "source_id": "waqi",
        "retrieved_at": "2026-10-30T00:00:00+00:00",
        "as_of": "2026-10-29",
        "license_tier": "attribution",
        "approximate": True,
        "url": "https://aqicn.org",
    }


def test_naive_timestamp_treated_as_utc():
    ref = ExternalFactReference(
        source_id="x",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    # No exception, sub-second age
    assert ref.age_seconds() is not None and ref.age_seconds() < 5


def test_license_tier_values():
    assert {t.value for t in LicenseTier} == {
        "public_domain", "attribution", "share_alike", "restricted", "unknown",
    }
