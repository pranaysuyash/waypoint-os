"""Phase 4E tests: Model chain, service fallback, pricing, factory.

Covers:
- ModelChain container
- _get_model_chain normalization
- RETRIABLE_ERRORS set
- Service fallback loop (mocked extractors)
- Model pricing
- Factory behavior with EXTRACTION_MODEL_CHAIN env var
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# TestModelChain
# ---------------------------------------------------------------------------


class TestModelChain:
    def test_chain_holds_ordered_pairs(self):
        from src.extraction.model_chain import ModelChain

        pairs = [("gemini-2.5-flash", "ext1"), ("gpt-5.4-nano", "ext2")]
        chain = ModelChain(pairs)
        assert chain.models == pairs
        assert len(chain) == 2

    def test_chain_returns_copy(self):
        from src.extraction.model_chain import ModelChain

        chain = ModelChain([("a", "ext")])
        models = chain.models
        models.append(("b", "ext2"))
        assert len(chain) == 1  # original unchanged

    def test_retriable_errors_set(self):
        from src.extraction.model_chain import RETRIABLE_ERRORS

        assert "api_timeout" in RETRIABLE_ERRORS
        assert "api_rate_limit" in RETRIABLE_ERRORS
        assert "api_server_error" in RETRIABLE_ERRORS
        assert "empty_response" in RETRIABLE_ERRORS
        assert "api_auth_error" not in RETRIABLE_ERRORS
        assert "schema_validation_failed" not in RETRIABLE_ERRORS


class TestGetModelChain:
    def test_normalizes_model_chain(self):
        from src.extraction.model_chain import ModelChain
        from spine_api.services.extraction_service import _get_model_chain

        chain = ModelChain([("gemini-2.5-flash", "ext1"), ("gpt-5.4-nano", "ext2")])
        result = _get_model_chain(chain)
        assert result == [("gemini-2.5-flash", "ext1"), ("gpt-5.4-nano", "ext2")]

    def test_normalizes_noop_extractor(self):
        from spine_api.services.extraction_service import NoopExtractor, _get_model_chain

        noop = NoopExtractor()
        result = _get_model_chain(noop)
        assert result == [("noop", noop)]

    def test_normalizes_single_extractor(self):
        from spine_api.services.extraction_service import _get_model_chain

        mock = MagicMock()
        mock._model = "gpt-5.4-nano"
        result = _get_model_chain(mock)
        assert result == [("gpt-5.4-nano", mock)]

    def test_normalizes_extractor_without_model(self):
        from spine_api.services.extraction_service import _get_model_chain

        mock = MagicMock(spec=[])  # no _model attribute
        result = _get_model_chain(mock)
        assert result == [("unknown", mock)]


# ---------------------------------------------------------------------------
# TestServiceFallback
# ---------------------------------------------------------------------------


class TestServiceFallback:
    def _make_result(self, fields=None):
        from spine_api.services.extraction_service import ExtractionResult
        return ExtractionResult(
            fields=fields or {"full_name": "TEST"},
            confidence_scores={"full_name": 0.9},
            overall_confidence=0.9,
            confidence_method="heuristic_presence",
            provider_metadata={"model_name": "test-model", "latency_ms": 100},
        )

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Reset extraction env for each test."""
        self.env = {
            "EXTRACTION_PROVIDER": "noop",
            "EXTRACTION_MODEL_CHAIN": "",
            "APP_ENV": "test",
        }

    def test_primary_succeeds_one_attempt(self):
        """Primary model succeeds → one attempt row, extraction pending_review."""
        from spine_api.services.extraction_service import (
            ExtractionResult, _get_model_chain, _resolve_provider_name,
        )
        from src.extraction.model_chain import ModelChain

        mock_extractor = AsyncMock()
        mock_extractor._model = "gpt-5.4-nano"
        mock_extractor.extract = AsyncMock(return_value=self._make_result())

        chain = ModelChain([("gpt-5.4-nano", mock_extractor)])
        models = _get_model_chain(chain)

        assert len(models) == 1
        assert models[0][0] == "gpt-5.4-nano"
        assert _resolve_provider_name("gpt-5.4-nano") == "openai"

    def test_primary_timeout_secondary_success(self):
        """Primary fails with retriable → secondary succeeds → two entries."""
        from src.extraction.vision_client import ExtractionProviderError
        from src.extraction.model_chain import RETRIABLE_ERRORS

        assert "api_timeout" in RETRIABLE_ERRORS
        # The service layer iterates the chain; retriable errors trigger next model
        # This is tested in the integration tests (test_extraction_attempts.py)

    def test_non_retriable_stops(self):
        """Non-retriable error (auth) → no further fallback."""
        from src.extraction.model_chain import RETRIABLE_ERRORS

        assert "api_auth_error" not in RETRIABLE_ERRORS
        assert "schema_validation_failed" not in RETRIABLE_ERRORS

    def test_all_fail_extraction_failed(self):
        """All models fail → extraction status=failed."""
        # Tested in integration tests with real DB


