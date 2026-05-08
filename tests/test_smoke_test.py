"""Tests for Phase 4F: Provider smoke test, env gating, and quality report CLI."""

import os
from unittest.mock import AsyncMock, patch

import pytest


class TestSmokeTestEnvGate:
    """Smoke test requires EXTRACTION_SMOKE_TEST=1 and is blocked in production."""

    def test_requires_env_flag(self):
        from src.extraction.smoke_test import _check_env

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "", "APP_ENV": "test"}, clear=False):
            # Remove the key entirely to test missing flag
            os.environ.pop("EXTRACTION_SMOKE_TEST", None)
            result = _check_env()
            assert result is not None
            assert "EXTRACTION_SMOKE_TEST" in result

    def test_blocked_in_production(self):
        from src.extraction.smoke_test import _check_env

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "1", "APP_ENV": "production"}, clear=False):
            result = _check_env()
            assert result is not None
            assert "production" in result.lower()

    def test_allowed_in_test_env(self):
        from src.extraction.smoke_test import _check_env

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "1", "APP_ENV": "test"}, clear=False):
            result = _check_env()
            assert result is None

    def test_allowed_in_local_env(self):
        from src.extraction.smoke_test import _check_env

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "1", "APP_ENV": "local"}, clear=False):
            result = _check_env()
            assert result is None


class TestSyntheticFixtures:
    """Synthetic documents contain fake data only."""

    def test_synthetic_jpeg_is_valid(self):
        from src.extraction.smoke_test import _make_synthetic_jpeg

        data = _make_synthetic_jpeg()
        assert data[:2] == b"\xff\xd8"  # SOI
        assert data[-2:] == b"\xff\xd9"  # EOI
        assert len(data) > 100  # not empty

    def test_synthetic_pdf_is_valid(self):
        from src.extraction.smoke_test import _make_synthetic_pdf

        data = _make_synthetic_pdf()
        assert data.startswith(b"%PDF")
        assert data.rstrip().endswith(b"%%EOF")

    def test_synthetic_jpeg_contains_no_pii(self):
        from src.extraction.smoke_test import _make_synthetic_jpeg

        data = _make_synthetic_jpeg()
        text = data.decode("latin-1")
        # No common PII patterns
        assert "passport" not in text.lower()
        assert "name" not in text.lower()
        assert "dob" not in text.lower()
        assert "social" not in text.lower()

    def test_synthetic_pdf_contains_no_pii(self):
        from src.extraction.smoke_test import _make_synthetic_pdf

        data = _make_synthetic_pdf()
        text = data.decode("latin-1")
        assert "passport" not in text.lower()
        assert "name" not in text.lower()


class TestSmokeTestRun:
    """Smoke test execution with mocked providers."""

    @pytest.mark.asyncio
    async def test_run_returns_error_without_env(self):
        from src.extraction.smoke_test import run_smoke_test

        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            os.environ.pop("EXTRACTION_SMOKE_TEST", None)
            result = await run_smoke_test()
            assert "error" in result

    @pytest.mark.asyncio
    async def test_run_with_noop_extractor(self):
        from src.extraction.smoke_test import run_smoke_test
        from spine_api.services.extraction_service import NoopExtractor, _get_model_chain

        noop = NoopExtractor()
        chain = _get_model_chain(noop)

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "1", "APP_ENV": "test"}, clear=False), \
             patch("spine_api.services.extraction_service.get_extractor", return_value=noop), \
             patch("spine_api.services.extraction_service._get_model_chain", return_value=chain):
            result = await run_smoke_test()

        assert result["total"] >= 1
        assert result["passed"] >= 1
        assert result["results"][0].status == "ok"
        assert result["results"][0].fields_found is not None
        assert result["results"][0].fields_found > 0

    @pytest.mark.asyncio
    async def test_run_filters_by_provider(self):
        from src.extraction.smoke_test import run_smoke_test

        noop = AsyncMock()
        noop.extract = AsyncMock(return_value=AsyncMock(
            fields={"full_name": "TEST"},
            confidence_scores={"full_name": 0.9},
            overall_confidence=0.9,
            confidence_method="model",
            provider_metadata=None,
        ))

        with patch.dict(os.environ, {"EXTRACTION_SMOKE_TEST": "1", "APP_ENV": "test"}, clear=False), \
             patch("spine_api.services.extraction_service.get_extractor", return_value=noop), \
             patch("spine_api.services.extraction_service._get_model_chain",
                   return_value=[("gemini-2.5-flash", noop), ("gpt-5.4-nano", noop)]):
            result = await run_smoke_test(provider="gemini")

        # Only gemini models tested
        assert result["total"] == 1
        assert "gemini" in result["chain"][0]


class TestSmokeTestResultFormat:
    """Result objects contain correct fields, no PII."""

    def test_result_has_no_field_values(self):
        from src.extraction.smoke_test import SmokeTestResult

        result = SmokeTestResult(
            provider="openai",
            model="gpt-5.4-nano",
            status="ok",
            latency_ms=100,
            fields_found=3,
        )

        # Only metadata fields
        d = result.__dict__
        assert "provider" in d
        assert "model" in d
        assert "status" in d
        assert "latency_ms" in d
        assert "fields_found" in d
        # No PII fields
        assert "fields" not in d
        assert "extracted_fields" not in d
        assert "values" not in d

    def test_result_error_format(self):
        from src.extraction.smoke_test import SmokeTestResult

        result = SmokeTestResult(
            provider="gemini",
            model="gemini-2.5-flash",
            status="error",
            error_code="api_timeout",
        )
        assert result.status == "error"
        assert result.error_code == "api_timeout"
        assert result.latency_ms is None


class TestQualityReportCLI:
    """CLI tool output does not contain field values."""

    def test_report_output_no_field_values(self):
        """Smoke test report dict has no field values in output."""
        from src.extraction.smoke_test import SmokeTestResult

        results = [
            SmokeTestResult(provider="openai", model="gpt-5.4-nano", status="ok", latency_ms=100, fields_found=3),
            SmokeTestResult(provider="gemini", model="gemini-2.5-flash", status="error", error_code="api_timeout"),
        ]
        report = {
            "results": results,
            "chain": ["gemini-2.5-flash", "gpt-5.4-nano"],
            "total": 2,
            "passed": 1,
            "failed": 1,
        }

        import json
        output = json.dumps(report, default=str)

        # No PII in output
        assert "full_name" not in output
        assert "passport_number" not in output
        assert "TEST" not in output
        # Metadata IS present
        assert "openai" in output
        assert "gpt-5.4-nano" in output
        assert "api_timeout" in output
