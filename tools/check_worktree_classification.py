#!/usr/bin/env python3
"""Validate a durable file-classification ledger against Git ground truth.

The checker supports either an immutable commit inventory or the live working
tree.  It intentionally validates classification coverage and provenance
fields; it does not claim that the classified implementation is correct.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


REQUIRED_COLUMNS = (
    "path",
    "git_state",
    "artifact_class",
    "slice_id",
    "ownership",
    "dependency",
    "disposition",
    "verification",
)


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def _commit_inventory(commit: str) -> dict[str, str]:
    output = _git(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "-M",
        commit,
    ).decode("utf-8")
    inventory: dict[str, str] = {}
    for line in output.splitlines():
        fields = line.split("\t")
        state = fields[0]
        path = fields[-1]
        inventory[path] = state
    return inventory


def _worktree_inventory() -> dict[str, str]:
    # -uall prevents Git from collapsing an untracked directory into one row.
    output = _git("status", "--porcelain=v1", "-z", "-uall")
    records = output.decode("utf-8").split("\0")
    inventory: dict[str, str] = {}
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4:
            raise ValueError(f"Malformed porcelain record: {record!r}")
        state = record[:2]
        path = record[3:]
        # Porcelain v1 emits a second NUL-delimited path for renames/copies.
        if "R" in state or "C" in state:
            if index >= len(records) or not records[index]:
                raise ValueError(f"Rename/copy record lacks source path: {record!r}")
            index += 1
        inventory[path] = state
    return inventory


def _is_tracked(path: Path) -> bool:
    result = subprocess.run(
        ("git", "ls-files", "--error-unmatch", "--", str(path)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _read_ledger(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    rows: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])
        ]
        if missing_columns:
            errors.append(f"missing columns: {', '.join(missing_columns)}")
            return rows, errors

        for line_number, row in enumerate(reader, start=2):
            normalized = {
                key: (row.get(key) or "")
                if key == "git_state"
                else (row.get(key) or "").strip()
                for key in REQUIRED_COLUMNS
            }
            path_value = normalized["path"]
            if not path_value:
                errors.append(f"line {line_number}: blank path")
                continue
            if path_value in rows:
                errors.append(f"line {line_number}: duplicate path {path_value}")
            blank_fields = [key for key, value in normalized.items() if not value]
            if blank_fields:
                errors.append(
                    f"line {line_number}: {path_value}: blank fields {', '.join(blank_fields)}"
                )
            forbidden = [
                key
                for key, value in normalized.items()
                if value.lower() in {"unclassified", "tbd", "todo"}
            ]
            if forbidden:
                errors.append(
                    f"line {line_number}: {path_value}: unresolved fields {', '.join(forbidden)}"
                )
            rows[path_value] = normalized["git_state"]
    return rows, errors


def _scaffold_worktree_ledger(path: Path) -> int:
    """Write a conservative ledger for the current worktree.

    The scaffold intentionally makes no ownership or correctness claim. It is
    a repeatable starting point for a human/agent to refine before accepting a
    release slice; the normal validator remains the required coverage gate.
    """
    inventory = _worktree_inventory()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        for file_path in sorted(inventory):
            writer.writerow(
                {
                    "path": file_path,
                    "git_state": inventory[file_path],
                    "artifact_class": "unknown_preserved_concurrent_artifact",
                    "slice_id": "LIVE-UNCLASSIFIED",
                    "ownership": "unknown_preserved_concurrent",
                    "dependency": "current_checkout_and_repo_instructions",
                    "disposition": "preserve_pending_semantic_classification",
                    "verification": "git_status_presence_only;not_product_or_release_proof",
                }
            )
    print(f"WROTE: {path} scaffold for {len(inventory)} live worktree paths")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument(
        "--scaffold-worktree",
        action="store_true",
        help="write a conservative current-worktree ledger, then exit",
    )
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--commit")
    source.add_argument("--worktree", action="store_true")
    args = parser.parse_args()

    if args.scaffold_worktree:
        if args.commit:
            parser.error("--scaffold-worktree cannot be combined with --commit")
        return _scaffold_worktree_ledger(args.ledger)
    if not args.commit and not args.worktree:
        parser.error("one of --commit or --worktree is required")

    expected = _commit_inventory(args.commit) if args.commit else _worktree_inventory()
    # A newly generated untracked ledger cannot classify itself until it is
    # accepted into Git. Exclude only that exact output path; once tracked, it
    # is part of the normal coverage contract.
    ledger_is_untracked = args.worktree and not _is_tracked(args.ledger)
    if ledger_is_untracked:
        expected.pop(str(args.ledger), None)
    actual, errors = _read_ledger(args.ledger)
    if ledger_is_untracked:
        actual.pop(str(args.ledger), None)

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        path for path in set(expected) & set(actual) if expected[path] != actual[path]
    )
    if missing:
        errors.append("missing Git paths: " + ", ".join(missing))
    if extra:
        errors.append("ledger-only paths: " + ", ".join(extra))
    for path in mismatched:
        errors.append(
            f"state mismatch: {path}: git={expected[path]!r}, ledger={actual[path]!r}"
        )

    if errors:
        print(f"FAIL: {args.ledger} ({len(errors)} error(s))")
        for error in errors:
            print(f"- {error}")
        return 1

    source_label = f"commit {args.commit}" if args.commit else "live worktree"
    print(
        f"PASS: {args.ledger} classifies all {len(expected)} paths from {source_label}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
