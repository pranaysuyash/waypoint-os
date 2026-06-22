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


# ---------------------------------------------------------------------------
# Shared post-processing: JSON parse → field validation → confidence → result
# ---------------------------------------------------------------------------


def _parse_and_validate_response(
    output_text: str,
    json_schema: dict,
) -> dict[str, Optional[str]]:
    """Parse provider output text as JSON and validate against schema fields.

    Shared by all vision clients to eliminate duplicate post-processing.
    Returns validated field dict with string/None values.
    Raises ExtractionProviderError on parse or validation failure.
    """
    import json

    if not output_text or not output_text.strip():
        raise ExtractionProviderError("empty_response")

    try:
        parsed = json.loads(output_text)
    except (json.JSONDecodeError, ValueError):
        raise ExtractionProviderError("schema_validation_failed")

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

    return validated


def _build_extraction_result(
    *,
    provider_name: str,
    model: str,
    output_text: str,
    latency_ms: int,
    validated: dict[str, Optional[str]],
    logprobs_data: Optional[list] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    extra_metadata: Optional[dict] = None,
) -> VisionExtractionResult:
    """Build a VisionExtractionResult with confidence scoring.

    Shared by all vision clients. Computes validation-based confidence
    (with optional logprobs blend) and assembles provider_metadata.
    """
    from src.extraction.confidence import compute_field_confidences, compute_overall_confidence
    from src.extraction.pricing import calculate_cost, PRICING_TABLE_SOURCE

    confidence_scores, confidence_method_used = compute_field_confidences(
        validated, logprobs_data=logprobs_data, output_text=output_text,
    )
    overall_confidence = compute_overall_confidence(confidence_scores, logprobs_data=logprobs_data)

    cost_estimate_usd = None
    if prompt_tokens is not None and completion_tokens is not None:
        cost_estimate_usd = calculate_cost(model, prompt_tokens, completion_tokens)

    metadata = {
        "provider_name": provider_name,
        "model_name": model,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_estimate_usd": cost_estimate_usd,
        "pricing_source": PRICING_TABLE_SOURCE,
        "confidence_method": confidence_method_used,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    return VisionExtractionResult(
        fields=validated,
        confidence_scores=confidence_scores,
        overall_confidence=overall_confidence,
        provider_metadata=metadata,
    )


def _extract_logprobs(response: object) -> Optional[list]:
    """Extract token-level logprobs from a provider response object.

    Checks Responses API output items first, then top-level logprobs
    (Chat Completions compatibility). Returns None if unavailable.
    """
    try:
        # Responses API stores logprobs on the output content items
        output_items = getattr(response, "output", None) or []
        for item in output_items:
            content_list = getattr(item, "content", None) or []
            for content_item in content_list:
                lp = getattr(content_item, "logprobs", None)
                if lp is not None:
                    return list(lp) if not isinstance(lp, list) else lp
        # Also check top-level logprobs (Chat Completions compatibility)
        top_logprobs = getattr(response, "logprobs", None)
        if top_logprobs is not None:
            content_logprobs = getattr(top_logprobs, "content", None)
            if content_logprobs is not None:
                return list(content_logprobs) if not isinstance(content_logprobs, list) else content_logprobs
    except (AttributeError, TypeError):
        pass
    return None


# ---------------------------------------------------------------------------
# Typed error classification
# ---------------------------------------------------------------------------

def _classify_openai_error(exc: Exception) -> str:
    """Map an OpenAI SDK exception to a classified error_code.

    Uses isinstance() checks on typed SDK exceptions first (deterministic,
    testable), then falls back to string matching for unknown SDK versions.
    """
    # Typed checks — prefer SDK exception hierarchy over string matching
    try:
        import openai
        if isinstance(exc, openai.APITimeoutError):
            return "api_timeout"
        if isinstance(exc, openai.AuthenticationError):
            return "api_auth_error"
        if isinstance(exc, openai.RateLimitError):
            return "api_rate_limit"
        if isinstance(exc, (openai.InternalServerError, openai.APIStatusError)):
            # APIStatusError covers 5xx; narrow below if needed
            status = getattr(exc, "status_code", 0)
            if isinstance(exc, openai.InternalServerError) or (500 <= status < 600):
                return "api_server_error"
    except (ImportError, AttributeError):
        pass  # openai SDK not installed or exception types changed

    # String-matching fallback — handles edge cases and unknown SDK versions
    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg:
        return "api_timeout"
    if "auth" in msg or "api key" in msg or "unauthorized" in msg:
        return "api_auth_error"
    if "rate" in msg or "429" in msg:
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

        # Extract output text
        try:
            output_text = response.output_text
        except AttributeError:
            output_text = ""

        # Shared post-processing: parse JSON, validate fields
        validated = _parse_and_validate_response(output_text, json_schema)

        # Extract logprobs from response if available
        logprobs_data = _extract_logprobs(response)

        # Token usage from response
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None) if usage else None
        completion_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0) if (prompt_tokens is not None and completion_tokens is not None) else None

        return _build_extraction_result(
            provider_name="openai_vision",
            model=self._model,
            output_text=output_text,
            latency_ms=latency_ms,
            validated=validated,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            logprobs_data=logprobs_data,
        )
