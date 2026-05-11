#!/usr/bin/env python3
"""Dev server manager for stable local QA loops.

Starts/stops/status-checks backend and frontend dev servers as detached
processes with pid/log files so they survive across agent turns.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / ".runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Service:
    name: str
    command: Sequence[str]
    cwd: Path
    pid_file: Path
    log_file: Path
    health_url: str
    port: int


BACKEND = Service(
    name="backend",
    command=(".venv/bin/python", "-m", "uvicorn", "spine_api.server:app", "--host", "127.0.0.1", "--port", "8000"),
    cwd=REPO_ROOT,
    pid_file=RUNTIME_DIR / "backend.pid",
    log_file=RUNTIME_DIR / "backend.log",
    health_url="http://127.0.0.1:8000/health",
    port=8000,
)

FRONTEND = Service(
    name="frontend",
    command=("npm", "run", "dev"),
    cwd=REPO_ROOT / "frontend",
    pid_file=RUNTIME_DIR / "frontend.pid",
    log_file=RUNTIME_DIR / "frontend.log",
    health_url="http://127.0.0.1:3000/overview",
    port=3000,
)

SERVICES = {"backend": BACKEND, "frontend": FRONTEND}


def _read_pid(pid_file: Path) -> int | None:
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text().strip())
    except (TypeError, ValueError):
        return None


def _is_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _remove_pid(pid_file: Path) -> None:
    if pid_file.exists():
        pid_file.unlink()


def _start_service(svc: Service) -> None:
    port_pid = _pid_on_port(svc.port)
    if _is_running(port_pid):
        svc.pid_file.write_text(f"{port_pid}\n")
        print(f"{svc.name}: already running on port {svc.port} (pid={port_pid})")
        return

    existing = _read_pid(svc.pid_file)
    if _is_running(existing):
        print(f"{svc.name}: already running (pid={existing})")
        return

    with svc.log_file.open("ab") as log:
        process = subprocess.Popen(
            list(svc.command),
            cwd=str(svc.cwd),
            stdout=log,
            stderr=log,
            start_new_session=True,
            env=os.environ.copy(),
        )

    svc.pid_file.write_text(f"{process.pid}\n")
    print(f"{svc.name}: started (pid={process.pid})")


def _stop_service(svc: Service, timeout_s: float = 10.0) -> None:
    pid = _read_pid(svc.pid_file)
    if not _is_running(pid):
        pid = _pid_on_port(svc.port)
    if not _is_running(pid):
        _remove_pid(svc.pid_file)
        print(f"{svc.name}: not running")
        return

    assert pid is not None
    os.kill(pid, signal.SIGTERM)
    start = time.time()
    while time.time() - start < timeout_s:
        if not _is_running(pid):
            _remove_pid(svc.pid_file)
            print(f"{svc.name}: stopped")
            return
        time.sleep(0.2)

    os.kill(pid, signal.SIGKILL)
    _remove_pid(svc.pid_file)
    print(f"{svc.name}: force-stopped")


def _health_code(url: str, timeout_s: float = 8.0) -> int | None:
    try:
        with urlopen(url, timeout=timeout_s) as response:
            return int(response.getcode())
    except (URLError, TimeoutError, ValueError):
        return None


def _wait_healthy(svc: Service, timeout_s: float = 45.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        code = _health_code(svc.health_url)
        if code == 200:
            return True
        time.sleep(0.5)
    return False


def _status_service(svc: Service) -> int:
    pid = _read_pid(svc.pid_file)
    listen_pid = _pid_on_port(svc.port)
    if _is_running(listen_pid):
        if pid != listen_pid:
            pid = listen_pid
            svc.pid_file.write_text(f"{pid}\n")
    elif not _is_running(pid):
        pid = None
    running = _is_running(pid)
    code = _health_code(svc.health_url)
    state = "running" if running else "stopped"
    print(f"{svc.name}: {state} pid={pid or '-'} health={code if code is not None else 'down'}")
    return 0 if running and code == 200 else 1


def _pid_on_port(port: int) -> int | None:
    try:
        result = subprocess.run(
            ["lsof", "-nP", "-iTCP:%s" % port, "-sTCP:LISTEN", "-t"],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        if not lines:
            return None
        return int(lines[0])
    except (ValueError, OSError):
        return None


def _tail_logs(svc: Service, lines: int = 40) -> None:
    if not svc.log_file.exists():
        print(f"{svc.name}: no log at {svc.log_file}")
        return
    content = svc.log_file.read_text(errors="replace").splitlines()
    for line in content[-lines:]:
        print(line)


def _select_services(target: str) -> list[Service]:
    if target == "all":
        return [BACKEND, FRONTEND]
    return [SERVICES[target]]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage local travel_agency_agent dev servers")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "logs", "check"], help="operation")
    parser.add_argument("--service", choices=["all", "backend", "frontend"], default="all")
    parser.add_argument("--lines", type=int, default=40, help="log lines for logs action")
    args = parser.parse_args()

    services = _select_services(args.service)

    if args.action == "start":
        for svc in services:
            _start_service(svc)
        bad = []
        for svc in services:
            ok = _wait_healthy(svc)
            print(f"{svc.name}: {'healthy' if ok else 'unhealthy'}")
            if not ok:
                bad.append(svc.name)
        return 1 if bad else 0

    if args.action == "stop":
        for svc in services:
            _stop_service(svc)
        return 0

    if args.action == "restart":
        for svc in services:
            _stop_service(svc)
        for svc in services:
            _start_service(svc)
        bad = []
        for svc in services:
            ok = _wait_healthy(svc)
            print(f"{svc.name}: {'healthy' if ok else 'unhealthy'}")
            if not ok:
                bad.append(svc.name)
        return 1 if bad else 0

    if args.action == "status":
        codes = [_status_service(svc) for svc in services]
        return 1 if any(c != 0 for c in codes) else 0

    if args.action == "check":
        bad = []
        for svc in services:
            code = _health_code(svc.health_url)
            print(f"{svc.name}: health={code if code is not None else 'down'}")
            if code != 200:
                bad.append(svc.name)
        return 1 if bad else 0

    if args.action == "logs":
        for svc in services:
            print(f"--- {svc.name} log ({svc.log_file}) ---")
            _tail_logs(svc, lines=max(1, args.lines))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
