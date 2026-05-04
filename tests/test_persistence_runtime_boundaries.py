from __future__ import annotations

import os
import time
from pathlib import Path

from spine_api.persistence import file_lock


def test_file_lock_recovers_ownerless_stale_lockdir(tmp_path: Path):
    target = tmp_path / "events.jsonl"
    lock_dir = target.with_suffix(target.suffix + ".lockdir")
    lock_dir.mkdir()
    stale_time = time.time() - 120
    os.utime(lock_dir, (stale_time, stale_time))

    with file_lock(target, timeout_seconds=0.05):
        assert (lock_dir / "pid").read_text().strip() == str(os.getpid())

    assert not lock_dir.exists()
