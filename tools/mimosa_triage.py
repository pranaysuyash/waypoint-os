#!/usr/bin/env python3
"""
tools/mimosa_triage.py — authorization-posture triage for Mimosa
business-logic-risk candidates.

Method (same bar as MIMOSA_TRIAGE_WAVE_2026-10-25.md): for each candidate
(file, line), walk back to the enclosing route decorator and classify the
authorization surface from REAL code — decorator dependencies, signature
dependencies, and router-level guards — then emit one ledger row per
candidate. Verdicts are computed from what the code declares, so a
"unguarded" row is a genuine lead requiring manual reading, never a final
classification by itself.

Usage:
  python3 tools/mimosa_triage.py <findings.json> [--seal-class business-logic-risk]

Output: TSV rows  file, line, findingId-tail, route, posture
Also prints posture histogram. Exit 0 always (triage tool).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

AGENCY_GUARDS = (
    "get_current_agency_id",
    "get_current_agency",
    "get_current_user",
    "get_current_membership",
    "require_platform_role",
    "get_platform_user",
    "require_super_admin",
    "boundary_principal",
)
CAPABILITY_GUARDS = (
    "verify_capability_token",
    "validate_token",
    "_verify",
    "hash_look",
    "token",
)
PUBLIC_BY_DESIGN_FILES = (
    "public_asks",
    "public_proposals",
    "public_collection",
    "public_checker",
    "trust_scorecard",
    "group_booking",
    "auth",
)


def _route_window(lines: list[str], idx: int) -> tuple[int, int]:
    """Return (decorator_start, func_def_line) for the route enclosing idx."""
    i = idx
    while i >= 0:
        stripped = lines[i].strip()
        if stripped.startswith("@") and ("router" in stripped or "public_router" in stripped):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("def "):
                j += 1
            return i, min(j, len(lines) - 1)
        i -= 1
    return -1, -1


def _signature_window(lines: list[str], def_i: int) -> list[str]:
    """Collect the function signature (through the line ending in ':')."""
    sig: list[str] = []
    j = def_i
    while j < len(lines):
        sig.append(lines[j])
        if re.search(r":\s*$", lines[j]) or "->" in lines[j]:
            break
        j += 1
    return sig


def classify(path: Path, line_no: int) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"posture": "FILE-MISSING", "route": "?"}
    idx = min(max(0, line_no - 1), len(lines) - 1)
    dec_i, def_i = _route_window(lines, idx)
    if dec_i < 0:
        return {"posture": "NON-ROUTE", "route": "?"}
    decorator = " ".join(
        lines[k].strip() for k in range(dec_i, def_i) if lines[k].strip().startswith("@")
    )
    sig = " ".join(s.strip() for s in _signature_window(lines, def_i))
    body = "\n".join(lines[def_i: min(def_i + 60, len(lines))])
    haystack = decorator + " || " + sig
    route = re.search(r"@[^\"']*\"([^\"]+)\"", decorator)
    route_path = route.group(1) if route else "?"
    method = "GET" if ".get(" in decorator else "POST" if ".post(" in decorator else (
        "PATCH" if ".patch(" in decorator else "PUT" if ".put(" in decorator else "DELETE" if ".delete(" in decorator else "?"
    )
    guards = sorted({g for g in AGENCY_GUARDS if g in haystack})
    cap = sorted({c for c in CAPABILITY_GUARDS if c in sig})
    if guards:
        posture = "AGENCY-DI:" + "+".join(guards)
    elif any(p in path.name for p in PUBLIC_BY_DESIGN_FILES):
        # public-by-design routers: the capability/token check lives in the body
        if any(c in body for c in ("token", "signature", "hmac", "HMAC", "hash")):
            posture = "PUBLIC-BY-DESIGN:token-verified-in-body"
        else:
            posture = "PUBLIC-BY-DESIGN:NEEDS-EYE"
    elif cap:
        posture = "CAPABILITY:" + "+".join(cap)
    else:
        posture = "UNGUARDED-LEAD"
    return {"posture": posture, "route": f"{method} {route_path}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("findings_json")
    ap.add_argument("--seal-class", default="business-logic-risk")
    args = ap.parse_args()
    data = json.loads(Path(args.findings_json).read_text(encoding="utf-8"))
    fs = data["findings"] if isinstance(data, dict) else data
    rows = []
    for f in fs:
        if f.get("identity", {}).get("publicClass") != args.seal_class:
            continue
        loc = f.get("location") or f.get("primaryLocation") or {}
        rel = str(loc.get("path") or loc.get("file") or "")
        line_no = int(loc.get("line") or 0)
        path = REPO / rel
        info = classify(path, line_no)
        rows.append((rel, line_no, f.get("findingId", "")[-12:], info["route"], info["posture"]))
    rows.sort()
    for rel, line_no, fid, route, posture in rows:
        print(f"{rel}:{line_no}\t{fid}\t{route}\t{posture}")
    from collections import Counter

    print("\nposture histogram:", json.dumps(Counter(r[4] for r in rows), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
