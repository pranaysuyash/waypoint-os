#!/usr/bin/env python3
"""
Read-only recovery guard report for stash/reset/worktree incidents.

This tool intentionally avoids any mutating git operation. It helps future
agents inspect the repo state and follow the safe selective-recovery workflow
instead of using destructive stash/reset shortcuts.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_git(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or proc.stderr).strip()
    return proc.returncode, output


def _print_section(title: str, body: str) -> None:
    print(f"\n## {title}")
    print(body if body else "(none)")


def _tracked_worktree_artifacts() -> str:
    code, output = _run_git(["ls-files", ".claude/worktrees"])
    if code != 0 or not output:
        return "(no tracked .claude/worktrees artifacts)"
    return output


def _stash_log_presence() -> str:
    stash_log = REPO_ROOT / ".git" / "logs" / "refs" / "stash"
    if not stash_log.exists():
        return "stash log missing"
    try:
        lines = stash_log.read_text().splitlines()
    except OSError as exc:
        return f"stash log unreadable: {exc}"
    if not lines:
        return "stash log present but empty"
    return f"stash log present with {len(lines)} entr{'y' if len(lines) == 1 else 'ies'}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a safe recovery report for stash/reset/worktree incidents."
    )
    parser.parse_args()

    code, branch = _run_git(["status", "--short", "--branch"])
    _print_section("Repository", str(REPO_ROOT))
    _print_section("Git Status", branch if code == 0 else "unable to read git status")

    code, head = _run_git(["rev-parse", "--short", "HEAD"])
    _print_section("HEAD", head if code == 0 else "unknown")

    code, worktrees = _run_git(["worktree", "list", "--porcelain"])
    _print_section("Worktrees", worktrees if code == 0 else "unable to read worktrees")

    code, stashes = _run_git(["stash", "list"])
    _print_section("Stash List", stashes if code == 0 and stashes else "(no visible stash entries)")
    _print_section("Stash Log", _stash_log_presence())

    _print_section("Tracked .claude/worktrees Artifacts", _tracked_worktree_artifacts())

    _print_section(
        "Safe Recovery Checklist",
        "\n".join(
            [
                "1. Do not run stash pop/apply, reset, restore, checkout --, or clean.",
                "2. Inspect branch ancestry and worktree status before deleting any worktree.",
                "3. Inspect stash/commit/worktree touched paths with read-only git commands.",
                "4. Classify each candidate path as source, doc, runtime/generated, or stale/superseded.",
                "5. Recover selectively and verify in the repo venv before claiming success.",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

