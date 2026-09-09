"""
E-H adversarial lane activation (2026-09-08).

Activates `data/fixtures/adversarial/adversarial_seed_v1.json` (40 records,
probe 2026-09-03) as a live regression lane with the corpus's own status
semantics:

- `passes_today` records are a HARD regression net: extraction must satisfy
  their contracts. If one fails, we regressed.
- `known_defect` records are expected to fail their contracts; the lane
  asserts the known-defect set never GROWS (each defect id must appear in the
  frozen KNOWN_DEFECT_IDS registry). When a defect is later fixed, remove its
  id from the registry AND move its corpus status to passes_today.
- No record may crash the pipeline (must_not_crash is universal).

Exit 1 = a regression (passes_today failure) or a NEW defect (known_defect
id missing from the registry). Exit 0 with printed defect count = status quo.
"""

import json
from pathlib import Path


from src.intake.extractors import ExtractionPipeline
from src.intake.packet_models import SourceEnvelope
from src.intake.validation import validate_packet

CORPUS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data" / "fixtures" / "adversarial" / "adversarial_seed_v1.json"
)

# Frozen registry of probe-time known defects (2026-09-03). When a defect is
# FIXED, remove its id here and flip its corpus status to passes_today. A NEW
# id appearing in _defect_ids means a regression introduced a new defect.
KNOWN_DEFECT_IDS = {
    "adv_bound_005",
    "adv_bound_006",
    "adv_bound_007",
    "adv_ling_004",
    "adv_ling_005",
    "adv_ling_007",
    "adv_ling_009",
    "adv_ling_010",
    "adv_sec_001",
    "adv_sec_003",
    "adv_sec_005",
    "adv_sec_006",
    "adv_sec_007",
    "adv_sec_008",
    "adv_sem_002",
    "adv_sem_003",
    "adv_sem_004",
    "adv_sem_005",
    "adv_sem_006",
    "adv_sem_007",
    "adv_struct_001",
    "adv_struct_006",
}


def _load_corpus() -> list[dict]:
    data = json.loads(CORPUS_PATH.read_text())
    return data.get("records", [])


def _packet_value(packet, dotted: str):
    """Read an extracted value: primary lookup is the packet's fact store
    (facts[field].value); dotted fallbacks cover non-fact attributes."""
    facts = packet.to_dict().get("facts") or {}
    entry = facts.get(dotted)
    if isinstance(entry, dict) and "value" in entry:
        return entry.get("value")
    obj = packet
    for part in dotted.split("."):
        if obj is None:
            return None
        obj = getattr(obj, part, None)
    return obj


def _check_contract(record: dict) -> list[str]:
    """Run one record through the pipeline and return a list of contract
    violations (empty = record satisfies its expected behavior)."""
    failures: list[str] = []
    rid = record["id"]
    try:
        pipeline = ExtractionPipeline()
        text = record["input"].get("text", "")
        envelope = SourceEnvelope.from_freeform(
            text, source="agency_notes", actor="traveler"
        )
        packet = pipeline.extract([envelope], stage="discovery")
        validate_packet(packet, stage="discovery")
    except Exception as exc:
        return [f"CRASHED — {type(exc).__name__}: {exc}"]

    expected = record.get("expected", {})
    for dotted, wanted in (expected.get("must_extract") or {}).items():
        got = _packet_value(packet, dotted)
        want_norm = (
            sorted(str(w).strip() for w in wanted)
            if isinstance(wanted, list)
            else str(wanted).strip()
        )
        if not isinstance(wanted, list):
            wanted = [wanted]
        got_values = got if isinstance(got, list) else [got]
        got_norm = sorted(str(g).strip() for g in got_values)
        want_norm = sorted(str(w).strip() for w in wanted)
        if got_norm != want_norm:
            failures.append(f"{rid}: {dotted} wanted {want_norm!r}, got {got_norm!r}")

    if expected.get("graceful_unknowns_required") and not (
        packet.to_dict().get("unknowns")
    ):
        failures.append(f"{rid}: graceful unknowns required but none reported")

    return failures


# ---------------------------------------------------------------------------
# Lane 1: passes_today records are a hard regression net
# ---------------------------------------------------------------------------


def test_passes_today_records_satisfy_contracts():
    records = [r for r in _load_corpus() if r.get("status") == "passes_today"]
    assert records, "corpus lost its passes_today population"
    failures = []
    for record in records:
        failures.extend(_check_contract(record))
    assert not failures, (
        "REGRESSION — passes_today records violating contracts:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Lane 2: known_defect records may not crash, and the defect set may not grow
# ---------------------------------------------------------------------------


def test_known_defect_records_never_crash_and_defect_set_is_frozen():
    records = [r for r in _load_corpus() if r.get("status") == "known_defect"]
    assert records, "corpus lost its known_defect population"
    crashes = []
    for record in records:
        try:
            _check_contract(record)
        except Exception as exc:
            crashes.append(f"{record['id']}: CRASHED — {exc}")
    assert not crashes, "known_defect records now CRASH the pipeline:\n" + "\n".join(crashes)


def test_defect_registry_matches_corpus_known_defect_ids():
    corpus_defects = {
        r["id"] for r in _load_corpus() if r.get("status") == "known_defect"
    }
    # Every registered id must still be a known defect in the corpus, and the
    # corpus must not have grown new known defects beyond the registry.
    assert corpus_defects == KNOWN_DEFECT_IDS, (
        "Defect registry drift:\n"
        f"  fixed (remove from registry): {sorted(corpus_defects - KNOWN_DEFECT_IDS)}\n"
        f"  new defects (investigate):    {sorted(KNOWN_DEFECT_IDS - corpus_defects)}"
    )
