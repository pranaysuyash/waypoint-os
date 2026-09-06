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


_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def auth_bypass_enabled() -> bool:
    """Return whether the local-only authentication bypass is explicitly enabled.

    Environment variables are strings, so checking their presence is unsafe:
    ``SPINE_API_DISABLE_AUTH=0`` must keep authentication enabled. Unknown
    values fail closed and are treated as disabled.
    """
    return os.environ.get("SPINE_API_DISABLE_AUTH", "").strip().lower() in _TRUE_VALUES


class StartupAssertionError(RuntimeError):
    """Raised when a startup assertion fails. Process should crash."""
    pass


def _check_database_url() -> Tuple[bool, str]:
    """DATABASE_URL must be set and non-empty."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return False, "DATABASE_URL is not set. Cannot start without a database connection."
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    if "sqlite" in url.lower() and env in {"production", "staging"}:
        return False, "DATABASE_URL points to SQLite in a production-like environment. Use PostgreSQL."
    if env in {"production", "staging"} and any(
        marker in url.lower()
        for marker in ("postgres:postgres@", "waypoint_dev_password@", "waypoint_password@")
    ):
        return False, "DATABASE_URL contains a known development credential in a production-like environment."
    return True, "DATABASE_URL is set."


def _check_auth_not_disabled_in_production() -> Tuple[bool, str]:
    """SPINE_API_DISABLE_AUTH must not be set outside development/test.

    A-18: staging previously slipped through (only 'production' was checked),
    so a staging deployment could boot with authentication disabled. The
    kill switch is allowed only in development (local) and test environments.
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    auth_disabled = auth_bypass_enabled()
    if env in ("production", "staging") and auth_disabled:
        return False, (
            f"SPINE_API_DISABLE_AUTH is set in ENVIRONMENT='{env}'. "
            "This is a critical security violation. Remove it or set "
            "ENVIRONMENT to 'development'/'test'."
        )
    return True, f"Auth kill switch is not set (ENVIRONMENT='{env}')."


def _check_secret_key() -> Tuple[bool, str]:
    """JWT_SECRET or SECRET_KEY must be set and not a well-known default."""
    key = os.environ.get("JWT_SECRET") or os.environ.get("SECRET_KEY", "")
    known_defaults = {
        "secret", "changeme", "password", "default", "test", "dev",
        "change-me-to-a-random-secret", "waypoint_dev_secret",
    }
    if not key:
        return False, "JWT_SECRET (or SECRET_KEY) is not set. JWT signing requires a real secret."
    if key.lower().strip() in known_defaults:
        return False, f"JWT_SECRET is a known default ('{key}'). Use a real secret."
    if len(key) < 32:
        return False, f"JWT_SECRET is only {len(key)} characters. Use at least 32 characters."
    return True, "JWT_SECRET is set and satisfies security requirements."


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
    """TRIPSTORE_BACKEND must be explicitly set to sql/postgres in production."""
    env = os.environ.get("ENVIRONMENT", "development")
    backend = os.environ.get("TRIPSTORE_BACKEND", "").strip().lower()
    if env == "production" and not backend:
        return False, (
            "TRIPSTORE_BACKEND is not set in production. "
            "Set to 'sql' or 'postgres' to prevent silent fallback to file-based storage."
        )
    if env == "production" and backend not in ("sql", "postgres", "postgresql"):
        return False, (
            f"TRIPSTORE_BACKEND='{backend}' in production. "
            "Production must use 'sql' or 'postgres'."
        )
    return True, f"TRIPSTORE_BACKEND is '{backend or 'not set (ok for dev)'}'"


