"""Memory slot wiring — E-D contract tests (ADR-008 item 4, Addendum 9).

Contract: memory may RANK questions, never select inventory.
- slot_candidates is the SOLE sanctioned read seam;
- shadow mode (default) computes + audits but never reorders;
- expired facts are dropped, not down-weighted;
- promotion-only: candidates never answer or suppress an unknown;
- import containment: no module outside the sanctioned set reads memory.
"""

import importlib
import inspect
import sys


from src.memory import slot_candidates as slots
from src.memory.slot_candidates import memory_slot_candidates


class _FakeItem:
    def __init__(self, item_id, content, fact_type="preference", created=None):
        self.id = item_id
        self.content = content
        self.metadata = {"fact_type": fact_type}
        self.created_at = created


class _FakeStore:
    def __init__(self, results):
        self._results = results
        self.queries = []

    def query_memories(self, agency_id, query, entity_id=None, tier=None, top_k=10):
        self.queries.append(query)
        return self._results


def _unknowns(*names):
    return [{"field_name": n} for n in names]


def test_shadow_mode_default_returns_order_unchanged():
    store = _FakeStore([(_FakeItem("m1", "customer prefers aisle seats on flights"), 0.9)])
    unknowns = _unknowns("seat_preference", "budget_min")
    result = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    applied = slots.apply_shadow(unknowns, result["candidates"], agency_id="a", trip_id="t")
    assert [u["field_name"] for u in applied] == ["seat_preference", "budget_min"]
    assert result["shadow"] is True


def test_promotion_only_never_answers_or_suppresses():
    store = _FakeStore([(_FakeItem("m1", "always flies business class to japan"), 0.95)])
    unknowns = _unknowns("cabin_class", "destination_candidates")
    result = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    names = {c["field_name"] for c in result["candidates"]}
    assert names <= {"cabin_class", "destination_candidates"}  # subset of unknowns


def test_expired_facts_dropped_not_downweighted():
    import datetime
    old = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    store = _FakeStore([(_FakeItem("m-old", "prefers window seats", "preference", old), 0.99)])
    result = memory_slot_candidates(store, "agency-1", "trip-1", _unknowns("seat_preference"))
    assert result["candidates"] == []


def test_store_failure_returns_no_candidates():
    class _Broken:
        def query_memories(self, **kwargs):
            raise RuntimeError("store down")

    result = memory_slot_candidates(_Broken(), "agency-1", "trip-1", _unknowns("budget_min"))
    assert result["candidates"] == []


def test_active_mode_promotes_without_answering():
    store = _FakeStore([(_FakeItem("m1", "budget discussions always reference lakhs"), 0.9)])
    unknowns = _unknowns("budget_min", "destination_candidates")
    result = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    slots.read_mode_active = True
    try:
        applied = slots.apply_active(unknowns, result["candidates"])
        assert sorted(u["field_name"] for u in applied) == ["budget_min", "destination_candidates"]
    finally:
        slots.read_mode_active = False


def test_import_containment_no_memory_reads_outside_slots():
    """E-D §5: only the sanctioned seam + the strategy shadow hook may read
    memory. Suitability and Tier-3 must read nothing (ADR-008 §4.2)."""
    sanctioned = {
        "src.memory.slot_candidates",
        "src.intake.strategy",
        "src.memory.store",
        "src.memory.retriever",
        "src.memory.feedback_bridge",
        "src.memory.decay_engine",
        "src.memory.gdpr_engine",
        "src.memory.supersession",
        "src.memory.eligibility_gate",
    }
    violations = []
    for name in list(sys.modules):
        if not name.startswith(("src.intake", "src.suitability")):
            continue
        module = sys.modules.get(name)
        if module is None:
            continue
        try:
            source = inspect.getsource(sys.modules[name])
        except (OSError, TypeError):
            continue
        if "from src.memory" in source or "import src.memory" in source:
            if name not in sanctioned:
                violations.append(name)
    assert not violations, f"unsanctioned memory reads: {violations}"


def test_suitability_reads_no_memory():
    source = inspect.getsource(importlib.import_module("src.suitability.llm_scorer"))
    assert "src.memory" not in source
