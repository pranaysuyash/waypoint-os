"""
src/memory/slot_review.py — Shadow-window review for E-D slot 1 (memory
question-promotion), ADR-008 §7 row 4.

Reads `memory_slot_promotion` audit events (emitted once per question-ranking
call in agency-scoped runs, with the full asked set and the promoted subset)
and reports whether the shadow data is ready for the owner's flip decision
(`MEMORY_SLOT_READ_MODE=active`).

Pre-registered criteria (mirrored in
Docs/architecture/MEMORY_SLOT_WIRING_2026-09-15.md — change them there
first, then here):

Sample floor
    >= MIN_ASKS asks recorded. Below that the verdict is INSUFFICIENT_DATA —
    a shadow window with no traffic says nothing.

Guardrails (must all hold; a violation is an UNWIRE/reopen signal, not a flip)
    G1 promotion-only invariant: no promoted field outside the asked set
       (code-enforced; audited here — a violation means the seam regressed).
    G2 trust floor: >= EXPLICIT_SHARE_FLOOR of promotions carry trust_class
       "explicit_user". Derived/agent-inferred memories dominating the ask
       order means the trust gate is not doing its job (FND-0230).
    G3 degeneracy: no single memory (rationale id) drives more than
       MAX_SINGLE_MEMORY_SHARE of promotions — one stale note steering every
       session is the exact shadow-state failure E-D §1 forbids.
    G4 noise bound: promotion rate <= MAX_PROMOTION_RATE. Promoting on every
       ask means the topicality gate is too loose to be informative.

The review NEVER flips the mode. Verdict REVIEW_READY means: criteria hold,
the owner decides. Per-trip answer-correlation ("did the promoted unknown
get answered sooner") lands when trip identity reaches the seam — registered
follow-up in the wiring report; until then rates are per-field aggregates.

CLI (repo root):
    .venv/bin/python -m src.memory.slot_review                  # human summary
    .venv/bin/python -m src.memory.slot_review --json           # machine-readable
    .venv/bin/python -m src.memory.slot_review --agency <id> --since 2026-09-15
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_AUDIT_FILE = Path("data/audit/events.jsonl")
EVENT_TYPE = "memory_slot_promotion"

# Pre-registered thresholds (see module docstring; keep in sync with the
# wiring report).
MIN_ASKS = 30
EXPLICIT_SHARE_FLOOR = 0.80
MAX_SINGLE_MEMORY_SHARE = 0.50
MAX_PROMOTION_RATE = 0.80


def load_events(
    audit_file: Path, agency: Optional[str] = None, since: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Reads promotion events from the JSONL audit log, oldest first."""
    if not audit_file.exists():
        return []
    events: List[Dict[str, Any]] = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("event_type") != EVENT_TYPE:
                continue
            if agency and event.get("user_id") != agency:
                continue
            if since:
                ts = str(event.get("created_at") or event.get("ts") or "")
                if ts and ts < since:
                    continue
            events.append(event)
    return events


