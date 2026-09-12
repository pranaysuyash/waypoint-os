"""E-08 adversarial-input gate lane — property-based grading, live by default.

Grades the promoted adversarial corpus records
(``data/fixtures/adversarial/adversarial_golden.json``, promoted from the E-11
seed corpus per ``Docs/exploration/E11_ADVERSARIAL_CORPUS_DESIGN_2026-09-02.md``
section 4.3 and the E-08 task in the master findings inventory) through the
real in-process intake pipeline and evaluates the property contract directly:

* every record: ``must_not_crash`` — no exception may escape
  ``ExtractionPipeline.extract`` / ``validate_packet`` (graceful degradation
  is the contract for hostile input);
* ``must_extract`` — extracted values must be within the acceptable set
  (list-typed fields must also be non-empty, i.e. the value was not lost);
* ``must_not_extract`` — banned values must never appear;
* ``must_not_extract_confidence`` — banned status values must never be claimed;
* ``must_flag`` — the named validation warning codes must fire;
* ``graceful_unknowns_required`` — the run must end in unknowns and/or
  warnings, never a fully confident extraction;
* ``latency_bound_seconds`` — probe latency must stay under the bound.

Exact-field matching is deliberately NOT used (design doc section 4.2): for
hostile inputs the pipeline's contract is degradation safety, and exact-field
expectations would be brittle against legitimate extractor improvements.

The probe is read-only by construction: it never touches the database, never
calls the geography persistence hook (``record_seen_city``), and never starts
a server.  All expectations were generated from actual in-process runs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope
    from src.intake.validation import validate_packet

    _HAS_INTAKE_PIPELINE = True
except ImportError:  # pragma: no cover — CI without full intake deps
    _HAS_INTAKE_PIPELINE = False

DEFAULT_ADVERSARIAL_GOLDEN_PATH = Path(
    "data/fixtures/adversarial/adversarial_golden.json"
)

# Extracted fact fields captured by the probe. Superset of every field
# referenced by any promoted record's expected properties.
_PROBE_FIELDS: tuple[str, ...] = (
    "destination_candidates",
    "destination_status",
    "destination_country",
    "origin_city",
    "party_size",
    "party_composition",
    "budget_min",
    "budget_max",
    "budget_currency",
    "budget_scope",
    "budget_raw_text",
    "date_window",
    "date_flexibility",
    "trip_duration_days",
    "trip_purpose",
)


# ---------------------------------------------------------------------------
# Fixture model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AdversarialGoldenRecord:
    """One promoted adversarial record with its property contract."""

    fixture_id: str
    taxonomy_class: str
    subcategory: str
    title: str
    input: dict[str, Any]
    expected: dict[str, Any]
    tags: list[str]


def load_adversarial_golden(
    path: Path | str = DEFAULT_ADVERSARIAL_GOLDEN_PATH,
) -> list[AdversarialGoldenRecord]:
    """Load the promoted adversarial gate corpus."""
    raw = json.loads(Path(path).read_text())
    return [
        AdversarialGoldenRecord(
            fixture_id=item["fixture_id"],
            taxonomy_class=item.get("taxonomy_class", "unclassified"),
            subcategory=item.get("subcategory", ""),
            title=item.get("title", ""),
            input=item["input"],
            expected=item["expected"],
            tags=item.get("tags", []),
        )
        for item in raw["records"]
    ]


# ---------------------------------------------------------------------------
# Probe (canonical in-process method, shared with the E-11 design doc
# Appendix A and tests/test_adversarial_corpus.py)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AdversarialProbeResult:
    """Fresh in-process pipeline result for one adversarial record."""

    crashed: bool
    error: str | None
    facts: dict[str, Any]
    unknown_fields: frozenset[str]
    warning_codes: frozenset[str]
    latency_seconds: float


def _fact_value(packet: Any, field_name: str) -> Any:
    slot = packet.facts.get(field_name)
    if slot is None:
        return None
    return getattr(slot, "value", None)


def run_adversarial_probe(record: AdversarialGoldenRecord) -> AdversarialProbeResult:
    """Run the canonical in-process probe (E-11 design doc Appendix A)."""
    if not _HAS_INTAKE_PIPELINE:  # pragma: no cover
        raise RuntimeError("intake pipeline not importable")
    payload = record.input
    if payload["content_type"] == "structured_json":
        envelope = SourceEnvelope.from_structured(payload["structured"])
    else:
        envelope = SourceEnvelope.from_freeform(payload["text"])

    started = time.monotonic()
    error: str | None = None
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
        return AdversarialProbeResult(
            crashed=True,
            error=error,
            facts={},
            unknown_fields=frozenset(),
            warning_codes=frozenset(),
            latency_seconds=latency,
        )

    facts = {name: _fact_value(packet, name) for name in _PROBE_FIELDS}
    unknown_fields = frozenset(u.field_name for u in packet.unknowns)
    warning_codes = frozenset(w.code for w in (report.warnings if report else []))
    return AdversarialProbeResult(
        crashed=False,
        error=None,
        facts=facts,
        unknown_fields=unknown_fields,
        warning_codes=warning_codes,
        latency_seconds=latency,
    )


# Records are static fixture content, so one probe per record per process is
# sufficient (the snapshot builds the grade report more than once per
# verify run — write, then compare).
_PROBE_CACHE: dict[str, AdversarialProbeResult] = {}


def run_adversarial_probe_cached(
    record: AdversarialGoldenRecord,
) -> AdversarialProbeResult:
    cached = _PROBE_CACHE.get(record.fixture_id)
    if cached is None:
        cached = run_adversarial_probe(record)
        _PROBE_CACHE[record.fixture_id] = cached
    return cached


# ---------------------------------------------------------------------------
# Property grading (E-11 design doc section 4.4 grader sketch)
# ---------------------------------------------------------------------------


def grade_adversarial_record(
    record: AdversarialGoldenRecord,
    probe: AdversarialProbeResult,
) -> list[str]:
    """Evaluate the record's property contract; returns a list of violations.

    An empty list means the record passes: no crash and every present
    expected property held.
    """
    violations: list[str] = []
    rid = record.fixture_id
    expected = record.expected

    if expected.get("must_not_crash", True) and probe.crashed:
        violations.append(f"{rid}: pipeline crashed — {probe.error}")
        return violations  # crash invalidates all other observations

    for field_name, acceptable in (expected.get("must_extract") or {}).items():
        actual = probe.facts.get(field_name)
        if actual is None:
            violations.append(f"{rid}: must_extract '{field_name}' but nothing was extracted")
            continue
        if isinstance(actual, list):
            if not actual:
                violations.append(
                    f"{rid}: must_extract '{field_name}' but candidates list is empty"
                )
                continue
            unexpected = [v for v in actual if v not in acceptable]
            if unexpected:
                violations.append(
                    f"{rid}: '{field_name}' contains values outside the acceptable "
                    f"set {acceptable!r}: {unexpected!r}"
                )
        elif isinstance(acceptable, list):
            if actual not in acceptable:
                violations.append(
                    f"{rid}: '{field_name}' = {actual!r} not in acceptable {acceptable!r}"
                )
        elif actual != acceptable:
            violations.append(
                f"{rid}: '{field_name}' = {actual!r}, expected {acceptable!r}"
            )

    for field_name, banned in (expected.get("must_not_extract") or {}).items():
        actual = probe.facts.get(field_name)
        if actual is None:
            continue
        if isinstance(actual, list):
            leaked = [v for v in actual if v in banned]
            if leaked:
                violations.append(
                    f"{rid}: banned values {banned!r} leaked into '{field_name}': {leaked!r}"
                )
        elif actual in banned:
            violations.append(
                f"{rid}: banned value extracted for '{field_name}': {actual!r} in {banned!r}"
            )

    for field_name, banned_statuses in (
        expected.get("must_not_extract_confidence") or {}
    ).items():
        actual = probe.facts.get(field_name)
        if actual in banned_statuses:
            violations.append(
                f"{rid}: '{field_name}' claimed banned status {actual!r} "
                f"(banned: {banned_statuses!r})"
            )

    for flag in expected.get("must_flag") or []:
        if flag not in probe.warning_codes:
            violations.append(
                f"{rid}: expected warning/flag '{flag}' did not fire "
                f"(got {sorted(probe.warning_codes)!r})"
            )

    if expected.get("graceful_unknowns_required"):
        if not probe.unknown_fields and not probe.warning_codes:
            violations.append(
                f"{rid}: graceful_unknowns_required — pipeline must end in "
                f"unknowns and/or warnings, not a fully confident extraction"
            )

    bound = expected.get("latency_bound_seconds")
    if bound is not None and probe.latency_seconds >= bound:
        violations.append(
            f"{rid}: latency {probe.latency_seconds:.2f}s exceeded bound of {bound}s"
        )

    return violations


# ---------------------------------------------------------------------------
# Eval report
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class AdversarialRecordGrade:
    """Grading outcome for one record."""

    record: AdversarialGoldenRecord
    violations: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


@dataclass(slots=True)
class AdversarialEvalReport:
    """Aggregate property-grading report for the adversarial gate lane."""

    grades: list[AdversarialRecordGrade] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        total = len(self.grades)
        passing = sum(1 for g in self.grades if g.passed)
        # must_not_crash is universal and crash-freedom is folded into the
        # fixture verdict, so it is excluded from the per-property count.
        properties_checked = sum(
            1
            for g in self.grades
            for key in g.record.expected
            if key != "must_not_crash"
        )
        by_class: dict[str, dict[str, Any]] = {}
        for g in self.grades:
            bucket = by_class.setdefault(
                g.record.taxonomy_class, {"total_fixtures": 0, "fixtures_passing": 0}
            )
            bucket["total_fixtures"] += 1
            if g.passed:
                bucket["fixtures_passing"] += 1
        for bucket in by_class.values():
            bucket["fixture_accuracy"] = (
                bucket["fixtures_passing"] / bucket["total_fixtures"]
                if bucket["total_fixtures"]
                else 0.0
            )
        fixture_accuracy = passing / total if total else 0.0
        return {
            "total_fixtures": total,
            "fixtures_passing": passing,
            "fixtures_failing": total - passing,
            "fixture_accuracy": round(fixture_accuracy, 4),
            "total_properties_checked": properties_checked,
            "properties_violated": sum(len(g.violations) for g in self.grades),
            "property_accuracy": (
                round(1.0 - sum(len(g.violations) for g in self.grades) / properties_checked, 4)
                if properties_checked
                else 0.0
            ),
            "by_taxonomy_class": by_class,
        }


def run_adversarial_eval(
    records: list[AdversarialGoldenRecord],
    *,
    saved_violations: dict[str, list[str]] | None = None,
) -> AdversarialEvalReport:
    """Grade each record's property contract against a fresh pipeline probe.

    ``saved_violations`` (fixture_id -> violation list) supplies pre-computed
    grades — the degraded-run simulation path used by the snapshot builder,
    mirroring how the other lanes accept explicit live results.  When it is
    ``None`` the real in-process pipeline is probed (the default, live path).
    """
    grades: list[AdversarialRecordGrade] = []
    for record in records:
        if saved_violations is not None:
            violations = list(saved_violations.get(record.fixture_id, []))
        else:
            probe = run_adversarial_probe_cached(record)
            violations = grade_adversarial_record(record, probe)
        grades.append(AdversarialRecordGrade(record=record, violations=violations))
    return AdversarialEvalReport(grades=grades)
