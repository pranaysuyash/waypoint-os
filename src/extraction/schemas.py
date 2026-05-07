"""Per-document-type extraction schemas and JSON Schema builder for OpenAI Structured Outputs."""

from typing import Any

# Field sets per document type — subset of VALID_EXTRACTION_FIELDS in extraction_service.py
DOCUMENT_SCHEMAS: dict[str, dict[str, Any]] = {
    "passport": {
        "fields": ["full_name", "date_of_birth", "passport_number", "passport_expiry", "nationality"],
        "prompt": (
            "Extract the following fields from this passport image. "
            "Return each field as a string or null if not found. "
            "Fields: full_name, date_of_birth, passport_number, passport_expiry, nationality."
        ),
    },
    "visa": {
        "fields": ["full_name", "nationality", "visa_type", "visa_number", "visa_expiry", "passport_number"],
        "prompt": (
            "Extract the following fields from this visa image. "
            "Return each field as a string or null if not found. "
            "Fields: full_name, nationality, visa_type, visa_number, visa_expiry, passport_number."
        ),
    },
    "insurance": {
        "fields": ["full_name", "insurance_provider", "insurance_policy_number"],
        "prompt": (
            "Extract the following fields from this insurance document image. "
            "Return each field as a string or null if not found. "
            "Fields: full_name, insurance_provider, insurance_policy_number."
        ),
    },
    "default": {
        "fields": ["full_name"],
        "prompt": (
            "Extract the full_name from this document image. "
            "Return as a string or null if not found."
        ),
    },
}


def get_schema(document_type: str) -> dict[str, Any]:
    """Get extraction schema for a document type."""
    return DOCUMENT_SCHEMAS.get(document_type, DOCUMENT_SCHEMAS["default"])


def build_json_schema(fields: list[str]) -> dict[str, Any]:
    """Build a JSON Schema for OpenAI Structured Outputs.

    Returns a schema where each field is string | null, with no additional
    properties allowed (strict mode).
    """
    properties: dict[str, Any] = {}
    for field in fields:
        properties[field] = {
            "type": ["string", "null"],
            "description": f"Extracted {field.replace('_', ' ')}",
        }

    return {
        "type": "object",
        "properties": properties,
        "required": fields,
        "additionalProperties": False,
    }
