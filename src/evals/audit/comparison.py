"""Shared comparison utilities for eval modules.

Provides normalised string comparison functions used by both the extraction
accuracy rule and the pipeline eval rule.  Centralises ``_normalise`` and
``values_match`` to prevent drift between modules.
"""

from __future__ import annotations

from typing import Any, Literal


def normalise(value: Any) -> str | None:
    """Lower-case, collapse whitespace, strip — the canonical comparison form.

    Accepts any value.  Non-string values are converted to ``str()`` before
    normalisation.  ``None`` passes through as ``None``.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value).strip()
    collapsed = " ".join(value.lower().split())
    return collapsed.strip()


def values_match(
    expected: Any,
    actual: Any,
    *,
    mode: Literal["exact", "contains"] = "exact",
) -> bool:
    """Compare two values under the chosen matching mode.

    Modes
    -----
    exact
        Normalised strings must be identical.
    contains
        The normalised actual value must *contain* the normalised expected
        value.  Useful when the extractor appends extra context (e.g.
        ``"BRITISH CITIZEN"`` extracted as ``"BRITISH CITIZEN (UNITED KINGDOM)``).
    """
    exp_n = normalise(expected)
    act_n = normalise(actual)

    # Both absent — true negative
    if exp_n is None and act_n is None:
        return True
    # One absent, other present — mismatch
    if exp_n is None or act_n is None:
        return False

    if mode == "exact":
        return exp_n == act_n
    if mode == "contains":
        return exp_n in act_n or act_n in exp_n
    return exp_n == act_n
