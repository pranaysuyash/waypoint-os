"""
Logging filter that scrubs sensitive values from log messages.

Prevents accidental leakage of cookies, authorization headers,
and tokens into log output. Installed once at startup; applies
to all loggers that inherit from the root logger.
"""

import logging
import re

SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(access_token\s*=\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(refresh_token\s*=\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(cookie\s*:\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(authorization\s*:\s*(?:bearer\s+)?)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(set-cookie\s*:\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(access_token=)[^;\s]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(refresh_token=)[^;\s]+", re.IGNORECASE), r"\1[REDACTED]"),
]


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args and isinstance(record.args, tuple):
            record.args = tuple(
                pattern.sub(replacement, arg)
                if isinstance(arg, str)
                else arg
                for arg in record.args
                for pattern, replacement in SENSITIVE_PATTERNS
            )
        elif record.args and isinstance(record.args, dict):
            record.args = {
                k: (
                    pattern.sub(replacement, v)
                    if isinstance(v, str)
                    else v
                )
                for k, v in record.args.items()
                for pattern, replacement in SENSITIVE_PATTERNS
            }
        return True


def install_sensitive_data_filter() -> None:
    root = logging.getLogger()
    if not any(isinstance(f, SensitiveDataFilter) for f in root.filters):
        root.addFilter(SensitiveDataFilter())
