#!/usr/bin/env python3
"""Project-local feature completeness scanner.

This is the repo-owned scanner used for progression reviews. It intentionally
keeps evidence matching conservative: every configured search term must be
found across all configured globs before a sub-feature is marked done.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

RG_EXCLUDES = [
    "node_modules",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".next",
    "dist",
    "build",
    ".turbo",
    ".cache",
    ".claude",
    ".codex",
    ".agent",
    ".hermes",
]


@dataclass(slots=True)
class SubResult:
    id: str
    name: str
    score: float = 0.0
    matches: int = 0
    matched_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    status: str = "unknown"


@dataclass(slots=True)
class FeatureResult:
    id: str
    name: str
    priority: str
    baseline_score: int = 0
    baseline_max: int = 10
    subs: list[SubResult] = field(default_factory=list)

    @property
    def norm(self) -> float:
        return sum(sub.score for sub in self.subs) / max(1, len(self.subs))

    @property
    def delta(self) -> float:
        return self.norm - (self.baseline_score / max(1, self.baseline_max))


def _rg_base_command(root: Path) -> list[str]:
    command = ["rg", "-n", "--no-heading"]
    for excluded in RG_EXCLUDES:
        command.extend(["--glob", f"!{excluded}/**"])
    command.append(str(root))
    return command


def _parse_rg_lines(root: Path, output: str) -> list[dict[str, Any]]:
    evidence = []
    for line in output.splitlines():
        match = re.match(r"^([^:]+):(\d+):(.*)$", line)
        if not match:
            continue
        path = Path(match.group(1))
        try:
            file_name = str(path.relative_to(root))
        except ValueError:
            file_name = str(path)
        evidence.append(
            {
                "file": file_name,
                "line": int(match.group(2)),
                "content": match.group(3).strip()[:160],
            }
        )
    return evidence


def rg_search(root: Path, file_globs: list[str], term: str, timeout: int = 30) -> list[dict[str, Any]]:
    command = ["rg", "-n", "--no-heading"]
    for file_glob in file_globs:
        command.extend(["--glob", file_glob])
    for excluded in RG_EXCLUDES:
        command.extend(["--glob", f"!{excluded}/**"])
    command.extend(["-e", re.escape(term), str(root)])
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except Exception:
        return []
    return _parse_rg_lines(root, result.stdout)


def file_exists(root: Path, file_globs: list[str]) -> bool:
    for file_glob in file_globs:
        try:
            result = subprocess.run(
                ["rg", "--files", "--glob", file_glob, str(root)],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            if list(root.glob(file_glob)):
                return True
        else:
            if result.stdout.strip():
                return True
    return False


def count_tests(root: Path, file_globs: list[str]) -> int:
    pattern = r"(?:def\s+test_|it\(|describe\()"
    total = 0
    for file_glob in file_globs:
        try:
            result = subprocess.run(
                ["rg", "-c", "--glob", file_glob, pattern, str(root)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            continue
        total += sum(int(line.rsplit(":", 1)[1]) for line in result.stdout.splitlines() if ":" in line)
    return total


def scan_sub(root: Path, sub: dict[str, Any]) -> SubResult:
    evidence_spec = sub.get("evidence", {})
    file_globs = evidence_spec.get("files") or ["**/*"]
    terms = evidence_spec.get("min_search_terms") or []
    result = SubResult(id=sub["id"], name=sub["name"])

    if evidence_spec.get("directory_exists"):
        result.status = "done" if (root / file_globs[0].rstrip("/")).is_dir() else "missing"
        result.score = 1.0 if result.status == "done" else 0.0
        return result

    if evidence_spec.get("count_instead"):
        result.matches = count_tests(root, file_globs)
        if result.matches >= 500:
            result.score, result.status = 1.0, "done"
        elif result.matches >= 200:
            result.score, result.status = 0.6, "partial"
        else:
            result.score, result.status = 0.2, "missing"
        return result

    if not terms:
        result.status = "done" if file_exists(root, file_globs) else "missing"
        result.score = 1.0 if result.status == "done" else 0.0
        return result

    for term in terms:
        term_evidence = rg_search(root, file_globs, term)
        if term_evidence:
            result.matched_terms.append(term)
            result.evidence.extend(term_evidence[:3])
        else:
            result.missing_terms.append(term)

    result.matches = len(result.evidence)
    if not result.missing_terms:
        result.score, result.status = 1.0, "done"
    elif result.matched_terms:
        result.score = round(len(result.matched_terms) / len(terms), 2)
        result.status = "partial"
    else:
        result.score, result.status = 0.0, "missing"
    return result


def scan(root: Path, catalog_path: Path, priority: str | None = None) -> list[FeatureResult]:
    catalog = json.loads(catalog_path.read_text())
    results = []
    for feature in catalog.get("features", []):
        if priority and feature.get("priority") != priority:
            continue
        feature_result = FeatureResult(
            id=feature["id"],
            name=feature["name"],
            priority=feature.get("priority", "?"),
            baseline_score=feature.get("baseline_score", 0),
            baseline_max=feature.get("baseline_max", 10),
        )
        feature_result.subs = [scan_sub(root, sub) for sub in feature.get("sub_features", [])]
        results.append(feature_result)
    return results


def _json_payload(project: str | None, scan_date: str, results: list[FeatureResult]) -> dict[str, Any]:
    return {
        "project": project,
        "scanned_at": scan_date,
        "current_overall": round(sum(result.norm for result in results) / max(1, len(results)), 2),
        "features": [
            {
                "id": result.id,
                "name": result.name,
                "priority": result.priority,
                "baseline": f"{result.baseline_score}/{result.baseline_max}",
                "current": round(result.norm, 2),
                "delta": round(result.delta, 2),
                "subs": [
                    {
                        "id": sub.id,
                        "name": sub.name,
                        "score": round(sub.score, 2),
                        "matches": sub.matches,
                        "status": sub.status,
                        "matched_terms": sub.matched_terms,
                        "missing_terms": sub.missing_terms,
                        "evidence": sub.evidence[:5],
                    }
                    for sub in result.subs
                ],
            }
            for result in results
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Feature completeness scanner")
    parser.add_argument("root")
    parser.add_argument("--catalog", default="tools/feature_catalog.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--delta", action="store_true")
    parser.add_argument("--priority", choices=["P0", "P1", "P2", "P3", "Complete"])
    parser.add_argument("--scan-date", default=date.today().isoformat())
    args = parser.parse_args()

    root = Path(args.root).resolve()
    catalog_path = Path(args.catalog).resolve()
    catalog = json.loads(catalog_path.read_text())
    results = scan(root, catalog_path, args.priority)

    if args.json:
        print(json.dumps(_json_payload(catalog.get("project"), args.scan_date, results), indent=2))
        return

    overall = sum(result.norm for result in results) / max(1, len(results))
    print(f"\n{'=' * 64}")
    print("  FEATURE COMPLETENESS SCAN")
    print(f"  Project: {catalog.get('project')}")
    print(f"  Scanned at: {args.scan_date}")
    print(f"  Current: {overall:.2f} / 1.00")
    print(f"  Features scanned: {len(results)}")
    print(f"{'=' * 64}\n")
    for result in sorted(results, key=lambda item: -item.norm):
        print(f"  [{result.priority}] {result.id}: {result.name} ({result.norm:.2f})")
        for sub in result.subs:
            print(
                f"      {sub.status:7} {sub.id}: {sub.name} "
                f"({sub.score:.2f}) matched={len(sub.matched_terms)} missing={len(sub.missing_terms)}"
            )
        print()


if __name__ == "__main__":
    main()
