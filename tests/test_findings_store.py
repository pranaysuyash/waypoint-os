"""
tests/test_findings_store.py — store mechanics for scripts/findings.py.

Covers: ID minting, projection of opened/imported events, fail-closed
validation (no-evidence close, unknown ID, bad disposition), alias
resolution, staleness gate, render, and migration dedupe rules.
Every test uses an isolated store via FINDINGS_STORE_PATH + tmp_path.
"""

from __future__ import annotations

import json

import pytest

from scripts import findings as findings_mod


@pytest.fixture()
def store_path(tmp_path, monkeypatch):
    path = tmp_path / "FINDINGS_STORE.jsonl"
    monkeypatch.setenv("FINDINGS_STORE_PATH", str(path))
    return path


def run(store_path, *argv):
    return findings_mod.main(list(argv))


def test_open_mints_monotonic_ids(store_path):
    assert run(store_path, "open", "--title", "One", "--actor", "t") == 0
    assert run(store_path, "open", "--title", "Two", "--actor", "t") == 0
    events = [json.loads(line) for line in store_path.read_text().splitlines()]
    assert [e["finding_id"] for e in events] == ["FND-0001", "FND-0002"]


def test_close_requires_evidence(store_path, capsys):
    run(store_path, "open", "--title", "X", "--actor", "t")
    # main() converts StoreError to exit code 1 + stderr; nothing is written
    assert run(store_path, "close", "FND-0001", "--evidence", "", "--actor", "t") == 1
    assert "evidence" in capsys.readouterr().err
    assert len(store_path.read_text().splitlines()) == 1


def test_close_unknown_id_rejected(store_path, capsys):
    run(store_path, "open", "--title", "X", "--actor", "t")
    assert run(store_path, "close", "FND-9999", "--evidence", "x", "--actor", "t") == 1
    assert "unknown finding" in capsys.readouterr().err


def test_invalid_disposition_rejected(store_path):
    run(store_path, "open", "--title", "X", "--actor", "t")
    # argparse rejects the bad choice before the store layer sees it
    with pytest.raises(SystemExit):
        run(store_path, "close", "FND-0001", "--evidence", "x", "--disposition", "meh", "--actor", "t")


def test_projection_close_and_reopen(store_path):
    run(store_path, "open", "--title", "X", "--actor", "t")
    run(store_path, "close", "FND-0001", "--evidence", "done", "--actor", "t")
    run(store_path, "reopen", "FND-0001", "--reason", "regressed", "--actor", "t")
    findings = findings_mod.project(findings_mod._read_events(store_path))
    state = findings["FND-0001"]
    assert state["status"] == "open"
    assert len(state["history"]) == 3


def test_alias_resolution_via_show(store_path, capsys):
    run(store_path, "import", "--alias", "A-18", "--title", "Legacy secrets", "--status", "open",
        "--source-register", "REG", "--actor", "t")
    capsys.readouterr()  # discard the import confirmation line
    assert run(store_path, "show", "A-18") == 0
    out = capsys.readouterr().out
    assert json.loads(out)["id"].startswith("FND-")
    assert "A-18" in json.loads(out)["aliases"]


def test_staleness_gate_fails_on_old_open(store_path):
    run(store_path, "import", "--alias", "OLD-1", "--title", "Stale", "--status", "open",
        "--source-register", "REG", "--last-verified", "2020-01-01", "--actor", "t")
    assert run(store_path, "validate") == 1


def test_staleness_gate_passes_fresh(store_path):
    run(store_path, "import", "--alias", "NEW-1", "--title", "Fresh", "--status", "open",
        "--source-register", "REG", "--actor", "t")
    assert run(store_path, "validate") == 0


def test_render_writes_generated_view(store_path, tmp_path):
    run(store_path, "open", "--title", "Rendered", "--actor", "t")
    out = tmp_path / "LIVE.md"
    assert run(store_path, "render", "--output", str(out)) == 0
    content = out.read_text()
    assert "GENERATED — DO NOT EDIT" in content
    assert "FND-0001" in content


def test_migrate_skips_terminal_duplicate_but_keeps_open(tmp_path, store_path):
    reg = tmp_path / "REG.md"
    reg.write_text(
        "# Register (2020-01-01)\n\n"
        "| ID | Type | Task | Pri |\n|----|------|------|-----|\n"
        "| Z-01 | I | Terminal duplicate task description here | P2 |\n"
        "| Z-02 | I | Open task that must not be lost whatsoever | P1 |\n"
    )
    run(store_path, "import", "--alias", "Z-01", "--title", "Original Z-01 closed", "--status", "closed",
        "--source-register", "OTHER", "--actor", "t")
    assert run(store_path, "migrate-registers", str(reg), "--tag", "reg") == 0
    findings = findings_mod.project(findings_mod._read_events(store_path))
    by_alias = {a: f for f in findings.values() for a in f["aliases"]}
    # terminal duplicate skipped: Z-01 resolves to the original closed finding
    assert by_alias["Z-01"]["title"] == "Original Z-01 closed"
    # open row imported (suffixed on collision or plain — both fine), never dropped
    z2 = [f for f in findings.values() if "Z-02" in f["aliases"]]
    assert len(z2) == 1 and z2[0]["status"] == "open"


def test_corrupt_jsonl_fails_validation(store_path, capsys):
    store_path.write_text('{"event_id": 1, broken\n')
    assert run(store_path, "validate") == 1
    assert "corrupt JSONL" in capsys.readouterr().err
