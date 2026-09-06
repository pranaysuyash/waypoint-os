"""
Document & Passport MRZ Extraction API Router (PER-DOC, DOC-01..12).

Provides endpoints for ICAO Doc 9303 checksum verification, TD3 passport parsing,
and e-ticket / hotel voucher extraction.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.intake.mrz_parser_engine import MRZParserEngine

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class MRZParseRequest(BaseModel):
    line1: str = Field(..., description="First 44-character line of TD3 Passport MRZ")
    line2: str = Field(..., description="Second 44-character line of TD3 Passport MRZ")


class VoucherExtractionRequest(BaseModel):
    document_text: str = Field(..., description="Raw OCR or PDF text of ticket/voucher")


@router.post("/mrz/parse-td3")
def parse_td3_mrz(payload: MRZParseRequest) -> Dict[str, Any]:
    """Parses and validates 2-line ICAO Doc 9303 passport MRZ with 7-3-1 Modulo-10 checksums."""
    try:
        parsed = MRZParserEngine.parse_td3_passport(payload.line1, payload.line2)
        return {
            "status": "success",
            "passport": parsed.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vouchers/extract")
def extract_vouchers_and_tickets(payload: VoucherExtractionRequest) -> Dict[str, Any]:
    """Extracts 13-digit e-tickets, 6-character PNRs, and hotel confirmations from raw document text."""
    res = MRZParserEngine.extract_eticket_and_voucher(payload.document_text)
    return {
        "status": "success",
        "extracted": res,
    }
