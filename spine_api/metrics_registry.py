"""
spine_api/metrics_registry.py — Minimal in-process Prometheus registry (PA-10).

PA-10 (2026-09-06): ``GET /metrics`` previously returned a static JSON body
while claiming to be a Prometheus endpoint. This module provides a
dependency-free counter/gauge registry plus a Prometheus text exposition
(v0.0.4) renderer, and server.py's ``/metrics`` renders it with the correct
content type.

Scope and honesty notes:
- Counters are process-local (single-worker truth). Multi-worker deployments
  should scrape each worker or promote this registry to a shared store.
- ``spine_runs_total`` / ``spine_runs_failed_by_class`` series are registered
  and label-ready but stay at 0 until the pipeline execution layer increments
  them at terminal-state writes. TODO(integrator, PA-10): call
  ``inc_run_outcome(outcome)`` / ``inc_run_failure(failure_class)`` from the
  run terminal callback in spine_api/services/pipeline_execution_service.py
  (owned by another workstream at the time of this change).
- Lease/pending/usage gauges are read defensively at scrape time; any read
  failure yields 0 rather than a failed scrape.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Dict, Tuple

_REGISTRY_LOCK = threading.Lock()

# (metric_name, sorted label tuple) -> value
_counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
_gauges: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}

# metric_name -> (HELP, TYPE)
_metric_meta: Dict[str, Tuple[str, str]] = {}

_PROCESS_START = time.time()

# Canonical run-outcome labels (matches RunLedger terminal vocabulary).
_RUN_OUTCOMES = ("completed", "failed", "blocked")


def _label_key(labels: Dict[str, str] | None) -> Tuple[Tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


def _declare(name: str, help_text: str, metric_type: str) -> None:
    with _REGISTRY_LOCK:
        _metric_meta.setdefault(name, (help_text, metric_type))


def inc_counter(name: str, labels: Dict[str, str] | None = None, value: float = 1.0) -> None:
    """Increment a counter series (creates it at 0 on first sight)."""
    key = (name, _label_key(labels))
    with _REGISTRY_LOCK:
        _metric_meta.setdefault(name, (name, "counter"))
        _counters[key] = _counters.get(key, 0.0) + value


def ensure_counter(name: str, labels: Dict[str, str] | None = None) -> None:
    """Declare a counter series at 0 without incrementing (label vocabulary)."""
    key = (name, _label_key(labels))
    with _REGISTRY_LOCK:
        _metric_meta.setdefault(name, (name, "counter"))
        _counters.setdefault(key, 0.0)


def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None) -> None:
    """Set a gauge series value."""
    key = (name, _label_key(labels))
    with _REGISTRY_LOCK:
        _metric_meta.setdefault(name, (name, "gauge"))
        _gauges[key] = float(value)


# ---------------------------------------------------------------------------
# Domain helpers (TODO hooks for the integrator)
# ---------------------------------------------------------------------------


def inc_run_outcome(outcome: str) -> None:
    """Increment spine_runs_total{outcome=...}.

    TODO(integrator, PA-10): wire from the run terminal-state write in
    spine_api/services/pipeline_execution_service.py (completed/failed/blocked)
    — that file is owned by another workstream and was left untouched here.
    """
    inc_counter("spine_runs_total", {"outcome": outcome})


def inc_run_failure(failure_class: str = "unclassified") -> None:
    """Increment spine_runs_failed_by_class{failure_class=...}.

    TODO(integrator, PA-10): pair with the PA-07 failure-taxonomy work so
    classes come from the ledger's failure classification, not raw exception
    names.
    """
    inc_counter("spine_runs_failed_by_class", {"failure_class": failure_class})


# ---------------------------------------------------------------------------
# Runtime gauge collectors (defensive: read failure -> 0)
# ---------------------------------------------------------------------------


def _requeue_jobs_pending() -> float:
    try:
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        counts = RequeueJobStore().snapshot().get("counts", {})
        return float(counts.get("pending", 0))
    except Exception:
        return 0.0


def _work_leases_active() -> float:
    try:
        from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

        snap = SQLWorkCoordinator().snapshot()
        total = float(len(snap.get("leases", {})))
        terminal = float(snap.get("completed", 0)) + float(snap.get("poisoned", 0))
        # TODO(PA-29): snapshot is capped at the 200 most recent lease rows, so
        # this is a bounded-window approximation until the coordinator grows a
        # dedicated COUNT query.
        return max(0.0, total - terminal)
    except Exception:
        return 0.0


def _usage_guard_spend_today_usd() -> float:
    """Today's usage-guard spend, summed across agencies/features.

    Reuses the canonical store's path + schema conventions
    (src/llm/usage_store.py: ``usage_events`` keyed by ``usage_date``
    YYYY-MM-DD, cost = actual for reserved/completed else estimated) via a
    read-only aggregate; the store module itself was not modified.
    """
    try:
        import os
        import sqlite3

        from src.llm.usage_store import LLMUsageStore

        db_path = LLMUsageStore.get_default_path()
        if not os.path.exists(db_path):
            return 0.0
        usage_date = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN status IN ('reserved','completed')
                                         THEN actual_cost ELSE estimated_cost END), 0)
                FROM usage_events WHERE usage_date = ?
                """,
                (usage_date,),
            ).fetchone()
            return float(row[0] or 0.0)
        finally:
            conn.close()
    except Exception:
        return 0.0


