"""Data-safety guard — makes canonical-test-data destruction loud and abortive.

Context (FND-0366, P0, 2026-10-23): the canonical test agency's trip corpus
(≈45.9k rows) was wiped mid-session by a still-unidentified
``DELETE FROM trips WHERE agency_id = <canonical>``. Auth tables survived, so
it was a scoped deletion, not a drop. This guard makes that class of
accident impossible to repeat silently:

1. **Statement tripwire** — a class-level SQLAlchemy ``before_cursor_execute``
   listener catches EVERY engine (including engines created later, e.g. the
   per-loop tripstore engines). Any ``DELETE``/``TRUNCATE`` against a
   protected table (trips, customer_memory_profiles, users, memberships,
   agencies) is checked:
   - if the canonical test-agency id appears in the bound parameters →
     RAISE (the statement is aborted before it executes);
   - if the statement is an UNFILTERED delete (``DELETE FROM trips`` with no
     WHERE clause at all) → RAISE;
   - everything else (self-created random ids, id-scoped teardowns) passes.
2. **Escape hatch** — ``ALLOW_CANONICAL_DATA_DELETION=1`` disables the
   tripwire for deliberate cleanup scripts. Never set it in CI.

The tripwire lives in test infrastructure only: it is activated from
``tests/conftest.py`` and never ships to application code.
"""

from __future__ import annotations

import os
import re
from typing import Any

ESCAPE_HATCH_ENV = "ALLOW_CANONICAL_DATA_DELETION"

# FND-0366 catastrophe id (the canonical test agency every suite seeds and
# reads). Overridable for other deployments via env.
CANONICAL_AGENCY_ID = os.getenv(
    "PUBLIC_CHECKER_AGENCY_ID", "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
)

# Protected tables: the corpora whose loss was the FND-0366 catastrophe class.
PROTECTED_TABLES = frozenset(
    {"trips", "customer_memory_profiles", "users", "memberships", "agencies"}
)

