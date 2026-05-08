"""Vision client for document extraction using Google Gemini API with structured outputs."""

import asyncio
import base64
import logging
import os
import tempfile
import time
from typing import Optional

from src.extraction.vision_client import (
    ERROR_CODES,
    ExtractionProviderError,
    VisionExtractionResult,
)

logger = logging.getLogger(__name__)


def _classify_gemini_error(exc: Exception) -> str:
    """Map a google-genai SDK exception to a classified error_code."""
    try:
        from google.genai import errors as genai_errors
        if isinstance(exc, genai_errors.ClientError):
            code = getattr(exc, "code", 0)
            if code == 401 or code == 403:
                return "api_auth_error"
            if code == 429:
                return "api_rate_limit"
            if code == 400:
                return "schema_validation_failed"
            return "api_server_error"
        if isinstance(exc, genai_errors.ServerError):
            return "api_server_error"
    except ImportError:
        pass

    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg or "deadline" in msg:
        return "api_timeout"
    if "auth" in msg or "api key" in msg or "unauthorized" in msg or "permission" in msg:
        return "api_auth_error"
    if "rate" in msg or "quota" in msg or "429" in msg:
        return "api_rate_limit"
    if "server" in msg or "500" in msg or "502" in msg or "503" in msg:
        return "api_server_error"

    return "api_server_error"


class GeminiVisionClient:
    """Vision client using Google Gemini API with structured outputs.

    Uses response_schema (JSON Schema dict) for structured extraction.
    PDF uploads use the Files API with temp file cleanup.
    """

    def __init__(self, model: str = "gemini-2.5-flash", timeout: int = 30) -> None:
        self._model = model
        self._timeout = timeout

        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini extraction")

        try:
            from google import genai
        except ImportError:
            raise RuntimeError("google-genai package is required: pip install google-genai")

        self._client = genai.Client(api_key=api_key)

    async def extract_from_image(
        self, image_data: bytes, mime_type: str, json_schema: dict, prompt: str,
    ) -> VisionExtractionResult:
        """Extract structured fields from an image or PDF using Gemini."""
        from google.genai import types

        start = time.monotonic()
        try:
            if mime_type == "application/pdf":
                result = await self._extract_pdf(image_data, json_schema, prompt, types)
            else:
                result = await self._extract_image(image_data, mime_type, json_schema, prompt, types)
        except ExtractionProviderError:
            raise
        except Exception as exc:
            raise ExtractionProviderError(_classify_gemini_error(exc))

        latency_ms = int((time.monotonic() - start) * 1000)

        # Parse response
        try:
            text = result.text
        except AttributeError:
            text = ""

        if not text or not text.strip():
            raise ExtractionProviderError("empty_response")

        import json
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            raise ExtractionProviderError("schema_validation_failed")

        if not isinstance(parsed, dict):
            raise ExtractionProviderError("schema_validation_failed")

        # Validate fields
        validated: dict[str, Optional[str]] = {}
        allowed = set(json_schema.get("properties", {}).keys())
        for key, value in parsed.items():
            if key not in allowed:
                continue
            if value is None:
                validated[key] = None
            elif isinstance(value, str):
                validated[key] = value
            else:
                raise ExtractionProviderError("schema_validation_failed")

        if not validated:
            raise ExtractionProviderError("empty_response")

        # Confidence
        confidence_scores = {k: (0.9 if v is not None else 0.0) for k, v in validated.items()}
        present_count = sum(1 for v in validated.values() if v is not None)
        overall_confidence = (present_count / len(validated)) * 0.9 if validated else 0.0

        # Token usage
        usage_metadata = getattr(result, "usage_metadata", None)
        prompt_tokens = getattr(usage_metadata, "prompt_token_count", None) if usage_metadata else None
        completion_tokens = getattr(usage_metadata, "candidates_token_count", None) if usage_metadata else None
        total_tokens = getattr(usage_metadata, "total_token_count", None) if usage_metadata else None

        # Cost estimate
        from src.extraction.pricing import calculate_cost, PRICING_TABLE_SOURCE
        cost_estimate_usd = None
        if prompt_tokens is not None and completion_tokens is not None:
            cost_estimate_usd = calculate_cost(self._model, prompt_tokens, completion_tokens)

        return VisionExtractionResult(
            fields=validated,
            confidence_scores=confidence_scores,
            overall_confidence=overall_confidence,
            provider_metadata={
                "provider_name": "gemini",
                "model_name": self._model,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_estimate_usd": cost_estimate_usd,
                "pricing_source": PRICING_TABLE_SOURCE,
                "provider_file_retention": "gemini_48h" if mime_type == "application/pdf" else None,
            },
        )

    async def _extract_image(self, image_data: bytes, mime_type: str, json_schema: dict, prompt: str, types) -> object:
        """Extract from image using inline base64."""
        b64_data = base64.b64encode(image_data).decode("utf-8")

        config = types.GenerateContentConfig(
            system_instruction="You are a document data extraction assistant. Extract only the requested fields accurately.",
            response_mime_type="application/json",
            response_schema=json_schema,
        )

        contents = [
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
            types.Part.from_text(text=prompt),
        ]

        return await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model,
            contents=contents,
            config=config,
        )

    async def _extract_pdf(self, file_data: bytes, json_schema: dict, prompt: str, types) -> object:
        """Extract from PDF using Files API with temp file cleanup."""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(file_data)
                tmp_path = f.name

            uploaded = await asyncio.to_thread(
                self._client.files.upload,
                file=tmp_path,
                config=types.UploadFileConfig(mime_type="application/pdf"),
            )

            config = types.GenerateContentConfig(
                system_instruction="You are a document data extraction assistant. Extract only the requested fields accurately.",
                response_mime_type="application/json",
                response_schema=json_schema,
            )

            contents = [uploaded, types.Part.from_text(text=prompt)]

            return await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model,
                contents=contents,
                config=config,
            )
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
