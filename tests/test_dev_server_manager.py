from __future__ import annotations

from pathlib import Path
import inspect

from tools import dev_server_manager


def test_dev_server_manager_uses_ignored_local_runtime_dir():
    repo_root = Path(__file__).resolve().parents[1]
    runtime_dir = repo_root / ".runtime" / "local"

    assert dev_server_manager.RUNTIME_DIR == runtime_dir
    assert dev_server_manager.BACKEND.pid_file == runtime_dir / "backend.pid"
    assert dev_server_manager.BACKEND.log_file == runtime_dir / "backend.log"
    assert dev_server_manager.FRONTEND.pid_file == runtime_dir / "frontend.pid"
    assert dev_server_manager.FRONTEND.log_file == runtime_dir / "frontend.log"

    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert ".runtime/local/" in gitignore


def test_dev_server_manager_creates_runtime_dir_with_parents():
    source = inspect.getsource(dev_server_manager)

    assert "RUNTIME_DIR.mkdir(parents=True, exist_ok=True)" in source
