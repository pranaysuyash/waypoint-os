"""Gemini Vision-based document extractor. Wraps GeminiVisionClient with extraction schemas."""

import logging

from src.extraction.schemas import get_schema, build_json_schema
from src.extraction.gemini_vision_client import GeminiVisionClient
from src.extraction.vision_client import VisionExtractionResult

logger = logging.getLogger(__name__)


class GeminiVisionExtractor:
    """Document extractor using Google Gemini API with structured outputs.

    extract() is async. MIME prevalidation happens in the endpoint before
    run_extraction() — no MIME check here.
    """

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self._model = model
        self._client = GeminiVisionClient(model=model)  # raises if GEMINI_API_KEY missing

    async def extract(self, file_data: bytes, mime_type: str, document_type: str) -> "ExtractionResult":
        from spine_api.services.extraction_service import ExtractionResult

        schema = get_schema(document_type)
        fields = schema["fields"]
        prompt = schema["prompt"]
        json_schema = build_json_schema(fields)

        vision_result: VisionExtractionResult = await self._client.extract_from_image(
            image_data=file_data,
            mime_type=mime_type,
            json_schema=json_schema,
            prompt=prompt,
        )

        return ExtractionResult(
            fields=vision_result.fields,
            confidence_scores=vision_result.confidence_scores,
            overall_confidence=vision_result.overall_confidence,
            confidence_method="heuristic_presence",
            provider_metadata=vision_result.provider_metadata,
        )
