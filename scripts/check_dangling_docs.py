#!/usr/bin/env python3
"""
CI check to detect dangling/orphaned doc references such as 'motto_v4.md'
or other retired filenames across active code, scripts, and documentation.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

RETIRED_DOC_NAMES = [
    "motto_v4.md",
]

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".agent",
}

# Registers and audits that historically record the finding itself are allowed to mention the name
EXCLUDED_FILES = {
    "FINDINGS_REGISTER_2026-08-31.md",
    "FINDINGS_REGISTER_2026-08-29.md",
    "FINDINGS_STORE.jsonl",
    "FINDINGS_LIVE.md",
    "FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md",
    "DOCS_CORPUS_SHADOW_AUDIT_2026-08-31.md",
    "PERSONA_COUNCIL_MASTER_AUDIT_2026-08-29.md",
    "SESSION_RECORD_PERSONA_AUDIT_2026-08-29.md",
    "EXPLORATION_RESEARCH_BACKLOG_2026-08-29.md",
    "IMPLEMENTATION_PLAN_2026-08-29.md",
    "GTM_ANGLE_ASSESSMENT_2026-09-01.md",
}


def main() -> int:
    dangling_hits = []

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_FILES or path.name == "check_dangling_docs.py":
            continue
        if path.suffix not in (".py", ".ts", ".tsx", ".md", ".sh", ".json", ".yaml", ".yml"):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for target in RETIRED_DOC_NAMES:
            if target in content:
                dangling_hits.append((str(path.relative_to(REPO_ROOT)), target))

    if dangling_hits:
        print("ERROR: Dangling retired document references found:")
        for file_path, target in dangling_hits:
            print(f"  - {file_path}: references '{target}'")
        return 1

    print("SUCCESS: Zero dangling retired doc references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
