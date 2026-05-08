"""Extraction-related exceptions."""


class ExtractionValidationError(ValueError):
    """Invalid input — should map to HTTP 422 in the endpoint.

    Raised for prevalidation failures (unsupported MIME, PDF over page limit, etc.)
    before any DB mutation or provider call.
    """
