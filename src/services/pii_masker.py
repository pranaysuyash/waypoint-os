"""
src/services/pii_masker.py — PII Sanitization & Data Masking Engine.

Grounding doctrine:
- PER-0933 & PER-0927: Clean boundary sanitization stripping sensitive personal data across trust zones.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union


class PIIMasker:
    """Masks sensitive identity and financial information before export across public trust zones."""

    @staticmethod
    def mask_passport_number(passport_num: str) -> str:
        """Mask passport number showing only first 2 and last 2 characters (e.g. L8****C3)."""
        clean = passport_num.strip()
        if len(clean) <= 4:
            return "****"
        return f"{clean[:2]}{'*' * (len(clean) - 4)}{clean[-2:]}"

    @staticmethod
    def mask_email(email_str: str) -> str:
        """Mask email address (e.g. j***n@domain.com)."""
        clean = email_str.strip()
        if "@" not in clean:
            return "***"
        user, domain = clean.split("@", 1)
        if len(user) <= 2:
            masked_user = f"{user[0]}*"
        else:
            masked_user = f"{user[0]}{'*' * (len(user) - 2)}{user[-1]}"
        return f"{masked_user}@{domain}"

    @staticmethod
    def mask_phone_number(phone_str: str) -> str:
        """Mask phone number showing only last 4 digits."""
        digits = re.sub(r"\D", "", phone_str)
        if len(digits) <= 4:
            return "****"
        return f"+{'*' * (len(digits) - 4)}{digits[-4:]}"

    @classmethod
    def sanitize_trip_payload(cls, data: Union[Dict[str, Any], List[Any], Any]) -> Any:
        """Recursively scrub sensitive keys from dictionaries and lists."""
        if isinstance(data, dict):
            sanitized: Dict[str, Any] = {}
            for k, v in data.items():
                k_lower = k.lower()
                if "passport" in k_lower and isinstance(v, str):
                    sanitized[k] = cls.mask_passport_number(v)
                elif "email" in k_lower and isinstance(v, str):
                    sanitized[k] = cls.mask_email(v)
                elif ("phone" in k_lower or "mobile" in k_lower) and isinstance(v, str):
                    sanitized[k] = cls.mask_phone_number(v)
                elif any(secret in k_lower for secret in ["card_number", "cvv", "api_key", "secret"]):
                    sanitized[k] = "[REDACTED_SECRET]"
                else:
                    sanitized[k] = cls.sanitize_trip_payload(v)
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize_trip_payload(item) for item in data]
        return data
