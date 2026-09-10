"""Contract tests for tools/strip_envelope_fragments.py.

Pins the write-mode contract repaired on 2026-09-10: --check and --dry-run
must NEVER mutate files; only plain apply mode writes. The defect: CI ran
`--check` on every build, and because fix() was gated only on --dry-run, the
"detector" silently repaired the working tree mid-gate (mutation during a
fail-closed check).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "strip_envelope_fragments.py"

# The exact 2026-04-23 defect shape: document body + welded envelope tail.
DIRTY_DOC = (
    "# Some Doc\n\nBody text describing a capability.\n\n"
    "Final prose line.</content>\n"
    '<parameter name="filePath">/Users/x/Projects/repo/SOME_FILE.md'
)
CLEAN_DOC = "# Some Doc\n\nBody text describing a capability.\n"


def _run(mode: str | None, root: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(TOOL)]
    if mode:
        cmd.append(mode)
    cmd.append(str(root))
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_doc(tmp: Path, name: str, content: str) -> Path:
    doc = tmp / name
    doc.write_text(content, encoding="utf-8")
    return doc


def test_check_mode_never_writes(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_check")
    doc = _make_doc(tmp, "dirty.md", DIRTY_DOC)
    before = doc.read_text(encoding="utf-8")

    proc = _run("--check", tmp)
    assert proc.returncode == 1, "--check must exit 1 on dirty files"
    assert doc.read_text(encoding="utf-8") == before, (
        "--check mutated a file — detection-only contract broken"
    )
    assert "WOULD FIX" in proc.stdout, "--check should still report dirty files"


def test_dry_run_mode_never_writes(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_dry")
    doc = _make_doc(tmp, "dirty.md", DIRTY_DOC)
    before = doc.read_text(encoding="utf-8")

    proc = _run("--dry-run", tmp)
    # Exit 0 with no review-class files (2 is reserved for review-needed).
    assert proc.returncode == 0
    assert "WOULD FIX" in proc.stdout, "--dry-run must report fixable files"
    assert doc.read_text(encoding="utf-8") == before, (
        "--dry-run mutated a file — report-only contract broken"
    )


def test_apply_mode_strips_only_the_envelope_tail(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_apply")
    doc = _make_doc(tmp, "dirty.md", DIRTY_DOC)

    proc = _run(None, tmp)
    assert proc.returncode == 0
    after = doc.read_text(encoding="utf-8")
    assert after == "# Some Doc\n\nBody text describing a capability.\n\nFinal prose line.\n", (
        "apply mode must strip exactly the envelope tail and ensure trailing \\n"
    )
    assert "</content>" not in after
    assert '<parameter name="filePath"' not in after


def test_clean_repo_exits_zero_all_modes(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_clean")
    _make_doc(tmp, "clean.md", CLEAN_DOC)

    for mode in (None, "--dry-run", "--check"):
        proc = _run(mode, tmp)
        assert proc.returncode == 0, f"clean tree must exit 0 in {mode or 'apply'} mode"


def test_multi_marker_file_is_review_not_fixable(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_review")
    doc = _make_doc(
        tmp,
        "multi.md",
        "# Doc\n\nline one</content>\n"
        '<parameter name="filePath">/a\nmore text</content>\n'
        '<parameter name="filePath">/b\n',
    )
    before = doc.read_text(encoding="utf-8")

    proc = _run("--check", tmp)
    assert proc.returncode == 1
    assert "REVIEW" in proc.stdout, "multi-marker file must land in review class"
    assert doc.read_text(encoding="utf-8") == before, "review files are never written"


def test_mid_document_self_referential_fragment_is_fixable(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_middoc")
    doc = _make_doc(
        tmp,
        "MID_DOC.md",
        "# First half\n\nProse ending.</content>\n"
        '<parameter name="filePath">/Users/x/Projects/repo/MID_DOC.md\n\n'
        "### Second half\n\nAppended later.\n",
    )
    proc = _run("--dry-run", tmp)
    assert "WOULD FIX" in proc.stdout, "self-referential mid-doc fragment must classify fixable"
    proc = _run(None, tmp)
    assert proc.returncode == 0
    after = doc.read_text(encoding="utf-8")
    assert after == (
        "# First half\n\nProse ending.\n\n### Second half\n\nAppended later.\n"
    ), "splice must preserve both halves, joined by exactly one blank line"


def test_mid_document_foreign_path_stays_review(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_foreign")
    doc = _make_doc(
        tmp,
        "MID_DOC.md",
        "# First half\n\nProse ending.</content>\n"
        '<parameter name="filePath">/Users/x/Projects/repo/OTHER_FILE.md\n\n'
        "### Second half\n\nAppended later.\n",
    )
    before = doc.read_text(encoding="utf-8")
    proc = _run("--check", tmp)
    assert proc.returncode == 1
    assert "REVIEW" in proc.stdout, "non-self-referential fragment must stay review-class"
    assert doc.read_text(encoding="utf-8") == before


def test_indented_eof_tail_is_fixable(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_indent")
    _make_doc(
        tmp,
        "INDENTED.md",
        "# Some Doc\n\nBody text.</content>\n"
        '  <parameter name="filePath">/Users/x/INDENTED.md\n',
    )
    proc = _run("--dry-run", tmp)
    assert "WOULD FIX" in proc.stdout, "indented EOF tail (sibling-corpus shape) must be fixable"


def test_stale_directory_self_reference_still_fixable(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_stale")
    # File lives in tmp now; envelope path names an old directory, but the
    # same basename — moved-after-defect, as seen in LFK's archive corpus.
    _make_doc(
        tmp,
        "MOVED.md",
        "# Doc\n\nProse.</content>\n"
        '<parameter name="filePath">/Users/x/Projects/old_dir/MOVED.md\n\n'
        "## Later section\n\nContent.\n",
    )
    proc = _run("--dry-run", tmp)
    assert "WOULD FIX" in proc.stdout, "stale-directory self-reference must stay fixable"


def test_escaped_self_reference_is_fixable(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("envelope_escaped")
    # LFK corpus escaping: ** corruption for __, backslash-escaped
    # underscores, and a stale directory — same basename though.
    _make_doc(
        tmp,
        "ui__src__frontend__src__pages__Login.tsx.md",
        "# Doc\n\nProse.</content>\n"
        '<parameter name="filePath">/Users/x/docs/audit/ui**src**frontend**src**pages\\_\\_Login.tsx.md\n\n'
        "## Later\n\nContent.\n",
    )
    proc = _run("--dry-run", tmp)
    assert "WOULD FIX" in proc.stdout, "escaped/corrupted self-reference must stay fixable"
