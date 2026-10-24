"""Do-all closeout — FND-0361 + cost rollup + render-selector honesty.

Three final items from the RAG do-all tranche (2026-10-22, exploration doc
§9/§12):

1. FND-0361: the deterministic suitability tier-3/tier-4 flags carry
   confidence 1.0 with an explicit ``deterministic_rule_trigger`` basis —
   never the old 0.85/0.90 constants that implied a measured uncertainty
   which never existed.
2. Semantic embedding calls record a char-derived INR cost estimate in the
   forensics record; the index endpoint surfaces it.
3. RenderSelection.source names what produced the SELECTED question: when
   the JEV lane grades but nothing passes the rubric, the selection is the
   verbatim floor and source says so.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("RUNNING_TESTS", "1")


# ---------------------------------------------------------------------------
# FND-0361 — deterministic rule flags: confidence asserts the trigger
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    """Mounted RAG router with an isolated store (same shape as
    test_rag_mount.client; duplicated locally to keep the closeout module
    self-contained)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from spine_api.core.auth import get_current_agency
    from spine_api.models.tenant import Agency
    from spine_api.routers import rag as rag_router
    from src.rag.service import RAGService

    app = FastAPI()
    app.include_router(rag_router.router)
    app.dependency_overrides[get_current_agency] = lambda: Agency(
        id="agency_closeout", name="Closeout", slug="closeout"
    )
    app.dependency_overrides[rag_router.get_rag_service] = lambda: RAGService(
        db_path=str(tmp_path / "closeout_rag.db")
    )
    return TestClient(app)


def _packet_with_pace(pace: str):
    from src.intake.packet_models import CanonicalPacket, Slot

    packet = CanonicalPacket(packet_id="fnd0361-packet")
    packet.facts["pace_preference"] = Slot(
        value=pace, authority_level="imported_structured", confidence=0.9
    )
    return packet


def test_fnd0361_tier3_tier4_flags_carry_rule_trigger_confidence():
    from src.suitability.integration import assess_activity_suitability

    packet = _packet_with_pace("relaxed")
    flags = assess_activity_suitability(packet)

    by_type = {f.flag_type: f for f in flags}
    tier3 = by_type.get("suitability_tier3_pacing_overload")
    tier4 = by_type.get("suitability_tier4_fatigue_warning")
    if tier3 is not None:
        assert tier3.confidence == 1.0
        assert tier3.details["confidence_basis"] == "deterministic_rule_trigger"
    if tier4 is not None:
        assert tier4.confidence == 1.0
        assert tier4.details["confidence_basis"] == "deterministic_rule_trigger"


def test_fnd0361_no_fabricated_constants_remain():
    """S2 (source-level): the fabricated constants are gone from the
    serving-path producer."""
    import inspect

    from src.suitability import integration

    source = inspect.getsource(integration.assess_activity_suitability)
    assert "confidence=0.85" not in source
    assert "confidence=0.90" not in source


# ---------------------------------------------------------------------------
# Embedding cost rollup
# ---------------------------------------------------------------------------


def test_embedding_cost_estimate_is_char_derived():
    from src.rag.embeddings import estimate_embedding_cost_inr

    # 400 chars ≈ 100 tokens ≈ 100 / 1M × $0.02 × ₹83 ≈ ₹0.000166
    est = estimate_embedding_cost_inr(400)
    assert 0.0001 < est < 0.001
    # Monotonic in input size.
    assert estimate_embedding_cost_inr(4_000_000) > est * 5000


def test_semantic_provider_records_cost_estimate_in_forensics():
    from src.rag.embeddings import SemanticEmbeddingProvider

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        provider = SemanticEmbeddingProvider(provider_name="openai")

    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(index=0, embedding=[0.1] * 1536)]
    )
    with patch.object(provider, "_get_sdk_client", return_value=fake_client), patch(
        "src.rag.embeddings._strip_pii_for_egress", side_effect=lambda t: t
    ):
        provider.embed_text("x" * 400)

    rec = provider.last_call_record
    assert rec["cost_estimate_inr"] > 0


def test_hash_lane_records_no_cost_estimate():
    """The hash lane is free — no cost estimate may be fabricated for it."""
    from src.rag.embeddings import HashEmbeddingProvider

    provider = HashEmbeddingProvider()
    provider.embed_text("hello world")
    # HashEmbeddingProvider has no forensics record at all: no model call,
    # no cost. (record_llm_call is only emitted by the semantic lane.)
    assert not hasattr(provider, "last_call_record") or provider.last_call_record is None