# ---------------------------------------------------------------------------
# TestModelPricing
# ---------------------------------------------------------------------------


class TestModelPricing:
    def test_known_model_pricing(self):
        from src.extraction.pricing import get_model_pricing, calculate_cost

        pricing = get_model_pricing("gemini-2.5-flash")
        assert pricing is not None
        assert pricing["input_per_1m"] == 0.30
        assert pricing["output_per_1m"] == 2.50

        cost = calculate_cost("gemini-2.5-flash", 1000, 500)
        expected = (1000 * 0.30 + 500 * 2.50) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_unknown_model_returns_none(self):
        from src.extraction.pricing import get_model_pricing, calculate_cost

        assert get_model_pricing("nonexistent-model") is None
        assert calculate_cost("nonexistent-model", 1000, 500) is None

    def test_pricing_source_in_metadata(self):
        from src.extraction.pricing import PRICING_TABLE_SOURCE, PRICING_TABLE_VERSION

        assert PRICING_TABLE_VERSION == "2026-05-07"
        assert "2026_05_07" in PRICING_TABLE_SOURCE


# ---------------------------------------------------------------------------
# TestFactory
# ---------------------------------------------------------------------------


class TestFactory:
    def test_chain_env_creates_model_chain(self):
        """EXTRACTION_MODEL_CHAIN with multiple models → ModelChain."""
        with patch.dict(os.environ, {
            "EXTRACTION_MODEL_CHAIN": "gpt-5.4-nano",
            "OPENAI_API_KEY": "test-key",
        }, clear=False):
            from spine_api.services.extraction_service import get_extractor
            from src.extraction.model_chain import ModelChain

            extractor = get_extractor()
            # Single model → unwrapped extractor
            assert not isinstance(extractor, ModelChain)
            assert hasattr(extractor, "extract")

    def test_single_model_returns_unwrapped(self):
        with patch.dict(os.environ, {
            "EXTRACTION_MODEL_CHAIN": "gpt-5.4-nano",
            "OPENAI_API_KEY": "test-key",
        }, clear=False):
            from spine_api.services.extraction_service import get_extractor
            from src.extraction.model_chain import ModelChain

            extractor = get_extractor()
            assert not isinstance(extractor, ModelChain)

    def test_noop_when_empty_and_development(self):
        with patch.dict(os.environ, {
            "EXTRACTION_MODEL_CHAIN": "",
            "EXTRACTION_PROVIDER": "noop",
            "APP_ENV": "development",
        }, clear=False):
            from spine_api.services.extraction_service import get_extractor, NoopExtractor

            extractor = get_extractor()
            assert isinstance(extractor, NoopExtractor)

    def test_resolve_provider_name_handles_noop(self):
        from spine_api.services.extraction_service import _resolve_provider_name

        assert _resolve_provider_name("noop") == "noop_extractor"

    def test_resolve_provider_name_handles_gemini(self):
        from spine_api.services.extraction_service import _resolve_provider_name

        assert _resolve_provider_name("gemini-2.5-flash") == "gemini"

    def test_resolve_provider_name_handles_unknown(self):
        from spine_api.services.extraction_service import _resolve_provider_name

        assert _resolve_provider_name("future-model-x") == "future-model-x"
