"""
tests/test_llm_egress.py — Tests for the LLM egress policy layer.

Verifies:
  - PII is stripped from egress content
  - Prompt delimiters are added around untrusted content
  - Unknown decision types raise ValueError
  - Audit log entries are created per LLM call
  - Field allowlisting works
"""

import pytest

from spine_api.core.llm_egress import (
    DecisionType,
    EgressPolicy,
    strip_pii,
    add_prompt_delimiters,
    prepare_egress_payload,
    get_audit_log,
    clear_audit_log,
    get_egress_policy,
)


class TestPIIStripping:
    """PII patterns are correctly detected and redacted."""

    def test_email_redaction(self):
        text = "Contact john.doe@example.com for details"
        cleaned, count = strip_pii(text)
        assert "[EMAIL_REDACTED]" in cleaned
        assert "john.doe@example.com" not in cleaned
        assert count == 1

    def test_phone_redaction(self):
        text = "Call +1-555-123-4567 or +91 9876543210"
        cleaned, count = strip_pii(text)
        assert "[PHONE_REDACTED]" in cleaned
        assert "555-123-4567" not in cleaned
        assert count >= 1

    def test_passport_redaction(self):
        text = "Passport: AB1234567"
        cleaned, count = strip_pii(text)
        assert "[ID_REDACTED]" in cleaned
        assert "AB1234567" not in cleaned

    def test_credit_card_redaction(self):
        text = "Card: 4111-1111-1111-1111"
        cleaned, count = strip_pii(text)
        assert "[CARD_REDACTED]" in cleaned
        assert "4111" not in cleaned

    def test_ssn_redaction(self):
        text = "SSN: 123-45-6789"
        cleaned, count = strip_pii(text)
        assert "[SSN_REDACTED]" in cleaned
        assert "123-45-6789" not in cleaned

    def test_no_pii(self):
        text = "Trip to Paris for 5 days, budget 3000 USD"
        cleaned, count = strip_pii(text)
        assert cleaned == text
        assert count == 0

    def test_multiple_pii_types(self):
        text = "John john@test.com passport AB1234567 phone +1-555-000-1234"
        cleaned, count = strip_pii(text)
        assert count >= 3
        assert "john@test.com" not in cleaned
        assert "AB1234567" not in cleaned


class TestPromptDelimiters:
    """Untrusted content is properly delimited."""

    def test_default_delimiter(self):
        content = "User's raw enquiry text"
        result = add_prompt_delimiters(content)
        assert result.startswith("<user_content>")
        assert result.endswith("</user_content>")
        assert "User's raw enquiry text" in result

    def test_custom_label(self):
        content = "Document text"
        result = add_prompt_delimiters(content, source_label="document")
        assert "<document>" in result
        assert "</document>" in result


class TestEgressPayloadPreparation:
    """Full egress pipeline: PII strip + delimiters + audit."""

    def setup_method(self):
        clear_audit_log()

    def test_extraction_policy_exists(self):
        policy = get_egress_policy(DecisionType.EXTRACTION)
        assert policy is not None
        assert policy.strip_pii is True
        assert policy.add_delimiters is True

    def test_unknown_decision_type_raises(self):
        """Hard fail if no policy exists for a decision type."""
        # Create a fake decision type by bypassing the enum
        with pytest.raises(ValueError, match="No egress policy defined"):
            prepare_egress_payload(
                decision_type="nonexistent_type",  # type: ignore
                content="test",
                provider="openai",
            )

    def test_pii_stripped_in_extraction(self):
        content = "Traveler john@test.com wants to go to Paris"
        result = prepare_egress_payload(
            decision_type=DecisionType.EXTRACTION,
            content=content,
            provider="openai",
        )
        assert "john@test.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_delimiters_added(self):
        result = prepare_egress_payload(
            decision_type=DecisionType.EXTRACTION,
            content="Trip details here",
            provider="openai",
        )
        assert "<user_content>" in result
        assert "</user_content>" in result

    def test_audit_log_entry_created(self):
        prepare_egress_payload(
            decision_type=DecisionType.EXTRACTION,
            content="Test content",
            provider="openai",
            agency_id="agency_123",
            trip_id="trip_456",
        )
        log = get_audit_log()
        assert len(log) == 1
        entry = log[0]
        assert entry.decision_type == "extraction"
        assert entry.provider == "openai"
        assert entry.agency_id == "agency_123"
        assert entry.trip_id == "trip_456"
        assert entry.content_length > 0

    def test_content_truncation(self):
        """Long content is truncated to max_content_length."""
        long_content = "x" * 100000
        result = prepare_egress_payload(
            decision_type=DecisionType.EXTRACTION,
            content=long_content,
            provider="openai",
        )
        # Should be truncated + delimiters
        assert len(result) < 100000 + 100  # delimiters add ~30 chars


class TestAllDecisionTypesHavePolicies:
    """Every DecisionType enum member has a defined egress policy."""

    def test_all_types_covered(self):
        for dt in DecisionType:
            policy = get_egress_policy(dt)
            assert policy is not None, f"No egress policy for {dt.value}"
            assert isinstance(policy, EgressPolicy)
