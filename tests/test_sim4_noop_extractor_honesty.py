"""
FND-0333 (Sim #4): the noop document extractor must say "nothing was
extracted" — never mock fields ("nationality: US", DO_NOT_LOG_*) wearing 0.85
confidence — and identical re-uploads must be flagged, not silently added.
"""

from __future__ import annotations

import asyncio

from spine_api.services.extraction_service import NoopExtractor


def test_noop_extractor_returns_no_fields_and_no_confidence():
    result = asyncio.run(NoopExtractor().extract(b"\x89PNG fake", "image/png", "passport"))
    assert result.fields == {}
    assert result.confidence_scores == {}
    assert result.overall_confidence == 0.0
    assert result.confidence_method == "noop"
    assert result.provider_metadata["status"] == "NOT_EXTRACTED"
    assert "EXTRACTION_MODEL_CHAIN" in result.provider_metadata["reason"]


def test_noop_extractor_does_not_fabricate_nationality():
    result = asyncio.run(NoopExtractor().extract(b"whatever", "image/jpeg", "visa"))
    assert "nationality" not in result.fields
    assert "US" not in result.fields.values()
    assert not any(str(v).startswith("DO_NOT_LOG") for v in result.fields.values())
