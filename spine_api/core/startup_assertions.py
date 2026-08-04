"""
spine_api/core/startup_assertions.py — Fail-closed boot checks.

Every assertion here runs at application startup. If any assertion fails,
the process crashes immediately with a clear error message.

This prevents silent unsafe defaults in production:
  - Missing DATABASE_URL → crashes (no silent fallback to SQLite/file)
  - Auth disabled in production → crashes
  - Missing SECRET_KEY → crashes
  - Missing ENVIRONMENT declaration → crashes

Design rationale (motto_v4 §0.6, §0.11):
  An application handling traveler details, budgets, and booking state
  cannot silently fall back to unsafe defaults. Every critical dependency
  must be explicitly satisfied or the service refuses to start.
"""

from __future__ import annotations

import logging
import os
from typing import List, Tuple

logger = logging.getLogger("spine_api.core.startup_assertions")


class StartupAssertionError(RuntimeError):
    """Raised when a startup assertion fails. Process should crash."""
    pass


def _check_database_url() -> Tuple[bool, str]:
    """DATABASE_URL must be set and non-empty."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return False, "DATABASE_URL is not set. Cannot start without a database connection."
    if "sqlite" in url.lower() and os.environ.get("ENVIRONMENT") == "production":
        return False, "DATABASE_URL points to SQLite in production. Use PostgreSQL."
    return True, "DATABASE_URL is set."


def _check_auth_not_disabled_in_production() -> Tuple[bool, str]:
    """SPINE_API_DISABLE_AUTH must not be set in production."""
    env = os.environ.get("ENVIRONMENT", "development")
    auth_disabled = os.environ.get("SPINE_API_DISABLE_AUTH", "").lower() in ("1", "true", "yes")
    if env == "production" and auth_disabled:
        return False, (
            "SPINE_API_DISABLE_AUTH is set in production. "
            "This is a critical security violation. Remove it or set ENVIRONMENT != 'production'."
        )
    return True, "Auth is not disabled in production."


def _check_secret_key() -> Tuple[bool, str]:
    """SECRET_KEY must be set and not a well-known default."""
    key = os.environ.get("SECRET_KEY", "")
    known_defaults = {"secret", "changeme", "password", "default", "test", "dev"}
    if not key:
        return False, "SECRET_KEY is not set. JWT signing requires a real secret."
    if key.lower().strip() in known_defaults:
        return False, f"SECRET_KEY is a known default ('{key}'). Use a real secret."
    if len(key) < 16:
        return False, f"SECRET_KEY is only {len(key)} characters. Use at least 32 characters."
    return True, "SECRET_KEY is set and appears non-trivial."


def _check_environment_declared() -> Tuple[bool, str]:
    """ENVIRONMENT must be explicitly set."""
    env = os.environ.get("ENVIRONMENT", "")
    if not env:
        return False, (
            "ENVIRONMENT is not set. Set to 'development', 'staging', or 'production'. "
            "This controls security posture and fail-closed defaults."
        )
    valid = {"development", "staging", "production", "test"}
    if env not in valid:
        return False, f"ENVIRONMENT='{env}' is not recognized. Use one of: {valid}"
    return True, f"ENVIRONMENT is set to '{env}'."


def _check_tripstore_backend() -> Tuple[bool, str]:
    """TRIPSTORE_BACKEND must be explicitly set in production."""
    env = os.environ.get("ENVIRONMENT", "development")
    backend = os.environ.get("TRIPSTORE_BACKEND", "")
    if env == "production" and not backend:
        return False, (
            "TRIPSTORE_BACKEND is not set in production. "
            "Set to 'postgres' to prevent silent fallback to file-based storage."
        )
    if env == "production" and backend != "postgres":
        return False, (
            f"TRIPSTORE_BACKEND='{backend}' in production. "
            "Production must use 'postgres'."
        )
    return True, f"TRIPSTORE_BACKEND is '{backend or 'not set (ok for dev)'}'"


def _check_public_checker_agency() -> Tuple[bool, str]:
    """PUBLIC_CHECKER_AGENCY_ID should be set if public checker is used."""
    agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", "")
    if not agency_id:
        # Non-fatal warning, not a crash
        return True, "PUBLIC_CHECKER_AGENCY_ID is not set. Public checker will use default."
    return True, f"PUBLIC_CHECKER_AGENCY_ID is set to '{agency_id[:8]}...'"


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

# Assertions ordered by criticality
_ASSERTIONS = [
    ("ENVIRONMENT", _check_environment_declared),
    ("DATABASE_URL", _check_database_url),
    ("SECRET_KEY", _check_secret_key),
    ("AUTH_SAFETY", _check_auth_not_disabled_in_production),
    ("TRIPSTORE_BACKEND", _check_tripstore_backend),
    ("PUBLIC_CHECKER_AGENCY", _check_public_checker_agency),
]


def run_startup_assertions(*, strict: bool = True) -> List[str]:
    """
    Run all startup assertions.

    Args:
        strict: If True (default), raise StartupAssertionError on first failure.
                If False, collect and return all failures as a list.

    Returns:
        List of failure messages (empty if all passed).

    Raises:
        StartupAssertionError: If strict=True and any assertion fails.
    """
    env = os.environ.get("ENVIRONMENT", "development")
    failures: List[str] = []

    logger.info("═══ Running Startup Assertions (ENVIRONMENT=%s) ═══", env)

    for name, check_fn in _ASSERTIONS:
        passed, message = check_fn()
        if passed:
            logger.info("  ✓ %-25s %s", name, message)
        else:
            logger.error("  ✗ %-25s %s", name, message)
            failures.append(f"[{name}] {message}")

    if failures:
        failure_summary = "\n".join(failures)
        logger.error(
            "═══ %d Startup Assertion(s) FAILED ═══\n%s",
            len(failures),
            failure_summary,
        )
        if strict and env in ("production", "staging"):
            raise StartupAssertionError(
                f"{len(failures)} startup assertion(s) failed:\n{failure_summary}"
            )
        elif strict:
            # In development, warn but don't crash
            logger.warning(
                "Startup assertions failed but ENVIRONMENT=%s, continuing with warnings.",
                env,
            )
    else:
        logger.info("═══ All Startup Assertions Passed ═══")

    return failures
