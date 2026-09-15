"""Memory slot wiring — E-D contract tests (ADR-008 item 4, Addendum 9).

Contract: memory may RANK questions, never select inventory.
- slot_candidates is the SOLE sanctioned read seam;
- shadow mode (default) computes + audits but never reorders;
- expired facts are dropped, not down-weighted;
- promotion-only: candidates never answer or suppress an unknown;
- import containment: no module outside the sanctioned set reads memory.
"""

import ast
import importlib
import inspect
import sys
from pathlib import Path


from src.memory import slot_candidates as slots
from src.memory.slot_candidates import memory_slot_candidates
from src.memory.models import MemorySourceType


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


def test_active_mode_promotes_without_answering(monkeypatch):
    store = _FakeStore([(_FakeItem("m1", "budget discussions always reference lakhs"), 0.9)])
    unknowns = _unknowns("budget_min", "destination_candidates")
    monkeypatch.setenv("MEMORY_SLOT_READ_MODE", "active")
    result = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    assert result["shadow"] is False
    applied = slots.apply_active(unknowns, result["candidates"])
    assert sorted(u["field_name"] for u in applied) == ["budget_min", "destination_candidates"]
    # Trust-weighted influence actually reorders: the promoted unknown leads.
    assert applied[0]["field_name"] == "budget_min"


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


# ---------------------------------------------------------------------------
# FND-0230 — trust-weighted influence, cross-trip isolation, and the
# repo-wide E-D read-path containment boundary.
# ---------------------------------------------------------------------------

_MEMORY_READ_ROOT = Path(__file__).resolve().parents[1]
_MEMORY_READ_SYMBOLS = {
    "memory_slot_candidates",
    "HybridMemoryRetriever",
    "apply_shadow",
    "apply_active",
    "query_memories",
}

# Sole sanctioned memory READ consumers (E-D §5: the seam + slot-1 hook;
# spine_api customer_memory router is the slot-2 display/hydrate API).
_MEMORY_READ_SANCTIONED_FILES = {
    "src/intake/strategy.py",
    "spine_api/routers/customer_memory.py",
}


def _iter_repo_python_files():
    for top in ("src", "spine_api"):
        root = _MEMORY_READ_ROOT / top
        for path in sorted(root.rglob("*.py")):
            yield path


def _memory_read_violations():
    """Static AST scan: no module outside the sanctioned set may import or
    call a memory read path (E-D §5 prescribed lint-style containment)."""
    violations = []
    for path in _iter_repo_python_files():
        rel = path.relative_to(_MEMORY_READ_ROOT).as_posix()
        if rel.startswith("src/memory/") or rel in _MEMORY_READ_SANCTIONED_FILES:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("src.memory"):
                    for alias in node.names:
                        if alias.name in _MEMORY_READ_SYMBOLS:
                            violations.append(
                                f"{rel}:{node.lineno}: imports memory read path {alias.name}"
                            )
            if isinstance(node, ast.Attribute) and node.attr == "query_memories":
                violations.append(f"{rel}:{node.lineno}: calls query_memories")
            if isinstance(node, ast.Name) and node.id == "HybridMemoryRetriever":
                violations.append(f"{rel}:{node.lineno}: references HybridMemoryRetriever")
    return violations


def test_repo_wide_memory_read_containment():
    """E-D §4/§5: suitability, RAG, orchestration, and every other module
    must be memory-read-free — memory can reach a trip ONLY through the
    sanctioned seam (slot 1) or the display/hydrate API (slot 2)."""
    violations = _memory_read_violations()
    assert not violations, f"unsanctioned memory reads: {violations}"


def test_suitability_and_rag_import_no_memory_static():
    """Direct E-D §4 non-slot assertion for the two highest-risk modules."""
    for rel in (
        "src/suitability/scoring.py",
        "src/suitability/integration.py",
        "src/suitability/llm_scorer.py",
        "src/rag/retriever.py",
        "src/rag/service.py",
    ):
        source = (_MEMORY_READ_ROOT / rel).read_text(encoding="utf-8")
        assert "src.memory" not in source, f"{rel} reads memory"


def _real_store(tmp_path):
    from src.memory.store import MemoryStore

    return MemoryStore(data_file=tmp_path / "slot_wiring_store.jsonl")


def test_real_memory_item_shape_supported(tmp_path):
    """The seam must work against the REAL MemoryStore/BaseMemoryItem shape
    (summary/memory_id/category/provenance) — it previously read .content/.id,
    which exist only on test fakes, silently producing zero candidates."""
    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    result = memory_slot_candidates(
        store, "agency-1", "trip-1", _unknowns("seat_preference", "budget_min")
    )
    assert result["candidates"], "real store produced no candidates"
    top = result["candidates"][0]
    assert top["field_name"] == "seat_preference"
    assert top["memory_excerpt"]  # real summary flowed through
    assert "mem_" in top["rationale"] or "anon" not in top["rationale"]
    assert top["source_type"] == "traveler_direct"
    assert top["trust_class"] == "explicit_user"
    assert top["trust_weight"] == 1.0


