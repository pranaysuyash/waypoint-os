"""Tests for test preflight capacity and target isolation runner (F-19 / FND-0056)."""

import os
import shutil

from scripts.test_preflight import (
    check_disk_capacity,
    create_isolated_run_namespace,
    run_preflight,
)


def test_check_disk_capacity_reports_free_gb():
    ok, free_gb = check_disk_capacity(min_free_gb=0.1)
    assert ok is True
    assert free_gb > 0.1


def test_create_isolated_run_namespace_creates_unique_dir(tmp_path):
    ns1 = create_isolated_run_namespace(base_dir=str(tmp_path))
    ns2 = create_isolated_run_namespace(base_dir=str(tmp_path))
    assert ns1 != ns2
    assert ns1.exists()
    assert ns2.exists()
    assert ns1.is_dir()


def test_run_preflight_clean_execution(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = run_preflight(require_clean_http=False, min_disk_gb=0.1, check_db=False)
    assert result.passed is True
    assert result.disk_free_gb > 0.1
    assert os.path.exists(result.isolated_namespace)
    # Cleanup
    if os.path.exists(result.isolated_namespace):
        shutil.rmtree(result.isolated_namespace, ignore_errors=True)
