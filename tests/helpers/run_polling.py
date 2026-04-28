from __future__ import annotations

import time
from typing import Any

import pytest
import requests

TERMINAL_RUN_STATES = {"completed", "failed", "blocked"}


def get_run_status(api_base: str, run_id: str, headers: dict[str, str], timeout: int = 10) -> requests.Response:
    return requests.get(f"{api_base}/runs/{run_id}", timeout=timeout, headers=headers)


def get_run_events(api_base: str, run_id: str, headers: dict[str, str], timeout: int = 10) -> requests.Response:
    return requests.get(f"{api_base}/runs/{run_id}/events", timeout=timeout, headers=headers)


def get_run_step(
    api_base: str,
    run_id: str,
    step_name: str,
    headers: dict[str, str],
    timeout: int = 10,
) -> requests.Response:
    return requests.get(
        f"{api_base}/runs/{run_id}/steps/{step_name}",
        timeout=timeout,
        headers=headers,
    )


def wait_for_terminal(
    api_base: str,
    run_id: str,
    headers: dict[str, str],
    timeout_s: float = 30.0,
    poll_s: float = 0.2,
) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        resp = get_run_status(api_base, run_id, headers)
        assert resp.status_code == 200, f"GET /runs/{run_id} failed: {resp.status_code} {resp.text}"
        last = resp.json()
        if last.get("state") in TERMINAL_RUN_STATES:
            return last
        time.sleep(poll_s)
    pytest.fail(
        f"Run {run_id} did not reach terminal state within {timeout_s}s. Last status: {last}"
    )