def test_low_trust_memory_influence_below_explicit_user(tmp_path):
    """FND-0230: derived/agent_inferred memory is down-weighted — it can
    never steer the ask order with explicit-user authority at equal
    similarity/recency."""
    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.SYSTEM_INFERRED,
        category_hint="preference",
    )
    result = memory_slot_candidates(
        store, "agency-1", "trip-1", _unknowns("seat_preference")
    )
    by_source = {c["source_type"]: c for c in result["candidates"]}
    assert by_source["traveler_direct"]["trust_weight"] == 1.0
    derived = by_source["system_inferred"]
    assert derived["trust_class"] in ("derived", "agent_inferred")
    assert derived["trust_weight"] < 1.0
    assert derived["score"] < by_source["traveler_direct"]["score"]


def test_cross_trip_memory_never_promotes_other_trip(tmp_path):
    """Cross-trip isolation: a trip-scoped episodic fact from trip A may
    promote trip A's unknowns only — never trip B's, and never an unknown
    trip (no trip context → conservatively excluded)."""
    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="delay discussion referenced the date window for this journey",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="trip_milestone",
        payload={"trip_id": "trip-A"},
        source_ref_id="trip-A",
    )
    own = memory_slot_candidates(store, "agency-1", "trip-A", _unknowns("date_window"))
    assert [c["field_name"] for c in own["candidates"]] == ["date_window"]

    other = memory_slot_candidates(store, "agency-1", "trip-B", _unknowns("date_window"))
    assert other["candidates"] == []

    unknown_trip = memory_slot_candidates(store, "agency-1", "", _unknowns("date_window"))
    assert unknown_trip["candidates"] == []


def test_entity_scoped_memory_is_cross_trip_eligible(tmp_path):
    """Traveler-profile preferences are global by design (E-D topical_scope
    'global'): they may promote another trip's unknowns via the sanctioned
    seam — this is the ONLY sanctioned cross-trip channel."""
    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
        payload={"trip_id": "trip-A"},
        source_ref_id="trip-A",
    )
    result = memory_slot_candidates(
        store, "agency-1", "trip-B", _unknowns("seat_preference")
    )
    assert [c["field_name"] for c in result["candidates"]] == ["seat_preference"]


def test_real_item_freshness_horizon_drops_stale(tmp_path):
    """Freshness horizon against the REAL item shape: an expired preference
    is dropped, not down-weighted (E-D §2 corollary 2)."""
    store = _real_store(tmp_path)
    item, _ = store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    assert item is not None
    # Age the persisted fact beyond the 365d preference horizon.
    import datetime as _dt

    stale = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=400)).isoformat()
    item.created_at = stale
    store._save()

    result = memory_slot_candidates(
        store, "agency-1", "trip-1", _unknowns("seat_preference")
    )
    assert result["candidates"] == []


def test_shadow_mode_real_store_logs_without_applying(tmp_path, caplog):
    """Shadow semantics hold against the real store: candidates are
    computed and audited; the returned unknown order is untouched."""
    import logging as _logging

    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_a@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    unknowns = _unknowns("seat_preference", "budget_min")
    result = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    assert result["shadow"] is True
    assert result["candidates"]

    with caplog.at_level(_logging.INFO, logger="spine_api.memory.slot_candidates"):
        applied = slots.apply_shadow(
            unknowns, result["candidates"], agency_id="agency-1", trip_id="trip-1"
        )
    assert [u["field_name"] for u in applied] == ["seat_preference", "budget_min"]
    assert any("memory_slot_promotion" in r.message for r in caplog.records)
    # Rationale visibility (E-D §2 corollary 3): the audit carries the trust class.
    assert any("explicit_user" in str(r.args) for r in caplog.records)


# ---------------------------------------------------------------------------
# X-14 purge propagation — GDPR forget must reach the slot read path
# (ADR-008 §7 row 4 precondition: "Forgetting/GDPR paths gain their
# enforcement purpose at the same time" as the read path wires).
# ---------------------------------------------------------------------------


def test_x14_gdpr_forget_propagates_to_slot_candidates(tmp_path):
    """A forgotten entity's facts must never promote an unknown afterward —
    erasure is load-bearing once the read path influences the ask order."""
    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_purge@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    unknowns = _unknowns("seat_preference")
    before = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    assert [c["field_name"] for c in before["candidates"]] == ["seat_preference"]

    store.forget_entity_gdpr("agency-1", "cust_purge@x.com")

    after = memory_slot_candidates(store, "agency-1", "trip-1", unknowns)
    assert after["candidates"] == [], "forgotten memory still promoting unknowns"


