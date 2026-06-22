"""Model chain container for multi-model extraction fallback.

ModelChain is a thin container holding ordered (model_name, extractor) pairs.
It has no fallback logic and no extract() method — the service layer owns
the fallback loop so it can persist every provider call as its own attempt row.
"""

import os

RETRIABLE_ERRORS = frozenset({
    "api_timeout",
    "api_rate_limit",
    "api_server_error",
    "empty_response",
})

# Retry-within-provider configuration.
# After a retriable error, the service retries the SAME provider up to
# MAX_PROVIDER_RETRIES times with exponential backoff before falling
# through to the next model in the chain.
# Configurable via env vars for operational tuning.
MAX_PROVIDER_RETRIES = int(os.environ.get("EXTRACTION_MAX_PROVIDER_RETRIES", "2"))
RETRY_BACKOFF_BASE_S = float(os.environ.get("EXTRACTION_RETRY_BACKOFF_BASE_S", "1.0"))
RETRY_BACKOFF_MAX_S = float(os.environ.get("EXTRACTION_RETRY_BACKOFF_MAX_S", "8.0"))


def retry_backoff_delay(attempt: int) -> float:
    """Compute exponential backoff delay in seconds for a retry attempt.

    attempt=0 is the first retry (after the initial failure), so delay is
    RETRY_BACKOFF_BASE_S * 2^0 = base.
    Capped at RETRY_BACKOFF_MAX_S.
    """
    delay = RETRY_BACKOFF_BASE_S * (2 ** attempt)
    return min(delay, RETRY_BACKOFF_MAX_S)


class ModelChain:
    """Ordered list of (model_name, extractor) pairs.

    No fallback logic — service layer owns that via _get_model_chain().
    """

    def __init__(self, extractors: list[tuple[str, object]]):
        self._chain = list(extractors)

    @property
    def models(self) -> list[tuple[str, object]]:
        return list(self._chain)

    def __len__(self) -> int:
        return len(self._chain)
