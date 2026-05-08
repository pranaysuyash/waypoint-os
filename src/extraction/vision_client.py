"""Vision client for document extraction using OpenAI Responses API with Structured Outputs."""

import asyncio
import base64
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Protocol

logger = logging.getLogger(__name__)

# Static error classification — error_summary comes from this dict, never from raw exceptions
ERROR_CODES: dict[str, str] = {
    "api_timeout": "Provider call timed out",
    "api_auth_error": "Provider authentication failed",
    "api_rate_limit": "Provider rate limit exceeded",
    "api_server_error": "Provider internal error",
    "schema_validation_failed": "Response did not match expected schema",
    "empty_response": "Provider returned empty response",
    "unsupported_mime_type": "MIME type not supported by provider",
    "internal_error": "Internal error during extraction",
}


class ExtractionProviderError(Exception):
    """Raised when the vision provider fails or returns invalid data."""

    def __init__(self, error_code: str, detail: str = ""):
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"{error_code}: {detail or ERROR_CODES.get(error_code, 'Unknown error')}")


@dataclass
class VisionExtractionResult:
    """Result from a vision extraction call."""
    fields: dict[str, Optional[str]]
    confidence_scores: dict[str, float]
    overall_confidence: float
    provider_metadata: dict


class VisionClient(Protocol):
    async def extract_from_image(
        self, image_data: bytes, mime_type: str, json_schema: dict, prompt: str,
    ) -> VisionExtractionResult: ...


def _classify_openai_error(exc: Exception) -> str:
    """Map an OpenAI SDK exception to a classified error_code."""
    exc_name = type(exc).__name__
    exc_module = type(exc).__module__ or ""

    if "Timeout" in exc_name:
        return "api_timeout"
    if "AuthenticationError" in exc_name or "AuthError" in exc_name:
        return "api_auth_error"
    if "RateLimitError" in exc_name or "RateLimit" in exc_name:
        return "api_rate_limit"
    if "InternalServerError" in exc_name or "ServerError" in exc_name:
        return "api_server_error"

    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg:
        return "api_timeout"
    if "auth" in msg or "api key" in msg or "unauthorized" in msg:
        return "api_auth_error"
    if "rate" in msg:
        return "api_rate_limit"
    if "server" in msg or "500" in msg or "502" in msg or "503" in msg:
        return "api_server_error"

    return "api_server_error"


class OpenAIVisionClient:
    """Vision client using OpenAI Responses API with Structured Outputs.

    Only the sync OpenAI SDK call is wrapped in asyncio.to_thread.
    The public extract_from_image method is async.
    """

    def __init__(self, model: str = "gpt-5.4-nano", timeout: int = 30) -> None:
        self._model = model
        self._timeout = timeout

        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EXTRACTION_PROVIDER=openai_vision")

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package is required: pip install openai")

        self._client = OpenAI(api_key=api_key)

    async def extract_from_image(
        self, image_data: bytes, mime_type: str, json_schema: dict, prompt: str,
    ) -> VisionExtractionResult:
        """Extract structured fields from an image or PDF using OpenAI Responses API."""
        # Build the user content based on MIME type
        if mime_type == "application/pdf":
            b64_data = base64.b64encode(image_data).decode("utf-8")
            user_content = [
                {"type": "input_text", "text": prompt},
                {"type": "input_file", "file_data": b64_data, "filename": "document.pdf"},
            ]
        else:
            b64_image = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64_image}"
            user_content = [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url},
            ]

        messages = [
            {"role": "system", "content": "You are a document data extraction assistant. Extract only the requested fields accurately."},
            {"role": "user", "content": user_content},
        ]

        start = time.monotonic()
        try:
            response = await asyncio.to_thread(
                self._client.responses.create,
                model=self._model,
                input=messages,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "document_extraction",
                        "strict": True,
                        "schema": json_schema,
                    }
                },
                timeout=self._timeout,
            )
        except Exception as exc:
            raise ExtractionProviderError(_classify_openai_error(exc))

        latency_ms = int((time.monotonic() - start) * 1000)

        # Parse response
        try:
            output_text = response.output_text
        except AttributeError:
            output_text = ""

        if not output_text or not output_text.strip():
            raise ExtractionProviderError("empty_response")

        import json
        try:
            parsed = json.loads(output_text)
        except (json.JSONDecodeError, ValueError):
            raise ExtractionProviderError("schema_validation_failed")

        # Validate: must be dict with string/null values
        if not isinstance(parsed, dict):
            raise ExtractionProviderError("schema_validation_failed")

        validated: dict[str, Optional[str]] = {}
        allowed = set(json_schema.get("properties", {}).keys())
        for key, value in parsed.items():
            if key not in allowed:
                continue  # drop unknown fields
            if value is None:
                validated[key] = None
            elif isinstance(value, str):
                validated[key] = value
            else:
                raise ExtractionProviderError("schema_validation_failed")

        if not validated:
            raise ExtractionProviderError("empty_response")

        # Heuristic confidence: present=0.9, null=0.0
        confidence_scores = {k: (0.9 if v is not None else 0.0) for k, v in validated.items()}
        present_count = sum(1 for v in validated.values() if v is not None)
        overall_confidence = (present_count / len(validated)) * 0.9 if validated else 0.0

        # Token usage from response
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None) if usage else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0) if (prompt_tokens is not None and completion_tokens is not None) else None

        # Cost estimate from pricing table
        cost_estimate_usd = None
        if prompt_tokens is not None and completion_tokens is not None:
            from src.extraction.pricing import calculate_cost
            cost_estimate_usd = calculate_cost(self._model, prompt_tokens, completion_tokens)

        # Pricing source for audit provenance
        from src.extraction.pricing import PRICING_TABLE_SOURCE

        return VisionExtractionResult(
            fields=validated,
            confidence_scores=confidence_scores,
            overall_confidence=overall_confidence,
            provider_metadata={
                "provider_name": "openai_vision",
                "model_name": self._model,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_estimate_usd": cost_estimate_usd,
                "pricing_source": PRICING_TABLE_SOURCE,
            },
        )
