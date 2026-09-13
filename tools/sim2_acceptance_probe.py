#!/usr/bin/env python3
"""Sim #2 (Family Summit) fresh-acceptance probe — reusable gate.

Re-runs the Sim #2 defect classes plus the extraction-realignment wave's
new contracts against the REAL pipeline (ExtractionPipeline + decision
layer), in-process and deterministic. Exit 0 = all checks pass.

Usage:
    .venv/bin/python tools/sim2_acceptance_probe.py

Checks (traceable to Docs/sims/SIM2_FAMILY_SUMMIT_RESULTS_2026-09-12.md
and Docs/architecture/EXTRACTION_REALIGNMENT_BLUEPRINT_2026-09-14.md):
  1. Origin fabrication dead      — "okinawa side trip?" never becomes Origin.
  2. Budget scope stable total    — number-free "budget whatever" never flips scope.
  3. D-02 v2                      — "total ... INCLUDING flights" is a fact, not an unknown.
  4. Per-traveler attribution     — Meera's Jain/no-heights bind to HER, not group-wide.
  5. Anniversary survives trades  — April 14 survives Dev's ±1-week flexibility.
  6. Group-chat dump attribution  — [speaker]: lines bind per-speaker facts.
  7. Direction intent (new)       — "bangalore side jaana hai" → OPEN, no fabricated destination.
  8. VFR promotion (new)          — "visit family in india" → India + family_visit purpose.
  9. Past-trip memory (new)       — memories captured as history; history-informed ask emitted;
                                    memories never suggested as destination values.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.intake.decision import (  # noqa: E402
    hypothesis_core_value,
    run_gap_and_decision,
)
from src.intake.extractors import (  # noqa: E402
    ExtractionPipeline,
    _extract_destination_candidates,
    _extract_past_trip_places,
    _extract_trip_intent,
)
from src.intake.packet_models import SourceEnvelope  # noqa: E402

NOTE_1_PRIYA = (
    "hi! i'm organising a japan trip for me and 3 friends — 2 couples. we're "
    "thinking spring next year for cherry blossoms but dates are flexible. "
    "budget is 3.5 lakhs total for everyone INCLUDING flights, that's my hard "
    "cap. we want to do tokyo + kyoto, maybe osaka. one cooking class somewhere "
    "would be amazing. everyone's sending me their own requests so i'll forward "
    "them as they come"
)
NOTE_2_ARJUN = (
    "yo it's arjun — priya's forwarding this. honestly spring is overrated and "
    "everyone goes. december = cheaper flights AND we can ski in hakuba. also we "
    "NEED a scuba day (okinawa side trip?) and osaka nightlife is non-negotiable, "
    "dotonbori till 3am. let's pack the schedule, we can sleep when we're dead. "
    "budget whatever, we'll manage."
)
NOTE_3_MEERA = (
    "hello, meera here (arjun's forwarding for me too). a few important things — "
    "i'm jain, so strictly no onion and no garlic, i'll need jain or at least "
    "pure veg meals everywhere. i'm also terrified of heights so please no "
    "cable cars, no observation decks, nothing like that. we'd love a quiet "
    "ryokan for a couple of nights — it's our 10th anniversary on the trip "
    "(april 14th), so a nice anniversary dinner that day would mean a lot. and "
    "definitely NOT a party hostel. please keep a kimono photo session if possible."
)
NOTE_4_DEV = (
    "hi, dev here. quick one — we can shift the dates by a week either side if "
    "it saves meaningful money, say 40k or more; meera's anniversary is april 14 "
    "so the trip needs to COVER that date no matter what. also please book 2 "
    "separate double rooms, we're not doing one big shared room (sorry arjun). "
    "and maybe don't pack every single day — one slow mid-week would be nice."
)
NOTE_5_CHAT_DUMP = (
    "[priya]: ok updates — total is still 3.5L MAX, don't make me the bad cop\n"
    "[arjun]: DECEMBER. skiing. just saying\n"
    "[meera]: i really can't do cold-weather stuff, and remember NO HEIGHTS. "
    "also jain food, it's in my earlier msg\n"
    "[dev]: april works for us, we just want the 14th covered\n"
    "[arjun]: fine but someone tell me why we're not doing scuba\n"
    "[priya]: because 3.5L, arjun"
)

PAST_TRIP_NOTE = (
    "we went to japan, korea last year and loved it. planning another trip "
    "soon, flexible dates."
)

RESULTS = []


def check(name: str, ok: bool, evidence: str) -> None:
    RESULTS.append((name, ok, evidence))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {evidence}")


def fact(packet, name):
    slot = packet.facts.get(name)
    return slot.value if slot else None


def main() -> int:
    pipeline = ExtractionPipeline()

    print("== Sim #2 fresh acceptance probe ==")

    # --- Notes 1+2: origin fabrication + budget scope stability ---
    packet = pipeline.extract(
        [
            SourceEnvelope.from_freeform(NOTE_1_PRIYA, "voice_note", "priya"),
            SourceEnvelope.from_freeform(NOTE_2_ARJUN, "voice_note", "arjun"),
        ],
        stage="discovery",
    )
    origin = fact(packet, "origin_city")
    origin_val = getattr(origin, "value", origin) if origin is not None else None
    check(
        "1. origin fabrication dead",
        origin_val in (None, [], "", {}) and "okinawa" not in str(origin_val).lower(),
        f"origin_city={origin_val!r}",
    )
    scope = fact(packet, "budget_scope")
    scope_val = getattr(scope, "value", scope) if scope is not None else None
    check(
        "2. budget scope stable total",
        scope_val == "total",
        f"budget_scope={scope_val!r} (after Arjun's 'budget whatever')",
    )

    # --- Note 3: D-02 fact + traveler attribution ---
    packet3 = pipeline.extract(
        [SourceEnvelope.from_freeform(NOTE_1_PRIYA + "\n" + NOTE_3_MEERA, "voice_note", "priya")],
        stage="discovery",
    )
    ambiguities = str(getattr(packet3, "ambiguities", None) or "")
    unknown_names = {u.field_name for u in getattr(packet3, "unknowns", [])}
    d02_fired = (
        "flights_inclusiveness" in ambiguities.lower()
        or "flights_inclusiveness" in unknown_names
    )
    check(
        "3. D-02 v2 fact not unknown",
        not d02_fired,
        f"no flights_inclusiveness ambiguity (ambiguities={bool(ambiguities)}, "
        f"unknowns={sorted(unknown_names)[:4]}...)",
    )
    travelers = fact(packet3, "travelers") or []
    traveler_names = {t.get("name", "").lower() for t in travelers if isinstance(t, dict)}
    meera_constraints = ""
    for t in travelers:
        if isinstance(t, dict) and t.get("name", "").lower() == "meera":
            meera_constraints = json_dumps(t).lower()
    attribution_ok = (
        "meera" in traveler_names
        and "jain" in meera_constraints
        and ("height" in meera_constraints or "heights" in meera_constraints)
    )
    check(
        "4. per-traveler attribution",
        attribution_ok,
        f"travelers={[t.get('name') for t in travelers if isinstance(t, dict)]}, "
        f"meera bundle holds jain+heights={attribution_ok}",
    )

    # --- Note 4: anniversary survives the ±1-week trade ---
    packet4 = pipeline.extract(
        [
            SourceEnvelope.from_freeform(NOTE_3_MEERA, "voice_note", "meera"),
            SourceEnvelope.from_freeform(NOTE_4_DEV, "voice_note", "dev"),
        ],
        stage="discovery",
    )
    all_text = json_dumps({k: fact(packet4, k) for k in list(packet4.facts)}).lower()
    anniversary_ok = "anniversary" in all_text and ("april 14" in all_text or "14th" in all_text)
    check(
        "5. anniversary survives trades",
        anniversary_ok,
        "anniversary + april-14 both present after Dev's ±1-week note",
    )

    # --- Note 5: group-chat dump attribution ---
    packet5 = pipeline.extract(
        [SourceEnvelope.from_freeform(NOTE_1_PRIYA + "\n" + NOTE_5_CHAT_DUMP, "chat_dump", "priya")],
        stage="discovery",
    )
    travelers5 = fact(packet5, "travelers") or []
    names5 = {t.get("name", "").lower() for t in travelers5 if isinstance(t, dict)}
    meera5 = json_dumps(
        [t for t in travelers5 if isinstance(t, dict) and t.get("name", "").lower() == "meera"]
    ).lower()
    dump_ok = {"priya", "arjun", "meera", "dev"}.issubset(names5) and "height" in meera5
    check(
        "6. group-chat dump attribution",
        dump_ok,
        f"speakers bound={sorted(n for n in names5 if n)}, meera keeps NO HEIGHTS={'height' in meera5}",
    )

    # --- New contract: direction intent ---
    cands, status, _ = _extract_destination_candidates("Bangalore side jaana hai")
    check(
        "7. direction intent open",
        "bangalore" not in {c.lower() for c in cands} and status == "open",
        f"candidates={cands}, status={status!r}",
    )

    # --- New contract: VFR promotion ---
    cands, status, _ = _extract_destination_candidates("want to visit family in india")
    purpose = _extract_trip_intent("want to visit family in india").get("trip_purpose")
    check(
        "8. VFR promotion",
        cands == ["India"] and status == "definite" and purpose == "family_visit",
        f"candidates={cands}, purpose={purpose!r}",
    )

    # --- New contract: past-trip memory + history-informed ask ---
    places = _extract_past_trip_places(PAST_TRIP_NOTE)
    regions = {p.get("region") for p in places}
    cands, _, _ = _extract_destination_candidates(PAST_TRIP_NOTE)
    packet9 = pipeline.extract(
        [SourceEnvelope.from_freeform(PAST_TRIP_NOTE, "voice_note", "priya")],
        stage="discovery",
    )
    past_fact = fact(packet9, "past_trips") or []
    result = run_gap_and_decision(packet9)
    dest_asks = [
        q["question"]
        for q in result.follow_up_questions
        if q.get("field_name") == "destination_candidates"
    ]
    suggested_leak = any(
        q.get("suggested_values") for q in result.follow_up_questions
        if q.get("field_name") == "destination_candidates"
    )
    memory_ok = (
        {p["place"] for p in places} == {"Japan", "Korea"}
        and regions == {"East Asia"}
        and all(p.get("sentiment") == "positive" for p in places)
        and cands == []
        and [p.get("place") for p in past_fact] == ["Japan", "Korea"]
        and dest_asks
        and "Japan and Korea" in dest_asks[0]
        and "East Asia" in dest_asks[0]
        and not suggested_leak
    )
    check(
        "9. past-trip memory + informed ask",
        memory_ok,
        f"history={[(p['place'], p['region'], p['sentiment']) for p in places]}, "
        f"dest candidates={cands}, ask={dest_asks[:1]}, memory-as-suggestion={suggested_leak}",
    )

    # --- New contract: origin "side" is a hypothesis, never a fact (Option 3) ---
    origin_note = (
        "Bangalore side jaana hai for 4 people, budget 2L total, "
        "next march for 5 days"
    )
    packet10 = pipeline.extract(
        [SourceEnvelope.from_freeform(origin_note, "voice_note", "priya")],
        stage="discovery",
    )
    origin_fact = fact(packet10, "origin_city")
    origin_hyp = packet10.hypotheses.get("origin_city")
    origin_hyp_core = hypothesis_core_value(origin_hyp)
    result10 = run_gap_and_decision(packet10)
    origin_asks = [
        q for q in result10.follow_up_questions
        if q.get("field_name") == "origin_city"
    ]
    origin_ok = (
        origin_fact is None
        and origin_hyp_core == "Bangalore"
        and origin_asks
        and "Starting from Bangalore itself" in origin_asks[0]["question"]
        and origin_asks[0].get("suggested_values") == ["Bangalore"]
        and origin_asks[0].get("can_infer") is True
    )
    check(
        "10. origin side hypothesis, not fact",
        origin_ok,
        f"origin fact={origin_fact}, hypothesis={origin_hyp_core!r}, "
        f"ask={origin_asks[0]['question'] if origin_asks else None!r}",
    )

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    print("ALL GREEN — Sim #2 defect classes dead, new contracts live.")
    return 0


def json_dumps(obj) -> str:
    import json

    return json.dumps(obj, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