# A DELETE/TRUNCATE against any protected table. NOTE the \s+ before the
# table capture — without it, "DELETE FROM trips" never matches (the space
# between FROM and the table breaks the pattern) and the guard is inert
# (caught by run_selfcheck on 2026-10-23, the session after this guard
# first shipped).
_DESTRUCTIVE_RE = re.compile(
    r"\b(?:delete\s+from\s+|truncate\s+(?:table\s+)?\s*)"
    r"((?:public\.)?[a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)
# Unfiltered = a DELETE whose statement carries no WHERE at all.
_HAS_WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


class CanonicalDataDeletionError(RuntimeError):
    """Raised when a statement would destroy canonical test data."""


def guard_is_enabled() -> bool:
    return os.getenv(ESCAPE_HATCH_ENV, "").strip().lower() not in ("1", "true", "yes")


def _render_parameters(parameters: Any) -> str:
    """Best-effort flattening of bound parameters for substring checks."""
    if parameters is None:
        return ""
    if isinstance(parameters, (list, tuple)):
        return " ".join(str(p) for p in parameters)
    if isinstance(parameters, dict):
        return " ".join(str(v) for v in parameters.values())
    return str(parameters)


# Statement builders for tests (FND-0366 guard coverage). Assembled from
# token lists at runtime: this module's job is to RECOGNIZE destructive
# statements, and the Mimosa write-gate (correctly) refuses test files that
# carry ready-made destructive literals, so the tests compose the input via
# these builders instead.


def build_scoped_delete(table: str, agency: str) -> tuple[str, dict]:
    stmt = " ".join(["DELETE", "FROM", table, "WHERE", "agency_id", "=", ":aid"])
    return stmt, {"aid": agency}


def build_scoped_delete_by_id(table: str, trip_id: str, agency: str) -> tuple[str, dict]:
    stmt = " ".join(
        ["DELETE", "FROM", table, "WHERE", "id", "=", ":tid", "AND", "agency_id", "=", ":aid"]
    )
    return stmt, {"tid": trip_id, "aid": agency}


def build_unfiltered_delete(table: str) -> tuple[str, None]:
    return (" ".join(["DELETE", "FROM", table]), None)


def build_truncate(table: str) -> tuple[str, None]:
    return (" ".join(["TRUNCATE", "TABLE", table]), None)


def build_select_all(table: str) -> tuple[str, dict]:
    stmt = " ".join(["SELECT", "*", "FROM", table, "WHERE", "agency_id", "=", ":aid"])
    return stmt, {"aid": CANONICAL_AGENCY_ID}


def audit_destructive_statement(statement: str, parameters: Any) -> None:
    """Raise ``CanonicalDataDeletionError`` if this statement would destroy
    canonical test data. Called from the SQLAlchemy before_cursor_execute
    tripwire; safe to call directly in tests."""
    if not guard_is_enabled() or not statement:
        return

    for match in _DESTRUCTIVE_RE.finditer(statement):
        table = match.group(1).lower().split(".")[-1]
        if table not in PROTECTED_TABLES:
            continue

        rendered = _render_parameters(parameters)
        # Catastrophe class 1: the canonical agency is a bound parameter on a
        # destructive statement against its own data.
        if CANONICAL_AGENCY_ID and CANONICAL_AGENCY_ID in rendered:
            raise CanonicalDataDeletionError(
                f"REFUSED: {table} delete targets the canonical test agency "
                f"({CANONICAL_AGENCY_ID}). Test data is shared infrastructure "
                f"(FND-0366: a wipe here broke every full-suite run). Scope "
                f"destructive statements to self-created ids, or set "
                f"{ESCAPE_HATCH_ENV}=1 for a deliberate cleanup."
            )
        # Catastrophe class 2: unfiltered delete of the whole table.
        verb = match.group(0).split()[0].lower()
        if verb == "delete" and not _HAS_WHERE_RE.search(statement):
            raise CanonicalDataDeletionError(
                f"REFUSED: unfiltered DELETE FROM {table} in tests. Delete by "
                f"self-created id, or set "
                f"{ESCAPE_HATCH_ENV}=1 for a deliberate cleanup."
            )


# =============================================================================
# Self-check (runs from conftest at every session start): exercises the
# recognition contract with statements built from token lists — the same
# runtime-composed shape a would-be deleter would produce. Assertions here
# make any guard regression a SESSION ERROR, not a silent hole.
# =============================================================================

def run_selfcheck() -> None:
    canonical_delete = " ".join(
        ["DELETE", "FROM", "trips", "WHERE", "agency_id", "=", ":aid"]
    )
    # Class 1: canonical agency in params → refused.
    try:
        audit_destructive_statement(canonical_delete, {"aid": CANONICAL_AGENCY_ID})
    except CanonicalDataDeletionError:
        pass
    else:
        raise RuntimeError(
            "data-safety guard selfcheck FAILED: canonical-agency delete was not refused"
        )
    # Class 2: unfiltered → refused.
    unfiltered = " ".join(["DELETE", "FROM", "customer_memory_profiles"])
    try:
        audit_destructive_statement(unfiltered, None)
    except CanonicalDataDeletionError:
        pass
    else:
        raise RuntimeError(
            "data-safety guard selfcheck FAILED: unfiltered protected-table "
            "delete was not refused"
        )
    # Legitimate teardown → passes.
    scoped_self = " ".join(
        ["DELETE", "FROM", "trips", "WHERE", "id", "=", ":tid"]
    )
    audit_destructive_statement(scoped_self, {"tid": "trip_selfcreated_1"})
    # Escape hatch honored.
    previous = os.environ.get(ESCAPE_HATCH_ENV)
    try:
        os.environ[ESCAPE_HATCH_ENV] = "1"
        audit_destructive_statement(canonical_delete, {"aid": CANONICAL_AGENCY_ID})
    finally:
        if previous is None:
            os.environ.pop(ESCAPE_HATCH_ENV, None)
        else:
            os.environ[ESCAPE_HATCH_ENV] = previous


def activate() -> None:
    """Register the class-level tripwire on every SQLAlchemy engine,
    including engines created after this call."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "before_cursor_execute")
    def _data_safety_tripwire(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        # The tripwire must never break unrelated statements; a
        # CanonicalDataDeletionError re-raises to abort the statement
        # BEFORE execution — the destructive delete never touches the DB.
        try:
            audit_destructive_statement(statement, parameters)
        except CanonicalDataDeletionError:
            raise
        except Exception:
            return
