import pytest
from spine_api.services.document_scanner import (
    EICAR_SIGNATURE,
    ScanResult,
    scan_document_bytes,
)


@pytest.mark.asyncio
async def test_scan_clean_pdf_bytes():
    clean_bytes = b"%PDF-1.4 sample content with valid header and metadata"
    result: ScanResult = await scan_document_bytes(clean_bytes, filename="passport.pdf")
    assert result.is_safe is True
    assert result.status == "clean"
    assert result.signature is None


@pytest.mark.asyncio
async def test_scan_detects_eicar_signature():
    infected_bytes = b"Some header " + EICAR_SIGNATURE + b" trailing data"
    result: ScanResult = await scan_document_bytes(infected_bytes, filename="eicar.com")
    assert result.is_safe is False
    assert result.status == "infected"
    assert result.signature == "EICAR-Test-Signature"