def collect_runtime_gauges() -> None:
    """Refresh the scrape-time gauges. Call immediately before render()."""
    set_gauge("spine_requeue_jobs_pending", _requeue_jobs_pending())
    set_gauge("spine_work_leases_active", _work_leases_active())
    set_gauge("spine_usage_guard_spend_today_usd", _usage_guard_spend_today_usd())
    set_gauge("spine_process_uptime_seconds", time.time() - _PROCESS_START)


# ---------------------------------------------------------------------------
# Runtime gauge collectors (defensive: read failure -> 0)
# ---------------------------------------------------------------------------


def _escape_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _escape_help(help_text: str) -> str:
    return help_text.replace("\\", "\\\\").replace("\n", "\\n")


def render() -> str:
    """Render the registry as Prometheus text exposition (v0.0.4)."""
    with _REGISTRY_LOCK:
        lines: list[str] = []
        seen_meta: set[str] = set()

        def _fmt(value: float) -> str:
            # Prometheus samples are floats; integral values render without a
            # trailing .0 for readability.
            return str(int(value)) if float(value).is_integer() else repr(float(value))

        def _emit_meta(name: str) -> None:
            if name in seen_meta:
                return
            help_text, metric_type = _metric_meta.get(name, (name, "untyped"))
            lines.append(f"# HELP {name} {_escape_help(help_text)}")
            lines.append(f"# TYPE {name} {metric_type}")
            seen_meta.add(name)

        for (name, labels), value in sorted(_counters.items()):
            _emit_meta(name)
            label_str = ""
            if labels:
                pairs = ",".join(
                    f'{k}="{_escape_label_value(v)}"' for k, v in labels
                )
                label_str = "{" + pairs + "}"
            lines.append(f"{name}{label_str} {_fmt(value)}")

        for (name, labels), value in sorted(_gauges.items()):
            _emit_meta(name)
            label_str = ""
            if labels:
                pairs = ",".join(
                    f'{k}="{_escape_label_value(v)}"' for k, v in labels
                )
                label_str = "{" + pairs + "}"
            lines.append(f"{name}{label_str} {_fmt(value)}")

    return "\n".join(lines) + "\n"


def reset() -> None:
    """Reset to the canonical pre-seeded state. Intended for tests only."""
    with _REGISTRY_LOCK:
        _counters.clear()
        _gauges.clear()
        _metric_meta.clear()
    _seed()


def _seed() -> None:
    """Pre-register canonical series so label vocabularies are visible from
    the first scrape (counters at 0 until the integrator wires increments)."""
    _declare(
        "spine_runs_total",
        "Spine runs by terminal outcome (wired by pipeline terminal callback; "
        "TODO PA-10 integrator hook).",
        "counter",
    )
    for _outcome in _RUN_OUTCOMES:
        ensure_counter("spine_runs_total", {"outcome": _outcome})

    _declare(
        "spine_runs_failed_by_class",
        "Failed spine runs by failure taxonomy class (PA-07); unclassified is "
        "the pre-taxonomy placeholder.",
        "counter",
    )
    ensure_counter("spine_runs_failed_by_class", {"failure_class": "unclassified"})

    _declare(
        "spine_requeue_jobs_pending", "Requeue jobs in pending state.", "gauge"
    )
    _declare(
        "spine_work_leases_active",
        "Active agent work leases (bounded-window approximation; TODO PA-29).",
        "gauge",
    )
    _declare(
        "spine_usage_guard_spend_today_usd",
        "Usage-guard spend for today, summed across agencies (USD-equivalent).",
        "gauge",
    )
    _declare(
        "spine_process_uptime_seconds", "Process uptime in seconds.", "gauge"
    )


_seed()


# Backwards-friendly alias for callers that prefer an explicit name.
render_prometheus = render
