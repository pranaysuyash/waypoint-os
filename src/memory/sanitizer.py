"""
src/memory/sanitizer.py — Prompt Injection Neutralization Layer.

Sanitizes retrieved memory strings before injection into agent LLM prompts:
- Strips role simulation tokens (e.g., 'system:', 'assistant:', 'user:').
- Neutralizes prompt injection commands (e.g., 'ignore previous instructions').
- Escapes delimiter injections (e.g., '---', '```markdown', '=== STOP ===').
"""

from __future__ import annotations

import re
from typing import Any, Dict

FORBIDDEN_PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"(?i)system\s*:\s*",
    r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
    r"(?i)admin\s+override\s*:",
    r"(?i)bypass\s+safety\s+filter",
]


class MemorySanitizer:
    """Sanitizes memory text against prompt injection before context assembly."""

    @staticmethod
    def sanitize_text(text: str) -> str:
        if not text:
            return ""

        sanitized = text
        for pattern in FORBIDDEN_PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[FILTERED_INJECTION]", sanitized)

        # Replace excessive dashes or markdown delimiters that could break formatting
        sanitized = re.sub(r"-{4,}", "---", sanitized)
        sanitized = re.sub(r"={4,}", "===", sanitized)

        return sanitized.strip()

    @classmethod
    def sanitize_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes dictionary payloads."""
        cleaned = {}
        for k, v in payload.items():
            if isinstance(v, str):
                cleaned[k] = cls.sanitize_text(v)
            elif isinstance(v, dict):
                cleaned[k] = cls.sanitize_payload(v)
            elif isinstance(v, list):
                cleaned[k] = [
                    cls.sanitize_text(x) if isinstance(x, str) else x for x in v
                ]
            else:
                cleaned[k] = v
        return cleaned