def _check_redis_url() -> Tuple[bool, str]:
    """Production-like multi-worker deployments must declare shared Redis.

    Redis backs rate limiting and usage accounting. Allowing an implicit
    in-process fallback with multiple workers makes security and spend limits
    process-local, so staging/production refuse that topology.
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    url = os.environ.get("REDIS_URL", "").strip()
    if env in {"production", "staging"} and not url:
        return False, (
            "REDIS_URL is not set in a production-like environment. "
            "Shared Redis is required for rate limits and usage accounting."
        )
    if url and not url.startswith(("redis://", "rediss://")):
        return False, "REDIS_URL must use redis:// or rediss://."
    return True, "REDIS_URL is configured." if url else "REDIS_URL is not set (development/test fallback allowed)."


def _check_idempotency_backend() -> Tuple[bool, str]:
    """Intake idempotency must use a cross-process backend in production-like envs.

    PT-08 (refined by E-3): the in-memory `IdempotencyRegistry` is
    single-process — with multiple workers, cross-worker dedup silently
    disappears (duplicate trips / duplicate LLM spend), and with any worker
    count a restart loses all records, so a client retry after a crash
    re-executes a completed intake. Production-like deployments must pin
    SPINE_API_IDEMPOTENCY_BACKEND=sql (the deploy surfaces already do; this
    assertion makes an unset/overridden env fail loudly instead).
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    backend = os.environ.get("SPINE_API_IDEMPOTENCY_BACKEND", "").strip().lower()
    if env in {"production", "staging"} and backend not in {"sql", "postgres", "postgresql"}:
        return False, (
            f"SPINE_API_IDEMPOTENCY_BACKEND='{backend or 'not set'}' in a "
            "production-like environment. Intake idempotency (F-28) requires a "
            "cross-process backend — set it to 'sql' or duplicate trips and "
            "duplicate LLM spend become possible across workers/restarts."
        )
    return True, (
        f"Idempotency backend is '{backend}'."
        if backend
        else "Idempotency backend not set (development/test single-process fallback allowed)."
    )


def _check_public_checker_agency() -> Tuple[bool, str]:
    """PUBLIC_CHECKER_AGENCY_ID should be set if public checker is used."""
    agency_id = os.environ.get("PUBLIC_CHECKER_AGENCY_ID", "")
    if not agency_id:
        # Non-fatal warning, not a crash
        return True, "PUBLIC_CHECKER_AGENCY_ID is not set. Public checker will use default."
    return True, f"PUBLIC_CHECKER_AGENCY_ID is set to '{agency_id[:8]}...'"


def _check_proposal_signing_key() -> Tuple[bool, str]:
    """PROPOSAL_SIGNING_KEY must be set and not a known default/placeholder.

    PT-01 / LR-B02: the proposal capability-token system signs booking-granting
    tokens with this key. The import-time check in public_proposals.py only
    proves *some* value is present — a clone-copy-deploy with the committed
    placeholder would still pass it. Known defaults are blocked here.
    """
    key = os.environ.get("PROPOSAL_SIGNING_KEY", "")
    known_defaults = {
        "waypoint_secret_proposal_key_2026",        # removed hardcoded fallback
        "change-me-to-a-random-secret",             # .env.example placeholder
    }
    if not key:
        return False, (
            "PROPOSAL_SIGNING_KEY is not set. Proposal capability tokens "
            "require a real signing secret."
        )
    if key.lower().strip() in known_defaults:
        return False, (
            f"PROPOSAL_SIGNING_KEY is a known default/placeholder ('{key}'). "
            "Use a real secret."
        )
    if len(key) < 32:
        return False, (
            f"PROPOSAL_SIGNING_KEY is only {len(key)} characters. "
            "Use at least 32 characters."
        )
    return True, "PROPOSAL_SIGNING_KEY is set and satisfies security requirements."


def _check_public_proposal_demo_mode() -> Tuple[bool, str]:
    """The fabricated proposal fixture seam is forbidden in production-like envs.

    ``PUBLIC_PROPOSAL_DEMO_MODE`` is intentionally available for local demos
    and tests, but enabling it in staging or production would reintroduce
    synthetic proposal content at a public trust boundary. Unknown/false
    values remain disabled by the route's explicit truthy parser.
    """
    env = os.environ.get("ENVIRONMENT", "development").strip().lower()
    raw = os.environ.get("PUBLIC_PROPOSAL_DEMO_MODE", "").strip().lower()
    enabled = raw in _TRUE_VALUES
    if env in {"production", "staging"} and enabled:
        return False, (
            "PUBLIC_PROPOSAL_DEMO_MODE is enabled in a production-like "
            f"environment ('{env}'). Disable the fabricated proposal fixture "
            "seam before exposing public proposal routes."
        )
    return True, (
        "Public proposal demo mode is disabled."
        if not enabled
        else f"Public proposal demo mode is enabled only for {env}."
    )


# ─────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────

# Assertions ordered by criticality
_ASSERTIONS = [
    ("ENVIRONMENT", _check_environment_declared),
    ("DATABASE_URL", _check_database_url),
    ("SECRET_KEY", _check_secret_key),
    ("PROPOSAL_SIGNING_KEY", _check_proposal_signing_key),
    ("PUBLIC_PROPOSAL_DEMO_MODE", _check_public_proposal_demo_mode),
    ("AUTH_SAFETY", _check_auth_not_disabled_in_production),
    ("TRIPSTORE_BACKEND", _check_tripstore_backend),
    ("IDEMPOTENCY_BACKEND", _check_idempotency_backend),
    ("REDIS_URL", _check_redis_url),
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
