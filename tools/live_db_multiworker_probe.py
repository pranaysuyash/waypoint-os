#!/usr/bin/env python3
"""CLI wrapper for the live-PostgreSQL multi-worker contention probe (PER-0700 wave 2).

Runs ``tests/test_pa_wave2_live_probe.py`` against a live PostgreSQL so the
repo's cross-process concurrency primitives are exercised at Tier 3: real OS
processes contending on the same durable rows, asserting exactly-one-winner
semantics.

This tool is a thin orchestrator only. The single source of truth for the
probe logic is the pytest module; this file intentionally contains no SQL and
no business logic. It performs preflight checks, forwards knobs to pytest,
propagates pytest's exit code, and maps results back to human-readable
guarantees.

Safety (inherited from the test module, additive-only by design):
- Probe rows anchor to the seeded canonical agency; each run creates one
  fresh namespaced probe trip and one fresh collection token via the
  canonical TripStore / collection service — nothing pre-existing is mutated
  or deleted.
- All probe tests auto-skip without DATABASE_URL, so PG-less runs stay green;
  this wrapper fails fast with exit 2 instead so the missing prerequisite is
  explicit.

Usage:
    .venv/bin/python tools/live_db_multiworker_probe.py
    .venv/bin/python tools/live_db_multiworker_probe.py --workers 8
    .venv/bin/python tools/live_db_multiworker_probe.py --check idempotency
    .venv/bin/python tools/live_db_multiworker_probe.py --check lease,token --verbose
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = "tests/test_pa_wave2_live_probe.py"
DEFAULT_WORKERS = 4
DB_TIMEOUT_SECONDS = 3
PG_SCHEMES = {"postgres", "postgresql", "postgresql+asyncpg", "postgresql+psycopg"}

# --check name -> what the corresponding probe test proves (one line each).
CHECK_PROOFS: dict[str, str] = {
    "idempotency": (
        "test_probe_idempotency_registry_single_winner_across_processes — "
        "SQL idempotency registry (CAS try_acquire) grants the action to "
        "exactly 1 of N cross-process contenders"
    ),
    "lease": (
        "test_probe_work_lease_single_winner_across_processes — "
        "SQLWorkCoordinator work lease is acquired by exactly 1 process; "
        "the other N-1 are rejected"
    ),
    "token": (
        "test_probe_collection_token_single_consumer_across_processes — "
        "collection tokens are single-use: 1 consumer redeems, the rest are "
        "rejected"
    ),
    "usage_events": (
        "test_probe_usage_events_correlation_columns_present — usage_events "
        "store exposes run correlation columns (run_id) without schema errors"
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the live-PostgreSQL multi-worker contention probe.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help=(
            "contending OS processes per check "
            f"(default: PROBE_WORKERS env or {DEFAULT_WORKERS})"
        ),
    )
    parser.add_argument(
        "--check",
        default=None,
        metavar="NAME[,NAME...]",
        help=(
            "run a subset of checks via pytest -k "
            f"(valid: {', '.join(CHECK_PROOFS)})"
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="extra pytest verbosity (-vv, long tracebacks, full summary)",
    )
    return parser


def _load_env() -> str | None:
    """Load .env into os.environ (explicit env vars win); report DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("  [warn] python-dotenv unavailable; relying on ambient env vars")
        return database_url

    env_path = REPO_ROOT / ".env"
    loaded = load_dotenv(env_path, override=False)
    if database_url:
        print("  DATABASE_URL: found (source: environment)")
    elif loaded and os.environ.get("DATABASE_URL"):
        print(f"  DATABASE_URL: found (source: {env_path})")
    else:
        print(f"  DATABASE_URL: MISSING (checked environment and {env_path})")
    return os.environ.get("DATABASE_URL")


def _db_endpoint(database_url: str) -> str:
    """Human-safe host:port/database summary (credentials redacted)."""
    parsed = urllib.parse.urlsplit(database_url)
    host = parsed.hostname or "<unparsed>"
    port = parsed.port or 5432
    db = (parsed.path or "").lstrip("/") or "<db>"
    return f"{host}:{port}/{db}"


def _tcp_reachable(database_url: str) -> None:
    """Cheap best-effort TCP dial of the Postgres host; warns, never blocks.

    False negatives are possible (unix sockets, IPv6 quirks), so a failure
    only prints a warning — pytest reports the authoritative connection error.
    """
    parsed = urllib.parse.urlsplit(database_url)
    if parsed.scheme not in PG_SCHEMES or not parsed.hostname:
        print("  [warn] DATABASE_URL scheme/host not TCP-checkable; skipping dial")
        return
    try:
        with socket.create_connection(
            (parsed.hostname, parsed.port or 5432), timeout=DB_TIMEOUT_SECONDS
        ):
            print(f"  Preflight:     Postgres reachable at {parsed.hostname}:{parsed.port or 5432}")
    except OSError as exc:
        print(f"  [warn] Postgres TCP preflight failed ({exc}); continuing —")
        print("         pytest will surface the authoritative connection error.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    workers = args.workers if args.workers is not None else int(
        os.environ.get("PROBE_WORKERS", DEFAULT_WORKERS)
    )
    if workers < 1:
        parser.error(f"--workers must be >= 1 (got {workers})")
    # Forward to the pytest subprocess; the test module reads this at import.
    os.environ["PROBE_WORKERS"] = str(workers)

    checks: list[str] | None = None
    if args.check:
        checks = [name.strip() for name in args.check.split(",") if name.strip()]
        unknown = [name for name in checks if name not in CHECK_PROOFS]
        if unknown:
            parser.error(
                f"unknown --check name(s): {', '.join(unknown)}; "
                f"valid: {', '.join(CHECK_PROOFS)}"
            )

    print("=" * 72)
    print("Live-PostgreSQL multi-worker contention probe (PER-0700 wave 2)")
    print("=" * 72)
    print(f"  Test module:  {TEST_FILE}")
    print(f"  Workers:      {workers} (real OS processes, spawn context)")
    print(f"  Checks:       {', '.join(checks) if checks else 'all 4'}")

    os.chdir(REPO_ROOT)
    database_url = _load_env()
    if not database_url:
        print()
        print(
            "PREFLIGHT FAILED: DATABASE_URL is not set. The probe requires a "
            "live PostgreSQL; without it every probe test silently skips and "
            "proves nothing.\nAdd DATABASE_URL to .env (or export it) and "
            "re-run."
        )
        return 2

    print(f"  Database:     {_db_endpoint(database_url)} (credentials redacted)")
    _tcp_reachable(database_url)
    print()

    pytest_args = [sys.executable, "-m", "pytest", TEST_FILE]
    pytest_args += ["-vv", "--tb=long", "-rA"] if args.verbose else ["-v", "--tb=short"]
    if checks:
        pytest_args += ["-k", " or ".join(checks)]

    # Fixed argv list (never shell=True); pytest's exit code propagates.
    # Flush first so the header precedes pytest output even when piped (CI).
    sys.stdout.flush()
    proc = subprocess.run(pytest_args, check=False)

    print()
    print("-" * 72)
    print("What each probe check proves (all must pass on a healthy live PG):")
    for proof in CHECK_PROOFS.values():
        print(f"  - {proof}")
    print("-" * 72)
    if proc.returncode == 0:
        print(f"Probe PASSED: contention guarantees hold at {workers} workers.")
    else:
        print(f"Probe FAILED (exit {proc.returncode}): contention guarantee "
              f"violated or environment error — see pytest output above.")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
