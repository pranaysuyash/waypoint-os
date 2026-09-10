#!/usr/bin/env python3
"""Strip AI tool-call envelope fragments from document files.

Repair tool for the 2026-04-23 batch-write defect (commit c7fa31d and
adjacent): 108+ docs under Docs/ were written with the tail of an XML-ish
agent tool-call envelope welded to the document body, e.g.:

    ...- Government travel experience and professional enhancement</content>
    <parameter name="filePath">/Users/.../SOME_FILE.md

The file ends mid-envelope (no closing tags, no trailing newline).

This tool removes ONLY the exact, verified envelope tail:
  * the marker `</content>` must occur exactly once, at end of a line,
  * the entire remainder after it must be exactly one line matching
    `<parameter name="filePath">...` (optionally followed by whitespace),
  * nothing before the marker may be touched.

Anything that does not match this strict shape is reported for manual
review and left unmodified. No bytes are rewritten beyond stripping the
envelope; a single trailing newline is ensured to match the series
convention (clean siblings end with \\n).

Usage:
    python3 tools/strip_envelope_fragments.py            # apply (default)
    python3 tools/strip_envelope_fragments.py --dry-run  # report only
    python3 tools/strip_envelope_fragments.py --check    # detection only,
                                                          # never writes;
                                                          # exit 1 if any
                                                          # file still dirty

Exit codes: 0 clean / 1 dirty (or error) / 2 manual-review needed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Exact envelope tail. `</content>` at end of a line, then exactly one
# `<parameter name="filePath">` line running to EOF (no closing tag was
# ever written). Trailing whitespace tolerated, nothing else.
ENVELOPE_TAIL = re.compile(
    r'</content>\s*\n<parameter name="filePath">[^\n]*\s*$'
)

# Any envelope-ish marker anywhere (detection for --check / review lists).
# Markdown code spans/blocks are exempted: documentation about this defect
# legitimately quotes the markers (see Docs/travel_agency_process_issue_review_2026-09-10.md),
# and machine-quoted text is not a write-path defect.
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
ANY_MARKER = re.compile(r"</content>|<parameter name=\"filePath\"")


def _strip_quoted_markdown(text: str) -> str:
    """Remove fenced blocks and inline code spans before marker detection."""
    return _INLINE_CODE.sub("", _CODE_FENCE.sub("", text))


def classify(path: Path) -> str:
    """Return 'clean' | 'fixable' | 'review' for one file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return f"unreadable:{exc}"
    if not ANY_MARKER.search(_strip_quoted_markdown(text)):
        return "clean"
    if ENVELOPE_TAIL.search(text):
        # Strict shape requires the marker set exactly once each.
        if text.count("</content>") == 1 and text.count('<parameter name="filePath"') == 1:
            return "fixable"
        return "review"
    return "review"


def fix(path: Path) -> tuple[str, int]:
    """Apply the strict tail strip. Returns (status, bytes_removed)."""
    text = path.read_text(encoding="utf-8")
    match = ENVELOPE_TAIL.search(text)
    if not match:
        return "review", 0
    fixed = text[: match.start()] + "\n"
    if fixed == text:
        return "already-clean", 0
    removed = len(text) - len(fixed)
    path.write_text(fixed, encoding="utf-8")
    return "fixed", removed


def _display(path: Path) -> str:
    """Repo-relative display path; absolute when the file lives in another
    repo (the tool is also used cross-repo for sibling-repo sweeps)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report only, no writes")
    parser.add_argument(
        "--check",
        action="store_true",
        help="detection only (exit 1 if any file under the roots still carries "
        "envelope markers); never writes — safe for CI/pre-commit",
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=["Docs"],
        help="directories to scan (default: Docs)",
    )
    args = parser.parse_args()

    roots = [Path(r) if Path(r).is_absolute() else REPO / r for r in args.roots]
    files = sorted(
        p
        for root in roots
        for p in root.rglob("*.md")
        if p.is_file()
    )

    stats: dict[str, int] = {}
    review_paths: list[Path] = []
    for path in files:
        status = classify(path)
        stats[status] = stats.get(status, 0) + 1
        if status == "fixable":
            # Writes are a positive opt-in: only plain apply mode mutates
            # files. --dry-run reports; --check detects (CI/pre-commit uses
            # --check and must never repair mid-gate).
            if args.dry_run or args.check:
                print(f"WOULD FIX: {_display(path)}")
            else:
                result, removed = fix(path)
                if result == "review":  # reclassified on exact-match fail
                    review_paths.append(path)
                    stats[result] = stats.get(result, 0) + 1
                    stats["fixable"] = stats["fixable"] - 1
                    continue
                print(f"FIXED: {_display(path)} ({removed} bytes removed)")
        elif status == "review":
            review_paths.append(path)
            print(f"REVIEW: {_display(path)}")

    print(f"\nSummary: {dict(sorted(stats.items()))}")
    if review_paths:
        print(f"Manual review needed for {len(review_paths)} file(s) — no changes made to them.")

    if args.check:
        dirty = stats.get("fixable", 0) + stats.get("review", 0)
        return 1 if dirty else 0
    return 2 if review_paths else 0


if __name__ == "__main__":
    sys.exit(main())
