"""E-08 — Standing adversarial-input regression corpus.

Runs every record in ``data/fixtures/adversarial/adversarial_seed_v1.json``
through the in-process intake pipeline (extraction + validation) with the
exact probe method recorded in the corpus design doc
(``Docs/exploration/E11_ADVERSARIAL_CORPUS_DESIGN_2026-09-02.md`` Appendix A)
and enforces the property contract:

(a) EVERY record: ``must_not_crash`` — no exception may escape
    ``ExtractionPipeline.extract`` / ``validate_packet``. The pipeline's
    contract for hostile input is graceful degradation, never a crash.
(b) ``status == "passes_today"`` records: every present ``expected`` property
    (``must_extract`` / ``must_not_extract`` / ``must_not_extract_confidence``
    / ``must_flag`` / ``graceful_unknowns_required`` / ``latency_bound_seconds``)
    must hold against a fresh run. Per the design doc §4.4, gating records are
    checked by property directly; the per-record ``observed`` block is probe-
    time provenance (pre-fix history on ``fixed_in`` records) consumed by the
    nightly fresh-probe diff, not a CI gate.
(c) ``status == "known_defect"`` records: only ``must_not_crash`` is asserted
    here. Wrong-extraction properties on these records are tracked defects
    (each carries ``defect.root_cause`` + ``defect.cite`` in the corpus);
    asserting them here would fail by design. When a defect is fixed, flip the
    record to ``passes_today`` (with a ``fixed_in`` note) and its full
    property set starts being enforced automatically.

Read-only by construction: the probe path never touches the database, never
calls the geography persistence hook (``record_seen_city``), and never starts
a server. Corpus records are append-only; never renumber or delete ids.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from src.intake.extractors import ExtractionPipeline
from src.intake.packet_models import SourceEnvelope
from src.intake.validation import validate_packet

CORPUS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "fixtures"
    / "adversarial"
    / "adversarial_seed_v1.json"
)

# Extracted fact fields captured by the probe. This is a superset of every
# field referenced by the corpus `expected` blocks (must_extract,
# must_not_extract, must_not_extract_confidence) plus the commonly-observed
# extraction fields.
_PROBE_FIELDS = (
    "destination_candidates",
    "destination_status",
    "origin_city",
    "party_size",
    "budget_min",
    "budget_max",
    "budget_currency",
    "budget_raw_text",
    "budget_scope",
    "date_window",
    "date_flexibility",
    "trip_purpose",
)


def _load_corpus() -> Dict[str, Any]:
    with open(CORPUS_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


_CORPUS = _load_corpus()
_RECORDS: List[Dict[str, Any]] = _CORPUS["records"]


@dataclass(slots=True)
class _ProbeResult:
    """Fresh in-process pipeline result for one corpus record."""

    crashed: bool
    error: Optional[str]
    facts: Dict[str, Any]  # field -> raw extracted value (None if absent)
    unknown_fields: set
    warning_codes: set
    latency_seconds: float


def _fact_value(packet: Any, field: str) -> Any:
    slot = packet.facts.get(field)
    if slot is None:
        return None
    return getattr(slot, "value", None)


def _probe(record: Dict[str, Any]) -> _ProbeResult:
    """Run the canonical in-process probe (design doc Appendix A)."""
    payload = record["input"]
    if payload["content_type"] == "structured_json":
        envelope = SourceEnvelope.from_structured(payload["structured"])
    else:
        envelope = SourceEnvelope.from_freeform(payload["text"])

    started = time.monotonic()
    error: Optional[str] = None
    packet = None
    report = None
    try:
        pipeline = ExtractionPipeline()
        packet = pipeline.extract([envelope], stage="discovery")
        report = validate_packet(packet, stage="discovery")
    except Exception as exc:  # noqa: BLE001 — crash capture IS the contract
        error = f"{type(exc).__name__}: {exc}"
    latency = time.monotonic() - started

    if packet is None:
        return _ProbeResult(
            crashed=True,
            error=error,
            facts={},
            unknown_fields=set(),
            warning_codes=set(),
            latency_seconds=latency,
        )

    facts = {field: _fact_value(packet, field) for field in _PROBE_FIELDS}
    unknown_fields = {u.field_name for u in packet.unknowns}
    warning_codes = {w.code for w in (report.warnings if report else [])}
    return _ProbeResult(
        crashed=False,
        error=None,
        facts=facts,
        unknown_fields=unknown_fields,
        warning_codes=warning_codes,
        latency_seconds=latency,
    )


# ---------------------------------------------------------------------------
# Property evaluators (mirror the §4.4 grader sketch; property, not exact
# field, matching — hostile-input contract is graceful degradation).
# ---------------------------------------------------------------------------


def _check_must_extract(record_id: str, field: str, acceptable: Any, probe: _ProbeResult) -> None:
    actual = probe.facts.get(field)
    assert actual is not None, (
        f"{record_id}: must_extract '{field}' but nothing was extracted"
    )
    if isinstance(actual, list):
        # List-typed fields (e.g. destination_candidates): every extracted
        # element must be one of the acceptable correct values, and the list
        # must be non-empty (empty would mean the value was lost).
        assert actual, f"{record_id}: must_extract '{field}' but candidates list is empty"
        unexpected = [v for v in actual if v not in acceptable]
        assert not unexpected, (
            f"{record_id}: '{field}' contains values outside the acceptable "
            f"set {acceptable!r}: {unexpected!r}"
        )
    elif isinstance(acceptable, list):
        # Scalar field with a list of acceptable values (e.g. budget_min
        # may legitimately be either of two parsed amounts).
        assert actual in acceptable, (
            f"{record_id}: '{field}' = {actual!r} not in acceptable {acceptable!r}"
        )
    else:
        assert actual == acceptable, (
            f"{record_id}: '{field}' = {actual!r}, expected {acceptable!r}"
        )


def _check_must_not_extract(record_id: str, field: str, banned: List[Any], probe: _ProbeResult) -> None:
    actual = probe.facts.get(field)
    if actual is None:
        return
    if isinstance(actual, list):
        leaked = [v for v in actual if v in banned]
        assert not leaked, (
            f"{record_id}: banned values {banned!r} leaked into '{field}': {leaked!r}"
        )
    else:
        assert actual not in banned, (
            f"{record_id}: banned value extracted for '{field}': {actual!r} in {banned!r}"
        )


def _check_passes_today_properties(record_id: str, record: Dict[str, Any], probe: _ProbeResult) -> None:
    expected = record.get("expected", {})

    for field, acceptable in (expected.get("must_extract") or {}).items():
        _check_must_extract(record_id, field, acceptable, probe)

    for field, banned in (expected.get("must_not_extract") or {}).items():
        _check_must_not_extract(record_id, field, banned, probe)

    for field, banned_statuses in (
        expected.get("must_not_extract_confidence") or {}
    ).items():
        actual = probe.facts.get(field)
        assert actual not in banned_statuses, (
            f"{record_id}: '{field}' claimed banned status {actual!r} "
            f"(banned: {banned_statuses!r})"
        )

    for flag in expected.get("must_flag") or []:
        assert flag in probe.warning_codes, (
            f"{record_id}: expected warning/flag '{flag}' did not fire "
            f"(got {sorted(probe.warning_codes)!r})"
        )

    if expected.get("graceful_unknowns_required"):
        assert probe.unknown_fields or probe.warning_codes, (
            f"{record_id}: graceful_unknowns_required — pipeline must end in "
            f"unknowns and/or warnings, not a fully confident extraction"
        )

    bound = expected.get("latency_bound_seconds")
    if bound is not None:
        assert probe.latency_seconds < bound, (
            f"{record_id}: latency {probe.latency_seconds:.2f}s exceeded "
            f"bound of {bound}s"
        )


# One fresh probe per record per session — both parametrized tests share it
# (the 1MB oversize record alone costs ~2s per run).
_PROBE_CACHE: Dict[str, _ProbeResult] = {}


def _probe_cached(record: Dict[str, Any]) -> _ProbeResult:
    cached = _PROBE_CACHE.get(record["id"])
    if cached is None:
        cached = _probe(record)
        _PROBE_CACHE[record["id"]] = cached
    return cached


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("record", _RECORDS, ids=lambda r: r["id"])
def test_must_not_crash(record):
    """(a) Every record, both lanes: the pipeline must survive the input."""
    probe = _probe_cached(record)
    assert not probe.crashed, (
        f"{record['id']}: pipeline crashed on hostile input — {probe.error}"
    )


@pytest.mark.parametrize("record", _RECORDS, ids=lambda r: r["id"])
def test_passes_today_properties_hold(record):
    """(b) passes_today records: the expected property contract must still
    hold (design doc §4.4: gating records are checked by property directly).
    The per-record `observed` block is probe-time provenance, NOT a CI gate —
    it intentionally records pre-fix behavior on records flipped by a fix
    wave (`fixed_in` markers) and is consumed by the nightly fresh-probe diff
    instead. known_defect records are intentionally excluded here — their
    wrong-extraction properties are tracked defects; the crash-freedom
    contract for them is enforced by test_must_not_crash."""
    if record["status"] != "passes_today":
        pytest.skip(f"{record['id']} is a known_defect record (tracked, shadow lane)")
    probe = _probe_cached(record)
    assert not probe.crashed, (
        f"{record['id']}: pipeline crashed — {probe.error}"
    )
    _check_passes_today_properties(record["id"], record, probe)


def test_corpus_self_consistent():
    """The corpus file itself must stay internally consistent: summary block
    matches the records, every known_defect carries a defect citation, and
    ids are unique (append-only by id — never renumber)."""
    ids = [r["id"] for r in _RECORDS]
    assert len(ids) == len(set(ids)), "duplicate corpus record ids"

    summary = _CORPUS["summary"]
    n_pass = sum(1 for r in _RECORDS if r["status"] == "passes_today")
    n_defect = sum(1 for r in _RECORDS if r["status"] == "known_defect")
    assert summary["total"] == len(_RECORDS)
    assert summary["passes_today"] == n_pass
    assert summary["known_defect"] == n_defect

    for record in _RECORDS:
        assert record["expected"]["must_not_crash"] is True, record["id"]
        if record["status"] == "known_defect":
            defect = record.get("defect") or {}
            assert defect.get("root_cause"), (
                f"{record['id']}: known_defect requires defect.root_cause"
            )
            assert defect.get("cite"), (
                f"{record['id']}: known_defect requires defect.cite (file:line)"
            )


# ---------------------------------------------------------------------------
# E-08 — D6 gate fixture (adversarial_golden.json) contract
# ---------------------------------------------------------------------------

GOLDEN_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "fixtures"
    / "adversarial"
    / "adversarial_golden.json"
)


def _load_golden() -> Dict[str, Any]:
    with open(GOLDEN_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_gate_fixture_parses_and_count_matches_manifest_expectation():
    """E-08: the D6 gate fixture file must parse, its record count must match
    its own declared expectation and the promotable seed population, and the
    manifest must carry the matching gating category."""
    from src.evals.audit.manifest import load_manifest

    assert GOLDEN_PATH.exists(), "adversarial_golden.json missing"
    golden = _load_golden()
    records = golden["records"]
    assert records, "adversarial_golden.json carries no records"

    # Unique ids (records are append-only by id; never renumber).
    golden_ids = [r["fixture_id"] for r in records]
    assert len(golden_ids) == len(set(golden_ids)), "duplicate golden fixture ids"

    # Count matches the envelope's own declared expectation AND the seed's
    # promotable population (gating_candidate + passes_today).
    assert golden["expected_record_count"] == len(records)
    promotable = {
        r["id"]
        for r in _RECORDS
        if r.get("lane") == "gating_candidate" and r.get("status") == "passes_today"
    }
    assert set(golden_ids) == promotable, (
        "golden/seed divergence: every gating_candidate record that passes "
        "today must be promoted, and nothing else may be"
    )

    # Per-record schema sanity.
    seed_by_id = {r["id"]: r for r in _RECORDS}
    for rec in records:
        assert rec["fixture_id"] in seed_by_id, rec["fixture_id"]
        assert rec["expected"]["must_not_crash"] is True, rec["fixture_id"]
        # The property contract must be verbatim-faithful to the seed corpus
        # (the gate grades exactly the contract the seed recorded).
        assert rec["expected"] == seed_by_id[rec["fixture_id"]]["expected"], (
            f"{rec['fixture_id']}: golden expected block drifted from seed"
        )
        assert rec["input"] == seed_by_id[rec["fixture_id"]]["input"], (
            f"{rec['fixture_id']}: golden input drifted from seed"
        )

    # Manifest expectation: the adversarial category exists, is gating, and
    # blocks on any regression (regression-ratchet min_accuracy).
    manifest = load_manifest()
    config = manifest.categories["adversarial"]
    assert config.status == "gating"
    assert config.min_accuracy == 1.0


def test_gate_fixture_records_pass_live_property_grading():
    """E-08: every promoted record must pass the shared property grader on a
    fresh in-process probe — the same evaluation the D6 snapshot lane runs.
    This is the direct unit-level check; the snapshot drift check enforces it
    at the artifact level."""
    from src.evals.audit.rules.adversarial import (
        load_adversarial_golden,
        run_adversarial_eval,
    )

    golden_records = load_adversarial_golden(GOLDEN_PATH)
    report = run_adversarial_eval(golden_records)
    summary = report.summary()
    failures = [
        (g.record.fixture_id, g.violations)
        for g in report.grades
        if not g.passed
    ]
    assert not failures, f"adversarial gate regressions: {failures!r}"
    assert summary["fixture_accuracy"] == 1.0
    assert summary["total_fixtures"] == len(golden_records)
