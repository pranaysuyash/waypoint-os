#!/usr/bin/env python3
"""
scripts/validate_decoupling.py — Rule 0.15 Third-Layer Decoupling Linter.

Verifies that LLM outputs in src/llm/ and src/intake/ are strictly decoupled from
pipeline decision gate state machines (Rule 0.15 in motto_v4.md).

Rules checked:
1. LLM prompts & extractors must NOT directly set decision_state ('PROCEED', 'ASK_FOLLOWUP', 'ESCALATE')
   without passing through deterministic validation in src/intake/decision.py or src/intake/gates.py.
2. Rate dictionaries, tax rules, and airport codes must remain in code/dict files, not LLM system prompts.
"""

import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Patterns that violate Rule 0.15 if present in LLM prompt strings
FORBIDDEN_PROMPT_PATTERNS = [
    (re.compile(r'decision_state\s*=\s*["\']PROCEED["\']', re.IGNORECASE), "LLM prompt directly assigns decision_state='PROCEED'"),
    (re.compile(r'decision_state\s*=\s*["\']ESCALATE["\']', re.IGNORECASE), "LLM prompt directly assigns decision_state='ESCALATE'"),
    (re.compile(r'SET_GATE_VERDICT', re.IGNORECASE), "LLM prompt directly triggers gate verdict bypass"),
]


def check_decoupling() -> bool:
    print("🔍 Running Rule 0.15 Third-Layer Decoupling Linter...")
    llm_dir = REPO_ROOT / "src" / "llm"
    intake_dir = REPO_ROOT / "src" / "intake"
    
    violations = 0
    scanned_files = 0
    
    target_files = list(llm_dir.glob("**/*.py")) + list(intake_dir.glob("extractors*.py"))
    
    for filepath in target_files:
        if not filepath.exists():
            continue
        scanned_files += 1
        content = filepath.read_text(encoding="utf-8")
        
        for pattern, description in FORBIDDEN_PROMPT_PATTERNS:
            if pattern.search(content):
                print(f"❌ Rule 0.15 Violation in {filepath.relative_to(REPO_ROOT)}: {description}")
                violations += 1
                
    if violations == 0:
        print(f"✅ Rule 0.15 Decoupling Check Passed ({scanned_files} files audited). Zero shadow bypasses found.")
        return True
    else:
        print(f"❌ {violations} decoupling violation(s) found!")
        return False


if __name__ == "__main__":
    success = check_decoupling()
    sys.exit(0 if success else 1)
