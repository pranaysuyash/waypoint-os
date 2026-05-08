"""Model chain container for multi-model extraction fallback.

ModelChain is a thin container holding ordered (model_name, extractor) pairs.
It has no fallback logic and no extract() method — the service layer owns
the fallback loop so it can persist every provider call as its own attempt row.
"""

RETRIABLE_ERRORS = frozenset({
    "api_timeout",
    "api_rate_limit",
    "api_server_error",
    "empty_response",
})


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
