"""Confidence scoring for document extraction results.

Provides multiple confidence calculation methods that form a fallback chain:

1. **logprobs** — token-level log probability averaging from the provider.
   Highest fidelity signal. Requires provider to expose logprobs.

2. **validation** — per-field format validation (regex, date plausibility).
   Provider-agnostic. Always available when a field value is present.

3. **heuristic_presence** — simple present/absent (legacy fallback).
   Used when no other signal is available.

The confidence_method field on ExtractionResult records which method produced
the scores, for audit trail and eval reproducibility.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Field-level validators
# ---------------------------------------------------------------------------

_PASSPORT_RE = re.compile(r"^[A-Z0-9]{6,12}$", re.IGNORECASE)
_VISA_NUM_RE = re.compile(r"^[A-Z0-9]{4,15}$", re.IGNORECASE)
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d %b %Y",
    "%B %d, %Y",
)


def _parse_date(date_str: str) -> Optional[datetime]:
    """Try to parse a date string in common formats."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _validate_date_field(value: str) -> float:
    """Validate a date-of-birth field and return confidence."""
    parsed = _parse_date(value)
    if parsed is None:
        return 0.3
    age = (datetime.now() - parsed).days / 365.25
    if 0 < age < 120:
        return 0.85
    return 0.4  # implausible age


def _validate_future_date(value: str) -> float:
    """Validate a future date (expiry) and return confidence."""
    parsed = _parse_date(value)
    if parsed is None:
        return 0.3
    if parsed > datetime.now():
        return 0.85
    return 0.5  # expired but could be correct data


# Per-field validation functions: field_name -> (value) -> confidence
_FIELD_VALIDATORS = {
    "passport_number": lambda v: 0.85 if _PASSPORT_RE.match(v.strip()) else 0.4,
    "date_of_birth": _validate_date_field,
    "passport_expiry": _validate_future_date,
    "visa_expiry": _validate_future_date,
    "nationality": lambda v: 0.8 if len(v.strip()) >= 2 else 0.4,
    "full_name": lambda v: 0.85 if len(v.strip().split()) >= 2 else 0.6,
    "visa_type": lambda v: 0.7 if len(v.strip()) >= 2 else 0.4,
    "visa_number": lambda v: 0.8 if _VISA_NUM_RE.match(v.strip()) else 0.4,
    "insurance_provider": lambda v: 0.7 if len(v.strip()) >= 2 else 0.4,
    "insurance_policy_number": lambda v: 0.75 if len(v.strip()) >= 4 else 0.4,
}


def _validate_field(field_name: str, value: str) -> float:
    """Return a confidence score (0.0–1.0) based on format validation."""
    validator = _FIELD_VALIDATORS.get(field_name)
    if validator:
        return validator(value.strip())
    return 0.6  # unknown field — moderate confidence


# ---------------------------------------------------------------------------
# Logprobs → confidence conversion
# ---------------------------------------------------------------------------


def logprobs_to_overall_confidence(logprobs_data: list) -> Optional[float]:
    """Convert token-level logprobs to a single overall confidence score.

    Returns None if logprobs data is unavailable or empty.
    Uses the geometric mean of token probabilities (exp of average log-prob).
    """
    if not logprobs_data:
        return None

    logprob_values: list[float] = []
    for item in logprobs_data:
        if isinstance(item, dict):
            lp = item.get("logprob")
        else:
            lp = getattr(item, "logprob", None)
        if lp is not None:
            logprob_values.append(float(lp))

    if not logprob_values:
        return None

    avg_logprob = sum(logprob_values) / len(logprob_values)
    # Geometric mean probability via exp of average log-prob
    confidence = math.exp(avg_logprob)
    return round(min(1.0, max(0.0, confidence)), 4)


