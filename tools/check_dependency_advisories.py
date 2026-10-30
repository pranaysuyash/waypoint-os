#!/usr/bin/env python3
"""Dependency-advisory gate analyzer — pure Python, no subprocess.

Pairs with pip-audit run OUTSIDE this script (the security scanner rejects
Python-spawned subprocesses on principle, so the pipeline lives in shell):

    uv export --no-hashes --no-emit-project -q -o /tmp/reqs.txt
    uvx pip-audit -r /tmp/reqs.txt --no-deps -f json -o /tmp/audit.json
    python3 tools/check_dependency_advisories.py /tmp/audit.json

Behavior: parse pip-audit JSON, list each vulnerability (package, version,
CVE id, fix versions), exit 0 when clean / 1 when any advisory exists /
2 when the input is unreadable. Context: the Mimosa scanner's OFFLINE
advisory DB over-matches (reported "6 packages / 41 advisories" where the
networked truth was 2 packages / 4 CVEs) — this tool is the authoritative
re-runnable check. Monthly cadence per TRV-DP-06 D1; wire the three-line
pipeline into CI when a networked CI runner exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    audit_path = Path(argv[1])
    if not audit_path.is_file():
        print(f"audit JSON not found: {audit_path}", file=sys.stderr)
        return 2

    try:
        data = json.loads(audit_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"could not read audit JSON: {exc}", file=sys.stderr)
        return 2

    deps = data.get("dependencies", [])
    vulns = [
        {"package": d.get("name"), "version": d.get("version"),
         "id": v.get("id"), "fix_versions": v.get("fix_versions")}
        for d in deps for v in d.get("vulns", [])
    ]

    if not vulns:
        print(f"advisory gate: PASS ({len(deps)} pinned dependencies, 0 vulnerabilities)")
        return 0

    print("advisory gate: FAIL")
    for v in vulns:
        fixes = ", ".join(v["fix_versions"] or [])
        print(f"  {v['package']} {v['version']}: {v['id']} (fix: {fixes})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
