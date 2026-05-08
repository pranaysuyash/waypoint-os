"""PDF utilities for extraction prevalidation.

Page-count check runs before any DB mutation or provider call. A PDF that
exceeds EXTRACTION_MAX_PDF_PAGES raises ExtractionValidationError with no
extraction row, no attempt row, and no audit event created.
"""

import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_pdf_page_count(file_data: bytes) -> Optional[int]:
    """Lightweight PDF page-count using pypdf. Returns None if cannot determine."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_data))
        return len(reader.pages)
    except Exception:
        logger.debug("Could not read PDF page count", exc_info=True)
        return None


def validate_pdf_pages(file_data: bytes, mime_type: str) -> Optional[int]:
    """Validate PDF page count against configured limit.

    Returns the page count if readable, None if not a PDF or unreadable.
    Raises ExtractionValidationError if PDF exceeds page limit.
    """
    if mime_type != "application/pdf":
        return None

    max_pages = int(os.environ.get("EXTRACTION_MAX_PDF_PAGES", "10"))
    page_count = get_pdf_page_count(file_data)

    if page_count is not None and page_count > max_pages:
        from src.extraction.exceptions import ExtractionValidationError
        raise ExtractionValidationError(
            f"PDF has {page_count} pages, max allowed is {max_pages}"
        )

    return page_count