def logprobs_to_field_confidences(
    fields: dict[str, Optional[str]],
    logprobs_data: list,
    output_text: str,
) -> Optional[dict[str, float]]:
    """Attempt to map logprobs to per-field confidence scores.

    This is a best-effort mapping: we match the JSON output tokens to their
    field positions and average the logprobs for each field's value tokens.

    Returns None if the mapping fails (caller should fall back to validation).
    """
    if not logprobs_data or not output_text:
        return None

    try:
        import json
        parsed = json.loads(output_text)
    except (ValueError, TypeError):
        return None

    if not isinstance(parsed, dict):
        return None

    # Build a character-position → field mapping from the parsed JSON.
    # For each field, find its value span in output_text and collect
    # the logprobs of tokens that fall within that span.
    field_scores: dict[str, float] = {}

    for field_name, expected_value in parsed.items():
        if field_name not in fields or expected_value is None:
            continue

        # Find the value in the output string
        value_str = str(expected_value)
        value_pos = output_text.find(f'"{value_str}"')
        if value_pos == -1:
            # Try without quotes (numeric values, though we expect strings)
            value_pos = output_text.find(value_str)
        if value_pos == -1:
            continue

        value_end = value_pos + len(value_str)

        # Collect logprobs whose token text falls within this value span.
        # This is approximate — token boundaries don't perfectly align with
        # character positions — but gives a meaningful signal.
        field_logprobs: list[float] = []
        char_pos = 0
        for token_item in logprobs_data:
            token_text = (
                token_item.get("token", "")
                if isinstance(token_item, dict)
                else getattr(token_item, "token", "")
            )
            token_start = char_pos
            token_end = char_pos + len(token_text)

            # Check overlap between token span and value span
            if token_start < value_end and token_end > value_pos:
                lp = (
                    token_item.get("logprob")
                    if isinstance(token_item, dict)
                    else getattr(token_item, "logprob", None)
                )
                if lp is not None:
                    field_logprobs.append(float(lp))

            char_pos = token_end

        if field_logprobs:
            avg_lp = sum(field_logprobs) / len(field_logprobs)
            field_scores[field_name] = round(
                min(1.0, max(0.0, math.exp(avg_lp))), 4
            )

    return field_scores if field_scores else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_field_confidences(
    fields: dict[str, Optional[str]],
    logprobs_data: Optional[list] = None,
    output_text: Optional[str] = None,
) -> tuple[dict[str, float], str]:
    """Compute per-field confidence scores and the method used.

    Returns:
        (field_confidences, confidence_method) — the scores dict and a string
        identifying which calculation method was applied.
    """
    # Try logprobs-based per-field confidence first
    if logprobs_data and output_text:
        logprobs_scores = logprobs_to_field_confidences(
            fields, logprobs_data, output_text
        )
        if logprobs_scores:
            # Blend with validation for fields where logprobs mapping succeeded
            blended: dict[str, float] = {}
            for field_name, value in fields.items():
                if value is None:
                    blended[field_name] = 0.0
                    continue
                logprob_score = logprobs_scores.get(field_name)
                validation_score = _validate_field(field_name, value)
                if logprob_score is not None:
                    # Weighted blend: 60% logprobs + 40% validation
                    blended[field_name] = round(
                        min(1.0, max(0.0, 0.6 * logprob_score + 0.4 * validation_score)),
                        4,
                    )
                else:
                    blended[field_name] = validation_score
            return blended, "logprobs+validation"

    # Fall back to validation-based confidence
    scores: dict[str, float] = {}
    for field_name, value in fields.items():
        if value is None:
            scores[field_name] = 0.0
        else:
            scores[field_name] = _validate_field(field_name, value)
    return scores, "validation"


def compute_overall_confidence(
    field_confidences: dict[str, float],
    logprobs_data: Optional[list] = None,
) -> float:
    """Compute overall confidence from per-field scores and optional logprobs.

    If logprobs are available, they serve as a model-certainty signal that
    modulates the validation-based scores. Otherwise, validation-only.
    """
    if not field_confidences:
        return 0.0

    validation_avg = sum(field_confidences.values()) / len(field_confidences)

    logprobs_confidence = (
        logprobs_to_overall_confidence(logprobs_data) if logprobs_data else None
    )

    if logprobs_confidence is not None:
        # Blend: validation (60%) + logprobs (40%)
        blended = 0.6 * validation_avg + 0.4 * logprobs_confidence
        return round(min(1.0, max(0.0, blended)), 4)

    return round(min(1.0, max(0.0, validation_avg)), 4)