# ---------------------------------------------------------------------------
# Audit at the seam — ADR-008 §1: every capability gets an audit event at
# its enforcing seam. The strategy hook must emit memory_slot_promotion in
# shadow mode (what WOULD have moved) with rationale + trust class.
# ---------------------------------------------------------------------------


def test_strategy_hook_emits_audit_event(monkeypatch, tmp_path):
    from src.intake import strategy as strategy_mod
    from spine_api.core.auth import _jwt_agency_id

    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_audit@x.com",
        raw_text="customer prefers aisle seats on flights",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="preference",
    )
    monkeypatch.setattr(strategy_mod, "_slot_store", lambda: store)
    monkeypatch.delenv("MEMORY_SLOT_READ_MODE", raising=False)  # default: shadow

    events: list = []

    class _FakeAuditStore:
        @staticmethod
        def log_event(event_type, user_id, details):
            events.append((event_type, user_id, details))

    import spine_api.persistence as persistence_mod

    monkeypatch.setattr(persistence_mod, "AuditStore", _FakeAuditStore)

    token = _jwt_agency_id.set("agency-1")
    try:
        ordered = strategy_mod.sort_questions_by_priority(
            _unknowns("seat_preference", "budget_min")
        )
    finally:
        _jwt_agency_id.reset(token)

    # Shadow: order untouched (still static constraint-first priority), but
    # the audit records the would-be promotion.
    priority = strategy_mod.QUESTION_PRIORITY_ORDER
    expected = sorted(
        ["seat_preference", "budget_min"], key=lambda n: priority.get(n, 999)
    )
    assert [u["field_name"] for u in ordered] == expected
    assert len(events) == 1
    event_type, user_id, details = events[0]
    assert event_type == "memory_slot_promotion"
    assert user_id == "agency-1"
    assert details["mode"] == "shadow"
    assert details["promoted"][0]["field_name"] == "seat_preference"
    assert details["promoted"][0]["trust_class"] == "explicit_user"
    assert details["promoted"][0]["rationale"]


# ---------------------------------------------------------------------------
# E-D slot 2 read — memory_on_file_facts (display-only durable facts).
# ---------------------------------------------------------------------------


def test_on_file_facts_labeled_mapped_and_freshness_dropped(tmp_path):
    """Slot-2 read: durable facts come back labeled with provenance, mapped
    to profile field names, and stale facts are dropped (one freshness
    policy shared with the slot-1 read)."""
    import datetime as _dt

    store = _real_store(tmp_path)
    store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_chips@x.com",
        raw_text="Dietary requirement: Strict Vegan & Nut-Free",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="dietary",
    )
    item, _ = store.ingest_memory(
        agency_id="agency-1",
        entity_id="cust_chips@x.com",
        raw_text="Seating preference: Window seat forward cabin",
        source_type=MemorySourceType.TRAVELER_DIRECT,
        category_hint="seating",
    )
    assert item is not None
    stale = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=400)).isoformat()
    item.created_at = stale
    store._save()

    facts = slots.memory_on_file_facts(store, "agency-1", "cust_chips@x.com")

    by_field = {f["field_name"]: f for f in facts if f["field_name"]}
    # Stale seating preference dropped (preference horizon 365d), not down-weighted.
    assert "seating_preference" not in by_field
    dietary = by_field["dietary_requirements"]
    assert "Vegan" in dietary["value"]
    assert dietary["source"] == "memory"
    assert dietary["trust_class"] == "explicit_user"
    assert dietary["observed_at"]
    assert all(f["source"] == "memory" for f in facts)


def test_on_file_facts_empty_entity_returns_nothing(tmp_path):
    store = _real_store(tmp_path)
    assert slots.memory_on_file_facts(store, "agency-1", "cust_nobody@x.com") == []
    assert slots.memory_on_file_facts(store, "agency-1", "") == []


def test_on_file_facts_dedupe_identical_reingestions(tmp_path):
    """Repeated identical ingestion (supersession does not treat identical
    content as a conflict) must render as ONE chip, keeping the newest."""
    store = _real_store(tmp_path)
    for _ in range(2):
        store.ingest_memory(
            agency_id="agency-1",
            entity_id="cust_dupe@x.com",
            raw_text="Dietary requirement: Strict Vegan & Nut-Free",
            source_type=MemorySourceType.TRAVELER_DIRECT,
            category_hint="dietary",
        )
    facts = slots.memory_on_file_facts(store, "agency-1", "cust_dupe@x.com")
    dietary = [f for f in facts if f["field_name"] == "dietary_requirements"]
    assert len(dietary) == 1, f"duplicate chips rendered: {len(dietary)}"
