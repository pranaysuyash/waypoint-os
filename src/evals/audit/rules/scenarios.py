"""Gap/decision scenario eval — the 30-scenario NB02 corpus as a D6 gate lane.

The corpus lives in ``data/fixtures/test_scenarios.py`` (``TestScenarios``)
with expected outcomes in ``TestScenarios.get_expected_results()``.  It
encodes five failure-mode families (basic flows, contradiction handling,
authority precedence, stage progression, edge cases + hybrids) as
hand-built packets, and is the repo's best failure-mode taxonomy
(``data/fixtures/TEST_PHILOSOPHY.md``).  Until this module existed the
corpus was wired into nothing (EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT
2026-08-31 §1.2) — this lane makes it grade the real decision engine.

Grading is fully live and deterministic: every scenario packet is run
through ``src.intake.decision.run_gap_and_decision`` and the resulting
``DecisionResult`` is compared against the corpus expectations on three
axes:

- ``decision_state`` — exact enum match.
- ``hard_blockers`` — exact blocker count match (when the expectation
  specifies one).
- ``contradictions`` — the packet-authored contradictions must survive
  into the decision result (when the expectation flags them).

The composite ``fixture_accuracy`` is the fraction of scenarios matching
on every applicable axis; ``decision_state_accuracy`` and
``hard_blocker_accuracy`` are reported separately so a single regression
can be localised without re-running the suite.

Fixture conversion
------------------
The corpus defines its own minimal dataclasses (EvidenceRef/Slot/
UnknownField/CanonicalPacket) pre-dating ``src/intake/packet_models``.
Loaders convert them into the real packet models so the decision engine
runs against production types.  Local evidence refs are preserved — the
contradiction/ambiguity classifiers read evidence spans.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

DEFAULT_SCENARIO_FIXTURES_PATH = Path("data/fixtures/test_scenarios.py")

try:  # pragma: no cover - exercised implicitly by import success/failure
    from src.intake.packet_models import (
        CanonicalPacket,
        EvidenceRef,
        Slot,
        UnknownField,
    )
    from src.intake.decision import run_gap_and_decision

    _HAS_DECISION_ENGINE = True
except ImportError:  # pragma: no cover - CI without full intake deps
    _HAS_DECISION_ENGINE = False


@dataclass(slots=True)
class ScenarioFixture:
    """One corpus scenario: id, converted packet, and expected outcomes."""

    fixture_id: str
    packet: Any  # src.intake.packet_models.CanonicalPacket
    expected_decision_state: str | None
    expected_hard_blockers: int | None
    expected_contradictions: bool


@dataclass(slots=True)
class ScenarioResult:
    """Outcome of running one scenario through the decision engine."""

    fixture_id: str
    expected_decision_state: str | None
    actual_decision_state: str | None
    expected_hard_blockers: int | None
    actual_hard_blockers: int
    expected_contradictions: bool
    actual_contradictions: bool
    decision_state_match: bool
    hard_blocker_match: bool
    contradiction_match: bool
    error: str | None = None

    @property
    def all_match(self) -> bool:
        if self.error is not None:
            return False
        return (
            self.decision_state_match
            and self.hard_blocker_match
            and self.contradiction_match
        )


@dataclass(slots=True)
class ScenarioEvalReport:
    """Aggregate metrics for the scenario lane."""

    total_fixtures: int = 0
    results: list[ScenarioResult] = field(default_factory=list)
    decision_state_accuracy: float = 0.0
    hard_blocker_accuracy: float = 0.0
    contradiction_accuracy: float = 0.0
    fixture_accuracy: float = 0.0

    def summary(self) -> dict[str, Any]:
        return {
            "total_fixtures": self.total_fixtures,
            "decision_state_accuracy": round(self.decision_state_accuracy, 4),
            "hard_blocker_accuracy": round(self.hard_blocker_accuracy, 4),
            "contradiction_accuracy": round(self.contradiction_accuracy, 4),
            "fixture_accuracy": round(self.fixture_accuracy, 4),
            "fixtures_passing": sum(1 for r in self.results if r.all_match),
            "fixtures_failing": sum(1 for r in self.results if not r.all_match),
            "failing_fixture_ids": [
                r.fixture_id for r in self.results if not r.all_match
            ],
        }


def _load_corpus_module(path: Path) -> Any:
    """Execute the corpus module from its file path.

    The corpus file predates the src/ package layout and self-registers a
    sys.path entry on import; loading via importlib keeps that contained
    to the module's own execution rather than import-time coupling.
    """
    spec = importlib.util.spec_from_file_location("d6_fixture_test_scenarios", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load scenario corpus from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _convert_evidence(evidence: Any) -> Any:
    return EvidenceRef(
        envelope_id=evidence.envelope_id,
        evidence_type=evidence.evidence_type,
        excerpt=evidence.excerpt,
        ref_id=evidence.ref_id,
        field_path=getattr(evidence, "field_path", None),
        confidence=getattr(evidence, "confidence", 1.0),
    )


def _convert_slot(slot: Any) -> Any:
    return Slot(
        value=slot.value,
        confidence=slot.confidence,
        authority_level=slot.authority_level,
        extraction_mode=getattr(slot, "extraction_mode", "unknown"),
        evidence_refs=[
            _convert_evidence(e) for e in (getattr(slot, "evidence_refs", None) or [])
        ],
        updated_at=getattr(slot, "updated_at", ""),
    )


def _convert_packet(packet: Any) -> Any:
    converted = CanonicalPacket(
        packet_id=packet.packet_id,
        stage=packet.stage,
    )
    converted.facts = {
        name: _convert_slot(slot) for name, slot in packet.facts.items()
    }
    converted.derived_signals = {
        name: _convert_slot(slot) for name, slot in packet.derived_signals.items()
    }
    converted.hypotheses = {
        name: _convert_slot(slot) for name, slot in packet.hypotheses.items()
    }
    converted.unknowns = [
        UnknownField(field_name=u.field_name, reason="not_present_in_source")
        for u in packet.unknowns
    ]
    converted.contradictions = [dict(c) for c in packet.contradictions]
    converted.source_envelope_ids = list(packet.source_envelope_ids)
    return converted


def load_scenario_fixtures(
    path: Path = DEFAULT_SCENARIO_FIXTURES_PATH,
) -> list[ScenarioFixture]:
    """Load the scenario corpus and convert packets to production models."""
    module = _load_corpus_module(path)
    scenarios = module.TestScenarios.get_all()
    expected = module.TestScenarios.get_expected_results()
    fixtures: list[ScenarioFixture] = []
    for name, raw_packet in scenarios.items():
        exp = expected.get(name, {})
        fixtures.append(
            ScenarioFixture(
                fixture_id=name,
                packet=_convert_packet(raw_packet),
                expected_decision_state=exp.get("decision_state"),
                expected_hard_blockers=exp.get("hard_blockers"),
                expected_contradictions=bool(exp.get("has_contradictions")),
            )
        )
    return fixtures


def run_scenario_eval(
    fixtures: list[ScenarioFixture],
    decision_fn: Callable[[Any], Any] | None = None,
) -> ScenarioEvalReport:
    """Run every scenario packet through the decision engine and grade it."""
    if decision_fn is None:
        decision_fn = run_gap_and_decision

    results: list[ScenarioResult] = []
    for fixture in fixtures:
        if not _HAS_DECISION_ENGINE or decision_fn is None:
            results.append(
                ScenarioResult(
                    fixture_id=fixture.fixture_id,
                    expected_decision_state=fixture.expected_decision_state,
                    actual_decision_state=None,
                    expected_hard_blockers=fixture.expected_hard_blockers,
                    actual_hard_blockers=0,
                    expected_contradictions=fixture.expected_contradictions,
                    actual_contradictions=False,
                    decision_state_match=False,
                    hard_blocker_match=False,
                    contradiction_match=not fixture.expected_contradictions,
                    error="decision_engine_unavailable",
                )
            )
            continue
        try:
            decision = decision_fn(fixture.packet)
            actual_state = str(decision.decision_state)
            actual_blockers = len(decision.hard_blockers)
            actual_contradictions = len(decision.contradictions) > 0
            error = None
        except Exception as exc:  # noqa: BLE001 — one broken scenario must not kill the lane
            actual_state, actual_blockers, actual_contradictions = None, 0, False
            error = f"{type(exc).__name__}: {exc}"
        state_match = (
            error is None
            and fixture.expected_decision_state is not None
            and actual_state == fixture.expected_decision_state
        )
        # Expectations may omit the hard_blocker axis entirely — when absent
        # it cannot fail (the axis is simply not graded for the scenario).
        blocker_match = error is None and (
            fixture.expected_hard_blockers is None
            or actual_blockers == fixture.expected_hard_blockers
        )
        contradiction_match = (
            error is None
            and fixture.expected_contradictions == actual_contradictions
        )
        results.append(
            ScenarioResult(
                fixture_id=fixture.fixture_id,
                expected_decision_state=fixture.expected_decision_state,
                actual_decision_state=actual_state,
                expected_hard_blockers=fixture.expected_hard_blockers,
                actual_hard_blockers=actual_blockers,
                expected_contradictions=fixture.expected_contradictions,
                actual_contradictions=actual_contradictions,
                decision_state_match=state_match,
                hard_blocker_match=blocker_match,
                contradiction_match=contradiction_match,
                error=error,
            )
        )

    total = len(results)
    state_hits = sum(1 for r in results if r.decision_state_match)
    blocker_hits = sum(
        1
        for r in results
        if r.expected_hard_blockers is not None and r.hard_blocker_match
    )
    blocker_total = sum(1 for r in results if r.expected_hard_blockers is not None)
    contradiction_hits = sum(1 for r in results if r.contradiction_match)
    composite = sum(1 for r in results if r.all_match)

    def _ratio(num: int, denom: int) -> float:
        return num / denom if denom > 0 else 0.0

    return ScenarioEvalReport(
        total_fixtures=total,
        results=results,
        decision_state_accuracy=_ratio(state_hits, total),
        hard_blocker_accuracy=_ratio(blocker_hits, blocker_total),
        contradiction_accuracy=_ratio(contradiction_hits, total),
        fixture_accuracy=_ratio(composite, total),
    )
