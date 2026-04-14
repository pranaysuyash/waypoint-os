#!/usr/bin/env python3
"""
Reusable E2E scenario runner for intake extraction + decision routing.

Runs scenario sets in repeatable passes:
  - first 5 existing scenarios
  - remaining existing scenarios
  - all existing scenarios
  - new scenarios
  - existing + new scenarios
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from intake.decision import run_gap_and_decision  # noqa: E402
from intake.extractors import ExtractionPipeline  # noqa: E402
from intake.packet_models import (  # noqa: E402
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
    SourceEnvelope,
    SubGroup,
)


PacketMutator = Callable[[CanonicalPacket], None]


@dataclass
class Scenario:
    scenario_id: str
    name: str
    raw_text: str
    stage: str = "discovery"
    source: str = "agency_notes"
    expected_decision: str | None = None
    mutator: PacketMutator | None = None


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    stage: str
    expected_decision: str | None
    decision_state: str
    operating_mode: str
    confidence: float
    hard_blockers: list[str]
    soft_blockers: list[str]
    contradictions: int
    ambiguities: int
    risk_flags: list[str]
    pass_expected: bool | None


def _mk_evidence(label: str) -> list[EvidenceRef]:
    return [EvidenceRef(envelope_id="synthetic", evidence_type="text_span", excerpt=label)]


def _mutate_confused_couple(pkt: CanonicalPacket) -> None:
    pkt.add_contradiction(
        "date_window",
        ["2026-03-15 to 2026-03-20", "2026-04-01 to 2026-04-06"],
        ["env_husband", "env_wife"],
    )
    pkt.add_contradiction(
        "destination_candidates",
        ["Singapore", "Thailand"],
        ["env_husband", "env_wife"],
    )


def _mutate_proposal_partial(pkt: CanonicalPacket) -> None:
    pkt.stage = "proposal"
    pkt.facts["resolved_destination"] = Slot(
        value="Singapore",
        confidence=0.92,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_mk_evidence("Singapore"),
    )
    # selected_itinerary intentionally missing for proposal-stage follow-up


def _mutate_shortlist_progression(pkt: CanonicalPacket) -> None:
    pkt.stage = "shortlist"
    pkt.facts["resolved_destination"] = Slot(
        value="Andaman",
        confidence=0.90,
        authority_level=AuthorityLevel.EXPLICIT_OWNER,
        evidence_refs=_mk_evidence("Andaman selected"),
    )


def _mutate_inferred_destination(pkt: CanonicalPacket) -> None:
    pkt.derived_signals["destination_candidates"] = Slot(
        value=["Singapore"],
        confidence=0.78,
        authority_level=AuthorityLevel.DERIVED_SIGNAL,
        evidence_refs=_mk_evidence("derived from history"),
    )


def _mutate_multi_envelope(pkt: CanonicalPacket) -> None:
    pkt.source_envelope_ids = ["env_1", "env_2", "env_3"]
    pkt.revision_count = 3


def _mutate_booking_ready(pkt: CanonicalPacket) -> None:
    pkt.stage = "booking"
    pkt.facts["resolved_destination"] = Slot(
        value="Singapore",
        confidence=0.95,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_mk_evidence("destination confirmed"),
    )
    pkt.facts["selected_itinerary"] = Slot(
        value="itinerary_A",
        confidence=0.93,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_mk_evidence("itinerary selected"),
    )
    pkt.facts["passport_status"] = Slot(
        value="all_valid",
        confidence=0.95,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_mk_evidence("passports valid"),
    )
    pkt.facts["visa_status"] = Slot(
        value="not_required",
        confidence=0.90,
        authority_level=AuthorityLevel.EXPLICIT_OWNER,
        evidence_refs=_mk_evidence("visa check complete"),
    )
    pkt.facts["payment_method"] = Slot(
        value="card",
        confidence=0.98,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_mk_evidence("payment mode"),
    )


def _mutate_budget_branch(pkt: CanonicalPacket) -> None:
    pkt.add_contradiction(
        "budget_range",
        ["120000", "220000"],
        ["env_agent_note", "env_whatsapp"],
    )


def _mutate_coordinator(pkt: CanonicalPacket) -> None:
    pkt.sub_groups = [
        SubGroup(group_id="A", label="Family A", size=4, composition={"adults": 2, "children": 2}),
        SubGroup(group_id="B", label="Family B", size=3, composition={"adults": 2, "children": 1}),
    ]


EXISTING_SCENARIOS: list[Scenario] = [
    Scenario(
        "S01",
        "Vague Lead",
        "Caller wants an international family trip maybe around March, budget is fine, will call back.",
        expected_decision="ASK_FOLLOWUP",
    ),
    Scenario(
        "S02",
        "Confused Couple",
        "Husband notes Singapore Mar 15-20. Wife notes Thailand Apr 1-6. 2 adults and maybe baby.",
        expected_decision="STOP_NEEDS_REVIEW",
        mutator=_mutate_confused_couple,
    ),
    Scenario(
        "S03",
        "Dreamer Luxury vs Budget",
        "Family wants overwater villa in Maldives but budget is around 1 lakh total.",
        expected_decision="BRANCH_OPTIONS",
    ),
    Scenario(
        "S04",
        "Ready to Buy",
        "2 adults from Bangalore to Singapore, 2026-05-12 to 2026-05-18, budget 3 lakhs, leisure, vegetarian meals preferred.",
    ),
    Scenario(
        "S05",
        "WhatsApp Dump",
        "Andaman or Sri Lanka maybe, family trip from Bangalore in June, budget around 2.5L maybe can stretch.",
    ),
    Scenario(
        "S06",
        "CRM Return with Fresh Data",
        "Returning lead: 2 adults + 1 child from Bangalore to Dubai, 2026-07-03 to 2026-07-09, budget 2.2L.",
    ),
    Scenario(
        "S07",
        "Elderly Pilgrimage",
        "6 travelers including 2 senior citizens, Bangalore to Varanasi in Aug, budget 1.8L, prefer low walking and wheelchair support.",
    ),
    Scenario(
        "S08",
        "Last-Minute Booker",
        f"Need urgent trip in 4 days from Bangalore to Goa for 2 adults, budget 50K.",
    ),
    Scenario(
        "S09",
        "Stage Progression Shortlist",
        "Customer shortlisted destination and wants option comparison for dates and pricing.",
        stage="shortlist",
        mutator=_mutate_shortlist_progression,
    ),
    Scenario(
        "S10",
        "Partial Proposal",
        "Proposal stage with destination confirmed but final itinerary not selected yet.",
        stage="proposal",
        mutator=_mutate_proposal_partial,
    ),
    Scenario(
        "S11",
        "Budget Stretch Signal",
        "Family of 4 to Singapore, budget around 3L and can stretch if value is strong.",
    ),
    Scenario(
        "S12",
        "Inferred Destination",
        "Family trip from Bangalore in September, budget 2L, destination not explicitly stated.",
        mutator=_mutate_inferred_destination,
    ),
    Scenario(
        "S13",
        "Multi-Envelope Accumulation",
        "Envelope 1: origin + dates. Envelope 2: destination + travelers. Envelope 3: budget + preferences.",
        mutator=_mutate_multi_envelope,
    ),
]


NEW_SCENARIOS: list[Scenario] = [
    Scenario(
        "N01",
        "Emergency Medical Routing",
        "URGENT medical case for elderly traveler in Singapore. Need immediate support and routing.",
    ),
    Scenario(
        "N02",
        "Hard Date Conflict",
        "Customer says both 2026-10-10 and 2026-11-11 as locked dates from different decision makers.",
        mutator=_mutate_confused_couple,
        expected_decision="STOP_NEEDS_REVIEW",
    ),
    Scenario(
        "N03",
        "Booking Stage Fully Ready",
        "Everything confirmed; proceed to booking and payment finalization.",
        stage="booking",
        mutator=_mutate_booking_ready,
    ),
    Scenario(
        "N04",
        "Budget Branching Candidate",
        "Lead provided conflicting budget across channels; needs branch recommendation.",
        mutator=_mutate_budget_branch,
    ),
    Scenario(
        "N05",
        "Coordinator Group Lead",
        "Coordinator handling two family groups for one destination and common travel window.",
        mutator=_mutate_coordinator,
    ),
]


def _build_sets() -> dict[str, list[Scenario]]:
    return {
        "first5": EXISTING_SCENARIOS[:5],
        "rest": EXISTING_SCENARIOS[5:],
        "existing": EXISTING_SCENARIOS,
        "new": NEW_SCENARIOS,
        "existing_plus_new": [*EXISTING_SCENARIOS, *NEW_SCENARIOS],
    }


def run_single_scenario(s: Scenario) -> ScenarioResult:
    envelope = SourceEnvelope.from_freeform(s.raw_text, source=s.source)
    packet = ExtractionPipeline().extract([envelope])
    packet.stage = s.stage
    if s.mutator:
        s.mutator(packet)

    result = run_gap_and_decision(packet)
    pass_expected = None
    if s.expected_decision:
        pass_expected = result.decision_state == s.expected_decision

    return ScenarioResult(
        scenario_id=s.scenario_id,
        name=s.name,
        stage=packet.stage,
        expected_decision=s.expected_decision,
        decision_state=result.decision_state,
        operating_mode=result.operating_mode,
        confidence=round(float(result.confidence_score), 3),
        hard_blockers=list(result.hard_blockers),
        soft_blockers=list(result.soft_blockers),
        contradictions=len(result.contradictions),
        ambiguities=len(result.ambiguities),
        risk_flags=list(result.risk_flags),
        pass_expected=pass_expected,
    )


def _print_results(label: str, results: list[ScenarioResult]) -> None:
    print(f"\n=== {label} ===")
    print(
        "ID   Name                           Stage      Decision                 "
        "Mode              Conf  Ctrd Amb"
    )
    print("-" * 108)
    for r in results:
        print(
            f"{r.scenario_id:<4} "
            f"{r.name[:30]:<30} "
            f"{r.stage:<10} "
            f"{r.decision_state:<24} "
            f"{r.operating_mode:<17} "
            f"{r.confidence:<5} "
            f"{r.contradictions:<4} "
            f"{r.ambiguities:<3}"
        )
    expected_total = sum(1 for r in results if r.pass_expected is not None)
    expected_pass = sum(1 for r in results if r.pass_expected is True)
    if expected_total:
        print(f"\nExpected-decision checks: {expected_pass}/{expected_total} passed")


def _write_markdown(path: Path, label: str, results: list[ScenarioResult]) -> None:
    lines = [
        f"# E2E Scenario Run — {label}",
        "",
        f"- Generated at: {datetime.now().isoformat()}",
        "",
        "| ID | Name | Stage | Decision | Mode | Confidence | Hard Blockers | Soft Blockers | Contradictions | Ambiguities |",
        "|---|---|---|---|---|---:|---|---|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r.scenario_id} | {r.name} | {r.stage} | {r.decision_state} | "
            f"{r.operating_mode} | {r.confidence} | "
            f"{', '.join(r.hard_blockers) or '-'} | "
            f"{', '.join(r.soft_blockers) or '-'} | "
            f"{r.contradictions} | {r.ambiguities} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reusable E2E scenario sets.")
    parser.add_argument(
        "--set",
        dest="scenario_set",
        default="existing",
        choices=["first5", "rest", "existing", "new", "existing_plus_new"],
        help="Scenario set to run",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON output path")
    parser.add_argument("--md-out", type=Path, default=None, help="Optional Markdown output path")
    args = parser.parse_args()

    sets = _build_sets()
    selected = sets[args.scenario_set]
    label = args.scenario_set

    results = [run_single_scenario(s) for s in selected]
    _print_results(label, results)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nWrote JSON: {args.json_out}")

    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown(args.md_out, label, results)
        print(f"Wrote Markdown: {args.md_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
