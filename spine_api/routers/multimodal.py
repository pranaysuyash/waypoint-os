"""
spine_api/routers/multimodal.py — Omnichannel Voice Note & Image Fact Extraction Engine (IDEA-123 / Section 3.2).

Parses WhatsApp/email voice note transcripts and booking screenshot OCR text into CanonicalPacket v0.3 facts
with confidence scoring and visual provenance flags.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Header, HTTPException

from spine_api.persistence import TEST_AGENCY_ID, AuditStore, TripStore

router = APIRouter(prefix="/api/v1/multimodal", tags=["Multimodal Fact Extraction"])


class VoiceNoteParseRequest(BaseModel):
    trip_id: Optional[str] = None
    transcript_text: str
    speaker_name: Optional[str] = None
    audio_duration_seconds: Optional[float] = None


class ImageOcrParseRequest(BaseModel):
    trip_id: Optional[str] = None
    ocr_text: str
    image_type: Optional[str] = Field(None, description="flight_confirmation, hotel_quote, passport_scan, itinerary_pdf")


class ExtractedFact(BaseModel):
    category: str
    field_name: str
    value: Any
    confidence: float = 0.95
    provenance_source: str


class MultimodalExtractionResponse(BaseModel):
    ok: bool = True
    trip_id: Optional[str] = None
    source_type: str
    confidence_tier: str  # HIGH, MEDIUM, NEEDS_HUMAN_REVIEW
    overall_confidence: float
    extracted_facts: List[ExtractedFact] = Field(default_factory=list)
    updated_packet_facts: Dict[str, Any] = Field(default_factory=dict)


def _extract_facts_from_text(text: str, source_type: str) -> List[ExtractedFact]:
    """Extract flight, hotel, date, budget, and passenger constraint facts using pattern matching."""
    facts: List[ExtractedFact] = []

    # 1. Flight numbers (e.g. BA178, EK201, UA900, AA100, AF006)
    flight_matches = re.findall(r"\b([A-Z]{2}\s?\d{3,4})\b", text.upper())
    if flight_matches:
        flight_no = flight_matches[0].replace(" ", "")
        facts.append(
            ExtractedFact(
                category="flight",
                field_name="flight_number",
                value=flight_no,
                confidence=0.98,
                provenance_source=source_type,
            )
        )

    # 2. Hotel names / Brands
    hotel_brands = ["Ritz-Carlton", "Four Seasons", "Aman", "Belmond", "Rosewood", "St. Regis", "Mandarin Oriental", "Hilton", "Marriott", "Hyatt"]
    for brand in hotel_brands:
        if re.search(r"\b" + re.escape(brand) + r"\b", text, re.IGNORECASE):
            facts.append(
                ExtractedFact(
                    category="hotel",
                    field_name="hotel_name",
                    value=brand,
                    confidence=0.95,
                    provenance_source=source_type,
                )
            )
            break

    # 3. Budget amounts (e.g. $10,000, $5k, USD 12000, 15000 dollars, budget 20000)
    budget_patterns = [
        r"\$(\d{1,3}(?:,\d{3})*|\d+k?)\b",
        r"(?:USD|budget|price|total)\s?\$?\s?(\d{1,3}(?:,\d{3})*|\d+k?)\b",
        r"\b(\d{1,3}(?:,\d{3})*|\d+k?)\s?(?:USD|dollars|usd)\b",
    ]
    budget_val = None
    for pat in budget_patterns:
        m = re.findall(pat, text, re.IGNORECASE)
        if m:
            raw_b = m[0].lower().replace(",", "")
            budget_val = int(raw_b[:-1]) * 1000 if raw_b.endswith("k") else int(raw_b)
            break

    if budget_val:
        facts.append(
            ExtractedFact(
                category="budget",
                field_name="budget_usd",
                value=budget_val,
                confidence=0.92,
                provenance_source=source_type,
            )
        )

    # 4. Dietary preferences (vegan, vegetarian, gluten-free, nut allergy, kosher, halal)
    dietary_terms = ["vegan", "vegetarian", "gluten-free", "nut-free", "nut allergy", "kosher", "halal"]
    found_dietary = [term for term in dietary_terms if re.search(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE)]
    if found_dietary:
        facts.append(
            ExtractedFact(
                category="preference",
                field_name="dietary_requirements",
                value=", ".join(found_dietary).title(),
                confidence=0.96,
                provenance_source=source_type,
            )
        )

    # 5. Room preferences (ocean view, high floor, king bed, suite, quiet room)
    room_terms = ["ocean view", "sea view", "high floor", "king bed", "suite", "quiet room", "balcony"]
    found_room = [term for term in room_terms if re.search(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE)]
    if found_room:
        facts.append(
            ExtractedFact(
                category="preference",
                field_name="room_preference",
                value=", ".join(found_room).title(),
                confidence=0.94,
                provenance_source=source_type,
            )
        )

    # 6. Passenger counts (e.g. 2 adults, 4 guests, 2 passengers)
    pax_matches = re.findall(r"\b(\d+)\s?(?:adults|guests|passengers|pax|travelers)\b", text, re.IGNORECASE)
    if pax_matches:
        facts.append(
            ExtractedFact(
                category="travelers",
                field_name="passenger_count",
                value=int(pax_matches[0]),
                confidence=0.95,
                provenance_source=source_type,
            )
        )

    return facts


def _determine_confidence_tier(confidence: float) -> str:
    if confidence >= 0.90:
        return "HIGH"
    elif confidence >= 0.70:
        return "MEDIUM"
    else:
        return "NEEDS_HUMAN_REVIEW"


@router.post("/voice-note", response_model=MultimodalExtractionResponse)
def parse_voice_note_transcript(
    body: VoiceNoteParseRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Extract structured travel facts from a voice note transcript."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    if not body.transcript_text or not body.transcript_text.strip():
        raise HTTPException(status_code=400, detail="transcript_text cannot be empty")

    facts = _extract_facts_from_text(body.transcript_text, source_type="voice_note")
    overall_conf = round(sum(f.confidence for f in facts) / len(facts), 2) if facts else 0.70
    conf_tier = _determine_confidence_tier(overall_conf)

    updated_packet_facts: Dict[str, Any] = {}
    for f in facts:
        updated_packet_facts[f.field_name] = f.value

    if body.trip_id:
        trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
        if trip:
            packet = trip.setdefault("packet", {})
            for key, val in updated_packet_facts.items():
                packet[key] = val
            packet["multimodal_voice_note_extracted"] = True
            packet["multimodal_confidence_tier"] = conf_tier
            TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="multimodal_fact_extracted",
        user_id=agency_id,
        details={
            "source_type": "voice_note",
            "trip_id": body.trip_id,
            "speaker_name": body.speaker_name,
            "facts_count": len(facts),
            "confidence_tier": conf_tier,
        },
    )

    return MultimodalExtractionResponse(
        ok=True,
        trip_id=body.trip_id,
        source_type="voice_note",
        confidence_tier=conf_tier,
        overall_confidence=overall_conf,
        extracted_facts=facts,
        updated_packet_facts=updated_packet_facts,
    )


@router.post("/image-ocr", response_model=MultimodalExtractionResponse)
def parse_image_ocr(
    body: ImageOcrParseRequest,
    x_agency_id: Optional[str] = Header(None, alias="X-Agency-ID"),
):
    """Extract structured travel facts from screenshot or document OCR text."""
    agency_id = x_agency_id or TEST_AGENCY_ID
    if not body.ocr_text or not body.ocr_text.strip():
        raise HTTPException(status_code=400, detail="ocr_text cannot be empty")

    facts = _extract_facts_from_text(body.ocr_text, source_type=f"image_ocr:{body.image_type or 'screenshot'}")
    overall_conf = round(sum(f.confidence for f in facts) / len(facts), 2) if facts else 0.70
    conf_tier = _determine_confidence_tier(overall_conf)

    updated_packet_facts: Dict[str, Any] = {}
    for f in facts:
        updated_packet_facts[f.field_name] = f.value

    if body.trip_id:
        trip = TripStore.get_trip_for_agency(body.trip_id, agency_id)
        if trip:
            packet = trip.setdefault("packet", {})
            for key, val in updated_packet_facts.items():
                packet[key] = val
            packet["multimodal_ocr_extracted"] = True
            packet["multimodal_confidence_tier"] = conf_tier
            TripStore.save_trip(trip, agency_id=agency_id)

    AuditStore.log_event(
        event_type="multimodal_fact_extracted",
        user_id=agency_id,
        details={
            "source_type": "image_ocr",
            "image_type": body.image_type,
            "trip_id": body.trip_id,
            "facts_count": len(facts),
            "confidence_tier": conf_tier,
        },
    )

    return MultimodalExtractionResponse(
        ok=True,
        trip_id=body.trip_id,
        source_type="image_ocr",
        confidence_tier=conf_tier,
        overall_confidence=overall_conf,
        extracted_facts=facts,
        updated_packet_facts=updated_packet_facts,
    )
