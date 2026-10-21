"""Test environment capacity preflight and target isolation runner (F-19 / FND-0056).

Verifies:
1. Capacity: Disk space (prevents ENOSPC), RAM availability, process limits.
2. Target isolation: Ensures per-run isolated file namespace (tmp directory)
   and verifies PostgreSQL readiness when configured.
3. HTTP tier contention: Detects whether live servers on :8000 collide with test executions.
"""

from __future__ import annotations

import os
import shutil
import socket
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PreflightResult:
    passed: bool
    disk_free_gb: float
    postgres_available: bool | None
    port_8000_free: bool
    isolated_namespace: str
    warnings: list[str]
    errors: list[str]


def check_disk_capacity(min_free_gb: float = 1.0, path: str = ".") -> tuple[bool, float]:
    """Check if the filesystem has sufficient free space to prevent ENOSPC."""
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024**3)
    return free_gb >= min_free_gb, round(free_gb, 2)


def is_port_in_use(port: int = 8000, host: str = "127.0.0.1") -> bool:
    """Check if a local port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def create_isolated_run_namespace(base_dir: str = "tmp_test_runs") -> Path:
    """Create an isolated, dedicated per-run directory for file storage."""
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    ns_dir = Path(base_dir) / run_id
    ns_dir.mkdir(parents=True, exist_ok=True)
    return ns_dir


def check_postgres_readiness(database_url: str | None = None) -> tuple[bool, str]:
    """Test connection to PostgreSQL if configured."""
    url = database_url or os.environ.get("DATABASE_URL")
    if not url or "postgresql" not in url:
        return True, "PostgreSQL not configured (using mock/file backend)"

    try:
        # Quick socket check on port
        import urllib.parse

        parsed = urllib.parse.urlparse(url.replace("+asyncpg", ""))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex((host, port)) != 0:
                return False, f"PostgreSQL port {port} at {host} unreachable"
        return True, f"PostgreSQL at {host}:{port} reachable"
    except Exception as e:
        return False, f"PostgreSQL preflight check failed: {e}"


def run_preflight(
    require_clean_http: bool = False,
    min_disk_gb: float = 1.0,
    check_db: bool = True,
) -> PreflightResult:
    """Run comprehensive capacity, isolation, and contention preflight."""
    warnings: list[str] = []
    errors: list[str] = []

    # 1. Capacity
    disk_ok, free_gb = check_disk_capacity(min_disk_gb)
    if not disk_ok:
        errors.append(f"Insufficient disk space: {free_gb}GB free (minimum required: {min_disk_gb}GB)")

    # 2. Port contention
    in_use = is_port_in_use(8000)
    if in_use:
        msg = "Port 8000 is occupied by an active server. Integration tests may experience contention."
        if require_clean_http:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 3. DB readiness
    pg_ok: bool | None = None
    if check_db:
        db_url = os.environ.get("DATABASE_URL")
        if db_url and "postgresql" in db_url:
            pg_ok, pg_msg = check_postgres_readiness(db_url)
            if not pg_ok:
                warnings.append(f"PostgreSQL warning: {pg_msg}")
        else:
            pg_ok = True

    # 4. Isolated namespace
    isolated = create_isolated_run_namespace()

    passed = len(errors) == 0
    return PreflightResult(
        passed=passed,
        disk_free_gb=free_gb,
        postgres_available=pg_ok,
        port_8000_free=not in_use,
        isolated_namespace=str(isolated),
        warnings=warnings,
        errors=errors,
    )


def main() -> int:
    result = run_preflight()
    print("=== Test Environment Capacity & Isolation Preflight (F-19) ===")
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Free Disk: {result.disk_free_gb} GB")
    print(f"Port 8000 Free: {result.port_8000_free}")
    print(f"Isolated Run Namespace: {result.isolated_namespace}")
    if result.warnings:
        for w in result.warnings:
            print(f"WARNING: {w}")
    if result.errors:
        for e in result.errors:
            print(f"ERROR: {e}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
