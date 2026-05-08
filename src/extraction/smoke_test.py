"""Provider smoke test: verifies each configured extraction provider can process a trivial document.

Tier 1 only — trivial synthetic documents with fake data to prove the provider call path works.
No accuracy measurement, no realistic document generation.

Requires EXTRACTION_SMOKE_TEST=1 to run. Blocked when APP_ENV=production.
"""

import io
import logging
import os
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SmokeTestResult:
    provider: str
    model: str
    status: str  # "ok" | "error" | "skipped"
    latency_ms: int | None = None
    fields_found: int | None = None
    error_code: str | None = None


def _check_env() -> str | None:
    """Return error message if smoke test cannot run, None if OK."""
    if os.environ.get("EXTRACTION_SMOKE_TEST") != "1":
        return "EXTRACTION_SMOKE_TEST=1 not set"
    if os.environ.get("APP_ENV", "production").lower() == "production":
        return "APP_ENV=production — smoke test blocked"
    return None


def _make_synthetic_jpeg() -> bytes:
    """Create a minimal valid JPEG with fake text content for smoke testing."""
    # Minimal JPEG: SOI marker + APP0 + minimal scan data
    # This is enough for the provider to accept and attempt extraction
    soi = b"\xff\xd8"
    # APP0 (JFIF) marker
    app0 = (
        b"\xff\xe0"
        b"\x00\x10"  # length
        b"JFIF\x00"  # identifier
        b"\x01\x01"  # version
        b"\x00"      # units
        b"\x00\x01"  # X density
        b"\x00\x01"  # Y density
        b"\x00\x00"  # thumbnail
    )
    # DQT (quantization table) — minimal
    dqt = b"\xff\xdb\x00\x43\x00" + b"\x10" * 64
    # SOF0 (start of frame) — 1x1 pixel, 1 component
    sof = (
        b"\xff\xc0"
        b"\x00\x0b"  # length
        b"\x08"      # precision
        b"\x00\x01"  # height
        b"\x00\x01"  # width
        b"\x01"      # num components
        b"\x01\x11\x00"  # component spec
    )
    # DHT (Huffman table) — minimal DC
    dht = (
        b"\xff\xc4"
        b"\x00\x1f"
        b"\x00"
        b"\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b"
    )
    # SOS (start of scan)
    sos = b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00\x7b\x40"
    # EOI
    eoi = b"\xff\xd9"

    return soi + app0 + dqt + sof + dht + sos + eoi


def _make_synthetic_pdf() -> bytes:
    """Create a minimal valid PDF for smoke testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF\n"
    )


async def _run_provider_smoke(model_name: str, extractor) -> SmokeTestResult:
    """Run smoke extraction against a single provider."""
    from spine_api.services.extraction_service import _resolve_provider_name

    provider = _resolve_provider_name(model_name)
    image_data = _make_synthetic_jpeg()

    start = time.monotonic()
    try:
        result = await extractor.extract(image_data, "image/jpeg", "passport")
        latency = int((time.monotonic() - start) * 1000)
        fields_found = sum(1 for v in result.fields.values() if v is not None)
        return SmokeTestResult(
            provider=provider,
            model=model_name,
            status="ok",
            latency_ms=latency,
            fields_found=fields_found,
        )
    except Exception as e:
        latency = int((time.monotonic() - start) * 1000)
        from src.extraction.vision_client import ExtractionProviderError
        if isinstance(e, ExtractionProviderError):
            error_code = e.error_code
        else:
            error_code = "internal_error"
        return SmokeTestResult(
            provider=provider,
            model=model_name,
            status="error",
            latency_ms=latency,
            error_code=error_code,
        )


async def run_smoke_test(provider: str | None = None) -> dict:
    """Run extraction smoke test against configured providers.

    Args:
        provider: If set, only test this provider/model. Otherwise test all in chain.

    Returns dict with per-provider results: {provider, model, status, latency_ms, fields_found}
    Must have EXTRACTION_SMOKE_TEST=1 set to run. Blocked when APP_ENV=production.
    """
    env_error = _check_env()
    if env_error:
        return {"error": env_error, "results": []}

    from spine_api.services.extraction_service import get_extractor, _get_model_chain

    extractor = get_extractor()
    models = _get_model_chain(extractor)

    # Filter to specific provider if requested
    if provider:
        models = [(m, e) for m, e in models if provider in m]
        if not models:
            return {"error": f"No models matching '{provider}' in chain", "results": []}

    results = []
    for model_name, model_extractor in models:
        result = await _run_provider_smoke(model_name, model_extractor)
        results.append(result)

    return {
        "results": results,
        "chain": [m for m, _ in models],
        "total": len(results),
        "passed": sum(1 for r in results if r.status == "ok"),
        "failed": sum(1 for r in results if r.status == "error"),
    }


def run_smoke_test_sync(provider: str | None = None) -> dict:
    """Synchronous wrapper for CLI usage."""
    import asyncio
    return asyncio.run(run_smoke_test(provider))


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)

    result = run_smoke_test_sync()
    if "error" in result and "results" not in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))