def review(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes the shadow-window metrics + verdict. Pure function of events."""
    asks = len(events)
    promoted_asks = 0
    promotions_total = 0
    field_asked: Counter = Counter()
    field_promoted: Counter = Counter()
    trust_classes: Counter = Counter()
    memory_ids: Counter = Counter()
    invariant_violations: List[str] = []
    last_event_at: Optional[str] = None

    for event in events:
        details = event.get("details") or {}
        asked = details.get("asked") or []
        promoted = details.get("promoted") or []
        for name in asked:
            field_asked[name] += 1
        if promoted:
            promoted_asks += 1
        for promo in promoted:
            promotions_total += 1
            name = promo.get("field_name")
            trust_classes[promo.get("trust_class") or "unknown"] += 1
            if name:
                field_promoted[name] += 1
                if asked and name not in asked:
                    invariant_violations.append(
                        f"promoted field not in asked set: {name} (G1)"
                    )
            rationale = str(promo.get("rationale") or "")
            memory_id = rationale.rsplit(":", 1)[-1] if rationale else "unknown"
            memory_ids[memory_id] += 1
        ts = str(event.get("created_at") or event.get("ts") or "")
        if ts and (last_event_at is None or ts > last_event_at):
            last_event_at = ts

    metrics: Dict[str, Any] = {
        "asks_recorded": asks,
        "asks_with_promotion": promoted_asks,
        "promotions_total": promotions_total,
        "promotion_rate": round(promoted_asks / asks, 4) if asks else None,
        "field_asked": dict(field_asked.most_common()),
        "field_promoted": dict(field_promoted.most_common()),
        "trust_class_distribution": dict(trust_classes.most_common()),
        "distinct_memories_promoting": len(memory_ids),
        "top_memory_share": (
            round(memory_ids.most_common(1)[0][1] / promotions_total, 4)
            if promotions_total
            else None
        ),
        "last_event_at": last_event_at,
    }

    if asks < MIN_ASKS:
        verdict = "INSUFFICIENT_DATA"
        reasons = [f"only {asks}/{MIN_ASKS} asks recorded"]
    elif invariant_violations:
        verdict = "GUARDRAIL_VIOLATION"
        reasons = invariant_violations[:10]
    else:
        reasons = []
        explicit = trust_classes.get("explicit_user", 0)
        explicit_share = explicit / promotions_total if promotions_total else 1.0
        metrics["explicit_share"] = round(explicit_share, 4)
        verdict = "REVIEW_READY"
        if explicit_share < EXPLICIT_SHARE_FLOOR:
            verdict = "GUARDRAIL_VIOLATION"
            reasons.append(
                f"explicit_user share {explicit_share:.2f} < {EXPLICIT_SHARE_FLOOR} (G2)"
            )
        top_share = metrics["top_memory_share"]
        if top_share is not None and top_share > MAX_SINGLE_MEMORY_SHARE:
            verdict = "GUARDRAIL_VIOLATION"
            reasons.append(
                f"single memory drives {top_share:.0%} of promotions "
                f"> {MAX_SINGLE_MEMORY_SHARE:.0%} (G3)"
            )
        rate = metrics["promotion_rate"]
        if rate is not None and rate > MAX_PROMOTION_RATE:
            verdict = "GUARDRAIL_VIOLATION"
            reasons.append(f"promotion rate {rate:.0%} > {MAX_PROMOTION_RATE:.0%} (G4)")
        if verdict == "REVIEW_READY":
            reasons.append(
                "all guardrails hold — owner decides the flip "
                "(MEMORY_SLOT_READ_MODE=active); correlation follow-up pending trip identity"
            )

    return {"verdict": verdict, "reasons": reasons, "metrics": metrics}


def render_human(report: Dict[str, Any]) -> str:
    m = report["metrics"]
    lines = [
        "=== E-D slot 1 shadow review (memory_slot_promotion) ===",
        f"verdict: {report['verdict']}",
    ]
    for reason in report["reasons"]:
        lines.append(f"  - {reason}")
    lines += [
        f"asks recorded: {m['asks_recorded']} (with promotion: {m['asks_with_promotion']}, "
        f"rate: {m['promotion_rate']})",
        f"promotions total: {m['promotions_total']} across "
        f"{m['distinct_memories_promoting']} distinct memories",
        f"trust classes: {m['trust_class_distribution']}",
        f"last event: {m['last_event_at']}",
        "",
        "per-field (asked -> promoted):",
    ]
    for name, asked_count in m["field_asked"].items():
        promoted_count = m["field_promoted"].get(name, 0)
        lines.append(f"  {name}: {asked_count} -> {promoted_count}")
    if not m["field_asked"]:
        lines.append("  (no asks recorded yet)")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit-file", type=Path, default=DEFAULT_AUDIT_FILE)
    parser.add_argument("--agency", default=None, help="filter by agency id (user_id)")
    parser.add_argument("--since", default=None, help="ISO timestamp lower bound")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    events = load_events(args.audit_file, args.agency, args.since)
    report = review(events)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(render_human(report))

    # Exit code: 0 = review-ready or clean-empty; 2 = insufficient data;
    # 3 = guardrail violation (a reopen signal for automation).
    if report["verdict"] == "GUARDRAIL_VIOLATION":
        return 3
    if report["verdict"] == "INSUFFICIENT_DATA":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
