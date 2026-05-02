"""
tests/test_jurisdiction_policy — Tests for PII jurisdiction handling.

Verifies:
- Jurisdiction enum values
- JurisdictionPolicy dataclass fields
- get_jurisdiction_policy() returns correct policy per jurisdiction
- Fallback to OTHER for unknown jurisdictions
- should_block_pii() logic per jurisdiction
- Agency model has jurisdiction column
- Migration adds jurisdiction column
"""

import pytest

from src.security.jurisdiction_policy import (
    Jurisdiction,
    JurisdictionPolicy,
    get_jurisdiction_policy,
    should_block_pii,
    requires_erasure_capability,
    get_retention_days,
    EU_POLICY,
    IN_POLICY,
    US_POLICY,
    OTHER_POLICY,
    JURISDICTION_POLICIES,
)


class TestJurisdictionEnum:
    def test_all_values(self):
        expected = {"eu", "in", "us", "other"}
        actual = {j.value for j in Jurisdiction}
        assert actual == expected

    def test_is_str_enum(self):
        assert isinstance(Jurisdiction.EU, str)
        assert Jurisdiction.EU == "eu"


class TestJurisdictionPolicies:
    def test_eu_policy_values(self):
        assert EU_POLICY.jurisdiction == Jurisdiction.EU
        assert EU_POLICY.right_to_erasure is True
        assert EU_POLICY.consent_required is True
        assert EU_POLICY.breach_notification_hours == 72
        assert EU_POLICY.data_residency_required is True
        assert EU_POLICY.dpo_required is True
        assert EU_POLICY.extra.get("regulation") == "GDPR"

    def test_in_policy_values(self):
        assert IN_POLICY.jurisdiction == Jurisdiction.IN
        assert IN_POLICY.right_to_erasure is True
        assert IN_POLICY.consent_required is True
        assert IN_POLICY.breach_notification_hours == 72
        assert IN_POLICY.data_residency_required is False
        assert IN_POLICY.dpo_required is False
        assert IN_POLICY.extra.get("regulation") == "DPDP Act 2023"

    def test_us_policy_values(self):
        assert US_POLICY.jurisdiction == Jurisdiction.US
        assert US_POLICY.right_to_erasure is False
        assert US_POLICY.consent_required is False
        assert US_POLICY.breach_notification_hours is None
        assert US_POLICY.data_residency_required is False
        assert US_POLICY.dpo_required is False

    def test_other_policy_values(self):
        assert OTHER_POLICY.jurisdiction == Jurisdiction.OTHER
        assert OTHER_POLICY.right_to_erasure is True
        assert OTHER_POLICY.consent_required is True
        assert OTHER_POLICY.breach_notification_hours == 72


class TestGetJurisdictionPolicy:
    def test_eu(self):
        policy = get_jurisdiction_policy("eu")
        assert policy.jurisdiction == Jurisdiction.EU

    def test_in(self):
        policy = get_jurisdiction_policy("in")
        assert policy.jurisdiction == Jurisdiction.IN

    def test_us(self):
        policy = get_jurisdiction_policy("us")
        assert policy.jurisdiction == Jurisdiction.US

    def test_other(self):
        policy = get_jurisdiction_policy("other")
        assert policy.jurisdiction == Jurisdiction.OTHER

    def test_unknown_falls_back_to_other(self):
        policy = get_jurisdiction_policy("antarctica")
        assert policy.jurisdiction == Jurisdiction.OTHER
        assert policy.consent_required is True

    def test_case_insensitive(self):
        policy = get_jurisdiction_policy("EU")
        assert policy.jurisdiction == Jurisdiction.EU

    def test_whitespace_trimmed(self):
        policy = get_jurisdiction_policy("  in  ")
        assert policy.jurisdiction == Jurisdiction.IN

    def test_all_policies_registered(self):
        assert len(JURISDICTION_POLICIES) == 4
        for j in Jurisdiction:
            assert j in JURISDICTION_POLICIES


class TestShouldBlockPii:
    def test_eu_blocks_pii(self):
        assert should_block_pii("eu") is True

    def test_in_blocks_pii(self):
        assert should_block_pii("in") is True

    def test_us_does_not_block_pii(self):
        assert should_block_pii("us") is False

    def test_other_blocks_pii(self):
        assert should_block_pii("other") is True

    def test_unknown_blocks_pii(self):
        assert should_block_pii("unknown") is True


class TestRequiresErasureCapability:
    def test_eu_requires_erasure(self):
        assert requires_erasure_capability("eu") is True

    def test_in_requires_erasure(self):
        assert requires_erasure_capability("in") is True

    def test_us_no_erasure(self):
        assert requires_erasure_capability("us") is False

    def test_other_requires_erasure(self):
        assert requires_erasure_capability("other") is True


class TestGetRetentionDays:
    def test_eu_no_specific_limit(self):
        assert get_retention_days("eu") is None

    def test_in_no_specific_limit(self):
        assert get_retention_days("in") is None

    def test_us_no_specific_limit(self):
        assert get_retention_days("us") is None


class TestAgencyJurisdictionField:
    def test_agency_model_has_jurisdiction_column(self):
        from spine_api.models.tenant import Agency
        column_names = {c.name for c in Agency.__table__.columns}
        assert "jurisdiction" in column_names

    def test_jurisdiction_column_type(self):
        from spine_api.models.tenant import Agency
        col = Agency.__table__.c.jurisdiction
        assert col.type.length == 10

    def test_jurisdiction_default_is_other(self):
        from spine_api.models.tenant import Agency
        col = Agency.__table__.c.jurisdiction
        assert col.default is not None
        assert col.default.arg == "other"


class TestJurisdictionMigration:
    def test_jurisdiction_migration_exists(self):
        from pathlib import Path
        migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migration_files = list(migration_dir.glob("*jurisdiction*"))
        assert len(migration_files) >= 1

    def test_migration_adds_jurisdiction_column(self):
        from pathlib import Path
        migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
        migration_files = list(migration_dir.glob("*jurisdiction*"))
        content = migration_files[0].read_text()
        assert "jurisdiction" in content
        assert "add_column" in content
        assert "agencies" in content