def test_index_endpoint_surfaces_cost_estimate(client):
    resp = client.post(
        "/api/v1/rag/documents/index",
        headers={"Authorization": "Bearer test-token"},
        json={
            "document_id": "cost_probe",
            "source_type": "agency_policy",
            "title": "Cost Probe",
            "text": "Some policy text for the cost probe.",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # Hash lane → no estimate fabricated (None), honest absence.
    assert "embedding_cost_estimate_inr" in body
    assert body["embedding_cost_estimate_inr"] is None


# ---------------------------------------------------------------------------
# Render selector — selection provenance
# ---------------------------------------------------------------------------


def test_render_selection_source_names_the_floor_when_nothing_passes(monkeypatch):
    from src.intake.question_render_selector import (
        QuestionRenderSelector,
        RenderingCandidate,
    )

    # The ask-loop gate must be ON to reach the grading path.
    monkeypatch.setenv("JEV_ASK_LOOP_ENABLED", "1")

    # JEV answers that FAIL the rubric (intent noul < 0.5): the lane ran,
    # but no candidate passes — the selection must be the verbatim floor
    # and source must name the floor, not the lane.
    failing = MagicMock()
    failing.is_available.return_value = True
    failing.raw_query.return_value = {
        "answers": {
            "preserves_field_intent": {"noul": 0.2},
            "introduces_no_new_facts": {"noul": 0.9},
            "traveler_naturalness": {"score": 2.0},
        }
    }
    selector = QuestionRenderSelector(client=failing)
    result = selector.select(
        field_name="origin_city",
        engine_question="Which city would you fly out from?",
        candidates=[RenderingCandidate(text="Origin city please?", origin="template")],
    )
    assert result.selected_origin == "verbatim_fallback"
    assert result.source == "verbatim_fallback"
    assert len(result.grades) == 1  # JEV evidence still carried
    assert result.grades[0].passes is False


# ---------------------------------------------------------------------------
# Usage-store quota integration — semantic embedding usage is ledgered
# ---------------------------------------------------------------------------


def _quota_service(tmp_path, guard):
    from src.rag.embeddings import SemanticEmbeddingProvider
    from src.rag.service import RAGService

    def _semantic_provider():
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            return SemanticEmbeddingProvider(provider_name="openai")

    service = RAGService(db_path=str(tmp_path / "quota_rag.db"))
    semantic = _semantic_provider()
    service.embedding_provider = semantic
    service.indexer.embedding_provider = semantic
    service.retriever.embedding_provider = semantic
    return service, semantic


def _ok_client():
    fake = MagicMock()
    fake.embeddings.create.return_value = MagicMock(
        data=[MagicMock(index=0, embedding=[0.1] * 1536)]
    )
    return fake


def test_semantic_indexing_respects_quota_block(tmp_path, monkeypatch):
    """A blocked quota reservation aborts semantic indexing BEFORE vectors
    are written (fail-closed), and nothing mislabeled enters the corpus."""
    from src.llm.usage_guard import LLMUsageGuard, LLMUsageStore
    from src.rag.models import DocumentSourceType

    store = LLMUsageStore(db_path=tmp_path / "quota.db")
    guard = LLMUsageGuard(
        enabled=True,
        agency_id="agency_quota",
        daily_budget=0.0,  # zero budget → every reservation blocked
        budget_mode="block",
        store=store,
    )
    monkeypatch.setattr(
        "src.llm.usage_guard.get_guard_for_agency", lambda agency_id: guard
    )

    service, semantic = _quota_service(tmp_path, guard)
    ok_client = _ok_client()
    with patch.object(semantic, "_get_sdk_client", return_value=ok_client):
        with pytest.raises(ValueError, match="quota ledger"):
            service.index_document(
                document_id="blocked_doc",
                agency_id="agency_quota",
                source_type=DocumentSourceType.AGENCY_POLICY,
                title="Blocked",
                text="Some text that would cost money to embed.",
            )

    # Nothing written, no embed call fired (block happens BEFORE the call).
    assert service.store.count_chunks("agency_quota") == 0
    ok_client.embeddings.create.assert_not_called()


def test_semantic_indexing_finalizes_quota_reservation(tmp_path, monkeypatch):
    """Happy path: reserve → embed → finalize as completed with the actual
    estimated cost, so the ledger's daily totals include RAG embeddings."""
    from src.llm.usage_guard import LLMUsageGuard, LLMUsageStore
    from src.rag.models import DocumentSourceType

    store = LLMUsageStore(db_path=tmp_path / "quota_ok.db")
    guard = LLMUsageGuard(
        enabled=True,
        agency_id="agency_quota_ok",
        store=store,  # no budget → allowed
    )
    monkeypatch.setattr(
        "src.llm.usage_guard.get_guard_for_agency", lambda agency_id: guard
    )

    service, semantic = _quota_service(tmp_path, guard)
    with patch.object(semantic, "_get_sdk_client", return_value=_ok_client()):
        service.index_document(
            document_id="ok_doc",
            agency_id="agency_quota_ok",
            source_type=DocumentSourceType.AGENCY_POLICY,
            title="OK",
            text="Embed me.",
        )

    with store._connect() as conn:
        rows = conn.execute(
            "SELECT * FROM usage_events WHERE agency_id = ?", ("agency_quota_ok",)
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "completed"
    assert float(rows[0]["actual_cost"]) > 0
    assert rows[0]["model"] == "text-embedding-3-small"
