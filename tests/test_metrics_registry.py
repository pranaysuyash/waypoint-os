"""
tests/test_metrics_registry.py — PA-10 S2 evidence (2026-09-06).

FAILED BEFORE: GET /metrics returned a static JSON body
(``{"status": "ok", "app": "spine_api", "version": "1.0.0"}``) while claiming
to be a Prometheus endpoint — nothing scrapable, no counters, no gauges.

PASSES AFTER: /metrics renders spine_api/metrics_registry.py as Prometheus
text exposition v0.0.4 with the correct content type, run-outcome counters
(label-ready, TODO-wired by the integrator), and live runtime gauges.
"""

from __future__ import annotations

import pytest

from spine_api import metrics_registry as mr


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the module-level registry to the canonical pre-seed per test."""
    mr.reset()
    yield
    mr.reset()


def test_counters_increment_and_render_with_labels():
    mr.inc_counter("spine_runs_total", {"outcome": "completed"})
    mr.inc_counter("spine_runs_total", {"outcome": "completed"})
    mr.inc_counter("spine_runs_total", {"outcome": "failed"})

    text = mr.render()
    assert '# TYPE spine_runs_total counter' in text
    assert 'spine_runs_total{outcome="completed"} 2' in text
    assert 'spine_runs_total{outcome="failed"} 1' in text


def test_preseeded_series_are_label_ready_and_zero():
    text = mr.render()
    # Run outcome vocabulary visible from the first scrape (PA-10 spec).
    for outcome in ("completed", "failed", "blocked"):
        assert f'spine_runs_total{{outcome="{outcome}"}} 0' in text
    assert 'spine_runs_failed_by_class{failure_class="unclassified"} 0' in text


def test_gauges_set_and_render():
    mr.set_gauge("spine_test_gauge", 3.5, {"agency": "a1"})
    text = mr.render()
    assert '# TYPE spine_test_gauge gauge' in text
    assert 'spine_test_gauge{agency="a1"} 3.5' in text


def test_runtime_gauges_populated_without_crash():
    # Defensive collectors must always produce finite gauge values (0 on error).
    mr.collect_runtime_gauges()
    text = mr.render()
    assert "spine_requeue_jobs_pending " in text
    assert "spine_requeue_jobs_poisoned " in text
    assert "spine_requeue_jobs_poisoned_age_seconds " in text
    assert "spine_work_leases_active " in text
    assert "spine_usage_guard_spend_today_usd " in text
    assert "spine_process_uptime_seconds " in text
    assert " nan" not in text.lower()


def test_poisoned_gauges_rendered_and_finite():
    # FND-0224: poison visibility is a scrape contract — gauges render with a
    # finite (0 on DB error) value like every other runtime gauge.
    mr.collect_runtime_gauges()
    text = mr.render()
    assert '# TYPE spine_requeue_jobs_poisoned gauge' in text
    assert '# TYPE spine_requeue_jobs_poisoned_age_seconds gauge' in text
    assert "spine_requeue_jobs_poisoned " in text
    assert "spine_requeue_jobs_poisoned_age_seconds " in text
    assert " nan" not in text.lower()


def test_render_escapes_help_and_label_values():
    mr.inc_counter("spine_esc_test", {"weird": 'a"b\\c'})
    text = mr.render()
    assert 'spine_esc_test{weird="a\\"b\\\\c"}' in text


def test_metrics_endpoint_content_type_and_body(session_client):
    resp = session_client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "version=0.0.4" in resp.headers["content-type"]
    body = resp.text
    assert body.startswith("# HELP")
    assert "spine_runs_total" in body
    # The old static-JSON contract is gone.
    assert '"status": "ok"' not in body
